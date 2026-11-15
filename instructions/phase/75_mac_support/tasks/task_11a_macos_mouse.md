# task_11a_macos_mouse

## 目的

macOS のマウスの操作を実装する（暫定 57 §5.4 の表「スクロール」「マウス操作」「クリック位置の取得」「物理状態」・§4.1 の未実測「中クリックの番号」）。今の `MacMouseBackend` は全メソッドが `NotImplementedError`、`MacWindowBackend.is_mouse_button_down` は常に False。

- pyautogui / pynput の実装は今 `windows/mouse_backend.py` にだけある。OS に依らない部分を `os_backend/` 直下の 1 ファイルへ移し、Windows と Mac の両方がそれを使う（M4・`file_organization_rules.md` の Feature Shared = レイヤ直下）。OS で違うのはスクロールの送り方だけ。
- infrastructure（`os_backend/`）とテストに限る。contracts・application・presentation・domain は変えない。Windows の動作は変えない（移すだけ）。

## 対象範囲

### `keyseq/infrastructure/os_backend/pyautogui_mouse.py`（新規）

- `class PyAutoGuiMouseBackend`: `windows/mouse_backend.py` の `WindowsMouseBackend` のうち `scroll_mouse` 以外（`capture_next_click`〔pynput の `mouse.Listener`〕・`cursor_position`・`move_cursor`・`click_at`・`click_mouse`・`mouse_down`・`mouse_up`・`_send_mouse_button`・`drag_mouse`）をそのまま移す（中身・FAILSAFE の扱い・`_pause` の指定を変えない）。`import pyautogui` / `from pynput import mouse` はこのファイルの先頭。
- `scroll_mouse` は持たない（サブクラスが実装する）。
- `ctypes` / Quartz 等の OS 固有の import をしない（`tests/test_os_backend_boundary.py` の `WINDOW_IMPORTS` / `MAC_IMPORTS`）。

### `windows/mouse_backend.py`

- `WindowsMouseBackend(PyAutoGuiMouseBackend)` にし、`scroll_mouse` と `_build_wheel_inputs`・定数・`send_input` の import だけ残す。`pyautogui` / `pynput` の import は消す（使わなくなる）。

### `macos/backend.py`

- `MacMouseBackend(PyAutoGuiMouseBackend)` にし、`scroll_mouse` を実装する:
  - `position` があれば `move_cursor(*position)`。`deltas` が空なら何もしない。
  - `deltas` の各値（`domain/mouse_scroll.py` の単位 = `WHEEL_DELTA` 120 が 1 ノッチ・端数あり）ごとに `CGEventCreateScrollWheelEvent` を 1 つ作って `CGEventPost(kCGHIDEventTap, ...)`。**単位は `kCGScrollEventUnitPixel`、量は `round(delta * 10 / 120)`（1 ノッチ = 10 px の近似・0 になる値は送らない）**。縦は wheel1（正 = 上）、横は wheel1 = 0・wheel2（正 = 右〔`mouse_scroll.py` の `sign`〕）。符号の向きは目視で確かめる。
  - イベントに `OWN_EVENT_MARK`（キー送信と同じ印）を付ける（自分の tap が読み飛ばせるように。tap はキーだけ見るので害は無い）。
  - 作れない（None）ときは `OSError`（Windows の `SendInput failed` と同じ扱い）。Quartz は既存の `self._quartz` / `load_quartz` の形で注入できるようにする（`MacMouseBackend.__init__(*, quartz=None)` を足す）。
- `MacWindowBackend.is_mouse_button_down`: `CGEventSourceButtonState(kCGEventSourceStateHIDSystemState, kCGMouseButtonLeft / Right)` のどちらかが真なら True（Windows = 左右だけ）。例外は False・ログは初回 1 回（`_physical_flags` の流儀）。
- `get_backend()` の組み立て（`:462` 付近）は `MacMouseBackend()` のまま（引数なしで動く）。

### テスト

