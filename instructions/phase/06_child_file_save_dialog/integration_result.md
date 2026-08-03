# Phase β integration result

> **本表の範囲**: 下記 §1 は **task_06（統合退行）時点の受入条件 1〜11** の対応表。
> **受入条件 12〜27**（v0.3〜v0.7 で追加された分）は、追加した各タスク
> （task_07〜09 / 11〜18）の「確認」節に固定テストを列挙しており、**各タスクの完了判定時に実測 pass 済み**。
> 最新の実測値は §2 の末尾行が正。

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

**フェーズ完了時点の実測**（2026-08-02・task_18 完了時。`verifier` 実測）:

| コマンド | 実測結果 |
| --- | --- |
| `-m compileall -q keyseq main.py tests_ui` | clean（exit 0） |
| `-m unittest discover -s tests` | **144 pass** / fail 0 |
| `-m unittest discover -s tests_ui` | **153 pass** / fail 0（16.3 秒で完走・ハングなし） |
| `-m tests.smoke_app` | pass（SMOKE OK） |

- 既存の後方互換テスト（`tests/test_config_service.py` の保存 JSON 完全一致・`_parent_refs` 無し JSON の読込）は
  **無修正で pass**。条件 7 の比較は JSON 比較から**バイト列比較**へ強化した（§10 の安全網に合わせた変更で、緩和ではない）。
- `tests_ui/test_config_io_characterization_keymap_set_startup.py` の変更は**コメント追加のみ**
  （ダイアログを意図的に迂回している理由の明示）。期待値の更新が必要な旧挙動固定は無かった。

## 3. 実機目視の結果

**全項目 OK**（ユーザー実施・**2026-08-02** 報告）。手順は [manual_check_plan.md](manual_check_plan.md)
（task_01〜18 の目視項目を操作順に統合した R1〜R11。task_06 定義「対象範囲 4」の 9 項目は R3〜R9 へ内包済み）。

| # | 確認内容 | 出所 | 結果 |
| --- | --- | --- | --- |
| R1 | 個別保存で root 直下に `user/` を作らない | v0.5-J | OK |
| R2 | 個別「トリガー一覧を保存」で sequence 行だけの一覧が出る | v0.5-K | OK |
| R3 | 一覧の見た目 4 点（初期省略・ホイール・縮小時のラジオ / ボタン・10 行以上） | v0.5-L/M・v0.4-C・目視 9 | OK |
| R4 | 一括保存の基本（一覧が出る / キャンセル / 保存しない / 変更なし保存） | 目視 1・2・7・8 | OK |
| R5 | 所有元不明・共有中の表示（`_parent_refs` を手編集して準備） | 目視 3・4 | OK |
| R6 | 依存確認の提示条件と 4 択・別名保存後に一覧が再表示されない | 目視 5・6・v0.3-A・v0.4-D/E | OK |
| R7 | 個別「別名で保存」→ 未保存マーク → 構成セット保存で索引が追随 | v0.5-N | OK |
| R8 | 新規作成直後の個別保存で前の構成が書き換わらない | v0.4-H | OK |
| R9 | 「例を復元」（未保存確認 / 別名保存ダイアログ / 子一覧） | v0.6-O/P/Q | OK |
| R10 | VS Code ▶ 起動（小文字ドライブ）でデフォルト外判定・落ち先が正しい | v0.3-B | OK |
| R11 | 共有状況「単独」の新文言・既定ラジオは「保存」のまま | v0.7-R | OK |

- 目視 9（dirty な子が 10 行以上）は縦スクロール実装済みのため **idea 起票は不要**（task_06「含まない」の条件は未発生）。
- 目視 5・6 は v0.3-A / v0.4-D/E で仕様が変わっており、**現行仕様（R6 の期待値）で判定**した。
