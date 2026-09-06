# task_03_orphan_sweep_entry

## 目的

**孤児ファイルの棚卸し（検出）の入口と結果表示**を作り、**「検出のみ」が green になる状態**まで到達させる。
task_02 の `scan_orphans` を設定メニューから呼び、結果を表示文言の純関数で整形して提示する。
根拠は暫定仕様 10 **§3-4 の未保存確認**（「保存する / 中止する」の 2 択）/ **§3-5**（走査の不完全性の提示）/
**§3-9**（UI・0 件は通知のみ・表示文言は純関数）/ **§3-11**（依存方向）+ **受け入れ条件 6 / 8 / 13 / 17 の警告部**。

- **レイヤ制約**: **presentation が主**。application は**保護対象パスの収集関数 1 つの追加**のみ
  （runtime の内部キーを読むため application が持つ。§3-11。domain / infrastructure は不変）。**スキーマ不変**。
- **破壊的 I/O なし**: 隔離・復元・削除は作らない。棚卸しそのものによる書き込みは 0 件
  （受け入れ条件 15。**未保存確認で保存した場合は対象外**）。
- 正本の規範: `data_schema.md` **§5.7**（表示は stored 表記。canonical を出さない）/
  **§5.8.4**（**分岐は判定名で行い表示文言で分岐しない**）。

## 対象範囲

### 追加: `keyseq/application/config_service/orphan_scan.py`（既存モジュールへ関数 1 つ）

保護対象は runtime の**内部キー**（`INTERNAL_KEYMAP_SOURCE_PATH` 等）を読む必要があるため、
**presentation に同等のロジックを書かず application 側に収集関数を置く**（§3-11 の
「保護対象パスの集合を引数で受け取る」は `scan_orphans` の API 制約であり、本関数は別関数として並置する）。

```python
def collect_protected_paths(service, runtime, *, keymap_set_path: str) -> tuple[str, ...]:
```

- 集めるのは §3-4 の 4 種。**stored 表記のまま**返す（canonical へ寄せない・実在確認しない）:
  1. `keymap_set_path`
  2. `runtime["keymaps"][].` **`service.INTERNAL_KEYMAP_SOURCE_PATH`**（要素が dict のときのみ）
  3. `runtime.` **`service.INTERNAL_TRIGGER_SET_SOURCE_PATH`**
  4. `runtime["triggers"][].` **`service.INTERNAL_SEQUENCE_SOURCE_PATH`**（要素が dict のときのみ）
  5. `runtime["hotkey_presets_path"]`（**source_path ではなく通常キー**。条件付きで載る・
     `split_loading.py:290`）
- `runtime` が dict でない場合も例外にせず、`keymap_set_path` だけを返す。
- 各値は `str(x or "").strip()` し、空は除く。**重複は入力順を保って除去**する。
- 既存の `parent_refs_cleanup._iter_child_paths`（`parent_refs_cleanup.py:134-159`）と**同じキーの読み方**に
  揃える（あちらは private なので**呼ばず**、同じ規約で書く）。

### 変更: `keyseq/application/config_service/__init__.py`（1 箇所のみ）

`scan_orphans` の直後（`:396` 付近）へ**1 行委譲のファサード**を追加する（import 行は task_02 で追加済み）:

```python
def collect_protected_paths(self, runtime: Any, *, keymap_set_path: str) -> Any:
    return orphan_scan.collect_protected_paths(self, runtime, keymap_set_path=keymap_set_path)
```

### 新規: `keyseq/presentation/orphan_sweep_text.py`（表示文言の純関数）

`presentation/reference_cleanup_text.py` と**同じ書き方**にする（application の**判定名定数を import** して
判定名で分岐する / tkinter を import しない / 戻り値は `tuple[str, ...]`）。

**定数**

```python
ORPHAN_SWEEP_EMPTY_MESSAGE: str = "隔離できる孤児ファイルはありません。"

_KIND_LABELS = {
    KIND_KEYMAP: "キーマップ",
    KIND_TRIGGER_SET: "トリガー一覧",
    KIND_SEQUENCE: "出力シーケンス",
    KIND_HOTKEY_PRESETS: "個別プリセット",
}

_SOURCE_REASON_LABELS = {
    SOURCE_MISSING: "ファイルが見つかりません",
    SOURCE_UNREADABLE: "読み取り / JSON 解析に失敗しました",
}

SCAN_SCOPE_NOTE: str = (
    "注意: 走査範囲外に保存された構成セットから参照されている可能性があります。"
)
```

**公開関数 1: 警告ブロック（受け入れ条件 17 / §3-5）**

```python
def format_scan_warnings(result) -> tuple[str, ...]:
```

