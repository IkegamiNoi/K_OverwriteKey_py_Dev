# task_10a_completion_review_fixes

## 目的

フェーズ完了判定前レビュー（deep-reviewer / codex-adversarial-reviewer）で採用した実装側の指摘を直す（ユーザー判断 2026-10-01・推奨どおり）。
application のみ。正本の文言修正は task_10（メイン）で行う。

## 対象範囲

1. **戻す / 先頭へだけのトリガーは連続実行 ON でも 2 回押し**（deep M1）
   - 現状: `sequence_runner/input_acceptance.py` `_accept_key` の連続実行トリガーの分岐（`discard_paused()` → `_start_run_to_end`）が、
     `_prepare_control_target` の 2 回押しより先に一時停止中のものを**すべて**捨てる。
   - 直す: 出力シーケンスが戻す / 先頭への 1 行だけのトリガーは、連続実行 ON でも先に `discard_paused()` をしない
     （単発と同じく戻す / 先頭への実行経路 → `_prepare_control_target` の 2 回押しに任せる。対象が一時停止中でなければ従来どおり実行）。
     判定は domain の既存の関数（`sequence_control` / `sequence_editing` の単独登録の判定）があれば使う。
2. **連続実行の呼び出しのタイマーの照合を厳密に**（Codex High 1）
   - 現状: `sequence_runner/call_run_to_end.py` `_run_to_end_call_matches` が `token + 1 == current_token` も一致扱いにし、タイマーの入口 `_run_to_end_call_is_current` もそれを使う。
     一時停止前に予約したコールバックが（取り消しが効かなかった場合）再開後に通る。
   - 直す: タイマーの入口と成功後の継続（`_run_to_end_call_is_current` の全呼び出し元）は**トークンの完全一致**を求める。
     「1 回分のずれ」を許すのは、通知の後の失敗の確定（エラー・送信失敗・file_line の失敗の後の照合。暫定 29 §4.5「一時停止を含めない」）に限る。
     どの呼び出し元がどちらに当たるかを確認して分ける（既存テストの意図を変えない）。
3. **呼び出しの文脈の 1 ステップの処理数を、送る前から送った後の先行処理へ通算**（Codex Medium 3）
   - 現状: `application/call_context.py` `call_step`（`_advance_call`）で数えた `processed` が `CallStep` に残らず、`finish_call_action` は 0 から数える。
   - 直す: 送る前の処理数を文脈（例: 最上段の `CallFrame` か `CallContext`）に保持し、`finish_call_action` の先行処理（入れ子から戻る `_finish_returned_call` を含む）へ引き継ぐ。
     送信の後に 0 へ戻す（次の文脈のステップは新しく数える）。file_line の読込中の保留をまたいでも保つ。通常経路（`advance` の `processed` を `settle_after_normal` へ渡す）と同じ意味にする。

## テスト（追加・修正まで。実行は依頼しない）

- 1: 一時停止中の連続実行 / 単発の呼び出しがあるとき、連続実行 ON の `[back]`（`[rewind]` も）トリガーの 1 回目は何も捨てず通知だけ・位置も変えない / 続けてもう一度で対象だけ捨てて実行 /
  無関係の一時停止中のものは残る。対象が一時停止中でなければ従来どおり実行。
- 2: 連続実行の呼び出し中に予約したコールバックを保存しておき、一時停止 → 再開の後に呼んでも文脈が進まない（再開後の予約だけが進める）回帰テスト。
  通知の表示中の一時停止で失敗を確定する既存テストは pass のまま。
- 3: 呼び出し先が `[stop × 6000, A, stop × 6000]` のように、送る前と後の合計が 10,000 を超えると上限のエラーになる / 合計が 10,000 以下なら成功する。
- deep L1: 連続実行 `[A, 待機, 停止, B]` の待機中に一時停止すると、待機を終えた扱いの先行処理で停止の行に達して連続実行が終わる（位置 B〔停止の次〕）。
  task_09f で削除された旧テストの代わり。
- deep L10: `tests/test_sequence_runner.py` の `test_single_wait_expiring_during_continuous_work_skips_next_action` を v0.8 の内容に合う名前へ改める（中身は変えない）。

## 読むファイル

- `keyseq/application/sequence_runner/{input_acceptance,call_run_to_end,sequence_runner,wait_stop}.py`・`keyseq/application/call_context.py`・`keyseq/application/sequence_steps.py`（`advance` / `settle_after_normal` の `processed`）
- `keyseq/domain/sequence_control.py`・`keyseq/domain/sequence_editing.py`（単独登録の判定）
- `tests/test_sequence_runner.py`・`tests/test_sequence_runner_call.py`・`tests/test_call_context.py`・`tests/test_sequence_runner_stop.py`
- 仕様: `instructions/common/spec_detail/features.md` §4.2.5・§4.2.9・§4.2.10（未コミットの正本反映を含む）

## 含まない

- presentation / 正本・暫定仕様の文書 / 呼び出しの文脈の中の待機の間隔（仕様どおり・変えない）/ deep L8（キーマップの切替・削除の失敗時の順序・受容）
