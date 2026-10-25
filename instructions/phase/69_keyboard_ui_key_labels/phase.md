# phase.md

## フェーズ名

キーボードUIのキー名の表示と最小サイズ（keyboard_ui_key_labels）

## フェーズの目的

キーボードUIのキーの文字を、キーの幅に合わせて縮め、単語の途中で折り返さないようにする。改行（`label` の `\n`）とキー置換の送信先の表示名（レイアウトの JSON の表）を指定できるようにする。
最小サイズを `w = 1.0` のキー 27px 基準にし、利用者が変えた窓の幅をレイアウトごとに記録して次に開くときその幅で開く。内蔵の US TKL と同じ内容の見本 JSON を置く。
**対象は presentation（キーボードUI・レイアウトの読込・起動設定の書き出し）。JSON スキーマ = 追加のみ（レイアウトの JSON の任意キー `key_display_names`・config.json の任意キー `keyboard_window_widths`。既存キーの削除・意味変更なし）。**

- 起票元: ユーザー要望（2026-10-25・最小まで縮めたキーボードUIでキー名が単語の途中で折り返す・JIS だけ大きいまま縮まらない）。
- 主入力（暫定仕様）: [52_keyboard_ui_key_labels.md](../../history/52_keyboard_ui_key_labels.md)（v0.4・ユーザー確定済）
- モード: **暫定仕様先行モード**。番号対応: phase 69 / 暫定 52 / decisions 69。

## 確定（ユーザー 2026-10-25）

- 文字はキーの幅に合わせて縮め、`\n` 以外では折り返さない。余白 1px・下限 主 7px / 下 6px（暫定 52 §2-1・§2-6・§3）
- 改行は `label`（と表の値）の `\n`（§2-2）
- 送信先の表示名はレイアウトの JSON の最上位の `key_display_names`（§2-3・§4）
- 最小 = `w = 1.0` のキー 27px。下限の上限なし・小さいレイアウトの追加の下限なし（§2-4・§2-7・§2-9・§5）
- 開く大きさ = 最小。変えた幅をレイアウトごとに `keyboard_window_widths` へ記録して次はその幅で開く。位置は記録しない（§2-8・§8）
- 見本 `config/user/keylayout/us_tkl.json`（`us_tkl_sample`・空の表）・jis.json に表の例と `label` の改行。内蔵の US TKL に表は持たせない（§2-5・§2-9・§6）

## スコープ

### 含む

- レイアウトの JSON の `key_display_names` の読込と見本（us_tkl.json 新規・jis.json）（§4・§6）
- キーの文字合わせ・縦の配置・送信先の表示名（§3・§4.2）
- レイアウトごとの最小サイズとレイアウトの切替（§5）
- 窓の幅の記録（§8）
- 実機目視・正本反映（§11）・暫定 52 の凍結

### 含まない（後送り）

- キーボードUI以外のキー名の表示（タイトル・ステータスバー・一覧）/ トリガー・`KM<n>`・`MODE`・`STOP` の文言 / 文字の色・フォントの種類 / 多言語化（暫定 52 §10）
- 窓の位置の記録

## このフェーズで読むファイル

1. 主入力: `instructions/history/52_keyboard_ui_key_labels.md`（各タスクは担当の節と §2 だけ読む）
2. `keyseq/presentation/keyboard_layouts.py`（:10-35 データ型・:38-134 内蔵の US TKL・:137-262 読込の検証）
3. `keyseq/presentation/keyboard_window.py`（:69-141 生成・レイアウトの更新 / :142-206 表示の対応 / :228-353 縦横比の補正 / :357-433 描画）・`keyseq/presentation/keyboard_window_size.py`・`tests/test_keyboard_window_size.py`
4. `config/user/keylayout/jis.json`・`tests/test_keyboard_layout_files.py`
5. task_04 のみ: `keyseq/presentation/controllers/config_io/startup_io.py`・`compact_window_size` の読込・書き込みの経路（`keyseq/presentation/compact_window_size.py`・`controllers/compact_window_controller.py:73,125`・`data_schema.md` §5.4・`features.md` §4.6「簡易表示のウィンドウ」）・キーボードUIを開く側（`controllers/layout_controller.py:60` の `KeyboardWindow(` 生成）・`tests_ui/test_keymap_set_history_flow.py:17-34`（実 `config/` を汚さない手法）
6. 正本反映（最終タスク）: 暫定 52 §11 の列挙

## タスク

- task_01: レイアウトの JSON の `key_display_names` の読込・検証（§4.1）と見本（us_tkl.json 新規・jis.json の表の例と `label` の `\n`）・内蔵と見本の行の一致の検査（§6）・tests
- task_02: キーの文字合わせ（px 指定・`\n` の行分け・収まるまで縮める・下限優先・縦の配置）と送信先の表示名（§3・§4.2）・tests / tests_ui
- task_03: レイアウトごとの最小サイズ（27px 基準・`minimum_size` / `corrected_size` の引数）とレイアウトの切替の当て直し（§5）・tests / tests_ui
- task_04: 窓の幅の記録（`keyboard_window_widths` の読込・開く大きさ・書き込み契機・自分が当てた大きさでは書かない）（§8）・tests / tests_ui
- task_05: 統合確認（tests / tests_ui / smoke）・統合レビュー（deep-reviewer + codex-reviewer）
- task_06: 実機目視・正本反映（§11）・暫定 52 凍結・`decisions_archive/69_keyboard_ui_key_labels.md`・decisions.md の索引・current.md の完了記載・`/refactor_check`・完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- task_01: 既存の JSON（表なし）の読込が変わらないか / 検証の規則が §4.1 どおりか / us_tkl.json が内蔵と完全に一致するか
- task_02: `create_text` に `width` が渡っていないか / フォントが px 指定（負の値）か / 下限が上限より優先されるか / 測り直しの規則 / 表示名を使う範囲がキー置換の枠だけか
- task_03・04: 縦横比の補正（phase 55）の既存の規則を壊していないか / 自分が当てた大きさで書かないか / 最大化・最小化中 / config.json の書き手を増やしていないか（`StartupIo.write_startup` 経由）/ tests_ui が実 `config/` を汚さないか
