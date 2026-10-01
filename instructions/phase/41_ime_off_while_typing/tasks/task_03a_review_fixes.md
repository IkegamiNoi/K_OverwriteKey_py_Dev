# task_03a_review_fixes

## 目的

phase 41 の完了判定前レビュー（deep-reviewer 修正要 / Codex 敵対的 needs-attention）で採用した修正を入れる（ユーザー判断 2026-10-01・推奨どおり）。
仕様の正 = 改訂済みの正本 `instructions/common/spec_detail/key_input.md` §7.7（phase 41 の項目）。判断 = `.claude_data/state/decisions.md`「task_03 完了判定前レビュー」。

## 対象範囲

1. **戻す時刻を早めない**（deep H1）: 予約中の再送では、戻す時刻 = max(前の戻す時刻, 今 + 200 ms + 40 ms × 今回の文字数)。タイマーにはその時刻までの残りを渡す（時計は単調時計・差し替え可能に）。
2. **時間制限つきでロックの外で呼ぶ**（deep M1 / Codex High）: `user32.SendMessageTimeoutW`（`SMTO_ABORTIFHUNG`〔0x0002〕・200 ms）で問い合わせ・切替を行い、戻り値 0（失敗・時間切れ）は失敗として扱う。
   共有状態（IME 窓 → 予約）の確認・更新だけをロックの中で行い、Win32 呼び出しはロックの外。外部呼び出しの後に世代を再検証して、間に別の送信・戻す処理が入ったら結果を捨てる（二重に戻す・戻し漏れ・オンのまま送るを起こさない）。
   64 bit の型宣言（`SendMessageTimeoutW` の `lpdwResult` は `PDWORD_PTR`）に注意。
3. **ユーザーの操作を上書きしない範囲を広げる**（Codex High の一部）:
   - 戻すとき: 状態を問い合わせ、**オフのときだけ**オンにする（オンなら触らない）。問い合わせが失敗したら戻さない（ログ）。
   - 予約中の再送: 状態を問い合わせ直し、オンなら再びオフにしてから送る（予約は引き継ぐ）。問い合わせが失敗したら IME に触らず送る（予約は残し、戻す時刻は 1 の規則で延ばす）。
4. **終了時にすべて戻す**（deep M2 / Codex Medium）: `ImeController` に予約をすべてその場で戻す口（例 `restore_all_now()`。タイマーを取り消し、各 IME 窓を 3 の規則で戻す）と、モジュール関数 + `InputGateway` の公開メソッド（例 `restore_ime_now()`）を設ける。
   `keyseq/presentation/app.py` の `on_close` から、フック停止の後・`destroy()` の前に呼ぶ（例外は握りつぶさず記録し、終了は続ける）。終了後の新しい予約は作らない。
5. **細部**（deep L2）: Windows 以外で Win32 の API が無いときのログを警告（トレースバックなし）へ下げる。

## テスト（追加・修正まで。実行は依頼しない）

- 1: 長い → 短いの順の再送で戻す時刻が前の時刻のまま（短くならない）/ 短い → 長いで延びる。
- 2: 時間切れ（戻り値 0）は失敗扱いで、送信は続く / Win32 呼び出し中に別の送信・戻す処理が入った場合に結果を捨てる（呼び出しを差し替えて途中で状態を変える）。
- 3: 戻すときオンなら触らない / 予約中の再送で状態がオンなら再びオフにする / 問い合わせ失敗時の扱い。
- 4: `restore_all_now` がタイマーを取り消して全部戻す・以後は予約しない / `App.on_close` から呼ばれる（tests_ui の既存の終了テストがあればそれに沿う。無ければ application を介さない最小のテスト）。
- 既存テストは仕様変更に合わせて期待値を直す（戻すときの問い合わせが増える等）。

## 読むファイル

- 正本 §7.7 / `keyseq/infrastructure/ime_control.py` / `keyseq/infrastructure/input_gateway.py` / `keyseq/presentation/app.py`（`on_close`）
- `tests/test_ime_control.py` / `tests/test_input_gateway_send.py`

## 含まない

- 入力欄ごとの IME 状態の扱い（既知の制約）/ 手での「オン → オフ」の検出（既知の制約）/ 待ちの係数の変更 / 文書（メイン）
