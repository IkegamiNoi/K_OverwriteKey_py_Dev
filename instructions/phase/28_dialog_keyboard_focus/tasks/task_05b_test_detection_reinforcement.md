# task_05b_test_detection_reinforcement

## 目的

task_05 の統合レビュー（`deep-reviewer`）で指摘された**テストの検出力不足 2 件**を補強する
（暫定仕様 22 **§8-13**）。

- **tests_ui 限定。production（`keyseq/`）を変更しない**。
- 既存アサートを**弱めない・削らない**（追加と置き換えのみ）。
- レイヤ制約: テストのみ。domain / application / データスキーマ不変。

## 背景（裏取り済みの事実。2026-09-23・メインが `ファイルパス:行` で実測確認）

- **M1**: 群 A のうち `KeymapSetHistoryDialog`（`tree`）と `CategoryChooserDialog`（`listbox`）は
  初期フォーカスの検査が `tests_ui/test_keymap_set_history_flow.py:143` / `:149` の
  `assertTrue(str(dialog.focus_get()).startswith(str(dialog)))` **のみ**で、
  「**ダイアログ内**」までしか見ていない。task_01 以降は `focus` 省略時でも**窓自身**へ
  フォーカスが入るため、**`focus=self.tree` / `focus=self.listbox` を落としても緑のまま**になる
  （= 検出力ゼロ。§5 が `focus_lastfor()` を却下した「トートロジー」と同じ構造）。
  `tests_ui/test_dialog_initial_focus.py` は action / keymap_edit / preset / trigger の
  4 経路しか widget 同一性を見ていない。
- **M3**: 群 C の 5 経路の Escape は**結線済みハンドラの直呼び**で固定されている
  （`tests_ui/test_dialog_escape_binding.py:63` の `self.handlers[dialog](None)` /
  `test_child_save_dialog.py:370` / `test_config_io_characterization.py:392`）。
  **実 `<Escape>` キーの配送は未検証**。task_03 時点の見送り理由は「idea_18 の flaky family を
  診断前に増やさない」だったが、**task_04 で `tests_ui/escape_delivery.py` の `send_escape` が入り
  前提が解消済み**。

## 対象範囲（tests_ui 限定）

### 1. M1 — 群 A の 2 経路へ widget 同一性の検査を追加

`tests_ui/test_dialog_initial_focus.py` へテストを **2 件追加**する（既存 7 件は変更しない）。

| 追加する検査 | 期待 |
|---|---|
| `KeymapSetHistoryDialog` の初期フォーカス | `assertIs(app.focus_get(), dialog.tree)` |
| `CategoryChooserDialog` の初期フォーカス | `assertIs(app.focus_get(), chooser.listbox)` |

- **既存の `_require_app_focus()` の skip ガードを必ず使う**（同ファイルの他テストと同じ形）。
- 属性名（`tree` / `listbox`）は実装を読んで確認する
  （`keyseq/presentation/dialogs/keymap_set_history_dialog.py:31` / `:214` 付近の
  `grab_modal(..., focus=...)` に渡している式が正）。
- `CategoryChooserDialog` は**履歴ダイアログを親として生成する**
  （手本 = `tests_ui/test_keymap_set_history_flow.py:146-149`）。
- **`tests_ui/test_keymap_set_history_flow.py:143` / `:149` の既存 `startswith` 判定は削除しない**
  （そのテストは「Escape が親へ抜けない」の再発防止として別の意味を持つ）。

### 2. M3 — 群 C の実 Toplevel 2 件を実配送へ格上げ

`tests_ui/test_dialog_escape_binding.py` の次の 2 テストで、
`_close_with_escape_handler`（ハンドラ直呼び）を **`send_escape` による実配送**へ置き換える。

| テスト | 対象クラス |
|---|---|
| `test_layout_delete_escape_destroys_and_resumes_hook` | `LayoutDeleteDialog` |
| `test_preset_manager_escape_discards_edits_and_resumes_hook` | `PresetManagerDialog` |

- **既存アサートはすべて残す**（`dialog.result is None` / `app.data` 不変 /
  `get_hook_pause_count()` の 1 → 0 / `assertFalse(dialog.winfo_exists())`）。
