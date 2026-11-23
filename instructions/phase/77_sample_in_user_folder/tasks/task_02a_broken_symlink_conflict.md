# task_02a_broken_symlink_conflict

## 目的

書き出す子のパスにリンク先の無いシンボリックリンクがあると、`os.path.exists` が「無い」と判定して衝突にせず、書き出しでリンクを置き換えてしまう（task_02 の codex-reviewer 指摘③・採用）。暫定 59 §3.2「読めない既存の子は衝突」に合わせる。
**application 限定（`sample_install.py` の 1 行）・JSON スキーマ不変。**

## 対象範囲（application 限定・既存ファイルの変更のみ）

### `keyseq/application/config_service/sample_install.py`

- `_find_conflicting_children` の `if not os.path.exists(child_path):` を `if not os.path.lexists(child_path):` に変える（リンク切れは読み取りで失敗 → 衝突になる）。他は変えない

### `tests/test_sample_install.py`（クラス末尾に 1 件追加・既存テストの途中に差し込まない）

- `test_broken_symlink_child_blocks_install_without_writes`: `user/sequences/copy.json` をリンク先の無いシンボリックリンクにして `install()` → `incomplete`・`error` に `user/sequences/copy.json`・`save_json` 未呼び出し・リンクがそのまま残る（`os.path.islink` が真）
- シンボリックリンクを作れない環境（Windows で権限が無い等の `OSError` / `NotImplementedError`）は `self.skipTest(...)` で飛ばす

## 読むファイル

1. `keyseq/application/config_service/sample_install.py:87-104`（`_find_conflicting_children`）
2. `tests/test_sample_install.py:167-178`（`test_different_leftover_child_blocks_install_without_writes`・手本）と末尾

## 含まない

- Codex ①（空の標準フォルダ・受容）・②（`.tmp`・除外）の対応
- 正本の更新（task_03）・実機目視（task_02）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sample_install` が pass（追加の 1 件は pass または環境による skip）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_02 でまとめて実施。
