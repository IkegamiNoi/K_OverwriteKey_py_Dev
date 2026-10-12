# task_03_grid_session_and_router

## 目的

枠の表示中のキー操作を扱う application の状態機械（ScreenGridSession）を作り、`InputRouter` の振り分けへ組み込み、枠 ON のキーマップがあればフックを開始・再開できるようにする（暫定 40 §4.1〜§4.5・§2-11・§2-12）。
**application 中心（新規 1 モジュール + `input_router.py`・`hook_coordinator.py`）+ `hook_controller.py` の開始 / 再開の引数の受け渡しだけ。モニタの列挙・カーソル移動 / クリックの実体・枠の窓・`app.py` の配線は task_04。スキーマ不変。**

## 対象範囲（application + hook_controller の引数のみ）

### 新規 `keyseq/application/screen_grid_session.py`（tkinter・ctypes・pyautogui に依存しない）

- 型（不変の dataclass）
  - `MonitorInfo(id: str, rect: Rect, primary: bool)`（`id` = `domain.screen_grid.monitor_identifier` の値。task_04 の infrastructure がこれを返す）
  - `GridRouteSnapshot(visible: bool, generation: int, suppress_keys: frozenset[str], esc_active: bool)`（フックのスレッドが読む値。**丸ごと差し替えて公開**し、途中の状態を見せない）
  - `GridView(visible, monitor: MonitorInfo | None, level: int, region: Rect | None, cells: tuple[tuple[Rect, str], ...], selected: int | None, generation: int)`（task_04 の窓が描く値）
- `ScreenGridSession.__init__(*, list_monitors: Callable[[], list[MonitorInfo]], cursor_position: Callable[[], tuple[int, int]], move_cursor: Callable[[int, int], None], click: Callable[[int, int, str], None], on_view_changed: Callable[[], None] | None = None)`（実体は task_04 が注入する。`click` の第 3 引数は `"left"` / `"right"`）
- `snapshot() -> GridRouteSnapshot` / `view() -> GridView`
- `sync(*, keymap_id: str, grid: dict | None, active: bool) -> None`（**UI スレッドで、表示の同期の契機ごとに呼ぶ**。呼び出しの配線は task_04）
  - 表示する = `active`（フック動作中 ∧ キーマップ一時停止でない ∧ フックの一時停止でない を呼び出し側が判定）∧ `grid` が dict ∧ `grid["enabled"]` が真
  - **世代を進めてやり直す**（§4.1）: 非表示 → 表示 / 表示中に `keymap_id` が変わった / 表示中に `grid` の内容が変わった（ダイアログの OK を含む。等価比較）。やり直し = モニタを列挙し、カーソルのある画面（無ければ主、無ければ先頭）の最上段・選択なしから
  - 非表示にしたら状態を捨てる（世代も進める。古い世代の操作を無効にするため）
  - 表示中に条件も内容も変わらなければ何もしない（状態を保つ）
- `handle(action: GridKeyAction) -> None`（UI スレッド。§4.3 の表のとおり）
  - 非表示、または `action.generation` が今の世代と違えば何もしない
  - 今の段の枠のキー: リピートなら無視 / その枠を選び `move_cursor` で中心へ（`domain.screen_grid.rect_center`）
  - `space`: リピート無視 / 選択あり ∧ `can_subdivide(選択の矩形, sub)` なら 1 段深く（領域 = 選択の矩形・選択なし・カーソルは動かさない）。それ以外は何もしない
  - `esc` / `backspace`: リピート無視 / 段 ≥1 なら 1 段戻り、戻った段で細分化した枠を選んだ状態にしてカーソルをその中心へ。段 0 なら何もしない
  - `enter` / `num enter`: リピートならクリックしない / 対象 = 選択の中心、選択なしで段 ≥1 なら今の領域の中心、段 0 で選択なしなら何もしない。**クリックの直前にモニタを列挙し直し、今の画面の `id` が無ければクリックせずやり直し（カーソルのある画面の最上段）**。あれば `move_cursor` → `click(x, y, "right" if action.shift else "left")` → 最上段・選択なしへ（同じ画面・世代は進めない）
  - `tab`: リピート無視 / モニタを列挙し直し、今の画面が無ければやり直し。画面が 1 つなら何もしない。それ以外は列挙順で次の画面の最上段・選択なし（カーソルは動かさない）
  - それ以外（suppress する集合に入るが今の段で意味が無いキー）: 何もしない
  - 状態が変わったら `on_view_changed` を呼ぶ
- suppress する集合（§4.3）= **今列挙されている全画面の最上段のキー（記録の無い画面は既定）∪ 細分化のキー ∪ `enter`・`num enter`・`space`・`backspace`・`tab`**。`esc` は入れない（`esc_active` で別扱い）。**表示の開始・終了・形の変化・モニタの列挙し直しで構成が変わったときにだけ作り直す**（段・選択では変えない・§4.4）
- `esc_active` = 段 ≥1。段が変わるたびに snapshot を差し替える
- 形の取得は `domain.screen_grid` の `top_layout_for` / `sub_layout_of` / `top_cell_rects` / `sub_cell_rects` / `can_subdivide` / `rect_center` を使う（独自に計算しない）
- `move_cursor` / `click` / `list_monitors` の例外は握りつぶさず呼び出し側へ伝える（task_04 が UI で扱う）。ただし例外が出ても内部状態が中途半端にならないようにする（クリックの例外 → 最上段へ戻す前に送出してよいが、snapshot は一貫した値のまま）

### `keyseq/application/input_router.py`

