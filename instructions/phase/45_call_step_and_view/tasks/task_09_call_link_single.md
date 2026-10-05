# task_09_call_link_single

## 目的

**単発の実行**を参照による連動へ切り替える（暫定 31 v0.6 §4.5.1〜§4.5.4・§4.5.5 の積み方・§10-12〜15d）。呼び出し先の状態は呼び出し先トリガー自身の位置・周回・保留とし、写しは使わない。
**application 限定（`call_context.py`・`sequence_runner/{sequence_runner,call_wait,input_acceptance}.py`・必要なら `call_view_notice.py`）。連続実行（`call_run_to_end.py`・`wait_stop.py`）は task_10 まで今の写しの方式のまま動かすこと。presentation・JSON は変えない。**

## 対象範囲（application 限定・単発の経路）

### 設計（推奨: 「押下ごとに文脈を組み立て、押下の終わりに書き戻す」）

今の `CallContext` / `CallFrame` の段の進め方（`_advance_call`・`finish_call_action`・`_finish_returned_call`・`_settle_stopped_call`）は、段の状態を**トリガー自身の状態から読み込み、押下の終わりに書き戻す**形にすれば、ほぼそのまま使える。

1. **押下の開始**: 押したトリガー P に参照中の印がある（task_08 の `call_refs_for`）、または P の位置の行が呼び出しのとき、`call_chain.chain_from(P)` で連鎖を求め、
   P の下の各トリガーを段として `CallFrame(key, position=そのトリガーの位置, frames=周回, deferred=保留)` に積んだ文脈を作る（**写しは作らない**。段のシーケンスは `find_trigger(key)` の今のもの）
   - 印が無く P の位置の行が呼び出しなら、今の `_start_single_call` と同じ検査（参照先なし・循環・深さ・無限ループ・戻す / 先頭へ）を**今のシーケンスで**して、呼び出し先の段を**呼び出し先の今の位置から**積む（先頭へ戻さない・§4.5.1）
   - 段のステップ / 一括の印（`CallFrame.step`・`first_step`）は P から各段までの呼び出しの行の `is_step_call` で決める（§4.5.4 の一括の範囲 = P に最も近い一括の行の呼び出し先）
2. **進める**: 今の `call_step` / `finish_call_action` で、ステップなら最上段の 1 ステップ、一括の範囲があればその呼び出し先の末尾まで（入れ子の呼び出しは押下を消費しない・§4.2 のまま）
3. **押下の終わり（書き戻し）**: 残った段と降ろした段の位置・周回・保留を**各トリガーの状態へ書き戻す**（降ろした段 = 末尾に達して先頭に回った状態）。
   P と残った段のうち、`▶` が呼び出しの行にあり続きの段があるものに印を立て、降ろした段の呼び出し元の印を下ろす。押下の合間に `PendingStep` に文脈を残さない（**合間の状態はトリガーの状態だけ**）
4. **完了の伝播（§4.5.3）**: この押下で末尾に達したトリガー U について、**この押下の連鎖の外で** U に印を立てている呼び出し元 T（`▶` が `call U` で印あり）を、
   トリガー一覧の上から順に、印を下ろして呼び出しの次へ進め先行処理まで（送らない）。T も末尾に達したら同じく T の呼び出し元へ続ける
5. **戻す履歴（§4.5.5）**: 押下の開始時に連鎖の全トリガー（と完了の伝播で動いた T）の `snapshot_for` を取り、押下の終わりに task_08 の `commit_press(...)` で、状態が変わったトリガーに同じ番号で 1 段ずつ積む。
   カウンターの差分は、その操作を実行したトリガー（段のキー）に帰属させる。`last_trigger` = P
