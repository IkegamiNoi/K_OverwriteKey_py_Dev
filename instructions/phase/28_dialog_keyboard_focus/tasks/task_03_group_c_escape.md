# task_03_group_c_escape

## 目的

Escape を bind していない 5 経路（群 C）へ **Escape を結線**する（暫定仕様 22 §3.5・§2.1-3）。
**Escape は「閉じる（×）」と同じ経路へ結ぐ**（新しい閉じ方を作らない）。

- **presentation 限定**。domain / application・データスキーマは**不変**。
- task_01 で群 C にもフォーカスが入るようになったため、**この結線で実際に Escape が効く**ようになる。

## 対象範囲（presentation + tests_ui 限定）

### 1. Escape の結線（暫定仕様 §3.5 の表が正）

| # | ファイル:行（`grab_modal` の位置） | 現在の「閉じる」 | **Escape の結線先** |
|---|---|---|---|
| 1 | `controllers/config_io/child_save_dialog.py:26`（子ファイルの保存） | `:25` `WM_DELETE_WINDOW` → `dialog.destroy` | `dialog.destroy` |
| 2 | `controllers/config_io/hotkey_presets_io.py:87` | `:86` `WM_DELETE_WINDOW` → `dialog.destroy` | `dialog.destroy` |
| 3 | `controllers/config_io/io_dialogs.py:57` | `:56` `WM_DELETE_WINDOW` → **`on_cancel`** | **`on_cancel`**（`destroy` 直呼びにしない） |
| 4 | `dialogs/layout_delete_dialog.py:52` | **`WM_DELETE_WINDOW` ハンドラ無し**。「キャンセル」（`:46`）= `self.destroy` | `self.destroy` |
| 5 | `dialogs/preset_manager.py:79` | **`WM_DELETE_WINDOW` ハンドラ無し**。「キャンセル」（`:163`）= `self.destroy` | `self.destroy` |

- 書き方は既存 4 クラスに合わせる: `bind("<Escape>", lambda _event: <閉じる経路>)`
  （手本 = `dialogs/orphan_sweep_dialog.py:24`）。
- **`bind` は `grab_modal` の呼び出しより前に置く**
  （静的検査 `tests_ui/test_nested_modal_grab.py:260` が「`__init__` の最後は `grab_modal`」
  「config_io は `grab_modal` の直後が `wait_window`」を固定しているため）。
- **`WM_DELETE_WINDOW` ハンドラが無い 4・5 にハンドラを足さない**
  （× の挙動は Tk 既定のまま変えない。最小差分。暫定仕様 §3.5）。

### 2. テスト（結線と後始末の固定）

**新規に `event_generate("<Escape>")` を使うテストは書かない**。理由:
idea_18 の flaky family（`focus_force` + `event_generate` の形）を**診断前に増やさないため**
（暫定仕様 §6。実配送の確認は task_04 のヘルパ導入時にまとめて行う）。
代わりに **①結線の存在 ②結線先が「閉じる」と同一であること ③ハンドラを直接呼んだときの後始末**
を固定する。

- **1（子ファイルの保存）**: `tests_ui/test_child_save_dialog.py` の既存ハーネス
  `_ask_dialog_internally`（`:286`）を使い、偽ダイアログの `bindings` に `"<Escape>"` があり、
  **`protocols["WM_DELETE_WINDOW"]` と同じ閉じ方になる**ことを固定する。
- **3（io_dialogs）**: `tests_ui/test_config_io_characterization.py` の `_FakeDialog`（`:65`）経路で、
  **`"<Escape>"` の結線先が `WM_DELETE_WINDOW` の結線先（`on_cancel`）と同一**であることを固定し、
  呼んだときに `result["ok"]` が False のままであることを確認する。
- **2・4・5**: 新規 `tests_ui/test_dialog_escape_binding.py` にまとめる。
  - **4・5** は実 Toplevel を直接生成できる
    （`LayoutDeleteDialog(app, title="...", items=[("id", "name")])` /
    `PresetManagerDialog(app)`）。`dialog.bind("<Escape>")` が非空であることを確認し、
    **結線されたハンドラを直接呼んで**窓が破棄されることと、
    **フック停止カウンタが 0 に戻ること**（`app.hook.get_hook_pause_count()`）を固定する。
  - **2** は `wait_window` を挟むため、`hotkey_presets_io.grab_modal` を patch して
    **モーダル化の時点でダイアログを捕まえ**、`bind("<Escape>")` の存在を確認してから
    そのハンドラを呼んで閉じる（`wait_window` はそこで復帰する）。
    **`hotkey_presets_io` はフック停止をしていない**（`suspend_hook_for_dialog` の呼び出しが無い）ため、
    **フックのアサートはしない**。
  - App の生成は `tests_ui/test_keymap_set_history_flow.py:17-34` の ExitStack 手法を踏襲し、
    実 `config/` へ書かせないこと。

