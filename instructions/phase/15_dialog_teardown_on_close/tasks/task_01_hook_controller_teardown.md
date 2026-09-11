# task_01_hook_controller_teardown

## 目的

`HookController` に **①ウィンドウ破棄時の自動解除**と **②アプリ終了ガード**を実装する。
暫定仕様 [13](../../../history/13_dialog_teardown_on_close.md)（v0.4）の §4-1 / §4-2 / §4-3 が根拠。

**presentation 限定。domain / application / infrastructure は不変。スキーマ不変。**
**`dialogs/` はまだ触らない**（task_02 の担当）。本タスクは
**`window` 省略時の挙動が現行と完全に同じであること**を先に固めるのが目的。

## 対象範囲（presentation 限定・2 ファイル）

### 1. `keyseq/presentation/controllers/hook_controller.py`

**(a) `suspend_hook_for_dialog` に `window` 引数を足す**

```python
def suspend_hook_for_dialog(self, window=None) -> None:
    """編集系ダイアログ表示中の誤爆を防ぐため、フックを一時停止（ネスト対応）。

    window を渡すと、その破棄時に自動で解除する（閉じ方によらず走る）。
    """
```

- **`window` 省略時は現行と 1 行も挙動が変わらないこと**（既存の try/finally 形 5 系統が
  引数なしで呼んでいる。`io_dialogs.py:35` / `child_save_dialog.py:22`・`:234`・`:301` /
  `keymap_panel_controller.py:173`）。
- `window` を渡したときだけ、**解除の予約**を行う（下記 (b)）。

**(b) 解除の予約（`<Destroy>` 結線 + `after(0)` 遅延）**

- `window.bind("<Destroy>", handler, "+")` で結線する。**第 3 引数 `"+"` は必須**
  （`keyseq/presentation/modal.py:46` の `grab_modal` を潰さないため。phase 14 の成果）。
- ハンドラは **`event.widget is window` でなければ何もしない**
  （`<Destroy>` は**子ウィジェットの破棄でも発火する**）。
- **解除は 1 度だけ**（`modal.py` の `restored` フラグと同型のガードを持つ）。
- **ハンドラの中で `resume_hook_after_dialog()` を直接呼ばない**。
  **`after(0)` で予約し、実行はイベントループへ回す**（§4-2）。
  理由は ①`start_hook()` が**同期で `messagebox.showerror` を開き得る**
  （`hook_controller.py:168`・`:183`・`:185`）ため破棄処理の途中で入れ子のモーダルを回さない
  ②**`grab_modal` の復元処理と同一イベント内で競合させない**（phase 14 の保証を守る）。
- **`after` は破棄されるウィンドウに対して呼ばない**（破棄済みでは使えない）。
  `self._app`（App）に対して呼ぶ。

**(c) 終了ガード**

- **アプリ終了が確定したことを記録する入口**を 1 つ足す（例: `begin_shutdown()`）。
- **ガードが立っている間 `start_hook()` は何もしない**。
  **`resume_hook_after_dialog` のカウンタ計算は従来どおり行い、再開だけを抑止する**
  （カウンタの整合を壊さないため）。
- **同期解除・遅延解除の両方に効く**こと（try/finally 形の 5 系統にも効く。§4-3）。

### 2. `keyseq/presentation/app.py`

`on_close`（`:527-539`）で **`self.destroy()` より前**に終了ガードを立てる。
`confirm_save_if_dirty` を通過した後に置く（**キャンセルされたら立てない**）。

### 3. `tests_ui/`（ヘルパ単体のテスト）

新規ファイルまたは既存への追記は実装者判断。**次の 5 点を実 `Toplevel` で固定する**:

