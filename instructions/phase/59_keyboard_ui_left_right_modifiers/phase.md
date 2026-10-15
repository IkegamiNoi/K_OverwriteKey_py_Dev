# phase.md

## フェーズ名

キーボードUI の左右の修飾キーの区別と割り当て禁止のキー（keyboard_ui_left_right_modifiers）

## フェーズの目的

キーボードUI で左右の修飾キー（Shift・Ctrl・Alt・Windows）の枠を左右別のキーとして表示・編集できるようにし、
抑止しても OS 側の動作が止まらない Windows キー（左右）・Caps Lock・AltGr 配列の右 Alt を、キーマップの元キーと切替キーに割り当てられないようにする。
**presentation 中心（keyboard_window・keymap_panel_controller・切替キーのダイアログ）+ application の切替キーの検査（`keymap_switch_batch.py`）。
入力の経路（`input_router`）・フック・送信は変えない。JSON スキーマ不変（レイアウトの JSON の書式も不変・標準の id `alt_gr` を 1 つ足す）。レイアウトの見本 `de.json` を新規に同梱。**

- 起票元: ユーザー要望（2026-10-15・キーボードUI が左右の修飾キーを区別せず、左右の枠に同じ割り当てが出て左のキーにしか効かない）。
- 主入力（暫定仕様）: [43_keyboard_ui_left_right_modifiers.md](../../history/43_keyboard_ui_left_right_modifiers.md)（v0.4・ユーザー確定済 2026-10-15）
- モード: **暫定仕様先行モード**。番号対応: phase 59 / 暫定 43 / decisions 59。

## 確定（ユーザー 2026-10-15）

暫定 43 §2 が正（本書に再掲しない）。要点: 枠のラベルはそのまま・id → キー名を左右で分ける（左は今の名前）/ レイアウト JSON の書式は変えない / 右 Alt は JIS・US で割り当て可 /
AltGr 配列の右 Alt は標準の id `alt_gr`（キー名 `alt gr`）で書き分けて割り当て禁止・アプリは配列を判定しない / Windows キー・Caps Lock・`alt gr` はキーボードUI と切替キーの取得の両方で割り当て禁止 /
`scan_code` は「書かない」と規定するだけ / `jis.json` に左右の Ctrl・Alt・Win を追加・ドイツ語配列の見本 `de.json` を同梱 / AltGr 配列は実機確認せず自動テストだけ。

## スコープ

### 含む

- 暫定 43 §3.1〜§3.6 の実装とテスト
- 実機目視（JIS 配列・暫定 43 §5-8・§5-9）
- 正本反映（暫定 43 §7）

### 含まない（後送り）

- 暫定 43 §6 のとおり（取得のダイアログでの左右の区別 / トリガー・停止 / トグルキー・送信先での禁止 / 既存の禁止キーの割り当ての自動削除 / AltGr 配列の実機確認・抑止 / 入力配列の判定 ほか）

## このフェーズで読むファイル

1. `instructions/history/43_keyboard_ui_left_right_modifiers.md`（全体）
2. キーボードUI: `keyseq/presentation/keyboard_window.py`（`_LOOKUP_KEY_BY_ID`・`redraw`・クリック / 右クリック・`set_key_color`・`_normalize_tk_key`）
3. レイアウト: `keyseq/presentation/keyboard_layouts.py`（既定レイアウト・`resolve_key_id_from_scan_code`）・`config/user/keylayout/jis.json`
4. 割り当てと切替キー: `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`（`assign_keymap_from_keyboard_ui`・`clear_keymap_from_keyboard_ui`・`validate_keymap_switch_assignment`・`apply_keymap_edit`）/
   `keyseq/application/keymap_switch_batch.py`（`validate_switch_batch`）
5. 切替キーの取得: `keyseq/presentation/dialogs/keymap_edit_dialog.py`・`keymap_switch_batch_dialog.py`・`keyseq/presentation/tk_keys.py`
6. キー名の正規化: `keyseq/domain/config.py:85-87`（`normalize_key_name`）/ 入力のキー名（読むだけ・変えない）: `keyseq/application/input_router.py`（`_extract_key_name`）・`keyseq/application/key_state_manager.py`
7. 正本: `features.md` §4.3（keymap）・§4.6「キーボード表示のウィンドウ」/ `codebase_map.md`（キーボードUI）
8. テスト: `tests_ui/test_task05_overlap_ui.py`・`test_task06_keymap_management_ui.py`・`test_trigger_effective_row.py`（`_display_map` / `_kind_map`）・`test_app_ui_flows.py`（キーボードUI）・切替キーのダイアログのテスト・`tests/` の `keymap_switch_batch`

## タスク

- task_01: キーボードUI の左右の修飾キーの対応（`_LOOKUP_KEY_BY_ID` を左右で分ける・表示 / 色 / 編集 / 右クリックのクリア / タイトルが枠ごと）と tests_ui（暫定 43 §3.1・§3.2・§3.4・§5-1〜5）
- task_02: 割り当て禁止のキー（判定の関数 1 つ〔application の検査からも使うので presentation に置かない＝domain / application〕・キーボードUI の禁止の色と編集しない・`assign_keymap_from_keyboard_ui` の拒否・切替キーの取得の無視と検査〔変えたときだけ〕）とテスト（暫定 43 §3.5・§5-6・§5-7）
- task_03: 標準の id `alt_gr`（キー名 `alt gr`・禁止）と `config/user/keylayout/de.json` の見本とテスト（暫定 43 §3.6・§5-11）
- task_04: `jis.json` に左右の Ctrl・Alt・Win を追加（`scan_code` なし）。静的確認（暫定 43 §5-10）+ **実装後にユーザーの実機目視**（JIS: 右 Ctrl・右 Shift・右 Alt が効く・Caps キーの名前と禁止の判定・暫定 43 §5-8・§5-9）
- task_05: 統合確認（tests / tests_ui / smoke・deep-reviewer + codex-reviewer）
- task_06: 正本反映（暫定 43 §7 の昇格・凍結・`codebase_map.md`）・`decisions_archive/59_keyboard_ui_left_right_modifiers.md`・decisions.md の索引・current.md の完了記載・`/refactor_check`

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: 左の枠のキー名は今のまま（既存のキーマップの `ctrl` 等が左で効き続ける）/ 判定は枠の id ではなくキー名で行う / 禁止の判定は 1 か所の関数を共有（表記の揺れ `caps_lock` 等を含む）/
  切替キーの検査は今の切替キーから変えたときだけ / 既存データを読込で拒否しない・自動で消さない / 入力の経路・フック・送信を変えていない
- 統合確認（task_05）: `deep-reviewer` + `codex-reviewer` / 完了判定前（task_06）: `deep-reviewer` + `codex-adversarial-reviewer`
- 実機（ユーザー）: task_04（task_01〜03 の分もまとめて見る）
