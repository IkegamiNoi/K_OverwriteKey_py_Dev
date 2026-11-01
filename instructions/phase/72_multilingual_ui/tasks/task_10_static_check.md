# task_10_static_check

## 目的

アプリのソース（`keyseq/`）に画面に出る日本語の文字列リテラルが残っていないことを静的テストで保証する（暫定 55 §9 受け入れ条件 9・
§2 Codex 指摘 2〔許可は内容・場所・理由の組で照合し、未使用の許可も失敗〕）。**テストの追加のみ・アプリのコードは変更しない**。

## 対象範囲（tests 限定・新規 1 ファイル）

### `tests/test_no_japanese_ui_literals.py`（新規）

- `keyseq/` 配下の全 `.py`（`__pycache__` を除く）を `ast` で読み（BOM 付きも読めるよう `utf-8-sig`）、文字列定数（`ast.Constant` の str・
  f-string の中の定数を含む）のうち、ひらがな・カタカナ・漢字（`[぀-ヿ一-鿿]`）を含むものを集める。
- 除くもの:
  - docstring（モジュール・クラス・関数の本体の先頭の文字列式）
  - ログ呼び出しの**メッセージの引数**: 呼び出し先が `<名前>.<debug|info|warning|error|exception|critical|log>` で、
    `<名前>` が `logging` / `logger` / `log` / `_logger` / `LOGGER` / `_log` のもの。**第 1 引数（メッセージ）の中の定数だけ**を除く
    （他の引数の中は除かない。`logging.warning("%s", messagebox_text("…"))` の「…」は検出する）。
- 残ったものを**許可リスト**と照合する。許可リストの 1 件 = `(ファイルの相対パス, 関数名〔モジュール直下なら "<module>"〕, 文字列の値, 理由)`。
  - 集めた文字列で許可リストに無いもの → 失敗（ファイル:行・関数・値を出す）
  - 許可リストにあって集めた中に無いもの（使われていない許可）→ 失敗
  - 同じ (パス, 関数, 値) が複数あるときは数も一致させる（多重集合で照合）
- 許可リスト（2026-11-01 の実測。値は今のソースの文字列をそのまま書く）:
  - `keyseq/domain/screen_grid/normalize.py` の `_key_error` / `_top_layout_with_reason` / `_sub_layout_with_reason` の理由文 17 件
    （理由 = 警告ログ専用。`normalize_grid` の `logger.warning` にだけ渡る）
  - `keyseq/infrastructure/win32_window.py` の `<module>` の `_ERROR_MESSAGES` の値 9 件（理由 = ログ専用。`_log_once` → `_logger.exception`）
  - `keyseq/presentation/dialogs/grid_editor_window.py` の `__init__` の `編集できる画面がありません` 1 件（理由 = プログラム側の例外・画面に出ない）
  - `keyseq/presentation/help/help_content.py` の `find_text_issues` の 4 件（理由 = 出荷前の文字検査・テストからだけ呼ばれる）
  - `keyseq/presentation/help/help_tab_view.py` の `<module>` の `・` 1 件（理由 = 区切りの記号・言語に依らない）
  - 正確な値と件数は実装時にソースを読んで書く（合計 32〜33 件の見込み）。
- 検査自身のテスト（同じファイル内・一時ディレクトリに小さな `.py` を書いて検査関数に渡す）:
  - 許可した場所の文字列を別の日本語に替えると失敗する
  - ログ呼び出しの第 1 引数の日本語は除かれ、第 2 引数以降の中の画面用の呼び出しの日本語は検出される
  - docstring は除かれ、関数の途中の文字列式は検出される
  - 使われていない許可で失敗する

## 設計メモ / 制約

- 検査のロジックはテストファイルの中に置く（アプリのコードに入れない）。
- 許可リストを増やすときは理由を必ず書く（テストのコメントにも「画面に出る文は tr へ。許可は画面に出ないものだけ」と書く）。

## 読むファイル

1. `instructions/history/55_multilingual_ui.md` §9（受け入れ条件 9）
2. 許可リストの対象の 5 ファイル（該当の関数だけ）
3. 手本: `tests/test_i18n_test_language_fixed.py`（ソースを走査する静的テストの形）

## 含まない

- アプリのコードの変更（画面に出る日本語が見つかったら直さず報告する）/ 正本の改訂（task_12）

## 確認

- 新しいテストが pass（`..\..\..\.venv\Scripts\python.exe -m unittest tests.test_no_japanese_ui_literals`）・tests 全体 pass・
  `-m compileall keyseq` clean

## 完了条件

- 上記確認 pass・**reviewer 採用**（判定規則が暫定 55 §9-9 どおりか・許可リストの理由の妥当性）。
