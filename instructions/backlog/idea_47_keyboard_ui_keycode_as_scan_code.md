# idea_47_keyboard_ui_keycode_as_scan_code.md

## 概要

**キーボードUI の編集中の送信先の取得で、Tk の `keycode`（Windows では仮想キーコード）を走査コードとして解決している**ため、F1 / F10 / F12 などが `kana` / `henkan` / `muhenkan` と記録される見込みの不具合を調べて直す。

## 起票経緯（2026-10-16）

phase 59 の暫定 43 起票時の deep-reviewer の指摘（範囲外・暫定 43 §6 で「別 idea に起票」）。コードの読みによる指摘で、実機では未確認。

## 現状

* `presentation/keyboard_window.py` `_normalize_tk_key`（:496-510 付近）: Tk の keysym を `TK_KEYSYM_TO_KEYBOARD_NAME` で引けなければ、`resolve_key_id_from_scan_code(self._layout, event.keycode)` で解決する
* Windows の Tk の `keycode` は仮想キーコード（F1 = 112・F10 = 121・F12 = 123）。`domain/key_identifiers.py` の既知の特殊キーの走査コード（`kana` 112・`henkan` 121・`muhenkan` 123・`zenkaku_hankaku` 41）と値が重なるため、レイアウトに関係なく F1 → `kana` 等になりうる
* keysym `f1` 等が `TK_KEYSYM_TO_KEYBOARD_NAME` に無い場合にだけ起きる（keysym が引ければその名前になる）。実際にどちらの経路を通るかは未確認

## 提案（方向性・要設計）

* まず実機で、キーボードUI の編集中に F1 / F10 / F12 を押して何が送信先として入るかを確かめる
* 起きているなら、`keycode` を走査コードとして使わない（Tk のイベントから走査コードを得る方法を使う、または keysym を優先して F キーを確実に引く）
* 取得の名前の作り方全般（記号キー＝ idea_45）とまとめて扱うかを決める

## 想定スコープ

* 含む: キーボードUI の編集中の送信先の取得の名前の修正とテスト / 影響レイヤ = presentation
* 含まない: フックの実行時のキー名（`input_router` は走査コードを正しく使っている）
* 仕様変更: なしの見込み（不具合の修正）
