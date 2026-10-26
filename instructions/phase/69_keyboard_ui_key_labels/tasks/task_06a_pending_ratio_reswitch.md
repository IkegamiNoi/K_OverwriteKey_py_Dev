# task_06a_pending_ratio_reswitch

## 目的

完了判定前の Codex 敵対的レビューの指摘（ユーザー確定 2026-10-26）を直す: 最小化 / 最大化中のレイアウトの切替で当て直しが保留（`_ratio_pending`）になった後、
通常へ戻して保留の当て直し（約 150ms）が走る前に、通常の状態でもう一度レイアウトを切り替えると `_ratio_pending` が残る。
その後の利用者の大きさの変化が保留の当て直しへ回され、利用者の幅が失われ記録もされない（`features.md` §4.6「幅の記録」に反する）。
**presentation のキーボードUI（`keyboard_window.py`）と tests_ui に限定。仕様は変えない。**

## 対象範囲

### `keyseq/presentation/keyboard_window.py`（`update_layout`・`:166-185` 付近）

- 当て直しが要る変化（`changed`）で、最大化 / 最小化中でない（通常の状態で当て直す）ときは、`_ratio_pending = False` にしてから当てる（`ratio` が None でも保留を解く）。
  `_apply_ratio_to_base` が予約を取り消すので、保留の予約も残らない
- 最大化 / 最小化中の扱い（保留を立てる）は今どおり

### `tests_ui/test_app_ui_flows.py`（回帰テスト）

- iconic でレイアウト B（記録の幅あり）へ `update_layout` → 通常の state で `_on_window_configure`（保留の当て直しの予約）→ 予約が走る前に通常の state でレイアウト A へ `update_layout`
  → `_ratio_pending` が False・保留の予約が残っていない → その後の利用者の大きさの変化（`_on_window_configure` → `_settle_size`）で補正され、`on_width_settled` が A の id と利用者の幅（または補正後の幅）で 1 回呼ばれる
- A の目標の大きさが今の大きさと同じで `geometry` が呼ばれない場合も同じ結果になること（`winfo_width` / `winfo_height` を目標に合わせて patch）
- `write_startup` と `_startup_settings` は既存のテストと同じく差し替える

## 読むファイル

- `keyseq/presentation/keyboard_window.py:140-200`・`:274-420`（編集対象）
- `tests_ui/test_app_ui_flows.py` の `test_keyboard_window_pending_ratio_survives_restore_configures_without_saving` 周辺（手本）

## 含まない

- 完了判定前レビュー（deep-reviewer）の文書の指摘（メインが反映）
- 提案書 26（保留）

## 確認

- compileall clean / 追加テストの単体 pass・`tests_ui.test_app_ui_flows` pass
- 追加テストが修正前の実装で落ちることをコードの読みで説明できる
- tests 全体 / tests_ui 全体（1 本だけ）/ smoke pass・件数が減らない・worktree の `config/config.json` が生成されない

## 完了条件

- 上記確認 pass・**reviewer 採用**
