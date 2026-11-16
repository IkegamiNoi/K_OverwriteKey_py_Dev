# idea_59_close_app_during_wait_window.md

## 概要

**ダイアログが子のダイアログを `wait_window()` で待っている間にアプリを閉じると、待ちが解けた後の続きの処理が破棄済みの窓に触れて `TclError: NULL main window` が出る。**
待ちの後に窓が残っているかを確かめるか、モーダルを開いている間にメインを閉じられる扱いそのものを決める。

## 起票経緯（2026-11-17）

phase 75 task_11c の Mac 目視の際に、ユーザーがアプリを閉じたときのトレースバックを報告。
Mac ではモーダルを開いていてもメインの赤いボタンで閉じられるため、この経路に入りやすい。task_11c の変更が原因ではない（以前からの経路）。

## 現状

- `keyseq/presentation/dialogs/action_dialog.py:645-649` の `_open_preset_manager`: `PresetManagerDialog(...).wait_window()` の後に `_rebuild_preset_buttons()`。待ちの間に App が破棄されると、続きが破棄済みの `presets_frame` に `ttk.Button` を作ろうとして `TclError`。
- `keyseq/presentation` 配下の `.wait_window()` は 25 か所（2026-11-17 時点・grep）。同じ形の「待ってから続ける」処理が他にもある可能性。
- 閉じる処理は `app.py:375` の `WM_DELETE_WINDOW` → `on_close`。影響は終了時のエラー表示だけで、保存・設定には影響しない（メインの確認）。

## 提案（方向性・要設計）

- 案 A: `wait_window()` の後で呼び出し側の窓が `winfo_exists()` でなければ何もしない（該当箇所を洗い出してまとめて直す）。
- 案 B: モーダルを開いている間はメインの閉じる操作を受け付けない、または閉じる前にモーダルを順に閉じる（仕様の判断が要る・Windows の挙動も確認）。

## 想定スコープ

- 含む: `wait_window()` の後続処理の洗い出しと保護（presentation）。案 B なら閉じる操作の扱い。
- 含まない: OS backend の変更。
- 仕様変更: 案 A は不要の見込み。案 B は `features.md` の閉じる操作の扱いに関わる可能性。
