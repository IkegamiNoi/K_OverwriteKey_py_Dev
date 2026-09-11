# task_04_grab_contract_tests

## 目的

暫定仕様 [12](../../../history/12_nested_modal_grab_restore.md)（**v0.5**）の復元契約 3 条を
実ダイアログ経路で固定する。
**§3-6**（grab 取得後に初期化を残さない）/ **§3-7**（非 LIFO 終了で grab を奪わない）/
**§3-8**（コールバック例外では子を閉じない）が対象。

あわせて **§3-6 の不変条件を全 13 箇所で成立させるための行移動**を行う
（系統 B の 4 箇所で `protocol` / `bind` の登録を `grab_modal` の前へ移す。**挙動同値**）。

**presentation 限定。domain / application / infrastructure は不変。スキーマ不変。**

### 前提（v0.5 での改訂点・必読）

§3-6 は **v0.5（2026-09-11・ユーザー確定）で規定が変わっている**。
v0.4 までの「初期化失敗時に**破棄 → 復元 → 再送出**する」は**撤回済み**で、
**回収機構は実装しない**。現在の規定は次のとおり:

- `grab_modal()` を**初期化の最後の文**に置く。待機（`wait_window()`）だけは後に置いてよい。
- 例外が `grab_modal()` より前で出れば、子はまだ grab を取っていないので
  **親が grab を保持したまま**になる。
- この規約を**静的検査テストで固定**する。

判断の経緯は `.claude_data/state/decisions.md`「2026-09-11 (phase 14 / 暫定仕様 12)」。

## 対象範囲

### 1. production の行移動（presentation 限定・4 箇所）

`grab_modal(...)` の**後ろに残っている登録行を前へ移す**。移動するのは登録の呼び出しだけで、
**`wait_window()` は後ろのまま**にする。

| ファイル | 現状 | 移動後 |
|---|---|---|
| `controllers/config_io/child_save_dialog.py:25-27` | `grab_modal` → `protocol` → `wait_window` | `protocol` → `grab_modal` → `wait_window` |
| `controllers/config_io/child_save_dialog.py:241-244` | `grab_modal` → `protocol` → `bind` → `wait_window` | `protocol` → `bind` → `grab_modal` → `wait_window` |
| `controllers/config_io/io_dialogs.py:56-59` | `grab_modal` → `protocol` → `try: wait_window` | `protocol` → `grab_modal` → `try: wait_window` |
| `controllers/config_io/hotkey_presets_io.py:82-84` | `grab_modal` → `protocol` → `wait_window` | `protocol` → `grab_modal` → `wait_window` |

（行番号は起票時点。ズレていたら該当箇所を探して適用する。）

**これは挙動同値の移動**。`protocol` / `bind` はハンドラを登録するだけで、
grab の有無に依存しない。**9 クラス側（`dialogs/`）は既に条件を満たしているので触らない**。

### 2. `tests_ui/test_nested_modal_grab.py`（既存ファイルへ追記）

task_03 で作った同ファイルに追記する（**新規ファイルを作らない**）。
既存の `setUpClass` / fail-fast ガード / `addCleanup` の後始末をそのまま使う。

**追加するテスト（4 本）**:

1. **§3-6 実行時**: `PresetManagerDialog` が grab を持つ状態で `PresetDialog` を開く際、
   **`grab_modal` より前で例外を発生させる**（例: `PresetDialog` の初期化途中で
   使われるメソッドを patch して例外を送出、または `tk.Toplevel` 側ではなく
   `PresetDialog` 内のウィジェット構築を patch する）。確認点:
   - 例外が**そのまま呼び出し元へ送出**される（`assertRaises`）。
   - **`grab_current()` が `PresetManagerDialog` のまま**であること。
   - マネージャが生存していること。

2. **§3-6 静的検査**: `keyseq/presentation/` のソースを `ast` で走査し、次の 2 点を固定する。
   - **`dialogs/` の 9 クラスの `__init__` の最後の文が `grab_modal(...)` の呼び出し**であること。
   - **`grab_modal(...)` の後に続く文は待機（`wait_window`）だけ**であること
     （系統 B の 4 箇所が該当。`try:` で包まれた `wait_window` も待機として許可する）。
   先例は `tests/test_config_service_contracts.py`（AST 走査による逆戻り防止テスト）。
   **違反時のメッセージにファイル名と行番号を含める**こと。

3. **§3-7 非 LIFO 終了**: **App を共通の master とする 3 段**を作る。
   `ActionDialog`（App の子）→ `PresetManagerDialog`（`action_dialog.py:341` で App の子）→
   上書き確認ダイアログ（`hotkey_presets_io.py:45` で App の子）。
   **中間の `PresetManagerDialog` だけをプログラムから破棄**し、確認点:
   - **最内側（確認ダイアログ）が grab を保ったまま**であること（奪われない）。
   - その後に確認ダイアログを閉じたとき、**記録した保持者が既に破棄されているので
     復元は起きない**こと（`grab_current()` が `None`）。これは**現仕様どおりの挙動**で、
     連鎖復元は保証範囲外（§3-5）。**期待値としてこの形で固定する**。

