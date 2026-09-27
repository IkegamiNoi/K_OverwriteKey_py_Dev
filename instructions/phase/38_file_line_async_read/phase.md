# phase.md

## フェーズ名

file_line の非同期読込（file_line_async_read）

## フェーズの目的

出力シーケンスの file_line の**ファイル読込を UI スレッドの外（ワーカースレッド）で行い**、遅い・応答しないパス（UNC・切断されたドライブ等）でも
UI・停止操作・待機の取り消しが止まらないようにする。読込には **5 秒の上限**を設け、ループで同じファイルを繰り返し使う用途のため
**読込結果をキャッシュ**する（実行のたびにサイズと更新日時を確認）。

**JSON スキーマ変更なし**。**主に application 層**（file_line の読込・行の選択の分離 / 読込の登録簿とキャッシュ / runner の読込中の保留・完了の確認・取り消し・
連続実行の一時停止と停止 / executor の準備と送信の分離）。presentation は配線（ワーカーの起動・キャッシュの全破棄の契機）のみ。

- 起票元: [idea_38](../../backlog/idea_38_file_line_async_read.md)（2026-09-27・phase 37 の Codex 敵対的レビュー High から分離・ユーザー判断「次フェーズで最初に対応」）。
- 主入力（暫定仕様）: [27_file_line_async_read.md](../../history/27_file_line_async_read.md)（v0.6・ユーザー確定済 2026-09-27）。
- モード: **暫定仕様先行モード**。番号対応: phase 38 / 暫定 27 / decisions 38。

## 確定（ユーザー 2026-09-27）

暫定仕様 27 §2 が正。要点:

- 読込はワーカー（デーモンスレッド）で行い、完了は UI 側の確認タイマー（50 ms ごと）で受け取る（ワーカーは Tk を呼ばない）。読込中のステップは単発の待機と同じ保留。
- 上限 5 秒固定（超過は実行時エラー）。連続実行の読込中の一時停止は結果を捨てて再開時に読み直す（戻す履歴は 1 段）。
- 同じ (パス, 文字コード) のワーカーは同時に 1 本。走っていれば**待ち合わせ**（前の結果は使わない）。上限超過で放置中なら即エラー。
- 読込結果（行の一覧）をキャッシュし、実行のたびにサイズと更新日時をワーカーで確認。構成セットの読込等で全破棄（世代で書き戻しを防ぐ）。

## スコープ

### 含む

暫定仕様 27 の §3〜§6（実行モデル / 取り消し / 上限 / 待ち合わせ・キャッシュ）と §8 の受け入れ条件。

### 含まない（後送り）

暫定仕様 27 §9（file_line 以外の非同期化 / 読込中の表示 / 上限の設定項目化 / カウンター条件分岐〔idea_37〕/ 制御アクション第 2 弾）。

## このフェーズで読むファイル

1. [暫定仕様 27](../../history/27_file_line_async_read.md)（主入力。§1 の現状監査に `ファイル:行` の入口あり）
2. `instructions/common/spec_detail/data_schema.md` §5.11.5・§5.11.7・§5.11.8、`features.md` §4.2（4.2.1〜4.2.6）
3. `instructions/common/codebase_map.md`「アクションの実行」「出力シーケンスの制御アクション」節
4. 実装の入口（タスクごとに該当分のみ）: `keyseq/application/{file_line_reader,action_executor,sequence_runner,app_state,sequence_history,sequence_steps}.py` /
   `keyseq/presentation/app.py`（runner・executor の組み立て）/ 取り消しの呼び出し元
   （`presentation/controllers/hook_controller.py:161,187`・`controllers/keymap_panel/keymap_panel_controller.py:438`・構成セットの読込等）
5. テスト: `tests/test_file_line_reader*.py`・`tests/test_action_executor_file_line.py`・`tests/test_sequence_runner.py`（FakeScheduler）

## タスク

依存順。各タスクの定義は着手時に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

- task_01: 読込と行の選択の分離（暫定 §3.1: `file_line_reader.py` を検証・読込〔行の一覧〕・行の選択に分ける。文言と検査の順は不変・純関数） — **完了**（2026-09-27。`validate_file_line_request` / `load_file_lines` / `pick_file_line`・`read_file_line` は合成で残す）
- task_02: 読込の登録簿とキャッシュ（暫定 §6: 読込キーの正規化・同時 1 本・待ち合わせ・上限超過の印・キャッシュ〔stat 確認・エラーで破棄・世代つき全破棄〕・1 つのロック・
  ワーカーの起動を差し替え可能に。application の新規モジュール + 単体テスト）
- task_03: 単発実行の読込中の保留（暫定 §3.1-5・§3.2・§3.3・§4・§5: executor の準備と送信の分離 / runner の保留・確認タイマー・読込トークン・上限・完了後の先行処理・
  戻す履歴 1 段・取り消し / 同期前提テストの書き換え）
- task_04: 連続実行の読込（暫定 §3.4: 読込中は予約しない・一時停止で捨てて読み直す〔1 ステップ・1 段〕・停止・エラー時に 1 段）
- task_05: 配線と実機目視（暫定 §6.2 の全破棄の契機・`presentation/app.py` の組み立て / 実機: 応答しないパスで UI が止まらない・終了時に例外なし〔§8-11〕）
- task_06: 統合確認（テストスイート全体・smoke。統合レビュー = deep-reviewer + codex-reviewer）
- task_07: 正本反映（暫定 27 §10: `data_schema.md` §5.11.5・§5.11.7 / `features.md` §4.2〔4.2.7 新設・4.2.6 の拒否条件〕/ `codebase_map.md` /
  暫定 27 の凍結 / `decisions_archive/38_file_line_async_read.md` / current.md 完了記載 / idea_38 を INDEX_done へ / `/refactor_check`）

## レビュー方針

- 各タスク: reviewer（5 観点）。**スレッド共有状態はすべて登録簿のロック下**か、UI スレッドのみで触るかを必ず確認する。
- 状態遷移の重点: 読込トークンによる古い結果の破棄 / 戻す履歴が 1 段（`commit_step` の二重呼び出しなし）/ 上限超過と完了の競合 / 待ち合わせで古い内容を送らない / 全破棄後の書き戻しなし。
- ワーカーを実スレッドで回すテストは待ちでフレークしやすい。単体テストはワーカーの起動を差し替えて決定的に行う（idea_18・idea_33 の flaky 経緯に留意）。
- 統合・フェーズ完了判定前は deep-reviewer + Codex レビュー（`.claude/rules/agent_selection.md`）。
