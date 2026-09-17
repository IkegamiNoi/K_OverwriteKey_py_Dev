# task_03b_keep_enlarged_height

## 目的

task_03 の二次レビュー（deep-reviewer）で採用した指摘を反映する（ユーザー判断 2026-09-18）。

- **指摘 1（中）**: 最小の高さが上がって Tk が自動で広げた高さが、後で最小の高さが下がると `geometry` で覚えていた元の高さ（820 等）へ縮む。
  暫定仕様 18 §3-4「最小以上なら高さは変えない」・§5-5 に反する。実測: ＋3 起動 844 → 標準で 820 / 標準 820 → ＋3 で 844 → 標準で 820。
- **指摘 2・3・6**: テストの検出力の補強と変数名の修正。

**presentation 限定・JSON 不変**。幅の挙動・保存判定は変えない。

## 対象範囲（既存 2 ファイルのみ）

### `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py`

- `apply_layout` の末尾で `self.window_min_height = measure_window_min_height(app)` を測った直後、最後の `app.minsize(...)` の**前**に:
  `app.wm_state() == "normal"` かつ `app.winfo_height() < self.window_min_height` のときだけ `app.geometry(f"{app.winfo_width()}x{self.window_min_height}")` を出す
  （Tk の覚えている高さを最小の高さへ更新し、後で最小が下がっても縮まないようにする）。
- 幅は `app.winfo_width()` のまま（幅の保存判定 `_on_window_configure` は幅が変わらなければ何もしない）。最大化中・最小化中は出さない。

### `tests_ui/test_full_view_min_height.py`

1. **指摘 2**: 「最小未満なら広がる」テスト（標準 → ＋3 で広がることを確かめているテスト）の末尾に、フォントを 0 へ戻した後も `app.winfo_height()` が広がった高さのまま、を追加。
   あわせて、フル表示の文言のまま「＋3 → 0」ではなく「−3 へ下げる」経路でも高さが変わらないことを 1 行で確かめてよい（同テスト内・任意）。
2. **指摘 3**: 「最小の高さまで縮めても切れない」テストの 3 枠の子部品の判定に、`child.winfo_height() >= child.winfo_reqheight()` を追加（pack が足りない分を削った場合を検出する）。
3. **指摘 6**: 高さを保存しないテストの変数 `first_height_only_call` を、中身（高さだけを変えた後の書き込み記録の開始位置）に合う名前へ変える。

### 設計メモ / 制約

- 起動時に高く開くこと（暫定 §5-5 の起動時分）のテストは追加しない（実機目視 task_03 で確認）。
- 既存テストの期待値は変えない（追加の assert のみ）。落ちたら**期待値を弱めず**報告する。

## 読むファイル

1. `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py` の `apply_layout`（`rg -n "def apply_layout"` で位置特定・編集対象）
2. `tests_ui/test_full_view_min_height.py`（全体・編集対象）
3. `instructions/history/18_full_view_min_height.md` §3-4・§5-5

## 含まない

- 指摘 4（一時メッセージのラベルを App の属性で参照する案）= **保留**（phase 01 で解消した「生やし」に戻るため）。
- 指摘 5（`show_full_view` の呼び出し順の文書追従）= **task_04** の正本反映で対応。
- 実機目視・`integration_result.md` の記録（**task_03**）。

## 確認

実行は `verifier`。python は `..\..\..\.venv\Scripts\python.exe`。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests_ui.test_full_view_min_height -v` が全 pass（10 項目）。
3. `-m unittest discover -s tests_ui` が全 pass（UI 全体。`apply_layout` の変更のため）。
4. **指摘 1 の検出力**: 本タスクの `pane_layout_controller.py` の変更だけを一時的に戻した状態で、追加 assert（指摘 2）が失敗することを確認し、元に戻す（verifier がスクラッチで行い、リポジトリには残さない）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は **task_03** でまとめて実施。