6. **連鎖のトリガーの押下（§4.5.2）**: 連鎖に属するトリガー（段・別の呼び出し元）を押したときも、そのトリガーを P として 1〜5 を行う（押したトリガーの単発の設定で動く）
7. **処理中**（待機・file_line の読込中・一括の範囲の実行中）は今の `PendingStep(call=ctx)` で保持してよい。処理中の押下の扱い（同じ連鎖のキーなら一時停止・他は無視・§4.2.10）、一時停止 → 再開は今の単発の呼び出しの一時停止の仕組みを使う。
   一時停止中・処理の取り消しでは、**その時点の段の状態を書き戻す**（位置を呼び出しの行へ戻さない・§4.5.7）

設計を変えたい場合（例: 文脈を常駐させる）は、上の 1〜7 の結果が同じになることを報告に書くこと。

### 一覧の順の取得（2026-10-05 追記・メイン判断）

- 完了の伝播の「トリガー一覧の上から順」のため、`SequenceRunner` に任意のコールバック `list_trigger_keys: Callable[[], Sequence[str]] | None = None`（アクティブなトリガー一覧の有効な行のキーを上から順）を足し、
  `keyseq/presentation/app.py` の `SequenceRunner(...)` 生成に**引数 1 つだけ**配線してよい（presentation の変更はこの 1 か所に限る）。None のとき（テストの簡易な生成）はキーの文字列順で代える

### 呼び出し元の扱いで変わる点（今の単発の呼び出しとの差）

- 押下の合間に `call_paused` の保留を残さない（押下の合間に他のトリガーが動いても、捨てる対象が無い）
- 呼び出し先トリガー自身の位置・周回・保留・戻す履歴が変わる（§4.2.9 の「変えない」を廃止）
- 呼び出しの成功 = この押下で呼び出し先の段が降り、P が呼び出しの次へ進んだとき

### テスト（追加・修正まで）

- `tests/test_sequence_runner_call.py`・`tests/test_call_context.py` のうち**単発の写し・合間の一時停止・呼び出し先の状態を変えない**ことを前提にしたテストを v0.6 に合わせて直す（連続実行のテストは task_10 まで変えない）。直したテストの一覧と理由を報告に書く
- 追加（単発・ステップ）: §10-12（X → a / A → b / A → c で X が B へ・B は送らない）/ §10-13（X を押していなければ A を末尾まで進めても X は動かない・A を途中まで進めてから X で続きから）/
  §10-14（X・Y が A を参照・どれを押しても同じ A・A の末尾で X・Y ともに次へ）/ §10-15（c の後に戻すと c の前・次の押下で c を送り直す・X・Y 交互でも A の新しい順）/
  §10-15a（`[call all A]`・A = `[call U, d]`・U = `[a, b]` で 1 押下 a・b・d）/ §10-15d（入れ子の完了を戻すとカウンターも戻る）/ 呼び出し先を選ぶと `▶`（`indices`）が呼び出しで進んだ位置
- 既存の単発の非呼び出しのテストは変えずに通ること

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §4.2・§4.5（全体）・§10-12〜15d
- `keyseq/application/call_context.py`（全体）・`keyseq/application/call_chain.py`・`keyseq/application/sequence_history.py:1-140`（task_08 の `commit_press`・`snapshot_for`）・`keyseq/application/app_state.py:1-60`
- `keyseq/application/sequence_runner/call_wait.py`（全体）・`input_acceptance.py`（全体）・`sequence_runner.py:60-130`・`:215-300`（`_run_single_action`）
- `tests/test_sequence_runner_call.py`（単発の部分。手本と書き直し対象）

## 含まない

- 連続実行の連動・「送った」・停止の行・一時停止中の連続実行への合流（task_10）
- 停止操作・ダイアログ・キーマップ切替で印を残す扱い・表示の要約の問い合わせと枠の中身の切替（task_11）
- `domain/call_graph.collect_call_snapshot` の削除（連続実行が使うため task_10 で）/ presentation

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加・修正したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass（tests_ui は verifier 1 つで）

## 完了条件

- 上記確認 pass・**reviewer 採用**。直したテストの一覧が v0.6 の条項で説明できること。
- 実機目視は task_11 の後にまとめて実施（単発の連動は task_11 の枠の切替と合わせて見る）。