- **`assertTrue(dialog.bind("<Escape>"))`（結線の存在確認）も残す**。
- `destroy` の `assert_called_once_with()` は実配送では成立しない場合がある。
  **`destroy` の呼び出し回数ではなく「破棄されたこと」と「フック解除がちょうど 1 回」で固定する**
  （`resume` の `assert_called_once_with()` 相当が既にあればそれを使う）。
- **フック再開は `<Destroy>` から `after(0)` で予約される**ため、数える前に `self.app.update()` を
  流す既存の作法を維持する（`test_dialog_escape_binding.py:68-70` のコメント参照）。
- **実 Toplevel でない 3 件（`io_dialogs` / `hotkey_presets_io` / `child_save_dialog`）は
  ハンドラ直呼びのまま**にする（偽 Toplevel のため実配送できない）。

### 設計メモ / 制約

- **production を変更しない**。変更が必要と判断したら**実装せずに報告する**。
- `send_escape` は `tests_ui/escape_delivery.py` の既存ヘルパをそのまま使う（**改変しない**）。
- 新規テストで `focus_force()` を**ダイアログへ**当てない（初期フォーカスの欠落を隠すため）。
  `_require_app_focus()` が App へ当てるのは既存の形なのでそのまま使う。
- `test_dialog_escape_binding.py` の `setUp` にある `tk.Misc.bind` の差し替え
  （`:50` 付近の `capture_bind`）は**触らない**。

## 読むファイル

- `instructions/history/22_dialog_keyboard_focus.md` の **§5 / §8-13**
- `tests_ui/test_dialog_initial_focus.py`（全体。追加先と `_require_app_focus` の形）
- `tests_ui/test_dialog_escape_binding.py`（全体。置き換え対象 2 件と `_close_with_escape_handler`）
- `tests_ui/escape_delivery.py`（`send_escape` の引数と失敗時の挙動。**読むだけ**）
- `tests_ui/test_keymap_set_history_flow.py:137-150`（`CategoryChooserDialog` の生成手順の手本）
- `keyseq/presentation/dialogs/keymap_set_history_dialog.py:25-35` / `:205-216`
  （`focus=` に渡している widget の確認。**読むだけ**）

## 含まない

- **production（`keyseq/`）の変更**。
- **群 A の 4 経路への Escape 追加**（= task_05c）。
- 偽 Toplevel を使う 3 件の実配送化（実現不可）。
- `tests_ui/escape_delivery.py` の改修（`deep-reviewer` の M2 = 確保ループの実時間待ち）。
  **別途ユーザー判断待ちのため本タスクでは触らない**。
- `test_dialog_teardown_flows.py` の `after(0)` 取りこぼし対策（別 family・ユーザー判断待ち）。
- 正本 `instructions/common/` の更新（task_06）。
- 実機目視（実装完了後にまとめて 1 回・§2.2-10）。

## 確認

`.venv` の python を使う（`..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

1. `python -m compileall -q keyseq` が clean。
2. **変異検査（M1 の検出力の証明）**: `keyseq/presentation/dialogs/keymap_set_history_dialog.py` の
   `grab_modal(..., focus=self.tree)` の `focus` 引数を**一時的に外すと追加した検査が赤になる**ことを
   確認し、**確認後に必ず元へ戻す**（`git diff keyseq/` が空に戻ることを確認する）。
   `listbox` 側も同様に 1 回行う。
3. `python -m unittest discover -s tests_ui` が全 pass（**504 前後へ増加**・skipped は環境依存）。
4. `python -m unittest discover -s tests` が全 pass（556・skipped 7 から不変）。
5. 置き換えた 2 テストを**単独で 5 回ずつ**実行して全 pass。
6. `git diff --stat keyseq/` が**空**。
7. `python -m tests.smoke_app` が `SMOKE OK`。

## 完了条件

- 確認 1〜7 が pass（実測は `verifier`。**Codex に python 実行を依頼しない**）。
- **確認 2（変異検査）で赤になること**を確認できている。赤にならなければ検出力が無いので**未完了**。
- **`reviewer` 採用**（重点観点 = 既存アサートを弱めていないか / production 無変更か /
  skip で緑にしていないか）。
- **実機目視は本タスクでは行わない**（実装完了後にまとめて 1 回）。
