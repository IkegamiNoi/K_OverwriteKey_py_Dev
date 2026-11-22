# idea_64_mac_save_panel_expanded.md

## 概要

**Mac の保存パネル（`filedialog.asksaveasfilename` = NSSavePanel）を、最初から広げた形（フォルダの一覧で保存場所が見える形）で出す。**
今はたたんだ形（「Where」のポップアップだけ）で出る。既定の保存先以外にも保存できるので、どこに保存しているかが一目で分かる広げた形のほうがよい。

## 起票経緯（2026-11-22）

ユーザー要望。phase 75 task_11g（メニューの処理の遅延）の Mac 目視の際に、別名保存のパネルがたたんだ形で出ることについて。読込のパネル（NSOpenPanel）は一覧の形で出ていて、保存場所の分かりやすさに差がある。

## 現状

- 保存パネルの呼び出し: `keyseq/presentation/controllers/config_io/keymap_set_io.py:114,663`・`io_dialogs.py:35`・`keymap_file_io.py:73`・`trigger_set_file_io.py:61`（いずれも `filedialog.asksaveasfilename`）。Tk の aqua 版は NSSavePanel を出し、広げるかどうかの引数は無い。
- macOS は、ユーザーが「Where」の右の ⌄ で広げた状態をアプリごとに覚える（と言われている・**未確認**）。開発実行は Python のアプリ、`.app` は `io.github.ikegaminoi.keyseq` として別々に覚える。
- Mac の OS 依存は `keyseq/infrastructure/os_backend/macos/` に閉じる決まり（暫定 57 §3.1）。

## 提案（方向性・要設計）

- 案 A: 起動時に、アプリの NSUserDefaults の `NSNavPanelExpandedStateForSaveMode`（と `NSNavPanelExpandedStateForSaveMode2`）を true にする（pyobjc の `NSUserDefaults.standardUserDefaults()`・macOS の backend に置き、App の組み立てから呼ぶ）。どちらの鍵が今の macOS で効くかは実測で決める。
- 案 B: 何もせず、手順書・ヘルプに「⌄ で広げると次回も広がる」と書く（OS が覚えることを実測で確かめてから）。
- ユーザーが自分でたたんだ後も毎回広げ直すか（起動のたびに true にするか、初回だけか）は要検討。

## 想定スコープ

- 含む: Mac の保存パネルの初期の形。案 A なら infrastructure（macOS の backend）と App の組み立ての 1 か所。
- 含まない: Windows（保存ダイアログは元から一覧の形）・読込のパネル・保存先の既定値の変更。
- 仕様変更: 案 A は暫定 57（または正本）の Mac の UI の条項に 1 行足す見込み。
