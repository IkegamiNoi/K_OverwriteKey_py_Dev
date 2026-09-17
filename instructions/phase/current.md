# Current Phase

このファイルは、現在どのフェーズ定義を読むべきかを示すためのルーティングファイルです。
**完了フェーズの要約はここに蓄積しない**（`.claude_data/state/decisions.md`「アーカイブ索引」+
`decisions_archive/<phase>.md` が正）。**例外は「直近の一連の作業が扱っている領域」の数行のみ**
（「フェーズ完了時の指示」節を参照）。

## 現在の参照先

- **アクティブなフェーズ: なし**（phase 20 は 2026-09-18 完了。次フェーズは未起票 = ユーザーに方針確認）。
- **直近の一連の作業が扱っている領域 = フル表示のウィンドウサイズ（幅配分・境界線ドラッグ・幅の保存と復元・ヘッダの幅・縦方向の最小サイズ）**。
  正本は `features.md` §4.6「フル表示の幅配分」/ `data_schema.md` §5.4（`full_view_pane_widths` / `full_view_window_width`）/
  `codebase_map.md` の `controllers/pane_layout/`・`pane_width_rules.py`・`button_width_rules.py`・`controllers/button_width.py`・`hook_button_texts.py`。暫定仕様 16・17・18 は凍結。
  **ウィンドウ最小幅 = max(メイン, ヘッダの要求幅〔ウィンドウ幅換算〕)** / ウィンドウ幅はリサイズ後 500ms 間引きで保存・終了時は保存しない /
  旧保存値が最小幅未満なら起動時に広げた幅で更新 / フル表示ヘッダの切替ボタンは最大文言幅で固定 /
  **最小の高さ = 一覧 6 / 6 / 9 行でのウィンドウ要求高さ（一時メッセージは 1 行分）・自動で広げた高さは縮めない・高さは保存しない**。
  **残件** = ①「別タスク化候補」の Phase 18 / 19 / 20 項（refactor_check の境界観察・レビューの保留）
  ②`tests_ui` 実行時の stderr に既存 `_clear_flash_message` の破棄後 `after` 実行が出る（無害・未対応）。
  その前の領域（モーダルダイアログの作法）の残件は [decisions_archive/17](../../.claude_data/state/decisions_archive/17_minimize_grab_custody.md) と
  「別タスク化候補」の Phase 14 / 17 項、[idea_18](../backlog/idea_18_escape_delivery_flaky_test.md)。
- 直前の完了フェーズ: [20_full_view_min_height](../../.claude_data/state/decisions_archive/20_full_view_min_height.md)
- その前の完了フェーズ: [19_full_view_header_width](../../.claude_data/state/decisions_archive/19_full_view_header_width.md)
- その前の完了フェーズ: [18_full_view_resizable_panes](../../.claude_data/state/decisions_archive/18_full_view_resizable_panes.md)
- 提案書 [07_refactor_per_keymap_set_presets](../modified_proposal/07_refactor_per_keymap_set_presets.md) は
  **「計画07」として実施し完了**（2026-08-16・項目 0〜3・**挙動不変**）。
  **フェーズ番号は消費していない**ため対応表は不変。判断は `decisions.md` の「計画07」節。
  成果 = `dialogs.py`（1026 行）を `dialogs/` **7 ファイル**へ分割 /
  `PresetManagerDialog.__init__` 99 → 8 行 / 直値の定数化 / 特性テスト **6 本追加**（`tests_ui` 229）。
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

- **phase 20 は 2026-09-18 完了**（decisions 20 はアーカイブ済・次は decisions 21）。
  次フェーズは **`21_<topic>`**（欠番が出た場合はここに明記し、再利用しない）。
  保存系リデザインの予定: **β=phase 06〔完了〕/ γ=phase 07〔完了〕/ プリセット=phase 08〔完了〕**。
  → **保存系リデザインは一巡完了**。その派生 = **phase 09〔完了〕**（idea_08）。
- 暫定仕様（`instructions/history/NN_<topic>.md`）はフェーズとは**独立採番**。
  04〜18 は起票済（04=α / 05=β / 06=γ〔凍結〕/ 07=プリセット〔凍結〕/
  08=個別プリセット〔**v0.10・凍結**〕/ 09=参照元の掃除〔**v0.5・凍結**〕/
  10=孤児ファイルの棚卸し〔**v0.8・凍結**〕/
  11=config_service の公開面〔**v0.3・凍結**〕/
  12=ネストしたモーダルの grab 復元〔**v0.5・凍結**〕/
  13=ダイアログ後始末の確実な実行〔**v0.4・凍結**〕/
  14=ネストしたダイアログの前面維持〔**v0.5・凍結**〕/
  15=最小化中の grab 預かり〔**v0.7・凍結**〕/
  16=フル表示メイン領域の幅配分〔**v0.5・凍結**〕/
  17=フル表示ヘッダの幅〔**v0.3・凍結**〕/
  18=フル表示の縦方向の最小サイズ〔**v0.5・凍結**〕）。
  次採番は **`19_<topic>`**。
