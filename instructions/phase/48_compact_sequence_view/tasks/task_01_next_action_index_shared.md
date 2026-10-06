# task_01_next_action_index_shared

## 目的

暫定 33 §4「次に実行の変更はフル表示と共有する 1 つの処理（行番号を受け取る）」の土台として、
`TriggerPanelController.on_action_list_select` から「行番号を受け取って次に実行にする」部分を抜き出す。
**フル表示の挙動は不変（純粋な抜き出し）。presentation 限定・domain / application 不変・スキーマ不変。**

## 対象範囲（presentation 限定・挙動不変）

### `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`

- 新しい公開メソッド `set_next_action_index(self, idx: int) -> bool` を追加する。中身は今の `on_action_list_select`（:583-618）のうち、一覧（Listbox）に依存しない部分:
  1. `selected_trigger_is_effective()` が偽なら False
  2. `selected_trigger_key()` → `_find_trigger_by_key` → `actions` が空 / 見つからなければ False
  3. `0 <= idx < len(actions)` でなければ False
  4. `idx == self._app._indices.get(key, 0)` なら `update_status()` して False（変更なし）
  5. それ以外は `_indices[key] = idx` → `sequence_runner.reset_loop_frames(key)` → `refresh_actions()` → `update_status()` して True
- `on_action_list_select` は `_programmatic_action_select`・マウス押下中・複数選択の判定と `sync_listbox_selection_to_focus` による行番号の取得を今のまま行い、
  行番号が得られたら `set_next_action_index(idx)` を呼ぶ形に置き換える（呼ぶ順・条件・副作用はいまと同じになること）
- 呼び出し先の実行中の拒否（`_refuse_running_chain_callee_edit`）は**このメソッドに入れない**（フル表示のキー操作の経路は拒否しない現状を変えないため・暫定 33 §11）。省略表示側からの呼び出しで拒否を通すのは task_02
- ファイルは 633 行（M1 の 600 行超）。**行数を増やさない方向で**抜き出す（重複を残さない）

### `tests_ui/test_sequence_list_operations.py`（既存へ追加）

- `set_next_action_index` を直接呼ぶテスト: ①有効なトリガーで別の行を渡すと `_indices` が変わり `▶` がその行へ動く ②同じ行なら `_indices` は変わらない
  ③範囲外の行番号では何もしない ④有効でない（グレーの）トリガーでは何もしない。既存テストの setUp・トリガーの作り方に合わせる

## 読むファイル

- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:82-110, 133-150, 264-330, 583-627`
- `tests_ui/test_sequence_list_operations.py`（冒頭の setUp と「次に実行」を確かめている既存テスト・:101 付近）

## 含まない

- 省略表示のシーケンス欄・その一覧からの呼び出し・呼び出し先の実行中の拒否の配線（task_02）
- 高さ・開閉・保存（task_03）/ ウィンドウの大きさ（task_04）
- `trigger_panel_controller.py` の分割（必要なら `/refactor_check` で判定）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests_ui` clean
- `tests_ui/test_sequence_list_operations.py` 全件 pass（追加 4 件を含む）
- tests（`unittest discover -s tests`）・tests_ui 全体・`-m tests.smoke_app` pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（重点: フル表示の `on_action_list_select` の挙動が不変か）
- 実機目視: なし（task_05 でまとめて実施）
