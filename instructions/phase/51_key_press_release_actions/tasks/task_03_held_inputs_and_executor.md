# task_03_held_inputs_and_executor

## 目的

`key_hold` の送信と押下中の集合（暫定 35 §4・§8）を作る: InputGateway の送信の追加・変更 / 押下中の集合 `HeldInputs` / ActionExecutor の `key_hold` の実行と text / file_line の前後の離す・押し直す・失敗時の扱い。
**infrastructure + application 限定**。runner（`sequence_runner/`）から持ち主を渡す配線・自動で離す入口は task_04、presentation（`app.py` の配線・ダイアログ・表示）は task_05。JSON 不変。

## 対象範囲（infrastructure + application）

### `keyseq/infrastructure/input_gateway.py`
- **拡張キーの送信を keyboard の押下記録に載せない**（§2-15）: `_send_extended_event` の `keybd_event` の前後で、keyboard 自身の送信（`keyboard.send` / `press`）と同じく `keyboard._listener.is_replaying` を True にして戻す（try / finally。属性が無ければそのまま送る）。`press_key` / `release_key` / `send_hotkey` の拡張キーの経路すべてに効く
- `write_text`: `keyboard.write(text, restore_state_after=False)`（§2-16。送信後に keyboard が修飾キーを押し直さない。空文字の経路も同じ）
- 新規 `key_identity(key: str) -> tuple[int, bool]`: 実際に送る対象（スキャンコード, 拡張フラグ）を返す（§4.3 の同じキーの判定）。拡張キーの表にあれば (スキャンコード, True)、それ以外は `keyboard.key_to_scan_codes(key)[0]` か `resolve_known_scan_code_from_key_name` で (スキャンコード, False)。解決できなければ例外
- 新規 `mouse_down(button: str, x: int | None = None, y: int | None = None)` / `mouse_up(...)`: 座標があれば `pyautogui.moveTo(x, y)`（瞬時）してから `pyautogui.mouseDown` / `mouseUp`。**FAILSAFE を外して送る**（`drag_mouse` と同じく try / finally で戻す）

### 新規 `keyseq/application/held_inputs.py`（`HeldInputs`）
- 押下中の集合: 識別子（キーボード = `("key", スキャンコード, 拡張)`・マウス = `("mouse", ボタン)`）→ 記録（送るときのキー名またはボタン・持ち主のトリガーのキー・押した順）
- `press_key(owner, key)` / `press_mouse(owner, button, position)`: **送る前に記録し**（持ち主を上書き・順は最初の押下のまま）、送信（キーボードは send_guard の中で）。送信が例外なら**そのキーにも離すを送ってから**記録を外し、例外を上げ直す（§4.3）
- `release_key(key)` / `release_mouse(button, position)`: 集合に無くても送り、送ってから記録を外す
- `release_owner(owner) -> list[Exception]` / `release_all() -> list[Exception]`: 該当分をすべて離す（1 つの例外で止めず、例外を集めて返す）。キーボードは send_guard の中。マウスは座標なしで離す
- `suspend_keyboard()` / `resume_keyboard()`（または同等のコンテキスト）: 集合のキーボードのキーをすべて離す / 押し直す（集合は変えない。§4.4）
- 変化の通知口（コンストラクタ引数の任意の callback・押下中の表示用。中身は「押した順の表示名の列」）。表示は task_05
- send_guard は ActionExecutor のものを使えるよう、ガードに入る / 出る口をコンストラクタで受け取る（または ActionExecutor から渡す）。**UI スレッドからだけ呼ぶ前提**（ロックは不要だが、ActionExecutor の send_guard のロックは尊重する）

### `keyseq/application/action_executor.py`
- `execute(action, owner: str | None = None)`（owner は省略可・既存の呼び出しは変えない）。`key_hold`:
  - `domain.key_hold.parse_key_hold` が文字列（エラー）/ キーボードの行で `input_gateway.validate_key_name` が例外 → **先に `release_owner(owner)` してから** `_on_action_error` で知らせ、False（止まる系・§4.5）
  - 押す / 離すを `HeldInputs` で送る。送信の例外 → `release_owner(owner)` してから `_on_action_error`（または `_on_runtime_error`）で知らせ、False
  - owner が None（呼び出し元が持ち主を渡さない既存経路）のときは owner を `""` として記録してよい（task_04 で配線）
- text（`_write_text`）と file_line の送信（`poll_file_line` 内の `_write_text`）: 集合にキーボードのキーがあれば**送る前に一時的に離し、送れたら押し直す**（§4.4・§2-14）。
  送信が例外なら**押し直さず**、`release_owner(owner)` してから知らせ、実行を終えるエラー（text は False を返す・file_line は既存どおり False）にする（§2-17）。
  text の例外を捕まえるのは新しい挙動（今は捕まえずに上へ抜ける）。file_line の `poll_file_line` は既に捕まえて False を返している（知らせる前の解放を足す）。`poll_file_line` にも owner を渡せるようにする（省略可）
- `_invalid_type_message` の種類の列挙に `key_hold` を足す
- `HeldInputs` はコンストラクタで受け取る（省略時は ActionExecutor が自分の gateway で作る。既存のテストのコンストラクタ呼び出しを壊さない）

### テスト（偽の gateway で送信を記録・実際の入力は送らない）
- 新規 `tests/test_held_inputs.py`: 送る前の記録・失敗時の補償の離す・集合に無い離すの送信・同じ識別子（`ctrl` と `left ctrl`）と別の識別子（`left ctrl` と `right ctrl`）・release_owner / release_all が例外を集めて残りも離す・suspend / resume が集合を変えない・通知
- 新規 `tests/test_action_executor_key_hold.py`: key_hold の押す / 離す・各エラー（parse・validate_key_name・送信の例外）で先に離してから知らせ False・text の前後の離す / 押し直す・text の例外で押し直さず離して False・file_line の送信でも同じ
- `tests/test_input_gateway_send.py`（既存に追加）: 拡張キーの送信で `is_replaying` が立つ・`write_text` が `restore_state_after=False`・`key_identity`・`mouse_down` / `mouse_up` の FAILSAFE と座標
- 既存のテストで text の例外が上へ抜けることを前提にしたものがあれば、新しい挙動へ追随（理由をテスト名かコメントに残す）

## 読むファイル

- `instructions/history/35_key_press_release_actions.md` §4・§4.5・§8
- `keyseq/infrastructure/input_gateway.py`（全体）
- `keyseq/application/action_executor.py`（全体）
- `keyseq/domain/key_hold.py`（task_02）・`keyseq/domain/key_identifiers.py:19-31`
- `.venv/Lib/site-packages/keyboard/__init__.py:361-390, 783-871`（`send` の `is_replaying`・`write` の `restore_state_after`）
- `tests/test_input_gateway_send.py`・`tests/test_action_executor_type.py`・`tests/test_action_executor_file_line.py`（偽の gateway の作り方）

## 含まない

- runner から持ち主を渡す配線・自動で離す入口・末尾 / 連動 / 実行を終えるエラーの解放（task_04）
- `app.py` の配線・ダイアログ・一覧 / 省略表示・押下中の表示・フック停止 / 終了の解放（task_05）
- 正本の改訂（task_07）

## 確認

- 上記テストの追加・追随（実行は verifier: compileall・`unittest discover -s tests`・`tests_ui`・smoke）
- 既存の hotkey / text / mouse_click / file_line の挙動が、押下中のキーが無いとき変わらないこと（text の例外の扱いと `restore_state_after=False` だけが意図した変更）
- reviewer（5 観点）
