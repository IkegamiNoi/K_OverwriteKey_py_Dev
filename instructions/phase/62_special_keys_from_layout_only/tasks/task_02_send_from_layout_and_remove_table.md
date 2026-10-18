# task_02_send_from_layout_and_remove_table

## 目的

送る側（送信・検査・同じキーの判定）の名前 → 走査コードを、次の順に一本化する（暫定 45 §4）。

テンキー → 拡張キー → keyboard → 選んでいるレイアウトの `id` → `scan_code`

レイアウトで決まったキーは `SendInput` の走査コード入力で実際に送る（今は `muhenkan` 等が検査を通るのに送れない）。
あわせて既知の特殊キーの表を削除する（§5）。

- 影響レイヤ:
  - domain（`key_identifiers.py` の削除）
  - presentation（`keyboard_layouts.py` の純関数・`LayoutController` のメソッド・`app.py` の注入）
  - infrastructure（`input_gateway.py`）
- application は不変。JSON スキーマ不変

## 対象範囲（domain・presentation・infrastructure）

### `keyseq/presentation/keyboard_layouts.py`

- 純関数 `resolve_layout_scan_code_from_key_name(layout: KeyboardLayout | None, key_name: str) -> int | None` を追加する（§4.1-4）
  - `layout.keys` を順に見て、次をすべて満たす最初の行の `scan_code` を返す
    - `scan_code` が `None` でない
    - `normalize_key_name(key_spec.id)` が `normalize_key_name(key_name)` と一致する（どちらも空でない）
  - 値が 1〜255 の範囲外なら、その行は当たらない扱いにして次の行へ進まず `None` を返す（「最初の行」で判定を終える）
  - `layout` が `None`・キー名が空・当たらないときは `None`

### `keyseq/presentation/controllers/layout_controller.py`

- `resolve_scan_code_from_key_name(self, key_name: str) -> int | None` を追加する（§4.4）
  - `self._keyboard_layout_entries.get(str(self.keyboard_layout_id).strip())` の `entry.layout`（**登録済みの値**）を上の純関数に渡す
  - entry が無ければ `None`
  - **`get_current_keyboard_layout` は呼ばない**（ファイルの読み直しも Tk の操作もしない。UI スレッドの外から呼ばれるため）

### `keyseq/presentation/app.py`

- :133 の `InputGateway()` を `InputGateway(resolve_layout_scan_code=lambda name: self.layout.resolve_scan_code_from_key_name(name))` にする
  - `self.layout` は :239 で作られるので、遅延評価の lambda で渡す

### `keyseq/infrastructure/input_gateway.py`

- `InputGateway.__init__(self, *, resolve_layout_scan_code: Callable[[str], int | None] | None = None)` を追加する（既存の引数なしの生成はそのまま通る）
- 内部の解決関数を 1 つ追加し、§4.1 の順に種類と値を返す
  1. テンキー: `numpad_key_spec`
  2. 拡張キー: `_resolve_extended_key`
  3. keyboard: `keyboard.key_to_scan_codes(key)` が**成功し、結果が空でない**
  4. レイアウト: `resolve_layout_scan_code` が整数を返す
     - 関数が `None`・例外・`None` を返したときは当たらない
     - 戻り値が `int` 以外・1〜255 の範囲外のときも当たらない（gateway 側でも確かめる）
  5. どれにも当たらなければ `ValueError(f"Unknown key name: {key!r}")`

  名前・戻り値の形は任意（例: `("numpad", scan, extended)` / `("extended", vk, scan)` / `("keyboard", scan_codes)` / `("layout", scan)`）
- `press_key` / `release_key`
  - 4 の場合は `_send_numpad_event(scan, False, key_up=...)` で送る（同じ `SendInput` の走査コード入力の経路。必要なら関数名を `_send_scan_code_event` に改め、呼び出し元をすべて直してよい）
  - 1・2・3 の場合は今と同じ（3 は `keyboard.press` / `keyboard.release`）
- `send_hotkey`
  - **全キーが 3 のときだけ** `keyboard.send(hotkey)` にまとめて渡す
  - 1・2・4 を 1 つでも含むときは、今の拡張キー・テンキーと同じく記述順に `press_key`、逆順に `release_key`
  - 失敗時の扱い（押せたものだけ離す・最初の例外を投げる）は今と同じ
- `key_identity`
  - 1 = テンキーの値
  - 2 = `(scan, True)`
  - 3 = 今の `scan_codes[0]` の扱い（`0xE0xx` → `(xx, True)`、それ以外 → `(scan, False)`）
  - 4 = `(scan, False)`
  - 5 = `ValueError`
- `validate_key_name`
  - `is_numpad_key_name` は通す。`is_reserved_numpad_name` のエラーは今と同じ（この 2 つが先）
  - その後に上の解決関数を呼び、5 なら例外をそのまま上げる
- `resolve_known_scan_code_from_key_name` の import とすべての参照を削除する

