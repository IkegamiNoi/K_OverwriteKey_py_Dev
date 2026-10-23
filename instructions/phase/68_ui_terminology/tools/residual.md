# 残存一覧（実装後・task_07）

機械抽出（`scan_residual.py` → `residual_candidates.md`・42 件）の全行に理由を付けたもの。理由の無い行は 0。

| 場所 | 規則 | 理由 |
|---|---|---|
| `application/action_executor.py:162`・`sequence_steps.py:161`「カウンター名が空です」 | D9 | 実行時の内部検査（入力ダイアログの検査ではない・§3.6 D9 の範囲） |
| `config_service/save_plan_execution.py:434`「別名保存先が空です」 | D9 | 内部検査 |
| `config_service/save_plan_execution.py:440`「…ディレクトリを作成できません」 | M9 | ユーザー確定（2026-10-24）で置換済み |
| `application/sequence_steps.py:48・50・52` | D1 | 誤検出（コードの括弧。表示は全角「（なし）」で適用済み） |
| `domain/hotkey.py:11・18`「hotkeyが空です」等 | D9 | ファイル・入力値の文法検査（§3.6 D9 の細則で据え置き明記） |
| `domain/screen_grid/assignment.py:77`・`normalize.py:37`・`ops.py:92`「キーが空です」 | D9 | 枠の設定の内部検査 |
| `domain/screen_grid/normalize.py:53〜101`「〜が不正です」 | D8 | ログ専用（`logger.warning`・画面に出ない） |
| `infrastructure/win32_window.py:62`「前面ウィンドウ HWND の…」 | D5 | ログ専用（`_log_once`） |
| `controllers/config_io/keymap_set_io.py:624〜646`「Import しました。」等 | D5 | D10（Import / Export は英字のまま・D3・D5 も当てない） |
| `keymap_panel/keymap_panel_controller.py:544・550` | A2 | 誤検出（差し込みの変数名 `keymap_id`） |
| `dialogs/keymap_edit_dialog.py:157`・`keymap_switch_batch_dialog.py:224`・`trigger_dialog.py:92` | A10 | 誤検出（「記録中: 」に置換済み） |
| `dialogs/preset_manager.py:320・356`「不正なhotkey」 | D8 | ユーザー確定（2026-10-24）で置換済み |
| `domain/screen_grid/normalize.py:41`「修飾キー {key!r} です」 | D5 | ログ専用（`logger.warning`。対の `ops.py:94` は画面に出るため適用済み） |
| `presentation/keyboard_layouts.py:150〜184`「〜が空です」 | D9 | 外部レイアウト JSON の中身の検査 |
| `presentation/reference_cleanup_text.py:63` | D1 | 誤検出（コードの括弧） |

D3 の「…」: task_06 の reviewer が `d3_ellipsis_list.md` の全行と実装の一致を確認済み（半角 `...` は Import... / Export... のみ）。
