# task_06_quarantine_restore

## 目的

**隔離した実行単位を一覧し、選んだ単位を元の場所へ復元できるようにする**。
根拠は暫定仕様 10 **§3-7**（復元）+ **§3-9**（「隔離の管理…」メニュー・実行単位のリスト選択 UI）
+ **受け入れ条件 11 / 19**。

- **レイヤ制約**: **application（一覧・復元の実行）+ presentation（メニュー・リスト選択 UI・確認・結果表示）**。
  domain / infrastructure は不変。**スキーマ不変**。
- **削除は本タスクに含めない** = **task_06b**。**復元を先に green にしてから**不可逆な削除を載せる
  （復元が検証済みなら、削除で誤っても戻せる経路が担保されている状態で進められる）。
- 正本の規範: `data_schema.md` **§5.7**（stored 表記。canonical は比較専用）/ **§5.8.4**（判定名で分岐）。

### 復元の不変条件（**MUST**）

1. **`original_path` が候補側 4 ディレクトリ（§3-4）の配下でなければ復元を拒否する**（M5）。
   マニフェストの破損・手編集で**任意パスへ書き込ませない**。
2. **復元先に同名ファイルが既にあれば上書きせずスキップ**し、結果に出す。
3. **復元先ディレクトリが無ければ作成する**（MUST）。
4. **部分失敗を許容**（1 件ずつ・失敗は理由付きで記録して継続）。
5. **全件が戻った実行単位は、マニフェストと空ディレクトリを削除する**。
   **1 件でも残っていれば実行単位を残す**。
6. **マニフェストが読めない実行単位は復元対象にしない**（一覧には「マニフェスト不正」として出す）。

### 【確定済みの設計判断】復元は `state` を信用しない

**復元対象の判定は `quarantined_path` の実体の有無で行う**。`state` は**表示・統計にのみ**使う。

理由: task_05 の実装では、移動中のマニフェスト進捗書込みが失敗すると
**`state` が `planned` のまま実体は移動済み**になり得る（敵対的レビュー H-1・実測済み）。
**`state == "moved"` だけを復元する実装にしてはならない**（復元不能なファイルが生まれる）。

## 対象範囲

### 1. `keyseq/application/config_service/quarantine.py`（**共有ヘルパの公開のみ**）

task_06 が再利用するため、**private を公開名へ変える**（**振る舞いは変えない**）:

- `_quarantine_root` → **`quarantine_root(config_root: str) -> str`**（既存呼び出し 2 箇所を追随）。
- **実行単位 ID の形式を定数化**する（`_allocate_unit_id` が生成する形と**一致させる**こと）:

  ```python
  UNIT_ID_PATTERN = re.compile(r"^\d{8}_\d{6}(?:_\d+)?$")
  ```
  実測した生成規則: `created_at.strftime("%Y%m%d_%H%M%S")` + 衝突時に `_2` / `_3` …
  （**ゼロ埋めなし・上限なし**。`quarantine.py:142-151`）。
  `_allocate_unit_id` を**この定数に合わせて書き換えない**（生成側は現状のままでよい）。

**これ以外の変更をしない**（隔離の実行ロジックには触れない）。

### 2. 新規: `keyseq/application/config_service/quarantine_manage.py`

`quarantine.py` は既に約 340 行で目安を超えているため、**一覧・復元は別モジュール**へ置く
（`.claude/rules/file_organization_rules.md`）。兄弟 import は `from . import quarantine`。

**定数**

```python
RESTORE_SKIPPED_EXISTS = "already_exists"       # 復元先に同名がある
RESTORE_REJECTED_TARGET = "rejected_target"     # original_path が候補側 4 ディレクトリ配下でない
RESTORE_SOURCE_MISSING = "source_missing"       # 隔離側に実体が無い（既に戻っている等）
RESTORE_FAILED = "restore_failed"               # 実 I/O 失敗

RESTORE_ABORTED_INVALID_ID = "invalid_unit_id"  # 実行単位 ID の形式・実在が不正
RESTORE_ABORTED_NO_MANIFEST = "no_manifest"     # 有効な manifest.json が無い
```

**結果型**

