# task_06b_editor_panel_layout_scroll

## 目的

完了判定前レビュー（Codex 敵対的 medium・ユーザー採用 2026-10-14）の対応。操作キーの欄の追加で縦に長くなった編集の窓のパネルを、2 列化で縦に縮め、
OK / キャンセルより上をスクロールできる領域にして、小さい画面・大きいフォント・細分化 9 段でも OK / キャンセルに届くようにする（正本 `features.md` §4.7「編集の窓」の「パネルの配置」）。
**presentation 限定**（`grid_editor_panel.py` と、高さの制限のための `grid_editor_window.py` の呼び出し 1 か所）。挙動（選択・取り込み・検査）は変えない。

## 対象範囲（presentation 限定）

### `keyseq/presentation/screen_grid/grid_editor_panel.py`

* **配置**
  * 操作のボタン 6 個を 2 列 × 3 行の `grid` にする（段の追加｜段の削除 / 列の追加｜列の削除 / 振り直し｜この画面を既定に戻す・各列は等幅で横に広がる）。`self.buttons` の辞書（文字 → ボタン）は保つ
  * 操作キーの欄（`self.ops_frame`）を「名前のラベル + キーのボタン」の組の 2 列 × 4 行にする（`GRID_OPS` の順に 左→右・上→下 = 深くする｜戻る / クリック｜次の画面へ / 上へ｜下へ / 左へ｜右へ）。
    「操作キーを既定に戻す」は 2 列ぶんの横幅いっぱい。`self.op_key_buttons` は保つ
  * パネルの幅は画面の切替の欄（`monitor_combo`）で決まるまま（2 列にしても広げない）
* **スクロール**
  * OK / キャンセル（`actions`）より上の中身を、`tk.Canvas` + 内側の `ttk.Frame` + 縦の `ttk.Scrollbar` の領域に入れる。`actions` はスクロール領域の外（下）に置き常に見える
  * `set_max_height(height: int)`: スクロール領域の高さを「中身の要求する高さ」と「`height` − `actions` などスクロール外の高さ」の小さいほうにする。中身が収まるときはスクロールバーを隠し（`grid_remove` / `pack_forget`）、収まらないときだけ出す
  * 中身の大きさが変わったとき（細分化の並びの作り直し・フォントの変更による `<Configure>`）にスクロール領域を測り直す
  * マウスホイール（`<MouseWheel>`）でスクロールする。スクロールバーが出ていないときは何もしない。ホイールの結び付けはパネルの中（スクロール領域の上）だけに効かせ、アプリの他の窓のホイールを奪わない
* 既存の属性・メソッド名（`monitor_combo` / `hint` / `buttons` / `label_position_check` / `label_position_var` / `ops_frame` / `op_key_buttons` / `rows_var` / `cols_var` / `count_spinboxes` / `sub_keys_frame` / `sub_key_buttons` / `select_*` / `clear_*` / `update_*` / `rebuild_sub_key_entries` / `sub_key_rows` / `set_selected_sub_key` / `_then_focus_editor`）と、`<Escape>` の結び付けは保つ

### `keyseq/presentation/dialogs/grid_editor_window.py`

* `switch_monitor` でパネルの位置を決めた後に `self.panel.set_max_height(<画面の高さ> − 80)` を呼ぶ（上の余白 12px + 下にタスクバー等の余白。画面の高さ = `self.monitor.rect` の高さ）。それ以外は変えない

### テスト（`tests_ui/test_grid_editor_window.py` に追加・既存の組み立てを流用）

* 操作のボタンが 2 列（`grid_info()` の `column` が 0 / 1）・操作キーのボタンが 2 列 × 4 行で `GRID_OPS` の順
* `set_max_height` を小さい値（例 200）にすると、スクロールバーが見え、パネルの高さが値を超えない・OK / キャンセルのボタンが見えている（`winfo_ismapped`）
* 大きい値にするとスクロールバーが隠れる
* 細分化の段数を 9 にして並びを作り直した後もスクロール領域が測り直される（スクロール領域の `scrollregion` の高さが増える）
* 既存のテスト（選択・Esc・操作キー・OK の検査）が変更なしで通る

