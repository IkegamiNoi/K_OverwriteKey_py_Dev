# 13_refactor_trigger_list_per_keymap.md

phase 34（トリガー一覧のキーマップ従属化）の `/refactor_check`（2026-09-27）で「推奨」となった項目。**挙動不変**（エラーメッセージ・保存ファイルのバイト列も変えない）。
PHASE_BASE = `b27336e`。判定の詳細は `decisions_archive/34_trigger_list_per_keymap.md`。

## 判定の根拠

| 記号 | 該当 |
|---|---|
| M1 | `config_service/__init__.py` 841 → 1133（+292）/ `keymap_panel_controller.py` 406 → 680（+274）/ `split_loading.py` 537 → 662（+125） |
| M2 | 40 行以上変更した 80 行超の関数 5 つ（`build_runtime_data_from_split` 154 / `save_runtime_data` 125 / `build_split_save_payloads` 120 / `collect_child_save_rows` 98 / `ensure_config_compatibility` 149） |
| M6 | 内部キー文字列の直値 3 箇所（定数あり） |

M2 の 5 関数は本提案に含めず `current.md`「別タスク化候補」へ送る（分割の設計が関数ごとに要るため）。
`config_service/__init__.py` の M1 は**既知**（`current.md`「別タスク化候補 / application / config_service」に分割保留として記載済み。値と切り出し単位を更新した）。
`split_loading.py` の M1（+125）は増分の大半が `build_runtime_data_from_split`（M2・候補送り）なので、その分割と一緒に扱う。

## 項目 0: 安全網の確認

- 対象領域は既存テストでカバー済み: `tests/test_per_keymap_bulk_save.py`（個別キーマップ保存計画を含む）/ `tests/test_per_keymap_triggers_load.py` /
  `tests_ui/test_config_io_characterization.py`（個別保存・読込の特性）/ `tests_ui/test_task06_keymap_management_ui.py`（追加フロー・削除・切替）/ `tests.smoke_app`。
- 完了条件（各項目共通）: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`（665 / skip 7）・`tests_ui`（575）・`tests.smoke_app` が全 pass、既存テストの変更なし。

## 項目 1: 内部キーの直値を定数参照へ（M6）

- 対象: `keyseq/application/config_service/split_loading.py:504,506` / `keyseq/application/config_service/__init__.py:781` / `keyseq/domain/config.py:199-200, 301-302, 306-307`（`"_trigger_set_source_path"` / `"_trigger_set_parent_refs"` も含む）
- 問題: `"_trigger_set_dirty"` / `"_trigger_set_imported"` / `"_trigger_set_parent_refs"` を直値で書いている（同値の定数が `domain/keymap_triggers.py:13-14` と `ConfigService` にある）。
  改名時に取り残される。`ConfigService` には SOURCE_PATH / PARENT_REFS だけ属性があり DIRTY / IMPORTED が無い非対称も原因。
- 変更: `domain/config.py` は `keymap_triggers` の定数を import して使う（domain 内の参照・依存方向は不変）。
  domain 側に SOURCE_PATH / PARENT_REFS の定数が無いので `keymap_triggers.py` に足す。`config_service/__init__.py` は既に import 済みの `INTERNAL_TRIGGER_SET_DIRTY` 等を使う（クラス属性は増やさない方が差分が小さい）。`split_loading.py` も同じ定数を import する。
- リスク / 戻し方: 値は同一なので挙動不変。戻すのは直値へ戻すだけ。依存: なし。

## 項目 2: キーマップの追加フローを `keymap_panel_controller.py` から切り出す（M1）

- 対象: `keyseq/presentation/controllers/keymap_panel_controller.py:204-388`（`add_keymap` / `add_imported_keymap` / `_collect_missing_switch_edits` / `_prompt_keymap_edit` /
  `_validate_addition_key` / `_apply_pending_switch_edits` / `_append_keymap` / `_restore_active_keymap`）
- 問題: 一覧の表示・グレー表示・切替・編集・削除・追加フロー（切替キー設定の連続ダイアログ）が 1 ファイル 680 行に同居。追加フローだけで約 180 行。
- 変更: `file_organization_rules.md` の親フォルダ方式で `controllers/keymap_panel/keymap_panel_controller.py` + `controllers/keymap_panel/keymap_add_flow.py`
  （追加フローのクラス。コントローラから委譲）へ。旧パスの再輸出は置かない（参照元を一括で差し替える・恒久互換レイヤー禁止）。
- 完了条件: 項目 0 + `tests_ui/test_task06_keymap_management_ui.py` pass・patch 先の文字列（`keyseq.presentation.controllers.keymap_panel_controller.messagebox` 等）を使うテストも新パスへ追随。
- リスク / 戻し方: モジュールパスの変更でテストの patch 先が変わる（計画07 の経験）。移動のみで挙動不変。依存: なし。

## 実施形態

ユーザーが選ぶ: (a) phase 34 の追加タスク（task_09_refactor）/ (b) 次フェーズ前の独立ミニ計画（「計画11」）。
