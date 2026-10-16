# idea_49_special_keys_from_layout_only.md

## 概要

**JIS の特殊キー（無変換・変換・かな・半角/全角）の名前を、外部レイアウトのファイル（jis.json 等の `scan_code`）だけが決めるようにする**。今はコードに直書きの既知の表（`domain/key_identifiers.py`）がレイアウトを問わず全体に効き、US 入力配列のバッククォート（走査コード 41）までフックの実行時に `zenkaku_hankaku` と呼ばれる。

## 起票経緯（2026-10-17）

phase 61（idea_47）の起票時の議論から分離。キーボードUI の取得はレイアウトだけで引く形にした（ユーザー判断）が、フックの実行時と送信は既知の表を使い続けるため、US 入力配列の「`」の名前がキーボードUI（`grave`）とフック（`zenkaku_hankaku`）で違ったまま残る。

## 現状

* 既知の表: `domain/key_identifiers.py`（`_SPECIAL_KEY_NAME_TO_SCAN_CODE` = muhenkan 123 / henkan 121 / kana 112 / zenkaku_hankaku 41・`resolve_known_key_name_from_scan_code`）
* 名前の解決: `presentation/keyboard_layouts.resolve_key_id_from_scan_code`（レイアウト → 既知の表）を `LayoutController.resolve_key_name_from_scan_code` 経由でフックの実行時（`application/input_router._extract_key_name`・`key_state_manager`）と画面の枠の編集の窓が使う
* 送信: keyboard ライブラリは `kana`・`zenkaku_hankaku` を知らない（2026-10-16 実測で「不明なキー」）。`infrastructure/input_gateway.py` が既知の表の走査コードで送る（`269fe5d` で導入）

## 提案（方向性・要設計）

* 名前の解決（フックの実行時・画面の枠の編集の窓）はレイアウトの `scan_code` だけで引く（既知の表へ落とさない）
* 送信は名前 → 走査コードの対応が要るため、既知の表を「送信用の対応」として残すか、レイアウトから引くかを決める（レイアウトを切り替えると送れなくなる名前が出る点の扱い）
* 既存のキーマップ・トリガーに `zenkaku_hankaku` 等を使っている構成で、jis.json 以外のレイアウトのときに効かなくなる影響（後方互換）を評価する

## 想定スコープ

* 含む: 特殊キーの名前の解決・送信の対応の見直し / 影響レイヤ = domain・presentation（レイアウト）・application（入力の名前）・infrastructure（送信）
* 含まない: キーボードUI の取得（phase 61 で対応済み）
* 仕様変更: `key_input.md`（キー名・入力の名前）・`features.md` §4.6（レイアウトの JSON）の見込み