### 設計メモ / 制約

- **フック解除がちょうど 1 回**であることは `key_input.md` §7.2 の既存規定に乗るだけで、
  新しい仕組みは作らない。4・5 は `suspend_hook_for_dialog(self)`（ウィジェット連動・破棄で解除）、
  1・3 は `try/finally` で `wait_window` の後に解除する既存の形をそのまま使う。
- **Escape に「キャンセル」以外の意味を持たせない**（保存する・確定する等の分岐を足さない）。
  5 経路とも「保存せずに閉じる」で、× と同じ結果になる。
- 群 C の `grab_modal` 呼び出しに `focus=` を足さない（省略時 = 窓自身でよい。task_01 の設計どおり）。

## 読むファイル

- `instructions/history/22_dialog_keyboard_focus.md` の **§3.5 / §4 / §8-9**
- `keyseq/presentation/controllers/config_io/child_save_dialog.py:18-31` /
  `hotkey_presets_io.py:80-90` / `io_dialogs.py:30-62`（結線を足す前後のみ）
- `keyseq/presentation/dialogs/layout_delete_dialog.py:13-53` / `preset_manager.py:72-90` と `:158-165`
- `keyseq/presentation/dialogs/orphan_sweep_dialog.py:20-27`（既存 4 クラスの書き方の手本）
- `tests_ui/test_child_save_dialog.py:280-300`（`_ask_dialog_internally` ハーネス）と `:150-198`（偽クラス）
- `tests_ui/test_config_io_characterization.py:60-110`（`_FakeDialog`）
- `tests_ui/test_dialog_initial_focus.py:1-45`（App 生成ハーネスと後始末の手本。task_02 で追加）
- `tests_ui/test_nested_modal_grab.py:260-302`（壊してはいけない静的検査）

## 含まない

- **idea_18 の診断・Escape ヘルパ・既存 Escape テストの移行・`focus_force()` の除去**（task_04）。
  既存の Escape 依存テスト（`test_dialog_teardown_flows.py` / `test_orphan_sweep_flow.py` /
  `test_quarantine_manage_flow.py` / `test_keymap_set_history_flow.py`）には**手を入れない**。
- **`event_generate("<Escape>")` を使う新規テストの追加**（上記「テスト」節の理由）。
- 群 C への `WM_DELETE_WINDOW` ハンドラの追加（4・5）。
- `grab_modal` / `modal.py` の変更（task_01 で完了済み）。
- 正本 `instructions/common/` の更新（task_06。`features.md` への Escape 条項は昇格タスクで入れる）。
- 統合確認・負荷下の再現確認・実機目視（task_05）。

## 確認

`.venv` の python を使う（`..\..\..\.venv\Scripts\python.exe`）。

1. `python -m compileall -q keyseq` が clean。
2. `python -m unittest discover -s tests` が全 pass（556 から不変）。
3. `python -m unittest discover -s tests_ui` が全 pass（前回 497・skipped 0。追加分だけ増えること）。
4. `tests_ui/test_nested_modal_grab.py::NestedModalGrabTest::test_grab_modal_is_last_initialization_statement`
   が **pass**（bind を `grab_modal` より前に置けているかの検査）。
5. `python -m unittest tests_ui.test_dialog_escape_binding -v` で新規テストの内訳を列挙する。
6. `grep -rn '"<Escape>"' keyseq/presentation/ --include=*.py | wc -l` が **11**
   （既存 6 + 今回の 5）。
7. `python -m tests.smoke_app` が `SMOKE OK`。

## 完了条件

- 上記確認 1〜7 が pass（実測は `verifier`。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（重点観点 = Escape の結線先が × と同一か / `bind` が `grab_modal` より前か /
  Escape に新しい意味を持たせていないか / 既存テストを壊していないか）。
- **実機目視は本タスクでは行わない**（task_05 でまとめて実施）。
