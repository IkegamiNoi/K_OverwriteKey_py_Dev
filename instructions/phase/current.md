# Current Phase

このファイルは、現在どのフェーズ定義を読むべきかを示すためのルーティングファイルです。
**完了フェーズの要約はここに蓄積しない**（`.claude_data/state/decisions.md`「アーカイブ索引」+
`decisions_archive/<phase>.md` が正）。

## 現在の参照先

- **[03_startup_font_settings_cleanup](03_startup_font_settings_cleanup/phase.md)** — 起動設定 / フォント設定クラスタの整理。
  App の起動設定読込・フォント設定 3 メソッド（`_coerce_font_delta` / `_load_startup_settings` / `set_ui_font_delta`）を
  整理し、責務混在・controller → App private 逆参照・初期化順序の制約・ui_vars の App private 依存を解消する。
  **presentation 内の再編に限定・スキーマ変更なし・挙動不変**。
  - モード: **暫定仕様先行モード**。主入力 = [暫定仕様 02](../history/02_startup_font_settings_cleanup.md)（v1.0・ユーザー確定済）。
    番号対応: phase 03 / 暫定 02 / decisions `decisions_archive/03_startup_font_settings_cleanup.md`。
  - 起票元: [idea_02](../backlog/idea_02_startup_font_settings_cleanup.md)。
- 直前の完了フェーズ: `02_hotkey_validation`（2026-07-18 完了）。hotkey 検証を presentation →
  domain / application へ層移設し**層の逆転を解消**（挙動不変）。
  要約・判断は [decisions_archive/02_hotkey_validation.md](../../.claude_data/state/decisions_archive/02_hotkey_validation.md) が正。
- 一つ前の完了フェーズ: `01_view_ref_cleanup`（2026-07-17 完了）。
  要約・判断は [decisions_archive/01_view_ref_cleanup.md](../../.claude_data/state/decisions_archive/01_view_ref_cleanup.md) が正。
- テンプレート導入前の経緯・過去仕様は `instructions/history/archive/` を参照（凍結済み）。
  過去のリファクタ計画・提案書（01〜04）は `instructions/modified_proposal/`（次採番 05）。
  計画04 は完了済（W0〜W7・手動確認まで完了）。

## 次採番

- 次フェーズは **`04_<topic>`**（欠番が出た場合はここに明記し、再利用しない）。
- 暫定仕様（`instructions/history/NN_<topic>.md`）はフェーズとは**独立採番**。次採番は **`03_<topic>`**。

## 次フェーズ候補（参考）

（`instructions/backlog/INDEX.md` の idea から着手候補を 1〜3 件リンクする）

計画04 の次期課題は「後始末 → hotkey検証 → 起動設定/フォント」の順で進める方針
（3フェーズに分割。1件1フェーズにはしない）。**1〜3 すべて着手済**:

1. ~~後始末~~ → **完了**（`01_view_ref_cleanup`・2026-07-17）
2. ~~[idea_01](../backlog/idea_01_hotkey_validation_to_domain.md)~~ → **完了**（`02_hotkey_validation`・2026-07-18）
3. ~~[idea_02](../backlog/idea_02_startup_font_settings_cleanup.md)~~ → **着手中**（`03_startup_font_settings_cleanup`・上記「現在の参照先」）

その他の未着手 idea: [idea_03](../backlog/idea_03_action_hotkey_save_normalization.md)（アクション hotkey の
保存時正規化/検証の統一。phase 02 task_04 から分離・優先度低・要設計）。

## 別タスク化候補

（継続保留、ソース変更を伴う細かい負債。`/refactor_check` からの追記先もここ）

計画04 W7 の次期課題（app.py の「どの責務分類にも属さない残留ロジック」。app.py は 489 行で目安 300 行を超過）
のうち、設計判断を伴う 2 クラスタは idea へ移した →
[idea_01](../backlog/idea_01_hotkey_validation_to_domain.md) / [idea_02](../backlog/idea_02_startup_font_settings_cleanup.md)。
機械的な後始末 2 件（`views/status_bar.py` の生やし / View の `trigger_list` alias）は
**`01_view_ref_cleanup` で解消済**（2026-07-17）。

- `action_list` alias（`full_view.py` の `self.action_list = self.sequence_box.action_list`）は**据え置き中**。
  `trigger_list` と違い production（`controllers/trigger_panel_controller.py`）が
  `app.full_view.action_list` を実際に使う**生きた参照経路**であり、計画04 §1.3-2 の
  「App → View → Widget のパス」を満たすため。所有 Widget 経由（`full_view.sequence_box.action_list`）へ
  統一したくなった場合のみ単独タスク化する（判断根拠は
  [decisions_archive/01_view_ref_cleanup.md](../../.claude_data/state/decisions_archive/01_view_ref_cleanup.md)）

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
