# task_04_full_view_min_size

## 目的

フル表示のウィンドウの最小の高さを「メイン領域の基準の高さ H の半分」まで下げ、3 枠の最小幅に縦のスクロールバーの要求幅を常に足す（暫定 42 §3.2・§3.3・§8-1・§9-1〜4）。
task_03 のスクロール領域があるので、最小より低くしても収まらない枠はスクロールで見せられる。
**presentation 限定（controllers/pane_layout）・domain / application 不変・JSON スキーマ不変。**

## 対象範囲（presentation・最小の高さ / 幅の測り方 + テスト）

### `keyseq/presentation/controllers/pane_layout/pane_measure.py`

- 新規 `measure_main_area_basis_height(app) -> int`: 3 枠それぞれ「枠の飾りの高さ（`box.winfo_reqheight() - box.scroll_area.winfo_reqheight()`）+ `box.scroll_area.content.winfo_reqheight()`」の最大 = H（§3.2。測る前に 3 枠の `sync()`）
- `measure_window_min_height(app)`: 今の値（`app.winfo_reqheight()` − 一時メッセージの余分）から `view.panes.winfo_reqheight()` を引き、`ceil(H / 2)` を足した値を返す（§3.2 の式）。一時メッセージの余分を引く規則はそのまま
- `measure_min_widths(app)`: 3 枠の最小幅（keymap・trigger・sequence）それぞれに **その枠の `scroll_area.scrollbar.winfo_reqwidth()`** を足す（表示の有無に関係なく常に・§3.3）。足す前の式（`stacked_min_width`・`side_by_side_min_width`・`pane_width_rules.py`）は変えない
- ウィンドウの最小幅は今の式（`pane_layout_controller._plan` / `pane_width_rules`）がこの最小幅から求めるので変えない

### `keyseq/presentation/views/full_view/scroll_area.py`

- 変えない（Canvas の要求の高さ・幅 = 中身の要求のまま。既定の大きさ・今の最小以上の見た目を今と同じに保つため）

### テスト

- 既存の最小の高さ・幅の期待（`tests_ui/test_full_view_min_height.py`・`test_full_view_panes.py`・`test_pane_drag_and_window_min.py`・`test_full_view_header_width.py`・`test_pane_widths_persistence.py`・`test_compact_window.py` のうち該当するもの）を本書の式に合わせて書き換える。
  **「最小の高さで何も切れない」系は、新しい最小では枠の中身がスクロール領域で見えることの確認へ置き換える**（期待を緩めて素通りにしない）。書き換えた箇所と理由を報告に列挙する
- 新規 `tests_ui/test_full_view_min_size.py`（作法 = `tests_ui/test_full_view_scroll_areas.py` の setUpClass / `_restore`）。フォント −3 / 0 / +3 の各値で:
  1. `layout.window_min_height == measure_window_min_height(app)` かつ = 今の測り方の値（`app.winfo_reqheight()` − 一時メッセージの余分）− `panes.winfo_reqheight()` + ceil(H/2)。`wm_minsize()[1]` も同じ
  2. 新しい最小の高さ < 今の測り方の値（下がっている）
  3. 最小幅 = 足す前の値 + 各枠のスクロールバーの要求幅（3 枠とも）
  4. ウィンドウを最小幅・新しい最小の高さにしたとき: 収まらない枠にスクロールバーが出て、スクロールバーが枠の内側に収まり（`x + width ≤` 枠の内側の幅）、
     中身の部品（ボタン・チェックボックス・間隔の入力欄）の幅が要求幅以上（横に切れない）。`yview_moveto(1)` で各枠の最下段の部品が Canvas の見える範囲に入る
  5. ウィンドウの高さを今の測り方の値以上にすると 3 枠ともスクロールバーが出ない（§9-1）
- `tests_ui/test_full_view_scroll_areas.py` の補強（task_03 のレビューの参考指摘）: スクロールバーが出ていない枠の上のホイールで枠が動かない / 呼び出し先の一覧（`call_view_frame.action_list`。呼び出し先の枠を開いた状態）の上のホイールで出力シーケンスの枠が動かない / 出力シーケンスの `action_list` の上で枠が動かないことを条件分岐なしで確かめる

### 設計メモ / 制約

- 測る契機・適用（`minsize`・最小より低ければ伸ばす・保存しない）は今の規則のまま（`pane_layout_controller.apply_layout`・`on_font_changed`・`on_full_view_shown`・ドラッグの後）。式だけ変える
- `<<ThemeChanged>>` での測り直しは追加しない（アプリに実行中のテーマ切替が無い。`theme_use` の呼び出しなし）
- 省略表示・上部・ステータス欄は変えない

## 読むファイル

1. `instructions/history/42_window_size_fit.md` §3.2・§3.3
2. `keyseq/presentation/controllers/pane_layout/pane_measure.py`（全体）
3. `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py:74-160`
4. `keyseq/presentation/views/full_view/scroll_area.py`（全体）
5. `keyseq/presentation/pane_width_rules.py:75-125`（最小幅の式）
6. `tests_ui/test_full_view_min_height.py`・`tests_ui/test_full_view_scroll_areas.py`（全体）
7. 書き換えが要る既存テストは `window_min_height` / `measure_min_widths` / `min_widths` を grep して該当箇所だけ読む

## 含まない

- 正本 `features.md` §4.6・`codebase_map.md` の更新（task_06）
- 横スクロール・スクロール位置の保存・Tab の自動スクロール（暫定 42 §10）
- 省略表示の最小の高さ（task_02 で済）

## 確認

（実行は verifier・`.venv` python）
- `compileall -q keyseq main.py tests tests_ui` clean
- `tests_ui/test_full_view_min_size.py`・`test_full_view_scroll_areas.py` pass
- 書き換えた既存テストを含む `unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` 全 pass（件数が減っていない）
- 実行後に `config/` の mtime が変わっていない

## 完了条件

- 上記確認 pass・**reviewer 採用**
- **ユーザーの実機目視**（本タスクで実施・task_03 分を含む）: フォント +3 でフル表示が画面に収まる / 最小幅・最小の高さまで縮めて 3 枠にスクロールバーが出ても切れない /
  スクロールバー・ホイールで最下段まで届き、一覧の上のホイールは一覧をスクロールする / 高さを戻すとスクロールバーが消えて先頭へ戻る
