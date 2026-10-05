# task_07a_review_decisions

## 目的

task_07 の完了判定前レビュー（deep-reviewer M2・M4）でのユーザー確定（2026-10-05・decisions.md 末尾）を実装する。正本は task_07 で先に改訂済み:
`features.md` §4.2.9「押下と実行」の「一時停止中の呼び出し先」・事象の表の「呼び出し先（連鎖の段）の位置変更…」の行 / §4.2.10「捨てる操作と知らせ方」。
**application 限定（`sequence_runner/` 配下と `call_context.py`）。presentation・JSON は変えない。**

## 対象範囲（application 限定）

### M2: 単発の呼び出しの実行中に連鎖の呼び出し先の状態を変えたら、その単発の呼び出しを取り消す

- 現状: `SequenceRunner.reset_loop_frames(U)`（`sequence_runner.py:231`）は `(一覧, U)` の保留しか取り消さない。別のトリガー P の単発の呼び出し（`PendingStep.call` が `CallContext`・**一時停止していない**）が U を段に持っていると、
  その文脈が U の古い位置を持ったままになり、次の書き戻し（`linked_call.py` の `_write_linked_progress`）で、ユーザーが変えた U の位置・内容が上書きされる（deep-reviewer の静的推論・**まずテストで再現する**）
- 変更: `reset_loop_frames(U)` で、U を使っている（`_call_context_uses_key` = root_key・first_target・stack の段）**一時停止していない単発の呼び出し**の保留を、`_cancel_pending_steps` と同じ経路で取り消す（そこまでの進みは書き戻す・履歴は今の規則どおり）。
  **ただし U の位置・周回・保留は、呼び出し側（presentation）が先に `_indices[U]` へ入れた新しい位置を優先する**（取り消しの書き戻しで U を古い位置へ戻さない。取り消しの前に U の新しい位置を控え、書き戻しの後に戻す等）。
  その後は今の `reset_loop_frames` の処理（U の状態を消す・周回の張り直し）を続ける
- 一時停止中の単発の呼び出しは対象外（一時停止の時点で書き戻し済みで、再開は今の状態から組み立て直すため。§4.2.10 の M1 の確定どおり）。連続実行は対象外（実行中は presentation 側の `is_running_chain_callee` で断る・一時停止中は今のまま）
- 取り消した P の位置と参照中の印は取り消した時点のまま残る（§4.2.10「捨てる」）。通知は出さない（待機・file_line の位置変更による取り消しと同じ）

### M4: 呼び出し先が単発の呼び出しの一時停止中なら、その一時停止を捨てて進める

- 現状: `call_context.py:169-172` は、段に入る U が `pending_steps` にあれば `CallStep("ignored")` を返す。U が**単発の呼び出しの一時停止中**（`PendingStep.call_paused`）でも無視になり、単発の T は押下の巻き戻し（`call_wait.py:133-139`）で黙って何も起きない
- 変更: U の保留が**単発の呼び出しの一時停止**なら、無視せずにその一時停止を捨てて（今の `discard_paused` / `_pending_control_discard` と同じ「捨てる」= 進行中の処理だけを取り消し、位置と印は残る）
  「一時停止中の実行を破棄しました（<キー>）」の通知を出し、T の設定で U を進める。U の保留が単発の待機・file_line の読込中なら今のまま（無視・連続実行の T の待機は §4.2.10 の取り消しを優先）
- 捨てる処理は runner 側（通知の口を持つ側）で行う。`call_context.py` は「一時停止中の呼び出しの保留がある」ことを判別できる戻り値（例 kind = `"paused_callee"` とキー）を返すか、runner が段に入る前に検査するかは実装者が選ぶ（UI・通知への依存を `call_context.py` に持ち込まないこと）
- 単発の T・連続実行の T の両方。連続実行の T は既に「一時停止中のものを全部捨てて開始」で U の一時停止が捨てられている場合があるので、二重に通知しない

### テスト（追加・修正まで）

- `tests/test_sequence_runner_call.py` か新規 `tests/test_call_review_decisions.py` に:
  - M2: X（f1）= `[call all A]`・A（f5）= `[a, 待機 100, b]` で X を押して待機中に、A の位置を 0 へ変える（`state.indices_for(...)["f5"] = 0` の後 `reset_loop_frames("f5")` = presentation と同じ順）→ X の単発の呼び出しの保留が無くなり、A の位置は 0 のまま（上書きされない）・X の印は残る・b は送られない
  - M2: 同じ操作を X の単発の呼び出しの**一時停止中**に行うと、X の一時停止は残り、再開で A の位置 0 から続く
  - M2: 連鎖に入っていないトリガーの位置変更では X の保留は取り消されない
  - M4: U = `[call all V]`・V = `[v1, 待機 100, v2]` で U を押して待機中に U を押して一時停止 → T = `[call U]`（単発）を押すと、U の一時停止が捨てられ通知が出て、T が U を進める（v2 を送る等・期待値は実装の規則で確定）
  - M4: U が単発の待機中・file_line の読込中なら、従来どおり T の押下は無視（既存テストが通ること）
- 既存テストは変えずに通ること（変える必要があれば理由を報告に書く）

## 読むファイル

- 正本 `instructions/common/spec_detail/features.md` §4.2.9「押下と実行」・事象の表 / §4.2.10（「捨てる」「捨てる操作と知らせ方」）
- `keyseq/application/sequence_runner/sequence_runner.py:86-152`・`:190-268`（`has_active_execution`・`_call_context_uses_key`・`_cancel_pending_steps`・`reset_loop_frames`）
- `keyseq/application/call_context.py:140-180`（段に入る `_push_frame` と ignored）
- `keyseq/application/sequence_runner/call_wait.py:120-160`（単発の段の進行と巻き戻し）・`call_run_to_end.py:110-160`
- `keyseq/application/sequence_runner/input_acceptance.py`（全体・一時停止と捨てる・通知）
- `keyseq/application/sequence_runner/linked_call.py`（全体・書き戻し）
- `tests/test_sequence_runner_call.py:1031-1075`・`:632-700`（テストの組み方）

## 含まない

- presentation の変更（`reset_loop_frames` の呼び出し元はそのまま）
- 提案書 19 のリファクタ（ユーザー判断待ち）
- 正本の改訂（task_07 で済み）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストが pass・`-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass（tests_ui は verifier 1 つで）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視: 任意（M4 の通知を見る程度。ユーザー判断）
