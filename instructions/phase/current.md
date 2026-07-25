# Current Phase

このファイルは、現在どのフェーズ定義を読むべきかを示すためのルーティングファイルです。
**完了フェーズの要約はここに蓄積しない**（`.claude_data/state/decisions.md`「アーカイブ索引」+
`decisions_archive/<phase>.md` が正）。

## 現在の参照先

- **アクティブ: [04_config_io_controller_split](04_config_io_controller_split/phase.md)**（2026-07-23 起票）。
  `config_io_controller.py`（598 行）を `controllers/config_io/` 配下の 6 モジュールへ分割する（**挙動不変**）。
  - 主入力（設計の正）: [暫定仕様 03](../history/03_config_io_controller_split.md)（v0.4・ユーザー確定済）
  - 番号対応: phase 04 / 暫定 03 / decisions 04
  - 起票元: ユーザー要望（2026-07-23）。下記「別タスク化候補」の 598 行の項目
  - 派生 idea: [idea_05](../backlog/idea_05_trigger_set_source_path_inconsistency.md)（本フェーズ完了後に着手）/
    [idea_06](../backlog/idea_06_individual_json_io_unification.md)（保留）
  - 進捗: **task_01・02（特性テスト 19+35件）+ task_03（D/E/F 分割）+ task_04（A/B/C 分割）完了**
    （2026-07-24・挙動不変・reviewer 採用・codex-reviewer clear）。ConfigIoController は 114 行の完全ファサード化。
    特性テストは task_03=境界 mock / task_04=アクセサ切替で調整（判断は decisions 04・タスクごとに最適手段を選択）。
    次は **task_05（呼び出し元30箇所差し替え・案B + 委譲層削除）→ task_06（正本反映＋実機目視ゲート）**。
- 直前の完了フェーズ: `03_startup_font_settings_cleanup`（2026-07-20 完了）。起動設定/フォント3メソッドを整理し
  4 負債（責務混在・controller→App private 逆参照・初期化順序制約・ui_vars 直読み）を挙動不変で解消。
  要約・判断は [decisions_archive/03_startup_font_settings_cleanup.md](../../.claude_data/state/decisions_archive/03_startup_font_settings_cleanup.md) が正。
- 一つ前の完了フェーズ: `02_hotkey_validation`（2026-07-18 完了）。hotkey 検証を presentation →
  domain / application へ層移設し**層の逆転を解消**（挙動不変）。
  要約・判断は [decisions_archive/02_hotkey_validation.md](../../.claude_data/state/decisions_archive/02_hotkey_validation.md) が正。
- テンプレート導入前の経緯・過去仕様は `instructions/history/archive/` を参照（凍結済み）。
  過去のリファクタ計画・提案書（01〜04）は `instructions/modified_proposal/`（次採番 05）。
  計画04 は完了済（W0〜W7・手動確認まで完了）。

## 次採番

- 次フェーズは **`05_<topic>`**（欠番が出た場合はここに明記し、再利用しない）。
- 暫定仕様（`instructions/history/NN_<topic>.md`）はフェーズとは**独立採番**。次採番は **`04_<topic>`**。

## 次フェーズ候補（参考）

（`instructions/backlog/INDEX.md` の idea から着手候補を 1〜3 件リンクする）

計画04 の次期課題は「後始末 → hotkey検証 → 起動設定/フォント」の順で進める方針
（3フェーズに分割。1件1フェーズにはしない）。**1〜3 すべて着手済**:

1. ~~後始末~~ → **完了**（`01_view_ref_cleanup`・2026-07-17）
2. ~~[idea_01](../backlog/idea_01_hotkey_validation_to_domain.md)~~ → **完了**（`02_hotkey_validation`・2026-07-18）
3. ~~[idea_02](../backlog/idea_02_startup_font_settings_cleanup.md)~~ → **完了**（`03_startup_font_settings_cleanup`・2026-07-20）

**計画04 由来の3フェーズはすべて完了**。現在は phase 04（計画04 由来ではない・別タスク化候補からの着手）。
phase 04 完了後の候補:
- [idea_05](../backlog/idea_05_trigger_set_source_path_inconsistency.md)（trigger_set の source_path 不整合。
  **phase 04 の完了が着手条件**・挙動変更を伴うため仕様変更フロー）。
- [idea_03](../backlog/idea_03_action_hotkey_save_normalization.md)（アクション hotkey の保存時正規化/検証の統一。
  phase 02 task_04 から分離・優先度低・要設計）。
- [idea_04](../backlog/idea_04_font_settings_controller.md)（FontSettingsController 新設 = phase 03 の案B。
  2026-07-23 に idea 化済）**状態は保留**。着手トリガー（idea_04 に 5 件明記）が発生するまで着手しない。
  着手時は初期化順序設計の暫定仕様が先に必要（判断は decisions_archive/03）。

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
- ~~`controllers/config_io_controller.py` が **598 行**で目安 600 行に接近~~ →
  **[04_config_io_controller_split](04_config_io_controller_split/phase.md) として着手**（2026-07-23・ユーザー判断）。
  `/refactor_check` の再判定を待たず独立した設計タスクとした（M1・M3 非該当。根拠は
  [暫定仕様 03](../history/03_config_io_controller_split.md)「着手根拠」）。
- [idea_06](../backlog/idea_06_individual_json_io_unification.md)（個別 JSON IO 3 種の共通化）は
  **保留**。着手条件は phase 04 完了 + [idea_05](../backlog/idea_05_trigger_set_source_path_inconsistency.md)
  の解消 + 共通化の実需（3 条件すべて）。

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
