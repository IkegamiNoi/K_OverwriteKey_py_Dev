# task_02_prohibited_assign_keys

## 目的

Windows キー（左右）・Caps Lock・AltGr 配列の右 Alt（`alt gr`）を、キーマップの元キーと切替キーに割り当てられないようにする（暫定 43 §3.5・§3.6 の禁止の集合・§5-6・§5-7）。
**domain（判定の関数）+ application（まとめて設定の検査）+ presentation（キーボードUI・割り当ての入口・切替キーのダイアログ）。入力の経路・フック・読込は変えない。JSON スキーマ不変。**

## 対象範囲

### domain: `keyseq/domain/key_identifiers.py`

- `is_prohibited_assign_key(name: str) -> bool` を足す: `normalize_key_name(name)` が
  `left windows` / `right windows` / `windows` / `caps lock` / `caps_lock` / `capslock` / `alt gr` / `altgr` のどれかなら True。集合はモジュールの定数 1 つ（`PROHIBITED_ASSIGN_KEY_NAMES` 等）
- application の検査からも使うので presentation に置かない

### presentation: `keyseq/presentation/keyboard_window.py`

- 禁止の種類 `"prohibited"` の色を `set_key_color` に足す（灰色系・既存の 6 種類と区別できる。例 塗り `#e5e7eb` / 枠 `#9ca3af` / 文字 `#6b7280`）
- `redraw`: 枠のキー名（`_LOOKUP_KEY_BY_ID` を通した後）が禁止なら、種類が `normal` か `keymap` のときだけ `"prohibited"` にする（トリガー・停止 / トグル・切替〔`KM<n>`〕の色は優先）。文言は今のまま（既存の割り当ての送信先があれば出る）
- `_on_canvas_left_click`: 枠のキー名が禁止なら編集を始めずに `"break"`（別の枠を編集中ならその編集を続ける＝何も変えない）
- 右クリックのクリアは今のまま（禁止の枠でも割り当てを消せる）

### presentation: `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`

- `assign_keymap_from_keyboard_ui`（:606〜）: 元キーが禁止なら割り当てず、`messagebox.showerror("設定できません", "Windows キー・Caps Lock・AltGr はキーマップの元キーにできません。")` を出して False を返す（既存の拒否と同じ形・データは変えない）
- `validate_keymap_switch_assignment`（:166〜）: 先頭で、`key` が禁止 **かつ** `normalize_key_name(key) != normalize_key_name(exclude_switch_key)`（今の切替キーから変えたとき）なら
  `messagebox.showerror("設定できません", "Windows キー・Caps Lock・AltGr は切替キーにできません:\n{key}", parent=message_parent)` で False

### presentation: 切替キーの取得

- `dialogs/keymap_edit_dialog.py` `_on_capture_keypress`（:166〜）・`dialogs/keymap_switch_batch_dialog.py` `_on_capture_keypress`（:237〜）:
  取得したキー名が禁止なら（今の修飾キー単独の無視と同じく）`"break"` で無視して取得を続ける

### application: `keyseq/application/keymap_switch_batch.py`

- `validate_switch_batch`: 各行で、キーが禁止 **かつ** その行のキーマップの今の切替キー（`runtime["keymap_switch_keys"]` を逆に引いた `row_keymap_ids[index]` のキー。新しいキーマップの行は無し）と違うなら、
  `(index, "Windows キー・Caps Lock・AltGr は切替キーにできません:\n{key}")` を返す（既存の `_validate_row_key` の検査より前・同じ戻り値の形）

### テスト

- 新規 `tests/test_prohibited_assign_keys.py`: `is_prohibited_assign_key` の各表記（大文字・前後の空白を含む）が True / `ctrl`・`right alt`・`a`・空文字が False
- `tests/` の `validate_switch_batch` のテスト（既存のファイルへ追加）: 新しく `caps lock` / `caps_lock` / `left windows` / `alt gr` にした行がその行番号で拒否される / 今の切替キーが `caps lock` の行をそのままにすると通る
- 新規 `tests_ui/test_prohibited_assign_keys_ui.py`（App はクラスで共有・保存系はパッチ・作法 = `tests_ui/test_keyboard_window_left_right.py`）:
  1. キーボードUI の左右の Win・Caps の枠の種類が `"prohibited"`（描画の色で確かめる）。同じキーがトリガーのキーならトリガーの色
  2. 禁止の枠を左クリックしても `_editing_source_key` が変わらない（未編集なら None のまま・別の枠を編集中ならその枠のまま）
  3. 既存の `caps lock` の割り当ては文言が出て、右クリックで消える
  4. `assign_keymap_from_keyboard_ui("caps lock", "a")` が False でデータが変わらない（`messagebox.showerror` はパッチ）
  5. `validate_keymap_switch_assignment("caps lock", target_id=..., exclude_switch_key="")` が False / `exclude_switch_key="caps lock"` なら禁止では拒否しない
  6. キーマップの編集ダイアログ・まとめて設定ダイアログの取得中に Caps Lock（keysym `Caps_Lock`）を押しても値が入らず取得が続く
- 各テストは `addCleanup` で元へ戻す

## 読むファイル

1. `instructions/history/43_keyboard_ui_left_right_modifiers.md` §3.4・§3.5・§3.6
2. `keyseq/domain/key_identifiers.py`（全体）・`keyseq/domain/config.py:85-87`
3. `keyseq/presentation/keyboard_window.py`（全体）
4. `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:160-210,455-490,600-650`
5. `keyseq/presentation/dialogs/keymap_edit_dialog.py:150-180`・`keymap_switch_batch_dialog.py:210-250`
6. `keyseq/application/keymap_switch_batch.py`（全体）と既存のテスト（`tests/` の `keymap_switch_batch` を grep）
7. `tests_ui/test_keyboard_window_left_right.py`（作法）

## 含まない

- 標準の id `alt_gr`・`de.json`（task_03。禁止の集合の `alt gr` は本タスクで入れる）/ `jis.json`（task_04）
- トリガー・停止 / トグルキー・送信先での禁止 / 読込での検査 / 既存の割り当て・切替キーの自動の削除（暫定 43 §6）
- 正本反映（task_06）

## 確認

（実行は verifier・`.venv` python）
- `compileall -q keyseq main.py tests tests_ui` clean
- 新規・追加のテスト pass
- `unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` 全 pass（件数が減っていない）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_04 でまとめて実施