`result` は `OrphanScanResult`。次の順に行を作る（該当が無い項目は行を出さない）。

1. **読めなかった参照側**（`unreadable_sources`）が 1 件以上のとき（**MUST・必ず先頭**）:
   - `f"警告: 読めなかった構成セット / トリガー一覧が {N} 件あります。"`
   - `"それらが参照していた子ファイルを孤児と誤判定している可能性があります。"`
   - 各件を `f"  {path}: {理由ラベル}"`（未知の理由コードは**コード文字列をそのまま**出す）
2. **見つからなかった走査ディレクトリ**（`missing_scan_dirs`）が 1 件以上のとき（§3-5-1）:
   - `f"見つからなかった走査ディレクトリ: {N} 件"` + 各パスを `f"  {path}"`
   - **危険信号として書かない**（§4-A 確定。「警告」の語を使わない）
3. **対象外と判定した JSON の件数**（`non_keymap_set_sources`）が 1 件以上のとき（§3-5-3）:
   - `f"構成セットとして解釈できなかった JSON: {N} 件"`（**件数のみ**・パスは出さない）
4. **`SCAN_SCOPE_NOTE`**（§3-5-4。**常に出す**）

**公開関数 2: 一覧（候補が 1 件以上のとき）**

```python
def format_orphan_plan(result) -> tuple[str, ...]:
```

- 先頭に **`format_scan_warnings(result)` の行**を置く（**MUST**。受け入れ条件 17）。
- 続いて `f"孤児候補: {N} 件"`、その後に **`state == ORPHAN_CANDIDATE` の行だけ**を
  `f"{kind ラベル}: {stored_path}"` で列挙する。
- さらに `ORPHAN_EXCLUDED` が 1 件以上あれば `f"形状検証で対象外: {N} 件"`（**件数のみ**）。
  `ORPHAN_REFERENCED` / `ORPHAN_PROTECTED` は**出さない**（隔離対象でないため）。
- **判定名の定数で分岐する**（表示ラベルで分岐しない。正本 §5.8.4）。

**公開関数 3: 0 件時の通知（§3-9 / 受け入れ条件 13）**

```python
def format_orphan_notice(result) -> tuple[str, ...]:
```

- `ORPHAN_SWEEP_EMPTY_MESSAGE` + **`format_scan_warnings(result)` の行**（§3-5 の項目は 0 件でも伝える）。

### 新規: `keyseq/presentation/controllers/config_io/orphan_sweep_io.py`

`config_io/reference_cleanup_io.py` と**同型**（`__init__(self, app)` / `messagebox` を直接使う /
`_app` 経由で `config_service` を呼ぶ。**`config_service` の内部モジュールを直参照しない**）。

```python
class OrphanSweepIo:
    def __init__(self, app) -> None: ...
    def run_sweep(self) -> None: ...
```

`run_sweep()` の手順:

1. **未保存確認**（§3-4 / H5 / 受け入れ条件 6）。
   `self._app.dirty_tracker.has_unsaved_changes()` が真のとき **`messagebox.askyesno`** で
   「棚卸しの前に保存が必要です。保存しますか？」を出し、**いいえなら `return`（棚卸しごと中止）**。
   - **`KeymapSetIo.confirm_save_if_dirty` を使ってはならない**（`keymap_set_io.py:32-47`。
     「いいえ = 保存しない」で **True（続行）**を返し、**本フェーズと意味が逆**）。
   - はいのとき: `keymap_set_path` があれば `keymap_set_io.save_keymap_set(show_success_dialog=False)`、
     無ければ `keymap_set_io.save_as(show_success_dialog=False)`。**戻り値が偽なら `return`**（保存失敗で中止）。
2. **保護対象の収集**: `self._app.config_service.collect_protected_paths(
   self._app.data, keymap_set_path=self._app.keymap_set_path)`。
3. **走査**: `self._app.config_service.scan_orphans(...)` を次の引数で呼ぶ。
   - `config_root=self._app.config_root` — **空文字を渡さない**（`resolve_config_path` は空だと
     **cwd 基準**になる。task_01 / task_02 からの申し送り）。
   - `scan_dirs=[]` — **本タスクでは固定で空リスト**（設定の永続化は task_04）。
   - `startup_keymap_set_path=str(self._app._startup_settings.get("keymap_set_path") or "").strip()`
     （`startup_io.py:18` と同じ読み方）。
   - `current_keymap_set_path=self._app.keymap_set_path`。
   - `protected_paths=` 2 の戻り値。
4. **候補 0 件**（`state == ORPHAN_CANDIDATE` が 1 件も無い）→ **ダイアログを出さず**
   `messagebox.showinfo("孤児ファイルの棚卸し", "\n".join(format_orphan_notice(result)))` で終了（§3-9）。
