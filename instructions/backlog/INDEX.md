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
| idea_26 | [idea_26_dialog_keyboard_focus.md](idea_26_dialog_keyboard_focus.md) | Escape を bind しているのにキーボードフォーカスを取らないダイアログ（`orphan_sweep` / `quarantine_manage` / `reference_cleanup`）があり、実使用で Escape が効かない。既存テストは `focus_force()` 後に Escape を送るため検出できない。 | 未着手（検討段階・phase 27 task_04 の実機目視から分離。**対象ダイアログのフォーカス欠落は診断スクリプトで実測済**。案 A=個別修正 / 案 B=`grab_modal` へ集約 + 正本 §4.6 追記の選択が要る）|
| idea_27 | [idea_27_mouse_click_button_type_coercion.md](idea_27_mouse_click_button_type_coercion.md) | `mouse_click` の `button` が非文字列だと `action_executor.py:119` の `.strip()` で `AttributeError`。x / y と違い `try` の外にある。正本 §5.11.2 は「非文字列は未定義」と明記しているため直すなら仕様改訂が先。 | 未着手（検討段階・**優先度低**・phase 22 完了判定前の `deep-reviewer` 指摘 6 から分離。2026-09-22 に current.md「別タスク化候補」から昇格。着手時は仕様変更フロー必須）|
| idea_28 | [idea_28_runtime_internal_key_type_coercion.md](idea_28_runtime_internal_key_type_coercion.md) | runtime 専用の内部キー（`_keymap_source_path` 等・§5.8.2）が §5.1 の型規則に未追従で、`save_path_resolution.py:127` の `str(...)` を経て保存先パス候補に repr が混入し得る。 | 未着手（検討段階・**優先度低**・phase 25 完了判定前の `deep-reviewer` 指摘 B から分離。2026-09-22 に current.md「別タスク化候補」から昇格。**正本 §5.7 に「実装側を追従させる」と明記済 → 実装修正が既定**。永続化されないため通常経路では発生しない）|
| idea_29 | [idea_29_action_dialog_listener_after_destroy.md](idea_29_action_dialog_listener_after_destroy.md) | `ActionDialog` の座標取得リスナー（`pynput` のデーモンスレッド）が、ダイアログ破棄後に `after(0, ...)` を呼ぶと `TclError` になり得る（`action_dialog.py:247-251`）。 | 未着手（検討段階・**優先度低**・phase 22 task_02 の `reviewer` 参考指摘から分離〔task_02 以前からの既存挙動〕。2026-09-22 に current.md「別タスク化候補」から昇格。**未再現・理屈上の経路**）|
| idea_30 | [idea_30_keymap_set_slug_collision.md](idea_30_keymap_set_slug_collision.md) | `slugify_file_stem` で別々の keymap_set 名が同一 stem へ丸まり、子ファイルの既定保存先が重なり得る。同一保存計画内の連番回避は効くが、別の keymap_set 由来の衝突は互いを知らない。 | 未着手（検討段階・**優先度低**・Phase β の `/refactor_check` 候補送りから分離〔受入条件 8 の範囲外〕。2026-09-22 に current.md「別タスク化候補」から昇格。**着手時はまず共有判定・確認ダイアログでどこまで防げているかの実測が先**〔防げていればクローズ〕）|
| idea_31 | [idea_31_input_gateway_dead_register_key_hook.md](idea_31_input_gateway_dead_register_key_hook.md) | `InputGateway.register_key_hook`（`input_gateway.py:58-75`）に呼び出し元が無い。フック登録の実経路は `register_global_hook` のみで、押下だけ上位へ渡す包み（18 行）が残っている。 | 未着手（検討段階・**優先度低**・phase 21 完了判定前の `deep-reviewer` 指摘 8 から分離〔当時は「phase 21 の差分外」として据え置き・ユーザー判断 2026-09-19〕。2026-09-22 に current.md「別タスク化候補」から昇格。**挙動不変**・削除前に `_wrapped` の挙動が他所で再実装されていないかの確認が要る）|
| idea_32 | [idea_32_grab_modal_static_check_discovery.md](idea_32_grab_modal_static_check_discovery.md) | `grab_modal` の静的検査（`tests_ui/test_nested_modal_grab.py:260`）が対象を dialogs 10 クラス + config_io 3 ファイルのハードコード列挙で持つため、新規ダイアログを守らない。発見ベースへ寄せたいが件数アサートが担う「呼び出しが消えた」検出を失う。 | 未着手（検討段階・**テストのみ・production 不変**・phase 14 の `/refactor_check`〔`deep-reviewer` M-6〕から分離・保留判断 2026-09-11。2026-09-22 に current.md「別タスク化候補」から昇格。案 A〔併用〕/ B〔発見ベース単独〕/ C〔足し忘れ検出のみ追加〕の選択と、phase 15 側の静的検査との棲み分けが要る）|
