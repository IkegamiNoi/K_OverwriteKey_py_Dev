# task_01_extra_scan_codes

## 目的

レイアウトの行に、受け取り専用の任意キー `extra_scan_codes` を書けるようにする（暫定 46 §4）。jis.json の無変換に 241、変換に 242 を足す。
**presentation 限定 + 見本 JSON**。送信・domain・application・infrastructure は不変。

## 対象範囲（presentation 限定 + 見本 JSON）

phase 62 で戻した `722a1e9` の 5 ファイル分の差分を、そのまま当て直す（`git show 722a1e9 -- config/user/keylayout/jis.json keyseq tests | git apply --3way`）。
内容は phase 62 の task_03b（`instructions/phase/62_special_keys_from_layout_only/tasks/task_03b_extra_scan_codes.md`）の「対象範囲」と同じで、暫定 46 §4 と一致する。

- `keyseq/presentation/keyboard_layouts.py`
  - `KeySpec.extra_scan_codes`
  - 読込の検証
  - 受け取りの照合（行の順、行ごとに `scan_code` → `extra_scan_codes`）
- `keyseq/presentation/controllers/layout_controller.py`: デバッグ出力の判定に `extra_scan_codes` を含める
- `config/user/keylayout/jis.json`: `muhenkan` に `[241]`、`henkan` に `[242]`
- テスト: `tests/test_keyboard_layout_files.py`・`tests/test_layout_controller_scan_code.py`

Codex 指摘 2 件（修飾キー等の行に書かない・受け取り専用の行の送信）は規定のみで、コードは変えない（送信側の `resolve_layout_scan_code_from_key_name` は `extra_scan_codes` を使わないまま）。

## 読むファイル

1. 暫定 46 §4
2. `git show 722a1e9`（当て直す差分）

## 含まない

- 押下だけのキーの組み直し（task_02・task_03）
- 正本反映（task_04）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_keyboard_layout_files tests.test_layout_controller_scan_code` が全 pass
- 既存テストが全 pass: `unittest discover -s tests` / `unittest discover -s tests_ui` / `-m tests.smoke_app`

## 完了条件

- 上記の確認が pass し、**reviewer が採用**していること
- 実機目視は task_03 でまとめて行う
  - 単独では、無変換・変換の受け取りで二重送信が起きる。phase 62 の task_03b と同じ状態で、task_03 で直す
