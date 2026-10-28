# task_06a_cursor_grid_terms

## 目的

「画面の枠」の呼び名を、機能・全体 = **カーソルグリッド** / 区画 = **マス** に改める（暫定 53 §13・ユーザー確定 2026-10-28）。
画面に出る文字列・ログ・ヘルプ本文・テストの期待値だけを変える。**識別子・ファイル名・JSON のキーと値・ヘルプの id は不変。スキーマ不変。**
正本 `spec_detail/`・`codebase_map.md` は直さない（task_08）。

## 対象範囲（文字列限定・挙動不変）

### domain（検査のメッセージ）

- `keyseq/domain/screen_grid/assignment.py`（:122・:130）・`normalize.py`（:99）・`ops.py`（:102・:109・:111）: 区画を指す「枠」→「マス」（§13.2）。

### presentation（画面の文字列・ログ）

- `keyseq/presentation/dialogs/keymap_edit_dialog.py`（:82・:86・:120）・`keymap_switch_batch_dialog.py`（:152）・`grid_editor_window.py`（:327・:343）
- `keyseq/presentation/screen_grid/grid_editor_panel.py`（:28・:57・:77・:104）・`grid_overlay_window.py`（:42）・`screen_grid_controller.py`（:88・:92・:93）
- 置き換えは §13.2 の表どおり。表に無いものは「全体ならカーソルグリッド・区画ならマス」。

### ヘルプ本文

- `keyseq/presentation/help/content/help_ja.json`: 大分類の題「画面の枠」→「カーソルグリッド」・本文の「枠」12 か所を §13.2 で置き換える（id 不変）。
  文として不自然になる箇所は最小限に言い換えてよい（意味を変えない）。
- 校正用の写し `instructions/phase/70_help_window/tools/help_ja_draft.md` も同じ内容に揃える。

### テストの期待値

- `tests/test_help_content.py`（:35 大分類の題）・`tests/test_screen_grid.py`（:238）・`tests/test_screen_grid_ops.py`（:98〜:104）
- `tests_ui/test_keymap_switch_batch_dialog.py`（:205・:228）
- 上記以外で、変えた文字列を期待値に持つテストがあれば追従する。

### 設計メモ / 制約

- **別の意味の「枠」は変えない**: 詳細表示の 3 枠（ペイン）・「ステータス」枠・表示枠・枠線・呼び出し枠
  （`tests/test_pane_width_rules.py`・`tests_ui/test_full_view_panes.py` 等の「枠」は対象外）。
- 「グリッド」だけに略さない（機能名は常に「カーソルグリッド」）。
- コメント・docstring は対象外（直さない）。

## 読むファイル

- `instructions/history/53_help_window.md` §13（全体）
- 上記の編集対象（該当行の前後のみ）
- `instructions/common/spec_detail/ui_terms.md` §2（用語表の書き方の参照のみ）

## 含まない

- 正本 `spec_detail/`（`ui_terms.md` A22 を含む）・`codebase_map.md` の更新（task_08）
- 識別子・ファイル名・JSON のキーの改名、コメント・docstring の書き換え
- 統合確認（task_07）・実機目視（task_08）

## 確認

- `grep -rn "枠" keyseq --include=*.py` の文字列リテラルに、カーソルグリッドを指す「枠」が残っていない（残るのは別の意味のものだけ）
- `help_ja.json` に「画面の枠」「枠」（カーソルグリッドの意味）が残っていない・写しの md と一致
- `tests.test_help_content`・`tests.test_screen_grid`・`tests.test_screen_grid_ops`・`tests_ui.test_keymap_switch_batch_dialog`・`tests_ui.test_grid_editor_window`・`tests_ui.test_help_window` pass（verifier）
- tests / tests_ui / smoke 全体 pass（verifier）

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: §13.2 どおりか / 別の意味の「枠」を巻き込んでいないか / 挙動・識別子の変更が無いか）
- 実機目視は task_08 でまとめて実施
