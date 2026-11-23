# task_02_integration_check

## 目的

task_01 の変更（暫定 59 §3.1・§3.2）を通しで確かめ、受け入れ条件（暫定 59 §4 の 1〜8）を照合する。実機目視（§4 の 3）はユーザーが行う。
**コード変更なし（検証・レビュー・照合のみ）。問題が出たら枝番タスク（task_02a 等）を起こして直す。**

## 対象範囲（検証のみ・コード変更なし）

### 標準検証（verifier）

- `compileall -q keyseq tests tests_ui` / `unittest discover -s tests` / `unittest discover -s tests_ui`（同時 1 本・`taskkill` で python.exe を一括終了しない）/ `-m tests.smoke_app`
- 既知の不安定（窓の大きさのテスト・`test_action_dialog_control.py` の実行順依存）は session.md の resume_hints のとおり切り分ける

### 受け入れ条件の照合（メイン）

| §4 | 確かめ方 |
| --- | --- |
| 1 | `test_sample_install.test_writes_fixed_paths_without_startup_or_sample_files` |
| 2 | `tests_ui/test_first_launch_flow.py` の期待値・`test_child_paths_and_external_layout_remain_config_relative` |
| 3 | ユーザーの実機目視（下記） |
| 4 | `test_missing_or_invalid_references_are_incomplete_and_unchanged`・`test_invalid_keymap_set_is_incomplete`・既存の `existing` のテスト |
| 5 | `test_different_leftover_child_blocks_install_without_writes`・`test_mixed_identical_and_different_children_remain_unchanged` |
| 6 | `test_failure_leaves_no_keymap_set_and_retry_succeeds`・`test_identical_leftover_children_allow_retry` |
| 7 | `test_orphan_scan.test_installed_sample_children_are_all_referenced`・`test_sample_set_references_user_child_without_expanding_candidates` |
| 8 | `test_old_sample_tree_is_untouched` |

### レビュー

- `deep-reviewer` + `codex-reviewer`（task_01 のコミット 4819cdb7 の差分。phase.md の「レビュー方針」の観点）

### 実機目視（ユーザー）

1. 手元の `config/config.json` を退避して初回起動にする（`config/user/` に `keymap_sets/sample.json` や同名の子があれば退避する）
2. Welcome で「サンプル入りで始める」→ `config/user/keymap_sets/sample.json` と子ができ、`config/sample/` が新しく作られないこと
3. メニューの構成セットの別名保存・読込、出力シーケンス等の子の保存のダイアログが `config/user/` の各フォルダを開くこと
4. 終わったら退避したファイルを戻す

## 読むファイル

1. `instructions/history/59_sample_in_user_folder.md` §4
2. `instructions/phase/77_sample_in_user_folder/phase.md`「レビュー方針」
3. `tests/test_sample_install.py`・`tests/test_orphan_scan.py:480-500`（照合のため・テスト名のみ）

## 含まない

- 正本・`codebase_map.md` の更新・暫定 59 の凍結（task_03）
- 新しい機能・テストの追加（問題が出たときの修正は枝番タスク）

## 確認

- 標準検証 4 種が pass（既知の不安定は再実行で切り分けて報告）
- 受け入れ条件 §4 の 1〜8 がすべて確かめられた（3 はユーザーの OK）
- deep-reviewer と codex-reviewer の指摘の採否をユーザーと決めた

## 完了条件

- 上記確認 pass・**reviewer 採用**（本タスクでは deep-reviewer の判定で代える）。
- 実機目視は本タスクで実施（ユーザー）。
