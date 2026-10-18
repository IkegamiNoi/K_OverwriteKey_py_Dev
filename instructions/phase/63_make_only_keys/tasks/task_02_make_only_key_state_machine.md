# task_02_make_only_key_state_machine

## 目的

押下だけが届くキー（走査コード 241 / 242）を「押した / リピート / 離した」に組み直す状態機械を作る（暫定 46 §3）。
**domain（走査コードの表）と application（状態機械）だけ**。

- presentation への組み込み（`hook_controller`・`app.py`・タイマーのワーカーの実体）は task_03
- application は keyboard・tkinter・pyautogui を import しない。時刻・タイマー・ルーティングは外から受け取る

## 対象範囲（domain・application 限定・新規のみ）

### `keyseq/domain/make_only_keys.py`（新規）

- `MAKE_ONLY_SCAN_CODES: frozenset[int] = frozenset({241, 242})`
- `is_make_only_scan_code(scan_code: object) -> bool`（整数にできなければ偽）

### `keyseq/application/make_only_keys.py`（新規）

**作るイベント**

```python
@dataclass(frozen=True)
class SyntheticKeyEvent:
    event_type: str      # "down" / "up"
    scan_code: int
    name: str | None     # 元のイベントの name を写す
    is_keypad: bool = False
```

**結果**

```python
@dataclass(frozen=True)
class MakeOnlyResult:
    accept: bool                      # フックへの戻り値
    routes: tuple[InputRoute, ...]    # 呼び出し側が実行する（actions を after(0) で予約）
    generation: int                   # 予約に付ける世代
```

**`class MakeOnlyKeyFilter`**

コンストラクタ（キーワード引数）:
- `route: Callable[[object], InputRoute]`（= `input_router.handle`）
- `release_state: Callable[[object], None]`（= `KeyStateManager.handle_event`。「離した」で `up` を渡す）
- `clock: Callable[[], float]`（単調・秒）
- `schedule: Callable[[float, Callable[[], None]], None]`（秒後に呼ぶ）
- `get_hook_pause_count: Callable[[], int]`
- `get_repeat_delay_ms: Callable[[], int]`
- `on_routes: Callable[[tuple[InputRoute, ...], int], None]`（タイマー由来の routes を実行する。**ロックの外で呼ぶ**）

定数:
- `PAIR_WINDOW_S = 0.016`
- 古い押下の時間 = `get_repeat_delay_ms() / 1000 + 0.3`

メソッド:
- `handle(event) -> MakeOnlyResult | None`
  - `event.scan_code` が表に無ければ `None`（呼び出し側は今の経路へ）
  - 時刻は `clock()` をこの中で取る
- `clear() -> None`: 全キーの状態と保留を消し、世代を上げる（ロックの中）
- `generation` プロパティ

キーごと（走査コードごと）の状態:
- 押している か
- 覚えた戻り値 `accept`
- 「押した」の `route` が actions を出したか `has_actions`
- 最後の押下の時刻
- 保留の時刻（無し = `None`）
- 「古い押下」の印
- 離した時刻
- 離した押下の `accept`

**遷移（暫定 46 §3.2 の表のとおり。すべて 1 本の `threading.Lock` の中で判定・状態更新・`route` / `release_state` の呼び出しまで行う。`on_routes` はロックの外）**

`down` のとき:
1. 押していない かつ 離した時刻から 16 ms 以内 → 捨てる。`accept` = 停止要求中なら `True`、それ以外は離した押下の `accept`。routes なし
2. 押していない（それ以外）→ **押した**
   - `route(event)` を呼び、`accept` と `has_actions = bool(route.actions)` を覚える
   - 押している状態へ。最後の押下 = t
   - 結果 = `(route.accept, (route,), 世代)`
3. 押している・保留なし
   - t − 最後の押下 > 古い押下の時間 なら「古い押下」の印をつけて保留 = t
   - そうでなければ保留 = t（印なし）
   - タイマーを `schedule(0.016, 満了処理)` で立てる（世代と保留の時刻を閉じ込める）
   - 最後の押下 = t
4. 押している・保留あり（時刻 p）
   - t − p ≤ 0.016 → **離した**
     - 保留を取り消す
     - `release_state(SyntheticKeyEvent("up", sc, name))`
     - 押していない状態へ。離した時刻 = t、離した押下の `accept` = 覚えた `accept`
   - t − p > 0.016 → その場で**保留の確定**（下）をしてから、3 と同じく新しい保留 = t
