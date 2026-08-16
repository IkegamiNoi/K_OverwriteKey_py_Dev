# task_03_cleanup_text

## 目的

参照元の掃除の**提示テキストの整形**を presentation 層へ新設する（暫定仕様 09 **§3-3 / §3-4**）。
確認 UI（1 枚）に出す**消える参照元の全件列挙**と、実行後の**結果通知**の文言を、
**Tk 非依存の純関数**として組み立てる。

**レイヤ制約**: **presentation 限定・新規モジュールのみ**。**Tk を import しない**。
**application は変更しない**（task_01 / task_02 の成果をそのまま使う）。
**ダイアログ・メニューは作らない**（task_04）。

## 対象範囲（presentation 限定・新規モジュール）

### 1. `keyseq/presentation/reference_cleanup_text.py`（新規）

**presentation 直下**に置く（`child_save_rows.py` と同じ「純モジュール」の位置づけ）。

- **`tkinter` を import しない**（純関数のみ）。
- **`keyseq/presentation/dialogs/` の中に置かない**。同パッケージの `__init__.py` は
  全ダイアログを import するため、**`tkinter` と `pynput` を巻き込み**、`tests/` から
  純関数だけをテストできなくなるため（配置の根拠。`file_organization_rules.md` の
  「所有者の近くに置く」より**テスト可能性を優先**した判断）。

#### 1-1. 確認 UI 用のテキスト

```python
def format_cleanup_plan(inspections) -> tuple[str, ...]:
```

`inspections` は task_01 の `inspect_parent_refs` の戻り値。**表示用の行のタプル**を返す
（結合・描画はダイアログ側の責務）。

**規則**:

- **子ファイルごとにブロックを作る**。ブロックには次を含める:
  - **子の種類の表示名**（キーマップ / トリガー一覧 / シーケンス 等）と**子ファイルのパス**
    ※**種類の呼び名は既存の文言に揃える**（`child_save_rows.py` や
    `spec_detail/data_schema.md` §5.8 の用語を確認して合わせる）
  - **消える参照元のパスを全件**（**省略・件数への丸めをしない**）。
    理由: 一時的に到達不能な媒体（外付け / ネットワークドライブ未接続）を掃除すると
    **生きている参照元を恒久的に消す**ため、ユーザーが目視で気づけるようにする。
  - **`CLEANUP_ALL_STALE` の子には警告**を添える（**この掃除で参照元が 0 件になる**旨）。
    併せて**子ファイル自体は削除しないこと**、**孤児かどうかはこの検査範囲では判定できない**ことを示す。
  - **保護対象（`protected_refs`）がある場合は「残す」側として明示**する
    （**消える側に混ぜない**。§3-1 で保護対象は除去しないと確定しているため、
    ここで消えるように見せると表示と実行結果が食い違う）。
- **`CLEANUP_PROTECTED` だけの子**（消えるものが無い）は、**「消える」ブロックに出さない**。
  出す場合は**保護のため残す**とわかる形にする。
- **先頭に要約行**を置く（**対象ファイル数**と**消える参照元の総数**）。
- **並び順は `inspections` の順序を保つ**（task_01 が keymap → trigger_set → sequence で固定済み）。

#### 1-2. 実行結果のテキスト

```python
def format_cleanup_result(result) -> tuple[str, ...]:
```

`result` は task_02 の `prune_parent_refs` の戻り値。

- **更新したファイル数**と**除去した参照元の総数**を出す。
- **失敗したファイルは全件出す**（パス + 理由）。
  **失敗理由の定数（`PRUNE_FAILURE_*`）を日本語の文言へ変換する**のはこの関数の責務
  （application 側は定数のみを持つ）。
- 失敗が 0 件のときは失敗の節を出さない。

#### 1-3. 対象 0 件のメッセージ

検査結果が 0 件のときに使う文言を**モジュール定数**として持つ（例:「掃除する項目はありません。」）。

### 2. テスト `tests/test_reference_cleanup_text.py`（新規）

**`tests/` に置く**（Tk 非依存のため）。`inspect_parent_refs` / `prune_parent_refs` の
**戻り値型を直接組み立てて**渡す（実ファイルは不要）。**最低限、次を固定する**:

- **消える参照元が全件出る**（3 件以上を渡して、**省略や「ほか N 件」に丸められない**こと）
- **`CLEANUP_ALL_STALE` の子に警告が付く** / `CLEANUP_TARGET` には付かない
- **保護対象は「残す」側に出て、「消える」側には出ない**
- **`CLEANUP_PROTECTED` だけの子が「消える」対象として提示されない**
- **要約行の件数**（対象ファイル数・消える参照元の総数）が正しい
- **並び順が入力の順序どおり**
- **失敗理由の定数 3 種**（`PRUNE_FAILURE_UNREADABLE` / `_INVALID_DATA` / `_SAVE_FAILED`）が
  **それぞれ異なる文言へ変換される**
- **失敗 0 件なら失敗の節が出ない**
- 実行結果の**更新件数・除去総数**が正しい

### 設計メモ / 制約

- **戻り値は行のタプル**にする（ダイアログ側が結合・描画する）。
  **改行コードや装飾（罫線など）を持ち込みすぎない**。
- **判定名で分岐する**（`CLEANUP_*` / `PRUNE_FAILURE_*`）。**表示文言で分岐しない**
  （正本 §5.8.4 と同じ規律）。
- **パスは記録表記のまま出す**（`canonical_path` の値を表示へ混ぜない。正本 §5.7）。
- **application の型を import して型注釈に使うのは可**。ただし
  **presentation → application の一方向**を守る（逆流させない）。

## 含まない

- **ダイアログ本体・メニュー項目・未保存時の保存確認導線・結果通知の表示** → **task_04**
- **`config_service/__init__.py` への委譲メソッドの追加** → **task_04**
- application 側（`parent_refs_cleanup.py`）の変更
- パスの省略表示（`_ellipsize_path` 相当）の流用・共有ヘルパの抽出
  （暫定仕様 §3-4 で「**流用しない**」と確定済み）

## 確認

- 新規テスト `tests/test_reference_cleanup_text.py` が上記の全項目を含み pass する
- **既存テストが件数・内容とも不変**で pass する
- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests`（現行 **257** + 追加分）/ `-m unittest discover -s tests_ui`（**229**・不変）/
  `-m tests.smoke_app` がいずれも pass（実測は `verifier`）
- **新モジュールが `tkinter` を import していない**こと（grep で確認できる形）

## 完了条件

- 上記確認が pass・**`reviewer` 採用**。
- 差分が **`keyseq/presentation/reference_cleanup_text.py`（新規）と
  `tests/test_reference_cleanup_text.py`（新規）の 2 ファイルのみ**であること。
- 実機目視は**本タスクでは行わない**（task_05 でまとめて実施）。
