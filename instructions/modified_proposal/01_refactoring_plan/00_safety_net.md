# 項目0 申し送り

- 計画書は `py` ランチャ前提だが、この実行環境では `py` / `python` / `python3` が PATH に無かった。
- unittest / import の検証は Codex バンドル Python `C:\Users\hima_\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` で代替できる。
- `tests/smoke_app.py` は Codex バンドル Python の Tcl/Tk が壊れているため、Tk が動く `D:\AI\StabilityMatrix\Data\Assets\Python\cpython-3.12.10-windows-x86_64-none\python.exe` で実行する。
- smoke 実行時は `PYTHONPATH=.;C:\Users\hima_\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages` を付ける。
- `keyseq.presentation.app` の import に必要な `keyboard` / `pyautogui` / `pynput` が未導入だったため、バンドル Python に pip install 済み。
- ベースラインの `compileall` と `import keyseq.presentation.app` は、依存導入後に成功確認済み。
- 項目0追加後の `compileall` / unittest 50件 / smoke は上記代替コマンドで成功確認済み。
