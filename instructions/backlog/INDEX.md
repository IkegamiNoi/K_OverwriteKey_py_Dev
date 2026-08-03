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
| idea_07 | [idea_07_reference_link_cleanup.md](idea_07_reference_link_cleanup.md) | 子ファイル（keymap/trigger_set/sequence）に記録した参照元（上位ファイル）の実在を一括確認し、参照できないものをリストから除去する掃除機能。menu_bar から起動。 | 未着手・**着手可**（Phase β 完了 = 2026-08-02 で前提充足）。β の参照元記録（`_parent_refs`・best-effort 更新）の陳腐化を回収する保守機能。**回収対象**: 上位の移動 / 削除で残る孤児 trigger_set と陳腐化した `_parent_refs`（β では「オーナー不在の孤児 / 前バージョンのファイル」への露出を許容と確定済み・正本 `data_schema.md` §5.8.1）|
| idea_08 | [idea_08_per_keymap_set_preset_ownership.md](idea_08_per_keymap_set_preset_ownership.md) | プリセットを keymap_set ごとの持ち物として個別指定できる上書き機構。プリセットの config.json グローバル化（案2）に対する per-set オーバーライド。 | 未着手（**プリセット案2 完了後に着手**・保存系リデザイン討議 P-a で分離。停止/トグルキー個別指定と同型パターン）|
| idea_09 | [idea_09_legacy_settings_save_path_fallback.md](idea_09_legacy_settings_save_path_fallback.md) | 別名保存でレガシー `settings/` 配下を選ぶと選択パスが捨てられ無言で `default.json` へ保存される残存経路（`config_paths.normalize_keymap_set_save_path:72-73`）。Phase α の「`default.json` フォールバック廃止」の取りこぼし。 | 未着手（検討段階・優先度低・phase 05 task_05 の deep-reviewer 指摘2 から分離。**正本 `data_schema.md` §5.4 に「実装未追従」として明記済 → 実装修正が既定**。判断が要るのは案 A〜C の選択のみ）|
