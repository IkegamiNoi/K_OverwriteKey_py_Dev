# task_06_call_view_compact

## 目的

省略表示にも呼び出し先の表示枠（常設の Expander）を置く（暫定 31 v0.6 §5.1「省略表示」・§5.2「表示の切替」・§6・§10-7・§10-9）。
フル表示の枠（task_05a・task_11 の問い合わせ方式）と**同じ開閉の状態・同じ表示**を、トリガー一覧の下に出す。
**presentation 限定**（`call_view_controller.py`・`compact_view/trigger_box.py`・`app.py` の表示切替・`trigger_panel_controller.py` の選択の通知）。application・JSON の形・runner は変えない。

## 対象範囲（presentation 限定）

### `keyseq/presentation/views/compact_view/trigger_box.py`

- トリガー一覧（`tl_frame` = 一覧 + スクロールバー）を縦の `tk.PanedWindow` の上の枠に入れ、その下に `CallViewFrame`（`views/full_view/call_view_frame.py` をそのまま使う）を置く。
  PanedWindow の見た目（`sashwidth=4`・`sashrelief="flat"`・背景 `#E8E8E8`・`sashpad=0`・`showhandle=False`）はフル表示の `sequence_box.py` と揃える
- 公開する属性: `trigger_panes`（PanedWindow）・`trigger_frame`（上の枠）・`call_view_column`（見出しを閉じた状態で置く親 = PanedWindow を包む Frame）・`call_view_frame`
- 見出しのクリックは `app.call_view.on_heading_click()` へ（フル表示と同じ）
- `trigger_list` の `height=16` は変えない（要求高さの基準）

### `keyseq/presentation/controllers/call_view_controller.py`

- 今はフル表示の `sequence_box` だけを扱っている。**枠の置き場（host）を 2 つ持つ形**に一般化する: host ごとに PanedWindow・上の枠・上の一覧（最小 3 行の基準）・`CallViewFrame`・見出しを閉じて置く親・高さの保存キー（`"full"` / `"compact"`）・ドラッグ中の高さ・レイアウト予約を持つ
  （小さな host クラス〔`_CallViewHost` 等〕を同ファイル内に置く。300 行を超えるなら `controllers/call_view/` へ親ごと分割してよい = `file_organization_rules.md` のフォルダ化）
- **開閉の状態（`_open_by_trigger`・`_manually_operated`）は 1 組のまま両方の host で共有**する（§5.2「表示の切替では同じトリガーの開閉・表示を新しい側の枠に出す」）
- `_render()` は **2 つの host を両方描き直す**（中身・見出し・開閉は同じ。高さは host ごとの保存値）。非表示側の PanedWindow は高さが 1 なので、高さの配置（`_apply_height`）は host が表示されて `<Configure>` で実寸が入ったときに行う（今の `_on_configure` の仕組みを host ごとに）
- `install()`・`on_font_changed()` は両方の host に対して行う。省略表示の上の枠の最小 = トリガー一覧の 3 行（`list_minimum_height(trigger_list)`）
- 境界線のドラッグを離したときの保存は**その host のキーだけ**を `desired` で更新し、今のとおり `desired` 全体（もう片方の今の希望値を含む）を `write_startup` で書く（§6）
- `_ensure_desired()` の `"compact"` の既定は、**開いたときの一覧と枠の合計**の 3 分の 1（今の `trigger_list.winfo_reqheight()` 基準をやめ、フル表示と同じ求め方に揃える。host が未表示〔高さ 1〕の間は既定を決めない）
- **省略表示ではウィンドウの大きさを変えない**: 枠の開閉でトリガー一覧が縮む / 伸びる。一覧と枠の最小を割る高さでは `displayed_call_view_height` のとおり枠を最小で出す

### `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`

- `set_selected_trigger_index` で省略表示のとき（`refresh_actions` を呼ばない分岐）にも `call_view.on_selection_changed()` を呼ぶ（省略表示でトリガーを選び替えたとき枠が追従するように）。`select_trigger_by_key` など他の選択の経路も、省略表示で `refresh_actions` を通らないなら同様に通知する

### `keyseq/presentation/app.py`

- `show_compact_view()` の末尾で `call_view.on_selection_changed()`（または同等の描き直し）を呼ぶ。`show_full_view()` は `refresh_actions()` 経由で通知済みなので変えない
- `_apply_compact_geometry()`（幅 270・高さは現状維持）は変えない

### テスト（追加・修正まで）

- 新規 `tests_ui/test_call_view_compact.py`（`tests_ui/test_call_view_frame.py` の setUpClass / setUp / `summary()` / `notify()` の形を流用。既存ファイルは 441 行なので足さない）:
  - 省略表示へ切り替えた直後は `▸ 呼び出し先` の見出しだけで、境界線（PanedWindow の 2 枚目）が無い
  - 選んでいるトリガーの要約を受けると省略表示の枠が開き、`▶`・経路の見出し・中身がフル表示と同じ
  - フル表示で開いた（または手で閉じた）トリガーは、省略表示へ切り替えても同じ開閉。逆向き（省略表示で見出しをクリック → フル表示へ戻す）も同じ
  - 省略表示でトリガーを選び替えると開閉と中身が追従する（`set_selected_trigger_index` 経由）
  - 省略表示で枠を開閉してもウィンドウの高さ・幅が変わらず、トリガー一覧の高さが変わる
  - 省略表示の境界線のドラッグを離すと `call_view_heights` の `"compact"` だけが変わり、`"full"` は今の希望値のまま一緒に書かれる。フル表示の枠の高さは変わらない
  - 低いウィンドウ高さでも枠は最小（見出し + 3 行）で表示され、トリガー一覧は 3 行を残す
  - 省略表示の枠も読み取り専用（クリック・ダブルクリック・キー入力で何も起きない。1 ケースでよい）
- 既存の `tests_ui/test_call_view_frame.py` はフル表示の確認のまま全 pass させる（controller の一般化に伴う参照の修正は可）

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §5.1・§5.2・§6（v0.6）
- `keyseq/presentation/controllers/call_view_controller.py`（全体）
- `keyseq/presentation/views/full_view/call_view_frame.py`（全体）・`views/full_view/sequence_box.py:20-55`（PanedWindow と枠の組み方の手本）
- `keyseq/presentation/views/compact_view/trigger_box.py`・`compact_view.py`（全体）
- `keyseq/presentation/call_view_heights.py`（全体）
- `keyseq/presentation/app.py:398-445`（表示の切替）
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:82-110`・`:255-285`（選択の変化と `refresh_actions` の通知）
- `tests_ui/test_call_view_frame.py:1-120`（テストの組み方）

## 含まない

- 正本反映・`codebase_map.md`・decisions_archive（task_07）
- 省略表示の枠の横スクロール・省略表示への出力シーケンス欄（暫定 31 §11 スコープ外）
- 開閉の保存・トリガーごとの高さ（スコープ外）
- runner / application の変更（要約の問い合わせ口 `call_view_summary_for` はそのまま使う）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `tests_ui/test_call_view_compact.py`・`tests_ui/test_call_view_frame.py` が全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass（tests_ui は verifier 1 つで）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: ①省略表示でトリガー一覧の下に `▸ 呼び出し先` ②ステップの呼び出しで止まると開き、ウィンドウの大きさは変わらず一覧が縮む ③フル ⇔ 省略の切替で同じトリガーの開閉・表示が保たれる ④境界線の位置がフル表示と別に保たれ再起動後も残る。
