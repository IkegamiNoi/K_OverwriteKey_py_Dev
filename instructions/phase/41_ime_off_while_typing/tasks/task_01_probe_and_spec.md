# task_01_probe_and_spec

## 目的

送り先の IME を「オフ → 文字を送る → 元へ戻す」方式が実機で効くか、**戻すタイミング**をどうすればよいかを probe で実測し、その結果で正本 `key_input.md` §7.7 の文言を決める（ユーザー承認）。

## 対象範囲

- probe スクリプト（scratchpad・リポジトリに入れない）: `.venv` python + `ctypes`（`imm32.ImmGetDefaultIMEWnd` / `user32.SendMessageW` の `WM_IME_CONTROL`〔0x283〕・`IMC_GETOPENSTATUS`〔5〕/ `IMC_SETOPENSTATUS`〔6〕）と、本番と同じ `keyboard.write`。
  変種: 制御なし / オフ → 送信 → すぐ戻す / 戻す前に 30・100・300 ms 待つ。各変種の後に IME の状態を読み戻して表示する。
- ユーザーが IME オンのメモ帳で実行し、変種ごとの入り方（カタカナで確定 / ひらがなの変換待ち）と IME が元へ戻ったかを報告する。
- 結果から決める: 戻すまでの待ち（UI スレッドを塞ぐ時間）/ IME の窓が取れない・失敗時の扱い（推奨: そのまま送る・通知しない）/ §7.7 の文言（同節末尾の「text は対象外」との書き分け・file_line にも及ぶ旨）。
- 正本 `key_input.md` §7.7 の改訂（ユーザー承認後）。

## 含まない

- 本番コードの変更（task_02）
