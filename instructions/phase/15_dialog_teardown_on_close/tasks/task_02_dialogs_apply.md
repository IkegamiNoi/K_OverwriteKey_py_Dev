# task_02_dialogs_apply

## 目的

task_01 で `HookController` に入れた**破棄時の自動解除**を、`keyseq/presentation/dialogs/` の
**8 クラス**へ適用する。暫定仕様 [13](../../../history/13_dialog_teardown_on_close.md)（v0.4）の
**§4-4**（各ダイアログの変更）/ **§3**（T1・T2 の分類）/ **§6-1**（空になる override は削除）が根拠。

**presentation 限定。domain / application / infrastructure は不変。スキーマ不変。**
**`HookController` / `app.py` / `modal.py` は本タスクでは触らない**（task_01 で確定済）。

## 対象範囲（presentation 限定・dialogs 8 ファイル + 影響を受ける既存テストの最小修正）

### 1. 8 クラス共通の変更（2 点のみ）

1. `self.parent.hook.suspend_hook_for_dialog()` → **`self.parent.hook.suspend_hook_for_dialog(self)`**。
   **呼ぶ位置は動かさない**（いずれも `super().__init__(parent)` の後なので `self` は有効な `Toplevel`）。
2. `destroy()` override から **`self.parent.hook.resume_hook_after_dialog()` の行を削除**。
   **二重実行を防ぐため必ず削る**（残すと OK 経路で override と破棄イベントの 2 回走る）。
   同じ行に付いているコメント（「ダイアログ終了でフックを必要なら再開」等）も一緒に削る。

### 2. ファイル別の内訳

| ファイル | suspend | `destroy()` override の扱い |
|---|---|---|
| `action_dialog.py` | `:25` | **残す**（`self._stop_recording()` = T2） |
| `keymap_edit_dialog.py` | `:25` | **残す**（`self._stop_capture()` = T2） |
| `trigger_dialog.py` | `:26` | **残す**（`self._stop_capture()` = T2） |
| `orphan_sweep_dialog.py` | `:17` | **残す**（`self.scan_dirs = tuple(self.listbox.get(...))` = T2） |
| `layout_delete_dialog.py` | `:22` | **override ごと削除**（`:63-65`・空になる） |
| `preset_manager.py` | `:80` | **override ごと削除**（`:383-386`・空になる） |
| `quarantine_manage_dialog.py` | `:17` | **override ごと削除**（`:63-65`・空になる） |
| `reference_cleanup_dialog.py` | `:29` | **override ごと削除**（`:63-65`・空になる） |

- **`preset_dialog.py` は対象外**（suspend を呼んでおらず override も無い）。
- override を残す 4 クラスは **`super().destroy()` の呼び出しを残す**（T2 の後に呼ぶ現在の順序のまま）。
- override を削除する 4 クラスは **`tk.Toplevel.destroy` をそのまま継承する**
  （空の override・`pass` だけの override を残さない）。

### 3. 既存テストの最小修正（本タスクで壊れる分のみ）

呼び出し形の変更で**アサーションが直接壊れるテストだけ**を直す。**新規テストは書かない**（task_03）。

| 対象 | 現状 | 直し方 |
|---|---|---|
| `tests_ui/test_orphan_sweep_flow.py:514-523` | `suspend.assert_called_once_with()` / `resume.assert_called_once_with()` | suspend 側は **`assert_called_once_with(dialog)`** へ。resume 側は**モック観測をやめ**、`self.app.update()` を回した後に **`self.app.hook.get_hook_pause_count()` が 0** であることで見る（suspend を patch すると結線ごと消えるため、resume の観測点は**実カウンタ**へ移す） |
| `tests_ui/test_quarantine_manage_flow.py:295-305` | 同上 | 同上 |
| `tests_ui/test_quarantine_manage_flow.py:307-321` | `resume.assert_called_once_with()` | `self.app.update()` 後の `get_hook_pause_count() == 0` へ置換 |
| `tests_ui/test_quarantine_manage_flow.py:323-335` | `resume.assert_called_once_with()` | 同上 |
| `tests_ui/test_app_ui_flows.py:1936-1952` | `resume_calls_after_destroy == 1` | suspend 側は `suspend_hook.call_count == 1` のまま可（引数検証をするなら `dialog` 付き）。resume 側は `self.app.update()` 後の `get_hook_pause_count() == 0` へ置換 |

