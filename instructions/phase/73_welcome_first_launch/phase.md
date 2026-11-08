# phase.md

## フェーズ名

初回起動の Welcome とサンプルの作り直し（welcome_first_launch）

## フェーズの目的

初めて起動した人が、Welcome の窓で言語とキーボード配列を選び、基本的な使い方を知り、サンプル入りか空かを選んで始められるようにする。
あわせて、コードの既定データ（＝サンプル）を、キーマップの切り替え・キー置換・出力シーケンスが見られる新しいサンプルに作り直す。
**新規 `keyseq/presentation/welcome/`・application 層に初回の判定とサンプルの書き出し・`domain/config.py` の既定データを組み立ての関数へ・
新規依存なし・JSON スキーマ不変**（既定データの中身・書き出し先 `config/sample/`・JIS の配列ファイルの名前が変わる）。

- 起票元: ユーザー要望（2026-11-08・idea は起票しない＝ユーザー指示）。
- 主入力（暫定仕様）: [56_welcome_first_launch.md](../../history/56_welcome_first_launch.md)（v0.5・ユーザー確定済 2026-11-08・v0.5 は 2026-11-09）。
- モード: **暫定仕様先行モード**。番号対応: phase 73 / 暫定 56 / decisions 73。

## 確定（ユーザー 2026-11-08）

- Welcome は 1 枚の窓（Language・キーボード配列・基本的な使い方・始め方・「ヘルプを開く」/「はじめる」）。初回だけ自動で出し、ヘルプのメニューから再表示できる。
- 初回 = 起動設定ファイル（`config/config.json`・旧 `settings/startup.json`）が無いとき。既存の利用者を区別しない。最初の言語は今の既定（英語）。
- 始め方は「サンプル入り」（既定）/「空」。キーボード配列は US TKL / JIS。
- サンプル = コードの既定データ（全言語で同じ中身・ラベルと案内文だけ言語ファイルから）。shortcut（1・最初に有効）/ right key（2）/ num（3）、
  num と right key に h の案内、停止キー F12・一時停止/再開キー F1（構成セット側）。書き出し先 `config/sample/`。
- 見本の `jis.json` を `jis_test.json` へ改名し、全キーの JIS を `jis.json` として作る。
- minus をキー置換の置換先にするとエラーになる不具合を本フェーズで直す。
- deep-reviewer の起票時レビュー（修正して採用）と Codex 敵対的レビューの指摘 4 件（推奨案）を反映済み（暫定 56 v0.4）。

## スコープ

### 含む

- 暫定 56 §3〜§8 の全部（初回の判定と起動の流れ・Welcome の窓・サンプル・JIS の配列ファイル・空で始める・ヘルプからの再表示・minus の修正）
- Welcome を出すかは `main.py` から `App` の引数で渡す（v0.5。既定は出さない＝smoke / tests_ui は不変）
- 既定データの F1 / F2 を前提にしたテスト・見本の `jis.json` を参照するテストとヘルプの本文の追従

### 含まない（後送り）

- プリセットが一度編集で開かないと表示されない不具合 / キー名の記号表記（`bar` → `|` 等）（ユーザー報告 2026-11-08・別扱い）
- OS の言語からの最初の言語の推定 / 用途別の複数のサンプル / 日英以外の言語のサンプル / `de.json` の作り直し

## このフェーズで読むファイル

1. `instructions/history/56_welcome_first_launch.md`（主入力）
2. `keyseq/presentation/app.py`（:107-150 の起動の順序・:349 `load_startup_and_config`・:517-535 言語の切り替え）
3. `keyseq/presentation/controllers/config_io/startup_io.py` / `keymap_set_io.py`（:70 新規・:669 復元・:692 起動時の構成セット）/ `keyseq/presentation/config_paths.py`
4. `keyseq/domain/config.py`（既定データ）/ `keyseq/application/config_service/__init__.py`・`split_loading.py`・`save_path_resolution.py`・`save_plan_execution.py`
5. `keyseq/presentation/help/help_window_controller.py`（`open` / `open_for_dialog`）/ `keyseq/presentation/modal.py` / `keyseq/presentation/views/menu_bar.py`
6. `keyseq/shared/i18n/catalog.py`・`locales/{ja,en}.json` / `keyseq/presentation/keyboard_layouts.py`（外部の配列の登録）
7. `config/user/keylayout/*.json`・`keyseq/presentation/help/content/help_{ja,en}.json`（見本の名前）
8. 正本 `features.md` §4.5・§4.6（「言語」「ヘルプの窓」「メニュー・個別保存」「モーダルダイアログの作法」）/ `data_schema.md` §5.4 / `ui_terms.md` / `key_input.md` §7.3 / `codebase_map.md`
9. task_01 のみ: キー置換の送信経路（minus の原因箇所。task_01 の調査で特定する）

