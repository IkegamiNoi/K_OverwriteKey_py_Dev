# task_01_click_selection_sync

## 目的

トリガー一覧・シーケンス一覧・キーマップ一覧で、1 回のクリックで選択と下線（アクティブ行）がクリックした行へ揃って移るようにする（phase.md「確定」）。presentation のみ。

## 対象範囲

- `keyseq/presentation/listbox_utils.py`: 同期処理に「選択を正とする」経路を加える（例: `sync_listbox_selection_to_focus(..., prefer_selection: bool = False)`。
  True なら `curselection()` の先頭を正とし、選択を整えて `activate` で下線をそこへ合わせる。選択が無ければ従来の判定へ落とす）。`focused_listbox_index` の既定の振る舞いは変えない。
- クリックとキー操作の判別（指摘 1）: 3 つの一覧のバインド（`views/full_view/{trigger_box,sequence_box,keymap_box}.py`・`views/compact_view/trigger_box.py`）で
  `<<ListboxSelect>>` と `<KeyRelease>` を別の入口へ分ける（または同じハンドラへ判別できる引数を渡す）。`<<ListboxSelect>>` → 選択を正 / `<KeyRelease>` → 従来どおり下線を正。
  - トリガー一覧: `trigger_panel_controller.on_trigger_list_focus_index_change`（両イベントが同じハンドラ）。
  - シーケンス一覧: `on_action_list_select`（`<<ListboxSelect>>`）/ `on_action_list_focus_index_change`（`<KeyRelease>` → `on_action_list_select`）。
  - キーマップ一覧: `keymap_panel_controller.on_keymap_list_select` / `on_keymap_list_focus_index_change`。
- **守ること（指摘 2）**: シーケンス一覧の `_programmatic_action_select` の抑止と、「同じ行なら何もしない」（位置が実際に変わったときだけ `reset_loop_frames`・phase 37 統合レビュー H1 の再発防止）を変えない。
  トリガーの選択 index・シーケンスの実行位置・アクティブなキーマップの更新は、揃った行で従来どおり行う。

## テスト（追加・修正まで。実行は依頼しない）

- `tests_ui/` に、3 つの一覧それぞれで: 一覧にフォーカスがあり下線が行 A にある状態から、行 B をクリックしたときの実際の順序
  （`<1>` 相当 = `selection_clear`/`selection_set(B)` → `event_generate("<<ListboxSelect>>")` → `<ButtonRelease-1>` 相当 = `activate(B)`。または Tk のクラスバインドを `event_generate("<Button-1>", x=, y=)` 等で実際に通す）で、
  **1 回目で選択と下線が B に揃い、アプリ側の状態（選択 index / 実行位置 / アクティブなキーマップ）も B になる**。修正前のコードでは選択が A に戻って落ちる形にする。
- キー操作の同期（下線を正とする）が従来どおりであることを確かめるテスト（既存があれば流用）。
- 既存の `tests_ui/test_sequence_control_review_fixes.py` は `trigger_module.sync_listbox_selection_to_focus` を patch している。シグネチャを変えたら追随させる（テストの意図は変えない）。
- App を作る新規テストは既存の tests_ui の流儀（`setUpClass` で共有・`addCleanup` で戻す・実 `config/` を汚さない）に従う。

## 読むファイル

- phase.md の「このフェーズで読むファイル」1〜6

## 含まない

- `focused_listbox_index` の他の呼び出し（`action_edit.py:46`・`keymap_panel_controller.py:63`）/ ダイアログ内の Listbox / 文書（メイン）
