# V6: キーマップパネル系の付け替えと委譲削除

- 実施日: 2026-07-06

## 付け替えた参照元

- **views.py**: キーマップ Listbox の bind 3 箇所（`_on_keymap_list_select` / `_on_keymap_list_focus_index_change` / `_on_keymap_list_double_click`）とボタン 4 箇所（`_add_keymap` / `_edit_selected_keymap` / `_delete_keymap` / `_select_keymap`）を `app.keymap_panel.<公開名>` へ。
- **app.py `__init__`**: `on_select_keymap=lambda keymap_id: self.activate_keymap_by_id(...)`→`self.keymap_panel.activate_keymap_by_id(...)`。
- **layout_controller.py**: KeyboardWindow 配線 `on_assign_keymap=self._app.assign_keymap_from_keyboard_ui`→`self._app.keymap_panel.assign_keymap_from_keyboard_ui`、`on_clear_keymap`→`self._app.keymap_panel.clear_keymap_from_keyboard_ui`。
- **config_io_controller.py**: `self._app._refresh_keymap_list_ui(...)`→`self._app.keymap_panel.refresh_keymap_list_ui(...)`（2）、`self._app._selected_keymap_list_index()`→`self._app.keymap_panel.selected_keymap_list_index()`。
- **trigger_panel_controller.py**: `self._app._refresh_keymap_list_ui()`→`self._app.keymap_panel.refresh_keymap_list_ui()`、`self._app._get_active_keymap_text()`→`self._app.keymap_panel.get_active_keymap_text()`。
- **tests_ui**: `refresh_keymap_list_ui` は V1 で付け替え済み。追加変更なし。

## 削除した App 委譲（計 13 def・連続ブロック 497-547 を一括削除）

`_selected_keymap_list_index` / `_refresh_keymap_list_ui` / `_on_keymap_list_select` / `_on_keymap_list_focus_index_change` / `_on_keymap_list_double_click` / `_add_keymap` / `_delete_keymap` / `_select_keymap` / `_edit_selected_keymap` / `activate_keymap_by_id` / `_get_active_keymap_text` / `assign_keymap_from_keyboard_ui` / `clear_keymap_from_keyboard_ui`。

- 直前の `_find_keymap_switch_target_id`（配線用薄ヘルパ・§1.4）と直後の `_select_trigger_by_key`（V7 対象）は残置。

## 検証結果

- 削除対象の facade caller: 0 件
- compile OK / tests 59 OK / tests_ui 9 OK / SMOKE OK
- app.py 行数: 741 → 689 行。
- **手動確認（キーマップ追加→変更→選択→削除 / キーボードUI上の左クリック割当・右クリッククリア）**: GUI 操作のため自動環境で実施不可。標準検証で代替、実機確認は要ユーザー。
