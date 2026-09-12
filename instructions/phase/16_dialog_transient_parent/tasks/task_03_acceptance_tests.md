# task_03_acceptance_tests

## 目的

task_01 / task_02 が暫定仕様 [14](../../../history/14_dialog_parent_and_app_separation.md)（v0.4）の
**§5 受け入れ条件 1〜4** を満たすことをテストで固定する。根拠は **§4（テスト方針）**。

**tests_ui 限定。`keyseq/` 配下の production コードは 1 行も変更しない**
（変異検査の一時変更は確認後に必ず戻す）。

## 【最重要】観測点の指定

**呼び出し引数を見るだけの検査は無効**。task_01 / task_02 の変異検査で、
**`grab_modal` の第 2 引数を元へ戻しても既存テストが全て pass する**ことが実測で分かっている
（task_02 で追随した 4 件は「引数が渡されたこと」しか見ていない）。

**本タスクのテストは実際の前面維持の相手を観測する**。

- **観測 API は `wm_transient()`**。**戻り値は `Tcl_Obj` でウィジェットではない**（実測）。
  **`assertIs` は使えない**。**`str()` で比較する**: `self.assertEqual(str(w.wm_transient()), str(parent))`。
  未設定のときは **`''`** が返る。
- 所有関係は **`w.master`** で見る（こちらはウィジェットなので `assertIs` でよい）。

## 対象範囲（tests_ui 限定・production 不変）

### 1. 新規ファイル `tests_ui/test_dialog_transient_parent.py`

`tests_ui/test_nested_modal_grab.py` の作法を流用する（`setUpClass` で `App` を 1 個 /
`_patch` ヘルパ / `report_callback_exception` の監視 / `cleanup_window` /
`update_idletasks()` + `winfo_viewable()` アサート）。

| # | 条件 | 内容 |
|---|---|---|
| T1 | §5-1・§5-3 | **アクション編集から開いたプリセット編集** — `ActionDialog` を実生成し `_open_preset_manager()` 経由でプリセット編集を開く。**`str(manager.wm_transient()) == str(action)`** かつ **`manager.master is app`**（所有関係が動いていないこと） |
| T2 | §5-4 | **既定の非変更** — `PresetManagerDialog(app)` で開くと **`str(manager.wm_transient()) == str(app)`** かつ **`manager.master is app`** |

- **`_open_preset_manager()` は `wait_window()` を呼ぶ**ため、
  `PresetManagerDialog.__init__` を patch して**開いた直後に閉じる**か、
  `after(0, ...)` で閉じる（`test_nested_modal_grab.py:92-110` の先例）。
- **`app` を `str()` すると `'.'`**（Tk のルート）。比較はこの形でよい。

### 2. 既存ファイル `tests_ui/test_nested_modal_grab.py` へ 1 本追加

| # | 条件 | 内容 |
|---|---|---|
| T3 | §5-2・§5-3 | **上書き確認の前面維持** — `_overwrite_conflict()` と `_close_overwrite()`（`:121-155`）を使い、確認ダイアログを捕まえて **`str(confirm.wm_transient()) == str(manager)`** かつ **`confirm.master is app`** |

- **新規ファイルではなくここへ足す理由**: 上書き確認を出すには
  `config_service` の 3 メソッドを patch する足場（`_overwrite_conflict`）と、
  新規 `Toplevel` を走査して捕まえる足場（`_close_overwrite`）が要る。
  **新規ファイルへ移すと 40 行規模の足場を複製する**ことになる（`anti_patterns.md` 3）。
- **既存テストのアサーションは 1 行も触らない**。**追加のみ**。

### 3. 変異検査（**両方とも fail することを確認する**）

| # | 壊す箇所 | 落ちるべきテスト |
|---|---|---|
| M1 | `dialogs/action_dialog.py:339` から `transient_parent=self` を外す | **T1** |
| M2 | `controllers/config_io/hotkey_presets_io.py:83` の `grab_modal` の第 2 引数を `self._app` へ戻す | **T3** |

**M1 / M2 のどちらかで落ちないテストがあれば、そのテストは空振りしている**。
確認後は必ず元へ戻し、**`git diff keyseq/` が空**であることを再確認する。

### 設計メモ / 制約

- **production コードを直さない**。テストが落ちた場合、原因が task_01 / task_02 の実装にあるなら
  **報告して判断を仰ぐ**（本タスクで production を書き換えて通さない）。
- **`assertIs` を `wm_transient()` の戻り値に使わない**（`Tcl_Obj` のため必ず失敗する）。
- **既存テストのアサーションを弱めない**（削除・緩和は禁止）。
- **phase 14 / 15 の非退行は既存スイートで担保する**。**新規に重複したテストを作らない**
  （`update_idletasks()` + viewable の作法は流用してよい）。
- **やってはいけないこと**: `keyseq/` 配下の変更 / 既存テストのアサーションの変更 /
  他 7 ダイアログ向けのテスト追加 / `modal.py` の検査追加。

## 含まない

- **統合確認・二次レビュー・実機目視** → **task_04**。
- **正本反映・暫定仕様 14 の凍結** → **task_05**。
- **production コードの変更**（`keyseq/` 配下は本タスクで不変）。
- 役割 1（所有関係）に関する新しい保証の追加（暫定仕様 §6 でスコープ外）。

## 確認

python は必ずリポジトリルートの `.venv`（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier` へ委任する**（Codex は python を実行できない）。

1. **静的確認**: `python -m compileall -q keyseq main.py tests tests_ui` が clean。
2. **新規テストが pass**: `python -m unittest tests_ui.test_dialog_transient_parent`（T1 / T2）。
3. **追加した T3 を含めて pass**: `python -m unittest tests_ui.test_nested_modal_grab`。
4. **変異検査 M1 / M2 がそれぞれ期待どおり fail**（上表）。**確認後に復元し `git diff keyseq/` が空**。
5. **既存テストが pass**:
   - `python -m unittest discover -s tests` = pass 417（skip 7）。
   - `python -m unittest discover -s tests_ui` = **321 + 新規分**（既存の件数は減らない）。
   - `python -m tests.smoke_app` が pass。
6. **production 無変更**: `git diff --stat` に `keyseq/` が**現れない**。
7. **既存アサーションの非改変**: `git diff -- tests_ui/test_nested_modal_grab.py` が
   **追加のみ**（削除行が無い）。
8. テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されていないこと。

## 完了条件

- 上記「確認」1〜8 がすべて pass。
- **`reviewer` 採用**。観点は `.claude/rules/review.md` の 5 観点 +
  phase.md「レビュー方針」の固有観点（**観測点が実際の `wm_transient()` か**〔呼び出し引数で
  代用していないか〕/ **所有関係の固定を含むか** / **既存アサーションを弱めていないか** /
  **スコープ逸脱**＝production を触っていないか）。
- **実機目視は本タスクでは行わない**（task_04 でまとめて実施）。
