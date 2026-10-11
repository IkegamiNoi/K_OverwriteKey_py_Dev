# task_01_probe

## 目的

実装の前に、暫定 38 の前提（§4 の `is_keypad` とスキャンコード・§5 の送り方・§6 の Tk の keysym・§4 の偽の shift）を実測で確かめる。
コード不変（scratchpad の probe スクリプトのみ）。

## 対象範囲（probe のみ・コード不変）

- テスト用の Tk の Text を前面に出し、`SendInput` のスキャンコード入力（`KEYEVENTF_SCANCODE`・拡張は `KEYEVENTF_EXTENDEDKEY`）で §3 の表の 16 キーを NumLock オン / オフで送る
- 記録: keyboard のフックのイベント（`name`・`scan_code`・`is_keypad`・down / up）・Tk の `<KeyPress>` の keysym・Text に入った内容
- shift を押したまま `num 1`（NumLock オン）を送り、フックのイベント列（偽の shift の有無）と Text の結果を記録する
- NumLock は測定後に元の状態へ戻す

## 読むファイル

- `instructions/history/38_numpad_key_distinction.md` §3〜§6
- `keyseq/infrastructure/input_gateway.py:125-216`・`../../../.venv/Lib/site-packages/keyboard/_winkeyboard.py:442-529`

## 含まない

- 物理キーでの確認（task_04 の実機目視。合成のスキャンコード入力で偽の shift が再現しない場合は、そこで確かめる）

## 確認

- 結果を本節に追記し、暫定 38 の §4・§5・§6 と食い違えば改訂してユーザー確認
- 結果（2026-10-11・メイン実測・scratchpad の probe・合成の `SendInput` スキャンコード入力）:
  1. **フック**: 表の 16 キーは NumLock オン / オフとも `is_keypad` 真・スキャンコードは表どおり（名前は オン = `0`〜`9` / `decimal` / `*` / `-` / `+` / `/` / `enter`・オフ = `insert` / `end` / `down` / `page down` / `left` / `clear` / `right` / `home` / `up` / `page up` / `delete`）。
     主キーボードの `end` / `home` / `down` / `delete` / `insert`（拡張）・`enter` / `1` / `/` は `is_keypad` 偽 → **§4 の前提どおり**
  2. **送信**: `SendInput` の `KEYEVENTF_SCANCODE`（`/`・Enter は `KEYEVENTF_EXTENDEDKEY`）は NumLock に従う（オン = `0123456789.*-+/` と改行・オフ = 数字は入らず移動等）→ **§5 の第 1 案で確定**。NumLock の切替はスキャンコード入力（69・拡張）では効かず、VK（`keybd_event(0x90, ..., EXTENDEDKEY)`）で効いた（probe の都合・仕様には影響なし）
  3. **Tk の記録**: keysym に `KP_` は付かない（`1` / `End` / `period` / `asterisk` / `plus` / `minus` / `slash` / `Return` 等で主キーボードと同じ）。
     **keycode（VK）と state の `0x40000`（拡張）で 16 キーとも区別できる**: オン = VK 96〜105 / 110 / 106 / 109 / 107・`/` = 111（拡張）・Enter = 13（拡張）/ オフ = 45 / 35 / 40 / 34 / 37 / 12 / 39 / 36 / 38 / 33 / 46（拡張**なし**）。
     主キーボードは End / Home / Down / Delete / Insert = 拡張**あり**・Enter = 13（拡張なし）・`1` = 49・`/` = 191 → **§6 の keysym の変換案は使えず、keycode + 拡張ビットへ改訂（§2-6 の受容も不要）**
  4. **偽の shift**: shift を押したまま `num 1`（NumLock オン）で、フックは shift の down → shift の up（スキャンコード 554）→ `end`（79・`is_keypad` 真）→ shift の down → shift の up。Text は空（shift + End の選択）→ **§4 の受容どおり**（合成入力でも再現）
- NumLock は元の状態へ戻したことを確認済み
