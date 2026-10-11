# idea_42_suppress_repeat_on_all_dialogs.md

## 概要

**key_hold のキーリピート中にアプリが出すモーダルダイアログ（messagebox 全般）でも、リピートを止めて表示中は抑止する**。
phase 52 では実行系のエラーの知らせ（ActionExecutor・runner・フック）だけを対象にしたため、UI 操作のダイアログ（保存失敗・確認・お知らせ等）では
`enter` / `space` 等のリピートがダイアログを即座に閉じる（確認ダイアログなら意図しない選択になる）可能性が残る。

## 起票経緯（2026-10-11）

phase 52 task_05 の完了判定前 Codex 敵対的レビュー（medium: シーケンスの保存失敗の `showerror` が抑止されない）と deep-reviewer L3（フック開始の失敗の知らせ）。
ユーザー判断で phase 52 は範囲を「実行系のエラーの知らせ」と正本に明記して閉じ、全ダイアログの抑止は次フェーズで実装する（[decisions_archive/52](../../.claude_data/state/decisions_archive/52_key_hold_auto_repeat.md)）。

## 現状

- 抑止の口 = `application/key_repeat.py` の `KeyRepeater.begin_suppress` / `end_suppress`（入れ子を数で数える）。
  使っているのは `presentation/app.py` の `repeat_suppressed` / `_show_runtime_error` と `controllers/hook_controller.py` の `show_action_error` だけ
- presentation の `messagebox.show*` / `ask*` の呼び出しは 28 ファイルに散在（`keymap_panel_controller.py` 20・`keymap_set_io.py` 16・`action_edit.py` / `trigger_row_edit.py` 13 等）
- アクション編集等のダイアログ（Toplevel）を開く操作はフック停止を通り `release_all` で離れる（リピートも止まる）。messagebox はフック停止を通らない経路がある
- 正本: `features.md` §4.2.12「キーリピート」の「知らせのダイアログとリピート」

## 提案（方向性・要設計）

- 案 A: presentation に messagebox の薄い入口（抑止つき）を 1 つ置き、呼び出し元を置き換える（呼び出しの差し替えが多い・漏れはテストの静的確認で防ぐ）
- 案 B: `tkinter.messagebox` の関数を起動時に包む（呼び出し元は変えない・暗黙的で追いにくい）
- 案 C: messagebox を出すときに、抑止ではなくリピートを止めるだけにする（表示中の新しい開始は許す）
- Toplevel のダイアログ（フック停止を通らないもの）も対象にするか・情報だけのお知らせ（showinfo）も対象にするか・確認（ask*）を含めるかを決める

## 想定スコープ

- presentation が中心（application の `KeyRepeater` の口は既存）。JSON の変更なし
- 正本 `features.md` §4.2.12 の対象の範囲を広げる仕様変更（暫定仕様先行の見込み）
- 含まない: リピート以外の押したままのキー（押したままは従来どおり保つ）
