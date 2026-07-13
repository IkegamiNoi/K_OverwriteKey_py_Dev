# V4: 保存・読込系の付け替えと委譲削除

- 実施日: 2026-07-06

## 付け替えた参照元

- **views.py**: ファイル系ボタン 13 箇所を `command=app.config_io.<名前>` へ（new_config / save_keymap_set / save_as / load_keymap_set_from / save_selected_keymap(_as) / load_keymap_file / save_trigger_set_file(_as) / load_trigger_set_file / save_selected_sequence(_as) / load_sequence_file）。
- **app.py `_build_menu`**: メニュー 8 項目を `self.config_io.<名前>` へ。ショートカットハンドラ 4 箇所（new/save/save_as/load）も同様。`on_close` の `_confirm_save_if_dirty`→`config_io.confirm_save_if_dirty`、`set_ui_font_delta` の `_write_startup`→`config_io.write_startup`、`__init__` の `_resolve_startup_path`/`_resolve_keymap_set_path`→`self.paths.*`、`_update_file_status` の `_has_unsaved_changes`→`dirty_tracker.*`、`open_preset_manager` の `_set_dirty`→`dirty_tracker.set_dirty`。
- **config_io_controller.py**: パス系（`_preferred_*` / `_json_dialog_initial_dir` / `_filename_stem` / `_suggest_json_path` / `_resolve_keymap_set_path` / `_normalize_keymap_set_save_path` / `_to_config_relative_or_absolute` / `_is_within_config_root`）→`self._app.paths.*`、ダーティ系（`_set_dirty` / `_has_unsaved_changes` / `_sync_dirty_state` / `_clear_individual_dirty_flags` / `_mark_trigger_set_dirty` / プロパティ `_trigger_set_*`）→`self._app.dirty_tracker.*`、維持3メソッド→`self._app.suggest_keymap_set_dialog_path` 等（公開名）。計 67 置換。
- **keymap_panel_controller.py / key_capture.py**: `self._app._set_dirty`→`self._app.dirty_tracker.set_dirty`。
- **trigger_panel_controller.py**: `self._app._mark_trigger_set_dirty`→`self._app.dirty_tracker.mark_trigger_set_dirty`。
- **layout_controller.py**: パス系→`paths.*`、`_set_dirty`→`dirty_tracker.set_dirty`、`_resolve_keylayout_dir`→`paths.resolve_keylayout_dir`、`_to_rel_if_possible`→`paths.to_rel_if_possible`、`save_keymap_set`→`self._app.config_io.save_keymap_set`。

## 削除した App 委譲（計 50 def = メソッド44 + プロパティ3×getter/setter6）

- パス系純委譲 18、ダーティ系 9（プロパティ3含む）、ConfigIO 系 20（`_confirm_save_if_dirty` / `_write_startup` / `_apply_loaded_data_to_ui` / new_config / save_keymap_set / save_as / load_keymap_set_from / import_config / export_config / restore_default / set_startup_keymap_set / save_selected_keymap(_as) / load_keymap_file / save_trigger_set_file(_as) / load_trigger_set_file / save_selected_sequence(_as) / load_sequence_file）。

## App に残した（§1.4・削除禁止）

- 状態依存で引数詰め替えのある 3 メソッドを**公開名化して残置**: `suggest_keymap_set_dialog_path` / `suggest_keymap_set_dialog_dir` / `keymap_set_file_stem`（いずれも `self.keymap_set_path` を詰め替えて `self.paths.*` へ委譲）。
- ダーティ調整役 `mark_keymap_dirty` / `mark_sequence_dirty`（V1 で公開名化済み。デフォルト対象解決を含むため残置）。

## 未使用だったため削除した facade（呼び出し元 0）

`_preferred_keymap_sets_dir` / `_legacy_settings_dir` / `_is_within_legacy_settings` / `_has_individual_dirty` / `_apply_loaded_data_to_ui`。

## 補足・申し送り

- config_io_controller.py 内の `self.save_keymap_set` / `self.save_as` / `self.save_selected_keymap_as` / `self.save_trigger_set_file_as` / `self.save_selected_sequence_as` は**同コントローラ自身のメソッド**、`self._app.config_service.*` は **ConfigService** であり、いずれも App facade ではないため付け替え対象外（誤変換していないことを grep で確認済み）。
- 削除で孤立したセクションコメント `# --- Individual JSON IO ---` / `# --- Config IO ---` を除去（実体を伴わないコメントのみ削除、挙動非関与）。
- app.py 行数: 991 → 779 行。

## 検証結果

- 削除対象の残存呼び出し: 0 件（付け替え前に全 delete-target を grep 確認）
- compile OK / tests 59 OK / tests_ui 9 OK / SMOKE OK
- **手動確認（計画02 S6 の一巡: 新規→トリガー追加→保存→読込→Export→Import→別名保存）**: GUI 操作のため自動環境で実施不可。標準検証で代替、実機確認は要ユーザー。
