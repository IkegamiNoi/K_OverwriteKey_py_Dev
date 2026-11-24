# task_02b_obligated_only

## 目的

ユーザー判断（2026-11-24）「窓に載せるのは表示の義務がある物だけ」を反映する（暫定 60 v0.9・Q2 を覆す）。義務の無い物は行にせず、棚卸しの記録に義務の判定を残す。

## 対象範囲

### メインが行う（全文・文書）

- 全文の削除: `bzip2.txt`・`xz.txt`・`zlib.txt`・`zlib-ng.txt`・`xz_macos.txt`・`libtommath.txt`
- `cpython_incorporated_macos.txt` の末尾の BLAKE2 の節（CC0・義務なし）を外す（HACL* は残す）
- 暫定 60 v0.9・正本 features.md の下書き・codebase_map.md の件数・task_01 / task_02 の記録・`packaging/README.md`

### Codex が行う（データ・テスト）

1. `third_party.json` から次の 6 行を削除する（他の行は変えない）: Windows の `bzip2`・`xz`（5.2.5）・`zlib`・`zlib-ng`、Mac の `libtommath`・`xz`（5.8.4）
2. `tests/test_third_party.py`: `windows_names` から `bzip2`・`xz`・`zlib`・`zlib-ng` を、`mac_names` から `libtommath`・`xz` を除く。`_NON_PYPI_NAMES` から表に無くなった名前（`bzip2`・`libtommath`・`xz`・`zlib`・`zlib-ng`）を除く。他のテストは変えない

## 確認

- Mac: compileall・`tests.test_third_party`・`tests`・`tests_ui.test_help_window`・smoke（verifier）・ライセンスの窓の目視（19 行）
- Windows: task_01a（21 行）

## 完了条件

- 上の確認 pass・reviewer 採用・Mac の目視 OK

## 実施結果（2026-11-24）

- JSON・テスト: codex-implementer（Luna high）。全文の削除・BLAKE2 の節を外す・文書はメイン
- reviewer: 修正して採用（6 行と BLAKE2 の義務なしの判定は削除前の全文で確認済み・残した 29 行はすべて義務あり。phase.md:21 の旧い Q2 の記述と task_03 の件数を修正）
- verifier（Mac）: compileall clean / `tests.test_third_party` 8 件 OK（skip 1）/ `tests` 2217 件 OK（skip 33）/ `tests_ui.test_help_window` 25 件 OK / smoke OK / win32 21 行・darwin 19 行・JSON の file 26 件がすべて実在し未参照の全文なし
- 再ビルドした `dist/keyseq.app` の表は 19 行・全文あり
- 実機目視（Mac・ユーザー）: 未実施
