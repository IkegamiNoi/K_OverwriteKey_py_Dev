# task_03_sample_default_data

## 目的

コードの既定データ（`DEFAULT_CONFIG`）を新しいサンプルに作り直す。既定データは呼び出しのたびに今の言語のラベルで組み立てる（暫定 56 §5.1・§5.2 の「既定データ」・§5.3・§6）。
あわせて、既定データを土台にしていた「新規」「空のデータ」「分離 JSON の読込の土台」が新しいサンプルを引き継がないよう、サンプルを含まない土台を分ける。
**domain（`config.py`）+ application（`config_service`・`split_loading`）+ presentation（`keymap_set_io.py` の新規）+ 言語ファイル・JSON スキーマ不変**。

## 対象範囲

### `keyseq/domain/config.py`

- 定数 `DEFAULT_CONFIG` を廃し、組み立ての関数 2 つにする（import 時に `tr` を評価しない）:
  - `build_base_config() -> dict`: **サンプルを含まない土台**。今の `DEFAULT_CONFIG` からトリガーを除いたもの
    （`keymaps` = `[{"id": "keymap_1", "label": "", "mappings": {}, "triggers": []}]`・`active_keymap_id` = `keymap_1`・`keymap_switch_keys` = `{}`・
    `hook_keys_individual` = False・`hook_stop_key` / `hook_toggle_key` = ""・`hotkey_presets` = 今の既定のプリセット・他のキーも今の値）
  - `build_sample_config() -> dict`: 土台 + 下のサンプル。**呼び出しのたびに今の言語のラベルで組み立てる**
- サンプルの中身（全言語で同じ・ラベルと案内文だけ言語ファイルから）:

  | id | ラベル（ja の例） | 切替キー | mappings | triggers |
  |---|---|---|---|---|
  | `keymap_1` | ショートカット | `1` | なし | r = 行を選択（連続・間隔 30・`home` → `shift+end`）/ c = コピー（`ctrl+c`）/ v = 貼り付け（`ctrl+v`）/ t = アプリの切替（`alt+tab`）/ a = 行を別のアプリへ貼る（連続・間隔 300・`home` → `shift+end` → `ctrl+c` → `alt+tab` → `ctrl+v` → `alt+tab`） |
  | `keymap_2` | 右手側の文字 | `2` | q→p w→o e→i r→u t→y a→l s→k d→j f→h z→m x→n c→b | h = 案内（文字の入力 1 行・下記） |
  | `keymap_3` | テンキー | `3` | z→0 x→1 c→2 v→3 a→plus q→**-** s→4 d→5 f→6 w→7 e→8 r→9 b→enter g→asterisk t→slash | h = 案内（文字の入力 1 行・下記） |

  - トリガーはすべて `suppress: True`・`select_before_run: False`。連続（`run_to_end`）でないものの間隔は今の既定（`DEFAULT_RUN_TO_END_DELAY_MS`）
  - アクションの形は今の既定データと同じ（`{"type": "hotkey", "value": ...}` / `{"type": "text", "value": ...}`）
  - `active_keymap_id` = `keymap_1`・`keymap_switch_keys` = `{"1": "keymap_1", "2": "keymap_2", "3": "keymap_3"}`
  - `hook_keys_individual` = True・`hook_stop_key` = `"f12"`・`hook_toggle_key` = `"f1"`・`keyboard_layout` = `DEFAULT_KEYBOARD_LAYOUT_ID`（Welcome での差し替えは task_04）
  - 案内文（ja の例。英語は `ui_terms.md` に従って訳す）:
    - 右手側の文字: 「右手側の文字のキーマップです。左手のキーで右手側の文字を入力します。割り当てはキーボード表示で確かめられます。数字キーで切り替え、F1 で一時停止/再開、F12 でフックを止めます。」
    - テンキー: 「テンキーのキーマップです。左手のキーで数字と記号を入力します。割り当てはキーボード表示で確かめられます。数字キーで切り替え、F1 で一時停止/再開、F12 でフックを止めます。」
- `config.py:240` 付近の `DEFAULT_CONFIG["hotkey_presets"]` の参照は、土台の関数（または既定のプリセットを返す小さな関数）から取る

### `keyseq/shared/i18n/locales/ja.json` / `en.json`

- サンプルのラベル（キーマップ 3・出力シーケンス 7〔行を選択・コピー・貼り付け・アプリの切替・行を別のアプリへ貼る・案内 2〕）と案内文 2 のキーを**両方**に足す（キー名は `sample.` で始める）
- 英語は `instructions/common/spec_detail/ui_terms.md` §2・§3（E1〜E7）に従う

### `keyseq/application/config_service/__init__.py`

