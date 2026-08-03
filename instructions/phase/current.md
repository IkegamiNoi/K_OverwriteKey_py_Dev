# Current Phase

このファイルは、現在どのフェーズ定義を読むべきかを示すためのルーティングファイルです。
**完了フェーズの要約はここに蓄積しない**（`.claude_data/state/decisions.md`「アーカイブ索引」+
`decisions_archive/<phase>.md` が正）。

## 現在の参照先

- **アクティブなフェーズ**: [07_hook_keys_global_default](07_hook_keys_global_default/phase.md)
  （**2026-08-03 起票**・保存系リデザイン **Phase γ**）。
  停止/トグルキーの全体デフォルトを `config/config.json` に持たせ、keymap_set 側のチェックで
  個別指定できるようにする（**挙動変更・スキーマ追加あり / 後方互換必須**）。
  - 主入力（確定設計）: [暫定仕様 06](../history/06_hook_keys_global_default.md)（v0.2・ユーザー確定済 2026-07-27）
  - モード: **暫定仕様先行モード**。番号対応: **phase 07 / 暫定 06 / decisions_archive 07**
  - 起票元: ユーザー要望（2026-07-26〜27・保存系統の改善討議・点5）
  - 判断履歴: `.claude_data/state/decisions.md`（フェーズ末に
    `decisions_archive/07_hook_keys_global_default.md` へ集約）
  - **進捗**: task_01（スキーマ/移行判定）・task_02（キー解決点）・task_03（保存時挙動）・
    task_04（全体デフォルト更新 API）・task_05（チェック UI）・task_06（所有者切替 capture）・
    task_06b（表示切替と個別値の保持）・task_07b（レビュー指摘 A〜D の是正）**完了**
    （task_06 は 06 / 06b へ分割）。
    **task_07（統合確認）は実施中 = 自動確認とレビューは完了・実機目視 G1〜G9 のみユーザー待ち**。
    その後 **task_08（正本反映）**
- 保存系リデザインの残り: γ の次は **プリセット = phase 08
  （[暫定仕様 07](../history/07_hotkey_presets_global.md)・確定済）**。
- 直前の完了フェーズ: [06_child_file_save_dialog](../../.claude_data/state/decisions_archive/06_child_file_save_dialog.md)
  （**2026-08-03 完了**・保存系リデザイン **Phase β**）。
  **完了フェーズの要約は本ファイルに置かない**。経緯・判断は `.claude_data/state/decisions.md`「アーカイブ索引」
  → `decisions_archive/<phase>.md` が正。
- 提案書 [05_refactor_child_file_save_dialog](../modified_proposal/05_refactor_child_file_save_dialog.md) は
  **「計画05」として実施し完了**（2026-08-03・項目 0 / 1 / 2）。フェーズ番号は消費していない。
  判断は `decisions.md` の「計画05」節。
- テンプレート導入前の経緯・過去仕様は `instructions/history/archive/` を参照（凍結済み）。
  過去のリファクタ計画・提案書（01〜05）は `instructions/modified_proposal/`（次採番 06）。
  計画04 は完了済（W0〜W7・手動確認まで完了）。

## 次採番

- 次フェーズは **`08_<topic>`**（欠番が出た場合はここに明記し、再利用しない）。
  保存系リデザインの予定: **β=phase 06〔完了〕/ γ=phase 07〔着手中〕/ プリセット=phase 08**。
- 暫定仕様（`instructions/history/NN_<topic>.md`）はフェーズとは**独立採番**。
  04〜07 は起票済（04=α / 05=β / 06=γ / 07=プリセット）。次採番は **`08_<topic>`**。
- リファクタ提案書（`instructions/modified_proposal/NN_*.md`）も独立採番。05 まで起票済・次採番は **`06_<topic>`**。

## 次フェーズ候補（参考）

（`instructions/backlog/INDEX.md` の idea から着手候補を 1〜3 件リンクする）

