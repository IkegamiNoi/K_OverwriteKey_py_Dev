# task_03_nested_modal_tests

## 目的

暫定仕様 [12](../../../history/12_nested_modal_grab_restore.md) §1 の**ネスト経路 3 系統**について、
**実 `Toplevel` を使った回帰テスト**を `tests_ui/` へ追加する。
task_01 / task_02 で入れた `grab_modal` が「子を閉じたら親へ grab が戻る」ことを、
ヘルパ単体ではなく**実際のダイアログ経路**で固定するのが目的（暫定仕様 §5）。

**テストの追加のみ。production コード（`keyseq/` 配下）は 1 行も変更しない。**
挙動が仕様どおりでないと分かった場合は、production を直さずユーザーへ報告して停止する。

## 対象範囲（`tests_ui/` の新規 1 ファイルのみ）

### `tests_ui/test_nested_modal_grab.py`（新規）

`App` を 1 つ生成して 3 経路を通す。クラス構成は
`tests_ui/test_quarantine_manage_flow.py:24-31` の `setUpClass` / `tearDownClass` に倣う
（`cls.app = App()` → `cls.app.update_idletasks()` / `tearDownClass` で `cls.app.destroy()`）。
**`AppUiFlowsTest` へは追加しない**（App 共有による dirty の混線を避けるため新規ファイルにする）。

追加するテスト（3 本 + × 閉じ 1 本 = **計 4 本**）:

1. **経路 1: プリセット編集 → 追加/編集**
   実 `PresetManagerDialog(self.app)` を生成し、`dialog.add()` を呼ぶ。
   `PresetDialog` は `preset_manager.add()` の内部で生成される（`preset_manager.py:282`）ため、
   **`PresetDialog.__init__` を patch して生成直後に `self.after(0, self.destroy)` を仕込む**
   （暫定仕様 §5 が手法まで固定している）。確認点:
   - 子が生きている間: `grab_current()` が **`PresetDialog` インスタンス**であること。
   - `add()` から戻った後: `grab_current()` が **`PresetManagerDialog` インスタンス**へ戻ること。
   `edit()` 側は経路が同じ（同じ `PresetDialog`）なので**テストを増やさない**。

2. **経路 2: アクション編集 → プリセット編集**
   実 `ActionDialog(self.app, title=...)` を生成し、`_open_preset_manager()`
   （`action_dialog.py:340-342`）を呼ぶ。`PresetManagerDialog.__init__` を同じ手法で patch する。
   確認点は経路 1 と同型（子が生きている間は子 / 戻ったら `ActionDialog` へ復帰）。
   `_open_preset_manager` は戻りに `_rebuild_preset_buttons()` を呼ぶので、
   **例外なく最後まで通ること**も確認する。

3. **経路 3: プリセット編集 → 上書き確認（最重要）**
   実 `PresetManagerDialog` から `on_ok()` を呼び、
   `hotkey_presets_io.confirm_overwrite`（`controllers/config_io/hotkey_presets_io.py:42`）が
   開く実 `Toplevel` を**上書きを承諾せずに閉じる**。確認点:
   - 確認ダイアログが生きている間: `grab_current()` が**確認ダイアログ**であること。
   - キャンセルで閉じた後: `grab_current()` が **`PresetManagerDialog` へ戻り、
     マネージャが破棄されていない**こと（`winfo_exists()` が真）。
     `save_hotkey_presets` が `False` を返すため `on_ok` はマネージャを閉じない
     （`preset_manager.py:375-380`）。**ここが本フェーズの本命**。

4. **× 閉じ 1 本**（暫定仕様 §5「× 閉じを 1 本」）
   経路 1 または 3 のいずれかで、`destroy()` 直呼びではなく
   **`protocol("WM_DELETE_WINDOW")` に登録されたハンドラ経由**（無い場合は `destroy()` を
   ウィンドウマネージャ相当の経路として扱う）で閉じ、同じく親へ復帰することを確認する。
   加えて、**親が先に破棄済みのケースで `TclError` にならない**ことを 1 アサート含める。

### 設計メモ / 制約

**経路 3 の前提づくり**
`on_ok()` から `confirm_overwrite` に到達するには
`app.save_hotkey_presets` が「個別プリセット + 上書き衝突あり」の分岐へ入る必要がある
（`app.py:434-460`）。実ファイル I/O を増やさずに、
`config_service.describe_individual_hotkey_presets_overwrite` を
`patch.object` で `{"conflict": True, "existing": [...]}` を返すよう差し替え、
`resolve_hotkey_presets_save_path` / `individual_hotkey_presets_save_rejection_reason` も
必要な値へ固定する。**`_temp` などの内部状態を直接組み立てず、
`PresetManagerDialog` を実インスタンス化して `individual_var` を True にする**。

**確認ダイアログの閉じ方**
`confirm_overwrite` は `dialog.wait_window()` でブロックする（`hotkey_presets_io.py:83`）。
`tk.Toplevel` 全体を patch せず、**`app.after(0, ...)` で「開いた確認ダイアログを探して閉じる」
コールバックを仕掛ける**か、`grab_modal` 呼び出し後に発火するタイミングで
`self.app.winfo_children()` から `Toplevel` を特定して `destroy()` する形にする。
どちらでも良いが、**`wait_window` を no-op に patch して経路を短絡させない**
（実際にブロック → 閉じる、を通すことがこのテストの価値）。

