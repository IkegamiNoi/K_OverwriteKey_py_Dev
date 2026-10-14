# task_04_grid_editor_ops_panel

## 目的

「枠を編集…」の窓のパネルに操作キーの欄を足し、操作キーの付け替え・既定に戻す・OK の検査・結果の取り込み（`grid.ops` の保存）を行う（暫定 41 §4「編集の窓の結果の取り込み」・§8）。
あわせて、編集の窓の自動割当・振り直し・枠のキーの検査に**今の操作キー**を渡す。
**presentation 限定**（編集の窓・パネル・取り込みの controller）+ domain の `editing.py` に `op_keys` の受け渡しを足すだけ。application は変えない。スキーマは task_01 のまま。

## 対象範囲（presentation + domain の editing.py の引数追加のみ）

### `keyseq/domain/screen_grid/editing.py`

* `split_row` / `split_cell` にキーワード専用引数 `op_keys: Collection[str] | None = None` を足し、`next_free_key(..., op_keys=op_keys)` へそのまま渡す（既定 None の意味は task_01 と同じ）

### `keyseq/presentation/dialogs/grid_editor_window.py`

* 状態 `self.ops: dict[str, str] = ops_of(self._grid)` を持つ。`_op_keys()` = `operation_keys(self.ops)`
* `split_row` / `split_cell` / `reassign_top_keys` / `auto_fill_sub_keys` / `validate_top` / `validate_sub` の呼び出しに `op_keys=self._op_keys()` を渡す
* **選択の排他**: 最上段の枠の選択（`self.selected`）・細分化のボタンの選択（`panel.sub_selected`）・**操作キーのボタンの選択（`panel.op_selected`）**のうち 1 つだけ
  * `on_press`・`switch_monitor`・`reset_monitor`・`select_sub_key`・`rebuild_sub_key_entries` で操作キーの選択を解除する
  * 操作キーのボタンを選んだら、最上段の枠の選択と細分化の選択を解除する
* `on_key`: `esc` は従来どおり先に `on_escape`。修飾キーは従来どおり無視。**操作キーのボタンを選んでいれば `self.ops[その操作] = key`** にしてボタンの表示を更新する（選択は保つ）。それ以外は従来どおり
* `on_escape` の順: 細分化の選択の解除 → **操作キーの選択の解除** → 最上段の枠の選択の解除 → 閉じる（ハンドラは 1 つ・状態で分ける）
* `reset_ops()`: `self.ops = dict(DEFAULT_OPS)`・ボタンの表示を更新・操作キーの選択を解除
* `accept()` の検査に足す: `validate_ops(self.ops, self.reserved, frame_keys)`。
  `frame_keys` = 細分化のキー（今のパネルの値）∪ **`self.monitors` の各画面の実効の最上段のキー**（`self._layouts` にあればそれ・無ければ `top_layout_for({"monitors": self._records}, id)`）∪ `default_top_layout()` のキー（暫定 41 §8）
* `accept()` の結果: `ops_to_json(self.ops)` が `None` でなければ `self.result["ops"]` に入れる（既定と同じなら入れない）

### `keyseq/presentation/screen_grid/grid_editor_panel.py`

* 「キーを枠の左上に表示」の下・細分化の前に「操作キー」の欄を足す:
  * 見出し「操作キー（Esc = 戻る・テンキーの Enter = クリック は固定）」
  * `GRID_OPS` の順に 8 行: ラベル（`OP_LABELS`）+ キーのボタン（`tk.Button`・細分化のボタンと同じ見た目の作法・選択中は SUNKEN と強調色）
  * 「操作キーを既定に戻す」ボタン（`_then_focus_editor` 経由で `editor.reset_ops`）
* 属性・メソッド: `op_selected: str | None` / `op_key_buttons: dict[str, tk.Button]` / `select_op_key(name)`（最上段・細分化の選択を解除・ボタンの表示を更新・`editor.draw()`・フォーカスを `editor.canvas` へ）/ `clear_op_selection()` / `update_op_buttons()`（`editor.ops` の値をボタンの文字へ・選択の見た目）
* パネルが縦に伸びるのは受容（画面に収まらない場合のスクロールは足さない）

