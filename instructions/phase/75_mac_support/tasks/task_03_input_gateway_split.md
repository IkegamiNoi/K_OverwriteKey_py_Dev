# task_03_input_gateway_split

## 目的

暫定 57 §3.2・§3.3 の段階 ① の 3 番目。`infrastructure/input_gateway.py` の Windows 依存（`keyboard`・`ctypes`・`pyautogui`）を `os_backend/windows/` の `KeyboardBackend` / `MouseBackend` へ移す。`InputGateway` は OS 非依存の窓口として残し、公開メソッドの契約を変えない（§3.2）。

**レイヤ制約**: infrastructure・`presentation/app.py`（1 行）・テスト。domain / application 不変・JSON スキーマ不変・Windows の動作不変。テストの件数を減らさない（基準 tests 1965 / tests_ui 1270）。

## 対象範囲

### `os_backend/contracts.py` に追加

- `@dataclass(frozen=True) class KeySend`: `kind: str` / `values: tuple[int, ...]` / `key: str`（`input_gateway.py` から移す。`kind` と `values` の中身は backend だけが解釈する不透明な値）
- `ResolveLayoutScanCode = Callable[[str], int | None] | None`
- `class KeyboardBackend(Protocol)`:
  - `register_global_hook(self, callback, *, suppress: bool = False) -> object`
  - `register_key_hook(self, key: str, callback, *, suppress: bool) -> object`
  - `unregister_hook(self, handle: object) -> None`
  - `resolve_send(self, key: str, resolve_layout_scan_code: ResolveLayoutScanCode) -> KeySend`（解決できなければ `ValueError`）
  - `press_send(self, send: KeySend) -> None` / `release_send(self, send: KeySend) -> None`
  - `identity_of(self, send: KeySend) -> tuple[int, bool]`
  - `needs_shift(self, send: KeySend) -> bool`
  - `press_shift(self) -> None` / `release_shift(self) -> None`
  - `send_native_hotkey(self, hotkey: str, keys: Sequence[str], resolve_layout_scan_code: ResolveLayoutScanCode) -> bool`（OS の一括送信で送れたら `True`。送らなかったら `False` を返し、呼び出し側が 1 キーずつ押す）
  - `write_text(self, text: str) -> None`
  - `repeat_timing(self) -> tuple[int, int]`
- `class MouseBackend(Protocol)`: `cursor_position` / `move_cursor` / `scroll_mouse` / `click_at` / `click_mouse` / `mouse_down` / `mouse_up` / `drag_mouse`（シグネチャは `InputGateway` の現在のものと同じ）
- `OsBackend` に `keyboard: KeyboardBackend` / `mouse: MouseBackend` を追加し、`__all__` に `KeySend` / `KeyboardBackend` / `MouseBackend` を追加

### 新規 `os_backend/windows/`

コードは `input_gateway.py` から**そのまま移す**（ロジック・定数・日本語コメントは変えない。ただし下の 1 点を除く）。

- `send_input.py`: `_KEYBDINPUT` / `_MOUSEINPUT` / `_INPUT_UNION` / `_INPUT`、`_INPUT_KEYBOARD` / `_INPUT_MOUSE`、`_send_input_api`
- `keyboard_backend.py`: `_EXTENDED_KEYS`、`_KEYEVENTF_*`、`_SPI_*`、`_DEFAULT_REPEAT_*`、`_needs_shift`、`repeat_delay_ms`、`repeat_interval_ms`、`_read_keyboard_setting`、`_resolve_extended_key`、`_send_extended_event`、`_send_numpad_event`、`class WindowsKeyboardBackend`
  - `resolve_send`: 現在の `_resolve_key` の順序のまま
  - `needs_shift`: `send.kind == "keyboard" and _needs_shift(send.key)`
  - `send_native_hotkey`: 現在の `send_hotkey` の `all_keyboard` の判定と `keyboard.send`
  - `repeat_timing`: 現在の `keyboard_repeat_timing` から `sys.platform` の分岐を除いたもの
- `mouse_backend.py`: `_MOUSEEVENTF_*`、`_build_wheel_inputs`、`class WindowsMouseBackend`（現在の `InputGateway` のマウス系メソッド）
- `backend.py`: `create_backend` に `keyboard` / `mouse` を追加

### `keyseq/infrastructure/input_gateway.py`

