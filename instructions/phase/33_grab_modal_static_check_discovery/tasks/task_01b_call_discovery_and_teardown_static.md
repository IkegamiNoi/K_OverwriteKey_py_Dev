# task_01b_call_discovery_and_teardown_static

## 目的

完了判定前レビュー（deep-reviewer L1・M1 / codex-adversarial 指摘 2）を受けた追加確定（[phase.md](../phase.md)「追加確定」）の実装。
①task_01 の検査の抜け道（式文以外の `grab_modal(...)`・関数形式・入れ子クラスの素通り）を塞ぎ、3 検査をメソッドに分ける。
②phase 15 側の static_1・static_2（`tests_ui/test_dialog_teardown_flows.py`）を発見ベースにする。
**tests_ui 限定・production 不変・検査する規約は不変（弱めない）**。

## 対象範囲（tests_ui 限定）

### `tests_ui/dialog_discovery.py`（新規・共有ヘルパ。「ダイアログとみなす条件」を 2 テストで同じ定義にするため）

- `PRESENTATION: Path`（`keyseq/presentation`）/ `DIALOGS: Path`（`PRESENTATION / "dialogs"`）
- `parse(path: Path) -> ast.Module`（`encoding="utf-8-sig"`・`filename=str(path)`）
- `find_calls(node: ast.AST, name: str) -> list[ast.Call]`: `ast.walk(node)` 内の**すべての `ast.Call`** のうち、
  `func` が `ast.Name(id=name)` または `ast.Attribute(attr=name)` のもの（式文に限らない）。
- `dialog_classes() -> list[tuple[Path, ast.ClassDef]]`: `DIALOGS/*.py`（ファイル名順）のモジュール直下の `ClassDef` で、
  基底に `ast.Attribute(attr="Toplevel")` または `ast.Name(id="Toplevel")` を持つもの。
- 30 行程度に収める。docstring で「別名 import・多段継承は拾わない」ことを 1 行明記する。

### `tests_ui/test_nested_modal_grab.py`

`test_grab_modal_is_last_initialization_statement` を**3 メソッドへ分割**する（検査内容は task_01 の版から弱めない）:

- `test_grab_modal_call_sites_are_dialogs_or_config_io`: `PRESENTATION` 配下（再帰）で `find_calls(tree, "grab_modal")` が 1 件以上あるファイルが、
  すべて `DIALOGS` 直下か `controllers/config_io/` 直下にある。
- `test_grab_modal_is_last_initialization_statement`（系統 A・名前は据え置き）: `dialog_classes()` の件数下限 11（失敗時にクラス名一覧）/
  各クラスの `__init__` がちょうど 1 つ・`find_calls(__init__, "grab_modal")` がちょうど 1 件・`__init__` の最後の文が式文の `grab_modal(...)` /
  **`DIALOGS/*.py` 全体の `find_calls(..., "grab_modal")` 総数 = 発見したクラス数**（関数形式・入れ子クラス・`__init__` 外の呼び出しを塞ぐ）。
- `test_config_io_grab_modal_is_followed_by_wait`（系統 B）: `find_calls` で数えた呼び出しファイル集合 = 期待件数の辞書のキー /
  各ファイルで `find_calls` の件数 = 期待件数 = 式文形式（既存 `is_call`）の件数（代入の右辺等の形なら落ちる）/ 以降の構造検査は現行のまま。
- 既存のローカル `is_call`（式文判定）は構造検査用に残してよい（クラス内の共有関数またはモジュール関数へ移す）。

### `tests_ui/test_dialog_teardown_flows.py`

