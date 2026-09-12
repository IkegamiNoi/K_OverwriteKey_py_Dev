# task_03_acceptance_tests

## 目的

task_01（`HookController` の破棄時自動解除 + 終了ガード）と task_02（`dialogs/` 8 クラスへの適用）が
**暫定仕様 [13](../../../history/13_dialog_teardown_on_close.md)（v0.4）§7 の受け入れ条件を満たすこと**を
テストで固定する。根拠は **§5（テスト方針）/ §7-1〜8（受け入れ条件）/ §6-2（意味が空になる既存テストの書き換え）**。

**tests_ui 限定。`keyseq/` 配下の production コードは 1 行も変更しない**
（変異検査の一時変更は確認後に必ず戻す）。スキーマ不変。

## 対象範囲（tests_ui 限定・production コード不変）

### 1. 新規ファイル `tests_ui/test_dialog_teardown_flows.py`

**書き方は `tests_ui/test_nested_modal_grab.py` を流用する**（`setUpClass` で `App` を 1 個 /
`_patch` ヘルパ / `report_callback_exception` の監視 / `cleanup_window` / `update_idletasks()` +
`winfo_viewable()` アサート）。**ただし `hook.suspend_hook_for_dialog` /
`hook.resume_hook_after_dialog` を patch しない**（patch すると `<Destroy>` の結線ごと消え、
検査が空振りする。task_02 で実際に空振りした）。

観測は次の 2 つだけを使う:

- **カウンタ実測** — `self.app.hook.get_hook_pause_count()`
- **`start_hook` の patch** — OS フック登録と `messagebox` の同期表示を避けるため
  （`hook_controller.py` の `start_hook` を Mock 化し呼び出し回数を数える）

**各テストはダイアログ生成前に `self.app.update()` を回してカウンタ 0 を確認してから始める**
（クラス内で `self.app` を共有するため、先行テストの `after(0)` 予約が未実行のまま溜まる。
task_02 で 2 件 fail した原因）。

固定する項目（受け入れ条件との対応を明記する）:

| # | 条件 | 内容 |
|---|---|---|
| T1 | §7-1 | **× 閉じで解除される** — `protocol` 未登録の代表 2 クラス（`PresetManagerDialog` / `ActionDialog`）を実生成し `dialog.tk.call("destroy", str(dialog))` で Tcl レベル破棄 → `self.app.update()` 後に **カウンタ 0**。**破棄直後（`update()` 前）は 1 のまま**であることも同じテストで固定する（§4-2 の遅延が仕様であることの明示） |
| T2 | §7-2 | **解除がちょうど 1 回** — 同 2 クラスで **OK / キャンセル / プログラム破棄（`dialog.destroy()`）/ × 閉じ**の各経路について、`resume_hook_after_dialog` を **`wraps` 付き patch** で数え **1 回**。**Escape は結線している 3 クラスのうち代表 1 つ**（`QuarantineManageDialog`）で見る |
| T3 | §7-3 | **子ウィジェットの破棄では走らない** — 実ダイアログの子ウィジェットを 1 つ `destroy()` → `self.app.update()` 後も**カウンタ 1 のまま**（ダイアログは生存） |
| T4a | §7-4 | **終了時（ダイアログ経路）にフックが再開しない** — ダイアログを開いた状態で `self.app.hook.begin_shutdown()` → ダイアログ破棄 → `update()`。**`hook_coordinator.start` が 0 回・`hook_active` が False・カウンタ 0**（下記「終了ガードの観測点」を必ず読む） |
| T4b | §7-4 | **終了時（try/finally 経路）にフックが再開しない** — `child_save_dialog` の `ask_child_save_actions`（`:22-29` の `suspend → wait_window → finally: resume` 形）を実行し、**`wait_window` 中に `begin_shutdown()` を立ててからダイアログを破棄**する（`after` でスケジュールする）。`finally` の**同期解除**を通して **`hook_coordinator.start` が 0 回・`hook_active` が False・カウンタ 0** |
| T5 | §7-8 | **phase 14 の非退行** — **suspend / resume を patch しない実結線のまま**、`PresetManagerDialog` の上に `PresetDialog` を開き**子を Tcl レベルで破棄** → `update()` 後に **grab が親（manager）へ戻る** かつ **カウンタが親の分の 1 に戻る**。既存 `test_nested_modal_grab.py:425` は suspend を patch した状態の検査なので**観点が異なり重複しない** |
| T6 | §7-5 / §7-6 | **静的検査（下記 2. の限定つき）** |

