# task_05b_tk9_screen_distance

## 目的

task_05 の Mac の起動目視で、フル表示が縮んだまま出る・一覧が窓の幅に追従しない・最小サイズが効かない・スクロールバーが出ない、が見つかった（2026-11-11・ユーザー報告）。
原因は Tk 9 で画面上の長さの `cget` が整数でない値を返すこと（probe 実測: Canvas の `width` / `height` の既定値 = `'10c'` / `'7c'`、PanedWindow の `sashwidth` = `'2.25p'`）。`int(...)` が例外になり、大きさを測る処理が毎回途中で止まる。
暫定 57 §4（Tk の差は presentation の 1 か所にまとめる）に従い、長さを `winfo_pixels` でピクセルに直して比べる形へ揃える。

**レイヤ制約**: presentation のみ。domain / application / infrastructure 不変・JSON スキーマ不変。Tk 8.6（Windows）では `winfo_pixels` が同じ値を返すため **Windows の動作不変**。

## 対象範囲（presentation 限定）

### `keyseq/presentation/tk_platform.py`

`screen_distance(widget, option: str) -> int` を追加する: `return int(widget.winfo_pixels(widget.cget(option)))`。docstring に「Tk 9 は長さの既定値を単位つき（`10c`・`2.25p`）で返すため」と書く。

### 置き換え（`int(X.cget("opt"))` → `screen_distance(X, "opt")`）

- `views/full_view/scroll_area.py:95,97`（canvas の width / height）
- `screen_grid/grid_editor_panel.py:181,183,197`（canvas の height・scroll_frame の height・canvas の width）
- `controllers/call_view_controller.py:256,258`（panes の sashwidth）
- `controllers/compact_pane_layout.py:91`（panes の sashwidth）

Listbox の `width` / `height`（`pane_measure.py:110`・`call_view_frame.py:79`）とフォントの `size`（`theme.py`）は文字数・ポイントで、Tk 9 でも整数を返すため**変えない**。

### テスト

- `tests/test_tk_platform.py` に `screen_distance` のテストを追加: Mock の widget で `cget` が `"10c"` を返し `winfo_pixels("10c")` が `378` を返すとき 378 / `cget` が `300` のとき `winfo_pixels(300)` の値をそのまま int で返す
- 既存のテストで `cget` を Mock している箇所が `winfo_pixels` を持たず落ちる場合は、その Mock に `winfo_pixels` を足す（テストは削除しない）

## 読むファイル

- `keyseq/presentation/tk_platform.py`・`tests/test_tk_platform.py`
- 上記の置き換え対象の各行の前後 10 行
- `grep -rn 'cget("sashwidth")\|cget("width")\|cget("height")' tests tests_ui`（Mock の影響の確認）

## 含まない

- Tk 9 のその他の差の洗い出し（task_06 の probe）
- 中ボタンの番号・カーソルグリッドの Tk 属性（task_06・task_11）

## 確認

**Mac**（メイン・`../../../.venv/bin/python`）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_tk_platform` が失敗 0
- `-m tests.smoke_app` が pass し、stderr に `invalid literal for int()` が出ない
- `-m unittest discover -s tests` の失敗・エラーが task_05 時点（失敗 89・エラー 15）から増えない
- `main.py` を起動し、フル表示が最小サイズで開き、幅を広げると一覧が追従し、縮めるとスクロールバーが出ること（ユーザー目視）

**Windows**: task_05 と併せて標準検証 4 種（ユーザー）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視: Mac のフル表示の大きさの挙動は本タスクで実施（ユーザー）。