1. **`window` を渡して破棄すると解除される** — `update()` を回した後にカウンタが 0 に戻る。
2. **`window` 省略時は自動解除されない**（従来どおり呼び出し側が `resume` する）。
3. **子ウィジェットの破棄では解除されない**（`event.widget` 判定）。
4. **同じウィンドウを 2 回破棄相当にしても解除は 1 度だけ**（多重解除でカウンタが負にならない）。
5. **終了ガードが立っていると `start_hook()` が呼ばれない**（カウンタは 0 に戻る）。

`tests_ui/test_modal_grab.py` の書き方（`make_window` / `addCleanup` / `report_callback_exception`
の監視）を流用する。**`update_idletasks()` + viewable アサート**の作法も同じ（phase 14 の罠）。

### 設計メモ / 制約

**`after(0)` の検証方法**
`after(0)` は**イベントループが回るまで実行されない**。テストでは `app.update()` を呼ぶ。
`update_idletasks()` では `after` は実行されない点に注意する。

**カウンタの整合**
`resume_hook_after_dialog` は `hook_suspend_count <= 0` のとき**何もせず 0 へ丸める**
（`hook_controller.py:34-36`）。多重解除でも負にはならないが、
**別のダイアログ分を過剰に decrement しないよう「1 度だけ」ガードは必須**。

**phase 14 との干渉**
`grab_modal` は `__init__` の最後で `<Destroy>` を `"+"` 結線する。
本タスクの結線は `suspend` 側（初期化の冒頭）なので**登録順は本タスクが先**になる。
`after(0)` 遅延により**実行順は grab 復元が先**になる。**この順序を壊さないこと**。

**やってはいけないこと**
- `dialogs/` の変更（**task_02**）。
- `resume_hook_after_dialog` / `start_hook` の既存ロジックの作り替え
  （**足すのはガードの分岐だけ**）。
- 既存の try/finally 形 5 系統の変更。
- `modal.py` の変更。

## 含まない

- **`dialogs/` の 8 クラスへの適用**（`suspend_hook_for_dialog(self)` 置換 /
  `destroy()` override からの resume 削除 / 空 override の削除）→ **task_02**。
- **受け入れ条件のテスト全般**（× 閉じ / 二重実行なし / 終了時 / phase 14 非退行 /
  静的検査）→ **task_03**。本タスクは**ヘルパ単体の 5 点のみ**。
- **既存テストの書き換え**（`test_app_ui_flows.py:1325-1341`）→ **task_03**。
- **統合確認・実機目視** → task_04。**正本反映** → task_05。

## 確認

python は必ずリポジトリルートの `.venv`（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier` へ委任する**（Codex は python を実行できない）。

1. **静的確認**: `python -m compileall -q keyseq main.py tests tests_ui` が clean。
2. **新規テストが pass**（上記 5 点）。
3. **既存テストが据え置き**:
   - `python -m unittest discover -s tests` = pass 417（skip 7）。
   - `python -m unittest discover -s tests_ui` = **pass 306 + 新規分**。
   - `python -m tests.smoke_app` が pass。
4. **`dialogs/` 無変更の確認**: `git diff --stat keyseq/presentation/dialogs/` が**空**であること。
5. **`window` 省略時の非変更**: `grep -rn "suspend_hook_for_dialog" keyseq/` の結果が
   **引数なし呼び出しのまま 5 系統 + dialogs 8 クラス**であること（本タスクでは呼び出し側を変えない）。
6. **変異検査**: `event.widget is window` の判定を外すと**子ウィジェット破棄のテストが fail** すること。
   **確認後は必ず元へ戻し、`git diff keyseq/` が意図した差分だけであることを再確認する**。
7. テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されていないこと。

## 完了条件

- 上記「確認」1〜7 がすべて pass。
- **`reviewer` 採用**（CLAUDE.md「レビュー（必須）」）。観点は `.claude/rules/review.md` の 5 観点 +
  phase.md「レビュー方針」の固有観点（二重実行 / `event.widget` 判定 / phase 14 との干渉 /
  終了ガードの網羅 / `window` 省略時の非変更）。
- **実機目視は本タスクでは行わない**（task_04 でまとめて実施）。
