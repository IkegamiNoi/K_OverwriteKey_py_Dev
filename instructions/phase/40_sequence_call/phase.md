# phase.md

## フェーズ名

出力シーケンスの制御アクション・第 2 弾 後半 = 他トリガーの呼び出し（sequence_call）

## フェーズの目的

出力シーケンスの system 種別に**呼び出し**（`op: call`・`target`）を加え、同じトリガー一覧の別トリガーの出力シーケンスを部品として丸ごと実行して戻れるようにする。

**JSON スキーマ変更あり**（op と `target` の追加のみ）。**全レイヤに跨る**（domain の判定・表示 / application の呼び出し文脈と単発・連続実行への組み込み / presentation の編集・表示・改名・間隔の欄）。

- 起票元: 暫定 28 §9（phase 39 で分離した申し送り）/ 暫定 26 §13 / ユーザー判断「phase 40 に着手」（2026-09-28）。
- 主入力（暫定仕様）: [29_sequence_call.md](../../history/29_sequence_call.md)（v0.3・ユーザー確定済 2026-09-28）。
- モード: **暫定仕様先行モード**。番号対応: phase 40 / 暫定 29 / decisions 40。

## 確定（ユーザー 2026-09-28）

暫定仕様 29 §2 が正。要点:

- 呼び出し先を先頭から末尾まで一括で実行して戻る（呼び出し先の位置は変えない・単発でも 1 押下）。呼び出しは押下を消費するアクション。
- 呼び出し中も他のトリガーは動く / 入れ子は深さ 9 まで / 呼び出し先の中の停止は読み飛ばす / 無限ループは実行時エラー。
- 開始時点のコピー（辿れる呼び出し先の内容と間隔）で最後まで実行。間隔 = 呼び出し先の「間隔(ms)」（連続実行 OFF でも欄を編集可能に）。
- 打ち切りは呼び出しの行に残す / 連続実行の一時停止は続きから / キー変更で参照を書き換える / 表示 `[call] f5（ラベル）` / グレー表示のトリガーも呼べる。

## スコープ

### 含む

暫定仕様 29 の §3〜§6 と §8 の受け入れ条件。

### 含まない（後送り）

暫定仕様 29 §10（他のトリガー一覧の呼び出し・引数 / 呼び出し中の表示 / 送信エラーへの連鎖の付加 / カウンター条件分岐）。

## このフェーズで読むファイル

1. [暫定仕様 29](../../history/29_sequence_call.md)（主入力。§1 の現状監査に `ファイル:行` の入口あり）
2. `instructions/common/spec_detail/features.md` §4.1・§4.2（4.2.1〜4.2.8）・§4.3・§4.6、`data_schema.md` §5.11
3. `instructions/common/codebase_map.md`「出力シーケンスの制御アクション」節
4. 実装の入口（タスクごとに該当分のみ）: `keyseq/domain/{sequence_control,sequence_editing,config}.py` / `keyseq/application/{sequence_steps,sequence_history,app_state}.py`・`sequence_runner/` /
   `keyseq/presentation/dialogs/{action_control_fields,action_dialog}.py`・`controllers/action_list_rendering.py`・`controllers/trigger_panel/`

## タスク

依存順。各タスクの定義は着手時に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

- task_01: domain（暫定 §3・§5・§6: `OP_CALL`・`target` の trim・表示〔解決関数を引数〕/ 開始時点のコピーの収集・循環・下流の深さ・直接の呼び出し先が戻す / 先頭へだけの判定〔純関数〕） — **完了**（2026-09-28。新規 `domain/call_graph.py`・`resolve_call` 引数）
- task_02: ステップの進め方（暫定 §4.1・§4.4: `advance` / `settle_after_normal` が呼び出しの行で止まる / 呼び出し文脈の中では無限ループの始まりでエラー） — **完了**（2026-09-28。`in_call` 引数）
- task_03: 呼び出し文脈の中核（暫定 §4.2・§4.4: 文脈とスタックの型・「文脈の 1 ステップ」〔単発・連続で共有〕・深さ / 循環 / 参照先なし・末尾での段の降ろしと保留の反映・差分） — **完了**（2026-09-28。新規 `application/call_context.py`〔`start_call` / `call_step` / `finish_call_action`〕）
- task_04: 単発実行への組み込み（暫定 §4.3・§4.5・§4.6 単発列: `PendingStep` の文脈・間隔の予約・差分の積み増し・通知の後の再照合・呼び出し元の照合・完了後の先行処理・打ち切り・通知の連鎖） — **完了**（2026-09-28。新規 `sequence_runner/call_wait.py`〔`CallWaitMixin`〕・`PendingStep.call`）
- task_05: 連続実行への組み込み（暫定 §4.3・§4.5・§4.6 連続列: 一時停止の保持と再開・停止・位置変更での続行・文脈の中の待機 / file_line・読み飛ばしの印） — **完了**（2026-09-28。新規 `sequence_runner/call_run_to_end.py`〔`CallRunToEndMixin`〕）
- task_06: 編集ダイアログ（暫定 §6: 「呼び出し」・呼び出し先のドロップダウン・参照先なしの初期値・OK 時の拒否） — **完了**（2026-09-28。reviewer 指摘で例示の f5 の埋め込みを修正・実キーで表示）
- task_07: 一覧の表示と間隔の欄（暫定 §6: 解決関数の配線・`[call] f5（ラベル）`・参照先なし / 間隔の欄を連続実行 OFF でも編集可能に） — **完了**（2026-09-28。見出しは据え置き・注記は編集ダイアログに〔暫定 29 v0.4〕）
- task_08: キー変更時の参照の書き換え（暫定 §5）・実機目視 — コード完了（2026-09-28。`call_graph.rename_call_targets`）。実機目視（2026-09-28）: 項目 5 以外は問題なし・項目 5 は v0.6 で仕様変更（task_09c/09d の後に再目視）
- task_09: 統合確認（統合レビュー = deep-reviewer + codex-reviewer） — レビュー実施済（deep-reviewer 修正して採用 / Codex P2 1 件）
- task_09b: 統合レビューの修正（暫定 29 v0.5: 値の欄 / 連続実行のエラー後の照合と一時停止 / 上限を 1 ステップ全体で通して数える / 文言 / テスト補完） — **完了**（2026-09-29。reviewer 完了可）
- task_09c: 入力の受け付けと一時停止（暫定 29 v0.6 §4.7 の application 側: 押下の判定・単発の呼び出しの一時停止・待機明け・確認して捨てる口・`can_switch_keymap`）
- task_09d: 警告のダイアログと配線（暫定 29 v0.6 §4.7 の presentation 側: ダイアログ・キーマップの切替 / 削除・確認中の切替キーの無視）・task_08 と合わせて実機目視
- task_10: 正本反映（暫定 29 §11 / 暫定 29 の凍結 / `decisions_archive/40_sequence_call.md` / current.md 完了記載 / `/refactor_check`）

## レビュー方針

- 各タスク: reviewer（5 観点）。**呼び出しを含まないシーケンスの既存挙動の不変**を必ず確認する。
- 重点: 戻す履歴（状態が変わったときだけ 1 段・呼び出し先の差分を含む・二重に積まない）/ 世代・トークンの照合（通知の後・一時停止・打ち切り）/ 開始時点のコピー / 文脈の中の待機・file_line。
- テストで履歴を確かめるときは状態が変わるシーケンスにし、カウンターは `counters.get(name, 0)` で見る（phase 38・39 の教訓）。検出力は変異検査で確かめる。
- 統合・フェーズ完了判定前は deep-reviewer + Codex レビュー（`.claude/rules/agent_selection.md`）。
