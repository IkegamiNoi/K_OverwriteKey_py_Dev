# V2: フック制御系の付け替えと委譲削除

- 実施日: 2026-07-06

## 付け替えた参照元

- **views.py**: `command=app.toggle_hook`→`app.hook.toggle_hook`（Full/Compact 各1）、`command=app.toggle_triggers_enabled`→`app.hook.toggle_triggers_enabled`（同）。
- **dialogs.py**: `self.parent.suspend_hook_for_dialog()`→`self.parent.hook.suspend_hook_for_dialog()`（5）、resume（5）。
- **keyboard_window.py**: `hasattr(self.master, "suspend_hook_for_dialog")`→`hasattr(self.master, "hook")` ガードへ変更し、`self.master.hook.suspend_hook_for_dialog()` / `resume` に。ガードの有無という挙動は維持。
- **key_capture.py / config_io_controller.py / keymap_panel_controller.py**: `self._app.suspend/resume_hook...`→`self._app.hook.suspend/resume_hook...`。
- **keymap_panel_controller.py**: `self._app.hook_active` / `self._app.custom_input_enabled`→`self._app.hook.*`。
- **trigger_panel_controller.py**: `self._app.start_hook()`→`self._app.hook.start_hook()`（4）、`self._app.hook_active`（5）/ `custom_input_enabled`（1）→`self._app.hook.*`。
- **App.__init__ 配線**（生成順の都合で全てラムダ包み。生成ブロックの位置は不動）:
  - `on_stop_hook=self.stop_hook`→`lambda: self.hook.stop_hook()`
  - `on_toggle_mode=self.toggle_custom_input_enabled`→`lambda: self.hook.toggle_custom_input_enabled()`
  - `on_action_error=... self._show_action_error(...)`→`... self.hook.show_action_error(...)`
  - `get_hook_pause_count=self._get_hook_pause_count`→`lambda: self.hook.get_hook_pause_count()`
  - `get_custom_input_enabled=lambda: bool(self.custom_input_enabled)`→`lambda: bool(self.hook.custom_input_enabled)`
- **App 本体**: `__init__` の `self._sync_hook_toggle_buttons()`→`self.hook.sync_hook_toggle_buttons()`、`on_close` の `self.stop_hook()`→`self.hook.stop_hook()`。
- **tests_ui**: `self.app.suspend_hook_for_dialog()`→`self.app.hook.suspend_hook_for_dialog()`、resume（アサーション不変。`get_hook_pause_count` は V1 で付け替え済み）。

## 削除した App 委譲・プロパティ（計 11）

`hook_active`（prop） / `custom_input_enabled`（prop） / `suspend_hook_for_dialog` / `resume_hook_after_dialog` / `_get_hook_pause_count` / `_sync_hook_toggle_buttons` / `start_hook` / `stop_hook` / `toggle_hook` / `toggle_custom_input_enabled` / `toggle_triggers_enabled` / `_show_action_error`。

- `_sync_trigger_toggle_buttons` / `_validate_hook_configuration` の App ファサードは計画02時点で存在せず（HookController のみ保持）、削除対象なし。

## 申し送り

- `key_capture.py:11` のドックストリング内に `App.suspend_hook_for_dialog / resume_hook_after_dialog` という記述が残るが、これは**呼び出しではなくコメント**であり、挙動説明として概念的に妥当なため変更しない（参照先付け替えは呼び出し箇所のみ対象）。
- `input_router.py` の `_get_hook_pause_count`（コンストラクタ引数・フィールド）は InputRouter 自身のものであり App ファサードではないため対象外。

## 検証結果

- app.py に削除対象の def 残存: 0 件
- compile OK / tests 59 OK / tests_ui 9 OK / SMOKE OK
- **手動確認（フック6項目）**: GUI 操作を伴うため自動実行環境では実施不可。標準検証（compile/unittest/smoke）で代替。実機での最終確認は V9 に集約し、ユーザー側での確認を要する旨を明記。