計画04 の次期課題は「後始末 → hotkey検証 → 起動設定/フォント」の順で進める方針
（3フェーズに分割。1件1フェーズにはしない）。**1〜3 すべて着手済**:

1. ~~後始末~~ → **完了**（`01_view_ref_cleanup`・2026-07-17）
2. ~~[idea_01](../backlog/idea_01_hotkey_validation_to_domain.md)~~ → **完了**（`02_hotkey_validation`・2026-07-18）
3. ~~[idea_02](../backlog/idea_02_startup_font_settings_cleanup.md)~~ → **完了**（`03_startup_font_settings_cleanup`・2026-07-20）

**計画04 由来の3フェーズはすべて完了**。`04_config_io_controller_split`（2026-07-26）・
`05_keymap_set_new_and_default_dir`（Phase α・2026-07-28）も完了。
**保存系リデザインの Phase β も完了**（phase 06 / 暫定 05・2026-08-03）。
**γ = phase 07 は着手中**（上記「現在の参照先」）。γ の次以降の候補:
- **保存系リデザインの続き（推奨）**: プリセット = phase 08
  （[暫定仕様 07](../history/07_hotkey_presets_global.md)・確定済）。
- [idea_07](../backlog/idea_07_reference_link_cleanup.md)（参照元の掃除。**β 完了で前提充足・着手可**。
  孤児 trigger_set と陳腐化した `_parent_refs` を回収する保守機能）。
- [idea_09](../backlog/idea_09_legacy_settings_save_path_fallback.md)（別名保存でレガシー `settings/` 配下を選ぶと
  `default.json` へ無言フォールバックする残存経路。Phase α の deep-reviewer 指摘2 から分離・**優先度低**・
  着手時は仕様変更フロー必須）。
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
  **保留**。着手条件は phase 04 完了（**充足・2026-07-26**）+ [idea_05](../backlog/idea_05_trigger_set_source_path_inconsistency.md)
  の解消（**充足・2026-08-02 / Phase β**）+ 共通化の実需（**残りはこの 1 条件のみ**）。
  Phase β の `/refactor_check` で M3（source_path 変化判定 + 追随メッセージが 3 ファイルに同型）に
  該当したが、**idea_06 がカバーする既知領域**のため提案書には含めていない。
- **Phase β の `/refactor_check` からの候補送り**（提案書
  [05_refactor_child_file_save_dialog](../modified_proposal/05_refactor_child_file_save_dialog.md) の上位 3 項目に入らなかった分）:
  - M4 の子カテゴリ列挙（`CHILD_KEYMAP` / `CHILD_TRIGGER_SET` / `CHILD_SEQUENCE` が 5 ファイルに散在。
    子の種類は仕様上 3 種で固定のため**優先度低**）
  - `child_save_dialog.py` が **370 行**（600 行未満で M1 非該当だが実装目安 300 行超）+
    `_add_text_cell` の戻り値が素の dict
  - `dirty_tracker.trigger_set_imported` が**読み手不在の残置状態**
  - slugify 後に別々の keymap_set 名が**同一 stem へ丸まる衝突**（受入条件 8 の範囲外）
  - `keymap_set_io.save_keymap_set_to` が **46 行**（計画05 項目 2 の対象外・無変更。
    同ファイルの他メソッドは 40 行以内に収まった）
- `app.py:64` の `keymap_set_path = resolve_keymap_set_path()` 初期化と、それが使う
  `config_paths.resolve_keymap_set_path()` の**引数なし分岐が実質デッド**（起動時に `load_startup_and_config` が
  必ず上書きするため）。**据え置き**（phase 05 の deep-reviewer 指摘3・実害なし）。
  同指摘4（`DEFAULT_KEYMAP_SET_FILENAME` を ConfigPaths 側へ寄せれば `save_as` の分岐が不要になる代替案）も
  挙動同値のため据え置き。まとめて触りたくなった時のみ単独タスク化する
  （判断根拠は [decisions_archive/05](../../.claude_data/state/decisions_archive/05_keymap_set_new_and_default_dir.md)）

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
