# task_09f_modifier_name_acceptance

## 目的

暫定 57 v0.11 §5.3.4 の「受け付け」と「修飾キー単独の読み飛ばし」を実装する。両 OS で他方の OS の修飾キーの名前を不明なキーとして拒否し（Windows で `command` / `cmd` / `option` 系が通らなくなる互換性の変更を含む）、拒否を §5.3.4 の入口ごとの時点で効かせる。記録の入口の修飾キー単独の判定を domain の `is_modifier_key` に揃える。

- 判定は backend の口 1 つ（OS ごと）。domain / application は OS を判定しない。スキーマ不変・既存データは読み込みで保持（変換しない）。

## 対象範囲

### backend（`os_backend/contracts.py`・`windows/`・`macos/`）

- `KeyboardBackend` に「その OS で受け付けるキー名か」を返す口を足す（例 `accepts_key_name(name: str) -> bool`。正規化 = trim + 小文字 + `_` → 空白）。
  - Mac で拒否: `windows` / `left windows` / `right windows` / `win` / `left win` / `right win` / `alt` / `left alt` / `right alt` / `left menu`
  - Windows で拒否: `command` / `left command` / `right command` / `cmd` / `option` / `left option` / `right option`
- 両 backend の `resolve_send`（= `validate_key_name` の経路）の先頭でこの口を通し、拒否なら今の不明なキーと同じ `ValueError`。Windows は `keyboard.key_to_scan_codes` へ渡す前に拒否する。hotkey の送信の解決も同じ経路を通ることを確かめる。
- `input_gateway` に口の横流しが要れば足す（presentation は gateway 経由で呼ぶ）。

### 拒否の入口（presentation / application・§5.3.4）

1. キーボードUIで置換元の編集を始めるとき: `keyboard_window.py:561-567` の `_on_canvas_left_click` で、拒否される枠は割り当て禁止と同じく編集を始めない。枠の色を禁止の色にするか（`:470` の `prohibited`）は、§5.3.2 v0.11「割り当てに使えない」に合わせて禁止の色にする。
2. 割り当ての確定: `keymap_panel_controller.py:631-664` の `assign_keymap_from_keyboard_ui` で置換元も口で検査（置換先は既存の `validate_key_name`）。エラーの文言は既存の不明なキー（`capture.error.unknown_key`）。キーマップ編集ダイアログ等、置換元を確定する他の経路があれば同じく（grep で洗い出して報告）。
3. トリガーの追加・キーの変更の確定: `controllers/trigger_panel/trigger_row_edit.py`（追加 :24-50・変更）で口を通す。
4. hotkey の保存（`action_dialog.py:246-251`）: 値を `+` で分けた各要素のうち、**他方の OS の修飾キーの名前だけ**を口で検査して拒否（他の名前は今どおり保存時に検査しない）。
5. `key_hold` の保存（`action_dialog.py:305-317`）: 今の `validate_key_name` のまま（backend の口を通るので追加不要。テストで確かめる）。
6. 切替 / 停止 / トグルキーの記録の確定（`controllers/key_capture.py`・`keymap_edit_dialog.py`・`keymap_switch_batch_dialog.py`）: 口で検査し、拒否は既存の取得のエラー表示。

### 修飾キー単独の読み飛ばし

- `("ctrl", "shift", "alt", "windows")` の固定の並びを `domain.key_hold.is_modifier_key` に置き換える: `trigger_dialog.py:126`・`keymap_edit_dialog.py:195-197`・`keymap_switch_batch_dialog.py:275` 付近・`key_capture.py:155`・`keyboard_window.py:618`・`action_dialog.py:453`（hotkey の修飾キーの集め方。並び順は task_09e のまま）。`key_hold` の記録（修飾キー単独を左右つきで記録）は変えない。`grep -rn '"windows")' keyseq` で漏れを確かめる。

## 読むファイル

- `instructions/history/57_mac_support.md` §5.3.4（受け付け・修飾キー単独の読み飛ばし）・§9 の 14・15
- `os_backend/contracts.py:20-64`・`windows/keyboard_backend.py:160-195`・`macos/backend.py:130-160`
- `keyboard_window.py:460-475,555-625`・`keymap_panel_controller.py:625-670`
- `trigger_dialog.py:110-150`・`trigger_row_edit.py:1-110`・`action_dialog.py:240-320,440-470`
- `key_capture.py:130-185`・`keymap_edit_dialog.py:180-210`・`keymap_switch_batch_dialog.py:265-285`
- `domain/key_hold.py:20-95`

## 含まない

- Mac のキー名そのもの・表示名の差し替えの撤去（task_09e・先に済ませる）
- 既存の設定の変換・読み込み時の拒否（しない・§5.3.4）
- 正本 `features.md` の別名の列挙・`key_input.md` の hotkey の保存時の検査の例外の追記（task_14）
- キーボードUIで置換先に修飾キーを記録すること（idea_57）

## 確認

Mac / Windows（verifier）:
- tests: 口の判定（両 OS の拒否リスト全件・`_` 区切り・大文字）・`resolve_send` / `validate_key_name` の拒否（Windows で `command+c` が `ValueError`・Mac で `windows+c` が `ValueError`・Windows で `windows+c` は通る）・`assign_keymap_from_keyboard_ui` の置換元の拒否・トリガーの追加の拒否・hotkey の保存で他方の修飾キーだけ拒否され未知の通常キーは保存できる・`key_hold` の未知のキーは今どおり OK で拒否・既存の設定（他方の名前を含む JSON）が読み込めてキー名が保持される・記録の入口で `option` / `left command` 単独が確定しない（Tk なしで済む部分は tests、Tk の要るものは tests_ui）。
- compile clean・Mac は `tests` が基準線から増えない・Windows は tests 失敗 0・smoke pass・`tests_ui` は `trigger_dialog` / `key_capture` / `keyboard_window` / `action_dialog` / `keymap_edit_dialog` / `keymap_switch_batch_dialog` に関係するものを 1 本ずつ（起票レビュー L3）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。`codebase_map.md` の backend の口・入口の行を追従（メイン）。
- 実機目視（Mac・本タスクで task_09e の分とまとめて実施）: §9 の 14・15 と、hotkey / トリガー / キーマップ一覧 / 停止キーの欄で `command` / `option` が表示されること・Option+a の hotkey が `option+a`。Windows の目視は task_09〜09f の Windows 検証でまとめて。

## 起票レビュー

reviewer「修正して採用」（2026-11-15）: 中 2（M1 = 09d のフォールバック先の誤り・M2 = 09d のレイアウトの受け取りと key_hold のファイル名）・低 3（L1 = 09e の modifier_flags と既存 id の扱い・L2 = 09e / 09f の action_dialog の分担・L3 = 09f の tests_ui の指定）を反映（ユーザー「反映してコミット」）。
