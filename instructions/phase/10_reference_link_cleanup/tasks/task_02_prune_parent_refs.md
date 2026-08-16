# task_02_prune_parent_refs

## 目的

参照元の掃除の**除去（書き込み）**を application 層へ追加する（暫定仕様 09 **§3-2**）。
task_01 の検査結果を入力に、**実在しない参照元だけを子JSON から取り除く**。

**レイヤ制約**: **application 限定**。変更するのは **task_01 で作った
`config_service/parent_refs_cleanup.py` と そのテスト**のみ。
**presentation は変更しない**（UI は task_03 / task_04）。**保存フロー・JSON スキーマを変更しない**。

## 対象範囲（application 限定）

### 1. `keyseq/application/config_service/parent_refs_cleanup.py`（追記）

#### 1-1. 除去関数

```python
def prune_parent_refs(service, inspections, *, runtime, config_root, keymap_set_path) -> <結果型>:
```

`inspections` は task_01 の `inspect_parent_refs` が返した検査結果のリスト。

**処理の規則**（1 件ずつ・この順序で）:

1. **`CLEANUP_TARGET` / `CLEANUP_ALL_STALE` の要素だけを処理する**。
   `CLEANUP_PROTECTED` は**除去するものが無い**ので書き込まない（no-op）。
2. **対象ファイルの JSON を丸ごと読み直す**
   （`service._load_optional_json(service.resolve_config_path(stored_path, config_root))`）。
   - **`None` が返る / dict でない場合は書かずに「失敗」として記録**し、次の要素へ進む
     （`None` を「refs 無し」と解釈して書き戻すと**他のキーを壊す**）。
   - **検査時に読んだ内容を書き戻してはならない**。書き込みは**ドキュメント全体の置換**なので、
     確認ダイアログの表示中に外部（別実装・手編集）が加えた変更を消してしまう。
3. **読み直した内容で判定をやり直す**（検査時の結果をそのまま適用しない）:
   - refs = **`service._normalize_parent_refs(data.get(service.PARENT_REFS_KEY))`**
   - **`None`（所有元不明）なら書かずにスキップ**（失敗ではない）。
   - **実在判定と保護対象の判定は task_01 と同じ規則・同じヘルパを使う**
     （**判定規則を二重に実装しない**。必要なら task_01 の private ヘルパを共用する）。
4. **残す参照元 = 実在するもの + 保護対象**。**記録されていた順序と表記を保つ**
   （`canonical_path` の値を混ぜない）。
5. **除去対象が 0 件なら書き込まない**（**冪等**。2 回目の実行が no-op になる）。
6. 1 件以上あれば、**読み直した dict の `_parent_refs` だけを差し替えて保存する**
   （`service.repository.save_json`）。
   - **全件が実在しない場合は `[]` を書く**（**キーごと削除しない**。正本 §5.1）。
   - **`_parent_refs` 以外のキーを変更しない**。
   - 保存が例外を投げた場合は**「失敗」として記録し、次の要素へ進む**
     （**1 件の失敗で全体を中止しない**。§3-2）。
7. **runtime を変更しない**（掃除の結果を runtime へ反映しない。暫定仕様 §2）。

#### 1-2. 結果の型

**Tk 非依存の凍結データクラス**を 1 つ追加する（表示都合を持たせない）。最低限:

| 名前 | 内容 |
|---|---|
| 更新したファイル | 実際に書き込んだ子の `stored_path`（記録表記）とその**除去件数** |
| 失敗したファイル | `stored_path` と**失敗理由の判定名** |

**失敗理由も判定名（モジュール定数）で表す**（例: 読めない / 内容が不正 / 書き込み失敗）。
**表示文言は持たせない**（文言は task_03）。

### 2. テスト `tests/test_parent_refs_cleanup.py`（追記）

task_01 と同じ流儀（`ConfigService(JsonRepository())` + `tempfile.TemporaryDirectory()` の実ファイル）。
**最低限、次を固定する**:

- **実在しない参照元だけが消え、実在する参照元は記録表記のまま残る**
- **全件が実在しない場合は `[]` が書かれ、キーは残る**（`None` にならない）
- **保護対象**（現在の keymap_set / trigger_set）は**実在しなくても残る**
- **`_parent_refs` 以外のキーが 1 つも変化しない**（子JSON の round-trip）
- **【重要】除去直前の読み直しが効いている**: 検査した後・除去する前に、**外部から同じファイルの
  別キーを書き換えておく**と、**その変更が保たれたまま** `_parent_refs` だけが更新される
  （検査時のスナップショットを書き戻していないこと）
- **【重要】読み直しで stale が解消していたら書き込まない**（冪等・no-op。
  ファイルの更新時刻またはバイト列が変わらないことで確認する）
- **2 回連続で実行しても結果が変わらない**（冪等）
- **読めないファイル（壊れた JSON / dict でない）は失敗として報告され、他のファイルの処理は続く**
- **書き込みが例外を投げた場合も失敗として報告され、他のファイルの処理は続く**
  （`repository.save_json` を特定パスだけ例外にする形で再現する）
- **`CLEANUP_PROTECTED` の要素は書き込まれない**
- **runtime が変化しない**

### 設計メモ / 制約

- **判定規則を task_01 と二重化しない**。実在判定・保護対象の判定は**共通のヘルパへ寄せる**
  （検査と除去で結果が食い違うと、UI の表示と実行結果が乖離する）。
- **`__init__` を import しない**（循環回避）。定数は **`service.PARENT_REFS_KEY`** のように
  `service` 経由で参照する（リテラルを書かない）。
- **`service._load_optional_json` / `service._normalize_parent_refs` の利用は可**
  （兄弟モジュールが `service` の private を使うのは既存の流儀）。
- **`config_service/__init__.py` へ委譲を足さない**（本タスクでは不要。必要になるのは task_04）。
- **競合（読み直し〜書き込みの間の外部変更）は対象外**（正本 §5.8.3 / §5.10.3 と同水準。
  **版情報の照合は行わない**）。

## 含まない

- **提示テキストの整形**（表示名・文言・パスの省略表示）→ **task_03**
- **ダイアログ・メニュー・未保存時の保存確認導線・結果通知の表示** → **task_04**
- **`config_service/__init__.py` への委譲メソッドの追加** → **task_04**
- **runtime への反映**（暫定仕様 §2 で「反映しない」と確定）
- 全走査 / 孤児検出 / 逆方向検査（→ [idea_12](../../../backlog/idea_12_orphan_child_file_sweep.md)）

## 確認

- 追記したテストが上記の全項目を含み pass する
- **既存テストが件数・内容とも不変**で pass する（`keyseq/` の既存ファイルを変更しないため）
- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests`（現行 **247** + 追加分）/ `-m unittest discover -s tests_ui`（**229**・不変）/
  `-m tests.smoke_app` がいずれも pass（実測は `verifier`）
- 実行後に **worktree ルートへ `user/` が生成されていない**こと

## 完了条件

- 上記確認が pass・**`reviewer` 採用**。
- 差分が **`keyseq/application/config_service/parent_refs_cleanup.py` と
  `tests/test_parent_refs_cleanup.py` の 2 ファイルのみ**であること。
- 実機目視は**本タスクでは行わない**（task_05 でまとめて実施）。
