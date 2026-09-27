# task_09_refactor

## 目的

[提案書 15](../../../modified_proposal/15_refactor_sequence_control_actions.md) の項目 1・2 を実施する（ユーザー承認 2026-09-27・(a) phase 37 末の追加タスク）。
**挙動不変**（表示文言・保存データ・エラーメッセージ・ウィジェットの配置を変えない）。

## 対象範囲

### 項目 1: アクション編集を `controllers/trigger_panel/` へ（親フォルダ方式・phase 34 の `keymap_panel/` と同じ形）

- `keyseq/presentation/controllers/trigger_panel_controller.py` を `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py` へ移す（`git mv`）。
- `keyseq/presentation/controllers/trigger_panel/__init__.py`: `TriggerPanelController` の再輸出のみ（`keymap_panel/__init__.py` と同じ書き方）。
- `keyseq/presentation/controllers/trigger_panel/action_edit.py`（新規）: `ActionEditFlow`（名前は `keymap_add_flow.py` の `KeymapAddFlow` に倣う）に
  `selected_action_index` / `add_action` / `edit_action` / `delete_action` / `move_action` / `_counter_names` の実体を移す（`messagebox` / `ActionDialog` / `sequence_editing` の import もこちらへ）。
  本体の同名メソッドは `self._action_edit.<name>(...)` への 1 行委譲として残す（`SequenceBox` のボタン・他のコントローラ・テストが `app.trigger_panel.<name>` を呼ぶため）。
- import の更新: `keyseq/presentation/app.py` ほか `trigger_panel_controller` を import している箇所（`rg -n "trigger_panel_controller" keyseq tests tests_ui`）。
  **旧パスに横流しモジュールを残さない**（恒久互換レイヤー禁止）。
- テストの追随: `tests_ui/test_trigger_panel_controller_action_edit.py` / `tests_ui/test_sequence_control_review_fixes.py` / `tests_ui/test_action_list_rendering.py` の import と、
  `patch.object(<旧モジュール>, "ActionDialog")` / `messagebox` の patch 先を `action_edit` モジュールへ変える（期待値は変えない）。
  他のテストに `trigger_panel_controller` モジュールの patch があれば同様に直す。
- `instructions/common/codebase_map.md` の presentation のフォルダ構成と「出力シーケンスの制御アクション」節の該当パスを更新する。

### 項目 2: `ActionControlFields.__init__` の分割と定数の参照

- `keyseq/presentation/dialogs/action_control_fields.py`: op 名・種別・文字コード・範囲外の値は `keyseq.domain.sequence_control` の定数を参照する
  （日本語の表示名との対応表だけをこのファイルに置く）。`__init__` を入力欄のまとまりごとの組み立てメソッドへ分け、40 行未満にする。**grid の行・列・順序は変えない**。
- 深さ上限「9」を含むメッセージ 2 箇所（`keyseq/application/sequence_steps.py` の「ループの入れ子が 9 段を超えています」と、コントローラのループ追加拒否の文言）を
  `MAX_LOOP_DEPTH` から組み立てる（**文言は同一**）。

## 読むファイル

- `instructions/modified_proposal/15_refactor_sequence_control_actions.md`（提案書）
- `keyseq/presentation/controllers/trigger_panel_controller.py`（移動・編集対象・全体）
- `keyseq/presentation/controllers/keymap_panel/__init__.py` / `keymap_panel/keymap_add_flow.py:1-40`（手本の形）
- `keyseq/presentation/dialogs/action_control_fields.py`（編集対象・全体）/ `keyseq/domain/sequence_control.py`（定数のみ）
- `keyseq/application/sequence_steps.py` の該当メッセージ（`rg -n "9 段" keyseq`）
- 上記テスト 3 ファイル（import と patch の箇所のみ）

## 含まない

- 振る舞いの変更・文言の変更 / `sequence_runner.py` の重複（別タスク化候補）/ 正本 spec_detail の変更（パスの記載がある codebase_map のみ更新）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` がエラー無し。
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`（829・skip 7）・`-s tests_ui`（615）が**件数不変で全 pass**、`..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass。
- `wc -l keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py` が 600 未満。`keyseq/presentation/controllers/trigger_panel_controller.py` が存在しない。
- `grep -nE '"(loop_start|loop_end|counter_inc|counter_reset|wait|back|rewind|utf-8|shift_jis)"' keyseq/presentation/dialogs/action_control_fields.py` がヒットしない。

## 完了条件

- 上記確認 pass・**reviewer 採用**。実機目視: 追加ダイアログの system / file_line の入力欄の並びが変わっていないこと（ユーザー）。
