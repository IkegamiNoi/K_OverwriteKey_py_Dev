# task_06b_quarantine_delete

## 目的

**隔離済みの実行単位を削除できるようにする**。根拠は暫定仕様 10 **§3-8**（削除・**v0.5**）
+ **§3-9**（UI）+ **受け入れ条件 12 / 19 / 21**。

- **このフェーズ唯一の不可逆操作**。**誤削除を最優先で防ぐ**こと。
- **レイヤ制約**: **application（削除の実行）+ presentation（削除ボタン・確認・結果表示）**。
  domain / infrastructure は不変。**スキーマ不変**。
- **`reviewer` に加えて Codex の敵対的レビューを通す**（ユーザー判断 2026-09-06。
  毎タスクではなく**不可逆・高リスクのタスクに限る**方針）。
- 正本の規範: `data_schema.md` **§5.7**（stored 表記。canonical は比較専用）。

### 削除の不変条件（**MUST**）

1. **削除 API はパスを受け取らない。実行単位 ID だけを受け取る**（Codex High 3・§3-8）。
   **UI から渡された文字列を信用しない**。
2. **①②③の検証は緩和しない**（1 つでも満たさなければ拒否）:
   - ① 隔離ルート**直下**に実在するディレクトリである
   - ② 名前が実行単位の形式（`UNIT_ID_PATTERN`。`_2` / `_3` は**ゼロ埋めなし・上限なし**）
   - ③ **canonical が隔離ルート自身と一致しない**
     （**`is_path_within` は同一パスも「配下」と判定する**〔`__init__.py:738` の docstring〕ため、
     それだけに頼ると**隔離ルートごと再帰削除され得る**）
3. **④「有効な `manifest.json` を持つ」は既定では必須**。ただし
   **呼び出し側が明示的に許可したときだけ上書きできる**（**v0.5 の緩和**。下記）。
4. **削除の実体は実行単位ディレクトリの再帰削除**（`manifest.json` も一緒に）。
   **OS のゴミ箱へ送らない通常削除**（新規依存を足さない）。
5. **シンボリックリンクは辿らず、リンク自体を削除する**（隔離ルート外への脱出を防ぐ）。
6. **削除前に対象パスを全件提示**し、**不可逆である旨を確認画面に明記**する。

### 【v0.5 で確定】マニフェスト不正な単位の削除

暫定仕様 **§3-8（v0.5）** と `decisions.md`「【task_06b 起票時】」が正。

- §3-7 によりマニフェスト不正な単位は**復元できない**。④を絶対条件にすると
  **アプリからは復元も削除もできない残骸**が残り、**§4-A の判断**
  （消せない隔離物が残ると結局エクスプローラで消すことになり事故りやすい）**と矛盾する**。
- → **④のみ「強い確認」で上書きできる**。**①②③は緩和しない**。
- **一覧の「マニフェスト不正」表示と §3-7 の復元不可は不変**。

## 対象範囲

### 1. `keyseq/application/config_service/quarantine.py`（**公開名への変更のみ**）

**task_06 の `reviewer` 指摘への対応**（本タスクで削除の境界検証にも必要）:

- `_is_real_path_within` → **`is_real_path_within(path: str, root: str) -> bool`** へ公開する。
- **既存の呼び出しを追随させる**: `quarantine.py` 内（3 箇所前後）と
  **`quarantine_manage.py:54,89,139`**（兄弟モジュールから private を直接呼んでいた箇所）。
- **振る舞いは変えない**。これ以外の変更をしない。

### 2. `keyseq/application/config_service/quarantine_manage.py`（削除 API の追加）

**定数**

```python
DELETE_REJECTED_INVALID_ID = "invalid_unit_id"      # ①② を満たさない
DELETE_REJECTED_IS_ROOT = "is_quarantine_root"      # ③ に該当
DELETE_REJECTED_NO_MANIFEST = "no_manifest"         # ④ 不成立かつ許可されていない
DELETE_FAILED = "delete_failed"                     # 実 I/O 失敗
```

**結果型**

```python
@dataclass(frozen=True)
class QuarantineDeleteResult:
    unit_id: str
    deleted: bool
    aborted_reason: str      # 拒否・失敗の理由コード（成功時は ""）
```

**公開関数**

```python
def collect_unit_paths(service, unit_id: str, *, config_root: str) -> tuple[str, ...]:
    """削除前の全件提示に使う、実行単位配下のファイルパス（stored 表記）を集める。"""


def delete_quarantine_unit(
    service,
    unit_id: str,
    *,
    config_root: str,
    allow_invalid_manifest: bool = False,
) -> QuarantineDeleteResult:
```

