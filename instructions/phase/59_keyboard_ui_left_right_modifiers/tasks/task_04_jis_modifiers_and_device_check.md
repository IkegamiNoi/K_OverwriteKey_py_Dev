# task_04_jis_modifiers_and_device_check

## 目的

`config/user/keylayout/jis.json` に左右の Ctrl・Alt・Windows の行を既定の id で足し（`scan_code` なし）、JIS 配列の実機でフェーズ全体（task_01〜03）を確かめる（暫定 43 §3.3・§5-8〜10）。
**見本のレイアウトファイル + テストのみ。コードは変えない。**

## 対象範囲

### `config/user/keylayout/jis.json`（最下段 y = 5.2・h 1.0・`scan_code` なし）

| id | label | x | w |
|---|---|---|---|
| ctrl_l | Ctrl | 0.0 | 1.0 |
| windows_l | Win | 1.0 | 1.0 |
| alt_l | Alt | 2.0 | 1.0 |
| alt_r | Alt | 10.5 | 1.0 |
| windows_r | Win | 11.5 | 1.0 |
| ctrl_r | Ctrl | 12.5 | 1.5 |

- 既存の行（無変換 x 3.0〜・スペース x 7.5〜10.5 等）は変えない。行の並びは同じ段の左から右へ（既存の最下段の行の前後に入れる）

### テスト（`tests/test_keyboard_layout_files.py`）

- 既存の de.json の 3 つの検査（読込・id の重複と矩形の重なり・修飾キー / Caps / Win / AltGr の行に `scan_code` が無い）を `jis.json` にも当てる（同じ検査を 2 つのファイルで回す形に直してよい。de.json の検査の内容は変えない）
- `jis.json` に `ctrl_l` / `ctrl_r` / `alt_l` / `alt_r` / `windows_l` / `windows_r` / `shift_l` / `shift_r` があること

## 読むファイル

1. `instructions/history/43_keyboard_ui_left_right_modifiers.md` §3.3
2. `config/user/keylayout/jis.json`（全体）
3. `tests/test_keyboard_layout_files.py`（全体）

## 含まない

- コードの変更・de.json の変更
- 統合確認（task_05）・正本反映（task_06）

## 確認

（実行は verifier・`.venv` python）
- `tests/test_keyboard_layout_files.py` pass・`unittest discover -s tests` 全 pass
- （コードを変えないため tests_ui・smoke は task_05 の統合確認で回す）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- **ユーザーの実機目視**（本タスクで実施・task_01〜03 の分を含む・JIS 配列・画面の枠は非表示）:
  1. キーボードUI のレイアウトを `jis.json` にして、左右の Ctrl・Alt・Shift の枠が別々に割り当てられ、右 Ctrl・右 Shift・右 Alt の割り当てがそのキーで効き、反対側では効かない。左の `ctrl` 等は従来どおり左で効く
  2. 左右の Win・Caps の枠が灰色（禁止）で、クリックしても編集が始まらない
  3. キーマップの編集ダイアログの「キー入力で取得」で Caps キーを単独 / Shift 付きで押しても切替キーにならない（JIS の Caps キーの名前が禁止の判定に当たるか）
  4. 右クリックで左右それぞれの割り当てだけが消える
