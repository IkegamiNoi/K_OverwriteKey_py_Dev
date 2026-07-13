# V8: 残存委譲の総ざらいと Listbox ヘルパの直接使用化

- 実施日: 2026-07-06

## 実施内容

1. **Listbox ヘルパ**: App 委譲 `_focused_listbox_index` / `_sync_listbox_selection_to_focus` は**呼び出し元 0 件**だった（keymap_panel_controller / trigger_panel_controller は既に `listbox_utils` のモジュール関数 `focused_listbox_index(self._app, ...)` / `sync_listbox_selection_to_focus(self._app, ...)` を直接呼んでいる）。App の 2 委譲を削除し、app.py の未使用 import（`from keyseq.presentation.listbox_utils import (...)`）も除去。
2. **総ざらい**: `grep -nE "return self\.(config_io|dirty_tracker|hook|layout|keymap_panel|trigger_panel|stop_key_capture|toggle_key_capture|paths)\."` と全 def の目視により残存委譲を確認。**コントローラへの純委譲は残っていない**。

## 残した委譲・薄ヘルパとその理由（§1.4「App に残すメソッド」該当）

- **状態依存で引数詰め替えあり（3）**: `suggest_keymap_set_dialog_path` / `suggest_keymap_set_dialog_dir` / `keymap_set_file_stem` — いずれも `self.keymap_set_path` を詰め替えて `self.paths.*` へ委譲。V4 で公開名化済み。
- **配線用薄ヘルパ（5）**: `_get_send_guard_count`（`action_executor.send_guard_count` を int 化）/ `_perform_action`（`action_executor.execute`）/ `_find_trigger_by_key` / `_find_keymap_target` / `_find_keymap_switch_target_id`（`trigger_service`/`keymap_service` へ。InputRouter/SequenceRunner に配線）。
- **調整役（6）**: `mark_keymap_dirty` / `mark_sequence_dirty`（デフォルト対象解決）、`toggle_stop_key_capture` / `start_stop_key_capture` / `toggle_toggle_key_capture` / `start_toggle_key_capture`（キャプチャ相互排他）。
- **状態互換エイリアス（2 プロパティ）**: `_selected_trigger_idx` / `_indices` — `self.state`（AppState）への委譲。§1.4 で `state` は「現状のまま」と明記された外部契約であり、コントローラ委譲ではないため残置。

## 検証結果

- compile OK / tests 59 OK / tests_ui 9 OK / SMOKE OK
- app.py 行数: 639 → 629 行。
