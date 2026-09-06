# task_05_quarantine

## 目的

**孤児候補を `<config_root>/quarantine/<実行単位>/` へ隔離（移動）できるようにする**。
根拠は暫定仕様 10 **§3-6**（隔離ルート / 実行単位 / 相対構造の保持 / マニフェスト / 再判定 / 部分失敗）+
**§3-5**（警告があっても実行を許す）+ **§3-9**（確認 UI）+ **受け入れ条件 9 / 10 / 16 / 17 / 20**。

- **本フェーズ初の破壊的 I/O**。**誤隔離と可逆性の破壊を最優先で防ぐ**こと。
- **レイヤ制約**: **application（隔離の実行）+ presentation（確認 UI・結果表示）**。domain / infrastructure は不変。
  **スキーマ不変**（`config.json` は触らない）。
- 正本の規範: `data_schema.md` **§5.7**（マニフェストのパスは stored 表記。**canonical を書かない**）/
  **§5.8.4**（判定名で分岐する）。

### 破壊的 I/O の不変条件（**MUST**・すべて満たすこと）

1. **マニフェストは移動より先に、原子書込みで作る**（Codex High 2）。**書けなければ 1 件も動かさない**。
2. **隔離するのは〔ユーザーへ提示した孤児候補〕∩〔隔離直前の再判定でも孤児候補〕だけ**（H2 / §3-12-3）。
   **再判定で新たに孤児になった候補は隔離しない**（提示していないものを動かさない）。
3. **元ファイルを削除しない**（**移動のみ**）。**runtime / dirty 状態を変更しない**。
4. **隔離ルートは遅延作成**。**隔離を 1 度も実行していない環境に作らない**（L3 / 受け入れ条件 16）。
5. **移動は 1 件ずつ・失敗しても継続**し、失敗を握り潰さず結果に出す。

## 対象範囲

### 新規: `keyseq/application/config_service/quarantine.py`

`orphan_scan.py` / `parent_refs_cleanup.py` と**同じ書き方**にする（`from __future__ import annotations` /
モジュール関数は **`service` を第 1 引数** / 結果は `@dataclass(frozen=True)` / `__init__.py` を import しない /
兄弟モジュールは `from . import orphan_scan`）。

**定数**

```python
QUARANTINE_DIR_NAME = "quarantine"
MANIFEST_FILE_NAME = "manifest.json"

ENTRY_PLANNED = "planned"
ENTRY_MOVED = "moved"
ENTRY_FAILED = "failed"

QUARANTINE_MANIFEST_WRITE_FAILED = "manifest_write_failed"
QUARANTINE_MOVE_FAILED = "move_failed"
```

**結果型**

```python
@dataclass(frozen=True)
class QuarantineResult:
    unit_id: str                                    # 実行単位 ID（中止時は ""）
    moved: tuple[tuple[str, str], ...]              # (kind, original_path〔stored 表記〕)
    failed: tuple[tuple[str, str], ...]             # (original_path〔stored 表記〕, 理由コード)
    dropped_paths: tuple[str, ...]                  # 提示したが再判定で孤児でなくなったもの
    newly_orphan_count: int                         # 再判定で新たに孤児になった件数（隔離しない）
    aborted_reason: str                             # 中止した場合の理由コード（通常は ""）
```

**公開関数**

```python
def quarantine_orphans(
    service,
    presented_paths: list[str],
    *,
    config_root: str,
    scan_dirs: list[str],
    startup_keymap_set_path: str,
    current_keymap_set_path: str,
    protected_paths: list[str],
) -> QuarantineResult:
```

振る舞い（**この順で行う**）:

1. **再判定**（**MUST**・H2）。`orphan_scan.scan_orphans(...)` を**引数をそのまま渡して呼び直す**
   （**presentation 側の再判定に任せない**。ここで必ず走らせることで、再判定の省略を構造的に防ぐ）。
