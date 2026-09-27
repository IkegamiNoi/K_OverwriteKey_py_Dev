# task_01_split_read_and_pick

## 目的

file_line の読込を「検証」「読込（行の一覧）」「行の選択」の 3 つに分ける（暫定 27 §3.1-1〜3）。
後続タスクで、検証と行の選択は UI スレッド、読込（I/O を含む部分）はワーカーで行う。また読込の結果（行の一覧）は行番号に依らないため、キャッシュ（§6.2）できる。
**application 限定（`file_line_reader.py` のみ）・純粋な分割・挙動と文言は不変・スキーマ不変**。

## 対象範囲（application 限定・`keyseq/application/file_line_reader.py` とそのテストのみ）

### `keyseq/application/file_line_reader.py`

現在の `read_file_line`（`:46-83`）を次の 3 関数へ分ける。文言・検査の順・例外型（`FileLineError`）は現行と完全に同じにする。

1. `validate_file_line_request(path: str, line_number: int, *, encoding: str, out_of_range: str) -> None`
   - 現行 `:54-59` の 3 検査（encoding → out_of_range → 行番号の型）を**この順で**行う。I/O はしない。
2. `load_file_lines(path: str, *, encoding: str) -> list[str]`
   - 現行 `_read_bytes`（1 MB 上限・読めない）→ 復号（`utf-8-sig` / `cp932`・失敗時の文言）→ `_split_lines`。**I/O を含むのはこの関数だけ**。
   - encoding の値は検証済みの前提（`shift_jis` 以外は `utf-8-sig`。現行 `:63` と同じ分岐）。
3. `pick_file_line(lines: Sequence[str], line_number: int, *, out_of_range: str, path: str) -> str | None`
   - 現行 `:70-83` の範囲内 / `empty` / `wrap`（空ファイルは例外）/ `error` の判定。`path` はエラー文言のためだけに受け取る。I/O はしない。
- `read_file_line` は残し、`validate_file_line_request` → `load_file_lines` → `pick_file_line` の合成にする（シグネチャ・戻り値・文言は不変）。
  現行の呼び出し元（`action_executor.py:103`）とテストはそのまま動く。

### `tests/test_file_line_reader.py`

- 既存テストは**変更しない**（`read_file_line` の挙動が不変であることの確認）。
- 3 関数の単体テストを追加する（最小限）:
  - `validate_file_line_request`: 不正な encoding・out_of_range・行番号（bool を含む非 int）で現行と同じ文言の `FileLineError`。
    **encoding と out_of_range が両方不正なら encoding の文言**（順序の固定）。ファイルが無くても I/O エラーにならない（存在しないパスで検証だけ通る）。
  - `load_file_lines`: 改行 3 種・末尾改行・BOM・cp932・1 MB 超・無いファイルが現行と同じ結果 / 文言（既存テストと重複する観点は 1〜2 件でよい）。
  - `pick_file_line`: 範囲内・範囲外 3 択・空リストの `wrap` がエラー・n=0 の `wrap` が最終行。ファイルを使わず `list[str]` を直接渡す。

### 設計メモ / 制約

- 3 関数は**すべて純関数（`load_file_lines` の I/O を除く）**。スレッド・ロック・キャッシュ・`os.stat` はこのタスクで入れない（task_02）。
- 既存の非公開関数 `_read_bytes` / `_split_lines` は再利用する（改名・移動しない）。
- 新しいモジュールを作らない。`file_line_reader.py` は 113 行程度なので分割不要。

## 読むファイル

- `keyseq/application/file_line_reader.py`（全体・編集対象）
- `tests/test_file_line_reader.py`（全体・編集対象）
- `instructions/history/27_file_line_async_read.md` §3.1（分担の根拠。`:53-65` 付近）

## 含まない

- 読込の登録簿・待ち合わせ・キャッシュ・`os.stat` による更新確認・ワーカーの起動（task_02）
- `action_executor.py` の準備と送信の分離・runner の保留・`read_file_line` の呼び出しの置き換え（task_03）
- 連続実行（task_04）/ 配線（task_05）/ 正本・codebase_map の更新（task_07）
- `read_file_line` の削除（呼び出し元が無くなるかは task_03 で判断する）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_file_line_reader tests.test_action_executor_file_line -v` が全 pass（既存 + 追加）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass（件数は増えるだけ・既存の失敗なし）
- `git diff --stat` が `keyseq/application/file_line_reader.py` と `tests/test_file_line_reader.py` のみ

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 文言・検査の順・例外型が不変か / I/O が `load_file_lines` にだけあるか / 後続タスクの先取りがないか）。
- 実機目視: なし（挙動不変の分割。実機確認は task_05 でまとめて実施）。
