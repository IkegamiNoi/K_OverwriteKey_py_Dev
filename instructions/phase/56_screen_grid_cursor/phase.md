# phase.md

## フェーズ名

画面の枠でカーソル移動・クリック（screen_grid_cursor）

## フェーズの目的

枠 ON のキーマップがアクティブな間、画面に枠（グリッド）を重ねて表示し、キーで枠を選んでカーソルを中心へ運び Enter でクリックできるようにする
（Space で細分化・Esc / BackSpace で一段戻る・Tab で画面の切替・最上段の枠はドラッグで編集し画面ごとに記録）。
**domain（形・細分化・キー割当・検証の純関数）/ application（枠の操作の状態機械・入力の振り分け・フックの開始条件）/ infrastructure（モニタの列挙・カーソル移動とクリック・窓の拡張スタイル）/ presentation（枠の窓・編集の窓・ダイアログのチェック）に跨る。JSON スキーマ変更あり（keymap に任意キー `grid`・後方互換）。**

- 起票元: ユーザー要望（2026-10-12）。
- 主入力（暫定仕様）: [40_screen_grid_cursor.md](../../history/40_screen_grid_cursor.md)（v0.6・ユーザー確定済 2026-10-12）
- モード: **暫定仕様先行モード**。番号対応: phase 56 / 暫定 40 / decisions 56。

## 確定（ユーザー 2026-10-12）

暫定 40 §2 の 1〜12 が正（本書に再掲しない）。要点: キーマップの編集 / 追加（新規の行）に「枠を使う」/ アクティブな間だけ表示しトリガー・置換は効かない /
既定の最上段 3×4・細分化 3×3（キーは任意指定）/ 最上段は段ごとに列を独立させて自由に編集・画面ごとに比率で記録 / Tab で画面の切替（同時表示はしない）/
クリック後は最上段へ戻り表示を続ける / 最上段の Esc は素通し・BackSpace は何もしない / 枠だけの構成でもフックを開始・再開できる / DPI は実機で検証してから決める。

## スコープ

### 含む

- 暫定 40 §3〜§9 の実装とテスト
- 画面・座標の検証（暫定 40 §6・本番の起動経路で・ユーザーの実機）。**既定案で成り立たなければ止めてユーザー確認**
- 実機目視（暫定 40 §11 の 1〜6・9〜13）
- 正本反映（暫定 40 §13）

### 含まない（後送り）

- 暫定 40 §12 のとおり（複数画面への同時表示 / 細分化後の境界のドラッグ / 中クリック・ダブルクリック・ドラッグ・ホイール / 配色等の設定 / まとめて設定のダイアログでの形の編集 / シーケンスからの枠の操作 / キーボード表示での枠のキー表示）

## このフェーズで読むファイル

1. `instructions/history/40_screen_grid_cursor.md`（全体）
2. 入力の振り分け: `keyseq/application/input_router.py`（:76-140 `handle`）・`keyseq/presentation/controllers/hook_controller.py`（:21-24 状態・:119-216 開始 / 停止 / 一時停止・:286-296 実行）・`keyseq/application/hook_coordinator.py`（:20-95 開始と再開の判定）
3. キーマップ JSON: `keyseq/domain/config.py`（:311 `_normalize_keymaps`）・`keyseq/application/config_service/__init__.py`（:156-186 `_normalize_loaded_keymap`・:227-229 `_keymap_item_for_save`）・`config_service/split_loading.py`（:439-455）・`config_service/split_payloads.py`（:507-521）
4. ダイアログ: `keyseq/presentation/dialogs/keymap_edit_dialog.py`（全体・128 行）・`dialogs/keymap_switch_batch_dialog.py`（:100-165）・`controllers/keymap_panel/keymap_panel_controller.py`（:375-395 編集・:441-485 アクティブ化）・`controllers/keymap_panel/keymap_add_flow.py`
5. 送信と Win32: `keyseq/infrastructure/input_gateway.py`（:320-370 クリック・カーソル）・`keyseq/infrastructure/win32_window.py`（全体）
6. 表示の同期の契機: `keyseq/presentation/controllers/layout_controller.py`（`refresh_keyboard_window`）
7. 正本: `data_schema.md` §5.1・§5.2・§5.6・§5.11.2 / `features.md` §4.3・§4.5・§4.6 / `key_input.md` §7 / `codebase_map.md`（フック関連 :622〜・マウス操作 :808〜・キーマップとトリガー一覧 :856〜）
8. テスト: `tests/test_input_router.py`・`tests/test_keymap_service.py`・`tests/test_config_service.py`・`tests_ui/test_task06_keymap_management_ui.py`・`tests_ui/test_keymap_switch_batch_dialog.py`

## タスク

- task_01: 画面・座標の検証（スパイク・暫定 40 §6）。本番の起動経路で DPI の実状態・モニタの列挙・枠なし窓の位置・カーソル移動とクリックの一致・非アクティブ / クリック素通し・負の座標・表示中の画面の抜き差し / 配置の変更・Space / Enter の直後の連打（§6 末尾）を実測し、手段（pyautogui / Win32）と画面の識別子の座標系を確定。**ユーザーの実機で確認**。既定案で成り立たなければ止める
- task_02: `grid` の domain（形のモデル・既定・正規化・セルの矩形・細分化・自動割当 / 振り直し・検証の純関数）と JSON の全経路の保持（暫定 40 §3・§5）と単体テスト
- task_03: application の枠の操作（状態機械・世代・画面の識別子・suppress する集合と Esc の印・Shift の採取・モニタ構成の変化〔識別子が見つからなければクリックせず最上段へ・集合の作り直し〕）と `input_router` への組み込み・フックの開始 / 再開の条件（暫定 40 §4）と単体テスト
- task_04: infrastructure（モニタの列挙・カーソル移動 / クリック・窓の拡張スタイル）と presentation の枠の窓・表示の同期・モニタ構成の変化での窓の作り直し（暫定 40 §4.1・§4.5・§7）。**実装後にユーザーの実機目視**
- task_05: ダイアログの「枠を使う」（編集ダイアログ + まとめて設定の新規の行・暫定 40 §8.1）と UI テスト
- task_06: 編集の窓（境界のドラッグ・段 / 列の追加と削除・キーの変更・振り直し・既定に戻す・細分化の設定・OK の検査・暫定 40 §8.2）と UI テスト。**実装後にユーザーの実機目視**
- task_07: 統合確認（tests / tests_ui / smoke・deep-reviewer + codex-reviewer）
- task_08: 正本反映（暫定 40 §13 の昇格・凍結）・`decisions_archive/56_screen_grid_cursor.md`・decisions.md の索引・current.md の完了記載・`/refactor_check`

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: **フックのスレッドでの判定が UI スレッドの状態に依存しない**（集合・世代・Esc の印・Shift の採取）/ 世代の不一致・表示外の操作は何もしない /
  画面が変わったらクリックしない / `grid` が全経路で落ちない・`grid` の無い keymap に差分が出ない / presentation から ctypes を直接呼ばない /
  domain に tkinter・Win32 を持ち込まない / 枠の窓がフォーカスを取らずクリックを素通しする
- 統合確認（task_07）: `deep-reviewer` + `codex-reviewer` / 完了判定前（task_08）: `deep-reviewer` + `codex-adversarial-reviewer`
- 実機（ユーザー）: task_01・task_04・task_06
