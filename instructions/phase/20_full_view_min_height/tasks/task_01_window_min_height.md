# task_01_window_min_height

## 目的

フル表示のウィンドウに縦方向の最小サイズを設ける本体を実装する（暫定仕様 18 §2-2・§2-5・§3-1〜§3-6）。
一覧の `height` を既定の半分（6 / 6 / 9）にし、**`paneconfigure` 後に測ったウィンドウの要求高さ**を `wm minsize` の高さとして、
フル表示中に最小サイズを当てる全箇所で使う。受け入れ条件は暫定 §5-1・§5-3・§5-5・§5-6。

**presentation 限定・domain / application / infrastructure 不変・JSON 不変（高さは保存しない）**。幅の計算・既定幅・ウィンドウ幅の保存判定は変えない。

## 対象範囲（presentation 限定・View 3 ファイル + pane_layout 2 ファイル + tests_ui 新規 1 ファイル）

### `keyseq/presentation/views/full_view/keymap_box.py` / `trigger_box.py` / `sequence_box.py`

- 一覧の `height` を変える: `keymap_listbox` 12 → **6** / `trigger_list` 12 → **6** / `action_list` 18 → **9**。`width` 等ほかの引数は変えない。
- 各行に短いコメント: 「既定の行数（12 / 18）の半分。フル表示のウィンドウの最小の高さの基準（表示される行数は伸びた分で決まる）」の趣旨。

### `keyseq/presentation/controllers/pane_layout/pane_measure.py`

- `measure_window_min_height(app: App) -> int` を追加: `app.update_idletasks()` の後の `app.winfo_reqheight()` を返す（暫定 §3-2）。
  呼び出し側が `paneconfigure` 後に呼ぶ前提（docstring に明記）。一時メッセージの扱いは入れない（task_02）。

### `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py`

- `__init__` に `self.window_min_height: int = 1` を追加。
- `apply_layout`（暫定 §3-4）:
  - 既存の `app.minsize(plan.window_min_width, 1)` の高さを `self.window_min_height` に（それまでに保持している値）。
  - 幅を変える `app.geometry(...)` の高さを `max(app.winfo_height(), self.window_min_height)` に。
  - 末尾の 3 つの `paneconfigure` の**後**に `self.window_min_height = measure_window_min_height(app)` を測り、
    `app.minsize(plan.window_min_width, self.window_min_height)` を当て直す（高さが最小未満なら Tk が広げる。`geometry` は追加しない）。
- `_update_window_min_size`（ドラッグ後）: `minsize(..., 1)` の高さを `self.window_min_height` に。
- `release_window_min_size`（`minsize(1, 1)`）・`_measure`・`on_font_changed`・`on_full_view_shown`・保存系（`_on_window_configure` 等）は**変えない**。

### `tests_ui/test_full_view_min_height.py`（新規）

`tests_ui/test_pane_drag_and_window_min.py:12-114` の構成を手本にする（クラス単位で `StartupIo.write_startup` / `ConfigService.save_startup` / `load_startup` をパッチ・
setUp で geometry / フォント / minsize / `desired` / `min_widths` / **`window_min_height`** を退避し `_restore` で戻す・**実 `config/config.json` を書かない**）。テスト:

1. **最小の高さまで縮めても切れない**（暫定 §5-1）: フォント −3 / 0 / ＋3 それぞれで `_apply_font_delta` → `app.geometry(f"{幅}x1")` → `update()` した状態で
   - `app.winfo_height() == layout.window_min_height` かつ `app.wm_minsize()[1] == layout.window_min_height`
   - `app.pack_slaves()` の各部品（`outer`・ステータス欄・ステータスバー）が `winfo_ismapped()` で、`winfo_y() + winfo_height() <= app.winfo_height()`
   - 3 枠（`full_view.keymap_box` / `trigger_box` / `sequence_box`）の直下の子（`winfo_children()` のうち pack されたもの）の下端 `winfo_y() + winfo_height() <= 枠の winfo_height()`
   - 各一覧の `winfo_height() >= winfo_reqheight()`（`height` が 6 / 9 のため要求高さ = 半分の行数分）
   - ヘッダ（`full_view.header_area`）の `winfo_height() >= winfo_reqheight()`
