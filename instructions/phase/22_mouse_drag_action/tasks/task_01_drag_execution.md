# task_01_drag_execution

## 目的

マウスのドラッグ（掴む点 → 離す点）を実際に送る経路を作る。根拠は暫定仕様
[19_mouse_drag_action.md](../../../history/19_mouse_drag_action.md) の **§3（データモデル）・§5（実行）**。

**application + infrastructure 限定**。**presentation / domain は変更しない**（UI と一覧表示は task_02）。
**JSON スキーマの追加キーを読む側だけ**を作る（書く側 = ダイアログは task_02）。
**`ctypes` を使わない**（`pyautogui` のみ。OS 分岐を増やさない = 暫定仕様 §2）。

## 対象範囲（application + infrastructure 限定）

### `keyseq/infrastructure/input_gateway.py`

`InputGateway` に次のメソッドを**追加**する（既存メソッドは変更しない）。

```python
def drag_mouse(self, x: int, y: int, to_x: int, to_y: int, button: str, duration_sec: float) -> None
```

振る舞い（暫定仕様 §5-4）:

1. `pyautogui.FAILSAFE` の現在値を退避し、`False` を代入する。
2. `pyautogui.moveTo(x, y)` で掴む点へ移動する。
3. 次を `try` / `finally` で囲む:
   - `try`: `pyautogui.mouseDown(button=button)` → `pyautogui.moveTo(to_x, to_y, duration=duration_sec)`
   - `finally`: `pyautogui.mouseUp(button=button)`
4. **外側の `finally` で `pyautogui.FAILSAFE` を退避した値へ必ず戻す**（例外時も）。

- `dragTo` は**使わない**（例外時に解放されないため。暫定仕様 §1「`dragTo` の中身」）。
- **`mouseDown` が失敗した場合も `mouseUp` を通す**形にする（未押下での解放は無害。押下直後に失敗した場合の押しっぱなしを防ぐ）。
- 例外は握りつぶさず**そのまま送出**する（呼び出し元の `action_executor` が報告する）。

### `keyseq/application/action_executor.py`

モジュール定数を追加する:

```python
DEFAULT_DRAG_SPEED_PX_PER_SEC = 1000
MIN_DRAG_DURATION_SEC = 0.15
MAX_DRAG_DURATION_SEC = 5.0
```

`_execute_mouse_click`（`:105-127`）を次のように拡張する。**既存の分岐・メッセージ・正規化は変えない**。

1. 既存どおり `x` / `y` を `int()` で取得（失敗時は既存のエラーメッセージのまま `return`）。
2. 既存どおり `button` / `clicks` を正規化する。
3. `drag = bool(action.get("drag"))` を求める。
   - **false なら従来どおり** `self.input_gateway.click_mouse(...)`（この経路は一切変更しない）。
4. true のとき:
   - `to_x` / `to_y` を **`int()` で取得**。失敗 / 欠落なら
     `self._on_runtime_error("送信エラー", "mouse_click の to_x/to_y が不正です（ドラッグの離す位置を整数で指定してください）。")`
     を呼んで **`return`**（**`click_mouse` へフォールバックしない** = 暫定仕様 §3-4）。
   - 速度を求める: `action.get("drag_speed", DEFAULT_DRAG_SPEED_PX_PER_SEC)` を `float()` で変換し、
     **変換不能 / 0 以下なら `DEFAULT_DRAG_SPEED_PX_PER_SEC`**（暫定仕様 §3-5）。
   - 距離 = `math.hypot(to_x - x, to_y - y)`、`duration_sec = 距離 / 速度`。
   - **クランプ**: `duration_sec = min(max(duration_sec, MIN_DRAG_DURATION_SEC), MAX_DRAG_DURATION_SEC)`（暫定仕様 §5-3）。
   - `self.input_gateway.drag_mouse(x=x, y=y, to_x=to_x, to_y=to_y, button=button, duration_sec=duration_sec)` を呼ぶ。
   - 例外時は既存と同じ形で
     `self._on_runtime_error("送信エラー", f"mouse_click の実行に失敗しました。\n{type(e).__name__}: {e}")`。
   - **`clicks` はドラッグでは使わない**（1 回の押下 → 移動 → 解放。暫定仕様 §3-6）。
- **send guard には入れない**（既存の `mouse_click` と同じ。暫定仕様 §2）。

### `tests/test_input_gateway_drag.py`（新規）

`unittest` + `unittest.mock`。`keyseq.infrastructure.input_gateway` の `pyautogui` を `patch.object` で差し替える
（既存 `tests/test_input_gateway_send.py` の `setUp` が手本。**`attach_mock` で呼び出し順を 1 本の `mock_calls` にまとめる**）。

