# idea_61_win_d_restore_blank_dialog.md

## 概要

**Windows で入れ子のダイアログ（プリセット管理 → プリセット追加）を開いたまま Win+D で最小化して戻すと、プリセット追加の窓が白いまま描かれない**（毎回再現・窓を戻しても白いまま）。
**phase 75 前の main でも起きる既存の問題**。原因を確かめて、戻したときに中身が描かれるようにする。

## 起票経緯（2026-11-17）

出所: phase 75 task_09〜11f の Windows 目視（ユーザー）。phase 75 前の main でも同じ手順で起きることをユーザーが確認した。
同じ系統の完了済みの件 = [idea_19](idea_19_minimize_restore_with_child_grab.md)（Win+D の後にアプリを操作できない → phase 17 で、最小化の間だけ grab を預かる形で決着）。今回はアプリには戻れるが、描画が欠ける別の症状。

## 現状

- 最小化の間の grab の預かりは `keyseq/presentation/modal.py` の `install_minimize_grab_custody`（phase 17・phase 75 task_11c）。Windows では task_11c の「隠し漏れの窓を隠す」処理は何もしない（入れ子の窓も OS が隠す）。
- ダイアログは `keyseq/presentation/dialogs/preset_dialog.py`（`grab_modal(self, parent, ...)`。親 = プリセット管理）。
- メインの実測（2026-11-17）: スクリプトで App を `iconify()` → `deiconify()`（タイトルバーの最小化に相当）しても、今の版・phase 75 前の版のどちらでも再現しない。**Win+D（デスクトップの表示）に固有**の可能性。
- 他のダイアログで起きるかは未確認（ユーザーの目視では見つかっていない）。

## 提案（方向性・要設計）

- 着手時にまず実測する: Win+D の後の各窓の `wm_state()`・`winfo_viewable()`・`<Map>` / `<Unmap>` / `<Expose>` の届き方。Win+D はふつうの最小化と違う経路で窓を隠すため、App の `<Map>` で行う処理（grab を戻す・フォーカスを戻す）とプリセット追加の描き直しの順に問題がないかを見る。
- 案 A: 復帰（App の `<Map>`）の後に、台帳のモーダルの窓を描き直させる（`update_idletasks` や `event_generate("<Expose>")` 相当）。
- 案 B: 原因が grab の預かりの順なら、`modal.py` の戻しの順を直す。
- 他のダイアログ（入れ子の深さ・親の違い）で起きるかも確かめ、範囲を決める。

## 想定スコープ

- 含む: `modal.py` の最小化からの復帰の処理（presentation のみ）・`tests_ui` の受け入れテスト（Win+D を自動で再現できるかは要確認）。
- 含まない: 最小化の経路そのもの・Mac の挙動（task_11c で対応済み）。
- 仕様変更: 復帰の後の見た目を直すだけなら不要の見込み。grab の預かりの規則（`features.md` §4.6）を変えるなら `.claude/rules/spec_change_workflow.md` に従う。
