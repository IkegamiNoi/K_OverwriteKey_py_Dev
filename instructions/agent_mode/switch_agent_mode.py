"""エージェント構成（Codex併用 / Claudeのみ）の切り替えスクリプト。

instructions/save_mode/switch_save_mode.py と同型の対話式スイッチャー。
save_mode が .claude/settings.json 1 ファイルを差し替えるのに対し、
本スクリプトは switch_files/<mode>/ 配下にミラーした複数ファイルを
リポジトリルートへ一括反映する。

- モードディレクトリに存在するファイル  → リポジトリへコピー
- 他モードにのみ存在するファイル        → リポジトリから削除
  （例: claude_only 適用時は codex-*.md エージェント定義を削除。
    codex モードへ戻すと復元される）
- 適用前に現状の管理対象ファイルを backup/<timestamp>/ へ退避する
"""

from __future__ import annotations

import difflib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[1]

MODES_FILE = SCRIPT_DIR / "modes.json"
SWITCH_FILES_DIR = SCRIPT_DIR / "switch_files"
BACKUP_DIR = SCRIPT_DIR / "backup"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_modes() -> list[dict[str, Any]]:
    return load_json(MODES_FILE)


def get_mode_by_id(modes: list[dict[str, Any]], mode_id: int) -> dict[str, Any] | None:
    for mode in modes:
        if int(mode["id"]) == mode_id:
            return mode
    return None


def mode_dir(mode: dict[str, Any]) -> Path:
    return SWITCH_FILES_DIR / mode["dir"]


def mode_files(mode: dict[str, Any]) -> dict[str, Path]:
    """モードディレクトリ配下のファイルを { リポジトリ相対パス: 絶対パス } で返す。"""
    base = mode_dir(mode)
    if not base.exists():
        return {}

    result: dict[str, Path] = {}
    for path in sorted(base.rglob("*")):
        if path.is_file():
            rel = path.relative_to(base).as_posix()
            result[rel] = path
    return result


def managed_relpaths(modes: list[dict[str, Any]]) -> list[str]:
    """全モードのファイルの和集合 = 本スクリプトが管理する（コピー/削除しうる）パス一覧。"""
    paths: set[str] = set()
    for mode in modes:
        paths.update(mode_files(mode).keys())
    return sorted(paths)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def files_equal(a: Path, b: Path) -> bool:
    return read_text(a) == read_text(b)


def match_mode(modes: list[dict[str, Any]], mode: dict[str, Any]) -> tuple[bool, list[str]]:
    """現在のリポジトリが指定モードと一致するか。(一致, 不一致理由リスト) を返す。"""
    problems: list[str] = []
    files = mode_files(mode)

    for rel in managed_relpaths(modes):
        repo_path = ROOT_DIR / rel

        if rel in files:
            if not repo_path.exists():
                problems.append(f"欠落: {rel}")
            elif not files_equal(repo_path, files[rel]):
                problems.append(f"内容差分: {rel}")
        else:
            if repo_path.exists():
                problems.append(f"余分（このモードでは削除される）: {rel}")

    return (not problems, problems)


def find_current_mode(modes: list[dict[str, Any]]) -> dict[str, Any] | None:
    for mode in modes:
        matched, _ = match_mode(modes, mode)
        if matched:
            return mode
    return None


def backup_current(modes: list[dict[str, Any]]) -> Path | None:
    """管理対象ファイルのうちリポジトリに存在するものを backup/<timestamp>/ へ退避する。"""
    targets = [rel for rel in managed_relpaths(modes) if (ROOT_DIR / rel).exists()]
    if not targets:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = BACKUP_DIR / timestamp

    for rel in targets:
        dest = backup_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT_DIR / rel, dest)

    return backup_root


def print_help() -> None:
    print(
        """
Commands:
  help, h, ?              ヘルプ表示
  list, l                 登録済みモード一覧
  show <id>, s <id>       内容説明と対象ファイルを表示
  diff <id>, d <id>       現在のリポジトリと指定モードの差分表示
  apply <id>, a <id>      指定モードをリポジトリへ適用
  check, c                現在の構成がどのモードと一致するか確認
  quit, q, exit           終了

Examples:
  l
  s 2
  d 2
  a 2
""".strip()
    )


def print_modes(modes: list[dict[str, Any]]) -> None:
    print("\n登録済みモード:")
    for mode in modes:
        print(f"  {mode['id']}: {mode['name']}  (switch_files/{mode['dir']}/)")
    print()


