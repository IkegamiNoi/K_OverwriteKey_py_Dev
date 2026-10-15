# task_03_alt_gr_id_and_de_layout

## 目的

AltGr 配列のレイアウトが右 Alt を書き分けるための標準の id `alt_gr`（キー名 `alt gr`・割り当て禁止）を足し、ドイツ語配列（QWERTZ）の見本のレイアウト `config/user/keylayout/de.json` を同梱する（暫定 43 §3.1・§3.6・§5-11）。
**presentation（キーボードUI の対応表）+ 見本のレイアウトファイル + テスト。入力の経路・レイアウト JSON の書式・読込は変えない。**

## 対象範囲

### `keyseq/presentation/keyboard_window.py`

- `_LOOKUP_KEY_BY_ID` に `"alt_gr": "alt gr"` を 1 行足す（禁止の色・左クリックで編集しないは task_02 の `is_prohibited_assign_key` でそのまま効く）

### 新規 `config/user/keylayout/de.json`

`jis.json` と同じ書式（`layout_id` / `display_name` / `keys`）。`layout_id` = `de`・`display_name` = `Deutsch (QWERTZ)`。キーは次のとおり（h はすべて 1.0。Enter だけ h 2.0。**修飾キー・Caps・Win・AltGr の行に `scan_code` を書かない**）:

| id | label | x | y | w |
|---|---|---|---|---|
| esc | Esc | 0.0 | 0.0 | 1.0 |
| f1 | F1 | 2.0 | 0.0 | 1.0 |
| f2 | F2 | 3.0 | 0.0 | 1.0 |
| 1 | 1 | 1.0 | 1.2 | 1.0 |
| 2 | 2 | 2.0 | 1.2 | 1.0 |
| tab | Tab | 0.0 | 2.2 | 1.5 |
| q | Q | 1.5 | 2.2 | 1.0 |
| w | W | 2.5 | 2.2 | 1.0 |
| e | E | 3.5 | 2.2 | 1.0 |
| r | R | 4.5 | 2.2 | 1.0 |
| t | T | 5.5 | 2.2 | 1.0 |
| z | Z | 6.5 | 2.2 | 1.0 |
| enter | Enter | 12.0 | 2.2 | 2.0（h 2.0） |
| caps_lock | Caps | 0.0 | 3.2 | 1.75 |
| a | A | 1.75 | 3.2 | 1.0 |
| shift_l | Shift | 0.0 | 4.2 | 2.25 |
| y | Y | 2.25 | 4.2 | 1.0 |
| shift_r | Shift | 11.0 | 4.2 | 2.75 |
| ctrl_l | Ctrl | 0.0 | 5.2 | 1.25 |
| windows_l | Win | 1.25 | 5.2 | 1.25 |
| alt_l | Alt | 2.5 | 5.2 | 1.25 |
| space | Space | 3.75 | 5.2 | 6.25 |
| alt_gr | AltGr | 10.0 | 5.2 | 1.25 |
| windows_r | Win | 11.25 | 5.2 | 1.25 |
| ctrl_r | Ctrl | 12.5 | 5.2 | 1.5 |

- `jis.json` は変えない（task_04）

### テスト

- `tests/`（既存のレイアウトのテストがあればそこ・無ければ新規 `tests/test_keyboard_layout_files.py`）:
  1. `config/user/keylayout/de.json` を `keyboard_layouts.load_layout_from_json` で読み込める・`layout_id` が `de`・`alt_gr` の行がある
  2. id が重複しない・どの 2 つのキーの矩形も重ならない（同じ y の行で x の区間が重ならない。Enter の h 2.0 も考慮）
  3. id が `shift_*` / `ctrl_*` / `alt_*` / `windows_*` / `caps_lock` / `alt_gr` の行は `scan_code` を持たない
- `tests/test_input_router.py` に追加: 走査コード 541・名前 `alt gr` のイベント（既存のテストの作法で偽のイベントを作る）を渡すと入力のキー名が `alt gr` になる（レイアウトの解決では何も返らない）
- `tests_ui/test_prohibited_assign_keys_ui.py`（task_02）に追加: キーボードUI に `de.json` のレイアウトを当てると（既存のレイアウトの切り替えの作法・登録はテストの中だけ・config を書かない）
  `alt_gr` の枠のキー名が `alt gr` で禁止の色・左クリックで編集しない / `alt_r` が無いので `right alt` の枠は無い

## 読むファイル

1. `instructions/history/43_keyboard_ui_left_right_modifiers.md` §3.1・§3.3・§3.6
2. `keyseq/presentation/keyboard_window.py:20-50`
3. `keyseq/presentation/keyboard_layouts.py:180-300`（読込・検証）
4. `config/user/keylayout/jis.json`（書式）
5. `tests/test_input_router.py`（偽のイベントの作法）・`tests_ui/test_prohibited_assign_keys_ui.py`（作法）
6. `keyseq/presentation/controllers/layout_controller.py` のレイアウトの切り替え（テストで de を当てる方法を探すため・grep で該当箇所だけ）

## 含まない

- `jis.json` の左右の修飾キーの追加と実機目視（task_04）
- 入力配列の判定 / AltGr 配列の実機確認（暫定 43 §6）
- 正本反映（task_06）

## 確認

（実行は verifier・`.venv` python）
- `compileall -q keyseq main.py tests tests_ui` clean
- 追加のテスト pass
- `unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` 全 pass（件数が減っていない）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- AltGr 配列の実機確認はしない（未確認として記録・暫定 43 §2）
