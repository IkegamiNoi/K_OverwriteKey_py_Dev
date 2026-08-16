# task_01_cleanup_inspection

## 目的

参照元の掃除の**検査ロジック**を application 層へ新設する（暫定仕様 09 **§3-1**）。
現在の構成セットが参照している子ファイルについて、`_parent_refs` に記録された上位パスの**実在**を調べ、
**保護対象を分離**したうえで**判定名付きの検査結果**を返す。

**レイヤ制約**: **application 限定・新規モジュールのみ**。
**presentation は変更しない**（UI は task_03 / task_04）。**除去（書き込み）は行わない**（task_02）。
**保存フロー・JSON スキーマを変更しない**。

## 対象範囲（application 限定・新規モジュール）

### 1. `keyseq/application/config_service/parent_refs_cleanup.py`（新規）

`config_service` パッケージの**兄弟モジュール**として新設する。既存の兄弟の規約に従うこと:

- **モジュール関数は `service` を第 1 引数に取る**（`service.X` で本体の API を参照する）
- **兄弟から `__init__` を import しない**（循環回避）
- **`config_service/__init__.py` へロジックを足さない**（同ファイルは 737 行で分割保留中。
  公開が要る場合も**委譲 1 行まで**。本タスクでは**委譲を足さない**）

#### 1-1. 検査結果の型

Tk 非依存の**凍結データクラス**を 1 つ定義する（表示都合を持たせない）。フィールド:

| 名前 | 型 | 内容 |
|---|---|---|
| `kind` | str | `"keymap"` / `"trigger_set"` / `"sequence"` |
| `stored_path` | str | 子ファイルのパス（**§5.7 の記録表記のまま**） |
| `alive_refs` | tuple[str, ...] | **実在する**参照元（記録表記のまま） |
| `stale_refs` | tuple[str, ...] | **実在せず、除去対象**の参照元（記録表記のまま） |
| `protected_refs` | tuple[str, ...] | **実在しないが保護対象**のため除去しない参照元 |
| `state` | str | 下記の判定名 |

**判定名はモジュール定数として定義する**（リテラルを散らさない）:
`CLEANUP_TARGET` / `CLEANUP_ALL_STALE` / `CLEANUP_PROTECTED` / `CLEANUP_SKIP`。

#### 1-2. 検査関数

```python
def inspect_parent_refs(service, runtime, *, config_root, keymap_set_path) -> list[<結果型>]:
```

**処理の順序と規則**:

1. **子の列挙は runtime の source_path 3 種のみを根拠にする**
   （`INTERNAL_KEYMAP_SOURCE_PATH`（`keymaps[]` の各要素）/
   `INTERNAL_TRIGGER_SET_SOURCE_PATH`（runtime 直下）/
   `INTERNAL_SEQUENCE_SOURCE_PATH`（`triggers[]` の各要素））。
   - **`resolve_child_save_targets` を使ってはならない**（「次に保存するとしたらどこへ書くか」であり
     実体ではない。未実体化の子に既定パスが割り当てられ、**無関係な既存ファイルを対象にしてしまう**）。
   - **source_path が空 / 非文字列の子は対象外**（未実体化）。
   - 列挙順は **keymap → trigger_set → sequence** で固定する（結果の順序を安定させる）。
2. **同一実体を指す子は 1 件へ重複排除する**（判定は `service.canonical_path`）。
   **先に列挙されたものを採用**し、後続はスキップする（共有 sequence 等で二重処理・二重計上しないため）。
3. 各子の `_parent_refs` を **`service.read_parent_refs(service.resolve_config_path(stored_path, config_root))`**
   で読む。**`None`（所有元不明・読めない・list でない）と `[]`（既知の空）は
   `CLEANUP_SKIP`**（除去するものが無い）。
4. 各参照元の実在を **`os.path.exists(service.resolve_config_path(ref, config_root))`** で判定する。
   **相対表記のまま `os.path` 系へ渡さない**（config 相対を cwd 基準で解決する事故を避ける）。
5. **保護対象を分離する**（実在しなくても除去対象にしない）:
   - `kind` が `"keymap"` / `"trigger_set"` … **現在の `keymap_set_path`**
   - `kind` が `"sequence"` … **現在の trigger_set のパス**
     （runtime 直下の `INTERNAL_TRIGGER_SET_SOURCE_PATH`）
   - 一致判定は **`service.canonical_path` で行う**（表記違いを吸収する）。
     **`canonical_path` の戻り値を `stored_path` / `*_refs` へ混入させない**（比較専用）。
   - 保護対象のパスが**空**なら保護対象なし（未保存など）。
