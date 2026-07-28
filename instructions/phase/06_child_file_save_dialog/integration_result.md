# Phase β integration result

## 1. 受入条件の対応表

| # | 条件 | 固定テスト | 結果 |
| --- | --- | --- | --- |
| 1 | dirty な子が2個以上なら一覧で行ごとに保存方法を選べる | `tests_ui/test_child_save_dialog.py::ChildSaveDialogFlowTest.test_dirty_choices_control_overwrite_save_as_and_skip` | pass |
| 2 | dirty な子が無ければダイアログを出さず親のみ保存する | `tests_ui/test_child_save_dialog.py::ChildSaveDialogFlowTest.test_clean_children_do_not_open_dialog_or_change_child_bytes` | pass |
| 3 | `_parent_refs` 無しの子は別名保存が既定になる | `tests/test_child_save_rows.py::ChildSaveRowsTest.test_collect_treats_missing_or_empty_parent_refs_as_unknown` | pass |
| 4 | 別の keymap_set に属する子は別名保存が既定になる | `tests_ui/test_child_save_dialog.py::ChildSaveDialogFlowTest.test_other_parent_child_reaches_dialog_with_save_as_default` | pass |
| 5 | 共有中の子に件数警告を表示し上書きを選べる | `tests_ui/test_child_save_dialog.py::ChildSaveDialogFlowTest.test_shared_child_reaches_dialog_with_warning_and_can_overwrite` | pass |
| 6 | 別名保存で親の保存が必須になり、スキップできない | `tests/test_dependency_query.py::DependencyQueryTest.test_query_and_save_validation_share_dependency_rule`、`tests_ui/test_child_save_dialog.py::ChildSaveDialogFlowTest.test_dependency_confirmation_can_save_trigger_set` | pass |
| 7 | 子書込み失敗時に親索引と startup 索引を旧バイト列のまま維持する | `tests/test_save_plan.py::SavePlanTest.test_child_write_failure_keeps_parent_and_startup_indexes` | pass |
| 8 | 複数 keymap_set の trigger_set 既定パスが名前ごとに分離される | `tests/test_config_service.py::TriggerSetDefaultPathTest.test_multiple_keymap_sets_do_not_share_default_trigger_set_file` | pass |
| 9 | trigger_set の source_path が keymap / sequence と一貫して接続される | `tests_ui/test_config_io_characterization.py::ConfigIoCharacterizationTest.test_loaded_keymap_set_syncs_trigger_set_source_path`、`tests_ui/test_config_io_characterization.py::ConfigIoCharacterizationTest.test_bulk_save_syncs_changed_trigger_set_source_path`、`tests_ui/test_config_io_characterization.py::ConfigIoCharacterizationTest.test_individual_trigger_save_keeps_bulk_save_on_new_path`、`tests_ui/test_config_io_characterization.py::ConfigIoCharacterizationTest.test_sequence_save_uses_nonempty_trigger_set_parent_ref_after_individual_save` | pass |
| 10 | `_parent_refs` 無しの既存子JSONを正常に読込・保存できる | `tests/test_config_service.py::ParentRefsSchemaTest.test_existing_files_without_parent_refs_remain_unknown`、`tests/test_config_service.py::ParentRefsSchemaTest.test_legacy_children_without_parent_refs_load_and_save` | pass |
| 11 | 更新後の特性テストと全検証経路で挙動を固定する | verifier: `../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests_ui`、`../../../.venv/Scripts/python.exe -m unittest discover -s tests`、`../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui`、`../../../.venv/Scripts/python.exe -m tests.smoke_app` | pass |

## 2. 検証コマンドと実測結果

実測は `verifier` が**リポジトリルートの `.venv`**（`..\..\..\.venv\Scripts\python.exe`）で実行（2026-07-29）。

| コマンド | 実測結果 |
| --- | --- |
| `-m compileall -q keyseq main.py tests_ui` | clean（exit 0） |
| `-m unittest discover -s tests` | **129 pass** / fail 0（task_05 時点 128 → +1） |
| `-m unittest discover -s tests_ui` | **97 pass** / fail 0（task_05 時点 95 → +2） |
| `-m tests.smoke_app` | pass（SMOKE OK） |
| 上記対応表の 13 テストを個別実行 | **13/13 実在・pass**（対応表のテスト名が実在することの担保） |

- 既存の後方互換テスト（`tests/test_config_service.py` の保存 JSON 完全一致・`_parent_refs` 無し JSON の読込）は
  **無修正で pass**。条件 7 の比較は JSON 比較から**バイト列比較**へ強化した（§10 の安全網に合わせた変更で、緩和ではない）。
- `tests_ui/test_config_io_characterization_keymap_set_startup.py` の変更は**コメント追加のみ**
  （ダイアログを意図的に迂回している理由の明示）。期待値の更新が必要な旧挙動固定は無かった。

## 3. 実機目視の結果

**未実施**（ユーザーが実施 → 結果をここへ記録する）。チェックリストは
[task_06 定義](tasks/task_06_integration_regression.md) の「対象範囲 4」。

| # | 確認内容 | 結果 | ユーザーコメント |
| --- | --- | --- | --- |
| 1 | 子 2 つ以上を変更して保存 → 一覧が出て行ごとに選べる | 未実施 | |
| 2 | 変更なしで保存 → ダイアログが出ない | 未実施 | |
| 3 | `_parent_refs` 無しの子 → 既定が別名保存・「所有元不明」表示 | 未実施 | |
| 4 | 共有中の子 → 「N 個の上位で共有中」警告つきで上書きも選べる | 未実施 | |
| 5 | 依存確認が出る・理由が分かる・所有元不明なら既定が「いいえ（別名保存）」 | 未実施 | |
| 6 | 「選び直す」で一覧へ戻る / trigger_set 別名保存で**一覧が再表示され保存先が変わる** | 未実施 | |
| 7 | 一覧でキャンセル → 1 ファイルも書かれず未保存表示が残る | 未実施 | |
| 8 | 「保存しない」を選んだ子 → 保存後も未保存マークが残る | 未実施 | |
| 9 | dirty な子が 10 行以上のときの見え方（縦スクロール無し） | 未実施 | |
