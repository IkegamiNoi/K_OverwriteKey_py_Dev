# task_10_call_link_run_to_end

## 目的

**連続実行**の呼び出しを参照による連動へ切り替え、写し（`collect_call_snapshot`）を廃止する（暫定 31 v0.6 §4.3 の v0.6 読み替え・§4.5.2・§4.5.3・§4.5.5・§4.5.6・§10-4・§10-15b・15c・15e）。
**application 限定（`call_context.py`・`sequence_runner/{call_run_to_end,wait_stop,sequence_runner,input_acceptance,call_wait}.py`・`domain/call_graph.py` の写しの関数）。presentation・JSON は変えない。**

## 対象範囲（application 限定・連続実行の経路）

### 実行（task_09 の単発と同じ組み立て・書き戻しを連続実行にも使う）

- 連続実行の呼び出しの開始（`_begin_run_to_end_call`）を `start_call`（写し）から task_09 の `start_linked_call`（各トリガーの今の状態・今のシーケンス）へ。呼び出し先は今の位置から
- 連続実行の**各ステップの終わり**に、task_09 と同じく段の状態を各トリガーへ書き戻し、印を立て / 下ろし、完了の伝播（§4.5.3・一覧順）をし、`commit_press`（押したトリガー = 連続実行のキー）で状態が変わったトリガーに同じ番号で 1 段ずつ積む（§4.5.5「連続実行は現行どおりステップ単位」）
- 呼び出し先の間隔・待機・file_line・入れ子・一括の範囲（§4.5.4）は今の連続実行の呼び出しの扱いのまま

### 停止の行と「送った」（§4.5.6）

- 「送った」は**連続実行 1 回ごと**（`_run_to_end_sent`）。開始から、連鎖のどの段で送った通常アクション・file_line の完了・呼び出しの成功も数える。文脈ごとの印（`CallContext.sent`・`CallFrame.sent` の停止判定への使用）は廃止する
- その連続実行で送った後に**最上段の停止の行**に達したら §4.3 の 1（文脈が残る → 連続実行の一時停止）/ 2（停止の後の先行処理で呼び出しが完了まで進んだ → 呼び出し元の先行処理をして連続実行を終える）
- 押し直して始めた連続実行（呼び出し先を直接押した場合を含む）は送っていない状態から数える。一時停止 → 再開では数え直さない
- **§10-4a（v0.5 の互換条件）は v0.6 §4.5.6 で置き換わる**（一括の呼び出しで送った後に位置を停止の行へ移して再開すると、その連続実行で送っているので止まる）。§4.5 が §4.2〜§4.4 に優先する（暫定 31 冒頭）。§10-4a を前提にした既存テストは §4.5.6 に合わせて直す

### 一時停止との交差（§4.5.2・§4.5.3）

- 一時停止中・処理の取り消し・停止操作では、**その時点の段の状態を書き戻す**（位置を呼び出しの行へ戻さない）。印は残す（停止操作で印を残す扱いの全体は task_11 だが、連続実行の取り消しの書き戻しは本タスク）
- 一時停止中の連続実行 X がある間に、同じ連鎖の別のトリガー（A・Y）を押したら、**押したトリガーの設定で最上段を進める**。X は一時停止のまま。押したトリガーが連続実行なら、今の §4.2.10 どおり一時停止中のものを捨てて（進行中の処理の取り消しだけ）開始し通知する
- 一時停止中の X の呼び出し先が別の押下で完了したら、X は**位置だけ進め（先行処理まで・送らない）一時停止のまま**。先行処理で X が末尾に達したら X の連続実行を終える
- `wait_stop.py`（待機中の一時停止で終える処理）の「呼び出しの文脈があるときは何もしない」を、連動の状態（印のある連鎖）に合わせて見直す

### 写しの廃止

- `domain/call_graph.collect_call_snapshot`・`CallEntry` と、`CallContext.snapshot` / `ctx.state is None` の分岐（写しの方式）を削除する。他に使う所が残らないこと（`grep -rn "collect_call_snapshot\|\.snapshot\b" keyseq`）。編集時の検査（`edit_call_violation` 等）は残す

### テスト（追加・修正まで）

- `tests/test_sequence_runner_call.py` の連続実行のテスト・`tests/test_call_graph.py` の写しのテスト・`tests/test_call_context.py` の写しの前提を v0.6 に合わせて直す。**直したテストの一覧と根拠の条項を報告に書く**
- 追加: §10-4（ステップの呼び出し先の停止の行で、送った後なら連続実行の一時停止・再開で停止の次から / `[A, 停止]` の形は一時停止にせず終える）/ §10-15b（X の連続実行が A の中で一時停止中に単発の Y で A を末尾まで → X は次の行へ進み一時停止のまま・再開でそこから）/
  §10-15c（A = `[a, 停止, b]` を X の単発で a まで → X を連続実行で押し直すと停止を読み飛ばして b）/ §10-15e（X の一時停止中に連続実行の Y で A → X の一時停止は捨てられ〔位置と印は残る〕通知・Y が動く）/
  一時停止中の X の呼び出し先の完了で X が末尾に達したら X の連続実行が終わる / 連続実行の各ステップで呼び出し先の位置が書き戻され、戻すで段ごとに戻る

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §4.3・§4.5（全体）・§10-4・§10-15b〜15e
- `keyseq/application/call_context.py`（全体）・`keyseq/application/sequence_runner/call_run_to_end.py`（全体）・`wait_stop.py`（全体）
- `keyseq/application/sequence_runner/call_wait.py:114-210`（task_09 の書き戻し・伝播・積み方の手本）・`sequence_runner.py:60-130`・`:300-480`（連続実行の開始・停止・一時停止）
- `keyseq/domain/call_graph.py`（写しの関数の削除範囲）
- `tests/test_sequence_runner_call.py`（連続実行の部分）

## 含まない

- 停止操作・ダイアログ・キーマップ切替で印を残す扱いの全体と、編集等で印を消す後始末の統合（task_11）
- 表示の要約の問い合わせ方式・枠の中身の切替（task_11）/ presentation

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加・修正したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass（tests_ui は verifier 1 つで）

## 完了条件

- 上記確認 pass・**reviewer 採用**。直したテストの一覧が v0.6 の条項で説明できること。
- 実機目視は task_11 の後にまとめて実施。
