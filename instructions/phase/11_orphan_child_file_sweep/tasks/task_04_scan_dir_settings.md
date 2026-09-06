# task_04_scan_dir_settings

## 目的

**ユーザー指定の走査ディレクトリを `config.json` へ永続化**し、**棚卸しダイアログ内で追加 / 削除**できるようにする。
task_03 で `scan_dirs=[]` 固定にした箇所を、設定値の読み出しへ差し替える。
根拠は暫定仕様 10 **§2**（指定ディレクトリは設定として記録し再指定を不要にする）/ **§3-10**（永続化の規約）/
**§3-5-1**（見つからないディレクトリはスキップして報告・**設定からは自動で消さない**）/ **§3-9 のリスト選択 UI ②**
+ **受け入れ条件 7 / 14**。

- **レイヤ制約**: **presentation が主**。application は**走査ディレクトリ設定の正規化関数 1 つの追加**のみ
  （パス表記の規範に関わるため application が持つ。§5.7）。domain / infrastructure は不変。
- **スキーマ変更あり**: `config.json` に **キー追加のみ**。**既存キーの削除・意味変更をしない**（正本 §5.4 / 後方互換）。
- **`config.json` を直接書かない**（**MUST**・H6）。書き込みは**起動設定の書き出し経路 1 本**
  （`StartupIo.write_startup`）を通す。正本 §5.10.1 のとおり `config.json` は keymap_set 保存時に
  **丸ごと書き直され**、未知キーの保全は**起動時スナップショット `_startup_settings`** に依存する
  （`split_payloads.build_startup_payload:347-357` が `startup_data` を丸ごと複製する /
  `keymap_set_io.py:126,133` が `_startup_settings` を渡して差し替える）。
  **直接書くと次の keymap_set 保存で無言で失われる**。

## 対象範囲

### 追加: `keyseq/application/config_service/orphan_scan.py`（既存モジュールへ関数 1 つ）

```python
def normalize_scan_dirs(service, values, *, config_root: str) -> tuple[str, ...]:
```

**読み出し・保存の両方でこの 1 関数を通す**（表記と重複排除の規約を 1 箇所に閉じる）。

1. `values` が `list` / `tuple` でなければ**空タプル**を返す（壊れた設定で落とさない）。
2. 各要素について **`isinstance(value, str)` でないものは捨てる**（§3-10。プリセット読み出しの
   正規化と同じ規律）。`strip()` して空なら捨てる。
3. **`service.resolve_config_path(value, config_root)` で解決 → `service.canonical_path(...)`** を
   キーに**重複を排除**する（**入力順を保つ**）。
4. 返す値は **`service.to_config_relative_or_absolute(resolved, config_root)`**
   （§5.7 = config 配下は相対 / 外は絶対 / 区切りは `/`）。**canonical 値を返さない**。
5. **実在確認をしない**（不在でも設定からは消さない。§3-5-1）。

### 変更: `keyseq/application/config_service/__init__.py`（1 箇所のみ）

`collect_protected_paths` の直後へ **1 行委譲のファサード**を追加する（import 行は追加済み）:

```python
def normalize_scan_dirs(self, values: Any, *, config_root: str) -> Any:
    return orphan_scan.normalize_scan_dirs(self, values, config_root=config_root)
```

### 新規: `keyseq/presentation/dialogs/orphan_sweep_dialog.py`

**棚卸しの入口ダイアログ**（§3-9 のリスト選択 UI ②）。`dialogs/layout_delete_dialog.py` と**同じ書き方**にする
（`tk.Toplevel` を継承 / `from __future__ import annotations` / `App` の型 import は `TYPE_CHECKING` ガード内 /
`__init__` 冒頭で `parent.hook.suspend_hook_for_dialog()`・`destroy` で `resume_hook_after_dialog()` /
`transient` + `grab_set` / `<Escape>` と `WM_DELETE_WINDOW` を閉じるへ）。

```python
class OrphanSweepDialog(tk.Toplevel):
    def __init__(self, parent: App, *, scan_dirs: tuple[str, ...], initial_dir: str): ...
```

