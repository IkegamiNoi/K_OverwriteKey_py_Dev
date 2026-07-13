# 項目0 環境メモ（申し送り）

- 作成日: 2026-07-05
- ベースライン HEAD: `9dcaa7dded28f93f5ab28b439b86c732914f2999`
- 実行ブランチ: この worktree の作業ブランチ（`claude/goofy-mclaren-c2b4bb`）上で作業する。
  計画書は `git switch -c refactor/02-app-split` を指示しているが、本作業は既に専用 worktree
  ブランチ上にあるため、そのままこのブランチに 1 項目 = 1 コミットで積む。

## 計画01 完了確認（すべて期待どおり）
- R1 `class ActionDialog` in views.py: 0 件 ✓
- R5 `chain` in keyseq: 0 件 ✓
- R11 `def _save_keymap_set_to` in app.py: 1 件 ✓
- R12 `def _sync_control_vars_from_data` in app.py: 1 件 ✓
- R14 `def slugify_file_stem` in config_service.py: 1 件 ✓
- R7 `def normalize_tk_keysym` in tk_keys.py: 1 件 ✓
- `py -m unittest discover -s tests`: 50 tests OK ✓

## Python 実行環境の注意（重要）
- 既定の `py` ランチャは Python 3.14.5（`C:\Users\hima_\AppData\Local\Python\pythoncore-3.14-64`）。
- この 3.14 環境には GUI 依存（pynput / keyboard / PyAutoGUI 一式）が未導入だったため、
  項目0で以下を pip 導入した（**プロジェクト依存の追加ではなく、実行環境への既存ランタイム依存の導入**）:
  - pynput 1.8.2, keyboard 0.13.5, six 1.17.0
  - PyAutoGUI 0.9.54 一式（MouseInfo, PyGetWindow, PyMsgBox, pyperclip, PyRect, PyScreeze, pytweening）
  - バージョンは動作中の別 venv（リポジトリ親の `.venv` / Python 3.12）の freeze に合わせた。
- **PYTHONPATH**: `py tests/smoke_app.py` を素で実行するとリポジトリ root が sys.path に無く
  `ModuleNotFoundError: No module named 'keyseq'` になる。これは既存の環境事情。
  本作業では GUI 系検証を次の形で実行する:
  - PowerShell: `$env:PYTHONPATH="."; py tests/smoke_app.py`
  - Bash: `PYTHONPATH=. py tests/smoke_app.py`
  - `py -m unittest discover -s tests` / `-s tests_ui` は root から実行すれば OK。

## 標準検証コマンド（本作業での実体）
```
py -m compileall -q keyseq main.py
py -m unittest discover -s tests -v
$env:PYTHONPATH="."; py -m unittest discover -s tests_ui -v
$env:PYTHONPATH="."; py tests/smoke_app.py
```