- **`update()` が必要**（`after(0)` は `update_idletasks()` では実行されない。暫定仕様 §4-2）。
- **上記以外のテストは触らない**。`patch.object(..., "resume_hook_after_dialog")` を
  アサーション無しで使っているだけの箇所（`test_app_ui_flows.py` の多数 / `test_nested_modal_grab.py:36-37`）は
  **そのまま**でよい。
- **`test_app_ui_flows.py:1325-1341`（`test_preset_manager_cancel_keeps_runtime_and_dirty_unchanged`）は
  本タスクでは触らない** — override 削除後は `tk.Toplevel.destroy` の patch に解決して
  **pass のまま意味が空になる**。観測点の移設は **task_03**（暫定仕様 §6-2）。

### 設計メモ / 制約

- **`grab_modal(self, parent)` は `__init__` の最後の文のまま**（phase 14 の静的検査
  `tests_ui/test_nested_modal_grab.py` が固定している）。suspend は初期化の冒頭なので衝突しない。
  **`grab_modal` の位置・有無を動かさない**。
- **`protocol("WM_DELETE_WINDOW", self.destroy)` / `bind("<Escape>", ...)` は現状のまま**
  （`orphan_sweep` / `quarantine_manage` / `reference_cleanup` にある）。
  **足さない・消さない**（案 A は採らない＝暫定仕様 §2）。
- **T2 の処理を破棄イベント側へ移さない** — `<Destroy>` の時点で**子ウィジェットは既に破棄済**で
  `TclError` になる（暫定仕様 §1-④）。`scan_dirs` の収集は `destroy()` override のままが正。
- **やってはいけないこと**: `HookController` / `app.py` / `modal.py` の変更 /
  ダイアログ同型スケルトンの共通化 / `key_capture.py`・`keyboard_window.py`・
  `controllers/config_io/` の try/finally 形の変更（**引数なし呼び出しのまま**）/
  `ActionDialog` の親付け替え（idea_17）。

## 含まない

- **受け入れ条件のテスト**（× 閉じ / 二重実行なし / 子ウィジェット破棄 / アプリ終了時 /
  phase 14 非退行 / **静的検査**）→ **task_03**。
- **`test_app_ui_flows.py:1325-1341` の観測点移設** → **task_03**（暫定仕様 §6-2）。
- **統合確認・二次レビュー・実機目視** → **task_04**。
- **正本反映・暫定仕様の凍結** → **task_05**。
- 非ダイアログ経路 5 系統の結線方式の変更（暫定仕様 §9・**終了ガードは task_01 で対応済**）。

## 確認

python は必ずリポジトリルートの `.venv`（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier` へ委任する**（Codex は python を実行できない）。

1. **静的確認**: `python -m compileall -q keyseq main.py tests tests_ui` が clean。
2. **呼び出し形の全数確認**:
   `grep -rn "suspend_hook_for_dialog" keyseq/presentation/dialogs/` が **8 件すべて `(self)` 付き**。
   `grep -rn "resume_hook_after_dialog" keyseq/presentation/dialogs/` が **0 件**。
3. **override の残存確認**: `grep -rn "def destroy" keyseq/presentation/dialogs/` が
   **4 件のみ**（`action_dialog` / `keymap_edit_dialog` / `trigger_dialog` / `orphan_sweep_dialog`）。
4. **非対象の無変更確認**: `git diff --stat` に
   `keyseq/presentation/controllers/` / `keyseq/presentation/app.py` /
   `keyseq/presentation/modal.py` / `keyseq/presentation/dialogs/preset_dialog.py` が**現れない**。
   `grep -rn "suspend_hook_for_dialog()" keyseq/` の引数なし呼び出しが
   **`controllers/` と `keyboard_window.py` の 7 箇所のまま**。
5. **既存テストが pass**:
   - `python -m unittest discover -s tests` = pass 417（skip 7）。
   - `python -m unittest discover -s tests_ui` = **pass 311**（task_01 までと同数。本タスクは
     テストを増減させない）。
   - `python -m tests.smoke_app` が pass。
6. テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されていないこと。

## 完了条件

- 上記「確認」1〜6 がすべて pass。
- **`reviewer` 採用**（CLAUDE.md「レビュー（必須）」）。観点は `.claude/rules/review.md` の 5 観点 +
  phase.md「レビュー方針」の固有観点（**二重実行** / **phase 14 との干渉**＝`grab_modal` が
  `__init__` の最後の文のままか / **`window` 省略時の非変更**＝`controllers/` 側が無変更か /
  **スコープ逸脱**＝スケルトン共通化・親付け替えを取り込んでいないか）。
- **実機目視は本タスクでは行わない**（task_04 でまとめて実施）。
