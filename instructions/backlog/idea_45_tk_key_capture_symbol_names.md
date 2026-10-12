# idea_45_tk_key_capture_symbol_names.md

## 概要

**既存のキー取得（トリガー・停止 / トグルキー等）で、記号キーがフックの名前と一致しない可能性を調べて直す**。
`tk_keys.py` の変換表は記号キーを変換しないため、`.` を押すと `period`、`,` を押すと `comma` のような Tk の名前で記録される。一方、フックの振り分けが返すのは `.` / `,`。

## 起票経緯（2026-10-13）

出所: phase 56 task_06 の実機目視（編集の窓で枠のキーに `period` が記録され、本番の枠で反応しなかった）。
ユーザー判断で、phase 56 では**編集の窓だけ**直し、アプリ全体の修正はこの idea に分離した（decisions.md「task_06 実機目視 → 暫定 40 v0.7」）。

## 現状

- `keyseq/presentation/tk_keys.py` `TK_KEYSYM_TO_KEYBOARD_NAME` / `normalize_tk_keysym`（修飾・Enter・Esc 等だけを変換。記号は小文字化のみ）
- 使っている所: `normalize_tk_key_event` を呼ぶキー取得（例 `keyseq/presentation/controllers/key_capture.py`・`keymap_edit_dialog.py` の切替キー・トリガーの追加ダイアログ等。全件は未調査）
- フック側の名前: `keyseq/application/input_router.py` `_extract_key_name`（テンキー → `resolve_scan_code`〔キーボード配列〕→ `event.name`）。今の配列（US TKL）の定義はスキャンコードを持たないため、実際は `keyboard` ライブラリの `event.name`（記号は `.` 等）
- phase 56 の編集の窓の解決: `keymap_panel_controller._grid_key_name_from_event`（テンキー → 配列のスキャンコード → `win32_window.vk_to_char`〔`MapVirtualKeyW` の `MAPVK_VK_TO_CHAR`〕→ `normalize_tk_key_event`）

## 提案（方向性・要設計）

- まず実害の確認: 記号キーをトリガー・停止キー等に取得して、実際に発火するか（`keyboard` の名前の別名で吸収されていないか）を実機と既存データで確かめる
- 実害があれば: 編集の窓の解決（VK → 配列 → 文字 → Tk）を共通の関数にして、既存のキー取得からも使う（infrastructure の `vk_to_char` を使うので presentation 直下の `tk_keys.py` では完結しない）
- 既存の JSON に `period` 等で保存済みのキーの扱い（読込時の読み替え・後方互換）を決める必要がある

## 想定スコープ

- presentation（キー取得の各所）+ 既存データの読み替えなら domain の正規化
- 仕様変更の見込みあり（`key_input.md` §7.4 キーキャプチャ・`data_schema.md` の不正値 / 読み替え）