- `new_default_data()` = `build_sample_config()`（サンプル。「サンプルを復元」と起動直後の仮のデータ・プリセット管理が使う）
- 新設 `new_base_data()` = `build_base_config()`
- `new_empty_data()` は `new_base_data()` を土台にする（今の「キーマップを空にする」処理はそのまま）

### `keyseq/application/config_service/split_loading.py`

- `:104` の読込の土台を `service.new_base_data()` に替える（サンプルのフックのキー・`hook_keys_individual` を読込に持ち込まないため）

### `keyseq/presentation/app.py`（:139・2026-11-08 追加）

- 起動直後の仮のデータを `new_base_data()` にする（読込で上書きされるため、サンプルである必要がない。
  読込を止めた tests_ui で、サンプルのフックのキーがキーの取得の検査に効いて IME のテストが落ちたため・メインの調査）

### `keyseq/presentation/controllers/config_io/keymap_set_io.py`

- `new_config`（:62-）: `new_default_data()` + `set_active_triggers(..., [])` をやめ、`new_base_data()` から作る（結果は今と同じ「トリガーなしのキーマップ 1 つ」）
- `restore_default`（:669-）は変えない（`new_default_data()` がサンプルを返すため）。
  `apply_global_defaults` はサンプルの `hook_keys_individual: True` で全体の既定値を注入しない（`config_service/__init__.py:546-549`）ので、F12 / F1 が残ることをテストで確かめる

### テスト

- 新しいサンプルのテスト（tests/）: キーマップ 3・切替キー・mappings（q → `-` を含む）・トリガーとアクション・フックのキー・`active_keymap_id`・
  **ja と en でキー・置換・トリガー・アクションが同じでラベルと案内文だけ違う**・呼び出しごとに新しい dict（変更が次の呼び出しに残らない）
- `build_base_config()` にトリガー・置換・切替キーが無く、`hook_keys_individual` が False
- `new_empty_data()`・分離 JSON の読込・メニュー「新規」がサンプルのキーマップ・フックのキーを持ち込まない
- 「サンプルを復元」の後に `hook_stop_key` = f12・`hook_toggle_key` = f1・`hook_keys_individual` = True（全体の既定値に上書きされない）
- 既存のテストの追従: `DEFAULT_CONFIG` の参照（`tests/test_config_service.py`・`tests/test_domain_config.py:4,353`・`tests/test_per_keymap_triggers_load.py:9,111-113`）を新しい関数へ。
  F1 / F2 のトリガー・`sample_text` 等の旧サンプルを前提にしたテスト（tests / tests_ui）があれば新しいサンプルか土台に合わせる（変えたテストと理由を完了報告に書く）
- テストの言語は既存のとおり固定（`fix_language("ja")` を使っているモジュールの作法に従う）

### 設計メモ / 制約

- 既定データの組み立てで `tr` を呼ぶのは関数の中だけ（モジュール定数・import 時に評価しない・phase 72 の規則）
- 出力シーケンスのラベルは今の既定データと同じ場所（トリガーの `label`）に入れる
- 案内文の数字は「数字キー」と書き、`1`・`2`・`3` を文に含めない（入力した数字が切替キーとして拾われるかが未確認のため。F1 / F12 の表記は残す）

## 読むファイル

- `keyseq/domain/config.py`（:1-120 の既定データと `normalize_key_name` 付近・:230-245 のプリセットの参照）
- `keyseq/application/config_service/__init__.py:55-75`・`:536-570`
- `keyseq/application/config_service/split_loading.py:95-130`
- `keyseq/presentation/controllers/config_io/keymap_set_io.py:60-90`・`:665-692`
- `keyseq/shared/i18n/locales/ja.json` / `en.json`（`config_io.keymap_set.restore` 付近の書式のみ）・`keyseq/shared/i18n/catalog.py`（`tr` の使い方）
- `instructions/common/spec_detail/ui_terms.md` §2・§3（英語の規則）
- 手本のテスト: `tests/test_per_keymap_triggers_load.py:100-120`・`tests/test_domain_config.py:340-360`
- 主入力: `instructions/history/56_welcome_first_launch.md` §5.1〜§5.3・§6

## 含まない

- `config/sample/` への書き出し・完全性の確認・Welcome での配列の差し替え（task_04）
- 初回の判定・起動の流れ・空で始めるときの構成の作成（task_05）
- Welcome の窓・再表示（task_06・07）
- 正本の更新（task_09）

## 確認

- 追加・変更したテストが通る（verifier が `.venv` で実行）
- `python -m compileall -q keyseq`・`python -m unittest discover -s tests`・`python -m unittest discover -s tests_ui`・`python -m tests.smoke_app` が通る
- `DEFAULT_CONFIG` の参照が keyseq / tests / tests_ui に残っていない（grep）
- 言語ファイルの完全性のテスト（ja と en のキーの一致）が通る

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視（サンプルを復元して試す・ラベルの文言）は task_09 でまとめて実施
