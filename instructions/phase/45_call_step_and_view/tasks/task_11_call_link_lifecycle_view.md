# task_11_call_link_lifecycle_view

## 目的

参照による連動の仕上げとして、①**参照中の印の後始末**を §4.5.1 の契機どおりに揃え、②呼び出し先の表示を**選んでいるトリガーの連鎖を問い合わせる方式**へ切り替える（暫定 31 v0.6 §4.5.1・§4.5.7・§5.2・§5.3 の v0.6 部分・§10-16・§10-17）。
**application（`call_view.py`・`sequence_runner/call_view_notice.py` ほか印の後始末に要る所）+ presentation（`call_view_controller.py`・`app.py` の配線・印の後始末の呼び出し元）。JSON・config.json は変えない。省略表示の枠は task_06。**

## 対象範囲

### A. 表示の要約の問い合わせ方式（application）

- 新しい公開の口 `SequenceRunner.call_view_summary_for(key: str) -> CallViewSummary | None`: アクティブなトリガー一覧で `call_chain.chain_from(key)` をたどり、2 段以上なら**最上段**の要約を返す
  （経路 = 連鎖のキー〔正規化後〕・行 = 最上段の今のシーケンスの複製・位置 / 周回 = 最上段の状態・カウンターの写し）。**処理中で状態の書き戻し前**（押下の途中・連続実行のステップの途中）は、その連鎖を持つ実行中の文脈の段の値を優先する
- 通知の口は「表示が変わり得る」ことだけを知らせる形にする: `notify_call_view: Callable[[], None]`（引数なし）。呼ぶ契機は今の `_publish_call_view` の呼び出し箇所のまま（状態・位置・印・カウンターが変わり得るとき）
- **廃止**: `CallViewMixin` の「止まった順・最後に止まった文脈」の管理（`_call_view_contexts`・`RUN_TO_END_CALL_VIEW`）と、task_09 の表示用の橋渡し（`changed_frames` を書き換える部分）。`build_call_view_summary` は新しい口の材料として残すか置き換える

### B. 枠の中身の切替（presentation）

- `CallViewController` は通知を受けたら、選んでいるトリガー S で `call_view_summary_for(S)` を問い合わせて描き直す（`on_selection_changed` も同じ）。`last_summary` で前の要約を覚える方式はやめる
- 自動で開く = S の要約が None でない（S に参照中の印がある）とき、S が手で操作されていなければ開く（§5.2）。自動では閉じない。None なら「呼び出し中ではありません」
- `app.py` の配線を新しい口に合わせる（`notify_call_view=self.call_view.on_changed` 等）

### C. 参照中の印の後始末（§4.5.1・§4.5.7）

以下の契機ごとに、**印が残る / 消える**が仕様どおりかを確かめ、違えば直す（多くは task_08〜10 で済んでいるはず。テストで固定するのが主）:

| 契機 | 印 | 位置 |
|---|---|---|
| フック停止・ダイアログを開く（`hook_controller.stop_hook`）・キーマップ一時停止・UI 編集の一時停止 | **残る** | 途中のまま（処理中の予約・待機の残り・読込中は取り消す） |
| キーマップの切替（往復） | **残る**（トリガー一覧ごとの状態として） | 途中のまま |
| 一時停止 → 再開 | 残る | 続きから |
| 呼び出し元 T の位置の変更・シーケンスの編集・削除・有効な行の交代 | T の印が**消える** | 既存の規則 |
| T のキー変更 | 新しいキーへ**移る** | 既存の規則 |
| 呼び出し先 U の編集・削除・キー変更 | T の印は残る（U の状態は既存の規則。削除なら次の押下で「参照先なし」のエラーで T の印が消える） | — |
| 呼び出しのエラー | 消える | 呼び出しの行 |
| 構成セットの読込等（状態の全消去） | 消える | 全消去 |
| 先頭へ（対象 T） | T の印が消える（参照先はそのまま） | 0 |

- §10-16: 呼び出しの途中でダイアログを開いても（フック停止）、呼び出し元・呼び出し先の位置と印が残り、フック再開後に続きから進む

### テスト（追加・修正まで）

- application: `call_view_summary_for` の単体（印なし → None・2 段 / 3 段で最上段・処理中は文脈の値・カウンターの写し）/ 上の表の各契機（runner または app_state の水準で）
- presentation（`tests_ui/test_call_view_frame.py` ほか）: 選んでいるトリガーで中身が切り替わる（f1 を選ぶと f1 の連鎖・f2 を選ぶと f2 の連鎖・印の無いトリガーは「呼び出し中ではありません」）/
  task_09 で外した「表示が前の文脈へ戻る」確認を、選択の切替で書き直す（`test_call_view_selects_last_stopped_context_then_restores_previous` の後半）/ 印が立つと自動で開く・手で閉じたら開かない（task_05a の確認を新しい通知の形で）/
  §10-16（フック停止を挟んで続きから）
- 通知の形の変更に合わせて既存のテスト（`tests/test_sequence_runner_call.py` の `call_views` を使う確認・`tests_ui/test_call_view_frame.py`）を直す。**直したテストの一覧と根拠の条項を報告に書く**

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §4.5.1・§4.5.7・§5.2・§5.3・§10-16・§10-17
- `keyseq/application/sequence_runner/call_view_notice.py`・`keyseq/application/call_view.py`・`keyseq/application/call_chain.py`（全体）
- `keyseq/application/sequence_runner/linked_call.py`（全体）・`sequence_runner.py:60-130`
- `keyseq/presentation/controllers/call_view_controller.py`（全体）・`keyseq/presentation/app.py:205-230`
- `keyseq/presentation/controllers/hook_controller.py:150-190`・`keyseq/application/app_state.py:100-180`（後始末の入口）
- `tests_ui/test_call_view_frame.py`・`tests/test_sequence_runner_call.py`（`call_views` を使う部分）

## 含まない

- 省略表示の枠（task_06。本タスクの問い合わせの口を使う）/ 正本反映（task_07）
- 経路のクリックで上の段を見る・枠からの編集（スコープ外）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加・修正したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass（tests_ui は verifier 1 つで）

## 完了条件

- 上記確認 pass・**reviewer 採用**。直したテストの一覧が v0.6 の条項で説明できること。
- 本タスクの後に task_08〜11 の**統合確認**（`deep-reviewer` + `codex-reviewer`）。
- **実機目視（本タスクの後にまとめて実施）**: 呼び出しの連動（§10-12〜16）と枠の中身の切替。
