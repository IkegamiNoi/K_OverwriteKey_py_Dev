# task_04b_keep_height_after_unmaximize

## 目的

task_04 の完了判定前レビュー（`codex-adversarial-reviewer` medium / `deep-reviewer` 指摘 3・ユーザー判断 2026-09-18 = 修正）を反映する。
**最大化中に最小の高さが上がり、最大化を解除すると Tk が最小まで広げるが、その高さは Tk の記憶に残らず、後で最小が下がると元の高さへ縮む**。
正本 `features.md` §4.6「最小の高さ」の「一度広げた高さは、後で最小が下がっても縮めない」に反する（task_03b と同じ仕組みの別経路）。
実測: 1200x820（標準）→ 最大化 → ＋3 → 解除で 1200x844 → 標準で **1200x820**。

**presentation 限定・JSON 不変**。幅の挙動・保存判定は変えない。

## 対象範囲（既存 2 ファイルのみ）

### `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py`

- `apply_layout` で、測り直す前の `self.window_min_height` を局所変数に保持する。
- 測定直後の既存の分岐（normal かつ 現在の高さ < 最小 → `geometry(現在の幅x最小)`）を次の条件へ広げる:
  `app.wm_state() == "normal"` かつ（現在の高さ < 新しい最小 **または** 新しい最小 < 測り直す前の最小）のとき
  `app.geometry(f"{app.winfo_width()}x{max(app.winfo_height(), self.window_min_height)}")`。
  （最小を下げる `minsize` の**前**に現在の高さを Tk の記憶へ確定させ、下げた後に縮まないようにする。）
- それ以外（最大化・最小化中、最小が変わらない / 上がって現在の高さが足りている場合）は geometry を出さない。

### `tests_ui/test_full_view_min_height.py`

- テスト追加: **最大化の解除で広がった高さは、最小が下がっても縮まない**。
  幅の変更が起きない十分な幅（現在の幅 + 400 程度）・フォント 0 で高さを最小より少し上（最小 + 40 程度）にする →
  `app.wm_state("zoomed")` → `update()` → ＋3 → `app.wm_state("normal")` → `update()` → `winfo_height()` が ＋3 の最小に広がったことを確認（前提 assert）→
  フォント 0 → `winfo_height()` が広がった高さのまま。
- `_restore` の先頭で `wm_state()` が `"normal"` でなければ `wm_state("normal")` + `update()` する（他のテストへ最大化を持ち越さない）。

### 設計メモ / 制約

- 幅は `app.winfo_width()` のまま（幅の保存判定 `_on_window_configure` は幅が変わらなければ何もしない）。
- 既存テストの期待値は変えない。落ちたら**期待値を弱めず**報告する。
- 最大化中にフォントを下げて解除したときの高さ（Tk が覚えている最大化前の高さへ戻る）は、広げていない高さなので対象外。

## 読むファイル

1. `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py` の `apply_layout`（`rg -n "def apply_layout"`・編集対象）
2. `tests_ui/test_full_view_min_height.py`（全体・編集対象）

## 含まない

- 文書の指摘（正本・codebase_map・凍結ヘッダ・archive・current.md の修正、smoke の再実行）= **task_04**。
- 省略表示・一時メッセージまわり（変更なし）。

## 確認

実行は `verifier`。python は `..\..\..\.venv\Scripts\python.exe`。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests_ui.test_full_view_min_height -v` が全 pass（11 項目）。
3. `-m unittest discover -s tests_ui` が全 pass / `-m unittest discover -s tests` が全 pass / `-m tests.smoke_app` が SMOKE OK。
4. **変異検査**: 条件の「または 新しい最小 < 測り直す前の最小」だけを一時的に外して追加テストが失敗することを確認し、元に戻す（verifier がリポジトリに残さない）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視（任意）: 最大化 → ＋3 → 解除 → 標準で高さが縮まない。
