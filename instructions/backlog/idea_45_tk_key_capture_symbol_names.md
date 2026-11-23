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

## 追記（2026-11-22・phase 75 task_13b の Mac 実機確認から）: キー名の入力用 / 出力用の整理

- **経緯**: Mac でサンプルのテンキーの置換先 `plus`・`asterisk`・`slash` が `Unknown key name` で送れなかった（Mac の backend は記号を文字でしか受け付けない・`macos/backend.py:196-218`）。ユーザー提案で「記号キーのキー名は文字を正にする（互換は気にしない・良いコードを優先）」を暫定 57 §5.3.5（v0.26 案）に下書きしたが、Codex 敵対的レビュー（needs-attention・high 2 / medium 3）で、文字に揃えるだけでは解決しないと分かり取り下げた（ユーザー判断 2026-11-22・decisions.md）。サンプルは物理のテンキーのキー名（`num add` / `num multiply` / `num divide`）に直した。
- **本質**: キー名に性質の違う 2 つの用途が混ざっている。
  - 入力側（トリガー・置換元・停止 / トグル / 切替キー）= どの物理キーか。フックの名前はテンキー → レイアウトの物理キー → イベントの名前の順（`application/input_router.py:186-200`）。Shift の付いた文字（US の `*`）は物理キーの名前（`8`）と一致しない。
  - 出力側（置換先・ホットキー・key_hold）= どの文字を出すか。Shift を足す規則は置換先だけにある（phase 74・`key_input.md` の「キー置換の送信の Shift」）。
- **レビューの指摘（設計の入力）**:
  - `,` も `+` と同じく文字にすると壊れる（ホットキーの送信が `,` で区切る〔`action_executor.py:249`〕・Windows の keyboard の文字列の分割・key_hold は `+` と `,` を拒否〔`domain/key_hold.py:86-87`〕）。
  - Shift の要る文字を出力に使うときの契約（置換先以外での Shift の付け方・押下と解放・リピート・既に押されている修飾）。
  - テンキーの `*` と Shift+8 の区別・OS ごとの候補の選び方。
  - 単語の名前（`slash` 等）の扱い（読み替え / 拒否）と、既存サンプルの再利用（`sample_install.py`）。
  - 正本 `features.md` §4.6（phase 74 の表示の表）・`key_input.md` の phase 56 / 74・§7.8 との整合。
- **方針の候補**: 入力用は「物理キー」（Shift なしの文字か特殊キーの名前）、出力用は「出す文字」とし、両者の対応（Shift の要否）を 1 か所で解決する。互換は取らない（ユーザー方針）。両 OS の実測（Shift の付いた割り当て・カンマの送信・テンキーの識別）が要るので、独立したフェーズで扱う。

## 追記（2026-11-23・phase 78 の完了判定前レビュー〔Codex〕・ユーザー判断で除外してここへ）

- macOS で hotkey に Option+, を記録すると `option+comma` になる（`tk_keys.resolve_modified_char_key_name` が記号を `KEY_SYMBOLS` の単語名へ変換）。macOS の送信側 `vk_for_name` は `,` しか持たず（`macos/key_table.py:26`・`_SEND_ALIASES` に別名なし）、見本レイアウトの `,` の行も `scan_code` を持たないため `comma` を解決できない。
- phase 78 で hotkey の OK に `validate_hotkey` を足したため、以前は実行時に失敗していたこの値が、OK の時点で弾かれるようになった（記録の直後でも保存できず、`,` へ手で直す必要がある）。記録の名前と送信の名前の対応を 1 か所で解決する本 idea の方針で扱う。