`collect_unit_paths` の振る舞い:

- **①②③の検証を通らなければ空タプル**を返す（**提示のためだけに検証を緩めない**）。
- 実行単位配下を再帰的に列挙し、**`to_config_relative_or_absolute` の stored 表記**で返す。
  **`manifest.json` も含める**（一緒に消えるため）。
- **シンボリックリンク / ジャンクションは辿らない**。リンク自体を 1 件として数える。
- **`canonical_path` の値を返さない**。

`delete_quarantine_unit` の振る舞い（**この順で**）:

1. **①② の検証**: `unit_id` が `quarantine.UNIT_ID_PATTERN` に一致し、
   `<隔離ルート>/<unit_id>` が**隔離ルート直下に実在するディレクトリ**であること。
   満たさなければ `DELETE_REJECTED_INVALID_ID` で**何もしない**。
   - **`unit_id` にパス区切り・`..`・空・空白は当然に弾かれる**こと（正規表現で担保）。
2. **③ の検証**: 解決したパスの canonical が**隔離ルート自身と一致しない**こと
   （**`is_path_within` だけに頼らない**）。加えて **`is_real_path_within`（realpath）で
   隔離ルート配下**であることも確認する（ジャンクション対策）。
   満たさなければ `DELETE_REJECTED_IS_ROOT` で**何もしない**。
3. **④ の検証**: `manifest.json` が**有効**（トップレベルが `dict` かつ `entries` が `list`）であること。
   - 無効で **`allow_invalid_manifest` が偽**なら `DELETE_REJECTED_NO_MANIFEST` で**何もしない**。
   - 無効でも **`allow_invalid_manifest` が真なら続行**する（v0.5）。
4. **再帰削除**: `shutil.rmtree`。**失敗したら `DELETE_FAILED`**（例外を握り潰さず理由コードへ落とす）。
   - **実測済みの前提**: **Python 3.14 の `shutil.rmtree` はジャンクションを辿らない**
     （リンク先の外部ファイルが残ることを確認済み）。**この挙動をテストで固定する**こと。
5. 削除後、**隔離ルートが空になったら隔離ルートも削除**してよい（best-effort。
   失敗しても `deleted=True` を変えない）。

### 3. 変更: `keyseq/application/config_service/__init__.py`（2 箇所）

**1 行委譲のファサード**を 2 つ追加する（`collect_unit_paths` / `delete_quarantine_unit`）。
**`allow_invalid_manifest` を必ず転送する**こと。

### 4. 変更: `keyseq/presentation/quarantine_manage_text.py`（関数 2 つ追加）

```python
def format_delete_plan(unit, paths, *, manifest_valid: bool) -> tuple[str, ...]:
def format_delete_result(result) -> tuple[str, ...]:
```

- `format_delete_plan`:
  - **先頭に「この操作は取り消せません。」**（**MUST**・§3-8）。
  - `f"削除する実行単位: {unit_id}"` + **削除されるパスを全件列挙**。
  - **`manifest_valid` が偽のとき**は、さらに（**MUST**・v0.5）:
    - **「マニフェストが読めないため、中身を確認できません。」**
    - **「ディレクトリごと削除します。」**
    を**通常の削除とは別の行として**加える。
- `format_delete_result`: 成功・拒否・失敗を**理由コードのラベル**で出す
  （**未知コードはコードのまま**）。拒否時は**「削除していません」**を明記する。
- **`orphan_sweep_text.py` を変更しない**。

### 5. 変更: `keyseq/presentation/dialogs/quarantine_manage_dialog.py`（削除ボタンの追加）

- ボタン「**削除する…**」を「復元する…」の隣へ追加する。
- `self.action` に **`"delete"`** を取り得るようにする（既存の `""` / `"restore"` に追加）。
- **選択が無ければ何もしない**。**これ以外の変更をしない**（レイアウト・既存の属性名は維持）。

### 6. 変更: `keyseq/presentation/controllers/config_io/quarantine_manage_io.py`

`action == "delete"` の分岐を追加する（既存の一覧・復元の経路は**無変更**）。

1. `collect_unit_paths(...)` で対象を集める。**0 件でも続行する**
   （空の実行単位ディレクトリも削除対象になり得る）。
