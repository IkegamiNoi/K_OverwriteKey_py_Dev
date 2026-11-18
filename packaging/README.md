# Windows 配布ビルド

リポジトリ直下で次の順に実行します。

1. `.venv` にビルド依存を入れます: `python -m pip install -r packaging/requirements-build.txt`
2. ソースアーカイブ（sdist）を `packaging/sources/` に取得します。まず `pip download --no-binary :all: --no-deps mouseinfo==0.1.3 pynput==1.8.2 -d packaging/sources` を試します。
   - 2026-11-18 の取得（0.1.3 / 1.8.2）では、Python 3.14 で sdist の metadata の生成が止まり進まなかったため、PyPI の各版のページ（`https://pypi.org/project/<名前>/<版>/#files`）の Source Distribution を直接取得し、ページの SHA256 と照合しました。
   - ファイル名は `<名前>-<版>.` で始まること（例 `MouseInfo-0.1.3.tar.gz`・`pynput-1.8.2.tar.gz`。大文字小文字は問わない）。`.spec` はこの名前で有無を検査し、無ければビルドを止めます。
3. `python -m PyInstaller packaging/windows/keyseq.spec` を実行します。
4. `build/keyseq/warn-keyseq.txt` と `build/keyseq/xref-keyseq.html` の収集結果を確認し、同梱依存を `third_party.json` の表と照合します。
5. 配布する版のタグ `v<版>` を作成し、push します。

依存の版を上げる場合は `requirements-build.txt`、`third_party.json`、`sources/` の版を揃えてください。任意の Windows アイコンは `packaging/windows/keyseq.ico` に配置します。