```python
@dataclass(frozen=True)
class QuarantineUnit:
    unit_id: str
    created_at: str                 # マニフェストの値（読めなければ ""）
    entry_count: int                # マニフェストの entries 件数（読めなければ 0）
    remaining_count: int            # 隔離側に実体が残っている件数（= 復元できる件数）
    manifest_valid: bool            # False = 復元対象にしない（§3-7 最終項）


@dataclass(frozen=True)
class QuarantineRestoreResult:
    unit_id: str
    restored: tuple[tuple[str, str], ...]   # (kind, original_path〔stored 表記〕)
    skipped: tuple[tuple[str, str], ...]    # (original_path〔stored 表記〕, 理由コード)
    unit_removed: bool                      # 全件戻って実行単位を片付けたか
    aborted_reason: str                     # 中止した場合の理由コード（通常は ""）
```

**公開関数 1: 一覧**

```python
def list_quarantine_units(service, *, config_root: str) -> tuple[QuarantineUnit, ...]:
```

- **隔離ルートが無ければ空タプル**（**作らない**）。
- 隔離ルート**直下のディレクトリのみ**を見る。**`UNIT_ID_PATTERN` に一致しない名前は無視**する。
  **シンボリックリンク / ジャンクションは辿らない**（`quarantine.py` の realpath 境界判定と同じ規約で、
  実体が隔離ルート配下でないものは無視する）。
- `manifest.json` を読み、**トップレベルが `dict` かつ `entries` が `list`** なら `manifest_valid=True`。
  そうでなければ `manifest_valid=False`（`created_at=""` / `entry_count=0` / `remaining_count=0`）。
- `remaining_count` は **`quarantined_path` を解決して実体が在るものの件数**（**`state` を見ない**）。
- **`unit_id` の昇順**で返す（表示とテストの再現性）。

**公開関数 2: 復元**

```python
def restore_quarantine_unit(service, unit_id: str, *, config_root: str) -> QuarantineRestoreResult:
```

振る舞い（**この順で**）:

1. **`unit_id` の検証**（**パスを受け取らない**）。`UNIT_ID_PATTERN` に一致し、
   `<隔離ルート>/<unit_id>` が**隔離ルート直下に実在するディレクトリ**であること。
   満たさなければ `aborted_reason = RESTORE_ABORTED_INVALID_ID` で**何もしない**。
2. **マニフェストを読む**。無効なら `RESTORE_ABORTED_NO_MANIFEST` で**何もしない**（§3-7 最終項）。
3. 各エントリについて、次の順で判定する:
   1. **`quarantined_path` の実体が無ければ** `RESTORE_SOURCE_MISSING` でスキップ
      （**`state` を見ない**。既に戻したものを二重に扱わないため。**再実行しても冪等**になる）。
   2. **`original_path` の検証**（**MUST**）: `resolve_config_path` で解決し、
      **候補側 4 ディレクトリ（`user/keymaps` / `user/trigger_sets` / `user/sequences` /
      `user/hotkey_presets`）のいずれかの配下**であること。
      - 判定には **`service.is_path_within`** を使う。
      - **`is_path_within` は同一パスも配下と判定する**（`__init__.py:732-733` の docstring）。
        そのため**「候補側ディレクトリそのもの」を弾く**追加条件を入れること
        （`os.path.basename` が空でない / 解決後のパスが候補側ディレクトリと canonical 一致しない）。
      - 外れたら `RESTORE_REJECTED_TARGET` でスキップ。
   3. **復元先に同名が既にあれば** `RESTORE_SKIPPED_EXISTS` でスキップ（**上書きしない**）。
   4. **復元先ディレクトリを作成**（`os.makedirs(..., exist_ok=True)`）してから **`shutil.move`** で戻す。
   5. 失敗は `RESTORE_FAILED` で記録して**継続**する（例外を握り潰さず理由コードへ落とす）。
4. **後始末**: 実行単位配下に**実体が 1 つも残っていない**なら、`manifest.json` を削除し、
   実行単位ディレクトリ配下の空ディレクトリと実行単位ディレクトリ自体を削除して `unit_removed=True`。
   **1 件でも残っていれば実行単位を残す**（`unit_removed=False`）。
   後始末は **best-effort**（失敗しても復元結果を失敗にしない。`unit_removed=False` にするだけ）。
   隔離ルートが空になったら**隔離ルートも削除**してよい（task_05 の中止時と同じ扱い）。
5. **マニフェストを書き換えない**（復元は冪等。再実行すれば戻し済みは 3-1 でスキップされる）。

### 3. 変更: `keyseq/application/config_service/__init__.py`（2 箇所のみ）