- 公開属性: **`self.result: bool`**（「棚卸しを実行」で `True`・既定 `False`）/
  **`self.scan_dirs: tuple[str, ...]`**（閉じた時点の一覧。**編集の有無に関わらず現在値を持つ**）。
- 構成: 説明ラベル → **`tk.Listbox`**（`LayoutDeleteDialog` と同型・スクロールバー付き）→
  ボタン「**追加…**」「**削除**」→ ボタン「**棚卸しを実行**」「**閉じる**」。
- 「追加…」= **`filedialog.askdirectory(parent=self, initialdir=initial_dir)`**。
  空文字（キャンセル）なら何もしない。**同じディレクトリの重複追加は防ぐ**
  （比較は表示中の文字列の一致で足りる。正規化は IO 側が `normalize_scan_dirs` で行う）。
- 「削除」= 選択が無ければ何もしない。**確認ダイアログを出さない**（設定 1 行の削除で、
  再追加が容易なため）。
- **設定の保存はダイアログの責務にしない**（`config.json` を触らない。保存は IO 側）。
- **走査ディレクトリの一覧が空でも「棚卸しを実行」は押せる**（既定ディレクトリ等は常に走査されるため）。

### 変更: `keyseq/presentation/dialogs/__init__.py`（1 行のみ）

`from .orphan_sweep_dialog import OrphanSweepDialog` を末尾へ追加する
（**明示列挙の再輸出のみ**という既存方針を崩さない）。

### 変更: `keyseq/presentation/controllers/config_io/orphan_sweep_io.py`

`run_sweep()` を次の順に変える（**未保存確認は現状どおり最初のまま**。§3-4「棚卸しの前」）:

1. `self._save_before_sweep()`（**無変更**）。
2. **設定の読み出し**: `scan_dirs = self._app.config_service.normalize_scan_dirs(
   self._app._startup_settings.get(SCAN_DIRS_KEY), config_root=self._app.config_root)`。
3. **入口ダイアログ**: `OrphanSweepDialog(self._app, scan_dirs=scan_dirs, initial_dir=self._app.config_root)`
   を開き `wait_window()`。
4. **設定の保存**: `dialog.scan_dirs` を `normalize_scan_dirs` で正規化し、**2 の値と異なるときだけ**
   `self._app.startup_io.write_startup({SCAN_DIRS_KEY: list(normalized)})` を呼ぶ。
   - **`dialog.result` が `False`（「閉じる」）でも保存する**。理由は設計メモ参照。
   - `write_startup` が偽を返した場合は**そのまま続行**（保存失敗は `write_startup` 内で
     `messagebox.showerror` 済み。棚卸し自体は止めない）。
5. `dialog.result` が偽なら `return`（走査しない）。
6. **走査**: `scan_orphans(..., scan_dirs=list(normalized), ...)`（他の引数は**無変更**）。
7. 結果表示は**無変更**（`format_orphan_notice` / `format_orphan_plan`）。

- モジュール定数 **`SCAN_DIRS_KEY = "orphan_sweep_scan_dirs"`** を同ファイルの先頭に置く。
- **走査結果を設定へ書き戻さない**（`missing_scan_dirs` に出たディレクトリを消さない。§3-5-1）。

### 変更なし（確認のみ）

- `keyseq/presentation/orphan_sweep_text.py` — **不在時の報告は task_03 で実装済み**
  （`format_scan_warnings` の `missing_scan_dirs` 節）。本タスクで**変更しない**。
  本タスクで初めて `scan_dirs` に実値が入るため、この経路が実際に機能するようになる。
- `keyseq/presentation/controllers/config_io/startup_io.py` — **`write_startup` をそのまま使う**
  （`write_global_hook_keys:61-69` と同じ使い方）。**専用ラッパを増やさない**。

### 変更・追記: テスト

- `tests/test_orphan_scan.py` へ **`normalize_scan_dirs` のテストを追記**（新規ファイルを作らない）。
- `tests_ui/test_orphan_sweep_flow.py` へ **設定の読み書きとダイアログ経由のフローを追記**。
  **`patch.object` を優先**する。`filedialog.askdirectory` は
  `patch.object(orphan_sweep_dialog.filedialog, "askdirectory", ...)` の形で差し替える。

### 設計メモ / 制約

