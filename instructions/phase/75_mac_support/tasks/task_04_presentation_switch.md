# task_04_presentation_switch

## 目的

暫定 57 §3.1〜§3.3 の段階 ① の最後。presentation に残る Windows 依存（`modal.py` の `WinDLL`・`tk_keys.py` のテンキー判定・`action_dialog.py` の `pynput`）を `os_backend` の裏へ移し、フックスレッドから UI スレッドへの受け渡しを注入できるようにする。AST テストの許可リストを空にする（§9-1）。

**レイヤ制約**: infrastructure の `os_backend/` と presentation のみ。domain / application 不変・JSON スキーマ不変・Windows の動作不変。テストの件数を減らさない（基準 tests 1967 / tests_ui 1270）。

## 対象範囲

### `os_backend/contracts.py`

- `TkKeyTranslator` に `numpad_name(self, keycode: object, state: object) -> str` を追加
- `MouseBackend` に `capture_next_click(self, on_capture: Callable[[float, float], None]) -> None` を追加（次の 1 回の押下の座標で、別スレッドから `on_capture` を 1 回呼ぶ。呼び出しは待たずに戻る）

### `os_backend/windows/`

- 新規 `tk_key_translator.py`: `tk_keys.py` の `_NUMPAD_NAMES_BY_KEYCODE` / `_NUMPAD_NAMES_BY_NON_EXTENDED_KEYCODE` と `numpad_name_from_tk_event` の本体を移す（ロジック不変）
- `backend.py`: `WindowsTkKeyTranslator.numpad_name` を上へ委譲
- `mouse_backend.py`: `capture_next_click` = `from pynput import mouse`（モジュール先頭）を使い、`on_click(x, y, button, pressed)` で `pressed` なら `on_capture(x, y)` を呼んで `False` を返し、そうでなければ `True` を返す `mouse.Listener` を `daemon = True` で開始する

### `keyseq/presentation/modal.py`

`ctypes` / `ctypes.wintypes` / `cache` と `_foreground_window_fn` を削除する。`_is_app_foreground` は次のとおり（捕捉する例外は現状のまま）:

```python
backend = get_backend().window
foreground = backend.foreground_own_window()
return foreground is not None and foreground == backend.window_handle(app)
```

### `keyseq/presentation/tk_keys.py`

テンキーの表を削除し、`numpad_name_from_tk_event(keycode, state)` は `get_backend().tk_keys.numpad_name(keycode, state)` を返す（呼び出し側は変えない）。

### `keyseq/presentation/dialogs/action_dialog.py`

`from pynput import mouse` を削除。`_capture_mouse_position` の `on_click` を `on_capture(x, y)` に変え（`after` の 4 回の予約と try / finally は変えない）、`get_backend().mouse.capture_next_click(on_capture)` を呼ぶ。

### `keyseq/presentation/controllers/hook_controller.py`（§3.2 ディスパッチャ）

- `HookController.__init__(self, app, dispatch: Callable[[Callable[[], None]], None] | None = None)`。`None` のときは `lambda callback: app.after(0, callback)`（Windows は `after` のまま）
- フックスレッドの経路 = `on_input_event` の予約（307 行付近）と `_schedule_make_only_routes`（333 行付近）の `self._app.after(0, ...)` だけを `self._dispatch(...)` に置き換える。他の `after` は変えない

### テスト（削除しない）

- `tests/test_os_backend_boundary.py`: 許可リストを空にする（`ALLOWLIST: set[tuple[str, str]] = set()`・テストは残す）
- `tests/test_os_backend_contracts.py`: 追加メンバーを反映（一致テストが検出する）
- `tests_ui/test_modal_app_foreground.py`: `modal._foreground_window_fn` の patch を、`modal.get_backend` が `window.foreground_own_window` / `window.window_handle` を持つ偽物を返す patch へ置き換える。`_foreground_window_fn` の `restype` 等を見ていたテスト（48〜58 行付近）は、同じ事実を `win32_window.foreground_own_window` の側で確かめる形へ付け替える（`tests/test_win32_window.py` に同じ検証が既にあるなら、`modal` が `ctypes.WinDLL` を呼ばないことの検証へ置き換える）
- `tests_ui/test_action_dialog_drag.py`: `pynput` を直接使う箇所を、`capture_next_click` の経路に合わせて付け替える
- 新規の小さなテスト: `capture_next_click`（`mouse_backend.mouse.Listener` を patch。press で `on_capture`・戻り値 False、release で True、daemon）/ `HookController` の既定の dispatch が `after(0, cb)` を呼び、注入した dispatch が予約の経路で使われること（`tests/test_hook_coordinator.py` か新規ファイル）
- `tests/test_tk_keys.py` は変更不要（Windows の実 backend を通る）

### `instructions/common/codebase_map.md`

141・183・390・824 行付近に反映する（テンキーの判定の実体・前面判定・クリック位置の取得）。

### 設計メモ / 制約

- 編集・移動は apply_patch（Python で編集しない）。`inspect` / 互換の `getattr` を足さない
- `TkKeyTranslator` の修飾 keysym は本タスクに含めない（Aqua の keysym の実測後に task_09 で扱う）

## 読むファイル

- `instructions/history/57_mac_support.md` §3.2
- `keyseq/infrastructure/os_backend/contracts.py`・`windows/backend.py`・`windows/mouse_backend.py`
- `keyseq/presentation/modal.py:1-32` / `tk_keys.py:1-50` / `dialogs/action_dialog.py:1-10,391-418`
- `keyseq/presentation/controllers/hook_controller.py:25-37,300-315,328-340`
- `tests_ui/test_modal_app_foreground.py` / `tests_ui/test_action_dialog_drag.py` / `tests/test_os_backend_boundary.py`

## 含まない

- macOS 側の実装とディスパッチャの実体（task_05・task_08）
- `TkKeyTranslator` の修飾 keysym（task_09）
- `spec_detail/` の更新（task_14）

## 確認

`..\..\..\.venv\Scripts\python.exe` で（verifier）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests`: 失敗 0・1967 件以上・skip 7
- `-m unittest discover -s tests_ui`: 失敗 0・1270 件以上
- `-m tests.smoke_app` が pass
- `git grep -n "ctypes\|pynput" -- keyseq/presentation` が 0 件

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 段階 ① の完了として、実機目視（IME オンの文字送信・キーの取得・キー置換とシーケンス・マウス操作とクリック位置の取得・キーボードUIの常に手前・カーソルグリッド・言語の再起動）をユーザーが行う。
