# task_02_paned_full_view

## 目的

フル表示のメイン領域を **`tk.PanedWindow`** に載せ替え、**ウィンドウ幅の変更をトリガー一覧だけが受ける**構成にし、
**一覧を枠に合わせて横に広げる**。あわせて**幅コントローラの骨格**を作り、**最小幅の実測**（暫定仕様 16 §3-4）と
**既定幅の初回適用**（§3-6）を行って、**既定幅での配置を変更前と一致**させる。
根拠: 暫定仕様 16（v0.3）§2-1・§2-4・§2-5・§2-10 / §3-1 / §3-3 / §3-4（最小幅の算出のみ）/ §3-6（既定幅のみ）。

**presentation 限定。task_01 の `pane_width_rules.py` を使う。保存・ドラッグ制御・`wm minsize`・フォント変更 /
省略表示との結線は入れない（task_03・04）。スキーマ不変。**

## 対象範囲（presentation 限定・新規 1 + 変更 4 + テスト新規 1）

### 1. `keyseq/presentation/views/full_view/full_view.py`

- `main_area` の中に **`tk.PanedWindow(orient="horizontal")`** を作り（属性名 `self.panes`）、
  `KeymapBox` / `FullTriggerBox` / `SequenceBox` を**その PanedWindow を親として生成**し、この順に `add` する。
  従来の `pack(side="left", ...)` と `padx=(12, 0)` は削除する。
- `paneconfigure`: **KeymapBox・SequenceBox は `stretch="never"`、FullTriggerBox は `stretch="always"`**。
- **境界線 1 本の占有幅を 12px**（`sashwidth` + `sashpad` × 2 = 12。旧 `padx=12` の置き換え・§3-6）。
  `showhandle=False`、`sashrelief` は目立ちすぎない値（例 `"flat"` か `"raised"`）、**背景色は ttk テーマの背景**
  （`ttk.Style().lookup(".", "background")`。取得できなければ既定のまま）に合わせる。
- `PanedWindow` 自体は `main_area` いっぱいに `pack(fill="both", expand=True)`。
- **`self.keymap_box` / `self.trigger_box` / `self.sequence_box` / `self.action_list` の属性名と参照経路は変えない**
  （`keymap_panel_controller.py:36-57` / `trigger_panel_controller.py:226-242` / `tests_ui` が使う）。
- FullView には**幅の計算・測定を書かない**（生成と配置のみ・§3-1）。

### 2. `keyseq/presentation/views/full_view/keymap_box.py` / `trigger_box.py`（§3-3）

- 一覧の親フレーム（`keymap_list_frame` / `tl_frame`）と一覧（`keymap_listbox` / `trigger_list`）を
  **`fill="both", expand=True`** にする。**`width=26` / `height=12` は残す**（既定幅の要求幅と高さのため）。
- ボタン群・suppress チェック等、他の部品は変えない。
- **詰める順序の補正（task_02 実装時に追加）**: `pack` は先に詰めた部品へ要求幅を優先して配るため、
  一覧を先に詰めていると最小幅でスクロールバー・ボタン列が削られる。**見た目の並び（一覧 | スクロールバー | ボタン列）は変えずに**、
  **スクロールバー（と SequenceBox のボタン列）を `side="right"` で一覧より先に詰める**。
  対象は `keymap_box.py` / `trigger_box.py` の一覧行と **`sequence_box.py`**（**変更は詰める順序と `side` だけ**。
  部品・`width`・`padx`・結線は変えない）。

### 3. `keyseq/presentation/controllers/pane_layout_controller.py`（新規）

`PaneLayoutController(app)`。本タスクでは次の 2 つだけを持つ（task_03・04 で拡張する）:

- `measure_min_widths() -> MinWidths` — §3-4 の式で 3 枠の最小幅を**実測値から**算出する（`pane_width_rules` の
  `list_row_width` / `stacked_min_width` / `side_by_side_min_width` を使う）。
  - 文字幅 = 一覧のフォントで `tkfont.Font(font=listbox.cget("font")).measure("0")`。
  - `list_chrome` = `listbox.winfo_reqwidth() − 文字幅 × int(listbox.cget("width"))`（SequenceBox の一覧は `width` 未指定 = 既定値を `cget` で読む）。
  - スクロールバー幅 = `winfo_reqwidth()`。縦並びの「他の子」= 一覧行以外の子の `winfo_reqwidth()`
    （KeymapBox: ボタン群 / FullTriggerBox: ボタン群・suppress チェック）。横並びのボタン列 = SequenceBox のボタン列フレームと `padx`。
  - `frame_chrome` = LabelFrame の左右 `padding` + 左右の枠線。`title_width` = 見出し文字列の幅（`TkDefaultFont` で measure）+ `frame_chrome` + 見出しの左右インセット。
    **取得方法は実装で決めてよいが、確認 5 のテストを満たすこと**。
  - 一覧の `width` を**一時的に書き換えて測らない**。子ウィジェットの参照が必要なら、Box 側に**属性を公開する**
    （例 `KeymapBox.keymap_buttons`。既存属性名は変えない）。