- リファクタ提案書（`instructions/modified_proposal/NN_*.md`）も独立採番。**09 まで起票済**
  （07 = phase 09 の `/refactor_check` 由来・**実施済＝計画07** / 08 = phase 11 由来・**実施済＝計画08** /
  **09 = phase 13 由来・実施済＝計画10**〔`collect_forbidden_refs` を 100 行 → 26 行へ分割〕/
  **10 = phase 19 由来・実施済＝phase 19 task_07**）・
  次採番は **`11_<topic>`**。**「計画09」は提案書を持たない**（`/spec_split` による正本の分割で、
  規範は `.claude/commands/spec_split.md`。**提案書 09 とは別物**）。

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
- ~~[idea_10](../backlog/idea_10_nested_modal_grab_restore.md)（ネストしたモーダルの grab 復元）~~
  → **完了**（phase 14・2026-09-12。判断は
  [decisions_archive/14](../../.claude_data/state/decisions_archive/14_nested_modal_grab_restore.md)）。
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
- **Phase 14（ネストしたモーダルの grab 復元）の `/refactor_check` からの候補送り**（判定は**不要**。
  M1〜M6 いずれも非該当。差分は 13 ファイル・+78/-27 で、**重複を増やす方向ではなく
  `grab_set` / `transient` の 12 箇所を `grab_modal` へ集約する方向**だった）:
  - **ダイアログ同型スケルトンの共通化**は**既知**（本節の phase 11 由来の項目）。**phase 14 で
    `transient` + `grab_set` の部分だけは `grab_modal` へ共通化済**。
    **phase 15 で `destroy()` override〔8 クラス〕は解消**（4 クラスは override ごと削除・
    残る 4 クラスはウィジェットに触る後始末のみ）。**残るのは
    `suspend_hook_for_dialog`〔8 クラス〕/ `bind("<Escape>")` + `protocol("WM_DELETE_WINDOW")`
    〔**3 クラス**で完全同型。`dialogs/` 実測。phase 14 時点の「4 クラス」は誤記〕**。
    合流先だった [idea_16] は **phase 15 で完了**（`INDEX_done.md`）。
  - **静的検査の発見ベース化（`deep-reviewer` の M-6）は保留**。
    `tests_ui/test_nested_modal_grab.py` の `test_grab_modal_is_last_initialization_statement` は
    **9 クラスと系統 B 3 ファイルをハードコードで列挙**しており、**新規ダイアログを守らない**。
    ただし**発見ベース単独にすると「`grab_modal` の呼び出しが消えた」検出が失われる**
    （現在は件数のアサートがそれを守っている）ため、**併用形にするかを含めて再判定が要る**。
    ユーザー判断で保留（2026-09-11）。**テストコードのため `/refactor_check` の対象範囲外**でもある。
- **Phase 17（最小化中の grab 預かり）の `/refactor_check` からの候補送り**（判定は**不要**）:
  `presentation/modal.py`（46 → 120 行）で `grab_current()` の try/except と
  `winfo_exists()` / `winfo_viewable()` の try/except が**それぞれ 3 箇所**になった（M3 の境界）。
  **意図的に意味が違う**ため共通化しない（`grab_modal` は解決不能を「保持者なし」と扱い、預かり側は
  **解決不能と `None` を区別する**〔暫定仕様 15 §3-2(5)〕/ `<Unmap>` は「非表示」、他 2 箇所は
  「生存かつ表示中」を見る）。**4 箇所目が同じ意味で増えたら**小さな判定ヘルパへの抽出を再判定する。
- **Phase 18（フル表示の幅配分）の `/refactor_check` からの候補送り**（判定は**不要**）:
  - `pane_width_rules.DEFAULT_LIST_CHARS = 26` が**未使用**で、`views/full_view/keymap_box.py` / `trigger_box.py` の `width=26` が直値のまま（M6 の境界）
  - `controllers/pane_layout/pane_layout_controller.py`（256 行）がドラッグ・レイアウト適用・ウィンドウ幅の保存の **3 まとまり**を持つ。
    さらに増えるならウィンドウ幅の保存を同フォルダの別モジュールへ分ける再判定をする
  - 完了判定前レビューの保留 3 件（ドラッグで元の希望幅へ戻したとき最小幅が更新されない場合 / `pane_measure.py` の SequenceBox 構造依存 /
    phase 18 以前の tests_ui が実 config を読む）。判断は [decisions_archive/18](../../.claude_data/state/decisions_archive/18_full_view_resizable_panes.md)
