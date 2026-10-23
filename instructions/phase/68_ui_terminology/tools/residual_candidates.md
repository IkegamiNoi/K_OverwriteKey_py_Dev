# 残存候補（実装後・機械抽出）

| 場所 | 規則 | 文字列 | 理由 |
|---|---|---|---|
| keyseq/application/action_executor.py:162 | D9 | `カウンター名が空です` | |
| keyseq/application/config_service/save_plan_execution.py:434 | D9 | `別名保存先が空です: {entry.kind}:{entry.key}` | |
| keyseq/application/config_service/save_plan_execution.py:440 | M9 | `別名保存先のディレクトリを作成できません: {entry.kind}:{entry.key}` | |
| keyseq/application/sequence_steps.py:48 | D1 | `回数={action.get('count', '（なし）')}` | |
| keyseq/application/sequence_steps.py:50 | D1 | `{action.get('ms', '（なし）')}ms` | |
| keyseq/application/sequence_steps.py:52 | D1 | `カウンター={action.get('counter', '（なし）')}` | |
| keyseq/application/sequence_steps.py:161 | D9 | `カウンター名が空です` | |
| keyseq/domain/hotkey.py:11 | D9 | `hotkeyが空です。` | |
| keyseq/domain/hotkey.py:18 | D9 | `hotkeyの '+' の前後が空です（例: 'ctrl++c' や '+ctrl+c' や 'ctrl+c+' は不可）。` | |
| keyseq/domain/screen_grid/assignment.py:77 | D9 | `{location}: キーが空です` | |
| keyseq/domain/screen_grid/normalize.py:37 | D9 | `キーが空です` | |
| keyseq/domain/screen_grid/normalize.py:53 | D8 | `段の形が不正です` | |
| keyseq/domain/screen_grid/normalize.py:55 | D8 | `比率が不正です` | |
| keyseq/domain/screen_grid/normalize.py:62 | D8 | `列の形が不正です` | |
| keyseq/domain/screen_grid/normalize.py:64 | D8 | `比率が不正です` | |
| keyseq/domain/screen_grid/normalize.py:73 | D8 | `比率が不正です` | |
| keyseq/domain/screen_grid/normalize.py:78 | D8 | `比率が不正です` | |
| keyseq/domain/screen_grid/normalize.py:92 | D8 | `形が不正です` | |
| keyseq/domain/screen_grid/normalize.py:95 | D8 | `段数が不正です` | |
| keyseq/domain/screen_grid/normalize.py:97 | D8 | `列数が不正です` | |
| keyseq/domain/screen_grid/normalize.py:99 | D8 | `段数・列数が不正です（枠を2つ以上にしてください）` | |
| keyseq/domain/screen_grid/normalize.py:101 | D8 | `キー数が不正です` | |
| keyseq/domain/screen_grid/ops.py:92 | D9 | `キーが空です` | |
| keyseq/infrastructure/win32_window.py:62 | D5 | `前面ウィンドウ HWND の取得に失敗しました` | |
| keyseq/presentation/controllers/config_io/keymap_set_io.py:624 | D5 | `Import しました。` | |
| keyseq/presentation/controllers/config_io/keymap_set_io.py:627 | D5 | `Import 失敗: {e}` | |
| keyseq/presentation/controllers/config_io/keymap_set_io.py:628 | D5 | `Import 失敗` | |
| keyseq/presentation/controllers/config_io/keymap_set_io.py:642 | D5 | `Export しました。` | |
| keyseq/presentation/controllers/config_io/keymap_set_io.py:645 | D5 | `Export 失敗: {e}` | |
| keyseq/presentation/controllers/config_io/keymap_set_io.py:646 | D5 | `Export 失敗` | |
| keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:544 | A2 | `キーマップに変更はありません: {self.format_keymap_display_name(keymap) or keymap_id}` | |
| keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:550 | A2 | `キーマップを変更しました: {self.format_keymap_display_name(keymap) or keymap_id}` | |
| keyseq/presentation/dialogs/keymap_edit_dialog.py:157 | A10 | `記録中: 切替キーにしたいキーを1回押してください（Escでキャンセル）` | |
| keyseq/presentation/dialogs/keymap_switch_batch_dialog.py:224 | A10 | `記録中: 切替キーにしたいキーを1回押してください（Escでキャンセル）` | |
| keyseq/presentation/dialogs/preset_manager.py:320 | D8 | `不正なhotkey` | |
| keyseq/presentation/dialogs/preset_manager.py:356 | D8 | `不正なhotkey` | |
| keyseq/presentation/dialogs/trigger_dialog.py:92 | A10 | `記録中: トリガーにしたいキーを1回押してください（Escでキャンセル）` | |
| keyseq/presentation/keyboard_layouts.py:150 | D9 | `layout_idが空です。` | |
| keyseq/presentation/keyboard_layouts.py:160 | D9 | `display_nameが空です。` | |
| keyseq/presentation/keyboard_layouts.py:166 | D9 | `keysが空です。` | |
| keyseq/presentation/keyboard_layouts.py:184 | D9 | `{key_prefix}.idが空です。` | |
| keyseq/presentation/reference_cleanup_text.py:63 | D1 | `  {path}: {_FAILURE_MESSAGES.get(reason, '不明な理由で失敗しました')}` | |
