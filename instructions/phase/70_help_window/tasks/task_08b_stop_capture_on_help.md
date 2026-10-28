# task_08b_stop_capture_on_help

## 目的

キーの記録中にダイアログの「?」を押したら、ヘルプを開く前にそのダイアログのキー記録を止める（暫定 53 §14.3・ユーザー確定 2026-10-29）。

## 対象範囲

- `keyseq/presentation/help/help_button.py` `add_help_button`: キーワード引数 `before_open: Callable[[], None] | None = None` を足し、
  「?」の押下でヘルプを開く**前に**呼ぶ（None なら何もしない）。既存の呼び出しは引数なしのまま動く。
- キーの記録を持つ 4 ダイアログで、Esc（`bind_escape_close` / `_on_escape`）が使っている停止の関数を `before_open` に渡す:
  - `dialogs/action_dialog.py` → `self._stop_recording`（キー入力の記録と `key_hold_fields` の記録の両方を止める既存の関数）
  - `dialogs/trigger_dialog.py`・`dialogs/keymap_edit_dialog.py`・`dialogs/keymap_switch_batch_dialog.py` → `self._stop_capture`
  - 停止の関数は記録していなければ何もしない（既存の挙動）ことをコードで確かめる。そうでなければ記録中のときだけ呼ぶ。
- `dialogs/action_dialog.py` `_open_preset_manager`（:591）: プリセットマネージャを開く前に `self._stop_recording()` を呼ぶ
  （記録中に開いた子の「?」で、親の記録が残ってヘルプで IME を切り替えられない経路を断つ。Codex 敵対的レビュー指摘）。
- ほかのダイアログは変更しない（キーの記録が無い）。

### テスト

- `tests_ui/test_dialog_help_buttons.py`（または近いテスト）に追加: トリガーの追加・編集で記録を始めた状態（既存テストの記録開始の手段に倣う）で
  「?」を押すと、記録が止まっている（`_capturing` が偽・ボタンの文言が記録前に戻る）こと。記録していない状態で押しても例外が出ないこと。
- アクションの追加・編集でも同様に 1 件（`_recording` が偽）。
- アクションの追加・編集で記録中に「プリセット編集…」を押すと、開く前に記録が止まる（`_recording` が偽・記録の owner が残らない）こと。
  `wait_window` で止まらないよう、`PresetManagerDialog` は差し替えてよい。

## 読むファイル

- `instructions/history/53_help_window.md` §14.3
- 上記の編集対象・`dialogs/escape_close.py`・`tests_ui/test_dialog_help_buttons.py`

## 含まない

- 記録用フック（`KeyCaptureHook` / `key_capture_ime.py`）の配送の仕組みの変更・正本の更新（メインが task_08 で行う）

## 確認

- `tests_ui.test_dialog_help_buttons`・`tests_ui.test_action_dialog_control` pass、tests / tests_ui / smoke 全体 pass（verifier）
- 実機目視（ユーザー・任意）: JIS 配列でトリガーの追加・編集の記録を開始 →「?」→ 絞り込み欄で半角/全角が効く

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: §14.3 どおりか / 4 ダイアログの漏れ / Esc と同じ停止の経路か / 既存の呼び出しへの影響）