2. **対象の確定**。`presented_paths` と再判定の `ORPHAN_CANDIDATE` を **canonical で照合**し、**積集合**を取る。
   - `presented_paths` にあって再判定で候補でなくなったものは **`dropped_paths`**（stored 表記）へ。
   - 再判定で候補だが `presented_paths` に無いものは**隔離せず** `newly_orphan_count` に数える。
   - **積集合が 0 件なら、ディレクトリを 1 つも作らずに空の結果を返す**（`unit_id=""`）。
3. **実行単位 ID の決定**。`<YYYYMMDD_HHMMSS>`（現在時刻）。
   **同名ディレクトリが既に在れば `_2` / `_3` … と連番を付す**（L4）。
   時刻取得は private ヘルパ `_now()` に切り出す（テストが `patch.object` で差し替えられるように）。
4. **ディレクトリの作成**（**ここで初めて作る**）。`<config_root>/quarantine/<unit_id>/` を `os.makedirs`。
5. **マニフェストの原子書込み**（**移動より先**・**MUST**）。
   - 全対象を `state = ENTRY_PLANNED` の**計画**として書く。
   - 書き込みは **`service.repository.save_json(manifest_path, payload)`**
     （既存実装が `.tmp` へ書いて `os.replace` する原子書込み・`json_repository.py:13-20`。
     **独自の書き込みを実装しない**）。
   - **例外が出たら 1 件も動かさず中止**する。`aborted_reason = QUARANTINE_MANIFEST_WRITE_FAILED` を返し、
     **作成した実行単位ディレクトリが空なら削除**して後始末する（`os.rmdir`。空でなければ残す）。
6. **移動**（1 件ずつ）。
   - 隔離先 = `<config_root>/quarantine/<unit_id>/<config_root からの相対パス>`
     （**元の相対構造を保つ**。例 `.../user/keymaps/foo.json`）。
   - **候補側は必ず config 配下**（task_02 の仕様）なので相対パスは常に取れる。
     万一 config 外だった場合は移動せず `failed` に記録する（**防御的に**）。
   - 親ディレクトリを `os.makedirs(..., exist_ok=True)` してから **`shutil.move`** で移動する
     （`relocate_individual_hotkey_presets` が `shutil` を直呼びする前例に倣う・L10）。
   - **成功のつどマニフェストのそのエントリを `ENTRY_MOVED` へ更新**して書き直す
     （毎回 `save_json`。中断しても計画と進捗が残る）。
   - **失敗しても継続**し、そのエントリを `ENTRY_FAILED` に更新して `failed` へ
     `(original_path, QUARANTINE_MOVE_FAILED)` を積む。**例外を握り潰さず理由コードへ落とす**。
7. **元ファイルの削除・runtime / dirty の変更をしない**。

**マニフェストの形**（§3-6。パスは **`to_config_relative_or_absolute`** の stored 表記・区切りは `/`）:

```json
{
  "created_at": "2026-09-06T10:15:00",
  "entries": [
    {"kind": "keymap",
     "original_path": "user/keymaps/foo.json",
     "quarantined_path": "quarantine/20260906_101500/user/keymaps/foo.json",
     "state": "planned"}
  ]
}
```

### 変更: `keyseq/application/config_service/__init__.py`（2 箇所のみ）

- `from . import orphan_scan, ...` の行へ **`quarantine` を追加**。
- `normalize_scan_dirs` の直後へ **1 行委譲のファサード** `quarantine_orphans` を追加する
  （引数はモジュール関数と同じ。実ロジックを `__init__.py` へ置かない）。

### 変更: `keyseq/presentation/dialogs/reference_cleanup_dialog.py`（**引数化のみ**）

§3-9 / H3 の**ヘッダ文言と実行ボタンラベルの引数化**。**本タスクで行う**
（phase.md は task_06 に置いていたが、**「隔離する」ボタンが必要なのは本タスク**のため前倒しする。
task_06 は引数化済みのものを**使うだけ**にする）。

```python
def __init__(
    self,
    parent: App,
    *,
    title: str,
    lines: tuple[str, ...],
    header: str = "除去する参照元を確認してください。",
    run_label: str = "実行",
): ...
```