6. **判定名を決める**（この優先順で）:

   | 条件 | `state` |
   |---|---|
   | refs が `None` / `[]` | `CLEANUP_SKIP` |
   | `stale_refs` が 1 件以上 **かつ** `alive_refs` と `protected_refs` がともに 0 件 | `CLEANUP_ALL_STALE` |
   | `stale_refs` が 1 件以上（上記以外）| `CLEANUP_TARGET` |
   | `stale_refs` が 0 件 **かつ** `protected_refs` が 1 件以上 | `CLEANUP_PROTECTED` |
   | 上記以外（実在しない参照元が無い）| `CLEANUP_SKIP` |

7. **戻り値には `CLEANUP_SKIP` を含めない**（一覧に出す対象だけを返す）。
   ※ `CLEANUP_PROTECTED` は**含める**（「保護のため残す」を提示できるようにするため。
   実際に何を表示するかは task_03 / task_04 で決める）。

### 2. テスト `tests/test_parent_refs_cleanup.py`（新規）

`ConfigService(JsonRepository())` を直接生成し、`tempfile.TemporaryDirectory()` の config_root で
実ファイルを作って検証する（既存 `tests/test_child_save_rows.py` / `tests/test_config_service.py` の流儀）。
**最低限、次を固定する**:

- 実在する参照元だけを持つ子は**結果に出ない**（`CLEANUP_SKIP`）
- `_parent_refs` が **無い / `None` / `[]` / list でない**子は**結果に出ない**
- **相対表記と絶対表記・区切り違い**（`\` と `/`）でも実在判定が正しい
- **保護対象**（現在の keymap_set / trigger_set）は、**実在しなくても `stale_refs` に入らず
  `protected_refs` に入る**。表記が違っても保護される
- **判定名 4 種**（`CLEANUP_TARGET` / `CLEANUP_ALL_STALE` / `CLEANUP_PROTECTED`）が
  上記の表どおりに決まる。**保護対象が残る場合は `CLEANUP_ALL_STALE` にならない**
- **source_path が空の子は対象外**
- **同一ファイルを指す複数の子が 1 件に重複排除される**（共有 sequence を 2 トリガーが指すケース）
- **列挙順が keymap → trigger_set → sequence** で安定している
- **検査でファイルが書き換わらない**（読み取りのみ。実行前後で子JSON のバイト列が不変）

### 設計メモ / 制約

- **`os.path.exists` を呼ぶのは解決後のパスだけ**。この repo で 2 度踏んだ事故
  （config 相対値を解決せずに `os.path` 系へ渡し、**リポジトリルートに `user/` が生成される**）を避ける。
- **`canonical_path` は比較専用**。保存値・戻り値・表示へ混ぜない（正本 §5.7）。
- `read_parent_refs` は **strip・完全一致の重複除去・非 str 除去**を行った結果を返す。
  検査結果の `alive_refs` / `stale_refs` はこの**正規化後の値**でよい。
- **`_normalize_parent_refs` の `None` と `[]` の区別**を潰さないこと（`None` は所有元不明）。

## 含まない

- **除去（書き込み）**・`prune_parent_refs` の実装 → **task_02**
- **提示テキストの整形**（表示名・文言・パスの省略表示）→ **task_03**
- **ダイアログ・メニュー・未保存時の保存確認導線** → **task_04**
- **`config_service/__init__.py` への委譲メソッドの追加**（必要になるのは task_02 / task_04。
  本タスクでは足さない）
- 全走査 / 孤児検出 / 逆方向検査（→ [idea_12](../../../backlog/idea_12_orphan_child_file_sweep.md)）

## 確認

- 新規テスト `tests/test_parent_refs_cleanup.py` が上記の全項目を含み pass する
- 既存テストが**件数・内容とも不変**で pass する
  （`keyseq/` の既存ファイルを変更しないため。変更したら不要変更として指摘対象）
- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests`（現行 **238** + 追加分）/ `-m unittest discover -s tests_ui`（**229**・不変）/
  `-m tests.smoke_app` がいずれも pass（実測は `verifier`）
- 実行後に **worktree ルートへ `user/` が生成されていない**こと

## 完了条件

- 上記確認が pass・**`reviewer` 採用**。
- 差分が **`keyseq/application/config_service/parent_refs_cleanup.py`（新規）と
  `tests/test_parent_refs_cleanup.py`（新規）の 2 ファイルのみ**であること。
- 実機目視は**本タスクでは行わない**（task_05 でまとめて実施）。