import 行へ `quarantine_manage` を追加し、**1 行委譲のファサード 2 つ**
（`list_quarantine_units` / `restore_quarantine_unit`）を追加する。

### 4. 新規: `keyseq/presentation/quarantine_manage_text.py`（表示文言の純関数）

`orphan_sweep_text.py` と**同じ書き方**（tkinter を import しない / 戻り値は `tuple[str, ...]` /
**判定名・理由コードの定数で分岐**）。**`orphan_sweep_text.py` は変更しない**（責務が違う）。

```python
def format_unit_list(units) -> tuple[str, ...]:          # リスト UI の各行（1 単位 1 行）
def format_restore_plan(unit) -> tuple[str, ...]:        # 確認ダイアログの本文
def format_restore_result(result) -> tuple[str, ...]:    # 実行結果の通知
```

- `format_unit_list` の 1 行は
  `f"{unit_id}  作成: {created_at}  残り {remaining}/{entry_count} 件"`。
  **`manifest_valid` が偽なら「マニフェスト不正（復元できません）」**と明示する（§3-7 最終項）。
- `format_restore_result` は復元件数 + スキップの理由別内訳（**理由ラベルは日本語・
  未知コードはコードのまま**）+ **実行単位を片付けたかどうか**を出す。
  `aborted_reason` があるときは**先頭に中止の旨**と**「1 件も戻していません」**を明記する。

### 5. 新規: `keyseq/presentation/dialogs/quarantine_manage_dialog.py`

**実行単位のリスト選択 UI**（§3-9 のリスト選択 UI ①）。
`dialogs/layout_delete_dialog.py` / `orphan_sweep_dialog.py` と**同じ書き方**
（`tk.Toplevel` / `TYPE_CHECKING` ガード / `suspend_hook_for_dialog` ・ `resume_hook_after_dialog` /
`transient` + `grab_set` / `<Escape>` と `WM_DELETE_WINDOW`）。

```python
class QuarantineManageDialog(tk.Toplevel):
    def __init__(self, parent: App, *, lines: tuple[str, ...], unit_ids: tuple[str, ...]): ...
```

- `tk.Listbox` に `lines` を表示する。**表示行と `unit_ids` は同じ並び**で受け取る
  （ダイアログは文言を組み立てない）。
- 公開属性: **`self.selected_unit_id: str`**（未選択なら `""`）/ **`self.action: str`**
  （`""` / `"restore"`）。
- ボタン: **「復元する…」**「閉じる」。**選択が無ければ何もしない**。
- **削除ボタンは本タスクでは置かない**（task_06b で追加する）。
- **`config.json` やファイルに触れない**（実行は IO の責務）。

### 6. 変更: `keyseq/presentation/dialogs/__init__.py`（1 行のみ）

`from .quarantine_manage_dialog import QuarantineManageDialog` を追加する。

### 7. 新規: `keyseq/presentation/controllers/config_io/quarantine_manage_io.py`

`orphan_sweep_io.py` と**同型**。

```python
class QuarantineManageIo:
    def __init__(self, app) -> None: ...
    def manage_quarantine(self) -> None: ...
```

1. `list_quarantine_units(config_root=self._app.config_root)` を呼ぶ。
   **`config_root` に空文字を渡さない**。
2. **0 件なら**ダイアログを出さず `messagebox.showinfo` で「隔離された実行単位はありません。」と通知する。
3. `QuarantineManageDialog` を開く（`lines=format_unit_list(units)` / `unit_ids=` 同順）。
4. `action == "restore"` かつ `selected_unit_id` があるとき:
   - **`manifest_valid` が偽の単位が選ばれたら**、実行せず `showinfo` で
     「マニフェストが読めないため復元できません」と伝える（§3-7 最終項）。
   - **`ReferenceCleanupDialog`**（**task_05 で引数化済み。再改修しない**）を
     `header="復元する内容を確認してください。"` / `run_label="復元する"` /
     `lines=format_restore_plan(unit)` で開く。
   - `result` が偽なら**何もしない**。
   - 真なら `restore_quarantine_unit(...)` を呼び、`format_restore_result` を `showinfo` で出す。
5. **`dirty_tracker` / `app.data` を触らない**。**復元後に runtime を再読込しない**
   （棚卸しと同じく、ファイル操作と runtime を混ぜない）。

