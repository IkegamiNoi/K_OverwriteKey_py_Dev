# Current Phase

このファイルは、現在どのフェーズ定義を読むべきかを示すためのルーティングファイルです。
**完了フェーズの要約はここに蓄積しない**（`.claude_data/state/decisions.md`「アーカイブ索引」+
`decisions_archive/<phase>.md` が正）。

## 現在の参照先

- **[01_view_ref_cleanup](01_view_ref_cleanup/phase.md)** — View 参照の後始末。
  計画04 で意図的に残した残存参照 2 件（`views/status_bar.py` の生やし / View の `trigger_list` alias）を解消する。
  presentation のみ・スキーマ変更なし・**挙動不変**。
  - モード: **直接改訂モード**（仕様変更なし・暫定仕様なし）。番号対応: phase 01 / 暫定 なし /
    判断は `.claude_data/state/decisions.md` → 完了時 `decisions_archive/01_view_ref_cleanup.md`。
  - 起票元: ユーザー要望（2026-07-17）+ 本ファイル「別タスク化候補」（計画04 W7 の残課題のうち機械的なもの）。
- テンプレート導入前の経緯・過去仕様は `instructions/history/archive/` を参照（凍結済み）。
  過去のリファクタ計画・提案書（01〜04）は `instructions/modified_proposal/`（次採番 05）。
  計画04 は完了済（W0〜W7・手動確認まで完了）。

## 次採番

- 次フェーズは **`02_<topic>`**（欠番が出た場合はここに明記し、再利用しない）。

## 次フェーズ候補（参考）

（`instructions/backlog/INDEX.md` の idea から着手候補を 1〜3 件リンクする）

計画04 の次期課題は「後始末 → hotkey検証 → 起動設定/フォント」の順で進める方針
（3フェーズに分割。1件1フェーズにはしない）:

1. **後始末**（次に着手）— `views/status_bar.py` の生やし + View の `trigger_list` alias 解消。
   計画04 W5/W6 のやり残し。挙動不変・機械的。下記「別タスク化候補」参照
2. [idea_01](../backlog/idea_01_hotkey_validation_to_domain.md) — hotkey 検証を domain へ（設計判断あり。`/spec_draft` 推奨）
3. [idea_02](../backlog/idea_02_startup_font_settings_cleanup.md) — 起動設定/フォント クラスタ（初期化順序の解決が前提）

## 別タスク化候補

（継続保留、ソース変更を伴う細かい負債。`/refactor_check` からの追記先もここ）

計画04 W7 の次期課題（app.py の「どの責務分類にも属さない残留ロジック」。app.py は 489 行で目安 300 行を超過）
のうち、設計判断を伴う 2 クラスタは idea へ移した →
[idea_01](../backlog/idea_01_hotkey_validation_to_domain.md) / [idea_02](../backlog/idea_02_startup_font_settings_cleanup.md)。
以下は残る機械的な後始末（次フェーズ候補 1「後始末」の中身）:

- 計画04 W5 の対象外で残存した生やし: `views/status_bar.py:6,10` の `app.runtime_status_frame` /
  `app.status_bar`。**grep 済: この 2 つは `build_status_area` 内でしか使われておらず読み手なし**
  （W5 で処理した write-only 生やしと同型）→ ローカル変数化するだけで解消
- 計画04 の暫定措置: View の `trigger_list` alias（`full_view.py` / `compact_view.py` の
  `self.trigger_list = self.trigger_box.trigger_list`）は tests_ui が `app.<view>.trigger_list` を
  参照するため残置中。**W5 で `keymap_listbox` の参照経路を変更した前例あり**（アサーション不変なら
  参照経路の変更は可）→ tests_ui を `app.full_view.trigger_box.trigger_list` へ変えれば alias を削除できる

## 作業開始時の指示

Claude は作業開始時に、このファイルで指定された参照先の `phase.md` を必ず読んでください。
次フェーズ未確定時はユーザーに方針確認すること。

## フェーズ完了時の指示

- 正本反映タスクの完了後、フェーズを完了扱いにする前に `/refactor_check`
  （`.claude/commands/refactor_check.md`）を実行し、リファクタ要否の判定結果を完了報告に含めること。
- フェーズ完了時は本ファイルの「現在の参照先」を差し替え、**旧フェーズの要約行は削除する**
  （要約は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` へ集約。ここに残さない）。

起票元 idea があるフェーズは、`instructions/backlog/INDEX.md` の該当行を完了 / クローズ状態に
更新して `instructions/backlog/INDEX_done.md` へ移動すること
（チェックリストは `.claude/rules/task_execution.md`「フェーズ完了時」）。

## 新フェーズ作成時の更新ルール

新しいフェーズ用フォルダを作成した場合は、`## 現在の参照先` を新フェーズの `phase.md` に更新してください。
フォルダ名は `instructions/phase/` 直下で**連番プレフィックス付き**（`NN_<topic>`）にしてください。
起票手順は `/phase_start`（`.claude/commands/phase_start.md`）に従うこと。

## 注意

このファイルには、実装順序・タスク詳細・チェック内容・完了フェーズの経緯を書かないでください。
それらは各フェーズフォルダ内の `phase.md` および `decisions_archive/<phase>.md` に記載してください。
