# task_08a_help_button_position

## 目的

task_08 の実機目視で出た 2 件を直す（暫定 53 §14・ユーザー確定 2026-10-29）。

1. ダイアログの「?」を、OK の左隣から**ダイアログ下端の左寄せ**へ移す（§14.1）
2. ヘルプ本文「用語」の注記の段落を、箇条書きの末尾の 1 項目にする（§14.2）

## 対象範囲

### 1. 「?」の位置（§14.1）

- `keyseq/presentation/help/help_button.py` `add_help_button`:
  - 「?」を、呼び出し時点で `row` に pack 済みの子（左側のボタン）の**後ろ**に `side="left"` で置く（今の `before=children[0]` をやめる）。
  - 続けて、`row` の中に横へ伸びる空き（`ttk.Frame` を `side="left", fill="x", expand=True`）を 1 つ pack する。
    これで、後から `side="left"` で pack される OK・キャンセル等は右端へ寄る（`side="right"` の列もそのまま右）。
  - docstring にこの前提（呼び出し後に pack するボタンは右寄せになる / `row` は横幅いっぱいに置く）を短く書く。
- §6.1 の 12 か所で、`add_help_button` に渡すボタン列を**横幅いっぱい**に置く:
  - grid の `sticky="e"` → `sticky="ew"`（列が足りなければ `column=0` から全列の `columnspan` にする）
  - pack の `anchor="e"` → `fill="x"`（`side="bottom"` 等の他の指定は維持）
  - 対象: `action_dialog.py`・`keymap_edit_dialog.py`・`trigger_dialog.py`・`preset_manager.py`・`preset_dialog.py`・
    `keymap_switch_batch_dialog.py`・`keymap_set_history_dialog.py`・`orphan_sweep_dialog.py`・`quarantine_manage_dialog.py`・
    `reference_cleanup_dialog.py`・`layout_delete_dialog.py`（以上 `dialogs/`）・`controllers/config_io/child_save_dialog.py`
- `action_dialog.py` のみ: 「プリセット編集…」（`self.preset_edit_btn`）をボタン列 `btns` の中へ移し、`add_help_button` より前に
  `side="left"` で pack する（並び: プリセット編集… / ? / 空き / OK / キャンセル）。`btns` は `column=0` から全列に広げる。
  `self.preset_edit_btn` の属性名・状態制御（有効 / 無効の切替）は不変。
  - **表示切替の対応（必須）**: 今は `_sync_type_visibility`（`action_dialog.py:485`）が `self._show(self.preset_edit_btn, ...)` で
    grid / grid_remove を呼ぶ（`_show` は `:506-510`）。pack へ移した後は grid を呼ぶと TclError になるため、このボタンだけ
    pack 用の切替にする（表示 = `pack(side="left", before=<「?」のボタン>)`・非表示 = `pack_forget()`。`add_help_button` の戻り値を属性に持つ）。
    hotkey 以外の種類では「?」が左端に来ること。
  - Tab 順は生成順で決まるため、「プリセット編集…」→「?」→ OK → キャンセルになる（生成順を変えない）。
- OK・キャンセル等のボタンの順・間隔・コマンドは変えない。

### 2. 「用語」の注記（§14.2）

- `keyseq/presentation/help/content/help_ja.json`: 「用語」の `list` の末尾に
  「キーを押す: 実際のキーボードのキーを押すことです。キーボードUIのキーをクリックすることではありません。」を追加し、直後の `p`（「このヘルプで「キーを押す」は、…」）を削除する。id 不変。
- 校正用の写し `instructions/phase/70_help_window/tools/help_ja_draft.md` も同じに揃える。

### テスト

- `tests_ui/test_dialog_help_buttons.py`（または近いテスト）に追加: 代表のダイアログで「?」が左寄せになっていること
  （例: 「?」の x 座標が OK ボタンより十分左 / アクションの追加・編集では「プリセット編集…」の右隣）。
- アクションの追加・編集: hotkey → 他の種類 → hotkey と切り替えて、「プリセット編集…」が隠れる / 「?」の左に戻る / 例外が出ないこと。
  初期の種類が hotkey 以外でも開けること。
- 既存テストが「?」の位置・`preset_edit_btn` の grid 情報・用語の段落に依存していれば追従する。

## 読むファイル

- `instructions/history/53_help_window.md` §6.1・§6.2・§14
- 上記の編集対象（該当箇所の前後のみ）・`tests_ui/test_dialog_help_buttons.py`・`tests_ui/test_action_dialog_control.py`

## 含まない

- タイトルバーへの「?」（§14.1 で不採用）・表記の変更・正本の更新（task_08）

## 確認

- `tests_ui.test_dialog_help_buttons`・`tests_ui.test_action_dialog_control`・`tests.test_help_content`・`tests_ui.test_help_window` pass（verifier）
- tests / tests_ui / smoke 全体 pass（verifier）
- 実機目視（ユーザー）: 12 か所のうち代表（トリガーの追加・編集 / アクションの追加・編集 / 未使用ファイルの整理）で「?」が左下にあり、
  OK・キャンセルは右のまま。ヘルプの「用語」で注記が箇条書きの末尾に揃っている

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: §14 どおりか / 12 か所の漏れ / ボタンの順・コマンド・Tab 順の変化が無いか / `preset_edit_btn` の状態制御を壊していないか）
