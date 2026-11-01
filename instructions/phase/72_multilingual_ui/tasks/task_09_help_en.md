# task_09_help_en

## 目的

ヘルプ本文の英訳 `help_en.json` を作る（暫定 55 §3.4・§2「ヘルプ本文も言語ごとのファイル」）。英語を選ぶと（task_01 の読む順で）
英語の本文が出るようにする。**同梱データの追加 + テストのみ・コードの変更なし（読込の仕組みは task_01 で済み）・JSON スキーマ不変**。

## 対象範囲（同梱データ + テスト限定）

### `keyseq/presentation/help/content/help_en.json`（新規）

- `help_ja.json` と**同じ構造・同じカテゴリ id・同じ項目 id・同じ並び**で、`title` と本文（ブロックの `text` / `items`）を英訳する。
  id・ブロックの種類（`kind`）・その他の非表示のキーは ja と同じ値にする。
- 訳は暫定 55 §8 の Q4（表記の規則 E1〜E6）と Q5（用語表の英語）に従う。画面の部品の名前（メニュー・ボタン・見出し）に触れる箇所は、
  `keyseq/shared/i18n/locales/en.json` の該当キーの英語と**同じ表記**にする（例: メニュー「設定」→ `Settings`・「別名保存…」→ en.json の値）。
- キーの名前（`Ctrl`・`Enter` 等）・ファイル名・JSON キー・コードの識別子は ja と同じ。
- 今の本文の検証（`help/help_content.py` の読込時の検査と、出荷前の文字検査〔`find_text_issues` 等〕）を通る形にする。

### テスト（`tests/test_help_content.py` に追加）

- 同梱の `help_en.json` が今の検証で読める（エラーなし）。
- `help_en.json` と `help_ja.json` のカテゴリ id・項目 id の並びが一致し、ブロックの数と種類が項目ごとに一致する。
- `help_en.json` の表示する文字列に日本語（ひらがな・カタカナ・漢字）を含まない。
- 出荷前の文字検査が `help_ja.json` に当てているものと同じ検査を `help_en.json` にも当てて問題が無い。
- 今の言語が `en` のとき `load_help_content()` が英語の本文を返す（`fix_language` / `reset_for_tests` で切り替え、最後に戻す）。

## 設計メモ / 制約

- `help_ja.json` は変更しない。コード（`help_content.py` 等）は変更しない（読込の順は task_01 で済み）。
- 英訳の確認はユーザーが実機で行う（task_12）。

## 読むファイル

1. `instructions/history/55_multilingual_ui.md` §3.4・§8（Q4・Q5）
2. `keyseq/presentation/help/content/help_ja.json`（全体）
3. `keyseq/shared/i18n/locales/en.json`（画面の部品の名前の確認・grep で該当キーだけ）
4. `keyseq/presentation/help/help_content.py`（検証の規則）・`tests/test_help_content.py`

## 含まない

- ライセンス本文・第三者ライセンス（訳さない・暫定 55 §6.2）/ 日本語リテラルの静的検査（task_10）/ 正本の改訂（task_12）

## 確認

- 上記の追加テスト・既存テスト全 pass（`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui`）・
  `-m compileall keyseq` clean・`-m tests.smoke_app` OK

## 完了条件

- 上記確認 pass・**reviewer 採用**（訳の規則・用語・画面の部品の名前と en.json の一致の抜き取り確認）。
- 英語の実機目視は task_12。