**アサートの書き方**
`grab_current()` の観測は `tests_ui/test_quarantine_manage_flow.py:286`
（`self.assertEqual(dialog.grab_current(), dialog)`）が先例。
**`assertIs` / `assertEqual` でインスタンス同一性を見る**こと。文字列比較にしない。

**フック制御の扱い**
各ダイアログの `__init__` / `destroy` は `suspend_hook_for_dialog` /
`resume_hook_after_dialog` を呼ぶ。既存テストと同様に `patch.object(self.app.hook, ...)` で
潰してよい（`tests_ui/test_app_ui_flows.py:1369-1372` が先例）。

**`messagebox` のガード**
保存経路の例外は `messagebox.showerror` になり、テストでは**モーダルで永久ブロックする**。
`tests_ui` の既存 4 ファイルと同じ **fail-fast ガード**（`showerror` / `askyesno` に
`side_effect` で `AssertionError` を出す patch）を `setUp` に置くこと
（`tests_ui/test_app_ui_flows.py:20-27`・`:56-68` が先例）。

**後始末**
各テストの最後に、開いたままのダイアログを `addCleanup` で確実に破棄する
（`tests_ui/test_modal_grab.py:26-32` の `cleanup_window` が先例）。
テスト間に grab が残ると後続テストが不可解に落ちる。

**やってはいけないこと**
- `keyseq/` 配下の production コードの変更（**1 行も変えない**）。
- `wait_window` / `grab_set` / `grab_current` を no-op へ patch して経路を短絡させること。
- `tk.Toplevel` そのものを差し替えるスタブの新規導入（実 `Toplevel` で見るのが本タスクの目的）。
- 契約 3 条（初期化失敗 / 非 LIFO 終了 / コールバック例外）のテスト追加（**task_04**）。

## `_FakeSaveDialog` の拡張要否（phase.md タスク 3 の判断事項）

**結論: 追加の拡張は不要**（task_01 で対応済み）。根拠:

- task_01 で `tests_ui/test_child_save_dialog.py:149` の `_FakeSaveDialog` と
  `tests_ui/test_config_io_characterization.py:66` の `_FakeDialog` の**両方**へ
  `grab_current` / `bind` を追加済みで、`tests_ui` 295 件が green。
- 本タスクの 3 経路は `PresetDialog` / `PresetManagerDialog` / `ActionDialog` /
  `confirm_overwrite` の実 `Toplevel` を通り、**上記スタブを 1 つも経由しない**。

実装時にこの結論が誤りだと分かった場合（スタブに属性不足で落ちる等）は、
**その場で拡張してよいが、拡張した内容を完了報告に明記する**。

## 含まない

- **契約 3 条のテスト**（初期化失敗 §3-6 / 非 LIFO 終了 §3-7 / コールバック例外 §3-8）→ **task_04**。
  ヘルパ単体レベルの非 LIFO / 冪等は task_01 の `tests_ui/test_modal_grab.py` に既にある。
- **統合確認（全スイート再実行）と実機目視**（stdlib ダイアログ 4 経路）→ **task_05**。
- **正本反映・暫定仕様の凍結・`/refactor_check`** → **task_06**。
- production コードの修正全般。仕様どおりでない挙動を見つけたら**報告して停止**する
  （`.claude/rules/spec_change_workflow.md`）。

## 確認

python は必ずリポジトリルートの `.venv`（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier` へ委任する**（Codex は python を実行できない）。

1. **静的確認**: `python -m compileall -q keyseq main.py tests tests_ui` が clean。
2. **新規テストが pass**: `python -m unittest tests_ui.test_nested_modal_grab -v` で
   **4 本すべて pass**（skip なし）。
3. **既存テストが据え置き**:
   - `python -m unittest discover -s tests` = pass 417（skip 7）。
   - `python -m unittest discover -s tests_ui` = **pass 299**（既存 295 + 新規 4）。
   - `python -m tests.smoke_app` が pass。
4. **production 無変更の確認**: `git diff --stat keyseq/ main.py` が**空**であること。
5. **テストが実際に欠陥を検出することの確認**: `keyseq/presentation/modal.py` の
   `restore_grab` を一時的に無効化（`return` を先頭に挿入）すると
   **新規 4 本のうち少なくとも 3 本が fail** すること。**確認後は必ず元へ戻し、
   `git diff keyseq/` が空であることを再確認する**（この検証は `verifier` へ依頼する）。
6. テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されていないこと。

## 完了条件

- 上記「確認」1〜6 がすべて pass。
- **`reviewer` 採用**（CLAUDE.md「レビュー（必須）」）。観点は `.claude/rules/review.md` の 5 観点 +
  phase.md「レビュー方針」の固有観点（特に**復元条件の取り違え**を突けるテストになっているか、
  経路を短絡させた「通るだけのテスト」になっていないか）。
- **実機目視は本タスクでは行わない**（task_05 でまとめて実施）。