- **Phase 19（フル表示ヘッダの幅）の `/refactor_check` からの候補送り**（判定は**推奨** → 提案書 10 を task_07 で実施済。提案書へ入れなかった分）:
  - `KEYBOARD_LAYOUT_COMBO_WIDTH` がボタン文言のモジュール `hook_button_texts.py` に同居（使う側は 2 箇所）
  - `tests_ui/test_full_view_header_width.py` / `test_header_button_widths.py` は保存予約の遅延を延ばしていない（現状は予約取消で実害なし・揺れたら task_03 と同じ対処）
  - `controllers/hook_controller.py` の `register_hook_buttons` と `apply_fixed_button_widths` の幅適用 2 行が同型（2 箇所・軽微）
- **Phase 20（フル表示の縦方向の最小サイズ）の `/refactor_check` と完了判定前レビューからの候補送り**（判定は**不要**）:
  - Phase 18 の再判定条件（`pane_layout_controller.py` が増えたらウィンドウ幅の保存を分ける）: 256 → 約 280 行。高さの処理は `apply_layout` 内の数行と属性 1 つで独立したまとまりではないため**分割不要と再判定**。次にまとまりが増えたら再判定する
  - 保留: 一時メッセージのラベルを App 属性で直接参照する案（phase 01 の「生やし」解消と衝突）。判断は [decisions_archive/20](../../.claude_data/state/decisions_archive/20_full_view_min_height.md)
- **Phase 11（孤児ファイルの棚卸し）の `/refactor_check` からの候補送り**（判定は**推奨** →
  提案書 [08_refactor_orphan_child_file_sweep](../modified_proposal/08_refactor_orphan_child_file_sweep.md)
  は**「計画08」として実施し完了**〔2026-09-08・挙動不変〕。提案書へ入れなかった分）:
  - **ダイアログの同型スケルトン**（`Toplevel` + `suspend_hook_for_dialog` / Escape bind /
    `protocol(WM_DELETE_WINDOW)` / `transient` + `grab_set` / `destroy` override）が
    **9 ダイアログ中 8 ファイル**に広がっている（phase 11 で +2）。**M3 該当だが
    フェーズ外 6 ファイルへ波及する**ため提案書には入れていない。着手するなら
    [idea_10](../backlog/idea_10_nested_modal_grab_restore.md)（ネストしたモーダルの grab 復元）と
    **同じ領域なので合流させる**
  - `controllers/config_io/` の IO クラス骨格（`__init__` + `run_*` → `config_service` 呼び出し →
    `format_*` → `messagebox`）と `presentation/*_text.py` の整形関数が **3 系統目**に達した。
    1 個目が phase 10（フェーズ外）で骨格も薄いため候補送り
  - `keyseq/application/config_service/__init__.py` が **828 行**（phase 11 で +61。M1 は
    「600 行超 **かつ** +100 行以上」のため非該当）。**分割は保留のまま**（テストが
    `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため
    本体とパス基盤メソッドを動かせない制約がある）。次フェーズ以降に再判定する

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
- フェーズ完了時は本ファイルの「現在の参照先」を差し替える。**完了フェーズはリンクのみを残し、
  要約は書かない**（要約は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正）。
  代わりに「**直近の一連の作業が扱っている領域**」を数行で置き、**いま何の続きを見ているのか**と
  **その領域の残件**が分かるようにする（2026-09-08 のユーザー判断。過去フェーズの要約を並べない）。

起票元 idea があるフェーズは、`instructions/backlog/INDEX.md` の該当行を完了 / クローズ状態に
更新して `instructions/backlog/INDEX_done.md` へ移動すること
（チェックリストは `.claude/rules/task_execution.md`「フェーズ完了時」）。

## 新フェーズ作成時の更新ルール

新しいフェーズ用フォルダを作成した場合は、`## 現在の参照先` を新フェーズの `phase.md` に更新してください。
フォルダ名は `instructions/phase/` 直下で**連番プレフィックス付き**（`NN_<topic>`）にしてください。
起票手順は `/phase_start`（`.claude/commands/phase_start.md`）に従うこと。

## 注意

このファイルには、実装順序・タスク詳細・チェック内容・完了フェーズの経緯を書かないでください
（**「直近の一連の作業が扱っている領域」の数行だけは例外**。「フェーズ完了時の指示」節を参照）。
それらは各フェーズフォルダ内の `phase.md` および `decisions_archive/<phase>.md` に記載してください。
