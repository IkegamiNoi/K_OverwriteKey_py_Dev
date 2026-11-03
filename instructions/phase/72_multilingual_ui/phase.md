# phase.md

## フェーズ名

画面の文言の多言語対応（multilingual_ui）

## フェーズの目的

画面に出る文言を日本語 / 英語で切り替えられるようにする。言語はメニュー「設定」で選び、次回の起動から反映する。
3 言語目以降は言語ファイルを置くだけで足せる仕組みにする（追加自体は別 idea）。
**新規 `keyseq/shared/i18n/`（標準ライブラリのみ・全層から依存可）+ 全層の文言のキー化・新規依存なし・
JSON スキーマ = config.json の任意キー `ui_language` の追加**（キーが無いときの既定 = 英語。今の利用者の見え方も変わる・ユーザー確定）。

- 起票元: ユーザー要望（2026-11-01・phase 71 完了後の予定「多言語対応 → Mac 対応」の 1 つ目）。
- 主入力（暫定仕様）: [55_multilingual_ui.md](../../history/55_multilingual_ui.md)（v0.3・ユーザー確定済）。
- モード: **暫定仕様先行モード**。番号対応: phase 72 / 暫定 55 / decisions 72。

## 確定（ユーザー 2026-11-01）

- 対応言語は日本語・英語の 2 つ。3 言語目以降は別 idea（[idea_56](../../backlog/idea_56_more_ui_languages.md)）。
- 言語は設定で選ぶ（OS の言語には合わせない）。次回の起動から反映し、選んだ直後に再起動が必要な旨を知らせる。
- 文言・ヘルプ本文は言語コードごとのファイル。訳が足りない文言は英語で出す。言語の一覧は置いたファイルから作る。
- `ui_language` が無いときの既定は英語（今の利用者もアップデート後は英語で開き、メニュー「Language / 言語」で戻す）。
- アプリが作って保存する既定の文言は作った時点の言語（該当は今 1 か所）。
- Codex 敵対的レビューの指摘 2 件を採用（`tr` の最初の引数を位置専用 / 静的検査の許可を内容・場所・理由の組で照合）。

## スコープ

### 含む

- `keyseq/shared/i18n/`（カタログの読込・`tr` / `tr_in`・フォールバック・言語の一覧・テスト用の差し替え）と `locales/ja.json` / `en.json`。
- App が画面を作る前に言語を決める処理・テストの言語を `ja` に固定する口・メニュー「設定」の言語の項目と保存・再起動の知らせ。
- 表示文字列を内部値に使っている箇所の内部コード化（暫定 55 §6.3）。
- 全層の画面に出る文言のキー化（日本語の文言は 1 文字も変えない）・モジュール定数の文言表をキーへ。
- アクションの種類の表示名・英語の用語と表記の規則（暫定 55 へ追記してユーザー確認）・`en.json` の作成。
- `help_en.json`（ヘルプ本文の英訳）とヘルプの読む順。
- 画面に出る日本語リテラルの残りを調べる静的テスト。
- 英語での見え方の確認（必要なら文字数基準の最小幅の見直し）。tests / tests_ui の追加・更新。正本反映。

### 含まない（後送り）

- 3 言語目以降の追加 / 実行中の即時切り替え / OS の言語に合わせた自動選択 / 日本語の文言の見直し /
  tkinter・OS 標準ダイアログの言語 / ログ文言の英語化 / 保存済みデータの翻訳 / 右から左に書く言語 /
  exe 化に向けた locales の場所の差し替え（暫定 55 §10）。

## このフェーズで読むファイル

1. [暫定 55](../../history/55_multilingual_ui.md)（全体）
2. `instructions/common/spec_detail/ui_terms.md`（§1 対象・内部名 / §2 用語表）
3. `instructions/common/architecture.md` §3.2（依存ルール）・`instructions/common/codebase_map.md`（各 task の対象の節）
4. `keyseq/presentation/app.py`（`__init__` の `load_startup_settings` 〜 `_build_ui` の前）・`startup_settings.py`・`controllers/config_io/startup_io.py`
5. `keyseq/presentation/views/menu_bar.py`・`help/help_content.py`・`bundled_paths.py`
6. 文言の表: `child_kind_labels.py`・`hook_button_texts.py`・`status_text.py`・`*_text.py`（暫定 55 §1）
7. 表示文字列の比較箇所: `dialogs/action_key_hold_fields.py`・`dialogs/action_dialog.py:262`・`controllers/keymap_panel/keymap_add_flow.py`
8. 各キー移行 task の対象ファイル（task 定義で列挙）と、日本語を assert しているテスト（例: `tests_ui/test_app_ui_flows.py`）