### `keyseq/domain/key_identifiers.py`

- 次を削除する: `_SPECIAL_KEY_NAME_TO_SCAN_CODE`・`_SPECIAL_SCAN_CODE_TO_KEY_NAME`・`SPECIAL_KEY_NAMES`・`resolve_known_scan_code_from_key_name`・`resolve_known_key_name_from_scan_code`・`is_special_key_name`
- 残す: `PROHIBITED_ASSIGN_KEY_NAMES`・`is_prohibited_assign_key`（`normalize_key_name` の import も残す）

### テスト

- `tests/test_key_identifiers.py`: 削除した関数だけを試しているので、ファイルごと削除する
- `tests/test_input_gateway_send.py`
  - `test_key_identity_falls_back_to_known_scan_code` / `test_key_identity_falls_back_after_resolution_exception`（:389-398 付近）は、`InputGateway(resolve_layout_scan_code=...)` でレイアウトの解決を差し替える形に書き換える
  - 次のテストを追加する
    - `muhenkan` → 123 を返す関数を渡したとき
      - `key_identity("muhenkan") == (123, False)`
      - `validate_key_name("muhenkan")` が通る
      - `press_key` / `release_key` が `SendInput` の走査コード入力（`_send_input_api` を差し替えて `wScan=123`・`KEYEVENTF_SCANCODE`・拡張なし・離しで `KEYUP`）で送る
      - `send_hotkey("ctrl+muhenkan")` が ctrl → muhenkan の順に押し、逆順に離す（`keyboard.send` を呼ばない）
    - 関数を渡さないとき・関数が例外を投げるとき・`None` を返すとき: `muhenkan` の `key_identity` / `validate_key_name` / `press_key` が `ValueError`
    - 関数が 0 / 256 / `"123"` を返すとき: 当たらない（`ValueError`）
    - keyboard が知る名前（`a`）は関数を呼ばずに今どおり（`keyboard.press` / `keyboard.send` で送る）
    - 全キーが keyboard の名前の `send_hotkey("ctrl+a")` は `keyboard.send` にまとめて渡す
- `tests/test_keyboard_layout_files.py`（または新規の `tests/test_layout_scan_code_from_key_name.py`）: 純関数のテスト
  - jis.json で `muhenkan` → 123・`MUHENKAN` → 123・`zenkaku_hankaku` → 41
  - US TKL で `muhenkan` → `None`
  - `layout=None` → `None`・空のキー名 → `None`
  - `scan_code` なしの行（jis.json の `a` 相当の行）→ `None`
  - 同じ `id` が 2 行あれば最初の行の値
  - 0 / 256 → `None`
- `tests/test_layout_controller_scan_code.py`: `resolve_scan_code_from_key_name` のテストを追加する
  - 登録済みの `entry.layout` を使う（jis.json の entry で `muhenkan` → 123）
  - `get_current_keyboard_layout` を呼ばない（差し替えて呼ばれないことを確かめる）
  - entry が無い id なら `None`

### 設計メモ / 制約

- 依存の向き: `input_gateway.py` は presentation を import しない（関数を受け取るだけ）
- 3 を 4 より先にする（keyboard が知る名前は keyboard の走査コードが正）
- `held_inputs` / `action_executor` は gateway の公開メソッドを呼ぶだけなので変更しない
- §7.7 / §7.8 の既存の挙動（拡張キー・テンキー・keyboard の押下記録に載せない・send_guard）を変えない

## 読むファイル

1. `instructions/history/45_special_keys_from_layout_only.md` §4・§5
2. `keyseq/infrastructure/input_gateway.py`（編集対象。全体）
3. `keyseq/domain/key_identifiers.py`（編集対象）
4. `keyseq/presentation/keyboard_layouts.py:1-30` / :320-345
5. `keyseq/presentation/controllers/layout_controller.py:170-200` / :355-360
6. `keyseq/presentation/app.py:125-140`
7. `tests/test_input_gateway_send.py`（:1-20・:240-265・:360-405）
8. `tests/test_layout_controller_scan_code.py`（task_01 で作った手本）

## 含まない

- レイアウトが変わる前の離し（task_03）
- 正本反映（task_04）
- 受け取る側の外部レイアウトの読み直しの挙動（idea_51）
- `should_debug_special_key_event` の未使用の引数 `resolved_key` の整理（変えない）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加・変更したテストのモジュールが全 pass
- 次の grep が 0 件
  - `grep -rn "resolve_known_\|SPECIAL_KEY_NAMES\|is_special_key_name\|_SPECIAL_KEY_NAME_TO_SCAN_CODE" keyseq tests tests_ui`
  - `grep -n "keyseq.presentation" keyseq/infrastructure/input_gateway.py`
- 既存テストが全 pass: `unittest discover -s tests` / `unittest discover -s tests_ui` / `-m tests.smoke_app`

## 完了条件

- 上記の確認が pass し、**reviewer が採用**していること。
- 実機目視は task_03 でまとめて行う。
