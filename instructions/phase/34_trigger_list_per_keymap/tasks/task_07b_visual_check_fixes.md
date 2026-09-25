# task_07b_visual_check_fixes

## 目的

実機目視（ユーザー 2026-09-26）の指摘を反映する（暫定仕様 25 v0.5 の §2-21・§2-22・§8.1・§8.2・§8.5）。

1. 一時的な案内（連続実行中の切替不可・重複キーの案内）の表示先を、上部の「ステータス」枠（`ui_vars.status_var`）から
   **画面下のステータスバー中央の一時メッセージ領域（`app._set_flash_message`）** へ移す。
2. キーマップの**追加フローのダイアログは、切替キーが空・不正・重複の入力エラーで閉じない**（エラーを示して開いたまま入力し直せる。キャンセルでのみ中止）。

**presentation 限定・JSON スキーマ不変・判定ロジック（key_overlap / can_switch_keymap）は変えない**。

## 対象範囲

### 1. 表示先の変更

- `keymap_panel_controller.py`（`show_keymap_switch_blocked` 付近・`SWITCH_BLOCKED_MESSAGE`）: `status_var.set(...)` をやめ、`self._app._set_flash_message(...)` で出す（自動消去は既定どおり）。
- `hook_controller.py:219-249` 付近（§8.5 の重複案内・`_last_shadowed_status`）: 上部「ステータス」枠へ書く処理をやめ、`_set_flash_message` で出す。
  - **上位動作の表示を消さない**（§8.5）: 停止キーでフックが止まる場合、既存の停止時の一時メッセージ（あれば）と案内を**1 つの一時メッセージに併記**する（後から出した方で上書きして消さない）。
  - 同じ案内の連続蓄積防止など task_05 で入れた振る舞いは、一時メッセージ領域向けに保つ。
  - 上部「ステータス」枠の通常表示（フック・キーマップ状態）は task_07 の形のまま。案内のために書き換えない。
- 一覧の行のグレー表示と理由（`（停止キーと重複）` 等）は**変えない**（A 案・一覧に残す）。

### 2. 追加フローのダイアログを入力エラーで閉じない

- `keyseq/presentation/dialogs/keymap_edit_dialog.py`: 任意の検証コールバック（例: `validate: Callable[[dict], bool] | None = None`）を受け取り、
  OK 時に呼んで **False ならダイアログを閉じず** 入力欄へフォーカスを戻す（エラー表示は検証側の既存 messagebox でよい。ダイアログを親にして前面に出す）。
  コールバック未指定の既存の呼び出しは挙動不変。
- `keymap_panel_controller.py` の追加フロー（`add_keymap` / 個別読込の追加 / `_collect_missing_switch_edits` / `_prompt_keymap_edit` / `_validate_addition_key`）:
  - 追加ダイアログ・切替キー未設定の既存キーマップへの設定ダイアログの**両方**で、既存の検証（`_validate_addition_key` 相当）をダイアログの検証コールバックとして渡す。
    検証を通った入力だけが返る。**キャンセル（×・Esc・キャンセルボタン）のときだけ追加を中止**する。
  - reviewer 参考（task_06）の「`_prompt_keymap_edit` がタイトル文字列 `"キーマップ変更"` で分岐」を、明示の引数（bool 等）に置き換える（同じ関数を触るため）。

### テスト（追加・更新）

- 既存テストの期待値更新は表示先の変更（status_var → 一時メッセージ）・ダイアログを閉じない挙動によるもののみ。アサーションを緩めない。未モックの実ダイアログを開かない（messagebox は patch）。
- 新規 / 更新:
  1. 連続実行中の切替で `_set_flash_message` に案内が出て、上部「ステータス」枠（status_var）は案内で書き換わらない。
  2. 重複キーの案内が `_set_flash_message` に出る・停止時は停止の表示と併記される・一時停止中は出ない（task_05 の条件を維持）。
  3. KeymapEditDialog: 検証が False なら閉じない（result 未設定・ウィンドウ存在）・True なら閉じて result を返す・検証なしは従来どおり。
  4. 追加フロー: 空の切替キー → エラー後もダイアログが残り、正しいキーを入れ直すと追加される / キャンセルで中止。既存キーマップへの設定ダイアログも同様。

## 読むファイル

- `instructions/history/25_trigger_list_per_keymap.md` §2-21・§2-22・§8.1・§8.2・§8.5
- `keyseq/presentation/app.py:280-300`（`_set_flash_message`）/ `keyseq/presentation/views/status_bar.py`
- `keyseq/presentation/controllers/hook_controller.py:200-260` / `keymap_panel_controller.py:175-300, 410-425`
- `keyseq/presentation/dialogs/keymap_edit_dialog.py`（全体）
- 手本のテスト: `tests_ui/test_task06_keymap_management_ui.py` / `tests_ui/test_task05_overlap_ui.py`（該当テストのみ）

## 含まない

- 判定ロジックの変更 / 一覧のグレー表示・理由の変更 / 通常のキーマップ編集（追加フロー外）のダイアログ挙動の変更 / `instructions/` 配下の編集（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（skip 7 据え置き）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass（ハングしないこと）
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass
- `git grep -n "SWITCH_BLOCKED_MESSAGE\|_last_shadowed_status" -- keyseq` の箇所で status_var を書いていないこと

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視はユーザーが再確認（指摘 3 点のみ）。
