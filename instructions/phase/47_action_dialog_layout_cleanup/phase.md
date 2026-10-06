# phase.md

## フェーズ名

アクションの追加・編集ダイアログの整理（action_dialog_layout_cleanup）

## フェーズの目的

出力シーケンスの追加・編集ダイアログ（`ActionDialog`）で、選んだ種別で使わない項目をグレーのまま残さず**非表示**にし、「末尾に追加」を種別の行の右端へ移して目につきやすくする。
**presentation 限定（`dialogs/action_dialog.py`）・domain / application 不変・JSON スキーマ不変。**

- 起票元: ユーザー要望（2026-10-06・「使用しない項目をグレー表示で放置している」「末尾に追加が目につきづらく、カーソルの動線としてもいまいち」）。
- 主入力（暫定仕様）: なし（直接改訂モード）。正本 `features.md` §4.6「出力シーケンスの編集」を task_02 で改訂する。
- モード: **直接改訂モード**（presentation の 1 ダイアログ・正本 1 か所・タスク 2）。番号対応: phase 47 / 暫定なし / decisions 47。

## 確定（ユーザー 2026-10-06）

1. 使わない種別では次を**非表示**（`grid_remove`）にする。既存のマウス設定・system / file_line の欄と同じ方式
   - 値: hotkey / text だけ表示（mouse_click・system・file_line では非表示）
   - 「キー入力で記録」と説明文: hotkey だけ表示
   - 「OSショートカット（プリセット）」の枠と「プリセット編集…」: hotkey だけ表示
2. 「末尾に追加」は**種別のドロップダウンと同じ行の右端**へ移す（追加ダイアログのときだけ・既定 ON・挙動は不変）
3. 種別の切替でダイアログの高さが中身に合わせて伸び縮みし、OK の位置が動くのは**受容**（高さは固定しない）
4. 開いたときのフォーカスは値欄。値欄が無い種別（mouse_click・system・file_line の行の編集など）では**種別のドロップダウン**へ入れる。
   ただしループの行の編集（`edit_loop`・種別と操作が固定で選べない）は**ループ回数の欄**（「無限」にチェックがあれば「無限」のチェック）へ入れる（起票時の整合チェックで補った・メイン判断）

## スコープ

### 含む

- 上記 1〜4 の実装とテスト（種別ごとの表示・「末尾に追加」の位置・初期フォーカス）
- 既存テストの追随（必須は `tests_ui/test_dialog_initial_focus.py:94-105` の mouse_click の subTest。`test_minimize_grab_custody.py` は hotkey のまま開くため追随不要）
- 最小化から復元したときに非表示の欄へフォーカスを戻さないことの新規テスト（復元は `modal.py:44` の `focus_lastfor`）
- 正本 `features.md` §4.6「出力シーケンスの編集」への追記・`codebase_map.md`（必要なら）

### 含まない（後送り）

- ダイアログの高さ・幅の固定 / 項目の並び順の全面的な見直し
- system / file_line / マウス設定の欄の中身の変更
- プリセット編集など他のダイアログの整理

## このフェーズで読むファイル

1. `keyseq/presentation/dialogs/action_dialog.py`（全体。`__init__` のレイアウト・`_sync_capture_ui`）
2. `keyseq/presentation/dialogs/action_control_fields.py:184-225`（`sync_system`・`_show` の表示切替の流儀）
3. `keyseq/presentation/modal.py:122` `grab_modal(..., focus=)`（初期フォーカスの渡し方・最小化の預かり）
4. `tests_ui/test_dialog_initial_focus.py:94-105`（値欄を前提にした初期フォーカス）・`tests_ui/test_minimize_grab_custody.py:63-66,326-353`（最小化の預かりのテストの流儀）・`tests_ui/test_action_dialog_control.py`（system / file_line の表示確認の流儀）
5. 正本 `features.md` §4.6「出力シーケンスの編集」・「モーダルダイアログの作法」（初期フォーカスの条項 :679-682）

## タスク

- task_01: presentation — 種別ごとの非表示・「末尾に追加」の移動・初期フォーカスの切替とテスト。**実装後にユーザーの実機目視** —
  **実装完了・実機目視待ち**（2026-10-06。codex-implementer・reviewer 修正要〔中: 非アクティブ時に focus_get() が None で隠れる欄からフォーカスを移せない〕→ メインで focus_lastfor も見るよう修正 + テスト 2 件。
  verifier 1 回目 tests_ui 104 件落ち〔`__init__` 途中の `_rebuild_preset_buttons` → `_sync_capture_ui` で preset_edit_btn 未定義・旧コードの hasattr ガードが消えていた〕→ メインで同期の呼び出しを外して解消。
  2 回目 1 件〔初回表示前の winfo_ismapped・テストを update() へ〕→ 該当 41 件 OK。tests 1308 / tests_ui 837 / smoke pass）
- task_02: 正本反映（`features.md` §4.6「出力シーケンスの編集」へ確定 1〔種別ごとの表示〕・2〔「末尾に追加」の位置〕・4〔初期フォーカス・edit_loop を含む〕を追記。「モーダルダイアログの作法」:679-682 は一般形のため改訂不要・`codebase_map.md`）・`decisions_archive/47_action_dialog_layout_cleanup.md`・current.md の完了記載・`/refactor_check`。起票元 idea なし

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: 種別の切替を往復しても表示が崩れないか（hotkey → system → hotkey 等）/ 記録中に種別を変えたとき記録が止まるか（既存挙動）/
  ループの行の編集（種別が固定）・プリセットの追加ダイアログ（mode なし）で壊れないか / 最小化から復元したときのフォーカスの預かり（非表示の値欄へ戻そうとしないか）
- 完了判定前に `deep-reviewer` + `codex-adversarial-reviewer`
- 実機目視（ユーザー）: task_01（各種別の表示・「末尾に追加」の位置・開いたときのフォーカス・切替での伸び縮み）
