# task_06_keys_inner_layers

## 目的

application / domain / infrastructure で作られて画面に出る日本語の文（例外の文・検証エラー・戻り値の理由文・既定の名前）を文言キーへ移す
（暫定 55 §3.1「shared は全層から依存可」・§6.1「内側の層で作られて画面に出る文」・§6.3 既定の文言。キー移行 4）。
**内側の層は `keyseq.shared.i18n` の `tr` を使う（他の新しい依存は足さない）・日本語の文言は 1 文字も変えない・ログ専用は残す・
JSON スキーマ不変**。

## 対象範囲（application / domain / infrastructure 限定）

### 対象（括弧内は日本語の文字列リテラルの概数・docstring を除く・ログ用を含む）

- application（約 160。多い順に action_executor 29・sequence_steps 23・file_line_reader 19・config_service/save_plan_execution 16・
  call_context 12・hook_coordinator 8・keymap_switch_batch 8・file_line_loader 6・save_plan 6・ほか）
- domain（約 116。screen_grid/ops 24・screen_grid/assignment 23・mouse_scroll 20・screen_grid/normalize 17・key_hold 14・call_graph 7・
  control_target 4・sequence_control 4・hotkey 3）
- infrastructure（約 10。win32_window 10）
- 既定の文言: `application/config_service/split_loading.py:381` の `旧トリガーセット（{stem}）`（作った時点の言語で作る。暫定 55 §6.3）

### 仕分け（ファイルごとに行う）

- **画面に出る文**（例外の文・検証の理由・戻り値の文で、presentation が messagebox / ステータス欄 / 一覧 / ツールチップへ出すもの）→ `tr` へ。
  呼び出し元をたどって画面に出るかを確かめる。迷ったら画面に出る側として扱う（訳しても表示は同じなので害が無い）。
- **ログ専用**（`logging.*` / `logger.*` の引数・ログにだけ渡す文）→ そのまま残す。
- 表示用の既定値（例 `sequence_steps.py:48` の `"（なし）"`）は画面に出る文として `tr` へ。
- 比較・辞書のキー・保存される値に日本語を使っている箇所を見つけたら、変えずに報告に列挙する（task_02 の形で直すかはメインが判断）。

### 移し方（task_03〜05 と同じ）

- 文字列リテラルを `tr("<キー>", **params)` に替え、`keyseq/shared/i18n/locales/ja.json` に**今と同じ日本語**を足す。
  f-string は名前付きの差し込みへ。文言中の `{` `}` は `{{` `}}`。連結・条件で組み立てる文は出力が今と同じになるまとまった文のキーにする。
- **モジュール定数・クラス属性・既定引数・dataclass のフィールドの既定値に `tr(...)` を書かない**（import 時に評価される）。
  定数の表は値をキーにして文を作る時点で `tr`、または関数にする。
- 例外を作る時点で `tr` する（言語は実行中に変わらないので表示の時点と同じ結果。暫定 55 §6.1）。
- キーは `<層>.<モジュール>.<用途>`（例 `application.file_line.read_failed`・`domain.mouse_scroll.amount_invalid`）。
  既存キーを使い回すときは値が完全に同じか必ず確かめる。
- `ja.json` は 2 スペースの字下げ・UTF-8・領域ごとにまとめる。`en.json` にはキーを足さない（英訳は task_08）。
- **対象外のまま残す**: ログ専用・docstring・コメント・キーの名前・JSON キー・保存されるデータ値・ファイル名・アクションの種類の内部名。
  判断に迷ったものは残し、報告に列挙する。

### テスト

- 既存テスト（日本語の文を assert しているもの）は期待する日本語を変えずに通ること（tests/ は言語を決める前の `tr` = ja・`fix_language("ja")` 済み）。

## 設計メモ / 制約

- 日本語の文言（全角・半角・改行・空白・句読点）を 1 文字も変えない。
- 内側の層から presentation・tkinter を import しない。`keyseq.shared.i18n` 以外の新しい依存を足さない。
- presentation は触らない（task_03〜05 で済み）。

## 読むファイル

1. `instructions/history/55_multilingual_ui.md` §3.1・§3.2・§6
2. `keyseq/shared/i18n/__init__.py`・`keyseq/shared/i18n/locales/ja.json`（既存キーの確認）
3. 対象ファイル（全体）
4. 画面に出るかを確かめるための呼び出し元（`grep` で該当箇所だけ）と、対象の文言を assert しているテスト（該当箇所だけ）

## 含まない

- presentation（task_03〜05 で済み）/ `en.json` の英訳・アクションの種類の表示名（task_08）/ 日本語リテラルの静的検査（task_10）

## 確認

- 対象の層に、画面に出る日本語の文字列リテラルが残っていない（ログ専用・報告で残した理由のあるものを除く）
- 内側の層の import に presentation・tkinter が無い
- `ja.json` が JSON として正しく、全キーの値が文字列 / en のキーが ja の部分集合（`tests/test_i18n.py`）
- 既存テスト全 pass（`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui`）・`-m compileall keyseq` clean・
  `-m tests.smoke_app` OK

## 完了条件

- 上記確認 pass・**reviewer 採用**（削除行の日本語と `ja.json` の値の完全一致の機械照合・ログ専用の仕分けの確認を含む）。
- 実機目視は task_12 でまとめて実施。
