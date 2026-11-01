# task_03_keys_main_views

## 目的

presentation のうち主画面・メニュー・views・文言の表・キーボード / レイアウト / カーソルグリッド / フック / キーの取得まわりの、
画面に出る日本語の文言を文言キーへ移す（暫定 55 §3・§6.1・§6.3。キー移行 1）。**presentation 限定・日本語の文言は 1 文字も変えない・
JSON スキーマ不変**。controllers の config_io / keymap_panel / trigger_panel は task_03b、dialogs は task_04・05、内側の層は task_06。

## 対象範囲（presentation の下記ファイル限定）

### 対象ファイル（括弧内は日本語の文字列リテラルの概数・docstring とログ専用を除く）

- `app.py`（26）・`views/menu_bar.py`（25）・`views/` 配下の全ファイル（full_view・compact_view・status_bar ほか 計約 60）
- 文言の表: `orphan_sweep_text.py`（38）・`quarantine_manage_text.py`（34）・`keymap_set_history_text.py`（29）・
  `reference_cleanup_text.py`（16）・`hook_button_texts.py`（7）・`child_kind_labels.py`（4）・`status_text.py`（1）
- `keyboard_layouts.py`（25）・`keyboard_window.py`（5）・`screen_grid/` 配下（grid_editor_panel 19 ほか）
- `controllers/hook_controller.py`（17）・`controllers/layout_controller.py`（16）・`controllers/key_capture.py`（7）
- 上記以外で `keyseq/presentation/` 直下・`views/`・`screen_grid/`・`controllers/` 直下にあり日本語の文字列リテラルを持つファイル
  （`controllers/config_io/`・`controllers/keymap_panel/`・`controllers/trigger_panel/`・`dialogs/`・`help/` は除く）

### 移し方（全対象に適用）

- 画面に出る文字列リテラルを `tr("<キー>", **params)` に替え、`keyseq/shared/i18n/locales/ja.json` にキーと**今と同じ日本語**を足す。
  - f-string は名前付きの差し込みへ: `f"読み込みました:\n{path}"` → `tr("io.loaded", path=path)`・ja = `"読み込みました:\n{path}"`。
    式は差し込み前に変数へ取り出す。文言中の `{` `}` は `{{` `}}`。
  - 文字列の連結・条件で組み立てている文は、**出力が今と同じ**になるように、まとまった文のキーにする（語の断片をキーにしない）。
- **モジュール定数・クラス属性・既定引数に `tr(...)` を書かない**（import 時に評価され、言語を決める前の ja で固まる）。
  定数の表は値を文言キーにし、表示する時点で `tr(表[x])` する。または表を関数にして呼び出し時に `tr` する（task_02 の形）。
  表をテストが直接 import して日本語を比べている場合は、テスト側を `tr(...)` を通した比較に直す（期待する日本語の文字列は変えない）。
- キーの名前: `<領域>.<画面や部品>.<用途>`（英小文字・数字・`_`・ドット区切り）。例 `menu.file.save`・`status.hook`・
  `orphan_sweep.result.title`・`keyboard.layout.delete_confirm`。同じ意味で多くの画面に出る短い語（「入力エラー」「確認」等の題名）は
  `common.<用途>` を 1 つ作って共用してよい。意味が違えば同じ日本語でも別のキーにする。
- `ja.json` は 2 スペースの字下げ・UTF-8（`\u` 形式にしない）・領域ごとにまとめる。`en.json` にはこの task のキーを足さない
  （足りない文言は日本語で出る。英訳は task_08）。
- **対象外のまま残す**: ログ専用の文言（`logging.*` / `logger.*` の引数）・docstring・コメント・キーの名前（`変換` 等）・JSON キー・
  保存されるデータ値・ファイル / フォルダ名・アクションの種類の内部名（表示名化は task_08）。判断に迷ったものは残し、報告に列挙する。

### `tests/test_i18n.py`（153 行付近）

- 「en が ja の全キーを持つ」検査を、移行の間は「**en のキーはすべて ja にある**（余分なキーが無い）・**共通のキーは差し込みの名前が一致**」
  へ替える（全キーの検査は task_08 で戻す）。

### テスト

- 既存テスト（日本語の表示を assert しているもの）は、期待する日本語を変えずに通ること。
- 新しい文言キーごとのテストは不要。代わりに、`ja.json` の全キーの値が文字列で、`tr` で引けることを確かめる既存のカタログのテストが通ること。

## 設計メモ / 制約

- 日本語の文言（全角・半角・改行・空白・句読点）を 1 文字も変えない。差分の `-` 行の日本語と `ja.json` の値が一致すること。
- 文言を共通モジュールへ集めない（`ja.json` 以外に文言の置き場を作らない）。
- 対象外のファイルは触らない（他の task と同時に触ると衝突する）。

## 読むファイル

1. `instructions/history/55_multilingual_ui.md` §3.1・§3.2・§6
2. `keyseq/shared/i18n/__init__.py`・`keyseq/shared/i18n/locales/ja.json`
3. 対象ファイル（全体）
4. 対象の文言を assert しているテスト（`grep` で文言を探して該当箇所だけ）

## 含まない

- `controllers/config_io/`・`controllers/keymap_panel/`・`controllers/trigger_panel/`（task_03b）/ `dialogs/`（task_04・05）/ `help/`（task_05）/
  application・domain・infrastructure（task_06）
- `en.json` の英訳・アクションの種類の表示名（task_08）/ 日本語リテラルの静的検査（task_10）

## 確認

- 対象ファイルに、画面に出る日本語の文字列リテラルが残っていない（ログ専用・docstring・報告で残した理由のあるものを除く）
- `ja.json` が JSON として正しく、全キーの値が文字列（`tests/test_i18n.py`）/ en のキーが ja の部分集合
- 既存テスト全 pass（`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui`）・`-m compileall keyseq` clean・
  `-m tests.smoke_app` OK

## 完了条件

- 上記確認 pass・**reviewer 採用**（文言の照合を含む）。
- 実機目視は task_12 でまとめて実施。
