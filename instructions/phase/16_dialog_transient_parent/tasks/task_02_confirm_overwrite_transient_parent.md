# task_02_confirm_overwrite_transient_parent

## 目的

上書き確認ダイアログの**前面維持の相手**を、呼び出し元である `PresetManagerDialog` にする。
暫定仕様 [14](../../../history/14_dialog_parent_and_app_separation.md)（v0.4）の **§3-3** が根拠。
**食い違い 2 件のうちの 2 件目**（1 件目は task_01 で対応済）。

**presentation 限定。domain / application / infrastructure は不変。スキーマ不変。正本の改訂なし。**
**変えてよいのは `grab_modal` の第 2 引数（役割 2 = 前面維持）だけ**。
**`tk.Toplevel` の引数（役割 1 = 所有関係）と `self._app`（役割 3 = App 参照）は触らない**。

## 対象範囲（presentation 限定・2 ファイル + 既存テスト 4 箇所）

### 1. `keyseq/presentation/controllers/config_io/hotkey_presets_io.py`

**(a) `confirm_overwrite` にキーワード必須の引数を足す**（`:44`）

```python
def confirm_overwrite(self, *, stored_path: str, existing: list | None,
                      transient_parent: tk.Misc) -> str:
```

- **既定値を置かない** — 呼び出し元は `preset_manager.py:364` の**1 箇所だけ**なので、
  既定を置くと**初日から到達しない分岐**になる（`anti_patterns.md` 3・暫定仕様 §3-3）。
  **task_01 の `PresetManagerDialog` が既定ありなのと非対称だが、これは意図どおり**
  （あちらは `app.py:418` という既定を使う呼び出し元が実在する）。
- 型注釈のために `tkinter` の参照が要る。**既存の import を確認し、無ければ足す**。

**(b) `grab_modal` の第 2 引数だけを差し替える**（`:82`）

```python
grab_modal(dialog, transient_parent)
```

- **`tk.Toplevel(self._app)`（`:47`）は無変更**（役割 1 = 所有関係は App のまま）。
- **`dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)`（`:81`）の位置も変えない**。

### 2. `keyseq/presentation/dialogs/preset_manager.py`

`on_ok` 内のコールバック（`:363-366`）から渡す。

```python
choice = self.parent.hotkey_presets_io.confirm_overwrite(
    stored_path=stored_path,
    existing=existing,
    transient_parent=self,
)
```

- **`self.parent`（役割 3 = App 参照）はそのまま**。`hotkey_presets_io` の取得経路も変えない。

### 3. 既存テストの引数契約の追随（**4 箇所・これで全数**）

| 対象 | 直し方 |
|---|---|
| `tests_ui/test_app_ui_flows.py:1201` | 期待値へ **`transient_parent=dialog`** を足す（`PresetManagerDialog.on_ok(dialog)` をスタブへ直接呼ぶ形なので、渡るのはそのスタブ） |
| `tests_ui/test_app_ui_flows.py:1261` | 同上 |
| `tests_ui/test_app_ui_flows.py:1313` | 同上 |
| `tests_ui/test_nested_modal_grab.py:185` | 期待値へ **`transient_parent=dialog`** を足す（`:176` で `dialog = self._preset_manager()` としている実ダイアログ） |

- **引数契約の追随のみ**を行う。
- **禁止**: `grab`・生存・復元先・`master` に関するアサーションを弱めること。
  **落ちたらテストを緩めず、原因を報告して止まる**（暫定仕様 §4）。

### 設計メモ / 制約

- **application 層は通らない** — コールバック `on_overwrite_conflict` は
  `preset_manager.on_ok` 内で定義され、`app.save_hotkey_presets`（`app.py:423`）は
  それを 2 引数で呼ぶだけ（`:457`）。**`save_hotkey_presets` のシグネチャは変えない**。
- **`presentation/modal.py` を触らない**。
- **やってはいけないこと**: `tk.Toplevel` の引数の変更 / `self._app`・`self.parent` の変更 /
  他 7 ダイアログへの引数追加 / 受け入れ条件のテスト追加（**task_03**）/
  4 箇所以外の既存テストの変更。

## 含まない

- **受け入れ条件のテスト・変異検査** → **task_03**。
- **統合確認・二次レビュー・実機目視** → **task_04**。
- **正本反映・暫定仕様の凍結** → **task_05**。
- 役割 1（所有関係）の付け替え / 正本 `features.md` の改訂（暫定仕様 §6）。

## 確認

python は必ずリポジトリルートの `.venv`（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier` へ委任する**（Codex は python を実行できない）。

1. **静的確認**: `python -m compileall -q keyseq main.py tests tests_ui` が clean。
2. **役割 1 / 役割 3 の無変更**:
   `grep -n "tk.Toplevel(" keyseq/presentation/controllers/config_io/hotkey_presets_io.py` が
   **`self._app` のまま**。`git diff` に `self._app = ` の変更が現れない。
3. **キーワード必須になっていること**:
   `confirm_overwrite` の定義に **`transient_parent` の既定値が無い**こと。
4. **非対象の無変更**: `git diff --stat` に `keyseq/presentation/app.py` /
   `keyseq/presentation/modal.py` / `dialogs/` の**他ファイル**が現れない
   （`preset_manager.py` は対象）。
5. **既存テストが pass**:
   - `python -m unittest discover -s tests` = pass 417（skip 7）。
   - `python -m unittest discover -s tests_ui` = **pass 321**（本タスクはテストを増減させない）。
   - `python -m tests.smoke_app` が pass。
   - **`tests_ui.test_nested_modal_grab` が単独でも pass**。
6. **アサーションを弱めていないこと**: `git diff -- tests_ui/` の変更が
   **`transient_parent=` の追加 4 行だけ**であること（削除・緩和が無い）。
7. テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されていないこと。

## 完了条件

- 上記「確認」1〜7 がすべて pass。
- **`reviewer` 採用**（CLAUDE.md「レビュー（必須）」）。観点は `.claude/rules/review.md` の 5 観点 +
  phase.md「レビュー方針」の固有観点（**役割の混同** / **既定の扱いの非対称が意図どおりか** /
  **既存テストのアサーションを弱めていないか** / **スコープ逸脱**）。
- **実機目視は本タスクでは行わない**（task_04 でまとめて実施）。
