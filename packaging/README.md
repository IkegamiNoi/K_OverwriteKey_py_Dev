# 配布ビルド

## Windows

リポジトリ直下で次の順に実行します。

1. `.venv` にビルド依存を入れます: `python -m pip install -r packaging/requirements-build.txt`
2. ソースアーカイブ（sdist）を `packaging/sources/` に取得します。まず `pip download --no-binary :all: --no-deps mouseinfo==0.1.3 pynput==1.8.2 -d packaging/sources` を試します。
   - 2026-11-18 の取得（0.1.3 / 1.8.2）では、Python 3.14 で sdist の metadata の生成が止まり進まなかったため、PyPI の各版のページ（`https://pypi.org/project/<名前>/<版>/#files`）の Source Distribution を直接取得し、ページの SHA256 と照合しました。
   - ファイル名は全体が `<名前>-<版>.tar.gz` か `.zip` であること（例 `MouseInfo-0.1.3.tar.gz`・`pynput-1.8.2.tar.gz`。大文字小文字は問わない。`.sha256` などは数えない）。`.spec` はこの名前で有無を検査し、無ければビルドを止めます。`dist/keyseq/sources/` は毎回空にして、一致したアーカイブだけを入れます。
3. `python -m PyInstaller packaging/windows/keyseq.spec` を実行します。
4. `build/keyseq/warn-keyseq.txt` と `build/keyseq/xref-keyseq.html` の収集結果を確認し、同梱依存を `third_party.json` の表と照合します。
5. 出荷ごとに `dist/keyseq/` を再帰的に棚卸しし、`.dll`・`.pyd`・`.exe` と `_internal/_tcl_data`・`_tk_data`・`tcl8` を一覧にして、各項目を `third_party.json` の行または表示しない理由（バイナリで配るときの表示の義務が無い物は行にせず、ライセンスと義務の判定を記録する）に対応づけます。対応づけられない項目があれば出荷しません。DLL・pyd は CPython のインストール先（`sys.base_prefix` と `DLLs`）にある同名ファイルとハッシュを比較し、一致する場合は CPython のその版のタグにある `PCbuild/get_externals.bat` を版の根拠にします。OpenSSL・Zstandard・mpdecimal・expat は `tests/test_third_party.py` の照合も通し、表の版と合わなければ出荷しません。Python 本体に組み込まれた第三者コードは、その版の `PCbuild/pythoncore.vcxproj` で確認し、`Doc/license.rst` に記載のないものは `cpython_incorporated.txt` の末尾に表示を追加します。拡張モジュール（`_zstd` など）に静的に入るライブラリは、その `PCbuild/<モジュール>.vcxproj` が取り込むソースの先頭の著作権表示を確かめ、ライブラリの LICENSE に無い表示があれば全文の末尾に足します（例: `zstandard.txt` の xxHash・threading・divsufsort）。`tcl86t.dll`・`tk86t.dll` に静的に入るコードと `_tcl_data`・`_tk_data` の中の第三者のファイル（例: libtommath・`cookiejar` の Public Suffix List）は、ライセンスを確かめて Tcl / Tk の行に対応づけ、バイナリで配るときの表示の義務がある物だけ `tcl.txt` / `tk.txt` に足します。結果（一覧・対応づけ・版の根拠・義務の判定）は `packaging/inventory/<版>.md` の Windows の節に残します。
6. 配布する版のタグ `v<版>` を作成し、push します。

依存の版を上げる場合は `requirements-build.txt`、`third_party.json`、`sources/` の版を揃えてください。任意の Windows アイコンは `packaging/windows/keyseq.ico` に配置します。

## macOS

Homebrew の Python 3.13 と `python-tk@3.13` を使います。

