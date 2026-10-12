# task_06_grid_editor

## 目的

キーマップの編集ダイアログに「枠を編集…」ボタンを足し、最上段の形（画面ごと）と細分化の形を編集する窓を作る（暫定 40 §8.1・§8.2・§5・§2-4〜§2-8）。
**domain に形の編集の純関数（新規 1 モジュール）+ presentation に編集の窓（新規）+ `KeymapEditDialog` と `apply_keymap_edit` の最小の追加。application・infrastructure は既存の API を使うだけで不変。スキーマ不変。実装後にユーザーの実機目視。**

## 対象範囲

### 新規 domain `keyseq/domain/screen_grid/editing.py`（純関数・不変の TopLayout を受けて新しい TopLayout を返す）

- `split_row(layout, row_index, reserved) -> TopLayout`: 選んだ段を上下に等分（h を半分ずつ）。新しい段（下側）は元の段と同じ列の幅の並びで、キーは `next_free_key` で自動割当（形の中で重複させない）
- `split_cell(layout, row_index, col_index, reserved) -> TopLayout`: 選んだ枠を左右に等分（w を半分ずつ）。新しい枠（右側）のキーは自動割当
- `delete_row(layout, row_index) -> TopLayout` / `delete_cell(layout, row_index, col_index) -> TopLayout`: 消した分は隣（下の段 / 右の枠、末尾なら上 / 左）が広がる。**最後の 1 段・段の最後の 1 列は消せない**（そのときは入力と同じ値を返す）
- `move_row_boundary(layout, boundary_index, new_ratio, min_ratio) -> TopLayout`: 段 `boundary_index` と `boundary_index + 1` の境界を、全体の高さに対する比率 `new_ratio` へ動かす。隣の 2 段がどちらも `min_ratio` 未満にならない範囲に止める
- `move_cell_boundary(layout, row_index, boundary_index, new_ratio, min_ratio) -> TopLayout`: 同じことを段の中の列の境界で行う
- `set_cell_key(layout, row_index, col_index, key) -> TopLayout`
- 比率は呼び出し側が px から作る（`min_ratio = MIN_EDIT_CELL_PX / 画面の高さ（幅）`・§8.2「隣の枠が 8px 未満にならない」）。比率の和は 1 を保つ
- `__init__.py` の `__all__` へ追加

### 新規 presentation `keyseq/presentation/screen_grid/grid_editor_window.py`（必要なら操作パネルを `grid_editor_panel.py` に分ける・各 300 行以内）

- `GridEditorWindow(parent, *, grid: dict | None, monitors: list[MonitorInfo], start_monitor_id: str, reserved: set[str])`。`result` = 編集後の `{"monitors": {...}, "sub": {...}}`（OK）/ `None`（キャンセル）
  - `grid` は深い写しで持ち、OK までは呼び出し元に書かない
  - 対象の画面 = `start_monitor_id`（呼び出し側がカーソルのある画面を渡す）。画面の切替は操作パネルの選択肢（列挙順・識別子を表示）
  - 記録の無い画面は既定の形の写しから始める（`top_layout_for`）
- 窓: 対象の画面いっぱいの、半透明（`-alpha` 0.5 前後）・枠なし・最前面の窓（**クリックを受ける**・フォーカスを取ってよい）。今の画面の最上段の形の線とキーを描き、選んだ枠（とその段）を強調
- 操作パネル: 小さな `tk.Toplevel`（最前面・編集の窓の上・主モニタまたは対象の画面の隅）。
  画面の切替 / 段の追加・削除 / 列の追加・削除（選んだ段・枠に対して）/ 振り直し（`reassign_top_keys`）/ この画面を既定に戻す（その画面の記録を `monitors` から消す）/
  細分化の設定（行数・列数の Spinbox 1〜9・キーは読む順に空白区切りの 1 つの Entry。行数・列数を変えたら `auto_fill_sub_keys` で埋め直す）/ OK / キャンセル
- マウス: 段の境界（横線）・段の中の列の境界（縦線）の近く（±4px）を押してドラッグすると境界が動く（`move_row_boundary` / `move_cell_boundary`）。それ以外の押下で枠を選ぶ
- キー: 枠を選んでいる間に押したキー（`normalize_tk_key_event`）をその枠のキーにする（修飾キー単独は無視）。**選んでいる間の Esc は選択の解除だけ**。選択なしの Esc はキャンセル（窓を閉じて捨てる）
- OK: 編集した全画面の形に `validate_top(layout, reserved)`、細分化に `validate_sub(sub, reserved)`。理由があれば `messagebox.showerror`（理由と画面の識別子を示す）で窓は閉じない。無ければ `result` を入れて閉じる
- 記録する形 = 編集した画面だけ `monitors[識別子] = top_layout_to_json(...)`（触っていない画面は元の記録のまま）
- モーダル（`grab_modal` の流儀）。フックは呼び出し元のダイアログで既に一時停止中（§8.2「ダイアログの子として扱う」）なので、ここでは一時停止しない

