# phase.md

## フェーズ名

キーボードUI の取得で VK を走査コードへ変換する（keyboard_ui_vk_to_scan_code）

## フェーズの目的

キーボードUI の編集中に押したキーの名前を作るとき、Tk の `keycode`（Windows では仮想キーコード = VK）を**走査コードとして**レイアウトに引いているため、どのレイアウトでも F1 → `kana`・F10 → `henkan`・F12 → `muhenkan` になる不具合を直す。
あわせて、この経路の本来の目的（JIS の特殊キー〔無変換・変換・半角/全角〕をレイアウトの `scan_code` で解決する）が効くようにする。
**presentation 限定（`keyboard_window._normalize_tk_key` に VK → 走査コードの変換〔`win32_window.vk_to_scan_code`〕を挟む・画面の枠の編集の窓〔phase 56〕と同じ）。application・domain・フック・送信・JSON スキーマ不変。**

- 起票元: [idea_47](../../backlog/idea_47_keyboard_ui_keycode_as_scan_code.md)（2026-10-16・phase 59 暫定 43 の起票時の deep-reviewer の指摘 → 2026-10-16 にメインがコードの経路を実測して確認）。
- 主入力（暫定仕様）: なし（直接改訂モード）。
- モード: **直接改訂モード**（1 ファイルの不具合修正・規定はキーの取得の名前の 1 項の追記・タスク 2）。番号対応: phase 61 / 暫定なし / decisions 61。

## 確定（ユーザー 2026-10-16〜17）

- **VK → 走査コードの変換を挟む案**で直す（idea_47 の調査結果の推奨）
- **変換後は外部レイアウトの `scan_code` だけで引き、既知の特殊キーの表（`domain/key_identifiers.py`）へは落とさない**（JIS の特殊キーはレイアウトのファイル〔jis.json〕に閉じ込める方針の第一歩・2026-10-17 ユーザー判断。整合チェックの reviewer 指摘 = 既知の表へ落とすと US 入力配列のバッククォート〔走査コード 41〕が `zenkaku_hankaku` になる）
- 受容: US 入力配列の「`」はキーボードUI では `grave`・フックの実行時は `zenkaku_hankaku` と名前が違ったまま（今と同じ）/ JIS キーボードで jis.json 以外のレイアウトを選んでいるとキーボードUI では特殊キーが名前にならない
- フックの実行時と送信の側も「特殊キーはレイアウトが決める」に寄せる話は [idea_49](../../backlog/idea_49_special_keys_from_layout_only.md) へ分離

## スコープ

### 含む

- `keyboard_window._normalize_tk_key` の修正: レイアウトを引く前に `win32_window.vk_to_scan_code(keycode)` で変換し、**レイアウトの `scan_code` だけ**で引く（既知の特殊キーの表へは落とさない・変換できなければレイアウトを引かず keysym へ）。順序は テンキー → `TK_KEYSYM_TO_KEYBOARD_NAME` → 走査コードでレイアウト → keysym の小文字（今と同じ）
- 単体（UI）テスト: F1 / F10 / F12 が `f1` / `f10` / `f12`・JIS の無変換 / 変換 / 半角/全角（VK 0x1D / 0x1C / 0xF3）が jis.json で `muhenkan` / `henkan` / `zenkaku_hankaku`・**`scan_code` を持たないレイアウト（既定の US TKL）で走査コード 41 になるキー（US の「`」・VK 0xC0）が `zenkaku_hankaku` にならず keysym の名前**・変換できない（`None`）ときは keysym（`vk_to_scan_code` を差し替えて固定）
- 実機目視（ユーザー・JIS 配列）: キーボードUI の編集で F1 / F10 / F12 と無変換・変換・半角/全角・かなを押して入る名前
- 正本反映: `key_input.md` §7.4 にキーボードUI の編集（#7）の名前の作り方を 1 項追記・`codebase_map.md`

### 含まない（後送り）

- 他の取得の入口の名前の作り方（記号キーの名前 = idea_45）/ 画面の枠の編集の窓の経路（既に変換している。#8 は走査コードで引けないとき `vk_to_char` を使うが、キーボードUI は keysym へ落とす今の作りのまま・同じ名前にはしない）
- フックの実行時・送信の既知の特殊キーの表の扱い（idea_49）
- かな（VK 0x15 は `MapVirtualKeyW` で走査コードが得られない）の解決の作り込み（実機目視で何が入るかを記録し、必要なら別 idea）
- フックの実行時のキー名（`input_router` は走査コードを正しく使っている）

## このフェーズで読むファイル

1. `instructions/backlog/idea_47_keyboard_ui_keycode_as_scan_code.md`（調査結果）
2. `keyseq/presentation/keyboard_window.py`（`_normalize_tk_key`・import）
3. `keyseq/infrastructure/win32_window.py:138-148`（`vk_to_scan_code`）/ `keyseq/presentation/keyboard_layouts.py:327-340`（`resolve_key_id_from_scan_code`）
4. 手本: `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:452-467`（`_grid_key_name_from_event`）
5. 正本: `key_input.md` §7.4 / `codebase_map.md`（phase 59・60 のキーボードUI の節）
6. テスト: `tests_ui/test_keyboard_window_left_right.py`（キーボードUI の作り方）

## タスク

- task_01: `_normalize_tk_key` に VK → 走査コードの変換を挟む・テスト。**実装後にユーザーの実機目視**（JIS: F1 / F10 / F12・無変換・変換・半角/全角・かな）
- task_02: 正本反映（`key_input.md` §7.4 に #7 の名前の作り方〔順序・レイアウトだけで引く・変換失敗時は keysym・受容〕を追記・`codebase_map.md`）・`decisions_archive/61_keyboard_ui_vk_to_scan_code.md`・decisions.md の索引・current.md の完了記載・idea_47 を INDEX_done へ・`/refactor_check`・完了判定前レビュー

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: 解決の順序が変わっていない（テンキー・keysym の表が先）/ 変換に失敗したとき（`None`・Windows 以外）は keysym へ落ちる / 既知の特殊キーの表へ落ちない（フックの実行時・画面の枠の編集の窓が使う `resolve_key_id_from_scan_code` の挙動は変えない）/ 他の取得の入口・画面の枠の編集の窓は変えていない / `scan_code` を持たないレイアウト（既定の US TKL・de）で挙動が変わらない
