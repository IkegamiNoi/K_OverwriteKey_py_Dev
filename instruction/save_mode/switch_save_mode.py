from __future__ import annotations

import copy
import difflib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[1]

CLAUDE_SETTINGS = ROOT_DIR / ".claude" / "settings.json"

MODES_FILE = SCRIPT_DIR / "modes.json"
SWITCH_FILES_DIR = SCRIPT_DIR / "switch_files"
BACKUP_DIR = SCRIPT_DIR / "backup"

FULL_HOOKS_FILE_NAME = "full_hooks.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def normalized_json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


def load_modes() -> list[dict[str, Any]]:
    return load_json(MODES_FILE)


def get_mode_by_id(modes: list[dict[str, Any]], mode_id: int) -> dict[str, Any] | None:
    for mode in modes:
        if int(mode["id"]) == mode_id:
            return mode
    return None


def mode_path(mode: dict[str, Any]) -> Path:
    return SWITCH_FILES_DIR / mode["file"]


def full_hooks_path() -> Path:
    return SWITCH_FILES_DIR / FULL_HOOKS_FILE_NAME


def backup_current_settings() -> Path | None:
    if not CLAUDE_SETTINGS.exists():
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"settings_{timestamp}.json"
    shutil.copy2(CLAUDE_SETTINGS, backup_path)
    return backup_path


def current_matches_registered(modes: list[dict[str, Any]], current: Any) -> dict[str, Any] | None:
    current_text = normalized_json_text(current)

    for mode in modes:
        path = mode_path(mode)
        if not path.exists():
            continue

        candidate = load_json(path)
        if normalized_json_text(candidate) == current_text:
            return mode

    return None


def unified_diff_text(title_a: str, a: Any, title_b: str, b: Any) -> str:
    a_lines = normalized_json_text(a).splitlines()
    b_lines = normalized_json_text(b).splitlines()

    return "\n".join(
        difflib.unified_diff(
            a_lines,
            b_lines,
            fromfile=title_a,
            tofile=title_b,
            lineterm="",
        )
    )


def find_missing_items(base: Any, current: Any, path: str = "$") -> list[tuple[str, Any]]:
    """
    base に存在せず、current に存在する項目だけを検出する。
    値変更はここでは検出しない。
    """
    missing: list[tuple[str, Any]] = []

    if isinstance(base, dict) and isinstance(current, dict):
        for key, current_value in current.items():
            child_path = f"{path}.{key}"

            if key not in base:
                missing.append((child_path, current_value))
            else:
                missing.extend(find_missing_items(base[key], current_value, child_path))

    elif isinstance(base, list) and isinstance(current, list):
        base_texts = {normalized_json_text(item) for item in base}

        for index, current_item in enumerate(current):
            if normalized_json_text(current_item) not in base_texts:
                missing.append((f"{path}[{index}]", current_item))

    return missing


def find_changed_values(base: Any, current: Any, path: str = "$") -> list[tuple[str, Any, Any]]:
    """
    base にも current にも存在するが、値が違うものを検出する。
    自動適用はしない。警告用。
    """
    changed: list[tuple[str, Any, Any]] = []

    if isinstance(base, dict) and isinstance(current, dict):
        common_keys = set(base.keys()) & set(current.keys())
        for key in sorted(common_keys):
            changed.extend(find_changed_values(base[key], current[key], f"{path}.{key}"))

    elif isinstance(base, list) and isinstance(current, list):
        return changed

    else:
        if base != current:
            changed.append((path, base, current))

    return changed


def apply_missing_items(target: Any, missing_items: list[tuple[str, Any]]) -> Any:
    """
    missing_items を target に追加する。
    dict の新規キー、list の新規要素の追加を想定。
    """
    result = copy.deepcopy(target)

    for item_path, value in missing_items:
        insert_by_path(result, item_path, value)

    return result


def insert_by_path(data: Any, item_path: str, value: Any) -> None:
    """
    "$.hooks.UserPromptSubmit[2]" のようなパスに追加する。
    - dictキーが存在しない場合は追加
    - list要素の場合は append
    """
    parts = parse_path(item_path)
    cursor = data

    for part in parts[:-1]:
        if isinstance(part, str):
            cursor = cursor[part]
        elif isinstance(part, int):
            cursor = cursor[part]

    last = parts[-1]

    if isinstance(last, str):
        if isinstance(cursor, dict) and last not in cursor:
            cursor[last] = copy.deepcopy(value)
    elif isinstance(last, int):
        if isinstance(cursor, list):
            value_text = normalized_json_text(value)
            existing = {normalized_json_text(item) for item in cursor}
            if value_text not in existing:
                cursor.append(copy.deepcopy(value))