1. `.venv` にビルド依存を入れます: `python -m pip install -r packaging/requirements-build.txt`
2. `packaging/sources/` に mouseinfo 0.1.3 と pynput 1.8.2 のソースアーカイブを取得します: `pip download --no-binary :all: --no-deps mouseinfo==0.1.3 pynput==1.8.2 -d packaging/sources`（2026-11-22 の取得では Python 3.13 でそのまま通りました）。 macOS の `.spec` は、ファイル名全体が `<名前>-<版>.tar.gz` か `.zip` と一致するもの（大文字小文字は問わない）だけを同梱し、無ければビルドを止めます（`.sha256` などは数えません）。
3. リポジトリ直下で `python -m PyInstaller packaging/macos/keyseq.spec` を実行します。
4. 配布するものは `dist/keyseq.app`・`dist/README.txt`・`dist/sources/` です。`dist/keyseq/` は中間生成物なので配布しません。zip は毎回空のフォルダに 3 点を揃えてから作ります（前のビルドのファイルを混ぜないため）。例: `rm -rf dist/keyseq-macos && mkdir dist/keyseq-macos && ditto dist/keyseq.app dist/keyseq-macos/keyseq.app && cp dist/README.txt dist/keyseq-macos/ && ditto dist/sources dist/keyseq-macos/sources && ditto -c -k --keepParent dist/keyseq-macos keyseq-macos.zip`。作った zip は空のフォルダに展開し、3 点が揃っていることと、`codesign --verify --deep --strict keyseq-macos/keyseq.app` が通ることを確かめてください。
5. 出荷ごとに `dist/keyseq.app/Contents` を再帰的に棚卸しし、`.so`・`.dylib`・実行ファイル（`MacOS/keyseq`・`Python.framework` の `Python`）と `Resources/_tcl_data`・`_tk_data`・`tcl9` を一覧にして、各項目を `third_party.json` の行または表示しない理由（バイナリで配るときの表示の義務が無い物は行にせず、ライセンスと義務の判定を記録する）に対応づけます。対応づけられない物があれば出荷しません。各 `.so`・`.dylib` は `otool -L` で確認し、`/usr/lib` の物（zlib・bzip2・expat・libffi・libedit）は macOS の物で同梱されないため行にしないことを確かめます。同梱の dylib の版は、まず配布物の中の版の文字列（`strings` で `OpenSSL 3.x.y`・liblzma の `5.x.y` など）で確かめます。そのうえで `build/keyseq/Analysis-00.toc` または Homebrew の `/opt/homebrew/opt/<formula>/lib` にある同名ファイルと `otool -tX` の出力（`-X` でファイルのパスの見出しを出さない）のハッシュを比べ（PyInstaller が署名と install name を書き換えるため、ファイル全体のハッシュは一致しません）、一致したら Homebrew formula の版（`brew info`）を補いの根拠にします。OpenSSL・mpdecimal は `tests/test_third_party.py` の照合も通します。表の版と合わなければ出荷しません。拡張モジュールに静的に入る第三者コードは Homebrew Python の `config-3.13-darwin/Makefile`（`MODULE_*_CFLAGS` / `LDFLAGS`）と `nm` で確かめます（3.13.18 では `_md5`・`_sha1`・`_sha2`・`_sha3` に HACL*、`_blake2` に BLAKE2 の参照実装があります）。`Doc/license.rst` に無い物は `cpython_incorporated_macos.txt` の末尾に表示を足します。`libtcl9.1.dylib`・`libtcl9tk9.1.dylib` に静的に入るコード（`nm` で確かめる。例: Tk の NanoSVG）と `Resources/_tcl_data`・`_tk_data`・`tcl9` の中の第三者のファイル（例: `cookiejar0.2/public_suffix_list.dat.gz` の Public Suffix List）は、ライセンスを確かめて Tcl / Tk の行に対応づけ、バイナリで配るときの表示の義務がある物だけ `tcl.txt` / `tk.txt` に足します（Mac と Windows で中身が違うなら `*_macos.txt` に分けます）。結果（一覧・対応づけ・版の根拠・義務の判定）は `packaging/inventory/<版>.md` の macOS の節に残します。

再ビルドすると署名が変わり、アクセシビリティの一覧の keyseq がオンのままでも効かなくなります（「開始」で権限の案内が出続ける・2026-11-22 に実測）。keyseq を終了し、`tccutil reset Accessibility io.github.ikegaminoi.keyseq`（または一覧で「−」）で消してから、起動し直して許可し直してください。要る許可はアクセシビリティだけです。任意のアイコンは `packaging/macos/keyseq.icns` に置きます。

依存の版を上げたら `requirements-build.txt`、`third_party.json`、`sources/`、Windows と macOS の 2 つの `.spec` の `SOURCE_PACKAGES` を揃えてください。bundle identifier `io.github.ikegaminoi.keyseq` は変更しないでください。権限は識別子と署名に結びつくため、変更すると再許可が必要になります。
