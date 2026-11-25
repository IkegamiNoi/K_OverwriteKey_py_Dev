# idea_62_uppercase_replacement_target.md

## 概要

**キー置換の置換先に英字の大文字（例: `F1` → `A`）を置けるようにする。** いまは置換先を保存するときに小文字へそろえるため、大文字は作れない。Shift の要る記号（`!` 等）は phase 74 で置けるようになったので、それを英字の大文字へ広げる。

## 起票経緯（2026-11-21 起票・2026-11-25 書き直し）

出所: phase 75 task_13 の Windows 実機確認（exe）の際のユーザー要望。当初は「置換元に修飾キー付きの組み合わせ（`Shift+A`）を指定する」案として起票したが、2026-11-25 にユーザーと意図を確認し、ねらいは**置換先に大文字を置くこと**だと分かったため書き直した。置換元に Shift を付ける案（同じキーマップに Shift を押している間の面を持たせる）は [idea_68](idea_68_shift_layer_replacement_source.md) へ分離した。

## 現状

- 置換先は保存・判定・表示のたびに小文字へそろえる（`keyseq/domain/config.py:328` の `_normalize_keymap_mappings` → `normalize_key_name`・`keyseq/application/input_router.py:142`・`keyseq/presentation/keyboard_window.py:230`）。
- 置換の送信の Shift（phase 74・`key_input.md`「キー置換の送信の Shift」）は `keyseq/infrastructure/input_gateway.py:80` の `send_mapped_key`。Windows は keyboard ライブラリの表で判定、macOS は `SHIFTED_US` / `SHIFTED_JIS` の表（英字なし）。
- キーボードUI の置換先の記録（`keyboard_window.py:618` の `_record_key`）は、Shift を押したまま英字を押しても小文字で記録する。

## 提案（方向性・要設計）

- 置換先が英字 1 文字の大文字なら大文字のまま保存・判定・表示し、送るときに Shift を付ける（phase 74 と同じ送り方）。
- キーボードUI で Shift を押しながら英字を記録すると大文字で保存する。

## 想定スコープ

- 含む: キーマップの置換先の保存・判定・送信（Windows / macOS）・キーボードUI の記録と表示。
- 含まない: 置換元・トリガー・hotkey・key_hold の大文字。置換元の修飾キー（idea_68）。
- 仕様変更あり（`data_schema.md` / `key_input.md` に跨る見込み → 暫定仕様先行）。
