# task_11_save_dialog_flex_layout

## 目的

task_09 で入れた一覧ダイアログのレイアウトが、実機目視（2026-07-30）で 2 点足りなかったので直す
（暫定仕様 05 **v0.4-C 追記** / §3-5・受入条件 **14b**）。

- **①右端のラジオ列が見えなくなることがある** → 対象名・保存先パスを**ダイアログ幅に追随する可変列**にし、
  幅が足りないときは可変列を詰めて**ラジオ列の完全表示を優先**する。
- **②縦を詰めると OK / キャンセルが消える** → ボタン行を**縮小時も押し出されない**レイアウト順にし、
  **最小サイズでも 5 列とボタンが見える**ようにする。

レイヤ制約: **presentation 限定**（`config_io/child_save_dialog.py` のみ）。
**application / domain 不変・スキーマ不変**。行モデル（`ChildSaveRow`）と `child_save_rows.py` の判定は
**変更しない**（表示の見せ方だけを変える）。**選択の意味・保存計画・A2 の判定条件は一切変えない**
（task_08 の挙動を維持する）。

## 対象範囲（`config_io/child_save_dialog.py` 限定）

### 1. ボタン行を常時表示にする

`_create_action_dialog` の pack 順を変える。現行は一覧（`list_frame`）→ ボタン（`buttons`）の順に pack して
いるため、縦を詰めると**後から pack したボタン行が押し出されて消える**。

- `buttons` を **`side="bottom"`（+ `anchor="e"`）で先に pack** し、そのあとに
  `list_frame` を `fill="both", expand=True` で pack する（スクロール領域の外である点は task_09 のまま）。
- ボタン行は縮小時に削られない側（`expand=False`）であること。

### 2. 一覧を可変列にする

`list_frame` / `content_frame` を次の構成にする。

| 列 | 内容 | weight | 備考 |
|---|---|---|---|
| 0 | 種別 | 0 | 固定 |
| 1 | 対象名 | 1 | **可変**・`minsize` を設定 |
| 2 | 保存先パス | 2 | **可変**・`minsize` を設定 |
| 3 | 共有状況 | 0 | 固定 |
| 4 | 操作（ラジオ） | 0 | 固定・**切らさない** |

- 内側フレーム（`content_frame`）の幅を **Canvas の幅へ追随**させる。
  `canvas.create_window(...)` の戻り id を保持し、Canvas の `<Configure>` で
  `canvas.itemconfigure(window_id, width=event.width)` を呼ぶ。
- 可変列のラベルは **`width=1`（文字）+ `anchor="w"` + `sticky="ew"`** で作る。
  こうしないとラベルのテキスト幅が列の要求幅を押し上げ、幅追随と省略が相互に干渉する
  （テキストを変えても要求幅が動かない状態にしてから、3 の省略で見せる）。
- ヘッダ行も同じ列構成・同じ weight にそろえる（見出しと値がずれないこと）。
- **横スクロールバーは持たない**（task_09 のまま）。

### 3. 省略幅を実際の列幅から決める

task_09 の固定文字数（対象名 24 / パス 56）をやめ、**割り当てられた幅（px）に収まる長さ**で省略する。

- 純関数を 1 本追加する（モジュール関数・`_ellipsize` と同じ場所）:
  `_fit_text(text: str, measure, max_px: int, ellipsize) -> str`
  - `measure: Callable[[str], int]`（文字列の描画幅を返す。実行時は `tkinter.font.Font.measure`）
  - `ellipsize: Callable[[str, int], str]`（既存の `_ellipsize` / `_ellipsize_path` をそのまま渡す）
  - `measure(text) <= max_px` ならそのまま返す。超えるなら**文字数を二分探索**して
    `measure(ellipsize(text, n)) <= max_px` を満たす最大の `n` の結果を返す。
    `max_px` が極端に小さく候補が無い場合は `"…"` を返す（例外は投げない）。
- **既存の `_ellipsize`（末尾省略）/ `_ellipsize_path`（中央省略）は変更しない**（`_fit_text` から再利用する）。
- 適用: 対象名 = `_ellipsize`、保存先パス = `_ellipsize_path` を渡す。
- 再省略のタイミング: Canvas の `<Configure>`（幅変更時）。**同じ幅で再入したら何もしない**
  （直前に適用した幅を保持して比較。テキスト更新 → `<Configure>` の無限ループを防ぐ）。
- **種別・共有状況・ラジオは省略しない**（判断に直結するため。task_09 のまま）。

### 4. ツールチップを動的省略に合わせる

- 対象名・保存先パスのセルには**常にツールチップをバインド**し、**表示するのは現在省略されているときだけ**にする
  （省略が解けている幅では表示しない）。全文の取得元は `ChildSaveRow` の**元の値**（省略前）。
- `_bind_tooltip` の Toplevel 生成・破棄・例外の握り（task_09）はそのまま流用する。

### 5. 最小サイズを要求幅から決める

- 初期サイズ `960x480` は維持する。
- **`minsize` は実測で決める**: 行を組んだ直後に `dialog.update_idletasks()` し、
  「固定列の要求幅 + 可変列の `minsize` + スクロールバー幅 + padding」を満たす幅を求めて
  `dialog.minsize(required_width, required_height)` を呼ぶ（`required_height` は
  ヘッダ 1 行 + 一覧 1 行 + ボタン行が収まる高さ）。**px 定数を決め打ちしない**（DPI / フォント差で崩れる）。
