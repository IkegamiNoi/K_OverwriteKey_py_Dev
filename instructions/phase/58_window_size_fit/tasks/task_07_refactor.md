# task_07_refactor

## 目的

`/refactor_check` の提案書 24（`instructions/modified_proposal/24_refactor_compact_header.md`）の項目 0〜3 を実施する（ユーザー承認 2026-10-15・このフェーズで実施）。
**挙動不変・presentation 限定（controllers/compact_header_controller・app.py の登録・controllers/pane_layout/pane_measure）・domain / application 不変・スキーマ不変。**

## 対象範囲（提案書 24 のとおり）

- 項目 0: `tests_ui/test_compact_header_view.py` に「閉じた見出し・開き直した枠の `pack_info()['pady']` と並び順が元と同じ」の確認が無ければ先に足す
- 項目 1: `compact_header_controller.py` に `_heading_text(title, is_open)` を置き、見出しの文言の組み立てをすべてこれに置き換える
- 項目 2: `register_section(name, frame, heading, collapsed_heading, title)` で題名を受け取り（`app.py` の登録 2 か所で `"フック"` / `"表示"` を渡す）、登録の順を並び順にし、
  枠の pack の引数（`side` / `fill` / `expand` / `pady` 等・`in` は除く）を登録時に `frame.pack_info()` から写して閉じた見出し・開き直した枠に使う。
  `_title`・`("hook", "display")` の 2 か所・`pady=(8, 0)` の 2 か所を消す。前提（登録時に枠が pack 済み）を docstring に書く。
  task_06a で足したキー操作の結び付け（見出し 2 つに同じループが 2 つ）も 1 つのループにまとめてよい（挙動不変）
- 項目 3: `pane_measure.py` に `_full_view_boxes(app)` を置き、3 枠のタプル 2 か所（`measure_main_area_basis_height`・`_sync_full_view_scroll_areas`）を置き換える
- `parse_compact_header_view`（保存形式の定義）は対象外

## 読むファイル

1. `instructions/modified_proposal/24_refactor_compact_header.md`（全体）
2. `keyseq/presentation/controllers/compact_header_controller.py`（全体）
3. `keyseq/presentation/app.py:350-365`
4. `keyseq/presentation/controllers/pane_layout/pane_measure.py`（全体）
5. `tests_ui/test_compact_header_view.py`（全体）

## 含まない

- `views/compact_view/sequence_frame.py`・`views/full_view/call_view_frame.py` の同じ見出しの形（phase 58 で触っていない）
- 挙動の変更

## 確認

（実行は verifier・`.venv` python）
- `compileall` clean / `tests_ui/test_compact_header_view.py`・`test_full_view_min_size.py`・`test_full_view_min_height.py`・`test_full_view_scroll_areas.py`・`test_full_view_panes.py` pass
- `unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` 全 pass
- 提案書の各項目の grep の完了条件

## 完了条件

- 上記確認 pass・**reviewer 採用**・提案書 24 の状態を「実施済」に更新