### `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`（:494-512 の `new_grid_shapes` の取り込み）

* `label_position` と同じ作法で: `new_grid_shapes` に `"ops"` があれば `grid["ops"]` へ deepcopy で写し（違うときだけ `changed`）、無ければ `grid` に `"ops"` があれば消して `changed`

### テスト

* `tests/test_screen_grid_editing.py`: `split_row` / `split_cell` が `op_keys` に渡したキーを新しい枠のキーにしない
* `tests_ui/test_grid_editor_window.py`（既存の組み立てを流用）:
  * パネルに 8 操作のボタンがあり、初期表示が `ops_of(grid)`（既定・付け替え済みの grid の両方）
  * 操作キーのボタンを選んでキーを押すとその操作のキーになり選択が保たれる / 最上段の枠のキーは変わらない
  * 選択の排他（操作キー ↔ 最上段の枠 ↔ 細分化のボタン）と、Esc の順（操作キーの選択の解除で窓が閉じない）
  * 「操作キーを既定に戻す」
  * OK の検査: 操作キーが枠のキー（今の画面・既定の形・細分化）と重なる / 操作キーどうしが重なる / 予約キー / 固定の esc・num enter（取り込みでは esc を入れられないので `editor.ops` を直接書き換えて確かめてよい）を拒否し窓を閉じない
  * 結果: 既定のままなら `result` に `ops` が無い / 付け替えれば 8 操作を持つ `ops` がある
  * 付け替えた操作キー（例 deepen = `h`）を列の追加・振り直し・細分化の作り直しが飛ばす / 最上段の枠のキーに `h` を入れて OK すると拒否
  * 付け替えて空いた既定のキー（例 `space`）を枠のキーにして OK できる
* `tests_ui/test_task06_keymap_management_ui.py`（:613-642 の `label_position` のテストを手本）: `new_grid_shapes` の `ops` の追加・置き換え・削除で `grid["ops"]` が変わり未保存になる / 同じ値なら変わらない

## 設計メモ / 制約

* 操作キーの検査・正規化は task_01 の domain（`validate_ops` / `ops_of` / `ops_to_json` / `operation_keys`）を使い、presentation に判定ロジックを書かない
* 今つながっていない画面の記録（`self._records` の残り）は `frame_keys` に入れない（窓で直せないため・暫定 41 §8）
* 取り込みは `normalize_grid` を通らない経路なので、窓の結果は domain の関数で正規化済みの値だけを入れること（`ops_to_json` の戻り値）
* `KeymapEditDialog` は `editor.result` を丸ごと下書きにするので変更不要（`ops` も一緒に運ばれる）

## 読むファイル

* `instructions/history/41_grid_crosshair_nudge.md`（§4・§8）
* `keyseq/presentation/dialogs/grid_editor_window.py`・`keyseq/presentation/screen_grid/grid_editor_panel.py`（全体・編集対象）
* `keyseq/domain/screen_grid/editing.py`（:1-50）・`ops.py`（全体）
* `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`（:455-520）
* `tests_ui/test_grid_editor_window.py`（全体・編集対象）・`tests_ui/test_task06_keymap_management_ui.py`（:576-642）・`tests/test_screen_grid_editing.py`（split の既存テスト）

## 含まない

* 編集の窓の境界のドラッグ中の十字（task_05）
* 枠の窓・セッション・振り分けの変更（task_02・task_03 で済み）
* パネルのスクロール化・操作キーの欄の折りたたみ
* 正本の改訂・`codebase_map.md`（task_07）

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_screen_grid_editing tests_ui.test_grid_editor_window tests_ui.test_task06_keymap_management_ui` が全 pass
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass（既知の実行順依存は current.md「テスト負債」のとおり切り分け）
* `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` OK

## 完了条件

* 上記確認 pass・**reviewer 採用**
* **ユーザーの実機目視（本タスクで実施）**: 暫定 41 §9 の 5・6（操作キーの欄で付け替え・既定に戻す・OK の検査・付け替えた keymap で新しいキーが効き元のキーがアプリへ届く）
