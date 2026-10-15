# task_03_full_view_scroll_areas

## 目的

フル表示の 3 枠（KeymapBox・FullTriggerBox・SequenceBox）の `LabelFrame` の内側の中身を、共通の縦スクロール領域（Canvas + 中身の Frame + 縦の Scrollbar）へ入れる（暫定 42 §3.1・§3.3 の測り方・§3.4）。
**このタスクでは最小の幅・高さの値を変えない**: Canvas の要求高さ・幅を中身の Frame の要求高さ・幅に合わせ、既存の最小の高さ・幅のテストが書き換えなしで通ることを完了条件にする（値の変更は task_04）。
**presentation 限定（views/full_view・controllers/pane_layout）・domain / application 不変・JSON スキーマ不変。**

## 対象範囲（presentation・フル表示の 3 枠 + 最小幅の測り方 + テスト）

### 新規 `keyseq/presentation/views/full_view/scroll_area.py`

- `VerticalScrollArea(ttk.Frame)`（3 枠で共通の部品 1 つ）。`self.canvas`（`highlightthickness=0`・`borderwidth=0`）・`self.content`（Canvas の中の `ttk.Frame`・`create_window(anchor="nw")`）・`self.scrollbar`（縦・grid で右列・初期は `grid_remove`）
- **作法は `screen_grid/grid_editor_panel.py:35-49,131-197` を踏襲**: 値が変わったときだけ `configure`・測り直しの結び付けは中身の Frame 1 つの `<Configure>`（`add="+"`）・再入防止の印・`after_idle` の予約は 1 つ・
  測る前に `content.update_idletasks()`・スクロールバーの表示は自前の印（`scrollbar_shown`）・破棄後の予約は何もしない（`winfo_exists()`）
- 要求の大きさ: Canvas の要求高さ = 中身の要求高さ・要求幅 = 中身の要求幅（**今の枠の要求の大きさと同じになるように**。task_04 で変える）
- **中身の窓の高さ = max(Canvas の実際の高さ, 中身の要求高さ)**・幅 = Canvas の実際の幅（`itemconfigure(window, width=, height=)`。値が変わったときだけ）。Canvas の方が高ければ中身が伸びて一覧が余りを使う（今と同じ）
- スクロールバー: 中身の要求高さ > Canvas の実際の高さ のときだけ出す。**隠すときは `canvas.yview_moveto(0)`**。`scrollregion` を中身の窓の大きさに合わせる
- 測り直しの契機: Canvas の `<Configure>`・中身の Frame の `<Configure>`・`<<ThemeChanged>>`・公開メソッド `sync()`（その場で同期して測る。`pane_layout` が測る前に呼ぶ）
- マウスホイール（§3.4）: 公開メソッド `bind_wheel(skip: Iterable[tk.Widget])` で、中身の Frame とその子孫・Canvas・scroll area 自身に `<MouseWheel>` を結び付ける。
  `skip` に渡した部品（一覧の Listbox とその Scrollbar）の上では結び付けない（Tk の既定の動きに任せる）。
  それ以外の上では、スクロールバーが出ているときだけ `yview_scroll` し、**出ていてもいなくても `"break"`**（間隔の入力欄等の値を変えない）。`bind_all` は使わない
- 300 行以内を目安

### `keyseq/presentation/views/full_view/keymap_box.py`・`trigger_box.py`・`sequence_box.py`

- 各枠の先頭で `self.scroll_area = VerticalScrollArea(self)` を `pack(fill="both", expand=True)` し、今 `self` に置いている子（一覧の Frame・ボタン列・`suppress_chk`・`action_column`・`abtns`）の親を `self.scroll_area.content` に替える。並び・pack の引数は変えない
- 末尾で `self.scroll_area.bind_wheel(skip=(一覧, 一覧の Scrollbar))`。SequenceBox は `action_list` とその Scrollbar に加え、呼び出し先の一覧（`call_view_frame.action_list`・`call_view_frame.scrollbar`）も skip に含める
- 外から参照される属性（`keymap_listbox`・`trigger_list`・`action_list`・`suppress_chk`・`run_to_end_chk`・`run_to_end_delay_entry`・`action_column`・`action_panes`・`call_view_frame` 等）の名前は変えない

### `keyseq/presentation/controllers/pane_layout/pane_measure.py`

- `_stacked_width`（:68-74）: 枠直下の子ではなく **`box.scroll_area.content` の子**から、一覧の Frame を除いた要求幅を取る（§3.3）。式（`stacked_min_width`）は変えない
- `measure_min_widths`: 出力シーケンスの横並び（`buttons.pack_info()` の padx 等）は中身の Frame 側にあるため式は変えずに動くことを確かめる。`_frame_widths` は枠（LabelFrame）のまま
- `measure_min_widths` と `measure_window_min_height` の先頭で 3 枠の `scroll_area.sync()` を呼ぶ（古い値で測らない・§3.1）