### 8. 変更: `keyseq/presentation/app.py`（2 箇所）/ `views/menu_bar.py`（1 箇所）

- `app.py`: import 1 行 + `self.quarantine_manage_io = QuarantineManageIo(self)` 1 行。
- `menu_bar.py`: 設定メニューの**「孤児ファイルの棚卸し…」の直後**へ
  `settings_menu.add_command(label="隔離の管理…", command=app.quarantine_manage_io.manage_quarantine)`。

### 9. テスト

- 新規 `tests/test_quarantine_manage.py`（application・**実ファイルで検証**）
- 新規 `tests/test_quarantine_manage_text.py`（純関数）
- 新規 `tests_ui/test_quarantine_manage_flow.py`（UI フロー・**`patch.object` 優先**・
  メニューは**ラベルで探す**）

### 設計メモ / 制約

- **`quarantine.py` の隔離ロジックを変更しない**（公開名への変更のみ）。
- **`orphan_sweep_text.py` / `orphan_sweep_io.py` / `orphan_sweep_dialog.py` /
  `reference_cleanup_*` を変更しない**。
- **`ReferenceCleanupDialog` を再改修しない**（task_05 で引数化済み）。
- **`canonical_path` の値を表示・マニフェスト・結果へ混入させない**。
- **クロスデバイス移動時に `failed` でも隔離側にファイルが残り得る**（task_05 の申し送り）。
  復元は**実体の有無**で判定し、**復元先に同名があればスキップ**するので、
  この組み合わせで**多重復元にならない**こと。
- 例外を握り潰さない（理由コードへ落とすのは可。`except: pass` は不可）。
- 関数はおおむね 30 行以内・新規ファイルは 300 行以内を目安に分割する。

## 含まない

- **削除（実行単位 ID + 4 検証・再帰削除・不可逆の明記・削除前の全件提示）** = **task_06b**。
  ダイアログの削除ボタンもそこで追加する。
- **マニフェスト不正な実行単位の掃除手段** = 本タスクでは提供しない
  （一覧に「マニフェスト不正」と出すのみ。扱いは task_06b / task_08 で判断）。
- **復元後の runtime 再読込・dirty 更新** = 行わない。
- **孤児候補の行ごとの選択 UI / 復元の行ごとの選択** = スコープ外（§3-9）。
- **H-1 の実装修正**（task_05 側）= 行わない。本タスクは**実体の有無で判定する**ことで吸収する。
- 正本 `spec_detail/` の改訂 = **task_08**。統合確認・実機目視 = **task_07**。

## 確認

`.venv` の python で実行する（worktree ルートから）。

```
..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui
..\..\..\.venv\Scripts\python.exe -m tests.smoke_app
```

**単体テストの項目**（`tests/test_quarantine_manage.py`・実ファイルで検証）:

1. **一覧**: 隔離ルートが無いとき空タプルを返し、**隔離ルートを作らない**。
2. **一覧**: 実行単位が `unit_id` 昇順で返り、`created_at` / `entry_count` / `remaining_count` が正しい。
   **`UNIT_ID_PATTERN` に一致しない名前のディレクトリ**（`foo` / `2026-09-06` 等）は**無視**される。
3. **一覧**: マニフェストが無い / 壊れている / `entries` が list でない単位は
   **`manifest_valid=False`** で返る（一覧からは消えない）。
4. **一覧**: `remaining_count` が **`state` ではなく実体の有無**で数えられる
   （**全件 `state="planned"` でも実体があれば残りとして数える**。H-1 の確定判断）。
5. **復元**: マニフェストどおりに元の場所へ戻り、**隔離側から消える**（受け入れ条件 11）。
6. **復元**: **全件 `state="planned"` のまま実体が移動済み**の単位でも**復元できる**
   （**H-1 の確定判断の担保。最重要**）。
7. **復元**: **復元先に同名ファイルがあると上書きせずスキップ**し、
   `RESTORE_SKIPPED_EXISTS` として報告される。**既存ファイルの内容が変わらない**ことを実体で確認する。
8. **復元**: **`original_path` が候補側 4 ディレクトリの配下でなければ拒否**され、
   `RESTORE_REJECTED_TARGET` になる（`../../outside.json` / config 外の絶対パス /
   `user/hotkey_presets/global/x.json` をマニフェストに手で書いて確認）。**そのファイルは動かない**。
