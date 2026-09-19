# instructions/backlog/

実装予定（または検討中）の改善ネタを蓄積する場所。

このフォルダのファイルは **正式なフェーズ／タスクではない**。
着手時は `instructions/phase/<phase>/tasks/` へ正式タスクとして起票し直すこと。
起票手順は `/idea`（`.claude/commands/idea.md`）。

---

## 運用ルール

- 1 ネタ 1 ファイル
- ファイル名: `idea_<連番>_<topic_snake_case>.md`
- 各ファイルは「概要 / 起票経緯 / 現状 / 提案 / 想定スコープ」を含む
- 着手時は状態列を「**着手**（→ 暫定仕様 / phase へのリンク）」へ更新し、行は本 INDEX に残す
- 完了・クローズ（対応不要 / 除外）が確定したものは、判定理由と対応フェーズへのリンクを
  状態列に残した上で、行を [INDEX_done.md](INDEX_done.md) へ移動する
  （フェーズ完了時の更新は `.claude/rules/task_execution.md`「フェーズ完了時」に従う）
- 「保留」は判定理由を状態列に残して本 INDEX に残す
- 仕様変更を伴うネタは `.claude/rules/spec_change_workflow.md` に従う
- 採番はフォルダ実体（`idea_*.md` の最大番号 + 1）が正。本表を基準にしない

---

## ネタ一覧

| ID | ファイル | 概要 | 状態 |
|---|---|---|---|
| idea_03 | [idea_03_action_hotkey_save_normalization.md](idea_03_action_hotkey_save_normalization.md) | アクション hotkey の保存経路がプリセットと非対称で生値のまま保存される点を統一。実行時は正規化されるため実害はないが JSON に生値が残る。保存/読込どちらで正規化するか等は要設計。 | 未着手（検討段階・phase 02 task_04 の実機目視から分離）|
| idea_04 | [idea_04_font_settings_controller.md](idea_04_font_settings_controller.md) | フォント設定（状態/正規化/適用/UI反映/永続化）が App に散在する点を `FontSettingsController` へ集約。phase 03 で案 B として比較検討し、初期化順序が未解決のため見送られたもの。 | **保留（着手条件付き）**: 対象が実質 int 1 個で controller 新設が過剰なため。フォント設定項目の追加・設定ダイアログ化等の**着手トリガー**（ファイル内に 5 件明記）が発生するまで着手しない。着手時は初期化順序設計の暫定仕様が先に必要（1 フェーズ規模）。phase 03 §6 案 B から分離 |
| idea_06 | [idea_06_individual_json_io_unification.md](idea_06_individual_json_io_unification.md) | 個別 JSON（keymap / trigger_set / sequence）の save/save_as/to_path/load 4点セットが同じ骨格で3回反復している点を共通テンプレートへ集約。 | **保留（前提条件付き）**: 骨格は同型だが細部が9点食い違い、うち2点は既存の不整合。①phase 04 完了（**充足・2026-07-26**）②[idea_05](idea_05_trigger_set_source_path_inconsistency.md) の解消（**充足・2026-08-02 / Phase β**）③共通化の実需（4種目の追加等）の**3条件すべて**を満たすまで着手しない。**残るは③のみ**（Phase β で個別保存 3 経路のパス解決・上位 dirty 化を揃えたため、共通化の対象は着手当時より整理されている）。暫定仕様 03 §5 案2 から分離 |
| idea_09 | [idea_09_legacy_settings_save_path_fallback.md](idea_09_legacy_settings_save_path_fallback.md) | 別名保存でレガシー `settings/` 配下を選ぶと選択パスが捨てられ無言で `default.json` へ保存される残存経路（`config_paths.normalize_keymap_set_save_path:72-73`）。Phase α の「`default.json` フォールバック廃止」の取りこぼし。 | 未着手（検討段階・優先度低・phase 05 task_05 の deep-reviewer 指摘2 から分離。**正本 `data_schema.md` §5.4 に「実装未追従」として明記済 → 実装修正が既定**。判断が要るのは案 A〜C の選択のみ）|
| idea_11 | [idea_11_save_as_preset_copy_rollback.md](idea_11_save_as_preset_copy_rollback.md) | 別名保存で個別プリセットの複製に成功した後、keymap_set 本体の保存が失敗しても巻き戻らない。孤児の複製とメモリ上だけ新パスを指す `hotkey_presets_path` が残り dirty も立たない。補償削除・参照復元、または最低限 dirty を立てる。 | 未着手（検討段階・**優先度低**・phase 09 task_08 の敵対的レビュー High 3 から分離。**現状は正本 `data_schema.md` §5.10.4 に既知の制約として明記済**。例外系が前提でデータは失われないため後送りとユーザー判断）|
| idea_13 | [idea_13_external_layout_path_base_asymmetry.md](idea_13_external_layout_path_base_asymmetry.md) | `external_keyboard_layouts[].path` の解決基準と保存表記が非対称（読込は config_root 基準で解決 → runtime は親基準の相対表記 → 保存はその値をそのまま書く）。保存された値を読み直すと解決先がずれ得る。 | 未着手（検討段階・**優先度低**・2026-09-06 起票。暫定仕様 10 v0.3 の `codex-adversarial-reviewer` 指摘〔Medium〕から分離。孤児検出側は両基準の superset で回避済み。着手時は後方互換の移行規則が要り仕様変更フロー必須）|
| idea_18 | [idea_18_escape_delivery_flaky_test.md](idea_18_escape_delivery_flaky_test.md) | `tests_ui/test_dialog_teardown_flows.py` の Escape 依存テストが **CPU 負荷下で不定期に fail** し、カウンタ残留で同クラスの後続 4 件が連鎖して落ちる（1 件の不安定が 5 件の赤になる）。**production の欠陥ではなくテストのみの問題**。 | 未着手（検討段階・phase 16 task_04 の統合確認で切り分け。**phase 15 時点から存在**することを実測確認済〔負荷下 6 回中 2 回 fail〕）|
| idea_23 | [idea_23_key_press_release_actions.md](idea_23_key_press_release_actions.md) | 出力シーケンスに「キーを押す（押しっぱなし）」「キーを離す」アクションを追加する（停止時に必ず離す安全策が要る）。範囲選択の不具合は拡張キー対応で直すため、足りない用途があれば着手。 | 未着手（検討段階・2026-09-18 ユーザー要望・優先度低）|
| idea_25 | [idea_25_path_field_type_normalization.md](idea_25_path_field_type_normalization.md) | keymap_set / 外部レイアウト登録の**パス系フィールド**（`path` / `switch_key` / `trigger_set_path` 等）に `str()` 強制が残っており、非文字列を渡すと Python の repr 文字列がパスとして扱われる。例外にはならず「存在しないパス」として無視されるため実害は小さい。正本 §5.5 / §5.7 に型規定が無い。 | **着手**（2026-09-19 → [phase 25](../phase/25_path_field_type_normalization/phase.md)・案 A で実装追従）|
