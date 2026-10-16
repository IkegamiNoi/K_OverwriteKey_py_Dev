# idea_47_keyboard_ui_keycode_as_scan_code.md

## 概要

**キーボードUI の編集中の送信先の取得で、Tk の `keycode`（Windows では仮想キーコード）を走査コードとして解決している**ため、F1 / F10 / F12 などが `kana` / `henkan` / `muhenkan` と記録される見込みの不具合を調べて直す。

## 起票経緯（2026-10-16）

phase 59 の暫定 43 起票時の deep-reviewer の指摘（範囲外・暫定 43 §6 で「別 idea に起票」）。コードの読みによる指摘で、実機では未確認。

## 現状

* `presentation/keyboard_window.py` `_normalize_tk_key`（:496-510 付近）: Tk の keysym を `TK_KEYSYM_TO_KEYBOARD_NAME` で引けなければ、`resolve_key_id_from_scan_code(self._layout, event.keycode)` で解決する
* Windows の Tk の `keycode` は仮想キーコード（F1 = 112・F10 = 121・F12 = 123）。`domain/key_identifiers.py` の既知の特殊キーの走査コード（`kana` 112・`henkan` 121・`muhenkan` 123・`zenkaku_hankaku` 41）と値が重なるため、レイアウトに関係なく F1 → `kana` 等になりうる
* keysym `f1` 等が `TK_KEYSYM_TO_KEYBOARD_NAME` に無い場合にだけ起きる（keysym が引ければその名前になる）。実際にどちらの経路を通るかは未確認

## 調査結果（2026-10-16・メイン実測〔コードの経路〕・実機のキー入力は未確認）

* **起きている**: `_normalize_tk_key` に Windows Tk と同じ (keysym, keycode = VK) を与えると、既定（US TKL）・jis・de のどのレイアウトでも **F1 → `kana`・F10 → `henkan`・F12 → `muhenkan`**（keysym `f1` 等は `TK_KEYSYM_TO_KEYBOARD_NAME` に無く、走査コードの経路を通る）。英字・数字・矢印・編集キー・記号・Enter 等の残り 75 キーは他の取得の入口と同じ名前
* 原因: VK をそのまま走査コードとして引いている。画面の枠の編集の窓（phase 56・`keymap_panel_controller._grid_key_name_from_event`）は先に `win32_window.vk_to_scan_code`（`MapVirtualKeyW`）で VK → 走査コードに変換しており、キーボードUI だけがこの変換を飛ばしている
* さらに、この経路の本来の目的（`269fe5d`「JIS 特殊キー対応のための scan_code の導入」）も果たせていない見込み: 無変換（VK 0x1D）・変換（VK 0x1C）・半角/全角（VK 0xF3）は、今の経路では jis.json の走査コード（123・121・41）に当たらない。VK → 走査コードの変換を挟むと `muhenkan` / `henkan` / `zenkaku_hankaku` に解決できる。かな（VK 0x15）は変換しても走査コードが得られない（Tk の実際の VK は未確認）
* 変換を挟むと F1 / F10 / F12 は走査コード 59 / 68 / 88 になり、レイアウトに当たらないので keysym の `f1` 等へ落ちる（期待どおり）

## 提案（方向性・要設計）

* **推奨: `_normalize_tk_key` で `resolve_key_id_from_scan_code` に渡す前に `win32_window.vk_to_scan_code(keycode)` で変換する**（画面の枠の編集の窓と同じ。presentation → infrastructure の直接参照は既存の前例どおり）。単体テストで F1 / F10 / F12 と JIS の特殊キーを固定し、実機で F キーと JIS の特殊キーを確かめる
* 以下は当初の方向性（参考）

* まず実機で、キーボードUI の編集中に F1 / F10 / F12 を押して何が送信先として入るかを確かめる
* 起きているなら、`keycode` を走査コードとして使わない（Tk のイベントから走査コードを得る方法を使う、または keysym を優先して F キーを確実に引く）
* 取得の名前の作り方全般（記号キー＝ idea_45）とまとめて扱うかを決める

## 想定スコープ

* 含む: キーボードUI の編集中の送信先の取得の名前の修正とテスト / 影響レイヤ = presentation
* 含まない: フックの実行時のキー名（`input_router` は走査コードを正しく使っている）
* 仕様変更: なしの見込み（不具合の修正）
