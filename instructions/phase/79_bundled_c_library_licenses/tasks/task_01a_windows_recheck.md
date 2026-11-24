# task_01a_windows_recheck

## 目的

task_02 / task_02a の変更後の最終のコードを Windows で確かめる（task_03 のレビューの C・`../task03_review_decisions.md`）。**Windows で実施**。コードの変更は無い見込み。

## やること

1. 標準検証 4 種（compileall・`tests`・`tests_ui`・smoke。`..\..\..\.venv\Scripts\python.exe`）。`tests.test_third_party` は Windows で skip 無し（Zstandard の照合が必須になったので、import できなければ失敗する）
2. `dist/keyseq/_internal/_tcl_data` に `cookiejar*/public_suffix_list.dat.gz` があるかを確かめ、task_01 の記録の追記を更新する（あれば Tcl の行に対応づけ・義務の判定は Mac と同じ）
3. ライセンスの窓の目視（ユーザー）: 21 行（task_02b で義務の無い 4 行を外した）・Zstandard の全文の末尾に xxHash・threading・divsufsort の節が出る
4. 出荷ごとの棚卸しの記録の初回として `packaging/inventory/<版>.md` を作るかは出荷時に行う（このタスクでは作らない）

## 完了条件

- 上の 1〜3 が済み、結果を本ファイルの末尾に記録した