### テスト

- 新規 `tests_ui/test_full_view_scroll_areas.py`（App はクラスで共有・作法 = `tests_ui/test_full_view_min_height.py` の setUp / `_set_font` / `_set_height`）:
  1. 既定の大きさと最小の高さのとき、3 枠ともスクロールバーが出ず、中身の窓の高さ ≥ 中身の要求高さ（今と同じ見た目）
  2. 最小の高さ・幅が scroll area の導入前と同じ値になっていること（Canvas の要求高さ = 中身の要求高さ・要求幅 = 中身の要求幅を各枠で確かめる）
  3. `app.minsize(1, 1)` で最小より低くすると、収まらない枠にだけスクロールバーが出て、`yview_moveto(1)` で中身の最下段（キーマップ管理・トリガー一覧 = 最後のボタン / suppress、出力シーケンス = 間隔欄・確認して実行）が Canvas の見える範囲に入る
  4. 高さを戻すとスクロールバーが隠れ、`canvas.yview()[0] == 0`（先頭へ戻る）
  5. ホイール: スクロールバーが出ているとき、ボタン・中身の Frame の上の `<MouseWheel>` で枠がスクロールし、一覧の上では枠がスクロールしない。間隔欄の上のホイールで `run_to_end_delay_var` が変わらない。出ていないときは枠が動かない
  6. 測り直しで `<Configure>` が回り続けない（一定時間 `update()` を回しても測る回数が増え続けない等）
  7. フォント −3 / +3 の変更後もテスト 1・2 が成り立つ
  - 各テストは `addCleanup` でフォント・ウィンドウの大きさ・`minsize` を元へ戻す

### 設計メモ / 制約

- 最小の高さ / 幅の**値は変えない**（`pane_measure.measure_window_min_height` の式・`pane_width_rules.py` は不変。スクロールバーの幅の加算は task_04）
- `tests_ui/test_full_view_min_height.py`・`test_full_view_panes.py`・`test_full_view_header_width.py`・`test_pane_drag_and_window_min.py` は**書き換えない**（通らなければ実装側を直す）。
  例外（2026-10-15 追記・構造の変化による）: `test_full_view_panes.py` の `_assert_children_fit` は、一覧の Frame と同じく scroll area・その Canvas・中身の Frame（要求幅に 26 文字の一覧を含む中継の容器）を幅の比較から外し、子への再帰は続ける（期待値は変えない）
- 呼び出し先の枠の開閉（`action_column` の中）は中身の Frame の `<Configure>` で測り直される。`call_view_controller` は変えない
- 上部（フック・表示・ファイル）・ステータス欄・省略表示は変えない

## 読むファイル

1. `instructions/history/42_window_size_fit.md` §3.1・§3.3・§3.4
2. `keyseq/presentation/views/full_view/keymap_box.py`・`trigger_box.py`・`sequence_box.py`・`full_view.py`（全体）
3. `keyseq/presentation/views/full_view/call_view_frame.py:9-38`（呼び出し先の一覧と Scrollbar）
4. `keyseq/presentation/screen_grid/grid_editor_panel.py:17-49,131-201`（スクロール領域の手本）
5. `keyseq/presentation/controllers/pane_layout/pane_measure.py`（全体）
6. `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py:74-148`（測る契機）
7. `tests_ui/test_full_view_min_height.py:1-80,157-185`（テストの作法と既存の期待）

## 含まない

- 最小の高さを下げる（H の測り方・ceil(H/2)）・各枠の最小幅へのスクロールバーの幅の加算（task_04）
- 既存の最小の高さ / 幅のテストの書き換え（task_04）
- 正本 `features.md` §4.6・`codebase_map.md` の更新（task_06）
- 横スクロール・スクロール位置の保存・Tab の自動スクロール（暫定 42 §10）

## 確認

（実行は verifier・`.venv` python）
- `compileall -q keyseq main.py tests tests_ui` clean
- `tests_ui/test_full_view_scroll_areas.py` pass（上記 1〜7）
- `tests_ui/test_full_view_min_height.py`・`test_full_view_panes.py`・`test_full_view_header_width.py`・`test_pane_drag_and_window_min.py`・`test_call_view_frame.py` が**書き換えなしで** pass
- `unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` 全 pass（件数が減っていない）
- 実行後に `config/config.json` の mtime が変わっていない

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_04 でまとめて実施（本タスクは値を変えないため）
