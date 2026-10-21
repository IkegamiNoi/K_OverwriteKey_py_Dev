# task_01_scroll_core

## 目的

暫定 50 v0.4 §3・§4・§6 の `mouse_scroll` の検証・実行・送信・一覧の書式を作る。
**domain（新規 `mouse_scroll.py` + `config.py` の書式の分岐）・application（`action_executor.py`）・infrastructure（`input_gateway.py`）。presentation は不変（ダイアログ・「次に実行」の要約は task_02）。スキーマ = 種類の追加のみ。**

## 対象範囲（domain / application / infrastructure）

### 新規 `keyseq/domain/mouse_scroll.py`（`key_hold.py` と同じ形・UI / infrastructure を import しない）

- 定数: `ACTION_TYPE_MOUSE_SCROLL = "mouse_scroll"` / `DIRECTIONS = ("up", "down", "left", "right")` / `UNIT_NOTCH = "notch"` / `UNIT_DELTA = "delta"` / `WHEEL_DELTA = 120` / `MAX_NOTCHES = 100` / `MAX_DELTA = 12000` / `DEFAULT_NOTCHES = 1`（task_02 が使う）
- `@dataclass(frozen=True) MouseScrollSpec`: `direction: str` / `unit: str` / `amount: int` / `position: tuple[int, int] | None`
- `parse_mouse_scroll(action) -> MouseScrollSpec | str`（文字列 = 理由・日本語）:
  - `direction`: 非文字列 → エラー / trim + 小文字が `DIRECTIONS` 以外 → エラー
  - `unit`: **キー無し、または文字列で trim 後が空 → notch** / キーがあって非文字列（`None` を含む）→ エラー / trim + 小文字が notch / delta 以外 → エラー
  - `amount`: bool → エラー / int → そのまま / float → `is_integer()` なら int・でなければエラー / str → `int(s.strip())`（失敗はエラー）/ それ以外（キー無し・None 含む）→ エラー。範囲 notch 1〜100・delta 1〜12000（外はエラー・理由に範囲を書く）
  - `x` / `y`: `key_hold.parse_key_hold` の座標と同じ（キーの有無で判定・片方だけはエラー・`int()` で変換できなければエラー。`key_hold.py:63-72`）
- `scroll_deltas(spec) -> tuple[bool, tuple[int, ...]]`: 1 つ目 = 縦なら True（up / down）。2 つ目 = 1 事象ごとの符号つきの量。notch → `±120` を amount 個 / delta → 120 ずつ + 端数を最後（300 → 120, 120, 60）。符号: up・right = 正 / down・left = 負
- `format_mouse_scroll_value(action) -> str`（暫定 50 §6）: 有効 → `[スクロール] 下 3` / delta は `[スクロール] 右 60 (生)` / 座標があれば末尾に ` (100, 200)`。向きの表示名 = 上 / 下 / 左 / 右。不正 → `direction` が文字列なら `[mouse_scroll] <direction の元の値>`・そうでなければ `[mouse_scroll]`
- `describe_mouse_scroll(action) -> str`: 通知用の `direction=… unit=… amount=…`（キーが無ければ `(なし)`・元の値の `repr` でなく `str`）+ 座標のキーがあれば ` x=… y=…`

### `keyseq/domain/config.py`（`format_action_list_item`）

- key_hold と同じく `[type]` の接頭辞を付けない分岐に `mouse_scroll` を加える（値 = `format_mouse_scroll_value`・ラベルは `: ラベル`）

### `keyseq/application/action_executor.py`

- `execute()` に `mouse_scroll` の分岐（mouse_click の前後どちらでもよい）→ `_execute_mouse_scroll(action, owner)`（戻り値 bool）:
  - `parse_mouse_scroll` が文字列 → `_report_held_error(action, owner, f"mouse_scroll の指定が不正です: {理由}（{describe}{ラベル}）")` → False。ラベルは空でなければ ` ラベル: …`
  - 成功 → `vertical, deltas = scroll_deltas(spec)` → `self.input_gateway.scroll_mouse(vertical=..., deltas=..., position=spec.position)` → True
  - 例外 → `_report_held_error(action, owner, f"mouse_scroll の送信に失敗しました: {exc}（{describe}{ラベル}）")` → False
  - send guard は使わない（マウス・暫定 50 §4-4）
