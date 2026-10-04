# task_03a_integration_review_fixes

## 目的

task_02・03 の統合確認（deep-reviewer 採用 / codex-reviewer P2 1 件）で見つかった不具合と軽微な指摘を直す（暫定 31 v0.4 §4.1・§4.2）。
**application（`call_context.py`・`sequence_runner/call_wait.py`）とテスト。挙動の変更は P2 の不具合の修正だけ。**

## 対象範囲

### P2（不具合・メインで再現済み）: 入れ子の一括の呼び出しの最後に待機があると、ステップの境界を越えて送る

- 再現: 呼び出し元 `[call step f5, X]`・`f5 = [call f7（一括）, B]`・`f7 = [A, wait 100]` を単発で 1 回押すと、**A と B が両方送られる**（正しくは A を送り、待機を待ち、f7 の段を降ろした時点で**押下の合間**に入る。B は次の押下）。
  `f7 = [A]`（待機なし）なら正しく A で止まる
- 原因（codex-reviewer）: 最上段が一括の段の間は `call_wait.py:247-252` が続きを予約する。最後の待機が明けた後の `call_step` の中で `_advance_frame` が f7 の段を降ろし、そのまま一時停止の判定を通らずに親の段の B まで進む
- 直し方: **`call_step` の中で一括の段を降ろしてステップの段へ戻ったとき、その段（入れ子の一括の呼び出し）で何か送っていれば、そこで 1 ステップの区切りとして返す**（例 `kind="next"` 相当を返し、`call_wait.py` 側の「最上段がステップなら押下の合間へ」に乗せる）。
  何も送っていない一括の段（空の呼び出し先など）は押下を消費しない現行のまま（§4.2）。連続実行の経路（`call_run_to_end.py`）でも同じ区切りで間隔が入ることを確認する（連続実行では区切りの後に通常の間隔で次のステップ）

### deep-reviewer の軽微な指摘

- L2: 単発の経路で `kind == "stopped"` を受けた場合の防御（今は `run_to_end=False` で届かない）: 受けたら呼び出しの成功 / 打ち切りのどちらとも扱わず、例外にせず `_drop_single_call` 相当で後始末する（保留を宙に残さない）。コメントで「単発では届かない」と書く
- L3: `call_context.py` の `_finish_returned_call` の docstring と、呼び出し側の変数名 `failure` を、`stopped` も返す今の意味に合わせる（`:229-230`・`:316`・`:340` 付近）

### テスト（追加・修正まで・`tests/test_sequence_runner_call.py`）

- P2 の再現ケース（上記）: 1 押下目は A だけ・合間に入る / 2 押下目で B / 3 押下目で X。待機なしの `f7 = [A]` も同じ結果
- 連続実行で同じ形（`call step f5` の中の一括 f7 に最後の待機）: A → 待機 → 区切り → 間隔 → B と進む
- L5 から 3 本:
  - 押下の合間にフック停止（`cancel_pending_waits`）→ 文脈が消え、位置は呼び出しの行・履歴 1 段
  - 連続実行の停止による一時停止と、単発の押下の合間の併存 → `paused_keys` に両方・それぞれ独立に再開できる
  - ステップの連続実行で、`handle_key` で同じキーを押して一時停止 → `handle_key` で再開して続きから（§10-6 のステップ側）
- L6: `test_same_key_during_step_call_wait_is_ignored_but_batch_call_still_pauses` の途中の `self.setUp()` 呼び直しをやめ、2 つのテストに分ける

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §4.1・§4.2
- `keyseq/application/call_context.py`（全体）
- `keyseq/application/sequence_runner/call_wait.py:100-135`・`:240-260`
- `keyseq/application/sequence_runner/call_run_to_end.py:100-140`・`:240-270`
- `tests/test_sequence_runner_call.py`（ステップの単発・連続実行のテストの節）

## 含まない

- deep-reviewer M1（文脈の「送った」に入れ子の呼び出しの成功を数えるか）は task_07 の正本反映で文言を決める（実装は現行 = 通常アクションを送ったときだけ）
- L1（停止の後の先行処理の上限 10,000）・L4（サイズ）・L7（合間の戻すの対象）は保留（decisions に記録）
- 表示の要約・枠（task_04 以降）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加・修正したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_02・03 とまとめて本タスクの後に実施（task_03 の完了条件 ①〜④）。
