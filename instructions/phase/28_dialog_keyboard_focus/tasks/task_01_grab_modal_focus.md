# task_01_grab_modal_focus

## 目的

モーダルダイアログの初期キーボードフォーカスを設定する責務を `modal.grab_modal` へ集約する
（暫定仕様 22 §3.1・§3.2）。あわせて、既にフォーカスを明示している 7 経路（群 A・A'）を
**新しい引数へ移し替える**（二重指定を残さない。§3.2）。

- **presentation 限定**。domain / application・データスキーマは**不変**。
- 本タスクの変更だけで**群 B の 3 ダイアログ（`orphan_sweep` / `quarantine_manage` /
  `reference_cleanup`）の欠落は解消する**（引数省略 = 窓自身へ入るため）。
  ただし**その確認テストは task_02**。

## 対象範囲（presentation + tests_ui 限定）

### 1. `keyseq/presentation/modal.py`

- `grab_modal` の署名を **`def grab_modal(window, parent=None, *, focus=None) -> None:`** にする
  （`focus` は**キーワード専用**）。
- **`window.grab_set()` の直後**にフォーカスを適用する。適用は
  **`_apply_initial_focus(window, focus)` という独立した関数**へ切り出す
  （`grab_modal` は既に 56 行で実装目安 30 行を超えているため。§3.2）。
- `_apply_initial_focus` の振る舞い:
  - `focus` が `None` なら **`window` 自身**へ、指定があれば**その widget** へ `focus_set()` する。
  - **`tk.TclError` のみ握る**（破棄中の窓に当たる場合）。**`KeyError` は握らない**
    （`grab_current()` と違い `_nametowidget` による解決を伴わないため）。
    **`AttributeError` は握らない**（偽 Toplevel の不足を隠すため）。
    握る理由をコメントで残す（`modal.py` 既存の防御コメントと同じ形）。
- **早期 return する経路ではフォーカスを触らない**
  （`previous is window` / `_custody_window is window` の二重呼び出し経路。§3.2）。
- **`focus_force()` / `lift()` は呼ばない**（§3.1-4）。
- docstring に「フォーカスもここで面倒を見る（省略時は窓自身）」を 1 行加える。

### 2. 群 A の 6 経路（`focus_set` を引数へ移す）

いずれも **`focus_set()` の行を削除し、`grab_modal` の `focus=` へ渡す**。移動先の widget は現状と同じ。

| ファイル | 現状 | 変更後 |
|---|---|---|
| `dialogs/action_dialog.py:129,131` | `self.value_entry.focus_set()` → `self._sync_capture_ui()` → `grab_modal(self, parent)` | `self._sync_capture_ui()` → `grab_modal(self, parent, focus=self.value_entry)` |
| `dialogs/keymap_edit_dialog.py:53,54` | `self.label_entry.focus_set()` → `grab_modal(self, parent)` | `grab_modal(self, parent, focus=self.label_entry)` |
| `dialogs/keymap_set_history_dialog.py:31,32` | `self.tree.focus_set()` → `grab_modal(self, parent)` | `grab_modal(self, parent, focus=self.tree)` |
| `dialogs/keymap_set_history_dialog.py:214,215` | `self.listbox.focus_set()` → `grab_modal(self, parent)` | `grab_modal(self, parent, focus=self.listbox)` |
| `dialogs/preset_dialog.py:39,40` | `self.value_entry.focus_set()` → `grab_modal(self, parent)` | `grab_modal(self, parent, focus=self.value_entry)` |
| `dialogs/trigger_dialog.py:52,53` | `self.key_entry.focus_set()` → `grab_modal(self, parent)` | `grab_modal(self, parent, focus=self.key_entry)` |

- **`__init__` の外にある `focus_set` は触らない**（`action_dialog.py:275`・`:378`、
  `keymap_edit_dialog.py:82`、`trigger_dialog.py:79`。`grab_modal` と無関係）。
- `keymap_set_history_dialog.py:30` の「フォーカスを移さないと Escape が親（App）へ届き…」コメントは、
  責務が `modal.py` へ移るため**削除する**（誤読を招くため）。

### 3. 群 A'（`controllers/config_io/child_save_dialog.py`）

- `_create_dependency_dialog`（`:249`〜）の戻り値を **`(dialog, save_as_button)` のタプル**に変える
  （Toplevel へ属性を生やす形は採らない。§3.2）。`:284` の `save_as_button.focus_set()` は削除する。
- 呼び出し側（`:219`〜 の `confirm_trigger_set_dependency`）で
  `dialog, focus_widget = self._create_dependency_dialog(...)` と受け、
  `:243` を **`grab_modal(dialog, self._app, focus=focus_widget)`** にする。

### 4. 偽 Toplevel への `focus_set` 追加（テスト側）

実物の `grab_modal` を通す偽クラスに **`focus_set(self)` を追加**する（無いと `AttributeError` で落ちる）。

- `tests_ui/test_child_save_dialog.py:149` の `_FakeSaveDialog`
- `tests_ui/test_config_io_characterization.py:65` の `_FakeDialog`

呼ばれたことを記録できる形にする（既存クラスの `call_log` / `_bindings` と同じ流儀に合わせる）。

### 5. 決定論的な単体テスト（`tests_ui/test_modal_grab.py` へ追加）