1. **呼び出し順と引数**: `drag_mouse(100, 200, 400, 500, "left", 0.3)` で
   `moveTo(100, 200)` → `mouseDown(button="left")` → `moveTo(400, 500, duration=0.3)` → `mouseUp(button="left")` の順（`mock_calls` の完全一致）。
2. **FAILSAFE の無効化と復元**: 呼び出し中に `pyautogui.FAILSAFE` が `False` であることを確認し（例: `moveTo` の `side_effect` で観測）、
   **戻り値が元の値（True）に復元**されていること。
3. **例外時も解放と復元**: 移動（2 つ目の `moveTo`）が例外を投げても **`mouseUp` が呼ばれ**、例外はそのまま送出され、`FAILSAFE` が復元されること。
4. **`mouseDown` が失敗しても `mouseUp` を通る**こと。
5. **`dragTo` を呼ばない**こと。

### `tests/test_action_executor_drag.py`（新規）

`ActionExecutor` をテストダブル（`Mock()` の gateway と各コールバック）で組み立てて検証する。

1. **drag なし**は従来どおり `click_mouse` が呼ばれ、`drag_mouse` は呼ばれない。
2. **drag あり**で `drag_mouse` が期待の引数で呼ばれる（`click_mouse` は呼ばれない）。
3. **所要時間**: 距離 ÷ 速度になる（例: (0,0)→(300,400) = 距離 500 / 速度 1000 → 0.5 秒）。
4. **クランプの境界**: 下限（例: 距離 50 / 速度 1000 = 0.05 → **0.15**）・上限（例: 距離 10000 / 速度 1000 = 10.0 → **5.0**）・
   クランプされない値（0.5）の 3 通り。
5. **速度の不正値**（欠落 / 空文字 / `"abc"` / `0` / 負数）で **1000 として扱われる**こと（暫定仕様 §8-5）。
6. **`to_x` / `to_y` の欠落・変換不能**で `on_runtime_error` が呼ばれ、**`drag_mouse` も `click_mouse` も呼ばれない**こと（暫定仕様 §8-4）。
7. **掴む点 = 離す点**でも例外にならず `drag_mouse` が呼ばれること（距離 0 → 下限 0.15 秒。暫定仕様 §8-8）。
8. **`clicks` が 3 でもドラッグは 1 回**（`drag_mouse` の呼び出しが 1 回・`clicks` を渡していない）。
9. **`drag_mouse` が例外を投げたとき** `on_runtime_error` が呼ばれること。

### 設計メモ / 制約

- **既存の `click_mouse` 経路の挙動・メッセージを変えない**（暫定仕様 §8-1）。`FAILSAFE` も触らない。
- `math` の import を `action_executor.py` へ追加してよい（新規依存は追加しない）。
- 型注釈を付ける（`.claude/rules/python_rules.md`）。関数は 30 行以内を目安に。
- **python を実行しないこと**（この環境では起動できない）。テストの実行は `verifier` が行う。
- **`git checkout --` / `git restore` / `git stash` を使わない**。

## 読むファイル

1. `instructions/history/19_mouse_drag_action.md` の **§2 / §3 / §5 / §8**（根拠。全文は読まなくてよい）
2. `keyseq/infrastructure/input_gateway.py`（全体・編集対象。既存の `click_mouse` と phase 21 の送信部分が手本）
3. `keyseq/application/action_executor.py:100-130`（編集対象の `_execute_mouse_click`）+ `:15-40`（`__init__` の依存）
4. `tests/test_input_gateway_send.py:1-60`（テストの書き方の手本。`setUp` の `attach_mock` 形）

## 含まない

- **UI（`ActionDialog`）の変更**（チェックボックス / 離す点の欄 / 速度欄 / 回数欄の無効化 / 座標取得の排他）= **task_02**
- **一覧表示の整形**（`domain/config.py` の `format_action_list_item`）= **task_02**
- **drag OFF で新キーを出力しない**規定（書く側の話）= **task_02**
- 正本 `spec_detail/` / `codebase_map.md` の更新 = **task_03**（フェーズ末に昇格）
- 実機目視 = **task_03**
- 別スレッド化・ホイール・押す/離すアクション・macOS 対応 = フェーズのスコープ外

## 確認

実行は `verifier`。python は `..\..\..\.venv\Scripts\python.exe`。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests.test_input_gateway_drag -v` が全 pass。
3. `-m unittest tests.test_action_executor_drag -v` が全 pass。
4. `-m unittest discover -s tests` が全 pass（**phase 21 完了時点の 461 から減っていない**こと）。
5. `-m tests.smoke_app` が SMOKE OK。
6. **変異検査**（ファイルのコピーで退避 → 編集 → コピーで復元）:
   - `drag_mouse` の `finally` の `FAILSAFE` 復元を消すと、復元を見るテストが失敗する。
   - クランプの下限 `0.15` を `0` にすると、下限の境界テストが失敗する。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は **task_03** でまとめて実施する（本タスクでは行わない）。