9. **復元**: **`original_path` が候補側ディレクトリ「そのもの」**（`user/keymaps`）でも拒否される
   （`is_path_within` が同一パスを配下と判定する穴を塞げているか）。
10. **復元**: **復元先ディレクトリが無ければ作成**して戻す。
11. **復元**: 1 件が失敗しても**残りは継続**し、失敗が理由コード付きで報告される。
12. **復元**: **全件戻ると `manifest.json` と実行単位ディレクトリが消え** `unit_removed=True`。
    **1 件でも残ると実行単位が残り** `unit_removed=False`。
13. **復元**: **同じ単位を 2 回復元しても壊れない**（2 回目は全件 `RESTORE_SOURCE_MISSING`。冪等）。
14. **復元**: **`unit_id` に不正値**（空 / `..` / `../../etc` / パス区切り入り / 形式違い /
    実在しない）を渡すと `RESTORE_ABORTED_INVALID_ID` で**何もしない**
    （**隔離ルート自身や config 配下に一切触れない**ことを確認する）。
15. **復元**: **マニフェストが読めない単位**は `RESTORE_ABORTED_NO_MANIFEST` で**何もしない**。
16. `ConfigService.list_quarantine_units` / `restore_quarantine_unit` の戻り値が
    モジュール関数の戻り値と一致する（**引数を既定値以外にして転送漏れを検出できる形**にする）。

**単体テストの項目**（`tests/test_quarantine_manage_text.py`）:

17. `format_unit_list` が 1 単位 1 行で、残り件数と作成日時を含む。
    **`manifest_valid=False` の単位は「復元できません」と明示**される。
18. `format_restore_result` が復元件数とスキップの**理由別内訳**を出す。
    **未知の理由コードはコードのまま**出る。
19. `aborted_reason` があるとき、**先頭に中止の旨**と**「1 件も戻していません」**が出る。
20. 戻り値がすべて `tuple[str, ...]` で、**canonical 表記を含まない**。

**UI フローの項目**（`tests_ui/test_quarantine_manage_flow.py`）:

21. **実行単位が 0 件のときはダイアログを開かず通知のみ**。
22. **設定メニューの「隔離の管理…」から `manage_quarantine` が呼ばれる**（**ラベルで探す**）。
23. **「閉じる」/ 未選択では `restore_quarantine_unit` が呼ばれない**。
24. **「復元する…」→ 確認ダイアログが `header` / `run_label="復元する"` で開き**、
    **キャンセルで復元が呼ばれない**・**実行で呼ばれる**。
25. **`manifest_valid=False` の単位を選ぶと、確認ダイアログを開かず通知で終わる**
    （復元 API を呼ばない）。
26. **`dirty_tracker` / `app.data` が変化しない**。
27. **UI テストが実ファイルを動かさない**（`restore_quarantine_unit` を patch する）。

**退行の基準**: `tests` は **354 → 増加**、`tests_ui` は **268 → 増加**（どちらも減らさない・実測 2026-09-06）。
既存の `tests_ui/test_reference_cleanup_flow.py` 9 件 / `tests/test_reference_cleanup_text.py` 8 件 /
`tests_ui/test_orphan_sweep_flow.py` 30 件 / `tests/test_quarantine.py` 24 件は**無変更で全 pass**
（`quarantine.py` の公開名変更に伴う**参照の追随のみ可**。その場合は理由を報告に含める）。
smoke pass。実行後に**worktree ルートへ `user/` も `quarantine/` も生成されていない**ことを確認する。

## 完了条件

- 上記「確認」がすべて pass（実測は **`verifier`**。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（5 観点）。特に:
  - **`original_path` のガード**が effective か（**同一パスの穴**を塞げているか）。
  - **復元が `state` を見ず実体の有無で判定**しているか（H-1 の確定判断）。
  - **同名スキップで既存ファイルを上書きしない**か。
  - **全件復元時の後始末**が正しく、**1 件でも残れば単位を残す**か。
  - **`unit_id` に不正値を渡しても何も触らない**か。
  - `quarantine.py` の変更が**公開名への変更だけ**に収まっているか。
  - **task_06b（削除）の先取りが無い**か（削除ボタン・削除 API を作っていないか）。
- **実機目視は行わない**（**task_07 でまとめて実施**）。ただし task_07 の目視観点に
  **「隔離 → 復元の往復で元に戻ること」**を必ず含める。
