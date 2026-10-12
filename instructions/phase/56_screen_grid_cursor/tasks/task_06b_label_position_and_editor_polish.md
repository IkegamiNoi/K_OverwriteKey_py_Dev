# task_06b_label_position_and_editor_polish

## 目的

暫定 40 v0.7（2026-10-13 ユーザー確定）の差分を実装する: キーの表示位置（keymap ごとに中央 / 枠の左上）と文字の収まりの判定、細分化のキーをクリックして取り込む方式、編集の窓の重なり順、表記を「段」に戻す（§2-13・§3・§5・§7・§8.2・decisions.md「task_06 実機目視 → 暫定 40 v0.7」）。
**domain（正規化の 1 キー・理由の文言）+ application（`GridView` に 1 項目）+ presentation（枠の窓・編集の窓・パネル・`apply_keymap_edit`）。infrastructure 不変。JSON スキーマ変更あり（`grid` の任意キー `label_position`・後方互換）。実装後にユーザーの実機目視。**

## 対象範囲

### domain `keyseq/domain/screen_grid/`

- `normalize.py` `normalize_grid`: `raw["label_position"] == "top_left"` のときだけ戻りの dict に `"label_position": "top_left"` を入れる。それ以外（無い・`"center"`・不正値）は入れない（= 中央。v0.6 までの `grid` を保存し直しても差分が出ない・§3）
- 公開の小さな関数 `label_position_of(grid) -> str`（`"top_left"` / `"center"`）を `__all__` へ
- **表記を「段」に戻す**: `validate_top` の理由（「段 n・列 m: …」「段がありません」等）と `normalize.py` の理由の文字列を「段」に（task_06 の修正で「行」にしたものを戻す）

### application `keyseq/application/screen_grid_session.py`

- `GridView` に `label_position: str = "center"` を足し、`view()` で今の `grid` から `label_position_of` で入れる（既存の項目と並び順は変えない・既定値付きの末尾に追加）

### presentation

- 新規 `keyseq/presentation/screen_grid/cell_label.py`（枠の窓と編集の窓の共用・tkinter のみ）:
  `draw_cell_label(canvas, rect, key, *, position, fill, center_font, corner_font) -> None`。
  `position == "top_left"` なら `corner_font`（= `tkfont.nametofont("TkDefaultFont")`・アプリのフォントの拡大縮小に従う）で枠の左上から各辺 4px 内側に `anchor="nw"`、`"center"` なら `center_font` で枠の中央。
  **文字の収まり**（§7）: `font.measure(key)` と `font.metrics("linespace")` を測り、各辺 4px の余白を含めて枠の幅・高さに収まらなければ描かない（中央・左上とも）。中央の文字の大きさの段階は今の `grid_overlay_window.py` の規則を流用する
- `grid_overlay_window.py`: キーの描画を `draw_cell_label` に置き換え、`view.label_position` に従う（線・強調・暗くする処理は変えない）
- `keyseq/presentation/dialogs/grid_editor_window.py`:
  - **重なり順**（§8.2）: 最初の `<Map>` の当て直しと `switch_monitor` の後に、編集の窓へ `-topmost` を当て直して `lift()`、続けて操作パネルへ `-topmost` を当て直して `lift()`（パネルが一番上・その下が編集の窓）
  - 表示位置: 下書きの `label_position` を持ち、キーの描画を `draw_cell_label` に置き換えてそれに従う。パネルのチェックで切り替えて描き直す
  - 結果: `result` に、チェックが ON なら `"label_position": "top_left"` を入れる（OFF なら入れない）
  - **表記を「段」に戻す**: ボタン「段の追加」「段の削除」・案内・理由の文言
