# phase.md

## フェーズ名

サンプルを config/user/ へ書き出す（sample_in_user_folder）

## フェーズの目的

初回の「サンプル入りで始める」で書き出すサンプルを `config/sample/` ではなく `config/user/` へ書き出し、保存・読込のダイアログが普段どおり `config/user/` の各フォルダを案内するようにする。
**対象レイヤ = application（`config_service/sample_install.py`）・presentation（`app.py` の初回起動の起動設定）。JSON スキーマ不変。**

- 起票元: ユーザー要望（2026-11-23）。
- 主入力（暫定仕様）: [59_sample_in_user_folder.md](../../history/59_sample_in_user_folder.md)（v0.2・ユーザー確定済）
- モード: **暫定仕様先行モード**。番号対応: phase 77 / 暫定 59 / decisions 77。

## 確定（ユーザー 2026-11-23）

暫定 59 の §2 が正。要点:

- 書き出し先 = `config/user/`（構成セット `user/keymap_sets/sample.json`・子の名前は今のまま）。起動設定の `keymap_set_path` = `user/keymap_sets/sample.json`。
- 既存の `config/sample/` は移行しない（書かない・動かさない）。
- 構成セットが無く、中身の違う同名の子が 1 つでもあれば何も書かずに警告して空で始める。中身が同じ子は衝突にしない（途中失敗の再試行を保つ）。
- 孤児の掃除の参照元 `config/sample/keymap_sets/`（経路 5）は残す。
- 受容: 利用者が自作した同名の構成セットをサンプルとして開く / 違う言語での再試行は衝突になる。除外: 書き出し中の別プロセスとの競合。

## スコープ

### 含む

暫定 59 の §3（§3.1 書き出し・§3.2 同名の子・§3.3 孤児の掃除〔コードは変えない・テストで確認〕）と §4 の受け入れ条件。

### 含まない（後送り）

暫定 59 の §5（既存 `config/sample/` の移行・削除 / ダイアログの初期フォルダの決め方 / ファイル名の変更 / サンプルかどうかの識別 / 別プロセスとの競合）。

## このフェーズで読むファイル

1. `instructions/history/59_sample_in_user_folder.md`（主入力）
2. `instructions/common/codebase_map.md` の `sample_install.py` の行（`application/config_service`）
3. `instructions/common/spec_detail/data_schema.md` §5.14・`data_schema/5_08_09_orphan_sweep.md`（経路 5）・`features.md` §Welcome
4. `keyseq/application/config_service/sample_install.py`・`save_plan_execution.py`（書き出しの順）・`orphan_scan.py`（経路 5・変更しない）
5. `keyseq/presentation/app.py` の `_prepare_first_launch`
6. テスト: `tests/test_sample_install.py`・`tests/test_orphan_scan.py`・`tests_ui/test_first_launch_flow.py`

## タスク

1. task_01: 書き出し先の変更と同名の子の判定 — `sample_install.py`（基準 `config/user/`・書き出す前の 13 子の照合〔中身が同じなら衝突にしない〕・衝突時は書かず `incomplete` 相当で空で始める）・`app.py:405` の起動設定・テスト（暫定 59 §4 の 1・2・4〜8）
2. task_02: 統合確認 — 標準検証 4 種・受け入れ条件 §4 の照合・実機目視（ユーザー・§4 の 3 = 初回起動でサンプルを開いた状態の保存 / 読込の案内先）
3. task_03: 正本反映 — 暫定 59 の昇格（§6: `data_schema.md` §5.14・`data_schema/5_08_09_orphan_sweep.md` 経路 5・`features.md` §Welcome）と凍結・`decisions_archive/77_sample_in_user_folder.md`・`codebase_map.md`・`current.md` の完了記載・`/refactor_check`

## レビュー方針

- 各タスクは `reviewer`（`.claude/rules/review.md` の 5 観点）。task_02 は `deep-reviewer` + `codex-reviewer`、フェーズ完了判定前は `deep-reviewer` + `codex-adversarial-reviewer`。
- 本フェーズ固有の観点:
  - **利用者のファイルを上書きしないか**（構成セットが無く中身の違う子があるとき、1 つも書かない。照合は書き出す全パス）
  - 途中失敗の再試行（`test_sample_install.py` の既存テスト `test_failure_leaves_no_keymap_set_and_retry_succeeds` の意図が保たれる）
  - 参照のパスが `config/` 基準の相対で書かれる（`split_base_dir` は絶対パスの `config/user/`）
  - `config/sample/` に書き込まない・`orphan_scan.py` の経路 5 を消さない
