# task_02_initial_focus_checks

## 目的

task_01 で入れた初期フォーカスを**実 Tk で検査する**（暫定仕様 22 §5 の「従」）。
①群 B の 3 ダイアログの欠落が解消したこと ②群 A・A' の初期フォーカス先が従来どおりであること
（§8-1・§8-2）を固定する。

- **tests_ui 限定。production コードは一切変更しない**（`keyseq/` 配下に差分を出さない）。
- **`focus_get()` 依存の検査は環境依存**（アプリが OS の入力フォーカスを失うと `None` を返す。
  §1.2 実測 3）。そのため**必ず skip ガードを付ける**（§2.1-7）。

## 対象範囲（tests_ui 限定）

### 1. 新規 `tests_ui/test_dialog_initial_focus.py`

初期フォーカスの実 Tk 検査を**この 1 ファイルへ集約**する（環境依存の検査を散らさない）。

- **App の生成**: `tests_ui/test_keymap_set_history_flow.py:17-34` の `ExitStack` 手法を**そのまま踏襲**する
  （`JsonRepository.save_json` / `ConfigService.ensure_split_config_dirs` /
  `load_keymap_set_history` / `save_keymap_set_history` を塞ぎ、**実 `config/` へ書かせない**）。
  `setUpClass` で 1 つだけ作り、`tearDownClass` で `update()` → `destroy()`。
- **skip ガード**: ヘルパ `_require_app_focus()` を用意し、
  **`self.app.focus_displayof() is None` なら `self.skipTest(...)`**（理由文に
  「アプリが OS の入力フォーカスを取れないため初期フォーカスを検査できない」旨を書く）。
  **各テストの冒頭で必ず呼ぶ**。
- **判定ヘルパ** `_assert_focus_inside(dialog)`:
  `self.app.update()` の後に `str(self.app.focus_get()).startswith(str(dialog))` を検査する
  （手本 = `tests_ui/test_keymap_set_history_flow.py:141-143`）。
  **`focus_lastfor()` は使わない**（修正前も真になるトートロジーのため。§5）。
- **後始末**: 各ダイアログを `addCleanup` で `grab_release()` → `destroy()` → `app.update()`
  （手本 = `tests_ui/test_action_dialog_drag.py:34-38`）。
- **フック**: 群 B は `__init__` で `suspend_hook_for_dialog` を呼ぶため、
  `self.app.hook` の `suspend_hook_for_dialog` / `resume_hook_after_dialog` を patch する。

検査項目:

| # | 対象 | 期待 |
|---|---|---|
| 1 | `OrphanSweepDialog(app, scan_dirs=(), initial_dir="")` | **窓自身**（`app.focus_get() is dialog`） |
| 2 | `QuarantineManageDialog(app, lines=(), unit_ids=())` | **窓自身** |
| 3 | `ReferenceCleanupDialog(...)` | **窓自身** |
| 4 | `ActionDialog` を **`type` = hotkey / text / mouse_click の 3 モード**で生成 | 3 モードとも `dialog.value_entry` |
| 5 | `KeymapEditDialog(app, title="...")` | `dialog.label_entry` |
| 6 | `PresetDialog(app, title="...")` | `dialog.value_entry` |
| 7 | `TriggerDialog(app, title="...")` | `dialog.key_entry` |

- 1〜3 は**修正の確認**（task_01 前なら失敗する検査であること）。4〜7 は**回帰確認**。
- 4 は `subTest(mode=...)` で 3 モードを回す。生成は
  `ActionDialog(self.app, title="...", initial={"type": <mode>, ...})`
  （手本 = `tests_ui/test_action_dialog_drag.py:40-45`）。
  **`mouse_click` では `value_entry` が `state="disabled"` になるが、フォーカス先は変わらない**
  （暫定仕様 §1.2 実測 11・12）。
- 3 の生成引数は `tests_ui/test_orphan_sweep_flow.py:439`、
  1 の生成引数は同 `:481`、2 は `tests_ui/test_quarantine_manage_flow.py:266` を手本にする
  （既存の呼び出し形をそのまま流用し、新しい引数を発明しない）。