- 下限として task_09 の `720 x 320` を下回らせない（`max(720, required_width)` の形）。

### 6. テスト（`tests_ui/test_child_save_dialog.py`）

**構造テスト**（既存の fake widget を patch する手法を踏襲。`_FakeDialogWidget` 等を新 API へ拡張）:

| # | 内容 |
|---|---|
| 1 | ボタン行が `side="bottom"` で **`list_frame` より先に** pack され、`expand=True` を渡していない |
| 2 | 可変列（1・2）に `weight >= 1` と `minsize` が設定され、固定列（0・3・4）は `weight=0` |
| 3 | Canvas の `<Configure>` バインドがあり、発火させると `itemconfigure(window_id, width=...)` が呼ばれる |
| 4 | `<Configure>` を**同じ幅で 2 回**発火させても再省略が 1 回しか走らない（再入防止） |
| 5 | `minsize` が `update_idletasks` の後に呼ばれ、引数が要求幅（fake の返す値）以上 |
| 6 | ツールチップは**省略中のセルだけ全文を表示**する（省略が解けている幅では表示しない）。※ task_09 のテスト 3（省略セルにだけ `_bind_tooltip` する）は、**バインド常時 + 表示条件**の形へ**等価に書き換える**（アサーションを緩めない） |

**純関数テスト**（同ファイル内・tkinter 非依存。`measure` は「1 文字 = 10px」等の fake を渡す）:

| # | 内容 |
|---|---|
| 7 | `_fit_text` — 収まる文字列はそのまま返る |
| 8 | `_fit_text` — 収まらない文字列は省略され、`measure(結果) <= max_px` を満たす（末尾省略・中央省略の両方） |
| 9 | `_fit_text` — `max_px` が 1 文字も入らない値でも例外にならず `"…"` を返す |

**実描画テスト 1 本**（受入条件 14b の境界判定。`tk.Tk()` が作れない環境は `skipTest`）:

| # | 内容 |
|---|---|
| 10 | 実 Tk でダイアログを作り最小サイズへ縮めた状態で `update_idletasks()` し、①ボタン行の `winfo_y + winfo_height <= ダイアログ高さ` ②ラジオ列の `winfo_x + winfo_width <= スクロール領域幅` ③幅を広げると可変列（対象名・保存先パス）の `winfo_width` が増える — を検証する |

### 設計メモ / 制約

- **選択・保存計画に関わるコードへ触らない**。`_confirm_actions` / `_resolve_action_targets` /
  `confirm_trigger_set_dependency` / `confirm_recalculated_overwrite` のロジックは無変更。
- `ChildSaveRow.target_path` / `display_name` の**値そのものは変えない**。省略は表示時の変換のみで、
  `_ask_save_as_path` の `initialdir` / `initialfile` は**全文**を使う（task_09 の不変条件）。
- 依存確認 / 再計算先確認は `messagebox` ベースのまま（**本タスクの対象外**。v0.4-D/E の 4 択化は task_12）。
- `child_save_dialog.py` は現在 252 行。本タスクの追加で 300 行の目安を超える見込みなら、
  **本タスクでは分割せず**フェーズ末の `/refactor_check` の判定へ回す（task 途中で構造を変えない）。
- ツールチップは `_app.hook` に触らない（`ask_child_save_actions` が既にフックを停止済み）。

## 含まない

- **依存確認ダイアログの 4 択化・提示条件の縮小（v0.4-D/E）— task_12**。
- **`data` 置換時の trigger_set 状態リセット（v0.4-H）— task_13**。
- **正本 `spec_detail/` への反映 — task_10**。
- 行モデル・共有状況の判定（`child_save_rows.py`）の変更。列の追加・削除・並べ替え。
- 一覧の並び順・グルーピング・フィルタ・全選択などの新機能（暫定仕様 §3-2 の列構成から増やさない）。
- 個別保存ボタンの統合（暫定仕様 §11）/ ダイアログの共通化・部品化。

## 確認

`.venv` の python で実行する（worktree ルートから `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests_ui` が clean
2. `-m unittest discover -s tests` が全 pass（現行 136 件）
3. `-m unittest discover -s tests_ui` が全 pass（現行 116 件 + 追加分）
4. `-m tests.smoke_app` が pass
5. **受入条件 14b（構造・実描画）**: 上記テスト 1〜10 が pass（10 は実 Tk が無ければ skip でよい）
6. **受入条件 14（目視・ユーザー実施。本タスクでは実施しない）**:
   dirty な子 12 行以上・対象名 40 文字・保存先パス 160 文字の状態でダイアログを開き、
   ①最小サイズまで縦横を詰めても OK / キャンセルとラジオが見える ②幅を変えると対象名・パスの省略量が変わる
   ③縦スクロールで全行に到達できる ④省略部にカーソルを合わせると全文がツールチップで見える
7. 既存の特性テスト（保存 JSON のバイト列比較）を**緩めずに** pass すること

## 完了条件

- 上記確認 1〜5・7 が pass・**reviewer 採用**。
- 実機目視（確認 6）は **task_10 の前にユーザーがまとめて実施**する。本タスクでは実施しない。