**実 Tk の Toplevel に対し `focus_set` を `patch.object` で差し替えて呼び出しを記録する**
（`focus_get()` を使わない = アプリの OS フォーカス状態に依存しない。§5）。追加する項目:

1. `focus` 省略時に **`window.focus_set()` がちょうど 1 回**呼ばれる。
2. `focus=<子 widget>` 指定時に **その子の `focus_set()` がちょうど 1 回**呼ばれ、
   **`window.focus_set()` は呼ばれない**。
3. **二重呼び出し（同じ窓へ 2 回 `grab_modal`）では 2 回目に `focus_set` を呼ばない**。
4. **最小化中の預かり経路（`_custody_window is window`）でも `focus_set` を呼ばない**。
5. **`focus_force` / `lift` を呼ばない**（`patch.object` で両方を見張る。§3.1-4）。

### 設計メモ / 制約

- **推測型（`focus_lastfor()` を読む / `after_idle` で判定する）は採らない**。
  未マップの Toplevel への `focus_set` は Tk 内で保留され、`focus_lastfor()` / `focus_get()` から
  **検出できない**ことを実測済（暫定仕様 §1.2）。推測型は群 A の初期フォーカスを奪う。
- `_sync_capture_ui()` が `value_entry` を `state="disabled"` にする経路があるが、
  **`disabled` 化と `focus_set` の前後関係はフォーカス先を変えない**ことを実測済（§1.2 条件 11・12）。
  そのため `action_dialog` の移動順（`_sync_capture_ui` の後に `grab_modal`）で問題ない。
- **`grab_modal` は `__init__` の最後の文のまま**にする（静的検査
  `tests_ui/test_nested_modal_grab.py:260` が固定している）。引数を足すだけで位置は変えない。
- 既存の grab 復元・預かりのロジック（`restore_grab` / `_custody_window` / `<Destroy>` 結線）は
  **一切変更しない**。

## 読むファイル

- `instructions/history/22_dialog_keyboard_focus.md` の **§1.1 / §1.2 / §3.1 / §3.2 / §3.4 / §5**
  （設計の根拠。他の節は読まなくてよい）
- `keyseq/presentation/modal.py:65-120`（`grab_modal` 全体。編集対象）
- `keyseq/presentation/dialogs/action_dialog.py:126-132` / `keymap_edit_dialog.py:50-55` /
  `keymap_set_history_dialog.py:26-33` と `:210-216` / `preset_dialog.py:36-41` /
  `trigger_dialog.py:49-54`（移動対象の前後のみ）
- `keyseq/presentation/controllers/config_io/child_save_dialog.py:219-248` と `:278-287`
  （呼び出し側とビルダの末尾）
- `tests_ui/test_modal_grab.py:1-50`（`setUp` / `make_window` の手本。テスト追加先）
- `tests_ui/test_child_save_dialog.py:149-175` / `tests_ui/test_config_io_characterization.py:65-100`
  （偽クラスの書き方）
- `tests_ui/test_nested_modal_grab.py:260-302`（壊してはいけない静的検査）

## 含まない

- **群 B の 3 ダイアログの確認テスト・群 A/A' の実 Tk 回帰確認**（task_02）。
  本タスクは**決定論的な単体テストのみ**。
- **群 C の 5 経路への Escape 追加**（task_03）。本タスクでは `bind("<Escape>")` を足さない。
- **idea_18 の診断・Escape ヘルパ・既存 Escape テストの移行**（task_04）。
  既存テストの `focus_force()` は**この時点では外さない**。
- **統合確認・負荷下の再現確認・実機目視**（task_05）。
- **正本 `features.md` / `codebase_map.md` の更新**（task_06。フェーズ中は正本を触らない）。
- `preset_manager.py` / `layout_delete_dialog.py` / `io_dialogs.py` / `hotkey_presets_io.py` /
  `child_save_dialog.py:26`（群 C）への**引数追加はしない**（省略呼び出しのままでよい）。

## 確認

`.venv` の python を使う（`..\..\..\.venv\Scripts\python.exe`）。

1. `python -m compileall -q keyseq` が clean。
2. `python -m unittest discover -s tests` が全 pass（件数を前回 556 と比較）。
3. `python -m unittest discover -s tests_ui` が全 pass
   （前回 484。本タスクの追加分だけ増えること）。
4. `tests_ui/test_nested_modal_grab.py::NestedModalGrabTest::test_grab_modal_is_last_initialization_statement`
   が **pass**（暫定仕様 §8-5）。
5. 新規単体テスト 5 項目（対象範囲 5 の 1〜5）がすべて pass。
6. `python -m tests.smoke_app` が `SMOKE OK`。
7. **変更前後で `grab_modal` の呼び出しが 15 箇所のまま**であること
   （`grep -rn "grab_modal(" keyseq/ --include=*.py | grep -v "def grab_modal" | wc -l` = 15）。

## 完了条件

- 上記確認 1〜7 が pass（実測は `verifier` が行う。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（重点観点 = 既存の初期フォーカス先を壊していないか / 早期 return 経路を
  触っていないか / 後続タスクの先取りがないか）。
- **実機目視は本タスクでは行わない**（task_05 でまとめて実施）。
