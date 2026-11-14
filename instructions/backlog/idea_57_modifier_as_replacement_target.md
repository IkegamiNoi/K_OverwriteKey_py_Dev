# idea_57_modifier_as_replacement_target.md

## 概要

**キーボードUI（およびキーマップ編集の取得）で、置換先に修飾キー（Control / Shift / Option〔Alt〕/ Command〔Win〕）を記録できるようにする。** いまは置換先の記録で修飾キーを押しても読み飛ばすため、`y` → `shift` のような割り当てを画面から作れない（JSON に書けば動く）。

## 起票経緯（2026-11-14）

出所: phase 75 task_09a の Mac 実機目視（ユーザー）。Mac 固有の不具合と見えたが、調べると Windows も同じ処理を通る当初（2026-03・キーボードUIの追加時）からの動きだったため、phase 75 から分離した。

## 現状

- `keyseq/presentation/keyboard_window.py:618`（`_record_key`）が `ctrl` / `shift` / `alt` / `windows` を読み飛ばす。OS の分岐は無い。
- 同系統の読み飛ばし: `keyseq/presentation/controllers/key_capture.py:145-155`・`keyseq/presentation/dialogs/keymap_edit_dialog.py:187-197`。
- 置換先の検査（`keymap_panel_controller.py:657-669` → `input_gateway.validate_key_name` → backend の `resolve_send`）は修飾キーの名前を通す見込み（未実測）。
- 正本 `features.md` に「修飾キーを置換先にできる」とは書かれていない。phase 75 で macOS の送るフラグを「物理側 + 送信側」に改訂した（暫定 57 v0.9 §5.1）ため、Mac でも置換先の修飾キーは効く。

## 提案（方向性・要設計）

- 置換先の記録に限り修飾キーを受け付ける（元キー・切替キーの読み飛ばしはそのまま）。
- 左右を区別して記録するか（`left ctrl` / `right shift` 等。`key_hold` の取得は左右を区別している）、左右なし（`ctrl`）にするか。
- Command / Windows キーを置換先にしてよいか（暫定 57 Q5・`features.md` §4.6 の禁止は元キーと切替キーだけ。置換先は OS のショートカットを壊さない見込み）。
- 置換先の修飾キーを押したまま別のキーを押したときの組み合わせ（Windows は OS が合成・Mac は §5.1 v0.9）の確認。

## 想定スコープ

- 含む: キーボードUI・キーマップ編集の置換先の取得、検査、テスト、正本 `features.md` の追記（仕様変更あり）。
- 含まない: 元キー・切替キー・トリガーで修飾キー単独を記録すること。
- 影響レイヤ: presentation（取得）中心。application / domain は変えない見込み。
