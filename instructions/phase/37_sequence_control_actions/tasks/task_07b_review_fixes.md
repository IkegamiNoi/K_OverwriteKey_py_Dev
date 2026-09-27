# task_07b_review_fixes

## 目的

phase 37 統合レビュー（deep-reviewer / Codex 標準レビュー 2 モデル）の指摘と、暫定 26 v0.4 の §2-21〜24 を反映する。
- **H1 / L7**: 一覧のフォーカス同期（`<KeyRelease>`）で位置が変わっていないのに周回・戻す履歴・待機がリセットされる → **位置が実際に変わったときだけ**扱い、そのときは再描画もする（§4.3）。
- **L2**: 連続実行の一時停止中に行を選ぶと、runner が持つ連続実行の続き状態（`_run_to_end_resume` / `_run_to_end_snapshot`）が古いまま残る → 位置変更時に消す。
- **M1**: トリガーの無効化（キーマップ一時停止）でも単発の待機を取り消す（§2-21・§7）。
- **M2**: 連続実行を待機の途中で停止したら、そのステップを戻す履歴に 1 段積み、位置は待機の行に残す（§2-22・§7）。一時停止 → 再開は従来どおり。
- **M3**: system の実行時エラーの通知に操作名・主な値・ラベルを含める（§2-24・§10）。
- **M4**: 待機の取り消し・周回の張り直しの presentation 側の配線にテストを付ける。
- **L5**: 種別が不正なときの文言に `system` / `file_line` を加える。
- **L12**: system / file_line を sequence ファイルへ保存して読み直す往復テスト。

**application + presentation の最小修正とテスト**。先行処理（§2-20）は task_07c で行う（本タスクでは触らない）。

## 対象範囲

### `keyseq/presentation/controllers/trigger_panel_controller.py`（H1 / L7）

- `on_action_list_select`: 求めた行 `idx` が今の位置（`self._app._indices.get(key, 0)`）と**同じなら何もしない**（`update_status` のみ可）。
  違うときだけ位置を書き、`reset_loop_frames(key)` を呼び、`refresh_actions()` で再描画する（周回表示を更新するため）。

### `keyseq/application/sequence_runner.py`（L2 / M2 / M3）

- L2: `reset_loop_frames(key)` で、`key` が連続実行中（一時停止中を含む）のトリガーなら、連続実行の続き状態（`_run_to_end_resume` / `_run_to_end_snapshot` と、M2 で足す待機の行）を消す。
- M2: 連続実行で待機に入ったとき、待機の行を控える（保存位置は従来どおり待機の次）。`stop_run_to_end` で待機の途中（控えがある）なら、
  位置を待機の行に戻し、`sequence_history.commit_step` でそのステップを 1 段積んでから状態を消す。一時停止（`pause_run_to_end`）では何もしない（従来どおり続きから）。
  通常アクションを実行して待機を抜けたら控えを消す。
- M3: system の実行時エラーを通知するとき、通知用に action の写しを作り、`value` に「操作名と主な値」（例: `loop_start 回数=abc`・`loop_start 無限`・`wait 500ms`・`counter_inc カウンター=n`・
  `back`）を入れ、メッセージにラベル（あれば）を含める。元の action は変更しない。file_line・通常種別の通知は変えない。
- 行数は 330 行未満に保つ（収まらなければ M3 の整形関数を `sequence_steps.py` か `sequence_history.py` の近くへ置く。新しい共通フォルダは作らない）。

### `keyseq/presentation/controllers/hook_controller.py`（M1）

- `toggle_custom_input_enabled` の無効化の分岐で、`stop_run_to_end()` と並べて `cancel_pending_waits()` を呼ぶ。

### `keyseq/application/action_executor.py`（L5）

- `_invalid_type_message` の文言を「種類が不正です（hotkey / text / mouse_click / system / file_line のいずれか）。」にする。既存テストの期待文言も合わせて直す。

### テスト

- `tests/test_sequence_runner.py`（追記）: L2（一時停止中に `reset_loop_frames` → 再開後に古い控えで履歴が積まれない）/ M2（`[inc n, wait, A]` を連続実行し待機中に `stop_run_to_end` →
  位置 = 待機の行・履歴 1 段・直前のトリガー更新・`back` で n が戻る / 一時停止 → 再開は待機の次から・履歴を積まない）/ M3（通知の action の `value` とメッセージに操作名・値・ラベル）。
- `tests_ui/`（M4・新規 1 ファイル。既存の命名に合わせる）: `stop_hook` が `cancel_pending_waits` を呼ぶ / 無効化で呼ぶ / `activate_keymap_by_id` で切り替わったときだけ呼ぶ /
  `on_action_list_select` が同じ行では `reset_loop_frames` を呼ばず、違う行では呼んで再描画する（H1）/ `delete_trigger` で `cancel_pending_wait` と履歴の消去 / 改名での付け替え。
- 往復テスト（L12）: `ConfigService.save_sequence_file` → `load_sequence_file` で system（7 操作・無限と回数）と file_line（全キー）の actions が一致すること
  （既存の sequence ファイル単体テストの置き場所・書き方に合わせる）。
- L5 の文言変更で落ちる既存テストの期待値を直す。

## 読むファイル

- `instructions/history/26_sequence_control_actions.md` §2-21〜24・§4.3・§7・§10（仕様）
- `keyseq/application/sequence_runner.py`（編集対象・全体）/ `keyseq/application/sequence_history.py`（`commit_step` / スナップショット）
- `keyseq/presentation/controllers/trigger_panel_controller.py` の `on_action_list_select`・`delete_trigger`・`rename_trigger`（`rg -n` で位置を特定し範囲指定）
- `keyseq/presentation/controllers/hook_controller.py:155-195`（`stop_hook` / `toggle_custom_input_enabled`）
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:407-445`
- `keyseq/application/action_executor.py:80-135` / `keyseq/application/config_service/child_file_io.py`（sequence の保存・読込の口）
- 既存テストの手本: `tests/test_sequence_runner.py`・`tests_ui/test_trigger_panel_controller_action_edit.py`（先頭 80 行程度）・sequence ファイル単体テスト（`rg -ln "save_sequence_file" tests`）

## 含まない

- 通常アクション直後の system の先行処理（§2-20）→ task_07c
- deep-reviewer の Low のうち L3・L4・L6・L8〜L11・L13・L14（current.md の別タスク化候補へ記録）
- 正本・codebase_map → task_08

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` がエラー無し。
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`・`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass、`..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass。
- `wc -l keyseq/application/sequence_runner.py` が 330 未満。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_07c の後にまとめて実施（H1 は一覧にフォーカスを置いたままトリガーを押して周回が進むこと）。
