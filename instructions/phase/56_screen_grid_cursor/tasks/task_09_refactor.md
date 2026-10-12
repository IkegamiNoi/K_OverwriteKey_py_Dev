# task_09_refactor

## 目的

[提案書 22](../../../modified_proposal/22_refactor_screen_grid.md)（ユーザー承認 2026-10-13・実施方法 (a)）の項目 1・2 を実施する。**挙動不変**（保存ファイルのバイト列・エラーメッセージを変えない）。

## 対象範囲

- 項目 1（M3・M4）: `domain/config.py` に keymap の「中身を解釈せずそのまま写す任意キー」の一覧 `KEYMAP_OPTIONAL_KEYS = ("grid",)` と `copy_keymap_optional_keys(source, target)`（`safe_deepcopy` で写す）を置き、次の 3 か所の 2 行をその呼び出しに置き換える:
  `application/config_service/__init__.py:182-183` / `application/config_service/split_loading.py:457-458` / `application/config_service/split_payloads.py:522-523`。
  `domain/config.py` の `_normalize_keymap_compat_fields` の `grid` の正規化（`normalize_grid` を通す）は変えない
- 項目 2（M6）: `domain/screen_grid/assignment.py:10-15` の `_LETTER_ROWS` を `AUTO_ASSIGN_ORDER`（`models.py:13`）の 10 文字ずつの切り出しで作る
- テスト: `copy_keymap_optional_keys` の単体テスト（キーがあれば深い写し・無ければ何もしない・入力を変えない）を `tests/test_domain_config.py` に追加。`_LETTER_ROWS` は既存の `reassign_top_keys` のテストで担保（追加不要）

## 読むファイル

- 提案書 22（全体）
- `keyseq/domain/config.py:1-20`・`:283-315`
- 上記 3 か所の前後 10 行・`keyseq/domain/screen_grid/assignment.py:1-20`・`models.py:1-20`

## 含まない

- 提案書 22 の「既知」の項目（色の重複・keymap_panel_controller の大きさ）/ それ以外のリファクタ

## 確認

- `grep -n '"grid" in' keyseq/application/config_service` が 0 件
- `compileall` / `discover -s tests` / `discover -s tests_ui`（1 本）/ `-m tests.smoke_app` が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**
