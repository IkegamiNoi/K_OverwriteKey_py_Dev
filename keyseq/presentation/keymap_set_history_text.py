"""構成セット履歴の表示文言（I/O を行わない）。"""

from pathlib import PureWindowsPath

RECENT_NODE_LABEL = "直近（最大 20 件）"
MISSING_SUFFIX = "（見つかりません）"
READ_ONLY_NOTICE = "履歴ファイルを読み込めませんでした。編集できません。"
TITLE = "構成セットの履歴"
NAME_HEADING = "名前"
PATH_HEADING = "パス"
CATEGORY_LABEL = "分類名"
ADD_CATEGORY = "＋分類を追加"
RENAME_CATEGORY = "分類名を変更"
REMOVE_CATEGORY = "分類を削除"
LOAD = "読み込む"
LOAD_ACTION = "読込"
REMOVE_ENTRY = "履歴から削除"
COPY_ENTRY = "分類へコピー…"
CLOSE = "閉じる"
CHOOSER_TITLE = "コピー先の分類"
OK = "OK"
CANCEL = "キャンセル"
NO_CATEGORIES = "分類がありません。先に分類を追加してください。"
INVALID_CATEGORY_NAME = "分類名が空か、同名の分類が既にあります。"
RENAME_REJECTED = "分類が存在しないか、分類名が空または同名です。"
CATEGORY_NOT_FOUND = "分類が存在しません。"
COPY_REJECTED = "分類が存在しないか、分類内に既に同じ構成セットがあります。"
ENTRY_NOT_FOUND = "履歴の項目が存在しません。"


def format_entry_name(path: str, *, exists: bool) -> str:
    """名前列 = 拡張子なしのファイル名。不在なら接尾辞を付す。"""
    return PureWindowsPath(path).stem + ("" if exists else MISSING_SUFFIX)


def format_edit_error(reason: str) -> str:
    return f"履歴を編集できませんでした: {reason}"


def format_open_error(reason: str) -> str:
    return f"構成セットを読み込めませんでした: {reason}"


def confirm_remove_category(name: str) -> str:
    return f"分類「{name}」を配下の履歴ごと削除しますか？\n実ファイルは削除しません。"


def confirm_remove_entry(path: str) -> str:
    return f"この項目を履歴から削除しますか？\n{path}\n実ファイルは削除しません。"
