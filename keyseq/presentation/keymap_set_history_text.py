"""構成セット履歴の表示文言（I/O を行わない）。"""

from pathlib import PureWindowsPath
from keyseq.shared.i18n import tr

RECENT_NODE_LABEL = "直近（最大20件）"
READ_ONLY_NOTICE = "履歴ファイルを読み込めませんでした。編集できません。"
TITLE = "構成セットの履歴"
NAME_HEADING = "名前"
PATH_HEADING = "パス"
CATEGORY_LABEL = "分類名"
ADD_CATEGORY = "＋分類を追加"
RENAME_CATEGORY = "分類名を変更"
REMOVE_CATEGORY = "分類を削除"
LOAD = "読み込む"
LOAD_ACTION = "keymap_set_history.load_action"
REMOVE_ENTRY = "履歴から削除"
COPY_ENTRY = "分類へコピー…"
CLOSE = "閉じる"
CHOOSER_TITLE = "コピー先の分類"
OK = "OK"
CANCEL = "キャンセル"
NO_CATEGORIES = "分類がありません。先に分類を追加してください。"
INVALID_CATEGORY_NAME = "keymap_set_history.invalid_category_name"
RENAME_REJECTED = "keymap_set_history.rename_rejected"
CATEGORY_NOT_FOUND = "keymap_set_history.category_not_found"
COPY_REJECTED = "keymap_set_history.copy_rejected"
ENTRY_NOT_FOUND = "keymap_set_history.entry_not_found"


def format_entry_name(path: str, *, exists: bool) -> str:
    """名前列 = 拡張子なしのファイル名。不在なら接尾辞を付す。"""
    name = PureWindowsPath(path).stem
    return name if exists else tr("keymap_set_history.entry_name_missing", name=name)


def format_edit_error(reason: str) -> str:
    return tr("keymap_set_history.edit_error", reason=reason)


def format_open_error(reason: str) -> str:
    return tr("keymap_set_history.open_error", reason=reason)


def confirm_remove_category(name: str) -> str:
    return tr("keymap_set_history.confirm_remove_category", name=name)


def confirm_remove_entry(path: str) -> str:
    return tr("keymap_set_history.confirm_remove_entry", path=path)
