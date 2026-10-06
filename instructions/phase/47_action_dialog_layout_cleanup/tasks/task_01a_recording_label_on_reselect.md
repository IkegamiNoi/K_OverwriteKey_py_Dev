# task_01a_recording_label_on_reselect

## 目的

task_01 で入った後退を直す: 記録中に種別のドロップダウンで hotkey を選び直すと、記録は続いたまま「記録停止」の文言だけ「キー入力で記録」へ戻る
（phase 47 完了判定前レビュー・Codex 敵対的 / deep-reviewer 指摘 2・ユーザー承認 2026-10-06）。旧コード（02c7eb8）は hotkey のとき文言を変えていなかった。
**presentation 限定・domain / application 不変・スキーマ不変。**

## 対象範囲（presentation 限定・`action_dialog.py` の 1 行 + テスト）

### `keyseq/presentation/dialogs/action_dialog.py`

- `_sync_hotkey_controls`（:404-412）の `self.capture_btn.configure(state="normal", text="キー入力で記録")` から `text=` を外し、`state="normal"` だけにする
  （文言の戻しは `_stop_recording`〔:321-325〕の責務。hotkey 以外へ切り替えたときは直前の `_stop_recording()` で戻る）
- それ以外は変えない

### `tests_ui/test_action_dialog_control.py`（既存クラスへ追加）

1. 記録中に種別 hotkey を選び直す（`type_var.set("hotkey")` → `_sync_capture_ui()`、既存 `test_type_change_stops_recording`:115 の流儀）と、`_recording` が True のまま・ボタン文言が「記録停止」のまま
2. hotkey → system → hotkey と往復したとき、値の欄・「キー入力で記録」・説明文・プリセットの枠・「プリセット編集…」が再び表示される（`winfo_ismapped()`・表示待ちは `update()`。`update_idletasks()` では初回が False）
3. 「キー入力で記録」にフォーカス（または `focus_lastfor` の戻し先）がある状態で text へ切り替えると、フォーカスが `type_combo` へ移る（既存 :95・:104 の流儀）

## 読むファイル

- `keyseq/presentation/dialogs/action_dialog.py:300-330, 380-452`
- `tests_ui/test_action_dialog_control.py:1-125`（setUp・既存の表示 / フォーカス / 記録のテスト）

## 含まない

- マウス設定・system / file_line の欄からのフォーカス移動（正本で対象外と明記・phase 37 からの隙間）
- `_sync_hotkey_controls` の名前・構造の整理（deep-reviewer 指摘 4・除外）
- 正本反映（task_02）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests_ui` clean
- `tests_ui/test_action_dialog_control.py` 全件 pass（追加 3 件を含む）
- tests（`unittest discover -s tests`）・tests_ui 全体・`-m tests.smoke_app` pass

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視: なし（文言 1 か所の後退修正・テストで固定。ユーザーが望めば task_02 完了報告時に案内）