- `tests/test_input_gateway_drag.py`・`tests/test_input_gateway_screen_grid.py`: patch 先を `pyautogui_mouse.pyautogui` に変える（Mac でも同じ共通クラスを通るので、基準線のエラー / 失敗のうちこの 2 本の分が消える見込み）。
- `tests/test_input_gateway_scroll.py`: Windows の SendInput を見るテストなので、`input_gateway` が使う backend を `WindowsMouseBackend()` に固定する patch を足して OS に依らず走るようにする（中身の期待値は変えない）。
- `tests/test_macos_keyboard_backend.py`（または新規 `tests/test_macos_mouse_backend.py`）: 偽 Quartz で `scroll_mouse` の縦 / 横・符号・端数（60 → 5 px）・0 になる値を送らない・`position` で移動・None で `OSError`・印が付く。`is_mouse_button_down` の左 / 右 / どちらも無し / 例外。
- `tests/test_os_backend_boundary.py` が通ること（新しいファイルに OS 固有の import が無い）。

## 読むファイル

- `instructions/history/57_mac_support.md` §4.1（`:85-90,119-121`）・§5.4 の表（`:294-312`）
- `keyseq/infrastructure/os_backend/windows/mouse_backend.py`（全体・移す元）
- `keyseq/infrastructure/os_backend/macos/backend.py`（`_physical_flags` `:35-46`・`write_text` の送信と印〔`_post_event`〕・`MacMouseBackend`・`MacWindowBackend`・`get_backend` の組み立て）
- `keyseq/infrastructure/os_backend/macos/event_tap.py:15-25`（`load_quartz`）
- `keyseq/domain/mouse_scroll.py:84-95`（`scroll_deltas` の単位と符号）
- `keyseq/infrastructure/os_backend/windows/win32_window.py:273-285`（`is_mouse_button_down` の意味）
- `tests/test_input_gateway_drag.py:1-30`・`test_input_gateway_screen_grid.py:1-30`・`test_input_gateway_scroll.py`（全体）・`tests/test_os_backend_boundary.py:1-60`

## 含まない

- モニタ一覧（`list_monitor_rects`）・クリック透過・窓の重なり順・NSWindow・`Capabilities` と無効化の UI（task_11b）。`test_screen_grid_overlay` の基準線の分は task_11b
- aqua のモーダル・トリガーの追加ダイアログが後ろへ回る件（task_11c）
- 割り当て禁止の文言（task_11d）
- 中クリックの `<Button-2>` のバインドの変更（目視で番号を確かめるだけ。違えば報告して止める）
- 再起動の実装の置き場（task_12 の M4）

## 確認

Mac（verifier）: compile clean・`tests` の失敗 / エラーが基準線（失敗 6・エラー 10）から増えない（drag / screen_grid の分は減る見込み。減った数を報告）・smoke pass。
- tests: 上のテスト・`tests.test_os_backend_boundary`・`tests.test_input_gateway_drag` / `_screen_grid` / `_scroll`。
Windows: task_09〜11 の Windows 検証と合わせて `tests`（移しただけで動作が変わらないこと・drag / scroll のテスト）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。`codebase_map.md` の Mac の backend の行（マウス）と Windows の `mouse_backend.py` の行・`mac_test_baseline.md:36` の行を追従（メイン）。
- 実機目視（Mac・本タスクで実施）:
  1. アクションダイアログの「クリック位置を取得」で画面をクリック → その位置の座標が入る（Retina でも、そのあとのクリックのアクションが同じ位置を押す）。フック稼働中でもキーの置換が今どおり動く（pynput の監視と §5.1 の tap の共存）。
  2. クリック・ダブルクリック・押す / 離す・ドラッグのアクションが動く。
  3. スクロールのアクション（ノッチ・量の両方・上下左右）が向きどおりに動き、1 ノッチが物理のホイール 1 ノッチと同じくらい（違えば換算を報告）。
  4. 中クリック（トラックパッドなら外付けのマウス）で、`<Button-2>` をバインドしている欄（呼び出しの一覧のパンなど）が反応するか。反応しなければ Tk の番号を記録して報告。
  5. マウスのボタンを押したままキーボードUIを動かす操作（`keyboard_window.py:340-365` の `is_mouse_button_down`）が Windows と同じに振る舞う。

## 起票レビュー（reviewer「修正して採用」2026-11-15）の反映 — 上の記述に優先する