## タスク

- task_01: 基盤 — `shared/i18n`（暫定 55 §3・§4.1）・`locales/ja.json` / `en.json`（`_meta` と本 task の新規文言のみ）・App の言語の決定（§4.2・画面を作る前）・テストの言語固定・メニューの言語の項目と保存・再起動の知らせ（§4.3・§5）・`help_content.py` の言語の差し替えと読む順（§3.4。本文の検証エラー文のキー化は task_05）+ tests。`startup_settings.py` / `startup_io.py` / `split_payloads.py` は変更せず、`ui_language` が書き込みの 2 経路（構成セットの保存を含む）で残ることをテストで確かめる（§1・§9 条件 4）。
- task_02: 表示文字列の内部値の分離 — 比較・Combobox の値に使っている表示文字列を仕分けて内部コードへ（§6.3）+ tests（日本語の表示は不変）。
- task_03: キー移行 1 — 主画面・メニュー・views・モジュール定数の文言表（`*_text.py` 等）・キーボード / レイアウト / カーソルグリッド・controllers 直下（約 350 リテラル）。
- task_03b: キー移行 1b — controllers の `config_io/`・`keymap_panel/`・`trigger_panel/`（約 400 リテラル・2026-11-01 に task_03 から分割）。
- task_04: キー移行 2 — アクションの編集まわりの dialogs（`action_dialog.py`・`action_control_fields.py`・`action_key_hold_fields.py` ほか）。
- task_05: キー移行 3 — 残りの dialogs（キーマップ・トリガー・プリセット・グリッド・整理 / 退避 / 履歴・レイアウト ほか）・ヘルプ / バージョン情報 / ライセンスの窓・ヘルプ本文の検証エラー文（`help_content.py`）。
- task_06: キー移行 4 — application / domain / infrastructure の画面に出る文（ログ専用と仕分け）・既定の文言（`split_loading.py:381`）。
- task_07: 英語の用語・表記の規則・アクションの種類の表示名（日英）を暫定 55 へ追記（ユーザー確認・版を上げる）。
- task_08: `en.json` の作成（全キー・差し込み名の一致）・アクションの種類の表示名の結線 + カタログの完全性テスト。
- task_09: `help_en.json`（`help_ja.json` と同じ id）+ id 一致のテスト。
- task_10: 静的検査 — 画面に出る日本語リテラルの残り（§9 受け入れ条件 9 の判定規則と検査自身のテスト）。
- task_11: 統合確認 — tests / tests_ui / smoke・二次レビュー（deep-reviewer + codex-reviewer）。
- task_11a: 二次レビューの採用分の修正（C1・D1・D7・英語のヘルプの JIS のキー名の併記・ユーザー判断 2026-11-01）。
- task_11b: 英語の文言の見直し（記録ボタンの短縮・機能名の大文字〔暫定 55 v0.5 E1・E7〕・英語のヘルプの JIS の特殊キーを例へ・ユーザー判断 2026-11-03）。
- task_12: 実機目視（英語・日本語の切り替えと見え方・必要なら最小幅の見直し）・正本反映（暫定 55 §11: features §4.6 / data_schema §5.4 / ui_terms / architecture §3.2 / codebase_map）・暫定 55 凍結・decisions_archive/72・current.md 完了記載・`/refactor_check`。

## レビュー方針

- **キー移行で日本語の文言が 1 文字も変わっていないこと**（既存テストの日本語 assert が通る・差分の文言の照合）。
- モジュール定数・import 時に `tr` を評価していないこと（言語を決める前の `ja` で固まらない）。
- 表示文字列を内部値に使う箇所が残っていないこと（英語でも同じに動く）。
- ログ専用の文を誤って訳していない / 画面に出る文を取りこぼしていないこと（内側の層の仕分け）。
- `shared/i18n` が他の層に依存していないこと・`tr` / `tr_in` の位置専用引数。
- テストが実機の言語設定に依らず日本語で走ること。
