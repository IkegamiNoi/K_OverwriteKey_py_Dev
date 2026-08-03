# instructions/backlog/INDEX_done.md

**完了・クローズ（対応不要 / 除外）が確定した idea** の記録。
アクティブな idea と運用ルールの正本は [INDEX.md](INDEX.md)。

- 行は INDEX.md「ネタ一覧」から移動する（判定理由・対応フェーズへのリンクを状態列に残す）
- ファイル本体（`idea_NN_*.md`）は `instructions/backlog/` に残る（移動しない）

---

## 完了・クローズ一覧

| ID | ファイル | 概要 | 状態 |
|---|---|---|---|
| idea_01 | [idea_01_hotkey_validation_to_domain.md](idea_01_hotkey_validation_to_domain.md) | App に住む hotkey 検証ロジック（約31行）を domain / application へ移し、App は dialogs 契約の薄い委譲に留める。application → presentation の逆転を解消し、`tk.Tk` なしで単体テストできるようにする。 | **完了**（[02_hotkey_validation](../phase/02_hotkey_validation/phase.md) フェーズ 2026-07-18・挙動不変で層移設完了。spec_detail に hotkey 検証の記述がなく正本昇格は不要＝担当層は codebase_map.md が正。判断は [decisions_archive/02_hotkey_validation.md](../../.claude_data/state/decisions_archive/02_hotkey_validation.md)）|
| idea_02 | [idea_02_startup_font_settings_cleanup.md](idea_02_startup_font_settings_cleanup.md) | 起動設定/フォントの3メソッド（`_load_startup_settings` / `_coerce_font_delta` / `set_ui_font_delta`）の責務混在と controller → App private 逆参照を解消。初期化順序の解決が前提。 | **完了**（[03_startup_font_settings_cleanup](../phase/03_startup_font_settings_cleanup/phase.md) フェーズ 2026-07-20・挙動不変。coerce→theme.py / 起動設定ローダ→startup_settings.py / set_ui_font_delta 案A分割 / UiVars 引数化。案B は将来 idea 化。正本昇格は不要＝担当層は codebase_map.md が正。判断は [decisions_archive/03_startup_font_settings_cleanup.md](../../.claude_data/state/decisions_archive/03_startup_font_settings_cleanup.md)）|
| idea_05 | [idea_05_trigger_set_source_path_inconsistency.md](idea_05_trigger_set_source_path_inconsistency.md) | trigger_set の source_path が読み手（未定義の App 属性・常に空）と書き手（read されない dirty_tracker 属性）で分断。「読込で持ってきた…別名で保存しますか？」の確認が到達不能なデッドコードになっている。keymap / sequence は対称で本件は trigger_set のみ。 | **完了**（[06_child_file_save_dialog](../phase/06_child_file_save_dialog/phase.md) フェーズ 2026-08-02・**Phase β が内包**。trigger_set の source_path を runtime データ側の内部キーと `dirty_tracker` で常に一致させる形へ統一し、keymap / sequence と対称にした。正本は `spec_detail/data_schema.md` §5.8.2。判断は [decisions_archive/06_child_file_save_dialog.md](../../.claude_data/state/decisions_archive/06_child_file_save_dialog.md)）|
