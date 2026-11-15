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

## 実装後の改訂（2026-11-15・ユーザー「推奨どおり絞る」）

reviewer（採用・中 1）の指摘を調べた結果、上の「keycode → レイアウトの id を先に引く」は記号キーで正本と食い違う: レイアウトの id は記号そのもの（`us_tkl.json` の `,` `.` `;` 等）で、正本 `features.md` §4.6「記号キーのキー名の表示」は単語の名前（`comma` 等）で保存する。そのため hotkey が `ctrl+,` になり、`key_hold` は `,` を `key_invalid_chars` で拒否する。Windows でも Shift+1 が `shift+exclam` → `shift+1` に変わる。**次のとおり範囲を絞る**（この節が上の「対象範囲」の該当部分に優先する）:

- `resolve_tk_event_key_name` は今のまま（キーボードUIは今の結果を保つ）。
- hotkey（`action_dialog.py`）と `key_hold`（`action_key_hold_fields.py`）は、**keysym を正規化した結果が ASCII 以外の 1 文字、または Tk の Unicode の keysym（`U` + 16 進 4 桁以上・例 `U2264`）のときだけ**（Mac の Option で `å` / `≤` 等に変わったとき。Mac の実測で保存値が `alt+å` = keysym が文字そのもの）keycode から引く。それ以外は従来の正規化（`normalize_tk_key_event` / `normalize_key_hold_tk_key_event`）のまま。→ Windows の keysym は ASCII のため Windows の記録結果は変わらない。
- keycode から引いた名前が記号 1 文字なら、`domain/key_symbols.py` の `KEY_SYMBOLS` を逆に引いて単語の名前にし（同じ記号が複数あるときは表の先の方 = `backslash` / `grave` / `apostrophe`）、続けて keysym の経路と同じ `TK_KEYSYM_TO_KEYBOARD_NAME` を通す（例: `,` → `comma`・`-` → `minus` → `-`）。結果は、Option を押さずに同じキーを押したときの従来の記録と同じ名前になる。
- 判定と変換は `tk_keys.py` の関数 1 つにまとめ（例 `resolve_modified_char_key_name(event, layout) -> str`・該当しなければ空文字）、hotkey と `key_hold` はそれを先に呼び、空なら従来の正規化へ戻る。
- テスト（tests・Tk なし）: keysym `aring` → `a`・`lessequal` 相当の非 ASCII 1 文字で位置が `,` → `comma`・ASCII の keysym（`a`・`exclam`・`comma`）では keycode を引かない（`vk_to_scan_code` を呼ばない）・修飾キーの keysym では空。

Mac の目視（完了条件）の期待値: Option+a → `alt+a`・Option+, → `alt+comma`・Command+→ → `windows+right`（`key_hold` は修飾キーを先に押すとそれを記録して止まるため、目視の対象にしない）。

## 実装後の改訂 2（2026-11-15・Mac 目視の結果・ユーザー「推奨どおり直す」）

Mac 目視: Option+a → `alt+å`・Option+, → `alt+lessthanequal`（直っていない）・Command+→ → `windows+right`（OK）。原因 = ①`self.parent.layout` は `LayoutController`（`app.py:297`）で `KeyboardLayout` ではなく、走査コードから名前が引けず毎回空文字になっていた ②Tk 9 の aqua は `≤` を名前の keysym（`lessthanequal`）で返し、改訂 1 の判定（非 ASCII 1 文字・`U....`）に当たらない。改訂 1 を次のとおり直す:

- **判定**: keysym ではなく **`event.char` が ASCII 以外の 1 文字**のとき（加えて改訂 1 の keysym の判定も残してよい）。Windows で変わるのは AltGr 等で ASCII 以外の文字を出したときだけ（例 de の AltGr+e: 従来 `ctrl+alt+eurosign`〔送れない名前〕→ `ctrl+alt+e`）。
- **名前の引き方**: `LayoutController.resolve_key_name_from_scan_code`（`layout_controller.py:417`・フックと同じ）を使う。`resolve_modified_char_key_name` は `KeyboardLayout` ではなく「走査コード → キー名」の関数を受け取る（hotkey / key_hold は `getattr(self.parent, "layout", None)` の `resolve_key_name_from_scan_code`・無ければ空文字）。テンキー名は除外、記号 1 文字は改訂 1 のとおり逆引き。
- **テスト**: 偽のレイアウトではなく実物の `LayoutController` 相当（`config/user/keylayout/us_tkl.json` を読んだ `KeyboardLayout` を `resolve_layout_key_id_from_scan_code` で引く関数）で、`char="å"`・`keysym="aring"`・vk 0 → `a`、`char="≤"`・`keysym="lessthanequal"`・vk 43（`,`）→ `comma`。`char` が ASCII（`a`・`!`）では keycode を引かない。

## 実装後の改訂 3（2026-11-15）・結果

- 改訂 2 の後もレイアウトから `a` が引けなかった（`us_tkl` は文字キーに走査コードを持たない）→ メインが「レイアウトの走査コード → backend の `vk_to_char`」の順に修正（`keymap_panel_controller.py:467-477` のグリッドと同じ順）。テストは Mac の `key_table` を使う偽の backend + 実物の `us_tkl.json`。
- reviewer 再レビュー 2「修正して採用」・中 1 = `event.char` の判定が Windows でも効く（de / 北欧の専用キー・非ラテン配列・AltGr の文字）。従来の記録（`adiaeresis` 等）は送れない名前のため、変化は「使えなかったものが使える」方向の見込み → **ユーザー判断: Windows も含める**（2026-11-15）。
- **Mac 実機目視 OK**（2026-11-15）: Option+a → `alt+a`・Option+, → `alt+comma`・Command+→ → `windows+right`。
- **Windows の完了条件に追加**（task_09〜09f の Windows 検証でまとめて・未実測）: Windows の入力にドイツ語を足し、hotkey の記録で ä の位置のキーと AltGr+e を記録 → 記録された値で hotkey を実行して ä / € が出ること。従来は送れなかった名前（`adiaeresis` / `ctrl+alt+eurosign`）が変わることの確認。
- 実装: codex-implementer（4 回の resume）。メイン修正 = `aring` の特例の除去（Windows の北欧配列で記録が変わるため）・`vk_to_char` への戻り・tests の Mock の import と `_mac_tk_keys_backend`・tests_ui の patch 先の行き過ぎと numpad_name の欠け。reviewer の低（docstring・import 順・関数の行数・型注釈）は参考扱いで未対応。