2. **`ReferenceCleanupDialog`**（**task_05 で引数化済み。再改修しない**）を
   `header="削除する内容を確認してください。"` / `run_label="削除する"` /
   `lines=format_delete_plan(unit, paths, manifest_valid=unit.manifest_valid)` で開く。
3. `result` が偽なら**何もしない**。
4. 真なら `delete_quarantine_unit(..., allow_invalid_manifest=not unit.manifest_valid)` を呼ぶ。
   - **`allow_invalid_manifest` を無条件に `True` にしない**（マニフェストが有効な単位では
     既定の拒否経路を残す）。
5. 結果を `format_delete_result` で `showinfo`。
6. **`dirty_tracker` / `app.data` を触らない**。

### 7. テスト

- `tests/test_quarantine_manage.py` へ削除のテストを追記。
- `tests/test_quarantine_manage_text.py` へ表示のテストを追記。
- `tests_ui/test_quarantine_manage_flow.py` へ UI フローを追記
  （**`delete_quarantine_unit` を `patch.object`** し、**実ファイルを消さない**）。

### 設計メモ / 制約

- **`quarantine.py` の隔離ロジック・`quarantine_manage.py` の復元ロジックを変更しない**
  （`is_real_path_within` の公開名対応を除く）。
- **`ReferenceCleanupDialog` を再改修しない**（task_05 で引数化済み）。
- **`orphan_sweep_*` / `reference_cleanup_*` を変更しない**。
- **`allow_invalid_manifest` を application 側の既定で真にしない**（既定は拒否）。
- 例外を握り潰さない（理由コードへ落とすのは可。`except: pass` は不可）。
- 関数はおおむね 30 行以内・ファイルは 300 行以内を目安に分割する
  （`quarantine_manage.py` は現在 219 行。**超えるなら削除を別モジュールへ分ける**ことも可）。

## 含まない

- **マニフェスト不正な単位の「復元」** = **不可のまま**（§3-7。v0.5 でも変更していない）。
- **孤児候補・復元の行ごとの選択 UI** = スコープ外（§3-9）。
- **隔離ルートそのものを削除する機能** = **作らない**（検証③で拒否する対象）。
- **OS のゴミ箱への送付 / `send2trash` 等の新規依存** = **禁止**（§3-8）。
- **統合確認・実機目視の観点リスト** = **task_07**。
- 正本 `spec_detail/` の改訂 = **task_08**。

## 確認

`.venv` の python で実行する（worktree ルートから）。

```
..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui
..\..\..\.venv\Scripts\python.exe -m tests.smoke_app
```

**単体テストの項目**（`tests/test_quarantine_manage.py` へ追記・**実ファイルで検証**）:

1. **正常削除**: 有効な単位を削除すると**実行単位ディレクトリと `manifest.json` が消える**
   （受け入れ条件 12 / 19）。`deleted=True`。
2. **①② の拒否**: `unit_id` に **空 / 空白 / `..` / `../../etc` / パス区切り入り / 形式違い
   （`foo` / `2026-09-06`）/ 実在しない ID** を渡すと `DELETE_REJECTED_INVALID_ID` で
   **何も削除されない**（**隔離ルートも他の実行単位も無傷**であることを実体で確認する）。
3. **③ の拒否（最重要）**: **隔離ルート自身を指す値**を渡しても拒否される
   （`DELETE_REJECTED_IS_ROOT`）。**隔離ルートと他の実行単位が残る**ことを実体で確認する。
   ※ `is_path_within` は同一パスも配下と判定するため、この検証が無いと**全実行単位が消える**。
4. **③ の拒否**: **実体がジャンクションで隔離ルート外を指す**実行単位は削除されない
   （ジャンクションを作れない環境では `skipTest`）。**リンク先の外部ファイルが無傷**であること。
5. **④ の拒否**: マニフェストが無い / 壊れている / `entries` が list でない単位は、
   **`allow_invalid_manifest=False`（既定）で `DELETE_REJECTED_NO_MANIFEST`**。**何も削除されない**。
6. **④ の緩和（v0.5）**: 同じ単位でも **`allow_invalid_manifest=True` なら削除できる**。
   **①②③は緩和されない**ことを、隔離ルート自身 / 不正 ID と組み合わせて確認する
   （`allow_invalid_manifest=True` でも 2・3 の拒否は変わらない）。
7. **シンボリックリンク / ジャンクションを辿らない**: 実行単位配下にジャンクションを作って削除すると、
   **リンクは消えるがリンク先の外部ファイルは残る**（**Python 3.14 の `rmtree` の挙動を固定する**。
   作れない環境では `skipTest`）。
