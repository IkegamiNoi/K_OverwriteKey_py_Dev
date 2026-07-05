# V7: トリガー/シーケンスパネル系の付け替えと委譲削除

- 実施日: 2026-07-06

## 付け替えた参照元

- **views.py**: トリガー/アクション Listbox の bind 計 6 種とボタン群を `app.trigger_panel.<公開名>` へ。`move_action` は `lambda: app.trigger_panel.move_action(-1)` の形（元のラムダ構造を維持）。`update_run_to_end_delay` の `<Return>`/`<FocusOut>` bind も付け替え。
- **app.py `__init__`（SequenceRunner 配線）**: `select_trigger`/`refresh_actions`/`update_status` を**ラムダ包み**へ（`lambda key: self.trigger_panel.select_trigger_by_key(key)` 等。計画指示どおり。trigger_panel は sequence_runner より前に生成されるが、計画の指示に従い一貫してラムダ化）。
- **app.py 本体**: `__init__` / `show_full_view` / `show_compact_view` の `_refresh_triggers` / `_refresh_actions` / `_update_status` / `_sync_trigger_selection_to_views` を `self.trigger_panel.*` へ。`mark_sequence_dirty`（調整役）内の `self._selected_trigger()`→`self.trigger_panel.selected_trigger()`。
- **各コントローラ（config_io / hook / keymap_panel）**: `self._app._refresh_triggers` / `_refresh_actions` / `_update_status` / `_selected_trigger`→`self._app.trigger_panel.*`。
- **tests_ui**: V1 で付け替え済み（refresh_triggers / refresh_actions / update_status / set_selected_trigger_index）。追加変更なし。

## 削除した App 委譲（計 22 def）

`add_trigger` / `rename_trigger` / `delete_trigger` / `update_suppress` / `update_run_to_end` / `update_run_to_end_delay` / `add_action` / `edit_action` / `delete_action` / `move_action` / `_on_trigger_list_focus_index_change` / `_on_trigger_double_click` / `_on_action_list_select` / `_on_action_list_focus_index_change` / `_on_action_double_click` / `_refresh_triggers` / `_refresh_actions` / `_update_status` / `_set_selected_trigger_index` / `_select_trigger_by_key` / `_selected_trigger` / `_sync_trigger_selection_to_views`。

## 申し送り

- `sequence_runner.py` の `self._refresh_actions` / `self._update_status` は SequenceRunner 自身のコンストラクタ引数・フィールドであり App facade ではないため対象外。
- 削除で孤立した連続セクションコメント（Trigger selection/helpers / run_to_end UI sync/update / Trigger CRUD / Actions CRUD）を除去。
- app.py 行数: 689 → 639 行。

## 検証結果

- 削除対象の facade caller: 0 件
- compile OK / tests 59 OK / tests_ui 9 OK / SMOKE OK
- **手動確認（トリガー追加/変更/削除、アクション追加/編集/削除/上下移動、suppress・連続実行・間隔(ms)、フル⇔省略の選択共有）**: GUI 操作のため自動環境で実施不可。標準検証で代替、実機確認は要ユーザー。