- **「閉じる」でも設定を保存する理由**: 走査ディレクトリの追加 / 削除は**明示的な設定操作**であり、
  「閉じる」は**今回は棚卸しを走らせない**の意（§2「設定として記録し、次回以降の再指定を不要にする」）。
  誤解を避けるため**ボタンラベルを「キャンセル」ではなく「閉じる」**にする。
  ※ 暫定仕様に明文が無いため**本タスクで定める規約**。結果確認側のボタン（§3-9 の
  「実行 / キャンセル」）とは別物なので混同しないこと。
- **受け入れ条件 15（棚卸しによる書き込み 0 件）の対象外**（M6）。§3-10 の設定保存と §3-4 の
  保存確認は明示的に対象外と規定されている。ただし**走査そのもの**（`scan_orphans`）は
  引き続き書き込みゼロであること。
- **`dirty_tracker` を触らない**。走査ディレクトリ設定は `config.json` 側で、keymap_set の
  未保存状態とは無関係（`write_startup` は `config.json` のみを書く）。
- task_02 の申し送り: **`missing_scan_dirs` の表記が不揃い**（`orphan_scan.py:77`。既定
  `user/keymap_sets/` が無い場合だけ絶対パスで入る）。本タスクで**初めて実際に一覧表示される**ため、
  テストで表示内容を確認する。**是正が必要なら報告のみ**行い、本タスクでは修正しない
  （範囲外。必要なら別タスク）。
- 例外を握り潰さない。関数はおおむね 30 行以内・新規ファイルは 300 行以内を目安に分割する。
- **`ReferenceCleanupDialog` を変更しない**（引数化は task_06）。本タスクの `OrphanSweepDialog` は
  **別クラス**として新設する（用途が違う: 入口の設定 + 実行開始 vs 結果確認）。

## 含まない

- **隔離 / 復元 / 削除・マニフェスト・「隔離の管理…」メニュー・実行単位のリスト選択 UI** = **task_05 / task_06**。
- **結果確認ダイアログの導入（`ReferenceCleanupDialog` のヘッダ / ボタンラベル引数化）** = **task_05 / task_06**。
  本タスクでも**結果の提示は `messagebox.showinfo` のまま**。
- **孤児候補の行ごとの選択 UI** = スコープ外（暫定仕様 §3-9 で作らないと確定）。
- **走査ディレクトリの再帰走査・候補側への追加** = スコープ外（§3-2-4 は**直下の `*.json`** のみ）。
- **見つからなかったディレクトリの自動削除** = **禁止**（§3-5-1）。
- **`missing_scan_dirs` の表記の不揃いの是正** = 本タスクでは行わない（報告のみ）。
- **統合確認・実機目視の観点リスト** = **task_07**。
- 正本 `spec_detail/` の改訂（§5.4 への走査ディレクトリ設定キーの追記を含む）= **task_08**。

## 確認

`.venv` の python で実行する（`.claude/rules/python_rules.md`。worktree ルートから）。

```
..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui
..\..\..\.venv\Scripts\python.exe -m tests.smoke_app
```

**単体テストの項目**（`tests/test_orphan_scan.py` へ追記・`normalize_scan_dirs`）:

1. **非文字列要素**（`None` / `int` / `dict` / ネストした list）が**除去**され、例外にならない。
2. `values` が `list` / `tuple` でない（`None` / `str` / `dict`）ときは**空タプル**を返す。
3. **空文字・空白のみ**の要素が除去される。
4. **同じディレクトリを指す相対 / 絶対 / 区切り違い（`\` と `/`）が 1 つへ寄り**、
   **入力順の先頭が残る**。
5. **config 配下は config 相対表記**、**config 外は絶対表記**で返る（正本 §5.7）。
   **canonical 表記（normcase 済み）を返さない**。
6. **実在しないディレクトリも除去されない**（§3-5-1）。
7. `ConfigService.normalize_scan_dirs` の戻り値がモジュール関数の戻り値と一致する。

**UI フローの項目**（`tests_ui/test_orphan_sweep_flow.py` へ追記）:

8. **設定の読み出し**: `_startup_settings["orphan_sweep_scan_dirs"]` の値が
   `scan_orphans` の `scan_dirs` へ**正規化されて渡る**（`[]` 固定でなくなったこと）。
   **設定キーが無い場合は空リスト**で渡る。
9. **壊れた設定**（非 list / 非文字列要素混じり）でも例外にならず、走査が続行する。
10. **ダイアログで「棚卸しを実行」→ 走査が呼ばれる** / **「閉じる」→ 走査が呼ばれない**
    （`scan_orphans` の呼び出し有無で assert）。
11. **設定に変更があれば `write_startup` が呼ばれ**、キー `orphan_sweep_scan_dirs` に
    正規化済みの一覧が渡る。**「閉じる」で終わった場合も保存される**。
12. **設定に変更が無ければ `write_startup` は呼ばれない**。
13. **`write_startup` が偽を返しても走査は続行**する（保存失敗で棚卸しを止めない）。
14. **`config.json` を直接書いていない**（`config_service.save_startup` が
    `startup_io.write_startup` 経由でのみ呼ばれること。**IO から `save_startup` を直呼びしない**）。
15. **受け入れ条件 14**: `write_startup` で設定を保存した後に **keymap_set の保存**を行っても、
    `config.json` から `orphan_sweep_scan_dirs` が**失われない**。**既存キーも失われない**
    （`_startup_settings` を経由するため。実ファイルを読み直して確認する）。
16. **見つからない走査ディレクトリが設定から自動削除されない**（走査後も
    `_startup_settings` の値が不変。§3-5-1）。
17. **見つからない走査ディレクトリが結果表示に出る**（受け入れ条件 7。
    task_03 の `format_scan_warnings` 経由。**「警告」の語を含まない**）。
    **task_02 の申し送りの確認**: 既定 `user/keymap_sets/` が存在しない config_root で走査したとき、
    `missing_scan_dirs` にどう表示されるかを assert し、**表記が不揃いなら報告する**（修正はしない）。
18. **走査そのものはファイルを書かない**（設定保存・未保存確認の保存を除く。受け入れ条件 15）。

**ダイアログの項目**（`tests_ui/test_orphan_sweep_flow.py` へ追記）:

19. **初期表示の Listbox の内容が渡した `scan_dirs` と一致**する。
20. **「追加…」で `askdirectory` の戻り値が一覧へ追加**される。**空文字（キャンセル）では追加されない**。
    **同じディレクトリの重複追加が防がれる**。
21. **「削除」で選択行が消える**。**選択が無いときは何も起きない**。
22. **`result` の既定が `False`** で、「棚卸しを実行」で `True` になる。
    **`<Escape>` / ウィンドウを閉じる操作では `False` のまま**。

**退行の基準**: `tests` は **309 → 増加**、`tests_ui` は **248 → 増加**（どちらも減らさない・実測 2026-09-06）。
既存の `tests_ui/test_reference_cleanup_flow.py` 9 件 / `tests/test_reference_cleanup_text.py` 8 件 /
`tests_ui/test_orphan_sweep_flow.py` の既存 10 件は**壊さない**（既存 10 件は `run_sweep` の
フロー変更に伴う**最小限の修正は可**。その場合は修正理由を報告に含める）。
smoke pass。実行後に**worktree ルートへ `user/` が生成されていない**ことも確認する。

## 完了条件

- 上記「確認」がすべて pass（実測は **`verifier`** が行う。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（`.claude/rules/review.md` の 5 観点。特に
  **仕様適合性**〔`config.json` を直接書いていないか・`_startup_settings` 経由で keymap_set 保存後も
  残るか・見つからないディレクトリを消していないか〕・
  **依存方向**〔ダイアログが `config.json` を触っていないか・presentation が `config_service` の
  内部モジュールを直参照していないか〕・
  **不要変更の有無**〔`ReferenceCleanupDialog` / `reference_cleanup_*` を触っていないか・
  後続タスクの隔離処理を先取りしていないか〕）。
- **実機目視は本タスクでは行わない**（**task_07 でまとめて実施**する）。
  ただし本タスクは**新規ダイアログを伴う**ため、task_07 の目視観点に
  「走査ディレクトリの追加 / 削除と再起動後の保持」を必ず含めること。