- 3・4 の戻り値: 停止要求中（`get_hook_pause_count() > 0`）なら `True`、それ以外は覚えた `accept`。確定で出た routes は結果の `routes` に入れる

**保留の確定**（ロックの中・保留の時刻から 0.016 秒を厳密に超えているときだけ）:
- 印なし かつ `has_actions` → `route(SyntheticKeyEvent("down", ...))` → routes に追加（リピート）
- 印なし かつ `has_actions` が偽 → 何もしない
- 印あり → `release_state(up)` → `route(down)` で押し直し、`accept` / `has_actions` を覚え直す → routes に追加
- 保留を外す

**満了処理**（タイマーのスレッド）:
- ロックを取り、世代が違う・保留が無い・保留の時刻が違う → 何もしない
- 経過 ≤ 0.016 → 残り時間で `schedule` し直す（早く満了した）
- そうでなければ保留の確定
- ロックを放してから、routes があれば `on_routes(routes, 世代)`

`up` のとき（表にある走査コード）:
- ロックの中で、保留を取り消し、押していない状態へ
- `release_state(event)` を呼ぶ（送信ガードに関係なく押下状態から外す）
- `route(event)` を呼ぶ
- 結果 = `(route.accept, (route,), 世代)`

### テスト `tests/test_make_only_keys.py`（新規）

時計とタイマーを差し替える（`schedule` は記録だけして、テストが手で満了させる）。`route` は記録するスタブ（`InputRoute(actions=(object(),), accept=False)` 等）。

確認する項目（暫定 46 §6 #1）:
- 1 回押して離す（0 → 45 ms → 56 ms）: 押した 1・離した 1・リピート 0
- 押し続ける（0 → 500 → 533 → …（33 ms ごと × 3）→ +22 → +13 ms）: 押した 1・リピート 3・離した 1
  - 各保留はタイマーを満了させて確定する
- 素早く 3 回連打: 押した 3・離した 3
- 古い押下 + 2 回組（0 → 1000 ms → 1011 ms・遅延 500 ms）: 離した 1・余計な出力 0
- 古い押下 + 単独（0 → 1000 ms → 満了）: 離した → 押した（routes 1）
- 最後のリピートの保留から 16 ms 以内に 2 回組: 離した 1・2 回目は捨てる
- 遅れた満了（保留から 21 ms で次の押下）: 保留をリピートで確定 → 新しい保留
- 早く満了（10 ms で満了処理）: 確定しない・`schedule` し直す
- 16 ms ちょうど: 次の押下が先でもタイマーが先でも「離した」
- 抑止の決定を覚える: 送信ガード相当（`route` は呼ばれない）でも続く押下は `False` / 停止要求中は `True`
- 素通しで actions なし: 続く押下は `True`・リピートで `route` を呼ばない
- 素通しで actions あり（`suppress: false` 相当）: リピートで `route` を呼ぶ
- `up` が届く: 保留が消え、`release_state` と `route` が呼ばれる
- `clear` の後の満了（古い世代）: 何もしない
- 241 / 242 以外は `None`
- `on_routes` がロックの外で呼ばれる（`on_routes` の中で `handle` を呼んでもデッドロックしない）

### 設計メモ / 制約

- `InputRoute` は `keyseq.application.input_router` から import してよい（同じ層）
- 状態機械は 1 ファイルで約 200 行以内を目安にする（超えるならキーごとの状態を dataclass に分ける）
- `print` を残さない。ログは `logging`

## 読むファイル

1. `instructions/history/46_make_only_keys.md` §3（全体）
2. `keyseq/application/input_router.py:1-60`（`InputRoute`）/ :87-110
3. `keyseq/application/key_state_manager.py:56-75`（`handle_event`）
4. 手本（注入と世代）: `keyseq/application/key_repeat.py:1-80`

## 含まない

- `hook_controller` / `app.py` への組み込み、タイマーのワーカーの実体、消去の呼び出し（task_03）
- `input_router` / `key_state_manager` の変更
- 正本反映（task_04）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_make_only_keys -v` が全 pass
- `grep -n "import keyboard\|tkinter\|pyautogui" keyseq/application/make_only_keys.py keyseq/domain/make_only_keys.py` が 0 件
- 既存テストが全 pass（`unittest discover -s tests`）

## 完了条件

- 上記の確認が pass し、**reviewer が採用**していること
- 実機目視は task_03 で行う