- **中（印の付け方）**: `MacKeyboardBackend._post_event` は `CGEventSetFlags` も呼ぶのでマウスでは使わない。`MacMouseBackend.scroll_mouse` は `q.CGEventSetIntegerValueField(event, q.kCGEventSourceUserData, OWN_EVENT_MARK)`（`OWN_EVENT_MARK` は `backend.py:14` で import 済み）→ `q.CGEventPost(q.kCGHIDEventTap, event)` を直接呼ぶ。
- **中（行番号）**: 組み立ては `get_backend` ではなく `macos/backend.py:513-517` の `create_backend()`（`MacMouseBackend()` は `:517`）。`_physical_flags` は `:37` 付近。
- **中（scroll のテスト）**: `tests/test_input_gateway_scroll.py` は `patch.object(input_gateway, "get_backend", return_value=SimpleNamespace(mouse=mouse_backend.WindowsMouseBackend()))` で backend を固定する（`input_gateway.py` が `get_backend` を名前で import している前提。違えば実在する参照先を patch する）。drag / screen_grid は `from keyseq.infrastructure.os_backend import pyautogui_mouse` → `patch.object(pyautogui_mouse, "pyautogui", ...)`。
- **中（端数の丸め）**: px = `delta * PIXELS_PER_NOTCH / 120`（`PIXELS_PER_NOTCH = 10` をモジュール定数に 1 か所）。0 でない delta は**符号を保って最低 1 px**（`int(math.copysign(max(1, floor(abs(x) + 0.5)), delta))`）。delta が 0 なら送らない。テストは 60 → 5・6 → 1・-6 → -1・1 → 1。
- **低（横の符号）**: wheel2 の正が右か左かは目視 3 で確かめ、逆なら報告して符号を直す（テストの期待値は目視後に確定）。
- **低（テストの追加）**: wheel1 / wheel2 の割り当て・`deltas` が空・`CGEventPost` の回数が delta の数と一致。
- **低（物理状態の差）**: `kCGEventSourceStateHIDSystemState` は物理のボタンだけ。Windows の `GetAsyncKeyState` は注入も含むので、自分の `mouse_down` のアクションの保持中は Windows = True・Mac = False になる（§5.4 は「物理状態」なので許容・仕様差として記録）。
- **中（pynput の権限）**: pynput の `mouse.Listener` は Mac で自前の CGEventTap を作る。目視 1 の前に、権限が足りないと「クリック位置を取得」が無反応になるか（例外が出ないならリスナーが無言で止まるか）を観察して報告する。権限の案内への接続は本タスクに含めない（無反応なら報告して止める）。
- **低（import）**: smoke で Mac の `macos/backend.py` の import（pyautogui の top-level import を含む）が通ることを確認する。
- **目視 5 の具体**: キーボードUIの窓の縁を左ボタンで押したままドラッグしてリサイズする → ドラッグ中は比率の補正が走らず、離した後に比率が収まる（暴れない・補正されないまま残らない）。aqua のリサイズ中に `after` が動くかも見る。
- **codebase_map**: `:915` の `windows/mouse_backend.py` の行・Mac の backend の行（`:39`）・新規 `pyautogui_mouse.py` の行を追従。

## 実装後の改訂（2026-11-15・Mac 目視・暫定 57 v0.14）— 上の記述に優先する

目視の結果: 1・5 は OK。4 は試せるマウスが無く未確認。2・3 は NG。
- 2: ダブルクリック（回数 2）が効かない。押すのアクションの後に手でマウスを動かしても窓が動かない。ドラッグのアクションがクリックになる。
- 3: 横の向きが逆。

メインの調査: pyautogui の Mac 実装（`_pyautogui_osx.py`）は、回数つきのクリックで単独のクリックを回数分送るだけで、`kCGMouseEventClickState` を付けない。ボタンを押した後の移動も `kCGEventMouseMoved` で送る。また macOS は、送った down を物理のボタンの状態に数えないので、手で動かした移動もただの移動になる。ユーザー判断は「この案で直す」、向きの設定は idea_58 に分けた。

### `macos/backend.py` の `MacMouseBackend`（`scroll_mouse` 以外は今は共通クラスのまま）

- **横スクロールの符号**: wheel2 に `-amount` を送る（`deltas` の正 = 右）。縦は変えない。
- **`click_mouse(x, y, button, clicks)`**: Quartz で直接送る。
  - `move_cursor(x, y)` の後、i = 1..clicks で down / up の組を送る。どちらにも `CGEventSetIntegerValueField(event, kCGMouseEventClickState, i)` と印（`kCGEventSourceUserData` = `OWN_EVENT_MARK`）を付けて、`CGEventPost(kCGHIDEventTap, ...)` する。
  - ボタン（`"left"` / `"right"` / `"middle"`）は、種類（`kCGEventLeftMouseDown` 等 / `kCGEventOtherMouseDown`）と `kCGMouseButton*` に対応させる表で引く（`drag_mouse` と保持中の tap でも使う）。
  - 位置は `CGEventCreateMouseEvent` の第 3 引数（`(x, y)`）。イベントが None なら `OSError`。
  - `click_at` は変えない（1 回のクリック）。