2. **フォント拡大で最小の高さが上がり、戻すと下がる**（暫定 §5-2 の前半・§5-5）: ＋3 で上がる / 0 へ戻すと下がる。`wm_minsize()[1]` も追従。
3. **最小未満なら広がり、最小以上なら変わらない**（暫定 §5-5）: 高さを最小ちょうどにしてから＋3 → `winfo_height()` が新しい最小に広がる。
   十分高い高さ（最小 + 200）で＋3 にしても（新しい最小を下回らない範囲で）高さは変わらない。
4. **ドラッグ後も高さの制約が保たれる**（暫定 §5-3）: 幅を広げてから境界線をドラッグ（手本 `_drag`）した後、`wm_minsize()[1] == layout.window_min_height`（> 解除値の高さ）。
5. **省略表示で高さも解除され、戻ると再び当たる**（暫定 §5-4 の前半。往復の測定の揺れは task_02）: `show_compact_view()` 後 `wm_minsize()` が解除値（手本の `_probe_released_minsize`）/
   `show_full_view()` 後 `wm_minsize()[1] == layout.window_min_height`。
6. **高さは保存されない**（暫定 §5-6）: `write_startup` のパッチの呼び出し引数に高さのキーが無い（各テストの操作中の呼び出しを集めて、`full_view_pane_widths` / `full_view_window_width` / `ui_font_delta_pt` 以外のキーが無い）。
   幅を変えず高さだけ変えて 500ms 以上待っても（`after` を `update` で流す）`full_view_window_width` の書き込みが起きない。

### 設計メモ / 制約

- **測る順序**: `tk.PanedWindow` の要求高さは `paneconfigure` まで古い値のまま（暫定 §1 実測）。必ず `paneconfigure` の後に測る。
- **最小の高さは測定値そのもの**。追加の余白・行の高さの計算・純関数の新規ファイルは作らない（暫定 §3-2・§3-6）。
- **画面の高さで打ち切らない**（暫定 §2-6）。
- `geometry` を新たに増やさない（高さの拡大は `minsize` に任せる。暫定 §3-4）。
- 820 での見た目（一覧の実高さ）が現状と同じになる想定（暫定 §3-2 実測）。本タスクでは既存テストの期待値を変えない。既存テストが落ちたら**期待値を弱めず**原因を報告する。

## 読むファイル

1. `instructions/history/18_full_view_min_height.md` §2・§3・§5
2. `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py`（全体・編集対象）
3. `keyseq/presentation/controllers/pane_layout/pane_measure.py`（全体・編集対象）
4. `keyseq/presentation/views/full_view/keymap_box.py` / `trigger_box.py` / `sequence_box.py`（`Listbox(` の行のみ編集）
5. `keyseq/presentation/views/status_bar.py:4-12`（root 直下の pack 部品）/ `keyseq/presentation/app.py` の `_build_ui`・`show_compact_view`・`show_full_view`・`_apply_font_delta`（`rg -n` で位置特定）
6. 手本: `tests_ui/test_pane_drag_and_window_min.py:12-122`（setUp / 退避と復元 / `_drag` / 解除値の実測）

## 含まない

- 一時メッセージを 1 行分として測る / `show_full_view` の `update_status` を測定より前へ移す / 暫定 §5-2 後半・§5-4 の往復時の測定値一致（**task_02**）。
- 統合確認（`tests` / `tests_ui` 全体・`smoke_app`）・二次レビュー・実機目視（**task_03**）。
- `features.md` §4.6 / `codebase_map.md` の更新・暫定仕様の凍結（**task_04**）。
- 省略表示の一覧の行数・高さの保存・初期高さ 820 の変更（スコープ外・暫定 §6）。

## 確認

実行は `verifier`（Codex は python を実行しない）。python は `..\..\..\.venv\Scripts\python.exe`。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests_ui.test_full_view_min_height -v` の 6 項目が pass。
3. 関連既存テストが pass: `tests_ui.test_pane_drag_and_window_min` / `tests_ui.test_full_view_header_width` / `tests_ui.test_full_view_panes` /
   `tests_ui.test_pane_widths_persistence` / `tests_ui.test_pane_window_width_persistence`。
4. `-m unittest discover -s tests` が全 pass（変化なしの確認）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は **task_03** でまとめて実施。