## タスク

- task_01: minus をキー置換の置換先にするとエラーになる不具合の調査と修正（`plus` / `asterisk` / `slash` 等の記号のキーも調査範囲・暫定 56 §8）+ tests。
- task_02: JIS の配列ファイル — 見本 `jis.json` → `jis_test.json` へ改名（`layout_id` を別の値へ・参照するテストとヘルプの本文を追従）・全キーの JIS を `jis.json`（`layout_id: "jis"`）で新規作成（§5.4）+ tests。
- task_03: 既定データ＝新しいサンプル — `domain/config.py` を組み立ての関数へ（ラベル・案内文は言語ファイルのキー・num の q = minus）・メニュー「新規」を直接の組み立てへ・
  「サンプルを復元」でサンプルのフックのキーが残ること・F1 / F2 前提のテストの修正（§5.1・§5.3・§6）+ tests。
- task_04: サンプルの書き出し — application 層で既定データを `config/sample/` へダイアログなしで書く（子 → 構成セットの順・選んだ配列と JIS の登録）・既存の一式の完全性の確認・
  `config/sample/` と置き場の走査の相互作用の確認（§5.2）+ tests。
- task_05: 初回の判定と起動の流れ — `super().__init__()` 直後の判定と `withdraw`・Welcome の結果の受け渡し・空で始めるときの構成の作成・読込後の書き出し・Welcome を出すかを `main.py` から `App` の引数で渡す（暫定 56 v0.5。既定は出さない＝smoke / tests_ui は不変）（§3・§6）+ tests。
  Welcome の窓は仮の差し替え口でよい（task_06 で本実装）。
- task_06: Welcome の窓（初回）— Language（その場で切り替え）・キーボード配列（言語への追従）・基本的な使い方・始め方・「ヘルプを開く」（Welcome の子）/「はじめる」・× / Esc（§4）・言語ファイルの文言（日英）+ tests_ui。
- task_07: ヘルプからの再表示 — メニュー「Welcome を表示」・始め方と配列を除く・`tr_in` で全体の言語を変えない・言語の変更は再起動の知らせ・子のヘルプ（§7）+ tests_ui。
- task_08: 統合確認 — tests / tests_ui / smoke・二次レビュー（deep-reviewer + codex-reviewer）。
- task_08a: 二次レビューの採用分の修正（復元で配列を保つ・再表示の modal の親・minus の読み替えをキーの名前だけに・書き出し → 読込の通しのテスト・孤児の掃除の参照元に config/sample・ユーザー判断 2026-11-09）。
- task_08b: 実機目視の指摘の修正（配列をドロップダウンに・日本語の折り返し・h の案内文の場所・再表示に基本的な使い方と「サンプル設定に戻す」ボタン・暫定 56 v0.6・ユーザー 2026-11-08）。
- task_08c: 再表示の Welcome から Language を外す（暫定 56 v0.7・ユーザー 2026-11-09）。
- task_08d: 完了前レビューの採用分の修正（復元で全キーマップを未保存に・警告の前に本体を表示・ユーザー 2026-11-09）。
- task_09: 実機目視（初回の Welcome・サンプルでの試行・JIS 表示）・正本反映（暫定 56 §12: features §4.6 / data_schema / ui_terms / codebase_map）・暫定 56 凍結・decisions_archive/73・current.md 完了記載（次採番 phase 74 / 暫定 57 / decisions 74 の明記）・`/refactor_check`。

## レビュー方針

- Welcome の前後で起動の順序が崩れていないこと（言語 → 画面の構築・`UiVars` の初期値・読込 → 書き出し）。初回以外の起動の挙動が変わらないこと。
- 既定データが呼び出しのたびに今の言語で組み立てられ、import 時に `tr` を評価していないこと。全言語で同じ中身（キー・置換・トリガー）であること。
- サンプルの書き出しが利用者のファイル（`config/user/`）を触らず、途中の失敗で不完全な一式を完成品として使わないこと。
- 復元・新規・空で始めるのデータが保存先の記録を持たず、保存で既存のファイルを上書きしないこと。
- 再表示で全体の言語が変わらないこと。Welcome の子のヘルプがモーダル中に操作できること。
- テストが Welcome を出さない入口で走り、実機の `config/` の有無に依らないこと。
