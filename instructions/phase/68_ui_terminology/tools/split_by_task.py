"""baseline_ja_strings.md を phase.md の担当（ファイル単位）でタスクごとの一覧へ分ける。"""
import re
import sys
from pathlib import Path

# (タスク, パスの正規表現)。上から順に最初に当たったタスクへ割り当てる。
OWNERS = [
    ("task_02", r"presentation/app\.py$", (123, 124)),
    ("task_02", r"controllers/config_io/(keymap_file_io|trigger_set_file_io|sequence_file_io|keymap_set_io|child_save_\w+|io_dialogs|save_target_snapshot|startup_io)\.py$", None),
    ("task_02", r"application/config_service/(__init__|child_file_io|keymap_save_plan|save_plan_execution|split_loading)\.py$", None),
    ("task_02", r"application/save_plan\.py$", None),
    ("task_05", r"(dialogs/preset_manager|config_io/hotkey_presets_io|orphan_sweep_\w+|quarantine_\w+|reference_cleanup_\w+|keymap_set_history_\w+|config_service/keymap_set_history)\.py$", None),
    ("task_03", r"controllers/(keymap_panel|trigger_panel)/", None),
    ("task_03", r"(controllers/(hook_controller|key_capture|layout_controller)|presentation/app|application/(keymap_switch_batch|hotkey_service|hook_coordinator|action_executor)|presentation/hook_button_texts|dialogs/(keymap_edit_dialog|keymap_switch_batch_dialog|trigger_dialog))\.py$", None),
    ("task_06", r"(presentation/views/|presentation/screen_grid/|domain/screen_grid/|dialogs/(grid_editor_window|layout_delete_dialog)\.py$|presentation/(keyboard_window|keyboard_layouts)\.py$|infrastructure/win32_window\.py$)", None),
    ("task_04", r"(dialogs/(action_\w+|preset_dialog)\.py$|application/|domain/|infrastructure/input_gateway\.py$)", None),
]


def owner_of(path: str, line: int) -> str:
    for task, pattern, lines in OWNERS:
        if re.search(pattern, path) and (lines is None or line in lines):
            return task
    return "unassigned"


def main(src: str, out_dir: str) -> None:
    buckets: dict[str, list[str]] = {}
    path = ""
    for raw in Path(src).read_text(encoding="utf-8").splitlines():
        if raw.startswith("## "):
            path = raw[3:].strip()
            continue
        m = re.match(r"- L(\d+): ", raw)
        if not m:
            continue
        task = owner_of(path, int(m.group(1)))
        buckets.setdefault(task, []).append(f"- {path}:{m.group(1)} {raw[m.end():]}")
    for task, rows in sorted(buckets.items()):
        Path(out_dir, f"{task}_strings.md").write_text(
            f"# {task} の対象文字列（実装前・baseline より）\n\n" + "\n".join(rows) + "\n", encoding="utf-8"
        )
        print(task, len(rows))


main(sys.argv[1], sys.argv[2])
