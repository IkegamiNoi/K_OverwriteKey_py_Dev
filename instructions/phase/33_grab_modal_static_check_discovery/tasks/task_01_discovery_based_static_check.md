# task_01_discovery_based_static_check

## 目的

`tests_ui/test_nested_modal_grab.py` の `test_grab_modal_is_last_initialization_statement` の検査対象を
ハードコードの列挙から**走査による発見**へ寄せ、列挙に無い `CategoryChooserDialog`
（`dialogs/keymap_set_history_dialog.py:195`）を含む新規ダイアログが自動で検査されるようにする。
根拠は [phase.md](../phase.md)「確定」（案 A'）。**tests_ui 限定・production 不変・検査する規約は不変**。

## 対象範囲（tests_ui 限定・`test_nested_modal_grab.py` のみ）

### `tests_ui/test_nested_modal_grab.py`

- **系統 A（`dialogs/`）**: `dialog_classes` 辞書を廃止し、`keyseq/presentation/dialogs/*.py` を AST で走査して
  **基底に `Toplevel` を持つモジュール直下のクラス**（`tk.Toplevel` = `ast.Attribute(attr="Toplevel")` と
  `Toplevel` = `ast.Name(id="Toplevel")` の両方）を発見する。発見した各クラスに**現行と同じ検査**を課す
  （`__init__` がちょうど 1 つ / `__init__` 内の `grab_modal` がちょうど 1 回 / `__init__` の最後の文が `grab_modal`）。
  - **発見件数の下限**をアサートする（現状 11 = 旧列挙 10 + `CategoryChooserDialog`）。失敗メッセージに発見したクラス名の一覧を含める。
- **系統 B（`controllers/config_io/`）**: `controllers/config_io/*.py` を走査し、**`grab_modal` を呼ぶファイルの集合**が
  期待件数の辞書（`child_save_dialog.py`=2 / `io_dialogs.py`=1 / `hotkey_presets_io.py`=1・据え置き）の**キー集合と一致**することを確かめる。
  以降の件数・構造検査（初期化関数または try の直下 / 直後は待機だけ / try 内は `wait_window` だけ / finally はフック再開だけ）は**現行のまま**。
- **呼び出し場所**: `keyseq/presentation/` 配下（再帰）で `grab_modal` を呼ぶファイルが、すべて `dialogs/` 直下か
  `controllers/config_io/` 直下にあることを確かめる（`modal.py` は定義側のため呼び出しが無ければ自然に対象外。
  呼び出しの判定は既存の `is_call` を使う）。
- 1 メソッドが長くなる場合、系統 A / 系統 B / 呼び出し場所を**別メソッドへ分けてよい**（`is_call` は共有する）。
  失敗メッセージは現行どおり `f"{path}:{lineno}: ..."` 形式を保つ。

### 設計メモ / 制約

- **発見条件を「`grab_modal` を呼んでいること」にしない**（呼び出しが消えたクラスが対象から外れ、消失を検出できなくなる）。
- 除外リストは作らない（`dialogs/` 配下の `Toplevel` 継承クラスは現状すべてモーダル）。非モーダルの窓が将来ここへ入ったら、そのとき検査が落ちて判断を促す。
- `CategoryChooserDialog` が検査に落ちた場合は**テストを緩めず・production を直さず作業を止めて報告**する
  （`instructions/common/codebase_map.md:344-345`・phase 14 の確定運用）。
- ファイル読み込みは現行どおり `encoding="utf-8-sig"`。

## 読むファイル

- `tests_ui/test_nested_modal_grab.py`（編集対象。`:1-12` の import と `:260-330` の検査のみ読めば足りる）
- `keyseq/presentation/dialogs/keymap_set_history_dialog.py:195-212`（新たに対象へ入るクラス・読むだけ）
- `tests_ui/test_dialog_teardown_flows.py:18-43`（phase 15 側の列挙・**変更しない**）

## 含まない

- production コード（`keyseq/`）の変更。
- `tests_ui/test_dialog_teardown_flows.py`（phase 15 側の静的検査）の変更。
- `codebase_map.md` / decisions_archive / current.md / backlog の更新（task_02）。
- テストの実行（実測は verifier が行う）。

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q tests_ui` が clean。
- `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_nested_modal_grab` が OK。
- 発見結果の実測: 系統 A の発見クラスが旧列挙 10 クラス + `CategoryChooserDialog` の 11 件と一致すること
  （verifier が AST 走査の結果を一覧で出す）。
- **検出力の確認（一時改変・確認後に必ず戻す）**: 以下それぞれで検査が落ちることを確かめる。
  1. `CategoryChooserDialog.__init__` の `grab_modal` 行の後ろに文を 1 つ足す（最後の文でなくなる）
  2. `LayoutDeleteDialog.__init__` の `grab_modal` 行を削除する（消失）
  3. `io_dialogs.py` の `grab_modal` 行を削除する（系統 B の件数）
  確認後 `git diff --stat -- keyseq` が空であること。
- 回帰: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が OK。`-m unittest discover -s tests` も OK。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は不要（テストのみ・production 不変）。