いずれも `hook_was_active_before_dialog` を経路に乗せるため、**`hook_active = True` を仕込む**
（`addCleanup` で元へ戻す）。T1 / T2 / T3 / T5 は `start_hook` を patch してよい。

**【終了ガードの観測点】T4a / T4b で `start_hook` を patch して「呼び出し 0 回」を見てはいけない。**
task_01 の実装は**ガードを `start_hook` の中**に置いており（`hook_controller.py:91-92`）、
`resume_hook_after_dialog`（`:54-55`）は終了中でも `start_hook()` を**呼ぶ**（呼ばれた側が即 return する）。
これは暫定仕様 §4-3「ガードが立っている間 `start_hook()` は何もしない」に沿った実装であり、
**受け入れ条件 §7-4 が禁じているのは「フックが実際に再開すること」**である。
したがって T4a / T4b は **`start_hook` を patch せず**、`hook_coordinator.start` の未呼び出しと
`hook_active` が False のままであることで見る。**先例は
`tests_ui/test_hook_controller_teardown.py:116-135`**（task_01 の同趣旨のテスト）。

### 2. 静的検査（`tests_ui/test_dialog_teardown_flows.py` 内・AST）

**対象は `keyseq/presentation/dialogs/` の 8 クラスに限定する**（`preset_dialog.py` は対象外）。
`test_nested_modal_grab.py:234-308` の `is_call` / `ast.parse` の書き方を流用する。

1. **§7-5**: 8 ファイルそれぞれで `suspend_hook_for_dialog` の呼び出しが **1 件**、かつ
   **位置引数が `self` の 1 個だけ**（`ast.Name` の `id == "self"`）。
2. **§7-6**: 8 ファイル全体で `resume_hook_after_dialog` の呼び出しが **0 件**。

- **`keyseq/presentation/controllers/` は検査対象に含めない** — phase 14 の既存静的検査
  （`test_nested_modal_grab.py:300-303`）が `finally: resume_hook_after_dialog` を**要求している**ため、
  対象を限定しないと**正面衝突する**（暫定仕様 §5）。
- **`def destroy` の件数固定（4 件のみ）のような追加検査は入れない** — 暫定仕様 §5 が挙げる
  **上記 2 点に限定する**（過剰実装の防止）。

### 3. 既存テストの書き換え（1 件のみ）

`tests_ui/test_app_ui_flows.py:1325-1341`
`test_preset_manager_cancel_keeps_runtime_and_dirty_unchanged`。

- **現状の問題**: task_02 で `PresetManagerDialog.destroy` の override を削除したため、
  `PresetManagerDialog.destroy(dialog)` が `tk.Toplevel.destroy` の patch に解決し
  **pass のまま検証内容が空**になっている（暫定仕様 §6-2）。
- **移設先**: `object.__new__` + `destroy` 直呼びをやめ、**`PresetManagerDialog(self.app)` を実生成して
  `dialog.destroy()`** し、`self.app.update()` の後に
  **`save_hotkey_presets` 未呼び出し / `dirty_tracker.set_dirty` 未呼び出し / `self.app.data` 不変**
  を見る（＝「キャンセル（閉じるだけ）では保存も dirty も走らない」の観測点）。
- **`resume_hook_after_dialog` の patch は外す**（フック再開の検証は上記 1. の新規テストが持つ）。
- **テスト名は変えない**。`addCleanup` で確実に破棄する。

**上記以外の既存テストは触らない**。task_02 で観測点を移した分
（`test_orphan_sweep_flow.py` / `test_quarantine_manage_flow.py` / `test_app_ui_flows.py:1936-1952`）は
**そのまま**。