def show_mode(modes: list[dict[str, Any]], mode_id: int) -> None:
    mode = get_mode_by_id(modes, mode_id)
    if mode is None:
        print("指定された番号は存在しません。")
        return

    print(f"\n[{mode['id']}] {mode['name']}")
    print(f"dir: switch_files/{mode['dir']}/")
    print(f"description: {mode.get('description', '')}")

    files = mode_files(mode)
    if not files:
        print(f"警告: モードディレクトリが空か存在しません: {mode_dir(mode)}")
        return

    print("\n適用されるファイル:")
    for rel in files:
        print(f"  copy:   {rel}")

    removed = [rel for rel in managed_relpaths(modes) if rel not in files]
    for rel in removed:
        print(f"  delete: {rel}")
    print()


def diff_mode(modes: list[dict[str, Any]], mode_id: int) -> None:
    mode = get_mode_by_id(modes, mode_id)
    if mode is None:
        print("指定された番号は存在しません。")
        return

    files = mode_files(mode)
    has_diff = False

    for rel in managed_relpaths(modes):
        repo_path = ROOT_DIR / rel

        if rel in files:
            if not repo_path.exists():
                has_diff = True
                print(f"\n--- （リポジトリに存在しない） {rel}")
                print(f"+++ 適用で作成: {rel}")
                continue

            if files_equal(repo_path, files[rel]):
                continue

            has_diff = True
            diff = "\n".join(
                difflib.unified_diff(
                    read_text(repo_path).splitlines(),
                    read_text(files[rel]).splitlines(),
                    fromfile=f"current {rel}",
                    tofile=f"{mode['dir']}/{rel}",
                    lineterm="",
                )
            )
            print(f"\n{diff}")
        else:
            if repo_path.exists():
                has_diff = True
                print(f"\n--- 適用で削除: {rel}")

    if not has_diff:
        print("差分はありません。")


def apply_mode(modes: list[dict[str, Any]], mode_id: int) -> None:
    mode = get_mode_by_id(modes, mode_id)
    if mode is None:
        print("指定された番号は存在しません。")
        return

    files = mode_files(mode)
    if not files:
        print(f"モードディレクトリが空か存在しません: {mode_dir(mode)}")
        return

    backup_root = backup_current(modes)

    for rel, src in files.items():
        dest = ROOT_DIR / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"copied:  {rel}")

    for rel in managed_relpaths(modes):
        if rel in files:
            continue
        repo_path = ROOT_DIR / rel
        if repo_path.exists():
            repo_path.unlink()
            print(f"deleted: {rel}")

    print(f"\n{mode['name']} に切り替えました。")
    if backup_root:
        print(f"backup: {backup_root}")
    print("反映には Claude Code の再起動、または新セッション開始が必要です。")


def check_current(modes: list[dict[str, Any]]) -> None:
    matched = find_current_mode(modes)
    if matched:
        print(f"現在の構成は登録済みです: [{matched['id']}] {matched['name']}")
        return

    print("警告: 現在の構成は登録モードのどれにも一致しません。")
    print("モードごとの不一致内容:")
    for mode in modes:
        _, problems = match_mode(modes, mode)
        print(f"\n[{mode['id']}] {mode['name']}")
        for problem in problems:
            print(f"  {problem}")
    print(
        "\n管理対象ファイル（.claude/rules/agent_selection.md 等）を直接編集した場合は、\n"
        "その内容を switch_files/ 配下の対応モードにも反映してください。"
    )


def parse_command(raw: str) -> tuple[str, list[str]]:
    parts = raw.strip().split()
    if not parts:
        return "", []
    return parts[0].lower(), parts[1:]


def main() -> None:
    if not MODES_FILE.exists():
        print(f"modes.json が存在しません: {MODES_FILE}")
        sys.exit(1)

    modes = load_modes()

    print("Claude agent-mode switcher")
    print_modes(modes)
    check_current(modes)
    print("\nhelp または h で操作一覧を表示できます。")

    while True:
        raw = input("\nどれに切り替えますか? > ")
        command, args = parse_command(raw)

        if command in {"", "help", "h", "?"}:
            print_help()

        elif command in {"list", "l"}:
            print_modes(modes)

        elif command in {"show", "s"}:
            if not args:
                print("番号を指定してください。例: show 1")
                continue
            show_mode(modes, int(args[0]))

        elif command in {"diff", "d"}:
            if not args:
                print("番号を指定してください。例: diff 1")
                continue
            diff_mode(modes, int(args[0]))

        elif command in {"apply", "a"}:
            if not args:
                print("番号を指定してください。例: apply 1")
                continue
            apply_mode(modes, int(args[0]))

        elif command in {"check", "c"}:
            check_current(modes)

        elif command in {"quit", "q", "exit"}:
            print("終了します。")
            break

        else:
            print("不明なコマンドです。help を確認してください。")


if __name__ == "__main__":
    main()