def parse_path(item_path: str) -> list[str | int]:
    """
    "$.hooks.UserPromptSubmit[2]" -> ["hooks", "UserPromptSubmit", 2]
    """
    if not item_path.startswith("$."):
        raise ValueError(f"Unsupported path: {item_path}")

    raw = item_path[2:]
    parts: list[str | int] = []

    for chunk in raw.split("."):
        while "[" in chunk:
            key, rest = chunk.split("[", 1)
            if key:
                parts.append(key)
            index_str, rest = rest.split("]", 1)
            parts.append(int(index_str))
            chunk = rest

        if chunk:
            parts.append(chunk)

    return parts


def print_help() -> None:
    print(
        """
Commands:
  help, h, ?              ヘルプ表示
  list, l                 登録済みファイル一覧
  show <id>, s <id>       内容説明を表示
  diff <id>, d <id>       現在の settings.json と指定ファイルの差分表示
  apply <id>, a <id>      指定ファイルを .claude/settings.json に適用
  check, c                現在の settings.json が登録済みか確認
  scan, sc                未登録時、full_hooks.json にない項目を確認
  quit, q, exit           終了

Examples:
  l
  s 1
  d 2
  a 1
  scan
""".strip()
    )


def print_modes(modes: list[dict[str, Any]]) -> None:
    print("\n登録済みファイル:")
    for mode in modes:
        print(f"  {mode['id']}: {mode['name']}  ({mode['file']})")
    print()


def show_mode(modes: list[dict[str, Any]], mode_id: int) -> None:
    mode = get_mode_by_id(modes, mode_id)
    if mode is None:
        print("指定された番号は存在しません。")
        return

    print(f"\n[{mode['id']}] {mode['name']}")
    print(f"file: {mode['file']}")
    print(f"description: {mode.get('description', '')}")

    path = mode_path(mode)
    if not path.exists():
        print(f"警告: ファイルが存在しません: {path}")
    print()


def diff_mode(modes: list[dict[str, Any]], mode_id: int) -> None:
    mode = get_mode_by_id(modes, mode_id)
    if mode is None:
        print("指定された番号は存在しません。")
        return

    if not CLAUDE_SETTINGS.exists():
        print(f"現在の settings.json が存在しません: {CLAUDE_SETTINGS}")
        return

    target_path = mode_path(mode)
    if not target_path.exists():
        print(f"対象ファイルが存在しません: {target_path}")
        return

    current = load_json(CLAUDE_SETTINGS)
    target = load_json(target_path)

    diff = unified_diff_text("current .claude/settings.json", current, mode["file"], target)
    print(diff if diff else "差分はありません。")


def apply_mode(modes: list[dict[str, Any]], mode_id: int) -> None:
    mode = get_mode_by_id(modes, mode_id)
    if mode is None:
        print("指定された番号は存在しません。")
        return

    target_path = mode_path(mode)
    if not target_path.exists():
        print(f"対象ファイルが存在しません: {target_path}")
        return

    backup_path = backup_current_settings()
    CLAUDE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target_path, CLAUDE_SETTINGS)

    print(f"{mode['name']} に切り替えました。")
    print(f"copied: {target_path}")
    print(f"to:     {CLAUDE_SETTINGS}")
    if backup_path:
        print(f"backup: {backup_path}")
    print("反映には Claude Code の再起動、または新セッション開始が必要です。")


def check_current(modes: list[dict[str, Any]]) -> None:
    if not CLAUDE_SETTINGS.exists():
        print(f"現在の settings.json が存在しません: {CLAUDE_SETTINGS}")
        return

    current = load_json(CLAUDE_SETTINGS)
    matched = current_matches_registered(modes, current)

    if matched:
        print(f"現在の settings.json は登録済みです: [{matched['id']}] {matched['name']}")
    else:
        print("警告: 現在の settings.json は登録ファイルのどれにも一致しません。")
        print("未登録の変更が含まれている可能性があります。")
        print("詳細確認は scan を実行してください。")


