# 提案書 18: phase 43（一覧のドラッグ移動・範囲選択・複製）後のリファクタ

> 状態: **未承認**（/refactor_check の判定 = 推奨・2026-10-04）。挙動不変。承認後に実施タイミング（同フェーズ末の task_10_refactor / 次フェーズ前のミニフェーズ）を選ぶ。

## 判定の要約

範囲 `git diff 4614585^..HEAD -- keyseq/`（34 ファイル・+2074 / -358）。メトリクスは verifier の実測。

- **M1 該当**: `presentation/controllers/trigger_panel/trigger_panel_controller.py` 734 行（+180）。phase 42 で「次に触るフェーズで分割を再判定」と別タスク化候補に記載済みのもの（今回が再判定の契機）
- **M2 該当**: `presentation/dialogs/keymap_switch_batch_dialog.py:21` `__init__` 107 行（新規）
- **M3 該当**: 「一覧の範囲 = 選択範囲か、無ければ下線の 1 行」を求める同型が 3 か所（`keymap_list_edit.py:24` `selection_bounds`・`trigger_list_edit.py:26` `selection_bounds`・`action_edit.py:322` `_selection_bounds`）
- M4・M5・M6: 該当なし
- 参考（非該当）: `keymap_set_io.py` 741 行（+40）・`app.py` 630 行（+2）は増分が基準未満

## 項目 0: 安全網の確認

- 対象領域のテスト: `tests_ui/test_trigger_list_operations.py`・`test_keymap_list_operations.py`・`test_sequence_list_operations.py`・`test_sequence_copy_paste.py`・`test_listbox_range_drag.py`・`test_preset_manager_range_drag.py`・`test_keymap_switch_batch_dialog.py`・`test_task06_keymap_management_ui.py`・`test_listbox_click_selection_sync.py`
- 完了条件: 着手前に `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` が全 pass（基準線）。不足があれば特性テストを先に足す

## 項目 1: `trigger_panel_controller.py` からトリガーの追加・改名・削除を切り出す（M1）

- 対象: `trigger_panel_controller.py:498-645`（`add_trigger` / `rename_trigger` / `_apply_trigger_rename` / `delete_trigger`・約 150 行）
- 変更: 同フォルダに `trigger_row_edit.py`（`TriggerRowEditFlow`）を新設して移し、コントローラは `_action_edit` / `_trigger_edit` と同じ遅延生成のプロパティから委譲する（数行ずつ）。
  公開メソッド名（`add_trigger` 等）はコントローラに残す（View・テストの呼び出し先を変えない）
  ```python
  # trigger_panel_controller.py
  def add_trigger(self):
      return self._trigger_row_edit.add_trigger()
  ```
- 完了条件: コントローラが 600 行未満・項目 0 のコマンドが全 pass
- リスクと戻し方: テストの patch 先がモジュール名を直接指していれば追随が要る（`grep -rn "trigger_panel_controller\.\(messagebox\|TriggerDialog\)" tests_ui`）。戻しは移動の取り消しのみ
- 依存: なし

## 項目 2: `KeymapSwitchBatchDialog.__init__` の分割（M2）

- 対象: `keymap_switch_batch_dialog.py:21-128`
- 変更: 行の生成（`for index, (kind, name, ...) in enumerate(rows)` の本体）を `_build_row(parent, index, row, single_row)`、スクロール領域の組み立てを `_build_rows_area(rows)`、
  ボタンとバインドを `_build_buttons()` へ切り出す。`__init__` は状態の初期化と 3 つの呼び出し・`grab_modal` だけにする（30 行目安）
- 完了条件: `__init__` が 40 行以下・`tests_ui/test_keymap_switch_batch_dialog.py` と項目 0 が全 pass
- リスクと戻し方: 属性（`key_entries` / `label_entries` / `_row_frames` / `_canvas`）の生成順を変えない。戻しは関数の展開のみ
- 依存: なし

## 項目 3: 「範囲か下線の 1 行」の取得を 1 つに（M3）

- 対象: `keymap_list_edit.py:24-31`・`trigger_list_edit.py:26-34`・`action_edit.py:322-`
- 変更: `presentation/listbox_range_drag.py` に純粋な取得関数を足し、3 か所はそれを呼ぶ
  ```python
  def range_or_index(listbox, length: int, fallback_index: int | None, *, compact: bool) -> tuple[int, int] | None:
      if listbox is not None and not compact:
          bounds = selected_range(listbox)
          if bounds is not None and 0 <= bounds[0] <= bounds[1] < length:
              return bounds
      return (fallback_index, fallback_index) if fallback_index is not None and 0 <= fallback_index < length else None
  ```
  （`action_edit.py` の現行の戻り値の形〔引数 `idx` を受ける〕が違えば、その差を呼び出し側に残して同じ関数を使う。合わなければ本項目は 2 か所だけにする）
- 完了条件: 3 か所（または 2 か所）が同じ関数を呼ぶ・項目 0 が全 pass
- リスクと戻し方: 省略表示（`_compact_mode`）の判定を落とさない。戻しは呼び出しの展開のみ
- 依存: なし
