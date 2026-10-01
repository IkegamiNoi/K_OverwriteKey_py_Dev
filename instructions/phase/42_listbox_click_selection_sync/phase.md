# phase.md

## フェーズ名

一覧のクリックで選択と下線がずれる不具合の修正（listbox_click_selection_sync）

## フェーズの目的

トリガー一覧・シーケンス一覧・キーマップ一覧で、1 回のクリックで選択（フォーカスの帯）と下線（Listbox のアクティブ行）がクリックした行へ揃って移るようにする。
**対象は presentation のみ（`listbox_utils.py` と 3 つの一覧のハンドラ）。JSON スキーマ変更なし・仕様変更なし（正本の記述への影響なし）。**

- 起票元: ユーザー要望（2026-10-02）。「一度のクリックでは下線だけ移動し、フォーカス（選択）が移動しないことがある」。
- 原因（裏取り済み・Tk 8.6 の Listbox のクラスバインド）: `<1>` の `tk::ListboxBeginSelect` が選択をクリックした行へ移して `<<ListboxSelect>>` を発生させ、
  下線（active）は `<ButtonRelease-1>` の `%W activate @%x,%y` で後から移る。
  `keyseq/presentation/listbox_utils.py` の `sync_listbox_selection_to_focus`（→ `focused_listbox_index`）は一覧にフォーカスがあると **active 行を正**とするため、
  `<<ListboxSelect>>` の時点ではまだ古い下線の行へ選択を戻してしまう。離した時点で下線だけクリックした行へ移る。2 回目のクリックでは下線が既にその行にあるので揃う。
  同期処理はキーボード操作で選択と下線を揃えるために入れたもの（2026-06-21 `5208447`）。
- 主入力（暫定仕様）: なし（直接改訂モード・正本の改訂なし）。
- モード: **直接改訂モード**。番号対応: phase 42 / 暫定なし / decisions 42。

## 確定（ユーザー 2026-10-02）

- **クリック（`<<ListboxSelect>>`）では、選択された行を正として下線をそこへ合わせる**。
- **キー操作（`<KeyRelease>`）では、従来どおり下線の行を正とする**（2026-06-21 の同期の意図を保つ）。
- 対象はトリガー一覧（フル / 省略表示の両方）・シーケンス一覧・キーマップ一覧。

## スコープ

### 含む

- `keyseq/presentation/listbox_utils.py` の同期処理（きっかけで正とする行を選べるようにする）
- 3 つの一覧のハンドラ: `controllers/trigger_panel/trigger_panel_controller.py`（`on_trigger_list_focus_index_change` / `on_action_list_select` / `on_action_list_focus_index_change`）・
  `controllers/keymap_panel/keymap_panel_controller.py`（`on_keymap_list_select` / `on_keymap_list_focus_index_change`）と、そのバインド（`views/full_view/{trigger_box,sequence_box,keymap_box}.py`・`views/compact_view/trigger_box.py`）
- テスト（`<1>` → `<<ListboxSelect>>` → `<ButtonRelease-1>` の順で、フォーカスがある一覧の 1 回目のクリックで選択と下線が揃う / キー操作の同期は従来どおり）

### 含まない（後送り）

- 編集対象を決める `focused_listbox_index` の他の呼び出し（`action_edit.py:46`・`keymap_panel_controller.py:63`）の変更（揃えば従来どおり正しく働くため）
- ダイアログ内の Listbox（同期処理を使っていない）

## このフェーズで読むファイル

1. `keyseq/presentation/listbox_utils.py`
2. `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`（`on_trigger_list_focus_index_change`・`on_action_list_select`・`on_action_list_focus_index_change`）
3. `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`（`on_keymap_list_select`・`on_keymap_list_focus_index_change`）
4. バインド: `keyseq/presentation/views/full_view/{trigger_box,sequence_box,keymap_box}.py`・`views/compact_view/trigger_box.py`
5. `instructions/common/codebase_map.md` の「出力シーケンスの制御アクション」節（`<KeyRelease>` は `on_action_list_select` へ流れる・同じ行なら何もしない）
6. 既存テスト: `tests_ui/test_sequence_control_review_fixes.py`（同期処理を patch している）

## タスク

タスク定義（`tasks/task_NN_<topic>.md`）は着手時に `/task_new` で順に起票する。

- task_01（**完了** 2026-10-02。reviewer 完了可・実機目視 OK）: 実装（`listbox_utils.py` と 3 つの一覧のハンドラ・バインド）・テスト・実機目視（3 つの一覧で 1 回のクリックで選択と下線が揃う / 矢印キー・Tab での同期は従来どおり）
- task_01a: 完了判定前レビューの修正（押している間は帯だけ・離したときに選択へ下線を合わせて反映）・再度の実機目視 — **完了**（2026-10-02。reviewer 完了可・実機目視 OK）
- task_02（**完了** 2026-10-02。完了判定前レビュー = deep-reviewer 完了可 / Codex 敵対的 needs-attention → task_01a・`/refactor_check` 不要）: 締め（`codebase_map.md`・`decisions_archive/42_listbox_click_selection_sync.md`・current.md の完了記載・`/refactor_check`）

## レビュー方針

- クリックとキー操作の両方の経路で、選択・下線・アプリ側の選択状態（トリガーの選択 index・シーケンスの実行位置・アクティブなキーマップ）が揃うか。
- シーケンス一覧の「同じ行なら何もしない」（phase 37 統合レビュー H1 の再発防止）を壊さないか。`_programmatic_action_select` の抑止との関係。
- テストは Tk の実際のクラスバインドの順序（`<1>` → `<<ListboxSelect>>` → `<ButtonRelease-1>`）を再現し、修正前のコードで落ちる形にする（検出力）。
