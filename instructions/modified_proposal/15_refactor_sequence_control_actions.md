# 提案書 15: phase 37（出力シーケンスの制御アクション）のリファクタ

> 起票: 2026-09-27・phase 37 の `/refactor_check`（PHASE_BASE = `3dc6ee8`・対象 `keyseq/` 16 ファイル・+1813 / −78）。
> 状態: **ユーザー判断待ち**。**挙動不変**（表示文言・保存データ・エラーメッセージを変えない）。

## 判定の根拠

| 記号 | 該当 | 箇所 |
|---|---|---|
| M1 | ○ | `presentation/controllers/trigger_panel_controller.py` 732 行（+168）。アクション編集（`selected_action_index`〜`_counter_names`・約 180 行）が追加 / 編集の分岐・単独登録・ループの対で膨らんだ |
| M2 | ○ | `presentation/dialogs/action_control_fields.py` の `__init__` 84 行（新規） |
| M6 | ○ | `action_control_fields.py` が `domain/sequence_control.py` の定数（op 名・`system` / `file_line`・`utf-8` / `shift_jis`・`error` / `empty` / `wrap`）と同値を直書き。深さ上限の「9」がメッセージ 2 箇所で直値（`application/sequence_steps.py:108`・`trigger_panel_controller.py:564`） |
| M3 / M4 / M5 | × | M4 は新モジュールの結果型の生成（欄はすべて既定値付き）で非該当と判断 |

参考（非該当・記録のみ）: `application/sequence_runner.py` 359 行で先行処理の呼び出しが単発・連続に重複（完了判定前レビュー L-8）/ `action_executor.py` の `"file_line"` 直値は既存の `"hotkey"` 等と同じ書き方で揃っている。

## 項目

### 項目 0: 安全網の確認

- 対象領域のテスト: `tests_ui/test_trigger_panel_controller_action_edit.py`（追加位置・ループの対・移動・単独登録）/ `tests_ui/test_sequence_control_review_fixes.py`（位置変更・削除・改名の配線）/
  `tests_ui/test_action_dialog_control.py`（各操作の結果 dict・入力エラー・モード）/ `tests_ui/test_action_list_rendering.py`。
- 完了条件: 着手前に `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` と `-s tests` が全 pass であることを確認（2026-09-27 時点で 615 / 829 pass）。

### 項目 1: アクション編集を `controllers/trigger_panel/` の補助モジュールへ（M1）

- **対象**: `trigger_panel_controller.py:521-698`（`selected_action_index` / `add_action` / `edit_action` / `delete_action` / `move_action` / `_counter_names`）。
- **どう変えるか**（`file_organization_rules.md` の親フォルダ方式・phase 34 の `keymap_panel/` と同じ形）:
  ```
  controllers/trigger_panel/
      __init__.py                  # TriggerPanelController の再輸出
      trigger_panel_controller.py  # 本体（トリガー一覧・一覧の描画・状態表示・アクション編集は 1 行委譲）
      action_edit.py               # ActionEditFlow: 上記 6 メソッドの実体（messagebox / ActionDialog を import）
  ```
  本体の `add_action()` 等は `return self._action_edit.add_action()` の 1 行委譲として残す（`SequenceBox` のボタン・テストが `app.trigger_panel.add_action` を呼ぶため）。
- **テストの追随**: `tests_ui/test_trigger_panel_controller_action_edit.py` / `test_sequence_control_review_fixes.py` の `patch.object(controller_module, "ActionDialog")` と
  `messagebox` の patch 先を `action_edit` モジュールへ変える（挙動の期待値は変えない）。import パスは `__init__.py` の再輸出で `from ...controllers.trigger_panel import TriggerPanelController` に揃える。
- **完了条件**: `trigger_panel_controller.py` 600 行未満 / tests・tests_ui・smoke 全 pass（件数不変）。
- **リスクと戻し方**: patch 先の取りこぼしで UI テストが実ダイアログを開く → テストが落ちるので検出できる。戻しは 1 コミットの revert。
- **依存**: 項目 0。

### 項目 2: `ActionControlFields.__init__` の分割と定数の参照（M2・M6）

- **対象**: `presentation/dialogs/action_control_fields.py:9-21`（op 表・文字コード・範囲外の直値）/ `:28-111`（`__init__`）。
- **どう変えるか**: op 名・種別・文字コード・範囲外の値は `domain/sequence_control` の定数を参照する（日本語の表示名との対応表だけをこのファイルに置く）。
  `__init__` を入力欄のまとまりごとの組み立てメソッド（例: `_build_loop_fields` / `_build_counter_fields` / `_build_wait_fields` / `_build_file_line_fields`）へ分け、`__init__` は 30 行程度にする。
- あわせて、深さ上限の「9」を含むメッセージ 2 箇所（`sequence_steps.py:108`・`trigger_panel_controller.py:564`）を `MAX_LOOP_DEPTH` から組み立てる（文言は同一）。
- **完了条件**: `__init__` 40 行未満 / `grep -nE '"(loop_start|loop_end|counter_inc|counter_reset|wait|back|rewind|utf-8|shift_jis)"' keyseq/presentation/dialogs/action_control_fields.py` がヒットしない /
  tests・tests_ui・smoke 全 pass（件数不変・`test_action_dialog_control.py` の期待 dict 不変）。
- **リスクと戻し方**: 組み立て順が変わるとウィジェットの grid 位置がずれる → `test_action_dialog_control.py` と実機目視で確認。戻しは revert。
- **依存**: 項目 0（項目 1 とは独立）。

## 実施タイミング（ユーザー判断）

- (a) phase 37 末の追加タスク（`task_09_refactor`）として実施 / (b) 次フェーズ（idea_38 = file_line の非同期読込）の前の独立ミニフェーズ。
