# task_06_integration_check

## 目的

phase 57（task_01〜05）を統合として確認する。task_02 のレビューで挙がったテストの抜けを補い、全体の退行テストと二次レビュー（`deep-reviewer` + `codex-reviewer`）を行う（暫定 41 §9）。
**テスト追加のみ**（`tests/test_screen_grid_session.py`）。実装コードは変えない（レビューで修正が要ると判断したら枝番タスクで行う）。

## 対象範囲（テスト追加のみ）

### `tests/test_screen_grid_session.py` に追加（期待値は暫定 41 §5・§6 から導く）

1. 画面の構成が変わり今の画面の識別子が見つからない状態でクリックの操作をすると、クリックせず `view().click_point` が `None`・最上段・選択なしになる（`_refresh_monitors` の経路）
2. 戻る（深さ 2 → 1 等）で親の枠が見つからない状態（細分化の元の矩形と親の枠が一致しない）では選択なし・`click_point` が `None`
3. `deepen` / `back` / `next_screen` は `shift=True` でも Shift なしと同じ結果になる
4. Shift + 枠のキー（`shift=True` の枠のキー）は枠の選択になり、クリック点は中心
5. 手編集で操作キーが重なった ops（例 deepen = back = `h`）では `GRID_OPS` の順で先の deepen が効く
6. 手編集で最上段にも細分化にも無い `esc` / 矢印の扱い: 最上段・選択なしの `snapshot().suppress_keys` に `esc` と矢印が入らない / 手編集で**最上段の枠のキー**に `up` があると最上段では `up` が集合に入り、`handle` で枠の選択になる

## 読むファイル

* `instructions/history/41_grid_crosshair_nudge.md`（§5・§6）
* `keyseq/application/screen_grid_session.py`（全体）
* `tests/test_screen_grid_session.py`（全体・編集対象）

## 含まない

* 実装コードの変更（レビューで要修正なら task_06a として起票）
* 正本反映（task_07）

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass（既知の実行順依存は current.md「テスト負債」のとおり切り分け）
* `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` OK
* 統合レビュー: `deep-reviewer`（phase 57 の全差分 `git diff d585e7f..HEAD`・暫定 41 との適合・層をまたぐ整合）+ `codex-reviewer`（同じ範囲の標準レビュー）

## 完了条件

* 上記確認 pass・**deep-reviewer と codex-reviewer の指摘の採否をユーザーと決め、要修正分を反映**（Codex 指摘の採否はユーザー確認）
* 実機目視は task_03〜05 で済み（追加なし）
