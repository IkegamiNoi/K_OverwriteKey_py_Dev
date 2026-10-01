# phase.md

## フェーズ名

文字の送信中は送り先の IME をオフにする（ime_off_while_typing）

## フェーズの目的

text / file_line の文字を送る間だけ送り先の窓の IME をオフにし、送り終えたら元の状態へ戻す。IME がオン（ひらがな入力）でもカタカナ・英数字がそのまま入るようにする。
**対象は infrastructure の送信部分のみ（`input_gateway.write_text`。text・file_line 共通）。JSON スキーマ変更なし・追加ライブラリなし。**

- 起票元: ユーザー要望（2026-10-01）。実機で確認済み: file_line のカタカナが IME オンでひらがなの変換待ちになる / IME オフならカタカナで正しく出る / text 種別も同様。
- 原因: `keyboard.write` は Windows では 1 文字ずつ Unicode 文字として送る（SendInput の `KEYEVENTF_UNICODE` = VK_PACKET。`.venv` の `keyboard/__init__.py` `write` → `_winkeyboard.type_unicode`）。
  送り先の IME がオンだと、IME がこれを変換前の入力として受け取る。
- 主入力（暫定仕様）: なし（直接改訂モード）。正本 `key_input.md` §7.7 に 1 項目を足し、同節末尾の「テキスト入力（text）・マウス操作は対象外」（拡張キーの規定の範囲）と衝突しないよう書き分ける。
  text と file_line は同じ `write_text` を通る（`action_executor.py:105,166` → `:221-224`・`data_schema.md` §5.11.7「送信は text と同じ経路」は変更不要）ので、§7.7 には file_line にも及ぶ旨を明記する。
- モード: **直接改訂モード**（単一ファイル・少数条項）。番号対応: phase 41 / 暫定なし / decisions 41。

## 確定（ユーザー 2026-10-01）

- 文字を送る間だけ送り先（前面の窓）の IME をオフにし、送り終えたら**元の状態へ戻す**（オフだったなら何もしない）。
- 方式: Windows の IMM（`ImmGetDefaultIMEWnd` + `WM_IME_CONTROL` / `IMC_GETOPENSTATUS`・`IMC_SETOPENSTATUS`）。追加ライブラリなし。
- 不採用: クリップボード経由の貼り付け（ユーザーのクリップボードを書き換える）/ `WM_CHAR` の直送（受け取れないアプリがある）。

## 未確定 → task_01 で決定済（2026-10-01・正本 `key_input.md` §7.7 / decisions「task_01 probe」）

- **戻すタイミング**: SendInput の入力は送り先の入力キューに積まれて後から処理され、IME の切替（SendMessage）はそれより先に処理されるため、
  送った直後に戻すと文字の処理前に IME がオンへ戻るおそれがある。待ち方（固定の待ち / 送り先の処理完了の確認 等）と UI スレッドを塞ぐ時間を実測で決める。
- IME の窓が取れない・API が失敗したときの扱い（推奨: そのまま送る・通知しない）。送信中の変換途中の文字列（あれば）の扱い。

## スコープ

### 含む

- `infrastructure/input_gateway.py` の `write_text` の IME 制御（IME 制御そのものは infrastructure の小さなモジュールへ分けてよい）
- 正本 `key_input.md` §7.7 の改訂・`codebase_map.md` のキーの送信の節
- テスト（Win32 呼び出しを差し替えて、オン → オフ → 送信 → 戻す の順序・オフのときは触らない・失敗時のフォールバック・例外時も戻す）

### 含まない（後送り）

- hotkey・キーマップの送信先キー・マウス操作（文字の Unicode 送信ではないため対象外）
- IME の入力モード（ひらがな / カタカナ / 英数）の切替・Windows 以外

## このフェーズで読むファイル

1. `instructions/common/spec_detail/key_input.md` §7.7
2. `instructions/common/codebase_map.md`「キーの送信（infrastructure/input_gateway.py の InputGateway・phase 21）」節
3. `keyseq/infrastructure/input_gateway.py`（`write_text`・拡張キーの `ctypes` 呼び出しの書き方）
4. `keyseq/application/action_executor.py` `_write_text`（呼び出し元・send guard）
5. テスト: `tests/test_action_executor_type.py`・`tests/test_action_executor_file_line.py`（`write_text` を mock している側）/ input_gateway のテスト（あれば）

## タスク

タスク定義（`tasks/task_NN_<topic>.md`）は着手時に `/task_new` で順に起票する。

- task_01（**完了** 2026-10-01。フォーカスの窓へ問い合わせ・戻す待ち 200 ms + 40 ms × 文字数・正本 §7.7 改訂済）: probe（`.venv` python の小スクリプトで、IME オンのメモ帳等へ「オフ → 送信 → 戻す」を実測し、戻すタイミングと失敗時の扱いを決める。ユーザーの実機確認を含む）→ 正本 `key_input.md` §7.7 の改訂（ユーザー承認）
- task_02: 実装（`write_text` の IME 制御・テスト）・実機目視（IME オンで text / file_line のカタカナ・英数字が変換待ちにならず入る / 送信後に IME が元の状態に戻る）
- task_03: 正本反映の確認・`codebase_map.md`・`decisions_archive/41_ime_off_while_typing.md`・current.md の完了記載・`/refactor_check`

## レビュー方針

- 例外時も IME を必ず戻すか（`finally`）/ オフだった窓に触らないか / 失敗時に送信自体を止めないか。
- infrastructure に閉じているか（application・presentation に Win32 の都合を漏らさない）。Windows 以外・`ctypes` が使えない環境で import が壊れないか。
- Win32 の挙動は推測せず probe で実測する（handoff の教訓）。テストは呼び出しの順序を固定し、検出力を変異検査で確かめる。