- **既定値を現行の固定文字列と同一**にする（`:26` のラベルと `:44` のボタン）。
  これにより **`reference_cleanup_io.py` は無変更**で、**`tests_ui/test_reference_cleanup_flow.py` 9 件も無変更で pass** する。
- **これ以外の変更をしない**（レイアウト・`result` の意味・hook の作法は現状維持）。

### 変更: `keyseq/presentation/orphan_sweep_text.py`（関数 1 つ追加）

```python
def format_quarantine_result(result) -> tuple[str, ...]:
```

- 先頭に `f"隔離しました: {len(result.moved)} 件"`（`unit_id` があれば `f"（実行単位: {unit_id}）"` を続ける）。
- `moved` を `f"{kind ラベル}: {original_path}"` で列挙する。
- `failed` があれば `"移動できなかったファイル:"` + `f"  {path}: {理由ラベル}"`。
- `dropped_paths` があれば `f"提示後に対象外になったため隔離しなかった: {N} 件"`（**件数のみ**）。
- `newly_orphan_count` が 1 以上なら
  `f"再判定で新たに孤児候補になったため今回は隔離しなかった: {N} 件"`（**件数のみ**）。
- `aborted_reason` があれば**先頭に**「隔離を中止しました」+ 理由ラベルを置き、
  **「ファイルは 1 件も移動していません」を明記**する。
- 理由コード → 日本語ラベルの表は同モジュールに置く（未知コードは**コードのまま**出す）。
- **判定名・理由コードの定数を application から import**して分岐する（既存パターン）。

### 変更: `keyseq/presentation/controllers/config_io/orphan_sweep_io.py`

`run_sweep()` の**末尾（結果提示）だけ**を変える。前段（未保存確認 → 設定 → 入口ダイアログ → 走査）は**無変更**。

1. 候補 0 件のとき: **無変更**（`messagebox.showinfo` + `format_orphan_notice`）。
2. 候補 1 件以上のとき（`messagebox.showinfo` を**置き換える**）:
   - `ReferenceCleanupDialog(self._app, title="孤児ファイルの棚卸し",
     lines=format_orphan_plan(result), header="隔離する孤児候補を確認してください。",
     run_label="隔離する")` を開き `wait_window()`。
   - **選択肢は「隔離する / キャンセル」の 2 択だけ**（受け入れ条件 17）。
     **読めなかった参照側があっても実行できる**こと（**警告で抑止しない**・§4-A）。
     **読めなかった親を確認するための UI を作らない**（§3-5）。
   - `dialog.result` が偽なら `return`（**何も動かさない**）。
   - 真なら `self._app.config_service.quarantine_orphans(presented_paths, ...)` を呼ぶ。
     **`presented_paths` = 一覧に出した `ORPHAN_CANDIDATE` の `stored_path`**。
     他の引数は走査時と**同一の値**を渡す（`config_root` / `scan_dirs` / `startup_keymap_set_path` /
     `current_keymap_set_path` / `protected_paths`）。
   - 結果を `messagebox.showinfo("孤児ファイルの棚卸し", "\n".join(format_quarantine_result(...)))` で出す。
- **`dirty_tracker` を触らない**。**`app.data` を書き換えない**。

### 新規・追記: テスト

- 新規 `tests/test_quarantine.py`（**実ファイルで検証する**。`tests/test_orphan_scan.py` と同型）。
- `tests/test_orphan_sweep_text.py` へ `format_quarantine_result` のテストを追記。
- `tests_ui/test_orphan_sweep_flow.py` へ確認ダイアログ経由のフローを追記。
- `tests_ui/test_reference_cleanup_flow.py` は**無変更で 9 件 pass** させる（引数化の既定値で担保）。

### 設計メモ / 制約

- **再判定を presentation でやらない**。`quarantine_orphans` の内部で必ず走らせる
  （呼び忘れ・順序間違いを構造的に防ぐ）。
- **マニフェストの独自書き込みを実装しない**。`service.repository.save_json` が既に
  `.tmp` + `os.replace` の原子書込み（`json_repository.py:13-20`）。