### `keyseq/presentation/dialogs/keymap_edit_dialog.py`

- 引数 `initial_grid: dict | None = None` と `grid_editor_context: Callable[[], tuple[list[MonitorInfo], str, set[str]]] | None = None` を追加（呼び出し側が「モニタの一覧・カーソルのある画面の識別子・設定で変わる予約キー」を返す。None ならボタンを出さない = 既存の呼び出しは今のまま）
- 「枠を使う」の横に「枠を編集…」ボタン（**チェックが偽でも押せる**・§8.1）。押すと `GridEditorWindow` を開き、`result` があれば下書き（`self._grid_draft`）に入れる
- 予約キーには、ダイアログの切替キー欄の今の値も足す（自分の切替キーを枠のキーにさせない）
- `_ok` の結果に、下書きがあるときだけ `"grid": 下書き` を足す（無いときは今の結果のまま）

### `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`

- 編集ダイアログの呼び出しで `initial_grid` = 対象 keymap の `grid`（dict なら）と `grid_editor_context` を渡す。context は `win32_window.list_monitor_rects()` を `MonitorInfo(monitor_identifier(*rect), rect, primary)` へ変換した一覧（`ScreenGridController` の変換と同じ。重複させるなら `ScreenGridController` に公開メソッド `list_monitors()` を足してそれを使う）・`app.input_gateway.cursor_position()` を含む画面の識別子（無ければ主・先頭）・停止キー / トグルキー / `keymap_switch_keys` の全キー
- `apply_keymap_edit` に `new_grid_shapes: dict | None = None` を追加（None = 変えない）。あれば keymap の `grid` の `monitors` と `sub` をそれで置き換える（`grid` が無ければ `{"enabled": False, ...}` で作ってから。`enabled` は `new_grid_enabled` の処理に任せる）。内容が変わったら `changed = True`
- 呼び出し元から `result.get("grid")` を渡す

### テスト

- 新規 `tests/test_screen_grid_editing.py`: 各関数（等分の比率・新しいキーの自動割当と重複なし・最後の 1 段 / 1 列は消せない・消した後に隣が広がり和が 1・境界の移動が min_ratio で止まる・入力不変）
- 新規 `tests_ui/test_grid_editor_window.py`: 偽のモニタ 2 つで開く / 枠の選択とキーの設定 / 選択中の Esc は解除だけ・選択なしの Esc でキャンセル / 段・列の追加と削除のボタン / 境界のドラッグ（event_generate か内部のハンドラを直接呼ぶ）/ 画面の切替で別の画面の形を編集し、OK で編集した画面だけ記録 / 既定に戻すで記録が消える / 細分化の行数を変えるとキーが埋め直される / 予約キー・重複・空のキーで OK を拒否して窓が残る
- `tests_ui/test_task06_keymap_management_ui.py` に追加: `grid_editor_context` が None ならボタンが無い / ボタンから開いた窓の OK で結果に `grid` が入り、`apply_keymap_edit` で keymap の形が置き換わり未保存になる / キャンセルで変わらない
- 既存テストは変えない

### 設計メモ / 制約

- 形の計算は domain の関数だけで行い、窓は px ↔ 比率の変換と描画・入力に限る
- presentation から ctypes を呼ばない（モニタの一覧は `win32_window` 経由・既存の関数を使う）
- 編集の窓は枠の表示（`GridOverlayWindow`）とは別物。表示中の枠には触れない（ダイアログ表示中はフックが止まり枠は隠れている）

## 読むファイル

- `instructions/history/40_screen_grid_cursor.md` §2-4〜§2-8・§5・§8
- `keyseq/domain/screen_grid/__init__.py`・`models.py`・`assignment.py`・`geometry.py`
- `keyseq/presentation/dialogs/keymap_edit_dialog.py`（全体・編集対象）
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:370-460`
- `keyseq/presentation/screen_grid/screen_grid_controller.py`・`grid_overlay_window.py`（変換と描画の手本）
- `keyseq/application/screen_grid_session.py:1-40`（`MonitorInfo`）
- `keyseq/presentation/modal.py:122-160`（`grab_modal`）・`keyseq/presentation/tk_keys.py:71-80`（`normalize_tk_key_event`）
- テストの手本: `tests_ui/test_screen_grid_overlay.py` の冒頭 60 行

## 含まない

- `KeymapSwitchBatchDialog` での形の編集（§12・チェックのみ）
- 細分化後の境界のドラッグ（§2-5・§12）
- 正本への反映・`codebase_map.md`（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストのモジュールが pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` と `discover -s tests_ui`（1 本ずつ）が全 pass
- **ユーザーの実機目視**（task_05 の分も含む）: キーマップの編集で「枠を使う」→ OK で枠が出る / 追加のダイアログの「枠を使う」で枠 ON のキーマップができる /
  「枠を編集…」で編集の窓が出て、境界のドラッグ・段と列の追加 / 削除・キーの変更・振り直し・既定に戻す・細分化の変更・画面の切替ができる / OK → 枠の表示に反映 / 保存 → 再起動で形が保たれる / キャンセルで変わらない / 予約キーで拒否される