- `GridKeyAction(key: str, generation: int, shift: bool, repeat: bool)` を他のアクションと同じ形で追加
- `InputRouter.__init__` に `get_grid_snapshot: Callable[[], object] | None = None` を追加（既定 None = 枠なし。既存の呼び出しはそのまま動く）
- `handle` の**直接切替キーの判定の後・トリガーの前**に（§4.4）: snapshot が `visible` なら
  - ctrl / alt / windows（左右・`alt gr` を含む）のどれかを押している（`key_state_manager.is_pressed`）→ 素通し（`InputRoute()`）
  - 押したキー自体が修飾キー（`domain.key_hold.MODIFIER_KEY_NAMES`）→ 素通し
  - `esc`: `esc_active` なら `GridKeyAction` を返して suppress（`accept=False`）、偽なら素通し
  - `suppress_keys` に入る → `GridKeyAction(key, snapshot.generation, shift=shift〔`shift` / `left shift` / `right shift` のどれかを押している〕, repeat)` を返して suppress
  - それ以外 → 素通し（**トリガー・置換へ進まない**・§2-1）
- 停止キー・トグルキー・直接切替キー・send guard・フックの一時停止・`custom_enabled` 偽の扱いは今のまま（枠の判定より先）

### `keyseq/application/hook_coordinator.py`

- `start` と `can_enable_custom_input` に `has_grid_keymaps: bool = False` を追加し `_can_process_input` へ渡す。真なら「トリガーまたは置換がある」と同じに扱う（「トリガーが1件も登録されていません」等で拒否しない・§2-11）

### `keyseq/presentation/controllers/hook_controller.py`（引数の受け渡しだけ）

- `start_hook`（:137）と `toggle_custom_input_enabled` の再開側（:197）の両方で、`has_grid_keymaps=` に「`self._app.data["keymaps"]` のどれかの `grid` が dict で `enabled` が真」を渡す。判定は domain の純関数（`keyseq/domain/screen_grid/` に `has_enabled_grid(keymaps) -> bool` を追加し `__init__.py` の `__all__` へ）を使う
- それ以外（`on_input_event`・`_execute_reserved_action` 等）は変えない（`GridKeyAction` の実行の配線は task_04）

### テスト

- 新規 `tests/test_screen_grid_session.py`（偽の `list_monitors` / `cursor_position` / `move_cursor` / `click` を注入）:
  sync の表示条件と世代（非表示 → 表示・keymap_id の変化・grid の変化・同じ値の再 sync では世代を保つ・非表示で世代が進む）/ カーソルのある画面から始まる（負の y の画面を含む）/
  枠のキーで選択とカーソル移動 / Space の細分化と 4px で何もしない / Esc・BackSpace で戻ると細分化した枠が選ばれる / Enter 左・Shift 右・リピートでクリックしない・段 0 選択なしで何もしない・段 ≥1 選択なしは領域の中心 /
  クリック前に画面が消えていたらクリックせずやり直し / Tab の循環・1 画面で何もしない / 古い世代の action を無視 / suppress する集合の中身（全画面の最上段 ∪ sub ∪ 固定 5 キー・esc を含まない）と段では変わらないこと / esc_active
- `tests/test_input_router.py` に追加（既存は変えない）: 枠の表示中に suppress する集合のキー → `GridKeyAction`・accept False / それ以外 → 素通しでトリガー・置換が効かない / ctrl・alt・windows 押下中は素通し / Shift 押下で shift=True / esc は esc_active で分かれる / 停止・トグル・直接切替キーが先に効く / `get_grid_snapshot` 未指定なら従来どおり
- `tests/test_hook_coordinator.py` に追加: トリガーも置換も無くても `has_grid_keymaps=True` なら開始・再開できる
- `has_enabled_grid` の単体テストを `tests/test_screen_grid.py` へ追加

### 設計メモ / 制約

- 状態の変更は UI スレッド（`sync` / `handle`）だけ。フックのスレッドは `snapshot()` を読むだけ（ロックは不要な作り = 不変オブジェクトの参照の差し替え）
- 画面は列挙の番号ではなく `MonitorInfo.id` と矩形で持つ（§4.1）
- 300 行を大きく超えるなら `keyseq/application/screen_grid_session/` パッケージに分けてよい（型 / セッション）
- `GridKeyAction` は `input_router.py` に置き、session 側がそれを import する（循環させない）

## 読むファイル

- `instructions/history/40_screen_grid_cursor.md` §2・§4（全体）
- `keyseq/application/input_router.py`（全体・編集対象）
- `keyseq/application/hook_coordinator.py`（全体・編集対象）
- `keyseq/presentation/controllers/hook_controller.py:119-205`（開始と再開）
- `keyseq/application/key_state_manager.py:47-95`（`is_pressed`）
- `keyseq/domain/screen_grid/__init__.py`・`normalize.py`・`geometry.py`（使う API）・`keyseq/domain/key_hold.py:12-38`
- テストの手本: `tests/test_input_router.py` の冒頭 80 行・`tests/test_hook_coordinator.py` の冒頭 40 行

## 含まない

- モニタの列挙・カーソル移動 / クリックの実体（pyautogui）・枠の窓・`app.py` での `ScreenGridSession` の生成と `InputRouter` への注入・`sync` の呼び出しの配線・`GridKeyAction` の UI スレッドでの実行（task_04）
- ダイアログの「枠を使う」（task_05）・編集の窓（task_06）
- 正本への反映・`codebase_map.md`（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_screen_grid_session tests.test_input_router tests.test_hook_coordinator tests.test_screen_grid` が pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass（`hook_controller.py` を触るため。既知の実行順依存 2 件は current.md「テスト負債」で切り分け）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は不要（task_04 で配線後にまとめて実施）
