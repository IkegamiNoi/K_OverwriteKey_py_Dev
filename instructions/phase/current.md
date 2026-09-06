# Current Phase

このファイルは、現在どのフェーズ定義を読むべきかを示すためのルーティングファイルです。
**完了フェーズの要約はここに蓄積しない**（`.claude_data/state/decisions.md`「アーカイブ索引」+
`decisions_archive/<phase>.md` が正）。

## 現在の参照先

- **アクティブなフェーズ: [11_orphan_child_file_sweep](11_orphan_child_file_sweep/phase.md)**
  （**孤児ファイルの棚卸し**・2026-09-06 起票）。
  主入力 = [暫定仕様 10](../history/10_orphan_child_file_sweep.md)（**v0.4・ユーザー確定済**）。
  モード: **暫定仕様先行**。番号対応: **phase 11 / 暫定 10 / decisions_archive 11**。
  起票元 = [idea_12](../backlog/idea_12_orphan_child_file_sweep.md)。
  到達範囲 = **検出 + 隔離 + 復元 + 隔離済みの削除**（削除は `<config_root>/quarantine/` 内のみ）。
  **本アプリ初のディレクトリ走査かつ初のファイル削除機能**。判断は `decisions.md` の phase 11 節。
- 直前の完了フェーズ: [10_reference_link_cleanup](../../.claude_data/state/decisions_archive/10_reference_link_cleanup.md)
  （**2026-09-05 完了**・参照元の掃除。暫定仕様 09 は**凍結済**。正本 `data_schema.md` §5.8.1 +
  `features.md` §4.6 + `codebase_map.md` へ昇格済）。
- 提案書 [07_refactor_per_keymap_set_presets](../modified_proposal/07_refactor_per_keymap_set_presets.md) は
  **「計画07」として実施し完了**（2026-08-16・項目 0〜3・**挙動不変**）。
  **フェーズ番号は消費していない**ため対応表は不変。判断は `decisions.md` の「計画07」節。
  成果 = `dialogs.py`（1026 行）を `dialogs/` **7 ファイル**へ分割 /
  `PresetManagerDialog.__init__` 99 → 8 行 / 直値の定数化 / 特性テスト **6 本追加**（`tests_ui` 229）。
  **完了フェーズの要約は本ファイルに置かない**。経緯・判断は `.claude_data/state/decisions.md`「アーカイブ索引」
  → `decisions_archive/<phase>.md` が正。
- 提案書 [06_refactor_hook_key_pair_enumeration](../modified_proposal/06_refactor_hook_key_pair_enumeration.md) は
  **「計画06」として実施し完了**（2026-08-06・項目 0 / 1。**(b) 次フェーズ前の独立ミニ計画**）。
  **フェーズ番号は消費していない**ため対応表は不変（γ=phase 07〔完了〕/ プリセット=phase 08〔完了〕）。
  判断は `decisions.md` の「計画06」節。
- 提案書 [05_refactor_child_file_save_dialog](../modified_proposal/05_refactor_child_file_save_dialog.md) は
  **「計画05」として実施し完了**（2026-08-03・項目 0 / 1 / 2）。フェーズ番号は消費していない。
  判断は `decisions.md` の「計画05」節。
- テンプレート導入前の経緯・過去仕様は `instructions/history/archive/` を参照（凍結済み）。
  過去のリファクタ計画・提案書（01〜07）は `instructions/modified_proposal/`（次採番は「次採番」節が正）。
  計画04 は完了済（W0〜W7・手動確認まで完了）。

## 次採番

- **phase 11 が進行中**。次フェーズは **`12_<topic>`**（欠番が出た場合はここに明記し、再利用しない）。
  保存系リデザインの予定: **β=phase 06〔完了〕/ γ=phase 07〔完了〕/ プリセット=phase 08〔完了〕**。
  → **保存系リデザインは一巡完了**。その派生 = **phase 09〔完了〕**（idea_08）。
- 暫定仕様（`instructions/history/NN_<topic>.md`）はフェーズとは**独立採番**。
  04〜10 は起票済（04=α / 05=β / 06=γ〔凍結〕/ 07=プリセット〔凍結〕/
  08=個別プリセット〔**v0.10・凍結**〕/ 09=参照元の掃除〔**v0.5・凍結**〕/
  10=孤児ファイルの棚卸し〔**v0.4・未凍結・phase 11 の主入力**〕）。
  次採番は **`11_<topic>`**。