- `DIALOG_FILES` を廃止。`NESTED_CHILD_DIALOGS = frozenset({"PresetDialog", "CategoryChooserDialog"})`（ネストした子はフックを止めない）を置く。
- `test_static_1_dialog_suspend_passes_self_once`: `dialog_classes()` を使い、
  - `NESTED_CHILD_DIALOGS` の名前が**すべて発見される**（除外リストの陳腐化検出）/ トップレベル（子以外）の件数下限 9（失敗時にクラス名一覧）
  - トップレベルの各クラスで `find_calls(class, "suspend_hook_for_dialog")` がちょうど 1 件・位置引数は `self`（`ast.Name(id="self")`）1 つ・キーワードなし（現行と同じ条件）
  - 子の各クラスで 0 件
  - `DIALOGS/*.py` 全体の `suspend_hook_for_dialog` 呼び出し総数 = トップレベルのクラス数
  - `subTest(class_name=...)` を使う。docstring の「指定9ファイル」を発見ベースの説明へ直す。
- `test_static_2_dialogs_do_not_call_resume`: `DIALOGS/*.py`（全ファイル）で `find_calls(tree, "resume_hook_after_dialog")` が 0 件。docstring も直す。
- `T2_DIALOG_FILES` と `test_static_3_*` は**変更しない**。モジュールの `is_call` が static_3 以外で不要になれば削除してよい（未使用を残さない）。

### 設計メモ / 制約

- 発見条件を「対象の呼び出しがあること」にしない（消失を素通りさせない）。
- 現物の実測（2026-09-24）: `dialogs/` のトップレベル 9 クラスはすべて `self.parent.hook.suspend_hook_for_dialog(self)` を 1 回、子 2 クラスは 0 回。
  `dialogs/` に `resume_hook_after_dialog` は 0 件。**検査が落ちた場合はテストを緩めず・production を直さず作業を止めて報告**する。
- 新規ヘルパの配置は既存の `tests_ui/escape_delivery.py` / `hook_resume_wait.py` と同じ tests_ui 直下（利用 2 ファイル = Feature Shared）。

## 読むファイル

- `tests_ui/test_nested_modal_grab.py:1-12, 258-355`（task_01 版の検査・編集対象）
- `tests_ui/test_dialog_teardown_flows.py:1-45, 244-282`（列挙と static_1〜3・編集対象）
- `tests_ui/hook_resume_wait.py`（tests_ui 共有ヘルパの書き方の手本・変更しない）

## 含まない

- production コード（`keyseq/`）の変更 / `T2_DIALOG_FILES`・static_3 の変更 / 静的検査以外のテストの変更。
- `Toplevel` の別名 import・多段継承の解決（残るリスクとして task_02 で記録）。
- 文書の更新（task_02）/ テストの実行（実測は verifier）。

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q tests_ui` が clean。
- `-m unittest tests_ui.test_nested_modal_grab tests_ui.test_dialog_teardown_flows` が OK。
- **検出力の確認（一時改変・確認後に必ず `git checkout --` で戻す・1 パターンずつ）**: 以下で該当テストが FAIL すること。
  1. `CategoryChooserDialog.__init__` の `grab_modal` 行の後ろに文を追加（系統 A・最後の文）
  2. `LayoutDeleteDialog.__init__` の `grab_modal` 行を削除（系統 A・消失）
  3. `io_dialogs.py` の `grab_modal(dialog, self._app)` を `_ = grab_modal(dialog, self._app)` に変える（系統 B・式文以外）
  4. `dialogs/layout_delete_dialog.py` の末尾にモジュール関数 `def _extra(w):\n    grab_modal(w, w)` を追加（系統 A・総数）
  5. `OrphanSweepDialog` の `suspend_hook_for_dialog(self)` 行を削除（static_1・止め忘れ）
  6. `PresetDialog.__init__` の先頭付近（`super().__init__` の直後）に `parent.hook.suspend_hook_for_dialog(self)` を追加（static_1・子が止める）
  7. `dialogs/trigger_dialog.py` の任意メソッドへ `self.parent.hook.resume_hook_after_dialog()` を追加（static_2）
  確認後 `git diff --stat -- keyseq` が空。
- 回帰: `-m unittest discover -s tests_ui` と `-m unittest discover -s tests` が OK。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は不要（テストのみ・production 不変）。
