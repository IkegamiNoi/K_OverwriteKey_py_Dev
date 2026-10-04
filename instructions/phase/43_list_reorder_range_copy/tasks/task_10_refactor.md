# task_10_refactor

## 目的

`/refactor_check` の判定（推奨）で起票した提案書 18 を実施する（ユーザー判断 2026-10-04・同フェーズ末に実施）。**挙動不変・presentation 限定・スキーマ不変。**
提案書: `instructions/modified_proposal/18_refactor_list_reorder_range_copy.md`（項目 0〜3）

## 対象範囲

### 項目 1: `controllers/trigger_panel/trigger_panel_controller.py` → 新規 `controllers/trigger_panel/trigger_row_edit.py`

- `add_trigger` / `rename_trigger` / `_apply_trigger_rename` / `delete_trigger`（現 `:498-645` 付近）の本体を `TriggerRowEditFlow`（コンストラクタで controller を受ける）へ移す
- controller には `_action_edit` / `_trigger_edit` と同じ遅延生成のプロパティ `_trigger_row_edit` を足し、公開メソッド `add_trigger` 等は 1 行の委譲として残す（View・テストの呼び出し先を変えない）
- 移した本体が参照する controller の属性・メソッドは `self._panel.xxx` 経由にする（振る舞い・メッセージ文言・呼び出し順を変えない）
- テストが `trigger_panel_controller` モジュールの名前（`messagebox` / `TriggerDialog` 等）を patch していれば、patch 先を新モジュールへ追随する
- 完了の目安: controller が 600 行未満

### 項目 2: `dialogs/keymap_switch_batch_dialog.py`

- `__init__` の行の生成・スクロール領域・ボタンとバインドを `_build_row` / `_build_rows_area` / `_build_buttons`（名前は目安）へ切り出し、`__init__` を 40 行以下にする
- 属性（`key_entries` / `label_entries` / `key_vars` / `label_vars` / `capture_buttons` / `_row_frames` / `_canvas` / `_rows_frame` 等）の生成順と値は変えない

### 項目 3: 「範囲か下線の 1 行」の取得の共通化

- `presentation/listbox_range_drag.py` に `range_or_index(listbox, length, fallback_index, *, compact) -> tuple[int, int] | None`（提案書のスケッチどおり）を足す
- `keymap_list_edit.py` の `selection_bounds`・`trigger_list_edit.py` の `selection_bounds`・`action_edit.py` の `_selection_bounds` がこれを呼ぶ。
  `action_edit.py` は引数の形（`idx` を受ける）が違うため、合わなければその差を呼び出し側に残し、どうしても合わなければ 2 か所だけにする（理由を報告）
- `range_or_index` の単体テストを `tests_ui/test_listbox_range_drag.py` に足す（範囲あり / 範囲が長さ外 / compact で範囲を無視 / 代替の index が None・範囲外）

### 設計メモ / 制約

- 挙動・エラーメッセージ・保存結果を変えない。既存テストの期待値を変える修正はしない（patch 先の追随のみ可）
- 新規ファイルは所有者フォルダ（`controllers/trigger_panel/`）に置く（`file_organization_rules.md`）

## 読むファイル

- 提案書 `instructions/modified_proposal/18_refactor_list_reorder_range_copy.md`
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:30-60`・`:490-660`
- `keyseq/presentation/dialogs/keymap_switch_batch_dialog.py`（全体）
- `keyseq/presentation/listbox_range_drag.py:1-35`
- `keyseq/presentation/controllers/keymap_panel/keymap_list_edit.py:15-35`・`keyseq/presentation/controllers/trigger_panel/trigger_list_edit.py:15-35`・`keyseq/presentation/controllers/trigger_panel/action_edit.py` の `_selection_bounds` 周辺
- patch 先の確認: `grep -rn "trigger_panel_controller\." tests_ui tests`

## 含まない

- 提案書 18 以外の整理（別タスク化候補の `can_move` 削除・`KeymapEditDialog.validate` 削除・まとめて設定のダイアログの Escape の共通化）
- task_09 の残り（凍結・decisions_archive・current.md）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass
- `wc -l keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py` が 600 未満 / `KeymapSwitchBatchDialog.__init__` が 40 行以下

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視: なし（挙動不変・自動テストで確認）。