4. **§3-8 コールバック例外**: 実際の Tk コールバック経由で例外を起こす。
   `PresetDialog` の OK ボタンの `command`（`_ok`）を patch して例外を送出させ、
   **ボタンを `invoke()` する**。確認点は 3 つ:
   - `report_callback_exception` が**呼ばれる**（通知されている）。
   - **子が生存している**（`winfo_exists()` が真）。
   - **`grab_current()` が子のまま**であること。
   その後に子を閉じたら親へ復元されることも確認する。

### 設計メモ / 制約

**既存テストとの重複を作らない**
ヘルパ単体レベルの非 LIFO / 冪等 / withdraw 済みの復元回避は
`tests_ui/test_modal_grab.py`（task_01）に既にある。**本タスクは実ダイアログ経路で見る**。
同じことを 2 度書かない。

**テスト 1 の例外注入点**
`grab_modal` より**前**で失敗させることが要点。`PresetDialog.__init__` の中で
呼ばれる何か（`ttk.Entry` の生成など）を patch するか、`PresetDialog` を継承した
テスト用サブクラスで `__init__` の途中に例外を挟む形でよい。
**`grab_modal` 自体や `modal.py` を patch して擬似的に作らない**（実経路で見る）。

**テスト 3 の組み立て**
上書き確認ダイアログの開き方は task_03 の `_close_overwrite` と同じ手法
（`app.after(0, ...)` で開いた `Toplevel` を特定する）を再利用する。
**中間の破棄はその中で行う**。task_03 の 4 本目（`destroy_parent=True`）は
2 段での確認なので、**本タスクは 3 段にする**ことが違い。

**`report_callback_exception` の扱い**
task_03 の `setUp` は `report_callback_exception` を Mock 化し、`addCleanup` で
`assert_not_called` を登録している。**テスト 4 では呼ばれることが期待値**なので、
そのテストだけ `assert_not_called` の登録を外すか、呼び出しを検証してから
Mock をリセットする形にする。**既存 3 テストのガードを弱めないこと**。

**やってはいけないこと**
- `modal.py` の実装変更（v0.5 の規定は現行実装で満たされている）。
- `dialogs/` 9 ファイルの変更（既に条件を満たしている）。
- 回収機構（破棄 → 復元 → 再送出）の実装（**v0.5 で撤回済み**）。
- `wait_window` / `grab_set` / `grab_current` を no-op へ patch して経路を短絡させること。

## 含まない

- **統合確認（全スイート再実行）と実機目視**（stdlib ダイアログ 4 経路）→ **task_05**。
- **正本反映・暫定仕様 12 の凍結・`/refactor_check`** → **task_06**。
- **× 閉じでフック再開が走らない不具合の是正** →
  [idea_16](../../../backlog/idea_16_wm_close_skips_destroy_override.md)（**フェーズ外**）。
- ダイアログ同型スケルトンの共通化 / `ActionDialog` の親付け替え / stdlib ダイアログの grab。

## 確認

python は必ずリポジトリルートの `.venv`（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier` へ委任する**（Codex は python を実行できない）。

1. **静的確認**: `python -m compileall -q keyseq main.py tests tests_ui` が clean。
2. **新規テストが pass**: `python -m unittest tests_ui.test_nested_modal_grab -v` で
   **8 本すべて pass**（task_03 の 4 本 + 本タスクの 4 本・skip なし）。
3. **既存テストが据え置き**:
   - `python -m unittest discover -s tests` = pass 417（skip 7）。
   - `python -m unittest discover -s tests_ui` = **pass 303**（299 + 新規 4）。
   - `python -m tests.smoke_app` が pass。
4. **行移動が挙動同値であることの確認**: `git diff` で系統 B の 4 箇所が
   **登録行の移動のみ**（追加・削除・書き換えなし）であること。
5. **静的検査テストが実際に効くことの確認（変異検査）**: `dialogs/` のいずれか 1 ファイルで
   `grab_modal` の後ろに 1 文（例: `self.update_idletasks()`）を一時的に足すと
   **静的検査テストが fail** すること。**確認後は必ず元へ戻し、`git diff keyseq/` が
   意図した 4 箇所の行移動だけであることを再確認する**（`verifier` へ依頼する）。
6. テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されていないこと。

## 完了条件

- 上記「確認」1〜6 がすべて pass。
- **`reviewer` 採用**（CLAUDE.md「レビュー（必須）」）。観点は `.claude/rules/review.md` の 5 観点 +
  phase.md「レビュー方針」の固有観点。特に **v0.5 の §3-6 を正しく反映しているか**
  （回収機構を実装していないか / 静的検査が不変条件を過不足なく突いているか）。
- **実機目視は本タスクでは行わない**（task_05 でまとめて実施）。