5. **候補 1 件以上** → `messagebox.showinfo("孤児ファイルの棚卸し", "\n".join(format_orphan_plan(result)))`。
   **本タスクでは提示のみで、実行の選択肢を出さない**（隔離は task_05）。

### 変更: `keyseq/presentation/app.py`（2 箇所のみ）

- `from keyseq.presentation.controllers.config_io.orphan_sweep_io import OrphanSweepIo`
  （既存 `reference_cleanup_io` の import〔`:20`〕の並びへ）。
- `self.orphan_sweep_io = OrphanSweepIo(self)`（既存 `self.reference_cleanup_io = ...`〔`:157`〕の直後）。

### 変更: `keyseq/presentation/views/menu_bar.py`（1 箇所のみ）

設定メニューの **「参照元を掃除…」（`:25`）の直後**へ 1 行追加する:

```python
settings_menu.add_command(label="孤児ファイルの棚卸し…", command=app.orphan_sweep_io.run_sweep)
```

**「隔離の管理…」は追加しない**（task_06）。

### 新規: `tests/test_orphan_sweep_text.py` / 追記: `tests/test_orphan_scan.py` / 新規: `tests_ui/test_orphan_sweep_flow.py`

- `tests/test_orphan_sweep_text.py` — `tests/test_reference_cleanup_text.py` と同型（純関数のみ・UI 不要）。
- `tests/test_orphan_scan.py` へ **`collect_protected_paths` のテストを追記**する（新規ファイルを作らない）。
- `tests_ui/test_orphan_sweep_flow.py` — `tests_ui/test_reference_cleanup_flow.py` と同型。
  **`patch.object` を優先**する（モジュール名前空間の patch を新規に増やさない）。
  メニュー項目は**インデックスで固定せずラベルで探す**（tearoff でずれる）。

### 設計メモ / 制約

- **表示は暫定的に `messagebox.showinfo`**。§3-9 の確認ダイアログ（`ReferenceCleanupDialog` の
  ヘッダ / ボタンラベル引数化版）は**実行の選択肢が生まれる task_05 / task_06 で導入**する。
  本タスクの純関数（行タプルを返す）はそのまま `lines=` へ渡せる形にしておくこと。
- **`reference_cleanup_text.py` / `reference_cleanup_dialog.py` / `reference_cleanup_io.py` を変更しない**。
  既存文言「孤児かどうかはこの検査範囲では判定できない」の見直しは **task_08**（`tests/test_reference_cleanup_text.py`
  8 件の追随が要るため。暫定仕様 §7 / L11）。
- **application の判定名・理由コードの定数を presentation から import してよい**
  （`parent_refs_cleanup` の定数を `reference_cleanup_text.py` が import している既存パターンと同じ。
  禁止されているのは presentation から `config_service` の**内部モジュールを使った処理の直呼び**）。
- **`app` から `config_service.orphan_scan` を直接呼ばない**。必ず `ConfigService` のファサード経由。
- 例外を握り潰さない。関数はおおむね 30 行以内・新規ファイルは 300 行以内を目安に分割する。
- `canonical_path` の値を表示へ出さない（`stored_path` / 入力表記をそのまま使う）。

## 含まない

- **走査ディレクトリ設定の `config.json` 永続化・`_startup_settings` 更新・リスト UI** = **task_04**
  （本タスクは `scan_dirs=[]` 固定）。
- **隔離の実行・確認ダイアログ・「実行 / キャンセル」の 2 択・`ReferenceCleanupDialog` の引数化** =
  **task_05 / task_06**（受け入れ条件 17 のうち**警告文の生成と先頭配置だけ**が本タスク）。
- **「隔離の管理…」メニュー・復元・削除・実行単位のリスト選択 UI** = **task_06**。
- **`reference_cleanup_text.py` の既存文言の見直し** = **task_08**。
- **統合確認・実機目視の観点リスト** = **task_07**。
- 正本 `spec_detail/` の改訂 = **task_08**（フェーズ中は正本を直接改訂しない）。
- 孤児候補の**行ごとの選択 UI**（暫定仕様 §3-9 で明示的に作らないと決めている）。

## 確認

`.venv` の python で実行する（`.claude/rules/python_rules.md`。worktree ルートから）。

```
..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui
..\..\..\.venv\Scripts\python.exe -m tests.smoke_app
```

**単体テストの項目**（`tests/test_orphan_sweep_text.py`。`OrphanScanResult` を直接組み立てて検証する）:

