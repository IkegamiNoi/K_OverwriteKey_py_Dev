# task_05_file_line

## 目的

暫定仕様 26 §9（file_line の実行）と §3.2（キーの既定値）を実装する。現在 file_line は通常アクションとして executor へ渡るが、
種別不正として止まる。これを「ファイルのカウンター値の行を text と同じ経路で送る」ようにする。
- 実行のたびに読む / 1 MB（1,048,576 バイト）超は読まずにエラー / `utf-8`（BOM を除く = `utf-8-sig`）・`shift_jis`（**cp932 で復号**）
- 改行は `\r\n` / `\r` / `\n` のみで分割（`str.splitlines()` は使わない）/ 最後の改行の後ろは行に数えない / 行番号 = カウンター値（1 始まり）
- 範囲外: `error` → エラー / `empty` → 何も送らず成功 / `wrap` → `((n-1) mod L)+1` 行目（L=0 はエラー）
- 空文字の行は何も送らず成功。送信は text と同じ `_write_text`（send guard 込み）
- 実行時エラー（§10）: 送信エラーの通知をして `False` を返す（runner がそこで止め、位置はその行に残る）

**application 中心**。presentation は executor への 2 つのコールバックの配線だけ。domain・runner は変更しない。

## 対象範囲（application 中心・presentation は配線のみ）

### `keyseq/application/file_line_reader.py`（新規）

UI・入力送信に依存しない純粋な読込部。
- `resolve_file_line_path(path: str, config_root: str) -> str`: `data_schema.md` §5.7 の読込規則（絶対パスはそのまま・相対は `config_root` 基準で `normpath`。空は空）。
- `read_file_line(path: str, line_number: int, *, encoding: str, out_of_range: str) -> str | None`:
  送る文字列（`empty` の範囲外は `None` = 何も送らない）を返す。エラーは専用の例外（例: `FileLineError(message)`）で送出する。
  - `encoding` / `out_of_range` は呼び出し側で既定値適用・小文字化済みのものを受ける。ここでは値の妥当性も検査する（不正はエラー）。
  - サイズ検査 → バイト列読込 → 復号 → 分割 → 行選択 の順。ファイルが無い・読めない・1 MB 超・復号できないはエラー。
- `normalize_file_line_options(action: Mapping) -> tuple[str, str, str, str]`（path / counter / encoding / out_of_range）: キーが無い・空（§5.1 で非文字列は空）なら
  既定値（`utf-8` / `error`）。trim + 小文字化（`path` と `counter` は小文字化しない・`counter` は大文字小文字を区別）。
- エラーメッセージは日本語で、何が不正か分かるもの（ファイルパス・行番号と行数・文字コード名を含める）。

### `keyseq/application/action_executor.py`

- コンストラクタにキーワード引数を追加: `resolve_file_line_path: Callable[[str], str] | None = None` / `get_counter: Callable[[str], int] | None = None`（既定 None）。
- `execute` に `file_line` 分岐を追加: オプション正規化 → カウンター名が空ならエラー → 行番号 = `get_counter(name)` → パス解決 → 読込 →
  文字列があり空でなければ `_write_text`・`True` を返す。エラーは `_on_action_error(action, message)` を呼び `False` を返す。
  コールバックが未設定（None）の場合もエラー扱いにする（黙って送らない）。
- 既存の hotkey / text / mouse_click / 種別不正の動きは変えない。**種別不正のメッセージ（`_invalid_type_message`）の文言は本タスクでは変えない**。

### presentation（配線のみ）

- `keyseq/presentation/app.py`: `ActionExecutor(...)` に
  `resolve_file_line_path=lambda p: resolve_file_line_path(p, self.config_root)` と `get_counter=lambda name: self.state.counters.get(name, 0)` を渡す
  （`self.config_root` / `self.state` が組み立て時点で使えることを確認し、使えなければ参照を遅延させる lambda にする）。

### テスト

- `tests/test_file_line_reader.py`（新規・一時ディレクトリに実ファイルを作る）: 通常の行 / 1 行目・最終行 / 末尾改行あり・なし / `\r\n`・`\r`・`\n` 混在 /
  `\x0b` や `\x0c` で分割しない / 空行 → `""` / UTF-8 の BOM 除去 / cp932 の拡張文字（①・〜）を `shift_jis` 指定で読める / 復号不能はエラー /
  1 MB ちょうどは読める・1 バイト超はエラー / ファイルが無い / 範囲外 3 種（n=0・n>L・負）/ `wrap` の式（n=0 → L 行目）と L=0 のエラー /
  不正な `encoding`・`out_of_range` / `resolve_file_line_path`（絶対・相対・空）/ `normalize_file_line_options` の既定値と型不正。
- `tests/test_action_executor_file_line.py`（新規・入力送信は偽の gateway）: 成功時に `write_text` が 1 回・send guard が戻る / 空行・`empty` の範囲外で送らず `True` /
  エラー時に `_on_action_error` が呼ばれ `False` / カウンター名が空 / コールバック未設定 / 既存の種別の動きが不変。

### 設計メモ / 制約

- `file_line_reader.py` は `keyboard` / `pyautogui` / tkinter / presentation を import しない。
- カウンターの値は読むだけ（変更しない）。
- ファイル内容はキャッシュしない（実行のたびに読む）。

## 読むファイル

- `instructions/history/26_sequence_control_actions.md` §3.2・§9・§10（仕様）/ `instructions/common/spec_detail/data_schema.md` §5.7（パスの解決規則のみ）
- `keyseq/application/action_executor.py`（編集対象・全体）
- `keyseq/presentation/app.py:70-135`（config_root・state・ActionExecutor の組み立て順）
- `keyseq/domain/sequence_control.py`（file_line の定数と既定値のみ）
- `tests/test_action_executor_type.py`（executor テストの手本・先頭 60 行程度）

## 含まない

- file_line の編集ダイアログ・一覧表示 → task_06 / task_07
- runner・ステップ処理の変更（file_line は既に通常アクションとして executor へ渡る）
- 正本反映 → task_08

## 確認

- 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` がエラー無し。
- 単体: `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_file_line_reader tests.test_action_executor_file_line tests.test_action_executor_type -v` が全 pass。
- 退行: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`・`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass、
  `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass。
- `grep -nE "splitlines|tkinter|keyseq\.presentation|pyautogui|import keyboard" keyseq/application/file_line_reader.py` がヒットしないこと。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_07 でまとめて実施（file_line の編集 UI が task_06 のため）。
- **Luna high の試行**（ユーザー判断 2026-09-27）: `codex-implementer` を `--model gpt-6-luna --effort high` で呼ぶ。所要時間・トークン・reviewer 判定・修正の往復を記録する。