## 設計メモ / 制約

- **`after(0)` は `update_idletasks()` では実行されない**。必ず `update()` を回す（暫定仕様 §4-2）。
- **suspend / resume を patch した検査は空振りする**。カウンタ実測か `wraps` 付き patch を使う。
- **`start_hook` は T1 / T2 / T3 / T5 でのみ patch する** — 実呼び出しは
  `validate_hook_configuration` 経由で `messagebox.showerror` を同期表示し得る（暫定仕様 §1-⑥）。
  **T4a / T4b では patch しない**（ガードが立っているため即 return し、副作用は起きない）。
  観測点は上記「終了ガードの観測点」。
- **production コードを直さない** — テストが落ちた場合、原因が task_01 / task_02 の実装にあるなら
  **報告して判断を仰ぐ**（本タスクで production を書き換えて通さない）。
- **やってはいけないこと**: `keyseq/` 配下の変更 / `controllers/` を静的検査の対象に含めること /
  既存テストの広範な書き換え / ダイアログ同型スケルトンの共通化 /
  静的検査の発見ベース化（phase 14 の `deep-reviewer` M-6・保留中）。

## 含まない

- **統合確認（`tests` / `tests_ui` 全体 + `smoke_app`）・二次レビュー・実機目視** → **task_04**。
- **正本反映・暫定仕様 13 の凍結・`/refactor_check`** → **task_05**。
- **production コードの変更**（`keyseq/` 配下は本タスクで不変）。
- 非ダイアログ経路 5 系統の結線方式の変更（暫定仕様 §9）。
- `key_capture.py` / `keyboard_window.py` の編集モード（暫定仕様 §9）。

## 確認

python は必ずリポジトリルートの `.venv`（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier` へ委任する**（Codex は python を実行できない）。

1. **静的確認**: `python -m compileall -q keyseq main.py tests tests_ui` が clean。
2. **新規テストが pass**: `python -m unittest tests_ui.test_dialog_teardown_flows`。
   T1 / T2 / T3 / T4a / T4b / T5 / 静的検査 2 点がすべて含まれていること。
3. **書き換えたテストが pass**:
   `python -m unittest tests_ui.test_app_ui_flows.<クラス名>.test_preset_manager_cancel_keeps_runtime_and_dirty_unchanged`。
4. **変異検査 3 件**（各々 1 つだけ壊し、**確認後は必ず元へ戻す**）:
   - `hook_controller.py` の `event.widget is window` 判定を外す → **T3 が fail**。
   - `hook_controller.py:91-92` の終了ガードの分岐を外す → **T4a / T4b が fail**
     （`hook_coordinator.start` が呼ばれるようになる）。
   - `dialogs/` の任意 1 クラスの `suspend_hook_for_dialog(self)` から `self` を外す →
     **静的検査 1 が fail**。
   - 3 件とも戻したうえで **`git diff keyseq/` が空**であることを再確認する。
5. **既存テストが pass**:
   - `python -m unittest discover -s tests` = pass 417（skip 7・増減なし）。
   - `python -m unittest discover -s tests_ui` = **311 + 新規分**が pass（既存の件数は減らない）。
   - `python -m tests.smoke_app` が pass。
6. **production 無変更の確認**: `git diff --stat` に `keyseq/` が**現れない**
   （変更は `tests_ui/` の 2 ファイルのみ）。
7. テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されていないこと。

## 完了条件

- 上記「確認」1〜7 がすべて pass。
- **`reviewer` 採用**（CLAUDE.md「レビュー（必須）」）。観点は `.claude/rules/review.md` の 5 観点 +
  phase.md「レビュー方針」の固有観点のうち本タスクに効くもの（**静的検査の対象限定**＝
  `controllers/` の try/finally 形を巻き込んでいないか / **phase 14 との干渉**＝既存 grab テストと
  観点が重複・衝突していないか / **スコープ逸脱**＝production コードを触っていないか）。
- **実機目視は本タスクでは行わない**（task_04 でまとめて実施）。