### 2. `tests_ui/test_child_save_dialog.py` へ群 A' の到達確認を 1 件追加

この経路は既存テストが**偽 widget**（`_FakeSaveDialog` / `_FakeDialogWidget`）で回すため、
実 Tk ではなく**引数の到達**を固定する。

- 既存ハーネス `_ask_dependency_internally`（`:364`）を使い、
  **`child_save_dialog_module.grab_modal` を patch** して、
  **`focus=` に「別名保存」ボタンの widget が渡っていること**を検査する
  （ビルダの戻り値が呼び出し側まで届いていることの固定）。

### 3. 追加しないもの（既に担保済み）

- `KeymapSetHistoryDialog` / `CategoryChooserDialog` は
  `tests_ui/test_keymap_set_history_flow.py:137`
  `test_keyboard_focus_moves_into_dialog_and_only_path_column_stretches` が既に担保している。
  **重複して書かない**。

### 設計メモ / 制約

- **この検査は「アプリが OS フォーカスを持つとき」だけ意味を持つ**（§3.1-1 の保証時点）。
  skip ガードを外したり、`focus_force()` で無理に取りにいったりしない
  （`focus_force` を使うと実使用の欠落を隠す。idea_26 の発端がそれ）。
- **新規ファイルの検査はすべて「生成直後」**で判定する。ボタン操作・Escape 送信はしない
  （Escape 経路は task_04 の担当）。

## 読むファイル

- `instructions/history/22_dialog_keyboard_focus.md` の **§5 / §8-1 / §8-2 / §8-8**
- `tests_ui/test_keymap_set_history_flow.py:1-45` と `:137-148`
  （App 生成ハーネスと焦点検査の手本）
- `tests_ui/test_action_dialog_drag.py:12-48`（App 共有・後始末・`ActionDialog` 生成の手本）
- `tests_ui/test_orphan_sweep_flow.py:435-445` と `:475-490`
  （`ReferenceCleanupDialog` / `OrphanSweepDialog` の生成引数）
- `tests_ui/test_quarantine_manage_flow.py:260-270`（`QuarantineManageDialog` の生成引数）
- `tests_ui/test_child_save_dialog.py:364-392`（`_ask_dependency_internally` ハーネス）
- `keyseq/presentation/dialogs/keymap_edit_dialog.py:17-55` / `preset_dialog.py:11-41` /
  `trigger_dialog.py:17-54`（生成引数と初期フォーカス先の確認のみ）

## 含まない

- **群 C の 5 経路への Escape 追加**（task_03）。
- **idea_18 の診断・Escape ヘルパ・既存 Escape テストの移行・`focus_force()` の除去**（task_04）。
  既存テストには**手を入れない**（`test_dialog_teardown_flows.py` /
  `test_orphan_sweep_flow.py` / `test_quarantine_manage_flow.py` の既存メソッドは触らない）。
- **production コードの変更**（`keyseq/` 配下に差分を出さない）。
- 正本 `instructions/common/` の更新（task_06）。
- 統合確認・負荷下の再現確認・実機目視（task_05）。

## 確認

`.venv` の python を使う（`..\..\..\.venv\Scripts\python.exe`）。

1. `python -m compileall -q keyseq` が clean。
2. `python -m unittest discover -s tests` が全 pass（556 から不変）。
3. `python -m unittest discover -s tests_ui` が全 pass（前回 489。追加分だけ増えること）。
4. `python -m unittest tests_ui.test_dialog_initial_focus -v` で
   **新規テストの内訳（名前と ok / skip）を列挙**する。
5. **skip が発生した件数を報告する**（暫定仕様 §8-8。0 件なら 0 件と明記）。
6. `git diff --stat keyseq/` が**空**であること（production 無変更の確認）。
7. `python -m tests.smoke_app` が `SMOKE OK`。

## 完了条件

- 上記確認 1〜7 が pass（実測は `verifier`。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（重点観点 = skip ガードが機能する形か / `focus_force` に頼っていないか /
  既存テストを壊す変更が混ざっていないか / 検査が生成直後に限定されているか）。
- **skip 件数を完了報告に記載する**。
- **実機目視は本タスクでは行わない**（task_05 でまとめて実施）。