- **`drag_mouse(x, y, to_x, to_y, button, duration_sec)`**: Quartz で直接送る。
  - `move_cursor(x, y)` の後、down を送る。
  - 途中の位置を直線で補間し、`kCG*MouseDragged` で送る。回数は `max(1, round(duration_sec / 0.01))`。各回の間に `duration_sec / 回数` だけ `time.sleep` する。最後の位置は必ず `(to_x, to_y)` にする。
  - `finally` で up を `(to_x, to_y)` に送る（共通クラスと同じく、途中の例外でも離す）。
  - 印を付ける。テストで待たないように、sleep は注入できるようにする（例: `__init__(*, quartz=None, sleep=time.sleep)`）。
- **`mouse_down(button, x, y)` / `mouse_up(button, x, y)`**:
  - down を送った後、保持中の tap（下記）をそのボタンで開始する。
  - up を送った後、tap を止める。
  - down / up は Quartz で送り、印を付ける（tap が自分の down / up を物理と取り違えないため。tap の開始より後に届くことがある）。位置の指定があれば先に `move_cursor`。
  - 保持中に別のボタンの down が来たら、tap を新しいボタンに切り替える（保持は 1 つだけ）。

### 新規 `macos/mouse_hold_tap.py`（`MouseHoldTap`）

- **`start(button)`**: listen-and-modify の CGEventTap を作る（`kCGSessionEventTap`・`kCGHeadInsertEventTap`・`kCGEventTapOptionDefault`）。
  - mask は `kCGEventMouseMoved` と、全ボタンの down / up。
  - 専用のスレッドで CFRunLoop を回す（`event_tap.py` の `_run` / `stop` の流儀・daemon・0.1 秒刻み）。
- **コールバック**:
  - `kCGEventMouseMoved` は、`CGEventSetType(event, 保持中のボタンの Dragged)` と `CGEventSetIntegerValueField(event, kCGMouseEventButtonNumber, 番号)` で書き換えて返す。
  - 保持中のボタンの down / up で、印の無いもの（物理）が来たら、書き換えを終え、tap を止める予約をする。イベントはそのまま流す。
  - 例外は素通し（イベントをそのまま返す）。ログに残す。
- **`kCGEventTapDisabledByTimeout` / `ByUserInput`**: 再有効化する。
- **`stop()`**: tap を外し、スレッドを止める。冪等にする。tap のスレッド自身から呼ばれても固まらないようにする。
- **tap を作れない（None・例外）とき**: 書き換えずに今の動作のままにする（例外を上へ出さない・ログは初回 1 回）。
- Quartz は注入できるようにする（`load_quartz` の流儀）。

### テスト（`tests/test_macos_mouse_backend.py`）

- 横の符号。
- 回数 2 で down / up が 2 組、ClickState が 1・2。
- ボタンの対応（left / right / middle）。
- ドラッグの Dragged の回数・最後の位置・例外でも up。
- mouse_down で tap 開始・mouse_up で停止。
- tap のコールバックが MouseMoved を Dragged に書き換える。物理の up で終える。印つきは終えない。
- tap を作れないときは例外にならない。
- Tk なし・偽 Quartz・Windows でも走る。

### 目視（やり直し）

- 2: クリック回数 2 で、ダブルクリックとして効く（例: Finder でフォルダが開く）。
- 2: ドラッグのアクションで窓が動く。
- 2: 押す → 手でマウスを動かす → 離す、で窓が動く。保持中に手でクリックしたら、保持が終わる。
- 3: 左右の向きが合う。ナチュラルなスクロールをオフにしても、縦横とも向きが変わらない。
- 4 は未確認のまま残す（マウスを用意できたとき）。

### 目視の結果（2026-11-16・Mac）

- 再目視 OK（ダブルクリック・ドラッグのアクション・押す → 手で動かす → 離す・横スクロールの向き）。1・5 は 1 回目で OK。
- 4（中クリックの `<Button-2>`）は試せるマウスが無く未確認（マウスを用意できたときに確かめる）。
- reviewer（改訂分）採用。参考の指摘のうち、停止の予約の競合（同じ tap のときだけ止める）と字下げはメインが修正。
