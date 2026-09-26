# phase.md

## フェーズ名

出力シーケンスの制御アクション・第 1 弾（sequence_control_actions）

## フェーズの目的

出力シーケンスに**入力を送らない制御用の system 種別**（ループ / カウンター +1・0 に / 待機 / 戻す / 先頭へ）と、
**カウンター値の行をファイルから読んで入力する file_line 種別**を加え、ループ・回数の把握・誤操作からの復帰を可能にする。

**JSON スキーマ変更あり**（`actions[]` の要素に種別 `system` / `file_line` を追加。既存の種別・キーは不変）。
**全レイヤに跨る**（domain の正規化・対応判定・表示整形 / application の実行モデル〔ステップ・周回・待機・戻す履歴・カウンター〕と
file_line の実行 / presentation の編集ダイアログ・追加位置・一覧の表示と色分け）。

- 起票元: ユーザー要望（2026-09-26・出力シーケンスに system 種別を追加したい）。
- 主入力（暫定仕様）: [26_sequence_control_actions.md](../../history/26_sequence_control_actions.md)（v0.3・ユーザー確定済 2026-09-26）。
- モード: **暫定仕様先行モード**。番号対応: phase 37 / 暫定 26 / decisions 37。

## 確定（ユーザー 2026-09-26）

暫定仕様 26 §2（確定事項 1〜19）が正。要点:

- system は押下を消費しない（単発実行は次の通常アクションまで進めて実行）。ループはネスト可・上限 9・周回は中断しても保持。
- カウンターは名前指定・アプリ全体共有・起動中のみ保持。戻すときは操作の分だけ差し引く。
- 戻す / 先頭へ の対象は直前のトリガー。待機中も他のトリガーは使える。file_line は 1 始まり・範囲外 3 択・UTF-8 / Shift_JIS・1 MB 上限。
- 追加ダイアログに「末尾に追加」チェック欄（既定 ON・全種別）。ネストは深さで色分け（青・緑・橙 × 薄・中・濃）。
- 停止・他トリガー呼び出しは第 2 弾（次フェーズ）。カウンター条件分岐は [idea_37](../../backlog/idea_37_counter_conditional_branch.md)。

## スコープ

### 含む

暫定仕様 26 の §3〜§11（データモデル / 実行モデル / ループ / カウンター / 待機 / 戻す・先頭へ / file_line / エラー規則 / 編集 UI と一覧表示）と
§14 の受け入れ条件。

### 含まない（後送り）

暫定仕様 26 §13（第 2 弾: 停止・他トリガー呼び出し）と §15（ジャンプ / カウンター条件分岐 / カウンターの −1・任意値・保存 /
ループの一括移動 / file_line のパスを参照元管理の対象にすること）。

## このフェーズで読むファイル

1. [暫定仕様 26](../../history/26_sequence_control_actions.md)（主入力。§1 の現状監査に `ファイル:行` の入口あり）
2. `instructions/common/spec_detail/data_schema.md` §5.1 / §5.7 / §5.11、`features.md` §4.2 / §4.6「一覧の表示形式」
3. `instructions/common/codebase_map.md` の SequenceRunner・ActionExecutor・TriggerPanelController・ActionDialog・JSON 読込時の型正規化の節
4. 実装の入口（タスクごとに該当分のみ）: `keyseq/domain/config.py` /
   `keyseq/application/{sequence_runner,action_executor,app_state}.py` /
   `keyseq/presentation/dialogs/action_dialog.py` / `keyseq/presentation/controllers/trigger_panel_controller.py` /
   `keyseq/presentation/app.py`（runner・executor の組み立て）/ `keyseq/presentation/controllers/hook_controller.py`（フック停止）/
   `keyseq/presentation/controllers/keymap_panel/`（切替・forget / rekey）

## タスク

依存順。各タスクの定義は着手時に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

- task_01: domain の土台（暫定 §3・§5.1・§11.3 の整形・§11.4 の深さ → 色の対応: system / file_line の読込正規化 /
  ループの対応判定と深さ・対応崩れの検出〔純関数〕/ 一覧の表示名〔runtime の値は引数で受ける〕/ 深さの色の表）— **完了**（2026-09-26。
  新規 `domain/sequence_control.py`。reviewer 参考 = 非文字列の op の表示は生値の文字列化〔未テスト・必須でない〕）