- `ctypes` / `sys` / `wintypes` / `cache` / `keyboard` / `pyautogui` の import と移した定義を削除する
- `InputGateway` の公開メソッドは名前・シグネチャを維持し、`get_backend().keyboard` / `.mouse` へ委譲する。`_resolve_key` は廃止し `resolve_send` に統一する
- `send_mapped_key`: `send = self.resolve_send(key)`、続いて `kb.needs_shift(send) and not window.is_shift_down() and not window.is_ctrl_alt_win_down()`（評価の順序を変えない）で `press_shift` → press / release → `finally` で `release_shift`
- `send_hotkey`: `keys` を作り `kb.send_native_hotkey(...)` が `True` なら戻る。`False` なら現在の 1 キーずつの押下と解放・例外の扱いをそのまま残す。`resolve_send` の `ValueError` は `send_native_hotkey` の中で `False` にする
- `write_text`: 空文字は `kb.write_text(text)` のみ。IME の予約と復元は現在どおり `InputGateway` に残す
- `validate_key_name`: `self.resolve_send(key_name)`
- モジュール関数 `keyboard_repeat_timing()`: `get_backend().keyboard.repeat_timing()`

### `keyseq/presentation/app.py`

`App.__init__` の `super().__init__()` より**前**に `backend = get_backend()` を置き、次の趣旨の英語コメントを付ける: the backend import loads pyautogui, which makes the process DPI aware; it must happen before Tk creates its first window。既存の `window_backend = get_backend().window` はこの `backend` を使う。

### テスト（削除しない）

- `tests/test_os_backend_boundary.py`: 許可リストから `input_gateway.py` の 2 項目を消す
- `tests/test_os_backend_contracts.py`: `KeyboardBackend` / `MouseBackend` と Windows 実装の一致を追加。`keyseq/presentation/app.py` を AST で読み、`App.__init__` で `get_backend` の呼び出しが `super().__init__()` より前の行にあることを確かめるテストを追加
- `tests/test_input_gateway_send.py` / `_repeat.py` / `_scroll.py` / `_drag.py` / `_screen_grid.py`: `input_gateway.<移した名前>` の patch と参照を、`keyboard_backend` / `mouse_backend` / `send_input` の該当モジュールへ付け替える。`_resolve_key` の呼び出しは `resolve_send` へ。`assertLogs` のロガー名は実際にログを出すモジュールに合わせる
- `tests/test_input_gateway_repeat.py` の `input_gateway.sys` の patch（非 Windows の既定値の検証）は「設定を読めない（`_read_keyboard_setting` が `None`）ときは既定値」の検証へ置き換える

### `instructions/common/codebase_map.md`

814・823・872・891 行付近に、実体が `os_backend/windows/keyboard_backend.py` / `mouse_backend.py` にあることを反映する。

### 設計メモ / 制約

- 編集・移動は apply_patch（Python で編集しない）。`inspect` / 互換の `getattr` を足さない
- 新規クラスのコメントは英語でよいが、移動するコードの既存コメントはそのまま
- `test_no_japanese_ui_literals.py` が移動後のコードで失敗しないこと（文字列リテラルの追加なし）

## 読むファイル

- `instructions/history/57_mac_support.md` §3.2
- `keyseq/infrastructure/input_gateway.py`
- `keyseq/infrastructure/os_backend/`（contracts・`windows/backend.py`）
- `tests/test_input_gateway_*.py`
- `tests/test_os_backend_contracts.py` / `tests/test_os_backend_boundary.py:1-20`

## 含まない

- `action_dialog.py` のクリック位置の取得（task_04）・`modal.py`・`tk_keys.py`・ディスパッチャ（task_04）
- macOS の実装（task_05 以降）
- `spec_detail/` の更新（task_14）

## 確認

`..\..\..\.venv\Scripts\python.exe` で（verifier）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests`: 失敗 0・1965 件以上・skip 7
- `-m unittest discover -s tests_ui`: 失敗 0・1270 件以上
- `-m tests.smoke_app` が pass
- `git grep -n "^import keyboard\|^import pyautogui\|^import ctypes" -- keyseq/infrastructure/input_gateway.py` が 0 件

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は段階 ① の完了時にまとめて行う（キー置換・シーケンス・文字送信・マウス操作）。