- リファクタ提案書（`instructions/modified_proposal/NN_*.md`）も独立採番。**07 まで起票済**
  （07 = phase 09 の `/refactor_check` 由来・**実施済＝計画07**）・次採番は **`08_<topic>`**。

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
**γ = phase 07 も完了**（暫定 06・2026-08-05）。**プリセット = phase 08 も完了**（暫定 07・2026-08-09）。
**個別プリセット = phase 09 も完了**（暫定 08・2026-08-16）。
**参照元の掃除 = phase 10 も完了**（暫定 09・2026-09-05）。
次フェーズの候補:
- ~~[idea_08](../backlog/idea_08_per_keymap_set_preset_ownership.md)（keymap_set ごとの個別プリセット）~~
  → **完了**（phase 09・2026-08-16。判断は
  [decisions_archive/09](../../.claude_data/state/decisions_archive/09_per_keymap_set_presets.md)）。
- [idea_10](../backlog/idea_10_nested_modal_grab_restore.md)（**ネストしたモーダルの grab 復元**。
  モーダル中のモーダルを閉じると親の grab が戻らず、ダイアログを開いたままメインを操作できる。
  **既存の「追加」「編集」も同じ挙動**＝アプリ全体の課題として phase 09 から分離・**未着手**）。
- ~~[idea_07](../backlog/idea_07_reference_link_cleanup.md)（参照元の掃除）~~
  → **完了**（phase 10・2026-09-05。判断は
  [decisions_archive/10](../../.claude_data/state/decisions_archive/10_reference_link_cleanup.md)）。
- ~~[idea_12](../backlog/idea_12_orphan_child_file_sweep.md)（全走査 + 孤児候補の検出＝逆方向検査）~~
  → **着手**（phase 11・2026-09-06 起票）。
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
    - **phase 10 で追記（2026-09-05）**: 定数の**使用ファイル数は 8 のまま不変**だが、phase 10 の新規 2 ファイル
      （`config_service/parent_refs_cleanup.py` / `presentation/reference_cleanup_text.py`）が
      **`save_plan.CHILD_*` を import せず同値の文字列直値**を使っている（M6 候補）。
      `/refactor_check` は**この既知領域として抑止**し「不要」に倒した。まとめて触るときはここも対象にする
  - `child_save_dialog.py` が **370 行**（600 行未満で M1 非該当だが実装目安 300 行超）+
    `_add_text_cell` の戻り値が素の dict
  - `dirty_tracker.trigger_set_imported` が**読み手不在の残置状態**
  - slugify 後に別々の keymap_set 名が**同一 stem へ丸まる衝突**（受入条件 8 の範囲外）
  - `keymap_set_io.save_keymap_set_to` が **46 行**（計画05 項目 2 の対象外・無変更。
    同ファイルの他メソッドは 40 行以内に収まった）
- **Phase γ の `/refactor_check` からの候補送り**（提案書
  [06_refactor_hook_key_pair_enumeration](../modified_proposal/06_refactor_hook_key_pair_enumeration.md) に入れなかった分）:
  - ~~**runtime を新規化・置換する入口が 4 経路**（`new_config` / `restore_default` / Import /
    起動時の空データフォールバック）あり、各所で `apply_global_hook_key_defaults` を呼ぶ規約~~
    → **phase 08 が引き取り**（2026-08-06 ユーザー判断）。暫定仕様 07 **§4 検討事項 A** として起票し、
    **task_03 で設計・確定する**。ここでの追跡は終了
- **Phase 08（プリセット案2）の `/refactor_check` からの候補送り**（判定は**不要**。次フェーズ以降の再判定用）:
  - `config_io/` の **`try/except Exception → messagebox.showerror → return False` が 14 箇所**に増えた
    （`hotkey_presets_io` の追加で +1）。各箇所はメッセージ・保存対象が独立のため M3 非該当に倒したが、
    さらに増えるなら共通化の再検討対象（近接領域を [idea_06](../backlog/idea_06_individual_json_io_unification.md) がカバー）
  - `keyseq/application/config_service/__init__.py` が **599 行**で目安 600 行に接近
    （本フェーズの増分は +30。M1 は「600 行超 かつ +100 行以上」のため非該当）
- **Phase 09（個別プリセット）の `/refactor_check` からの候補送り**（判定は**推奨** →
  提案書 [07_refactor_per_keymap_set_presets](../modified_proposal/07_refactor_per_keymap_set_presets.md)・
  **計画07 として実施し完了**。上位 3 項目に入らなかった分）:
  - `keyseq/application/config_service/__init__.py` が **767 行**（phase 10 で +32。phase 09 時点は 734 行）。
    **phase 09 で M1 該当**（当時 +135）。**phase 10 では M1 非該当**（増分が閾値未満）だが**分割は保留のまま**。
    ただし**テストが `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を
    差し替えるため `ConfigService` 本体とパス基盤メソッドを動かせない**制約があり、分割方針の
    設計判断が別途必要。実ロジックを持つのは `relocate_individual_hotkey_presets`（約 40 行）で、
    他はほぼ 1 行委譲。**次フェーズ以降に再判定する**
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
