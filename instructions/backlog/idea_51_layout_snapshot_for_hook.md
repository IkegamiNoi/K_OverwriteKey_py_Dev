# idea_51_layout_snapshot_for_hook.md

## 概要

**フックの実行時に、外部レイアウトの JSON をキーが届くたびに読み直すのをやめ、受け取りと送信が同じ「レイアウトの写し」を使うようにする**。
写しの更新は UI スレッドだけで行い、更新の前に押したままのキーを古い写しで離す。

## 起票経緯（2026-10-18）

暫定 45（phase 62・idea_49）の Codex 敵対的レビューの指摘から分離した。ユーザーは最小の対応である案 B を選び、本件（案 A）は後送りにした。

## 現状

* `LayoutController.get_current_keyboard_layout`（`presentation/controllers/layout_controller.py:178`）は、外部レイアウトを呼ぶたびに JSON から読み直す。読めなければ `_set_flash_message`（Tk の操作）を呼ぶ。
  * これをフックのスレッドの `resolve_key_name_from_scan_code` が毎回の打鍵で呼ぶ。そのため、UI スレッドの外でファイルを読み、Tk を操作している
* 暫定 45 で、送信側は登録時の値（`entry.layout`）を引くことにした。そのため、起動中に JSON を書き換えると、受け取りと送信で `scan_code` が食い違う（受容・暫定 45 §6）

## 提案（方向性・要設計）

* `LayoutController` に「受け取りと送信の両方が読む写し」を持たせ、写しを UI スレッドでだけ差し替える
  * 差し替える契機: 選び直し / 読み直し / UI スレッドで JSON の変更を見つけたとき
* 差し替える前に `held_inputs.release_all()` を呼び、押したままのキーを古い写しで離す（暫定 45 §6 と同じ考え方）
* 読込失敗の通知は UI スレッドから出す

## 想定スコープ

* 含む: フックの実行時の名前の解決と送信のレイアウトの参照 / 影響レイヤ = presentation（`LayoutController`）
* 含まない: レイアウトの JSON の書式
* 仕様変更: `key_input.md` §7.1・`features.md` §4.6（外部レイアウトの変更の反映時期）の見込み
