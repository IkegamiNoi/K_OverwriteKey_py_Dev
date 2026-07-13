# V5: レイアウト系の付け替えと委譲削除

- 実施日: 2026-07-06

## 付け替えた参照元

- **views.py**: `command=app.open_keyboard_window`→`app.layout.open_keyboard_window`（2）、`bind("<<ComboboxSelected>>", app.on_keyboard_layout_selected)`→`app.layout.on_keyboard_layout_selected`（2）。
- **app.py `_build_menu`**: レイアウト系メニュー 4 項目（open_keyboard_window / add_external_keyboard_layout / delete_keyboard_layout / toggle_keyboard_show_physical_key_labels）を `self.layout.*` へ。
- **app.py `__init__`**: `self._reload_keyboard_layouts()`→`self.layout.reload_keyboard_layouts()`。`KeyStateManager(resolve_scan_code=...)` と `InputRouter(resolve_scan_code=...)` は **ラムダ包み** `lambda sc: self.layout.resolve_key_name_from_scan_code(sc)`（生成時点で `self.layout` 未生成のため。実行時解決）。生成ブロックの位置は不動。
- **app.py `_sync_control_vars_from_data`**: `self._sync_keyboard_layout_controls()`→`self.layout.sync_keyboard_layout_controls()`。
- **app.py `on_close`**: `self.keyboard_window`（3 参照）→`self.layout.keyboard_window`。
- **各コントローラ**: `self._app._refresh_keyboard_window()`→`self._app.layout.refresh_keyboard_window()`（config_io 2 / hook 3 / keymap_panel 7 / trigger_panel 1）。hook_controller の `_resolve_key_name_from_scan_code` / `_should_debug_special_key_event` / `_debug_special_key_event`→`self._app.layout.*`。
- **tests_ui**: `self.app.open_keyboard_window()`→`self.app.layout.open_keyboard_window()`、`self.app.keyboard_window`（3）→`self.app.layout.keyboard_window`（アサーション不変）。

## 削除した App 委譲・プロパティ（計 12 def）

`keyboard_window`（property getter+setter） / `open_keyboard_window` / `_refresh_keyboard_window` / `_reload_keyboard_layouts` / `_sync_keyboard_layout_controls` / `toggle_keyboard_show_physical_key_labels` / `on_keyboard_layout_selected` / `add_external_keyboard_layout` / `delete_keyboard_layout` / `_resolve_key_name_from_scan_code` / `_should_debug_special_key_event` / `_debug_special_key_event`。

## 申し送り

- `keyboard_window` の setter を App 経由で使う箇所は存在しなかった（LayoutController 自身が `self.keyboard_window` を保持・更新）。よってプロパティ削除は安全。
- resolve_scan_code のラムダは `self.layout` が生成される前に定義されるが、呼び出しは実行時（フックイベント時）のため遅延解決で問題なし。
- app.py 行数: 779 → 741 行。

## 検証結果

- 削除対象の facade caller: 0 件
- compile OK / tests 59 OK / tests_ui 9 OK / SMOKE OK
- **手動確認（レイアウトコンボ切替 / キーボードUI開閉 / 外部レイアウト追加→削除）**: GUI 操作のため自動環境で実施不可。標準検証で代替、実機確認は要ユーザー。
