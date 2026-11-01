"""構成セット履歴の表示文言（I/O を行わない）。"""

from pathlib import PureWindowsPath
from keyseq.shared.i18n import tr

RECENT_NODE_LABEL = "keymap_set_history.recent_node_label"
READ_ONLY_NOTICE = "keymap_set_history.read_only_notice"
TITLE = "keymap_set_history.title"
NAME_HEADING = "keymap_set_history.name_heading"
PATH_HEADING = "keymap_set_history.path_heading"
CATEGORY_LABEL = "keymap_set_history.category_label"
ADD_CATEGORY = "keymap_set_history.add_category"
RENAME_CATEGORY = "keymap_set_history.rename_category"
REMOVE_CATEGORY = "keymap_set_history.remove_category"
LOAD = "keymap_set_history.load"
LOAD_ACTION = "keymap_set_history.load_action"
REMOVE_ENTRY = "keymap_set_history.remove_entry"
COPY_ENTRY = "keymap_set_history.copy_entry"
CLOSE = "keymap_set_history.close"
CHOOSER_TITLE = "keymap_set_history.chooser_title"
OK = "common.ok"
CANCEL = "common.cancel"
NO_CATEGORIES = "keymap_set_history.no_categories"
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