8. **削除失敗**は `DELETE_FAILED` として返り、**例外が漏れない**（`shutil.rmtree` を例外に差し替える）。
9. **隔離ルートが空になったら隔離ルートも消える**。**他の実行単位が残っていれば隔離ルートは残る**。
10. **`collect_unit_paths`**: 実行単位配下のファイルを**再帰的に**列挙し、**`manifest.json` を含む**。
    **stored 表記**（canonical でない）で返る。**リンクは辿らず 1 件として数える**。
11. **`collect_unit_paths`**: **①②③を通らない `unit_id` では空タプル**を返す
    （提示のためだけに検証を緩めていないこと）。
12. **復元との共存**: 削除しても**他の実行単位の復元が壊れない**（一覧・復元が従来どおり動く）。
13. `ConfigService.collect_unit_paths` / `delete_quarantine_unit` の戻り値がモジュール関数と一致し、
    **`allow_invalid_manifest` が転送される**（**真偽を変えて差が出ることを確認する**）。

**表示の項目**（`tests/test_quarantine_manage_text.py` へ追記）:

14. `format_delete_plan` の**先頭に「取り消せません」**の趣旨が出る（**MUST**）。
15. `format_delete_plan` に**削除されるパスが全件**出る。
16. **`manifest_valid=False` のとき**、**「中身を確認できません」**と**「ディレクトリごと削除します」**が
    **通常の削除には出ない別行として**加わる（**MUST**・v0.5）。
17. `format_delete_result` が成功・各拒否理由・失敗を日本語ラベルで出し、
    **拒否時は「削除していません」**を明記する。**未知コードはコードのまま**出る。
18. 戻り値がすべて `tuple[str, ...]` で、**canonical 表記を含まない**。

**UI フローの項目**（`tests_ui/test_quarantine_manage_flow.py` へ追記）:

19. **「削除する…」→ 確認ダイアログが `run_label="削除する"` で開く**。
    **キャンセルで `delete_quarantine_unit` が呼ばれない**・**実行で呼ばれる**。
20. **`manifest_valid=False` の単位を選んだとき、`allow_invalid_manifest=True` が渡る**。
    **有効な単位のときは `False` が渡る**（**無条件に真にしていないこと**）。
21. **未選択では削除が呼ばれない**。
22. **既存の復元フローが壊れていない**（`action == "restore"` の経路が従来どおり）。
23. **`dirty_tracker` / `app.data` が変化しない**。
24. **UI テストが実ファイルを消さない**（`delete_quarantine_unit` を patch）。

**退行の基準**: `tests` は **377 → 増加**、`tests_ui` は **279 → 増加**（どちらも減らさない・実測 2026-09-06）。
既存の `tests/test_quarantine.py` 24 件 / `tests/test_orphan_scan.py` 31 件 /
`tests_ui/test_orphan_sweep_flow.py` 30 件 / `tests_ui/test_reference_cleanup_flow.py` 9 件 /
`tests/test_reference_cleanup_text.py` 8 件は**無変更で全 pass**
（`is_real_path_within` の公開名変更に伴う**参照の追随のみ可**。理由を報告に含める）。
smoke pass。実行後に**worktree ルートへ `user/` も `quarantine/` も生成されていない**ことを確認する。

## 完了条件

- 上記「確認」がすべて pass（実測は **`verifier`**。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（5 観点）。特に:
  - **検証①②③が緩和されていない**か（**`allow_invalid_manifest=True` でも**）。
  - **③が `is_path_within` だけに頼っていない**か（**隔離ルート自身を消せない**か）。
  - **削除 API がパスを受け取っていない**か。
  - **`allow_invalid_manifest` が既定で偽**で、**UI が無条件に真を渡していない**か。
  - **不可逆の明記と全件提示**があるか。**マニフェスト不正時の追加文言**があるか。
  - `quarantine.py` / 復元ロジック / `ReferenceCleanupDialog` を不要に変更していないか。
- **Codex の敵対的レビュー（`codex-adversarial-reviewer`）を通す**（ユーザー判断）。
  指摘は**提示のみ**とし、採否はユーザーが決める。
- **実機目視は行わない**（**task_07 でまとめて実施**）。ただし task_07 の目視観点に
  **「隔離 → 削除で実体が消えること」**と**「マニフェスト不正な単位の削除時に警告文が出ること」**を含める。