- `apply_default_widths()` — **PanedWindow の最初の `<Configure>`（幅 > 1）で 1 回だけ**呼ばれ、
  `default_pane_widths(main_width=panes.winfo_width(), keymap_req=keymap_box.winfo_reqwidth(),
  trigger_req=trigger_box.winfo_reqwidth(), sash_total=24, mins=measure_min_widths())` の結果を
  **`paneconfigure(box, width=...)`** で KeymapBox / SequenceBox に当てる。あわせて 3 枠の `paneconfigure(minsize=...)` に最小幅を設定する。
  - 結線（`<Configure>` の 1 回限りのバインド）はコントローラ側で行う（`install()` 等）。**`add="+"` で結線**し、1 回適用後は何もしない。
  - `sash_total` の 24 は定数として `full_view.py` の境界線幅と**同じ定義元**から取る（直値の重複禁止）。
    **定義元は `pane_width_rules.py` に `SASH_WIDTH = 12` を追加**し、`full_view.py` とコントローラの両方がそこから import する
    （**コントローラが View モジュールから定数を import しない**。task_01 のモジュールへの追加はこの定数 1 つだけ許可）。

### 4. `keyseq/presentation/app.py`

- `self.pane_layout = PaneLayoutController(self)` を他のコントローラと同じ並びで生成し、
  `_build_ui()` の後で **結線を 1 回だけ**行う（`self.pane_layout.install()` 相当）。**既存の初期化順序は変えない**。

### 5. `tests_ui/test_full_view_panes.py`（新規）

前例: `tests_ui/test_app_ui_flows.py` の `setUpClass`（`App()` を共有・`tearDownClass` で `update()` → `destroy()`）。
**config を書く操作はしない。** 最低限:

1. **構造**: `full_view.panes` が `tk.PanedWindow`、`panes()` の並びが keymap / trigger / sequence、
   `stretch` が never / always / never、境界線 1 本の占有幅が 12。
2. **既定配置が変更前と一致**（§2-10）: `app.update()` 後、
   `keymap_box.winfo_width() == keymap_box.winfo_reqwidth()` /
   `trigger_box.winfo_x() == keymap_box.winfo_x() + keymap_box.winfo_width() + 12` /
   `trigger_box.winfo_width() == trigger_box.winfo_reqwidth()` /
   `sequence_box.winfo_x() == trigger_box.winfo_x() + trigger_box.winfo_width() + 12` /
   `sequence_box` の右端 == `panes.winfo_width()`。
   （初期ウィンドウ幅 780 でメイン領域が 3 枠の要求幅合計以上ある前提。満たさない場合はテストが理由付きで失敗すること）
3. **ウィンドウ幅の変更でトリガー一覧だけ変わる**（§2-1）: 幅を +120px / −40px（最小幅を割らない範囲）へ変えて `update()` し、
   KeymapBox・SequenceBox の幅が変わらず、トリガー一覧の幅だけが同じ量変わる。**テスト後に元の geometry へ戻す**。
4. **一覧が枠に合わせて広がる**（§2-4）: トリガー一覧を広げたとき `trigger_list.winfo_width()` も広がる。
   KeymapBox は `paneconfigure(width=)` で広げて `keymap_listbox.winfo_width()` が広がる（**後で元の幅に戻す**）。
5. **最小幅で中身が切れない**（§2-5・§3-4・v0.3）: 各枠を `paneconfigure(width=最小幅)` にして `update()` し、
   ボタン・チェックボックス・間隔入力等の子ウィジェットがすべて `winfo_width() >= winfo_reqwidth()`、
   一覧が 10 文字分以上（`winfo_width() >= 文字幅 × 10`）。**フォント delta −2 / 0 / +2 で繰り返す**
   （`app._apply_font_delta` を使い、**`startup_io.write_startup` は patch して config を書かない**。テスト後に元の delta へ戻す）。
   ※ task_02 ではフォント変更後の最小幅の自動再計算は無いので、テスト内で `measure_min_widths()` を再度呼んで使う。
6. `full_view.action_list is full_view.sequence_box.action_list`（既存 alias の維持）。

## 設計メモ / 制約

- **`PanedWindow` の標準のサッシュドラッグは本タスクでは制限しない**（押し出しの防止・中ボタン無効は task_03）。
- ヘッダ領域（hook / display / file）は変更しない。CompactView は変更しない。
- `measure_min_widths` の各測定は **`update_idletasks()` 後**に行う（要求幅が確定していないと 1 が返る）。
- `pane_width_rules.py` は `SASH_WIDTH` の追加以外は変更しない（不足があれば実装せず報告）。
- 関数はおおむね 30 行以内。コントローラが 150 行を超えそうなら報告。

## 含まない

- サッシュのドラッグ制御（可動範囲・中ボタン無効・離したときの処理）/ `wm minsize` / `resolve_layout` の適用 /
  フォント変更後の再計算 / 省略表示との切替順（**task_03**）
- 希望幅の保持・`write_startup` による保存・起動時の保存値の復元（**task_04**）
- 正本 / `codebase_map.md` の更新（**task_06**）

## 確認

python は `../../../.venv/Scripts/python.exe`。実測は `verifier`。

1. `python -m compileall -q keyseq main.py tests tests_ui` が clean。
2. `python -m unittest tests_ui.test_full_view_panes -v` が全 pass（上記 1〜6 が存在）。
3. `python -m unittest discover -s tests` が 441 実行 OK（skip 7）のまま。
4. `python -m unittest discover -s tests_ui` が全 pass（**既存 351 + 追加**。既存アサーションを変更していないこと）。
5. `python -m tests.smoke_app` が SMOKE OK。
6. `git diff --stat` が対象範囲のファイルのみ。`config/` 配下に差分・新規ファイルが無い（`git status --short config`）。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- 実機目視は **task_05 でまとめて実施**（本タスクでは行わない）。
