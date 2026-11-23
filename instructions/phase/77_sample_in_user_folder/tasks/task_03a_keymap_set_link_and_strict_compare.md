# task_03a_keymap_set_link_and_strict_compare

## 目的

フェーズ完了判定前の Codex 敵対的レビュー指摘 1・3（採用）を直す。①構成セット本体がリンク切れのシンボリックリンクだと「無い」とみなして置き換える ②子の照合で JSON の `false` と `0` を同一視する（Python の `False == 0`）。正本 `data_schema.md` §5.14 の「既存の構成セットは手を付けない」「中身の違う子があれば何も書かない」に合わせる。
**application 限定（`sample_install.py`）・JSON スキーマ不変。**

## 対象範囲（application 限定・既存ファイルの変更のみ）

### `keyseq/application/config_service/sample_install.py`

- `install_sample` の `if os.path.exists(path):`（63 行付近）を `os.path.lexists(path)` にする。リンク切れの構成セットは `check_sample_complete` が読めず False → `incomplete`（何も書かない）になる。他は変えない
- `_find_conflicting_children` の比較を、真偽値と数値を区別する形にする: `json.dumps(existing, ensure_ascii=False, sort_keys=True) == json.dumps(payload, ensure_ascii=False, sort_keys=True)`（`expected = json.loads(json.dumps(payload))` の行は不要になれば消す）。キー順は無視・値の型は区別する

### `tests/test_sample_install.py`（クラス末尾に 2 件追加・既存テストの途中に差し込まない）

- `test_broken_symlink_keymap_set_is_incomplete_without_writes`: `user/keymap_sets/sample.json` をリンク先の無いシンボリックリンクにして `install()` → `incomplete`・`save_json` 未呼び出し・リンクが残る。symlink を作れない環境は `skipTest`（task_02a のテストと同じ書き方）
- `test_bool_and_number_difference_is_conflict`: 1 回書き出してから構成セットだけ消し、子の 1 つ（JSON に `false` を含むもの。例: 書き出したキーマップかトリガー一覧の JSON を読み、値が `False` のキーを 1 つ `0` に変えて保存）→ `install()` が `incomplete`・`error` にそのパス・snapshot 不変

## 読むファイル

1. `keyseq/application/config_service/sample_install.py:56-104`
2. `tests/test_sample_install.py:167-178`・末尾（task_02a のテスト `test_broken_symlink_child_blocks_install_without_writes`）

## 含まない

- Codex 指摘 2（リンク・ジャンクション構成）・4（個別プリセットの参照）の対応（除外）
- 正本・decisions_archive の更新（メインが task_03 の中で行う）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sample_install` が pass（symlink のテストは環境により skip）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。実機目視は不要（初回起動の流れは不変）。