1. `unreadable_sources` が 1 件以上のとき、**戻り値の先頭行が警告行**で、件数・各パス・
   日本語の理由ラベルが含まれる（`format_scan_warnings` / `format_orphan_plan` の**両方**で確認。
   受け入れ条件 17）。
2. **未知の理由コード**を渡すと、そのコード文字列がそのまま出る（握り潰さない）。
3. `missing_scan_dirs` が件数 + パスで出る。**「警告」の語を含まない**（§4-A・危険信号にしない）。
4. `non_keymap_set_sources` は**件数のみ**が出て、**パスは出ない**（受け入れ条件 8）。
5. `SCAN_SCOPE_NOTE` が**常に**含まれる（該当項目が 1 つも無いときも。§3-5-4）。
6. `format_orphan_plan` は **`ORPHAN_CANDIDATE` の行だけ**を列挙し、
   `ORPHAN_REFERENCED` / `ORPHAN_PROTECTED` の `stored_path` を**出さない**。
7. `ORPHAN_EXCLUDED` が**件数のみ**で出る（パスを出さない）。
8. `format_orphan_notice` は `ORPHAN_SWEEP_EMPTY_MESSAGE` + 警告ブロックを返す
   （候補 0 件でも §3-5 の項目が伝わる。受け入れ条件 13）。
9. 4 種の kind ラベルが日本語へ変換される。**未知の kind はそのまま**出る。
10. 戻り値がすべて `tuple[str, ...]` で、**canonical 表記（normcase 済みの絶対パス）を含まない**。

**単体テストの項目**（`tests/test_orphan_scan.py` へ追記・`collect_protected_paths`）:

11. `keymap_set_path` + keymaps の `_keymap_source_path` + `trigger_set` + triggers の
    `_sequence_source_path` + `hotkey_presets_path` の **5 種すべて**が集まる。
12. **stored 表記のまま**返る（canonical へ寄せない）。**重複が入力順を保って除去**される。
13. `runtime` が dict でない / 空 / 内部キーが無い場合も例外にならず、
    `keymap_set_path` だけ（または空）を返す。
14. `ConfigService.collect_protected_paths` の戻り値がモジュール関数の戻り値と一致する。

**UI フローの項目**（`tests_ui/test_orphan_sweep_flow.py`）:

15. **未保存で「いいえ」→ 保存も走査も呼ばれず中止**する（受け入れ条件 6。
    `scan_orphans` が**呼ばれない**ことを assert）。
16. **未保存で「はい」→ 保存に成功したら走査へ進む**。**保存に失敗したら走査へ進まない**。
17. **未保存の変更が無いときは保存確認を出さずに走査へ進む**。
18. **候補 0 件のとき `showinfo` のみで、ダイアログを開かない**（§3-9 / 受け入れ条件 13）。
19. **候補 1 件以上のとき、提示された本文の先頭に警告行が来る**（`unreadable_sources` あり）。
20. `scan_orphans` へ渡る引数が正しい: **`config_root` が空文字でない** /
    `current_keymap_set_path` が `app.keymap_set_path` / `startup_keymap_set_path` が
    `_startup_settings["keymap_set_path"]` / `scan_dirs == []` / `protected_paths` が
    `collect_protected_paths` の戻り値。
21. **設定メニューの「孤児ファイルの棚卸し…」から `run_sweep` が呼ばれる**
    （**ラベルで探す**。インデックス固定にしない）。
22. **棚卸しの実行でファイルが書き込まれない**（未保存確認で保存した場合を除く。受け入れ条件 15）。

**退行の基準**: `tests` は **295 → 増加**（減らさない・実測 2026-09-06）、
`tests_ui` は **238 → 増加**（既存 238 件を 1 件も落とさない。特に
`tests_ui/test_reference_cleanup_flow.py` 9 件と `tests/test_reference_cleanup_text.py` 8 件は**無変更で pass**）、
smoke pass。実行後に**worktree ルートへ `user/` が生成されていない**ことも確認する。

## 完了条件

- 上記「確認」がすべて pass（実測は **`verifier`** が行う。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（`.claude/rules/review.md` の 5 観点。特に
  **仕様適合性**〔未保存時が「保存する / 中止する」の 2 択になっているか・警告が一覧の先頭か〕・
  **依存方向**〔presentation が `config_service` の内部モジュールを直参照していないか〕・
  **責務分離**〔表示文言が純関数側にあり IO が組み立てていないか〕・
  **不要変更の有無**〔`reference_cleanup_*` 3 ファイルを触っていないか〕）。
- **実機目視は本タスクでは行わない**（**task_07 でまとめて実施**する）。
  ただし本タスク完了をもって**「検出のみ」が green** の状態になる（暫定仕様 §4-F の段取り）。