- **`canonical_path` の値をマニフェスト・表示へ書かない**（比較専用。正本 §5.7）。
- **隔離ルートを `ensure_split_config_dirs` に加えない**（L3・受け入れ条件 16）。
- **隔離物が再走査で候補として拾われない**ことをテストで確認する（`quarantine/` は `user/` の外で
  候補側 4 ディレクトリと交差しないため原理的に起きないはずだが、破壊的な経路なので明示的に守る）。
- 例外を握り潰さない（**理由コードへ落として結果に出す**のは握り潰しではない。ログに残らない
  `except: pass` を書かない）。
- 関数はおおむね 30 行以内・新規ファイルは 300 行以内を目安に分割する。

## 含まない

- **復元 / 削除・「隔離の管理…」メニュー・実行単位のリスト選択 UI** = **task_06**
  （マニフェストの読み手・`original_path` のガード・削除の 4 検証はすべて task_06）。
- **孤児候補の行ごとの選択 UI** = スコープ外（暫定仕様 §3-9 で作らないと確定）。
- **読めなかった参照側を確認するための UI** = **作らない**（§3-5 で明示的に禁止）。
- **走査・判定ロジックの変更** = 不可（task_02 の成果をそのまま使う）。
- **`missing_scan_dirs` の表記の不揃いの是正** = 本タスクでは行わない（task_04 からの申し送り）。
- **統合確認・実機目視の観点リスト** = **task_07**。
- 正本 `spec_detail/` の改訂 = **task_08**。

## 確認

`.venv` の python で実行する（`.claude/rules/python_rules.md`。worktree ルートから）。

```
..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui
..\..\..\.venv\Scripts\python.exe -m tests.smoke_app
```

**単体テストの項目**（`tests/test_quarantine.py`・すべて実ファイルで検証する）:

1. **元の相対構造を保って移動**され、`<config_root>/quarantine/<unit_id>/user/keymaps/foo.json` に
   実体があり、**元の場所からは消えている**（受け入れ条件 9）。
2. **`manifest.json` が実行単位ディレクトリ直下に書かれる**。`created_at` / `entries[]` の
   `kind` / `original_path` / `quarantined_path` / `state` を持ち、**パスが stored 表記**
   （config 相対・区切り `/`・**canonical でない**）。
3. **成功したエントリの `state` が `moved`** になっている。
4. **マニフェストが移動より先に書かれる**（**受け入れ条件 20**）。
   `service.repository.save_json` を `patch.object` で包み、**最初の呼び出しが移動より前**であることと、
   その時点の全エントリが `planned` であることを確認する。
5. **マニフェストが書けないときは 1 件も移動しない**（`save_json` を例外送出に差し替える）。
   `aborted_reason` が返り、**元ファイルが全件そのまま**で、**空の実行単位ディレクトリが残らない**。
6. **再判定で対象外になった候補は隔離されない**（提示後にそのファイルを参照する keymap_set を
   置いてから実行する）。`dropped_paths` に入り、**ファイルは動かない**。
7. **再判定で新たに孤児になった候補は隔離されない**（提示後に参照を消す）。
   `newly_orphan_count` に数えられ、**ファイルは動かない**（**受け入れ条件 10**）。
8. **積集合が 0 件のとき、`quarantine/` ディレクトリが作られない**・`unit_id` が空。
9. **隔離を 1 度も実行していない環境に隔離ルートが作られない**（走査だけを行っても
   `<config_root>/quarantine/` が存在しない。**受け入れ条件 16**）。
10. **同一秒に 2 回実行すると `_2` の連番**が付き、**1 回目の実行単位を上書きしない**
    （`_now()` を `patch.object` で固定する）。
11. **移動に失敗しても継続**する（1 件目を移動不能にして 2 件目が成功することを確認）。
    失敗は `failed` に理由コード付きで入り、**マニフェストのそのエントリが `failed`**。
12. **元ファイルを削除しない**（移動のみ）。**`runtime` を渡していない**ので変更しようがないことを
    API の形（引数に runtime が無い）で担保し、テストでは**呼び出し前後で `app.data` 相当の
    dict を渡していない**ことを確認する。
