# task_09d_hotkey_capture_base_char

## 目的

Mac で hotkey の「キー入力で記録」で Option+a を押すと `alt+å` が記録される（task_09c の Mac 目視・2026-11-15）。原因は `action_dialog.py:450` が修飾なしのキーの名前を Tk の keysym から作っていること（aqua の keysym は Option で変わった文字になる）。修飾なしのキーの名前を、キーボードUI（`keyboard_window.py:636-662` の `_normalize_tk_key`）と同じく **keycode → 走査コード → レイアウトの id** で引き、引けないときだけ今の keysym の経路（`normalize_tk_key_event`）に戻る。暫定 57 §5.3（Tk のキー取得は aqua の keycode を vk として解釈）の適用漏れ。

- presentation 限定。domain / application / backend・スキーマ不変。OS を判定しない（Windows は keycode からの解決が今の keysym と同じ名前になる見込み。違う場合は報告して止める）。
- 修飾キーの名前（`alt` / `windows` → `option` / `command`）は task_09e で変わる。本タスクは修飾キーの集め方を変えない。

## 対象範囲（presentation 限定）

### `keyseq/presentation/tk_keys.py`

- キーの名前を keycode から引く純関数を 1 つ足す（例 `resolve_tk_event_key_name(event, layout) -> str`）。中身は `keyboard_window.py:636-661` の `_normalize_tk_key` と同じ順: テンキー → `TK_KEYSYM_TO_KEYBOARD_NAME`（修飾キー・Enter 等）→ `get_backend().tk_keys.vk_to_scan_code` → `resolve_layout_key_id_from_scan_code` → 正規化（テンキー名は除く）。**引けなければ空文字を返し、戻り先は呼ぶ側が決める**（起票レビュー M1）。
- `keyboard_window.py` の `_normalize_tk_key` はこの関数を呼び、空なら今と同じく小文字の keysym（`:662` の `return k`）を返す（振る舞いは不変）。

### `keyseq/presentation/dialogs/action_dialog.py`

- `_on_key_press`（:447-460）の修飾なしのキーの名前を上の関数で作り、空なら今の `normalize_tk_key_event` に戻る（aqua の Super → `??` を保つ）。レイアウトは App の `self.layout`（`app.py:175,194`）。`action_dialog.py` は今レイアウトを参照していないため、受け取り方（`self.parent` 経由・引数等）を決め、完了報告に書く（起票レビュー M2）。`_on_key_release` の修飾キーの判定は今のまま。
- `key_hold` の「1キーを記録」（`presentation/dialogs/action_key_hold_fields.py`）が同じ問題を持つか確かめ、持つなら同じ関数へ揃える（持たないなら報告だけ）。

## 読むファイル

- `keyseq/presentation/dialogs/action_dialog.py:400-490`
- `keyseq/presentation/keyboard_window.py:600-662`
- `keyseq/presentation/tk_keys.py`（全体）
- `keyseq/infrastructure/os_backend/macos/backend.py:275-297`（`MacTkKeyTranslator`）
- `instructions/history/57_mac_support.md` §5.3 の「Tk のキー取得」の行

## 含まない

- 修飾キーのキー名の変更・hotkey の修飾キーの並び順（task_09e）
- 修飾キー単独の読み飛ばしの統一・他方の OS の名前の拒否（task_09f）
- トリガー・切替キー等の他の記録の入口（Option を押したまま文字を押す使い方が無いため対象外。必要なら報告）
- キーボードUIで置換先に修飾キーを記録すること（idea_57）

## 確認

Mac（`../../../.venv/bin/python`・verifier）:
- tests: 新関数の単体テスト（Tk なし・偽のイベントとレイアウト）= aqua の keycode（vk 0 = `a` を上位 8 ビットに持つ値）で keysym が `aring` でも `a` を返す・走査コードが引けないときは keysym の正規化に戻る・テンキーはテンキー名。
- compile clean・`tests` が基準線（失敗 6・エラー 10）から増えない・smoke pass・`tests_ui` の action_dialog / keyboard_window に関係するものを 1 本ずつ。
Windows: task_09 / 09a / 09c と合わせて verifier（compile・tests 失敗 0・tests_ui 1 本ずつ・smoke）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視（Mac・本タスクで実施）: hotkey の記録で Option+a → `alt+a`・Option+Shift+2 → `alt+shift+2`（記号に化けない）・Command+→ → `windows+right`（修飾キーの名前は task_09e の前のため `alt` / `windows` のまま）。

## 起票レビュー

reviewer「修正して採用」（2026-11-15）: 中 2（M1 = 09d のフォールバック先の誤り・M2 = 09d のレイアウトの受け取りと key_hold のファイル名）・低 3（L1 = 09e の modifier_flags と既存 id の扱い・L2 = 09e / 09f の action_dialog の分担・L3 = 09f の tests_ui の指定）を反映（ユーザー「反映してコミット」）。
