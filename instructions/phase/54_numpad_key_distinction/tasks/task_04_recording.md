# task_04_recording

## 目的

暫定 38（v0.5）§6 の記録。Tk のキーイベントの **keycode（Windows では VK）と拡張ビット（`event.state & 0x40000`）**でテンキーを判定し、表の名前（`num 1` 等）で記録する（keysym はテンキーでも主キーボードと同じため使えない・task_01 の probe）。実装後にユーザーの実機目視（§8 の 10〜12）。

## 対象範囲

### `keyseq/presentation/tk_keys.py`
- 純関数 `numpad_name_from_tk_event(keycode, state) -> str`（表の名前 or `""`）。拡張 = `int(state) & 0x40000` が非 0。
  - 拡張に関係なく: 96〜105 → `num 0`〜`num 9` / 110 → `num decimal` / 106 → `num multiply` / 109 → `num subtract` / 107 → `num add` / 111 → `num divide`
  - 13 かつ拡張あり → `num enter`（13 かつ拡張なしは `""` = 主 Enter）
  - **拡張なし**のときだけ: 45 → `num 0` / 35 → `num 1` / 40 → `num 2` / 34 → `num 3` / 37 → `num 4` / 12 → `num 5` / 39 → `num 6` / 36 → `num 7` / 38 → `num 8` / 33 → `num 9` / 46 → `num decimal`（拡張ありは本物の Insert / End / 矢印等 → `""`）
  - keycode / state が int に変換できなければ `""`
- イベントを受ける関数 2 つ（既存の keysym の関数の前に上を試す）:
  - `normalize_tk_key_event(event) -> str`: `numpad_name_from_tk_event(getattr(event, "keycode", None), getattr(event, "state", 0))` が空でなければそれ・空なら `normalize_tk_keysym(event.keysym)`
  - `normalize_key_hold_tk_key_event(event) -> str`: 同じく、空なら `normalize_key_hold_tk_keysym(event.keysym)`
- 既存の `normalize_tk_keysym` / `normalize_key_hold_tk_keysym` は残す（他の用途・テストのため）

### 記録の入口（イベントからキー名を決めている箇所を上の関数へ）
- `keyseq/presentation/dialogs/action_dialog.py`（:372・:389 の hotkey の記録。`_normalize_tk_key(event.keysym)` → イベントを渡す形へ）
- `keyseq/presentation/dialogs/action_key_hold_fields.py`（:185-189 の「1 キーを記録」。Escape の判定は keysym のまま）
- `keyseq/presentation/dialogs/trigger_dialog.py`（:105）・`keymap_edit_dialog.py`（:122）・`keymap_switch_batch_dialog.py`（:231。Escape の判定は keysym のまま）
- `keyseq/presentation/controllers/key_capture.py`（:129）
- `keyseq/presentation/keyboard_window.py` の `_normalize_tk_key`（:310）: 最初に `numpad_name_from_tk_event` を試し、空なら従来どおり（keysym の表 → レイアウトの keycode → keysym）
- 各所の `_normalize_tk_key(keysym)` の形のメソッドは、呼び出しを置き換えて不要になれば消してよい（他から呼ばれていないこと）。修飾キー・Escape・既存の挙動は変えない

### テスト
- `tests/` に `numpad_name_from_tk_event` の表（NumLock オン / オフ・拡張あり / なし・13・不正値）と 2 つのイベント関数（テンキーと主キーボードのイベント・keycode / state の無いイベント）の単体テスト（§8-8）
- `tests_ui/` の既存の記録のテストの形に合わせ、hotkey の記録・key_hold の「1 キーを記録」・トリガーの取得のうち少なくとも 2 か所で、keycode 97 のイベントが `num 1`・keycode 35 + 拡張ありが `end` になることを確かめる（偽のイベントに `keycode` / `state` を持たせる）
- 既存の記録のテストの偽イベント（`keycode` / `state` を持たないもの）がそのまま通ること

## 読むファイル

- `instructions/history/38_numpad_key_distinction.md` §2-6・§6・§8
- `instructions/phase/54_numpad_key_distinction/tasks/task_01_probe.md`（確認の 3）
- `keyseq/presentation/tk_keys.py`・上記の記録の入口の該当箇所・`keyseq/domain/numpad_keys.py`
- 既存の記録のテスト（`tests_ui/test_action_dialog_key_hold.py`・hotkey 記録 / トリガー取得のテスト等、`normalize_tk_keysym` や `keysym=` を grep して該当するもの）

## 含まない

- 入力の名前・送信（task_02・03 で完了）・組み込みのキーボード表示へのテンキーの追加（§2-7）・正本の改訂（task_06）

## 確認

- 上記テスト + 既存テスト（実行は verifier）・reviewer（5 観点）・ユーザーの実機目視（暫定 38 §8 の 10〜12）
