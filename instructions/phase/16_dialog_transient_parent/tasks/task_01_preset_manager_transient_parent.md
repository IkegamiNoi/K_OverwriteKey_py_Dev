# task_01_preset_manager_transient_parent

## 目的

`PresetManagerDialog` に**前面維持の相手**を受け取る引数を足し、
`ActionDialog` からの呼び出しを追随させる。暫定仕様
[14](../../../history/14_dialog_parent_and_app_separation.md)（v0.4）の **§3-1 / §3-2** が根拠。

**presentation 限定。domain / application / infrastructure は不変。スキーマ不変。正本の改訂なし。**
**変えてよいのは `grab_modal` の第 2 引数（役割 2 = 前面維持）だけ**。
**`tk.Toplevel` の引数（役割 1 = 所有関係）と `self.parent`（役割 3 = App 参照）は触らない**。

## 対象範囲（presentation 限定・2 ファイル）

### 1. `keyseq/presentation/dialogs/preset_manager.py`

**(a) `__init__` にキーワード専用の引数を足す**（`:65`）

```python
def __init__(self, parent: App, title: str = "プリセット編集", *,
             transient_parent: tk.Misc | None = None):
```

- **引数名は `transient_parent`**。`owner` にしない（役割 1 と紛らわしいため。暫定仕様 §3-1）。
- **`super().__init__(parent)`（`:66`）は無変更**。
- **`self.parent = parent`（`_init_preset_manager_state` 内・`:75`）も無変更**。

**(b) `grab_modal` の第 2 引数だけを差し替える**（`:72`）

```python
grab_modal(self, transient_parent if transient_parent is not None else parent)
```

- **`grab_modal` が `__init__` の最後の文であることを変えない**
  （phase 14 の静的検査 `tests_ui/test_nested_modal_grab.py:262-276` が固定している。
  **落ちたらテストを緩めず止めてユーザーへ諮る**）。
- **既定は `parent`**（= App）。`app.py:418` の `PresetManagerDialog(self, title=...)` は
  **無変更で従来どおり**。

### 2. `keyseq/presentation/dialogs/action_dialog.py`

`:339` の呼び出しを追随させる。

```python
PresetManagerDialog(self.parent, title="ホットキープリセット編集", transient_parent=self).wait_window()
```

- **`self.parent`（App）を第 1 引数に渡すのは従来どおり**。App 参照として必要（暫定仕様 §1-⑤）。
- **`ActionDialog` 自身の引数・属性は変更しない**。

### 設計メモ / 制約

- **`tk` の import** — `preset_manager.py` が型注釈のために `tkinter` を参照できるか確認する。
  既に `import tkinter as tk` があればそれを使う。無ければ足してよい
  （`from __future__ import annotations` があるので実行時コストは無い）。
- **`app.py:418` を触らない**（既定で従来どおりになるのが設計の要点）。
- **`presentation/modal.py` を触らない** — `grab_modal` の実装も引数名も変えない。
- **やってはいけないこと**: `tk.Toplevel` の引数の変更 / `self.parent` の改名・付け替え /
  `confirm_overwrite` の変更（**task_02**）/ 他 7 ダイアログへの引数追加 /
  受け入れ条件のテスト追加（**task_03**）。

## 含まない

- **上書き確認ダイアログ（`confirm_overwrite`）の対応と既存テスト 4 件の追随** → **task_02**。
- **受け入れ条件のテスト・変異検査** → **task_03**。
- **統合確認・二次レビュー・実機目視** → **task_04**。
- **正本反映・暫定仕様の凍結** → **task_05**。
- 役割 1（所有関係）の付け替え / 正本 `features.md` の改訂（暫定仕様 §6）。

## 確認

python は必ずリポジトリルートの `.venv`（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier` へ委任する**（Codex は python を実行できない）。

1. **静的確認**: `python -m compileall -q keyseq main.py tests tests_ui` が clean。
2. **役割 1 / 役割 3 の無変更**:
   `git diff keyseq/presentation/dialogs/preset_manager.py` に
   **`super().__init__` と `self.parent = parent` の変更が現れない**。
   `grep -n "tk.Toplevel(" keyseq/presentation/dialogs/preset_manager.py` の結果が変わらない。
3. **`grab_modal` の位置**: `grep -n "grab_modal" keyseq/presentation/dialogs/preset_manager.py` が
   **`__init__` の最後の文のまま**（phase 14 の静的検査が pass することで確認する）。
4. **非対象の無変更**: `git diff --stat` に `keyseq/presentation/app.py` /
   `keyseq/presentation/modal.py` / `controllers/` が**現れない**。
5. **既存テストが pass**:
   - `python -m unittest discover -s tests` = pass 417（skip 7）。
   - `python -m unittest discover -s tests_ui` = **pass 321**（本タスクはテストを増減させない）。
   - `python -m tests.smoke_app` が pass。
   - **`tests_ui.test_nested_modal_grab` が単独でも pass**（静的検査を含む）。
6. テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されていないこと。

## 完了条件

- 上記「確認」1〜6 がすべて pass。
- **`reviewer` 採用**（CLAUDE.md「レビュー（必須）」）。観点は `.claude/rules/review.md` の 5 観点 +
  phase.md「レビュー方針」の固有観点（**役割の混同**＝役割 1・3 を触っていないか /
  **phase 14 との干渉**＝`grab_modal` が最後の文のままか /
  **スコープ逸脱**＝`confirm_overwrite`・他ダイアログ・`modal.py` を取り込んでいないか）。
- **実機目視は本タスクでは行わない**（task_04 でまとめて実施）。
