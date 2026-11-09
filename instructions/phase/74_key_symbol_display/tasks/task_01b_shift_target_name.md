# task_01b_shift_target_name

## 目的

正本 `key_input.md`「キーボードUI の置換先の Shift 付きの記号」を実装する。JIS で Shift+¥ / Shift+ろ を置換先に記録したとき、`yen` / `ro` ではなく `bar` / `underscore` で保存し、枠に `|` / `_` と出す。

## 対象範囲

### `keyseq/infrastructure/win32_window.py`

- `is_shift_down() -> bool` を `is_mouse_button_down` と同じ形で追加する（`GetAsyncKeyState(VK_SHIFT = 0x10) & _KEY_DOWN`・`_guarded`）。

### `keyseq/presentation/keyboard_window.py`

- モジュール定数 `_SHIFTED_TARGET_NAMES = {"yen": "bar", "ro": "underscore"}`。
- `_record_key` で、`esc` / 修飾キー / 空の判定の後、`callback` を呼ぶ前に、`key` が表にあり `win32_window.is_shift_down()` が真なら表の名前へ置き換える。`_record_key` は Tk とフックの両経路が通る。

### テスト

`tests_ui/test_keyboard_window_scan_code.py` に追加（`_record_key` を `SimpleNamespace` か既存の手本の形で呼ぶ）:
- Shift あり: `yen` → `bar`、`ro` → `underscore` で `_on_assign_keymap` が呼ばれる
- Shift なし: `yen` / `ro` のまま
- Shift ありでも表に無いキー（`a`）はそのまま

## 読むファイル

- `instructions/common/spec_detail/key_input.md` の該当項
- `keyseq/presentation/keyboard_window.py:610-629`
- `keyseq/infrastructure/win32_window.py:269-280`
- `tests_ui/test_keyboard_window_scan_code.py`

## 含まない

- `key_capture_hook.py`・他の記録の入口（トリガー・key_hold・キーマップ編集・切替 / 停止 / トグル）
- 送信の変更（Shift を付けない）
- 表示の表の変更（`minus` の追加〔36 個〕だけは同じコミットで別途メインが実施）

## 確認

- `tests_ui.test_keyboard_window_scan_code`・`tests_ui.test_capture_hook_entries`・`tests_ui.test_keyboard_key_text`・`tests.test_key_symbols` が pass

## 完了条件

上記 pass・reviewer 採用。実機目視は task_02。