- `_invalid_type_message` の文言を「種類が不正です（hotkey / text / mouse_click / mouse_scroll / system / file_line / key_hold のいずれか）。」へ

### `keyseq/infrastructure/input_gateway.py`

- 定数 `_INPUT_MOUSE = 0` / `_MOUSEEVENTF_WHEEL = 0x0800` / `_MOUSEEVENTF_HWHEEL = 0x1000` を足す
- `InputGateway.scroll_mouse(self, *, vertical: bool, deltas: Sequence[int], position: tuple[int, int] | None) -> None`:
  - `position` があれば `self.move_cursor(x, y)`（既存・FailSafe を外し待ちなし）
  - `deltas` が空なら何もしない。各値で `_INPUT(type=_INPUT_MOUSE, mi=_MOUSEINPUT(dx=0, dy=0, mouseData=<delta & 0xFFFFFFFF>, dwFlags=WHEEL or HWHEEL, time=0, dwExtraInfo=0))` を作り、**配列 1 つにして `_send_input_api()(n, array, sizeof(_INPUT))` を 1 回**。戻り値 != n なら `OSError(ctypes.get_last_error(), "SendInput failed")`
  - 事象の配列を作る部分は小さな関数に分けてテストできるようにする（例 `_build_wheel_inputs(vertical, deltas)`）

### テスト（tests）

- 新規 `tests/test_mouse_scroll.py`: parse（4 方向・大文字 / 空白・不正な向き / 非文字列・unit のキー無し / 空 / `"Delta"` / 不正な文字列 / 非文字列 / None・amount の int / `3.0` / `"3"` / `2.7` / bool / None / キー無し / 0 / 101 / delta の 12000 と 12001・座標の両方 / 片方 / 変換不能 / null）・`scroll_deltas`（notch 3・delta 300 → 120,120,60・delta 120・4 方向の符号と縦横）・`format_mouse_scroll_value`（§6 の各例・不正の 2 形）・`describe_mouse_scroll`
- `tests/test_action_executor_*.py`（新規 `test_action_executor_mouse_scroll.py` でよい・既存の偽の gateway の手本は `test_action_executor_key_hold.py`）: 成功で True・gateway へ渡す値 / 不正で False・gateway を呼ばない・通知の内容（理由・describe・ラベル）・持ち主の押下中を離す / gateway の例外で False / 未知の種類の文言
- `tests/test_input_gateway_*.py`（新規 `test_input_gateway_scroll.py` でよい）: `_build_wheel_inputs` のフラグ・`mouseData`（-120 → `0xFFFFFF88`）・個数 / `scroll_mouse` が `move_cursor` を座標のあるときだけ呼ぶ・`SendInput` を 1 回だけ呼ぶ・戻り値不足で OSError（`_send_input_api` を差し替え・本物の SendInput を呼ばない）
- `test_domain_config.py` 等: `format_action_list_item` の mouse_scroll（ラベルあり / なし）

## 読むファイル

1. `instructions/history/50_mouse_scroll_action.md`（§3・§4・§6）
2. `keyseq/domain/key_hold.py`（全体・手本）
3. `keyseq/domain/config.py:425-480`
4. `keyseq/application/action_executor.py:1-40`（import）・`:110-210`・`:255-295`
5. `keyseq/infrastructure/input_gateway.py:1-200`・`:230-260`
6. `tests/test_action_executor_key_hold.py`・`tests/test_input_gateway_send.py`（偽の値の手本・必要な範囲）

## 含まない

- ダイアログの欄・OK の検査・「次に実行」の要約（`action_list_rendering.py`）（task_02）
- 正本・codebase_map の更新（task_03）
- runner（sequence_runner 系）の変更（戻り値で足りる・暫定 50 §4-5）

## 確認

- `compileall` clean / `unittest discover -s tests` 全 pass（新規分を含む）/ `unittest discover -s tests_ui` 全 pass / `-m tests.smoke_app` pass
- 差分の直読み: domain が UI・infrastructure を import しない / presentation・runner の変更なし / 本物の `SendInput` をテストで呼ばない

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_03 でまとめて実施
