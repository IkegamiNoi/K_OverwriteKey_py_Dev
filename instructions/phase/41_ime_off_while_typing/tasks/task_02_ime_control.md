# task_02_ime_control

## 目的

正本 `instructions/common/spec_detail/key_input.md` §7.7「文字の入力（text・file_line の行）の間は、送り先の IME をオフにする」（phase 41）を実装する。**infrastructure のみ**。

## 対象範囲

- 新規 `keyseq/infrastructure/ime_control.py`（IME 制御。Win32 呼び出しはこのモジュールに閉じる）:
  - 送り先 = `GetForegroundWindow` → `GetWindowThreadProcessId` → `GetGUIThreadInfo` の `hwndFocus`（取れなければ前面の窓）→ `imm32.ImmGetDefaultIMEWnd`。
  - 状態の問い合わせ / 設定 = `user32.SendMessageW(ime_wnd, WM_IME_CONTROL=0x283, IMC_GETOPENSTATUS=5 / IMC_SETOPENSTATUS=6, value)`。
  - 送信の前: 状態がオンならオフにして「戻す予約」を持つ。オフなら何もしない。IME 窓が取れない・例外 → 何もしない（送信は続ける・通知しない）。
  - 送信の後: 戻す待ち = **200 ms + 40 ms × 文字数** の後に、別スレッドのタイマー（`threading.Timer`）でオンへ戻す。UI スレッドを塞がない。
  - 戻す前に**同じ IME 窓**へ次の送信が来たら: オフのまま送り（状態を問い合わせ直してオフと読んで「触らない」と誤判定しない）、戻すタイマーを取り消して新しい待ちで張り直す。別の IME 窓の予約はそれぞれ独立に戻す。
  - 共有状態（IME 窓 → 予約）は `threading.Lock` で守る。戻す処理の例外はタイマースレッドから外へ出さないが、握りつぶさず `logging` で記録する。
  - タイマーはデーモンにしない（アプリ終了時も戻してから終わる）。
  - Windows 以外・`ctypes.WinDLL` が無い環境では import が壊れず、何もしない。
  - 待ちの係数（200 / 40）はモジュール定数。タイマーと Win32 呼び出しはテストで差し替えられるようにする（`keyseq/application/file_line_loader.py` の差し替え可能な設計に倣う）。
- `keyseq/infrastructure/input_gateway.py` の `write_text`: IME 制御を挟んで `keyboard.write(text)` を呼ぶ（送信中に例外が出ても戻す予約を張る〔`finally`〕。例外はそのまま外へ出す＝従来どおり）。空文字では IME に触らない。
- テスト `tests/test_ime_control.py`（Win32・タイマーを差し替え）: オン → オフ → 送信 → 予約（待ち = 200 + 40 × 文字数）→ 戻す の順序 / オフなら触らない / IME 窓が取れない・例外なら送信だけする /
  予約中の同じ窓への 2 回目は問い合わせずに送り、予約を張り直す / 別の窓は独立 / 送信の例外でも予約される / 空文字は触らない。
  `write_text` のテストは既存の `tests/test_input_gateway_send.py` の書き方に合わせる。

## 読むファイル

- `instructions/common/spec_detail/key_input.md` §7.7 / `instructions/phase/41_ime_off_while_typing/phase.md`
- `keyseq/infrastructure/input_gateway.py`（`ctypes` の使い方・`write_text`）/ `keyseq/application/file_line_loader.py`（差し替え可能な設計の例）
- `tests/test_input_gateway_send.py`

## 含まない

- application・presentation の変更 / hotkey・キーマップの送信先キー・マウス / IME の入力モードの切替 / 正本・codebase_map の文書（メインが行う）