13. **保護対象・参照ありのファイルは隔離されない**（`presented_paths` に混ぜても再判定で落ちる）。
14. **隔離後に再走査しても、隔離物が孤児候補として現れない**（`quarantine/` は候補側と交差しない）。
15. `ConfigService.quarantine_orphans` の戻り値がモジュール関数の戻り値と一致する。

**単体テストの項目**（`tests/test_orphan_sweep_text.py` へ追記・`format_quarantine_result`）:

16. `moved` の件数と各行（kind ラベル + `original_path`）が出る。
17. `failed` が理由ラベル付きで出る。**未知の理由コードはコードのまま**出る。
18. `dropped_paths` / `newly_orphan_count` が**件数のみ**で出る（パスを出さない）。
19. `aborted_reason` があるとき、**先頭に中止の旨**と**「1 件も移動していない」旨**が出る。

**UI フローの項目**（`tests_ui/test_orphan_sweep_flow.py` へ追記）:

20. 候補 1 件以上のとき **`ReferenceCleanupDialog` が `header="隔離する孤児候補を確認してください。"` /
    `run_label="隔離する"` で開かれる**（**受け入れ条件 17 の 2 択**）。
21. **キャンセル（`result` が偽）で `quarantine_orphans` が呼ばれない**。
22. **「隔離する」で `quarantine_orphans` が呼ばれ**、`presented_paths` に
    **一覧へ出した `ORPHAN_CANDIDATE` の `stored_path` だけ**が渡る
    （`REFERENCED` / `PROTECTED` / `EXCLUDED` が混ざらない）。
    他の引数が**走査時と同一の値**であること。
23. **読めなかった参照側があっても「隔離する」で実行できる**（警告で抑止されない。§4-A / 受け入れ条件 17）。
24. **候補 0 件のときはダイアログを開かず通知のみ**（既存の振る舞いが変わっていない）。
25. **`dirty_tracker` / `app.data` が変化しない**。

**引数化の退行確認**:

26. `ReferenceCleanupDialog` を**既定値で開くと、ヘッダが「除去する参照元を確認してください。」・
    実行ボタンが「実行」**のままである（`tests_ui/test_reference_cleanup_flow.py` 9 件が**無変更で pass**）。

**退行の基準**: `tests` は **316 → 増加**、`tests_ui` は **262 → 増加**（どちらも減らさない・実測 2026-09-06）。
既存の `tests_ui/test_reference_cleanup_flow.py` 9 件 / `tests/test_reference_cleanup_text.py` 8 件は
**無変更で全 pass**。`tests_ui/test_orphan_sweep_flow.py` の既存 24 件は、**候補 1 件以上の経路が
`showinfo` からダイアログへ変わるため最小限の修正は可**（修正理由を報告に含めること）。
smoke pass。実行後に**worktree ルートへ `user/` も `quarantine/` も生成されていない**ことを確認する。

## 完了条件

- 上記「確認」がすべて pass（実測は **`verifier`** が行う。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（`.claude/rules/review.md` の 5 観点）。本タスクは破壊的 I/O のため、
  特に次を重点確認する:
  - **マニフェストが移動より先で、書けなければ 1 件も動かない**か（**MUST**）。
  - **〔提示済み〕∩〔再判定でも孤児〕への限定**が effective か（再判定が
    `quarantine_orphans` の内部で必ず走るか）。
  - **元ファイルを削除していない**か・**runtime / dirty を変更していない**か。
  - **隔離ルートが遅延作成**で、対象 0 件・中止時にディレクトリが残らないか。
  - **`ReferenceCleanupDialog` の変更が引数化だけ**に収まり、既定値で既存挙動が変わらないか。
  - 後続タスク（task_06 の復元 / 削除・「隔離の管理…」メニュー）の先取りが無いか。
- **実機目視は本タスクでは行わない**（**task_07 でまとめて実施**する）。ただし本タスクは
  **実ファイルを動かす**ため、task_07 の目視観点に「隔離の実行と `quarantine/` の中身の確認」を必ず含める。
