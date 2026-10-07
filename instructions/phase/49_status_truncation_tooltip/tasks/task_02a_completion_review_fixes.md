# task_02a_completion_review_fixes

## 目的

phase 49 の完了判定前レビュー（Codex 敵対的 medium 1 件・deep-reviewer M1 / L1 / L5）への対応（ユーザー承認 2026-10-07）。
正本 `features.md` §4.5「ステータスの見切れのツールチップ」は先に改訂済み（乗せている間に見切れたら出す・最前面に出す）。**presentation 限定。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/hover_tooltip.py`

- **乗せているか**を覚える（`<Enter>` で真・`<Leave>` / `<Button>` / `<Destroy>` で偽）。最後のマウス位置（`x_root` / `y_root`）も覚える
- `refresh()`: 出していれば今どおり（追従 / 閉じる）。**出していなくても乗せていれば**、`should_show()` が真で `text()` が空でなければ最後のマウス位置の右下（+12, +12）に出す
  （Codex 指摘: 欄の幅の再配置の前に古い幅で判定して閉じた後、後続の `<Configure>` の refresh で復帰できるようにする / L1: 乗せている間に見切れ始めたら出す）
- `<Button>` で閉じた後は、乗せ直すまで refresh で出し直さない（クリックで閉じるの意味を保つ）
- ツールチップの Toplevel を最前面に出す（`wm_attributes("-topmost", True)` 等。失敗は吸収）（M1: 「常に最前面」の本体の窓の裏に隠れない）

### `keyseq/presentation/views/status_bar.py`

- `cleanup` の `trace_remove` / `after_cancel` を例外を吸収する形にする（L5: 終了時の破棄の順序で例外が外へ出ない）

### テスト

- `tests_ui/test_hover_tooltip.py`: ①乗せている間に `should_show` が偽 → 真になったら refresh で出る ②出していて閉じた（偽）後、乗せたまま真に戻ると refresh で出る ③`<Leave>` 後・`<Button>` 後は refresh で出ない ④Toplevel が topmost
- `tests_ui/test_status_tooltip.py`: Codex 指摘の再現（中央に長いメッセージがある状態で左のファイル状態の文言を変え、乗せたまま再配置を経ても新しい全文のツールチップが出ている）・乗せたまま窓を狭めて見切れたら出る

## 読むファイル

- `keyseq/presentation/hover_tooltip.py`・`keyseq/presentation/views/status_bar.py`（全体）
- `tests_ui/test_hover_tooltip.py`・`tests_ui/test_status_tooltip.py`（全体）
- 正本 `instructions/common/spec_detail/features.md` §4.5「ステータスの見切れのツールチップ」

## 含まない

- 画面内への寄せ（はみ出しは受容）・表示の遅延・ステータス以外への展開
- 子ファイル保存ダイアログ側のコード変更（共有部品の変更で同じ挙動になる）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- tests・tests_ui 全体・`-m tests.smoke_app` pass。実 `config/` を汚さない

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視（ユーザー）: 本タスクで実施（常に最前面オンでステータス欄に乗せる / 乗せたまま一時メッセージやファイル状態が変わる / 子ファイル保存ダイアログのツールチップ）
