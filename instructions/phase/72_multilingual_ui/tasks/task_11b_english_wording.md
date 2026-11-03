# task_11b_english_wording

## 目的

英語の文言の見直し 3 点（ユーザー判断 2026-11-03）:
(1) 記録ボタンの文言を短くする / (2) 機能名を大文字にする（暫定 55 v0.5 の E1・E7）/
(3) 英語のヘルプの変換・無変換の説明を「特殊キー一般の注意 + JIS は例」に組み直す。

## 対象範囲

### (1) 記録ボタン（`keyseq/shared/i18n/locales/en.json`）

- `hook_button.capture_idle`: `Record by pressing a key` → `Record key`（key は E7 の機能名ではないので小文字）
- `hook_button.capture_active`: `Recording… (Press Esc to stop)` → `Recording… (Esc)`
- ヘルプでこのボタン名を引用している箇所（`help_en.json` の “Record by pressing a key”・3 か所）を新しい名前へ。
- ボタンの幅を文言から決めている箇所（`keyseq/presentation/hook_button_texts.py` 等）があれば、それが新しい文言で動くことだけ確かめる（ロジックは変えない）。

### (2) 機能名の大文字（`en.json`・`help_en.json`）

暫定 55 §8 Q4 の E1・E7 に従い、E7 の語を**文中も含めて**各語の先頭を大文字にする（例: `Edit presets…` → `Edit Presets…`・
`Delete the selected preset?` → `Delete the selected Preset?`・`Use cursor grid` → `Use Cursor Grid`・`keymap edit dialog` → `Keymap edit dialog`）。

- E7 の対象外（操作の語・Folder・記録や候補の語・アクションの種類の表示名）は変えない。
- 語が機能を指さない一般の用法（動詞の trigger・一般語の action / sequence 等）は変えない。判断に迷ったものは一覧にして報告する。
- **変えないもの**: キー（`hook_button.capture_idle` 等）・差し込み名（`{trigger}` 等）・ファイル名（`trigger_set.json`）・JSON のキー名（`hotkey_presets_path`）・
  内部名（`key_hold`・`[hotkey]`）・help_en.json の `id`・`ja.json`・`help_ja.json`。
- 英語の文言を直接比べているテスト（`tests/`・`tests_ui/`。`grep -rn` で探す）は新しい文言へ合わせる。

### (3) 英語のヘルプの JIS の特殊キー（`help_en.json`）

- `limits.make_only`
  - title: `Some special keys do not repeat`
  - body: キーボードによっては一部の特殊キーが押下だけを送り、押し続けてもリピートせず、トリガー / キー置換は 1 回だけ動く・
    離してすぐ押し直すとその 1 回が反映されないことがある、を述べたあと、**例として** JIS キーボードの
    `Muhenkan (無変換)` と `Henkan (変換)` を挙げる。
- `limits.layout_names`
  - 主旨: キーボード固有のキーは、それを定義したレイアウトを選んだときだけ名前で受け取り・送信できる。
    **例として** JIS の `Muhenkan (無変換)`・`Henkan (変換)`・`Hankaku / Zenkaku (半角 / 全角)` は見本 jis.json が定義しており、
    既定の US TKL では送れない。
- 日本語の併記は上の形（括弧の中は日本語だけ・英語の言い換えは付けない）。`tests/test_help_content.py` の許可語 3 つ
  （`無変換`・`変換`・`半角 / 全角`）はそのまま通ること。
- 文の英語は E1〜E7 に従う。

## 含まない

- `ja.json`・`help_ja.json`・日本語の表示 / 正本 `spec_detail/` の改訂（task_12）/ 文言以外のコード変更

## 読むファイル

1. 本書・暫定 55 §8 Q4〜Q6（`instructions/history/55_multilingual_ui.md`）
2. `keyseq/shared/i18n/locales/en.json`・`keyseq/presentation/help/content/help_en.json`
3. `keyseq/presentation/hook_button_texts.py`
4. 英語の文言を比べているテスト（`grep -rn` で探す）・`tests/test_help_content.py`

## 確認（verifier）

- compileall clean / tests 全件 / tests_ui 全件（単独実行）/ smoke