- `keyseq/presentation/screen_grid/grid_editor_panel.py`:
  - チェック「キーを枠の左上に表示」（初期値 = 下書きの `label_position`）
  - **細分化のキー**（§8.2）: 行ごとの入力欄をやめ、R×C の小さなボタンの並び（各ボタンの文字 = その枠のキー）にする。ボタンをクリックするとその枠を選び（強調）、続けて押したキーを、編集の窓と同じ `key_name_from_event` で名前にしてその枠のキーにする（修飾キー単独は無視・Esc は選択の解除だけ）。行数・列数を変えたら並びを作り直し `auto_fill_sub_keys` で埋め直す。最上段の枠の選択と細分化の枠の選択は同時に持たない（片方を選んだらもう片方は解除）
  - 表記を「段」に戻す
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py` `apply_keymap_edit`: `new_grid_shapes` に `label_position` があれば `grid["label_position"] = "top_left"`、無ければ `grid` から `label_position` を消す。変わったら `changed = True`（既存の monitors / sub の比較と同じ流れ）

### テスト

- `tests/test_screen_grid.py`: `label_position` の正規化（`top_left` は残る / `center`・不正値・無しは出力に無い / v0.6 の `grid` は変わらない）・`label_position_of`・理由の文言が「段」
- `tests/test_screen_grid_session.py`: `view().label_position`（既定 `center` / `top_left`）
- `tests_ui/test_screen_grid_overlay.py`: `top_left` のとき文字が `anchor="nw"` で左上に描かれる / 収まらない小さな枠では文字が描かれない
- `tests_ui/test_grid_editor_window.py`: チェックで表示が切り替わり結果に `label_position` が入る / 細分化のボタンのクリック → キーで設定（記号・`num 1` のような空白を含む名前を含む・`key_name_from_event` を偽で注入）/ 行数・列数の変更で並びが作り直される / Esc は選択の解除 / 最上段と細分化の選択が排他 / 重なり順の当て直し（`lift` と `-topmost` が編集の窓 → パネルの順に呼ばれる）/ ボタンと理由の文言が「段」
- `tests_ui/test_task06_keymap_management_ui.py`: `apply_keymap_edit` の `label_position` の付与と削除と未保存
- task_06 で「行」に変えた既存テストの文言は「段」に戻す（それ以外の既存テストは変えない）

### 設計メモ / 制約

- `GridEditorWindow.__init__` の最後は `grab_modal` のまま（構造テスト）。presentation から ctypes を呼ばない
- 文字の描画の規則は `cell_label.py` の 1 か所（枠の窓と編集の窓で重複させない）
- 細分化の深さ（最上段 / 段 ≥1）の用語は画面に出さないので触らない

## 読むファイル

- `instructions/history/40_screen_grid_cursor.md` §2-13・§3（`label_position`）・§5・§7・§8.2
- `keyseq/domain/screen_grid/normalize.py`・`assignment.py`・`__init__.py`
- `keyseq/application/screen_grid_session.py:1-75`
- `keyseq/presentation/screen_grid/grid_overlay_window.py`・`grid_editor_panel.py`・`keyseq/presentation/dialogs/grid_editor_window.py`（全体・編集対象）
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:455-500`（`apply_keymap_edit` の grid の部分）
- `keyseq/presentation/theme.py:91-110`（`TkDefaultFont` にフォントの拡大縮小が入ること）

## 含まない

- 既存のキー取得（トリガー等・`tk_keys.py`）の記号キーの名前（別の idea）
- 正本への反映・`codebase_map.md`（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加・修正したテストのモジュールが pass / `discover -s tests` が全 pass（tests_ui 全体は task_07）
- **ユーザーの実機目視**: 編集の窓とパネルがアプリの前に出る（パネルが一番上）/ 表記が「段」/ 細分化のボタンのクリック → キーで設定できる（記号を含む）/ 「キーを枠の左上に表示」で編集の窓と本番の枠（最上段・細分化後）の文字が左上に出る（UI フォントの大きさ・小さい枠では出ない）/ OFF に戻すと中央 / 保存 → 再起動で保たれる。task_06 の残り（OK → 枠に反映・保存と再起動・キャンセル・予約キーの拒否）と、フック動作中のクリック所要時間（grid_check.log）

## 完了条件

- 上記確認 pass・**reviewer 採用**・ユーザーの実機目視で問題なし

## 実機目視の結果と追加の調整（2026-10-13・ユーザー判断）

- 実機目視: 重なり順・表記「段」・細分化のキーのクリックでの取り込み・表示位置の切替・保存と再起動・キャンセル・予約キーの拒否・フック動作中のクリック時間（2〜36ms）とも問題なし
- 文字の見た目は実機で試して決めた（暫定 40 §7 に記録）: 左上 = UI フォントの大きさ + 暗い下地（枠の線のすぐ内側の角に付ける）/ 中央 = 下地なし（UI フォントの 2 倍の太字・全体の下地も試したうえで）。フォントの大きさの変更で枠を描き直す（`ScreenGridController.on_font_changed`）
- 配色の見直しは idea_44 に分離。既存のキー取得の記号キー名は idea_45 に分離
- レビュー: reviewer = 修正要（M1 パネルの KeyPress の直結・M2 列数が空で例外）→ codex-implementer で修正 + 推奨 3 件。最後の文字の調整（メイン）は task_07 の統合レビューで確認する