- task_02: 実行モデルの中核（暫定 §4・§5・§6・§10: ステップ〔system は押下を消費しない・末尾の回り込みと開始位置での終了・
  10,000 の上限〕/ 周回スタックと整合〔張り直し〕/ カウンター / runtime 状態の生存期間 / 実行時エラー）。
  **重いタスク。Codex の Sol medium + Luna xhigh サブエージェントの試行対象**（下記「実装モデルの試行」）— **完了**（2026-09-27。
  新規 `application/sequence_steps.py`。**試行結果: Sol medium 単独で完了・サブエージェントは起動されず**〔セッション記録で実測〕・約 6 分・
  入力 52.5 万〔キャッシュ 48.4 万〕/ 出力 1.2 万トークン。reviewer 参考 = `refresh_actions` の run_to_end 用 clamp が到達不能化〔害なし〕/
  単発で先頭へ回って開始位置で止まると周回スタックは空で返る〔次のステップで張り直し・害なし〕）
- task_03: 待機（暫定 §7: 連続実行の待機 / 単発実行の非同期待機・保留中ステップ・世代番号・取り消し契機）— **完了**（2026-09-27。
  `codex-delegating-implementer`・**Luna xhigh のサブエージェントがテスト 2 ファイルを担当**〔実測〕・約 11 分・入力 親 175 万 / 子 147 万〔大半キャッシュ〕・
  出力 親 1.2 万 / 子 2.0 万。reviewer 参考 = runtime 状態を消す契機で保留の `after` 予約そのものは残る〔発火時に何もしない・害なし〕）
- task_04: 戻す・先頭へ（暫定 §8: 戻す履歴〔操作を差分で打ち消す〕/ 直前のトリガー / 対象が無いときの一時メッセージ / 選択の順序）
- task_05: file_line の実行（暫定 §9: 1 MB 上限・UTF-8〔BOM〕/ cp932・改行 3 種のみで分割・範囲外 3 択・text と同じ送信経路）
- task_06: 編集 UI（暫定 §11.1・§11.2: system / file_line の編集 / カウンター名の候補 / ループの行の編集規則 /
  「末尾に追加」チェック欄と挿入位置 / ループの対での追加・削除・深さ上限 / 移動規則 / 対応が崩れた行の扱い）
- task_07: 一覧の表示（暫定 §11.3・§11.4: 周回・カウンター値の表示と更新 / ネストの色分け / 省略表示の「次に実行」の要約）
- task_08: 統合確認と正本反映（暫定 26 の `spec_detail/` への昇格・凍結 / `codebase_map.md`〔新モジュール・色値〕/
  decisions_archive/37 / current.md の完了記載 / `/refactor_check`）

### 実装モデルの試行（ユーザー判断 2026-09-26）

- **task_02** は `codex-implementer` の呼び出しで **Sol medium（`--model gpt-6-sol --effort medium`）を主とし、
  Luna xhigh のサブエージェント使用を許可**して実装させる。**着手前にユーザーへ「このタスクで試行する」ことを知らせる**
  （使用量の減りをユーザーが確認するため）。
- サブエージェントが使えていない・使用量の減りが多すぎる場合は、実装での使用を見送る（判断はユーザー）。
- 実装後の Codex レビューで Luna xhigh と Sol medium を再比較する（レビューモデルの方針決定用）。
- 他のタスクは従来どおり（`config.toml` の既定 = Luna xhigh）。
- **結論（ユーザー判断 2026-09-27）**: Codex 実装エージェントを 2 種にした。`codex-implementer` = Luna xhigh（修正箇所が具体的で量が多くない）/
  `codex-delegating-implementer` = Sol medium + Luna xhigh サブエージェント許可（判断が要る・量が多い）。基準は `agent_selection.md`。
  task_03 以降はこの基準で選ぶ。

## レビュー方針

- 共通観点は `.claude/rules/review.md`。各タスクは `reviewer`、統合（task_08 前）は `deep-reviewer` + `codex-reviewer`、
  フェーズ完了判定前は `deep-reviewer` + `codex-adversarial-reviewer`（`.claude/rules/agent_selection.md`）。
- **本フェーズ固有**:
  - **後方互換**: 既存の hotkey / text / mouse_click だけのシーケンスで、単発・連続実行の結果と位置の動きが変わらないか
    （system が無ければ従来と同じ、を往復テストで固定しているか）。
  - **状態機械の網羅**: ステップ・待機・取り消し・戻すの組み合わせ（待機中の別トリガー実行・取り消し後の古い続き・エラーで止まったステップの戻し）がテストされているか。
  - **UI スレッドを塞がない**: 待機は `after()`、file_line は 1 MB 上限。`time.sleep` 等の同期待ちが入っていないか。
  - **依存方向**: domain の整形・対応判定が application の状態を参照していないか（値は引数で受ける）。
  - **runner の肥大**: ループ・ステップ・履歴を `sequence_runner.py` へ詰め込まず、責務ごとにモジュールを分けているか。