def scan_unregistered(modes: list[dict[str, Any]]) -> None:
    if not CLAUDE_SETTINGS.exists():
        print(f"現在の settings.json が存在しません: {CLAUDE_SETTINGS}")
        return

    full_path = full_hooks_path()
    if not full_path.exists():
        print(f"full_hooks.json が存在しません: {full_path}")
        return

    current = load_json(CLAUDE_SETTINGS)
    full_hooks = load_json(full_path)

    matched = current_matches_registered(modes, current)
    if matched:
        print(f"現在の settings.json は登録済みです: [{matched['id']}] {matched['name']}")
        return

    print("警告: 現在の settings.json は登録ファイルのどれにも一致しません。")

    missing = find_missing_items(full_hooks, current)
    changed = find_changed_values(full_hooks, current)

    if changed:
        print("\n値変更があります。これは自動適用しません。")
        for path, before, after in changed:
            print(f"  {path}")
            print(f"    full_hooks: {before}")
            print(f"    current:    {after}")

    if not missing:
        print("\nfull_hooks.json にない追加項目はありません。")
        print("値変更だけが原因の可能性があります。")
        return

    print("\nfull_hooks.json にない追加項目:")
    for i, (path, value) in enumerate(missing, start=1):
        print(f"\n[{i}] {path}")
        print(normalized_json_text(value))

    print(
        """
選択:
  all        full_hooks.json と全登録ファイルに追加項目を適用
  some       full_hooks.json と指定した登録ファイルに追加項目を適用
  new        現在の settings.json を新しい置き換えファイルとして保存
  full       full_hooks.json のみに追加項目を適用
  ignore     何もしない
""".strip()
    )

    choice = input("> ").strip().lower()

    if choice in {"ignore", "i", "q"}:
        print("何も変更しませんでした。")
        return

    if choice in {"new", "n"}:
        create_new_switch_file_from_current(modes, current)
        updated_full = apply_missing_items(full_hooks, missing)
        save_json(full_path, updated_full)
        print("full_hooks.json にも追加項目を適用しました。")
        return

    if choice in {"full", "f"}:
        updated_full = apply_missing_items(full_hooks, missing)
        save_json(full_path, updated_full)
        print("full_hooks.json に追加項目を適用しました。")
        return

    target_modes: list[dict[str, Any]] = []

    if choice in {"all", "a"}:
        target_modes = [
            mode for mode in modes
            if mode["file"] != FULL_HOOKS_FILE_NAME
        ]

    elif choice in {"some", "s"}:
        print_modes(modes)
        raw = input("適用する番号をカンマ区切りで入力してください: ").strip()
        ids = parse_ids(raw)
        for mode_id in ids:
            mode = get_mode_by_id(modes, mode_id)
            if mode and mode["file"] != FULL_HOOKS_FILE_NAME:
                target_modes.append(mode)
    else:
        print("不明な選択です。何も変更しませんでした。")
        return

    updated_full = apply_missing_items(full_hooks, missing)
    save_json(full_path, updated_full)
    print("full_hooks.json に追加項目を適用しました。")

    for mode in target_modes:
        path = mode_path(mode)
        if not path.exists():
            print(f"skip: {path} が存在しません。")
            continue

        data = load_json(path)
        updated = apply_missing_items(data, missing)
        save_json(path, updated)
        print(f"updated: {path}")


def parse_ids(raw: str) -> list[int]:
    result: list[int] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        result.append(int(item))
    return result


def create_new_switch_file_from_current(modes: list[dict[str, Any]], current: Any) -> None:
    file_stem = input("新規ファイル名を入力してください。例: custom_mode.json: ").strip()

    if not file_stem:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_stem = f"custom_mode_{timestamp}.json"

    if not file_stem.endswith(".json"):
        file_stem += ".json"

    new_path = SWITCH_FILES_DIR / file_stem
    if new_path.exists():
        print(f"すでに存在します: {new_path}")
        return

    save_json(new_path, current)

    next_id = max(int(mode["id"]) for mode in modes) + 1
    name = input("表示名を入力してください: ").strip() or file_stem
    description = input("説明を入力してください: ").strip()

    modes.append(
        {
            "id": next_id,
            "name": name,
            "file": file_stem,
            "description": description,
        }
    )
    save_json(MODES_FILE, modes)

    print(f"新規置き換えファイルを作成しました: {new_path}")
    print(f"modes.json に登録しました: id={next_id}")


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

    print("Claude settings switcher")
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

        elif command in {"scan", "sc"}:
            scan_unregistered(modes)
            modes = load_modes()

        elif command in {"quit", "q", "exit"}:
            print("終了します。")
            break

        else:
            print("不明なコマンドです。help を確認してください。")


if __name__ == "__main__":
    main()