- フック動作中のクリック所要時間を `scratchpad/run_grid_check.py` のログで一度確かめる（task_04 からの申し送り）

## 完了条件

- 上記確認 pass・**reviewer 採用**・ユーザーの実機目視で問題なし

## 実機目視の指摘と修正（2026-10-12・ユーザー判断を含む）

1回目の実機目視（3 で中断）の指摘。以下を task_06 の範囲で直してから目視をやり直す。

1. **開始の画面に編集の窓が出ない**（画面を切り替えると出る）。表示前に `overrideredirect` と `-alpha` を当てた窓が最初の表示で描かれないため。→ 最初の `<Map>` の後（1 回だけ）に `-alpha` と `geometry` を当て直す（`switch_monitor(self.monitor.id)` 相当）。`grab_modal` は `__init__` の最後のまま（構造テスト）
2. **`period` などのキーが効かない**: `normalize_tk_key_event` は記号キーを `period` / `comma` 等の Tk の名前のまま返し、フックの名前（`.` / `,`）と一致しない。
   → **ユーザー判断: 編集の窓だけ直す**。押したキーを**フックと同じ方法**で名前にする: テンキーは既存の `numpad_name_from_tk_event`、それ以外は `event.keycode`（VK）→ Win32 `MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)` でスキャンコード → `app.layout.resolve_key_name_from_scan_code(scan)`（`InputRouter` の `resolve_scan_code` と同じ）。取れなければ `normalize_tk_key_event` へ戻す。
   - infrastructure `win32_window.py` に `vk_to_scan_code(vk: int) -> int | None`（失敗・非 Windows は None）
   - `GridEditorWindow` に `key_name_from_event: Callable[[object], str] | None = None`（None なら `normalize_tk_key_event`）。`KeymapEditDialog` に同名の引数を足して渡し、`keymap_panel_controller.py` が上の合成を渡す
   - 既存のキー取得（トリガー等）の `tk_keys.py` は変えない（アプリ全体の修正は別の idea として起票）
3. **境界をドラッグできることが分かりにくい**: 境界（±4px）の上ではカーソルを `sb_v_double_arrow`（行の境界）/ `sb_h_double_arrow`（列の境界）にし、離れたら戻す（`<Motion>`）
4. **追加・削除のボタンがグレーで使えない**（枠を選ぶ前は無効のため・自動の再現では選択で有効になる）: 開いたとき・画面を切り替えたときに**左上の枠を選んだ状態**にする。パネルに「枠をクリックして選ぶ → キーを押すとその枠のキー」の短い案内を出す
5. **「段」→「行」（ユーザー判断）**: 編集の窓・パネル・OK の検査の理由の文言で、最上段の横の帯を「行」と表記する（ボタン「行の追加」「行の削除」・理由「行 2・列 3: …」）。domain の `validate_top` の理由文字列も「行」に揃える。細分化の深さ（最上段 / 段 ≥1）の用語は画面に出さないので変えない。正本への昇格（task_08）で用語を整理する
6. **細分化のキーの入力（ユーザー判断: 行ごとに入力欄を分ける）**: 行数ぶんの Entry を縦に並べ、各欄にその行のキーを空白区切りで入れる（区切り記号は使わない。`,` `/` もキーにできる）。行数・列数を変えたら欄を作り直し `auto_fill_sub_keys` で埋め直す。OK では各欄の語数が列数と一致しなければ「細分化・行 n: キーは C 個にしてください」で拒否

追記（メイン・reviewer 採用）: 今のキーボード配列（US TKL 等）の定義はスキャンコードを持たず、配列による解決が空を返す。このため 2 の解決の順を
**テンキー → 配列のスキャンコード → 修飾なしの文字（`win32_window.vk_to_char`・`MapVirtualKeyW(vk, MAPVK_VK_TO_CHAR)`・フックの `event.name` と同じ形）→ `normalize_tk_key_event`** にした。
「この画面を既定に戻す」の後も左上の枠を選ぶ（4 と揃える）。読込時のログの理由も「行」に揃えた。