## 設計メモ / 制約

* 新しい外部ライブラリを足さない（tkinter 標準のみ）
* パネルは `resizable(False, False)` のまま。高さの制限は `set_max_height` だけで行う
* 2 列化の幅は列ごとに `weight=1`・`uniform` で等幅にする

## 読むファイル

* `instructions/common/spec_detail/features.md`（§4.7「編集の窓」の「パネルの配置」）
* `keyseq/presentation/screen_grid/grid_editor_panel.py`（全体・編集対象）
* `keyseq/presentation/dialogs/grid_editor_window.py`（:66-85 `switch_monitor`）
* `tests_ui/test_grid_editor_window.py`（:1-60 組み立て・パネルを参照する既存テスト）

## 含まない

* 提案書 23 の項目（選択の解除の 1 つの呼び出し・ボタンの色の定数・task_08_refactor）
* パネルの横幅の変更・パネルの位置の規則の変更・選択 / 取り込み / 検査の挙動の変更

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_grid_editor_window` が全 pass
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `discover -s tests_ui` が全 pass・`-m tests.smoke_app` OK

## 完了条件

* 上記確認 pass・**reviewer 採用**
* **ユーザーの実機目視（本タスクで実施）**: パネルが 2 列で縦に縮む・フォントを大きくする / 細分化 9 段でスクロールが出てホイールで動く・OK / キャンセルが常に見える

## 実機目視の差し戻し（2026-10-14）と修正の範囲

ユーザーの実機目視で NG（スクリーンショット）: ①画面 2（`1024x768+895-768`）を切替の欄で選ぶと編集の窓が主画面の `+0+0` に出る ②パネルの文字・キーのボタンが横に切れる
③細分化の列を増やしても幅が変わらず見えない ④段を 9 にしてもキーのボタンが途中までしか見えずスクロールバーも出ない。
メインの probe（`.venv`・実機の 2 画面）で①の原因を特定: **位置の反映が保留中に `wm_attributes("-topmost", True)` を呼ぶと Windows で窓が `0,0` へ戻る**
（`geometry` → `update_idletasks()` → `-topmost` なら移る / `geometry` → `-topmost` だと `0,0`。`_reapply_stacking`〔phase 56〕が `switch_monitor` の末尾で呼ぶため。phase 56 の最終コミットでも同じ手順で再現 = 既存の不具合）。
②〜④は本タスクの「幅は画面の切替の欄で決まる（広げない）」という前提の誤り（正本を「幅は中身に合わせて広がる」へ訂正済み）。

* `grid_editor_window.py` `switch_monitor`: `self.geometry(...)` の直後に `self.update_idletasks()` を呼ぶ（`-topmost` の再設定より前に位置を反映させる）
* `grid_editor_panel.py`:
  * スクロール領域の幅を固定しない（`scroll_frame` の固定幅と `pack_propagate(False)` をやめる、または幅を測り直しのたびに中身の要求幅へ合わせる）。幅 = max(中身の要求幅, 画面の切替の欄の要求幅) + 出ているときのスクロールバーの幅。細分化の並びの作り直し（列・段の変更）・フォントの変更で測り直す
  * 操作キーの欄のラベルとボタンが切れない（4 列の `uniform` 等幅をやめ、ラベルの列は中身の幅・ボタンはキー名〔`page down` / `num enter` 等〕が入る幅）
  * 収まらないときのスクロールバーがパネルの中に見え、ホイールで動く（段 9 × 列 9 でも最後の段まで届く）
* テスト（`tests_ui/test_grid_editor_window.py`）: 列を 9 にすると スクロール領域の幅（`canvas.winfo_reqwidth()`）が増える / 段 9 × 列 9 と小さい上限でスクロールバーが見え `scrollregion` の高さが中身の高さと一致する / 操作キーのボタンの要求幅が `page down` の文字幅以上

