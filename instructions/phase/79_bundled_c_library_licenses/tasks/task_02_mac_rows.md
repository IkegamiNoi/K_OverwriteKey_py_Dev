# task_02_mac_rows

## 目的

Mac の配布物に入る C ライブラリを第三者ライセンスの表に載せる（暫定 60 §3・§4・§4.1・§6 Q2・Q3・Q5・§7 の 2〜6・8・9 の Mac 分）。**変更はデータ（`third_party.json`・全文の `.txt`）・テスト（`tests/test_third_party.py`）・手順書（`packaging/README.md` の macOS 節）に限る。`keyseq/` のコードと JSON の形は変えない。**

## 対象範囲（データ・テスト・手順書のみ）

### 全文の `.txt`（メインが配置済み・上流のファイルをそのまま写した物）

`keyseq/presentation/help/content/third_party/` に次を置いた（入手元は下の「棚卸しの記録」）。実装者は**中身を変えない**。OpenSSL は Windows の `openssl.txt` と同一（3.6.2 の `LICENSE.txt` と diff 一致）なので共有する。

`cpython_incorporated_macos.txt`・`libtommath.txt`・`mpdecimal_macos.txt`・`xz_macos.txt`

### `keyseq/presentation/help/content/third_party/third_party.json`

Mac の Python の行（`"name": "Python", "version": "3.13.18"`）の直後、Mac の Tcl の行の前に、次の 5 行をこの順で足す（暫定 60 §3 = 大文字小文字を無視した ABC 順）。すべて `"platforms": ["darwin"]`。他の行は変えない。

| name | version | license | file |
|---|---|---|---|
| CPython incorporated software | 3.13.18 | Various (see text) | cpython_incorporated_macos.txt |
| libtommath | 1.3.0 | The Unlicense | libtommath.txt |
| mpdecimal | 4.0.1 | BSD 2-Clause License | mpdecimal_macos.txt |
| OpenSSL | 3.6.2 | Apache License 2.0 | openssl.txt |
| xz | 5.8.4 | BSD Zero Clause License | xz_macos.txt |

### `tests/test_third_party.py`

1. `test_bundled_notices_are_complete_unique_and_ordered` の `mac_names` を、上の 5 行を `"Python"` と `"Tcl"` の間に入れた列へ更新する。`windows_names` は変えない。
2. `_NON_PYPI_NAMES` に `"libtommath"` を加える（他の 4 つは既にある）。
3. `test_c_library_versions_match_runtime` は変えない（Mac では OpenSSL・mpdecimal が照合され、expat は行が無いので skip・Zstandard は 3.13 に無いので対象外）。

### `packaging/README.md`（macOS 節）

`## macOS` の手順 4（配布するもの）の後に、出荷ごとの棚卸しの手順を手順 5 として 1 段落で足す（暫定 60 §4.1・Q4）。書くこと:
- `dist/keyseq.app/Contents` を再帰的にたどり、`.so`・`.dylib`・実行ファイル（`MacOS/keyseq`・`Python.framework` の `Python`）と `Resources/_tcl_data`・`_tk_data`・`tcl9` を一覧にし、各項目を `third_party.json` の行か表示しない理由に対応づける。対応づけられない物があれば出荷しない。
- 各 `.so`・`.dylib` を `otool -L` で見て、`/usr/lib` の物（zlib・bzip2・expat・libffi・libedit）は macOS の物で同梱されない（行にしない）と確かめる。同梱の dylib は `build/keyseq/Analysis-00.toc` か Homebrew の `/opt/homebrew/opt/<formula>/lib` の同名ファイルと `otool -t` の出力のハッシュを比べ（PyInstaller が署名と install name を書き換えるのでファイル全体のハッシュは一致しない）、一致すれば Homebrew の formula の版（`brew info`）を根拠にする。OpenSSL・mpdecimal は `tests/test_third_party.py` の照合も通す。表の版と合わなければ出荷しない。
- 拡張モジュールに静的に入る第三者のコードは Homebrew の Python の `config-3.13-darwin/Makefile`（`MODULE_*_CFLAGS` / `LDFLAGS`）と `nm` で確かめ（3.13.18 では `_md5`・`_sha1`・`_sha2`・`_sha3` に HACL*・`_blake2` に BLAKE2 の参照実装）、`Doc/license.rst` に無い物は `cpython_incorporated_macos.txt` の末尾に表示を足す。

### 設計メモ / 制約

- 全文に ` — ` を含めない（`tests_ui/test_help_window.py:255`）。配置済みの 4 ファイルは確認済み（0 件）。
- `keyseq/presentation/help/third_party.py` は変えない。
- 同じ `file` を OS をまたいで共有してよい（暫定 60 §3。`openssl.txt`・`tcl.txt`・`tk.txt`）。一覧のテストの重複検査は OS ごと。

## 読むファイル

1. `instructions/history/60_bundled_c_library_licenses.md` §3・§4・§4.1
2. `keyseq/presentation/help/content/third_party/third_party.json`（全体）
3. `tests/test_third_party.py`（全体・編集対象）
4. `packaging/README.md`（`## macOS` 節）

## 含まない

- Windows の行・`windows_names`・Windows 節（task_01 で完了）
- 正本 `features.md` の改訂・暫定 60 の凍結・`decisions_archive/79`（task_03）
- `third_party.py`・`tests_ui/test_help_window.py`・`.spec` の変更（暫定 60 §8）

## 確認

- `../../../.venv/bin/python -m compileall -q keyseq tests` が clean
- `../../../.venv/bin/python -m unittest tests.test_third_party -v` が pass（Mac で OpenSSL・mpdecimal の照合が pass・expat は skip）
- `tests` 全体（`unittest discover -s tests`）・`tests_ui` の `test_help_window`・`-m tests.smoke_app` が pass
- ライセンスの窓の目視（Mac・ユーザー）: 一覧に 21 行（既存 16 + 5）・各行の全文が出る

## 完了条件

- 上記確認 pass・**reviewer 採用**・実機目視（ユーザー）

---

## 棚卸しの記録（2026-11-24・メイン実測）

対象 = `dist/keyseq.app`（2026-11-24 にこの worktree〔コミット 7b1604b7〕で `packaging/macos/keyseq.spec` からビルド・`.venv` = Homebrew の Python 3.13.18・PyInstaller 6.22.3）。同梱の dylib 7 個と `Python.framework` の `Python`・拡張モジュール 51 個（`lib-dynload` と `_tkinter`）は、Homebrew のインストールの同名ファイルと `otool -t` の出力の SHA が一致（PyInstaller が署名と install name を書き換えるのでファイル全体ではなくコードの部分を比べた）。

| 配布物の項目 | 表示する行 / 表示しない理由 | 版の根拠 |
|---|---|---|
| `MacOS/keyseq` | PyInstaller（ブートローダ） | `requirements-build.txt` |
| `Frameworks/Python.framework/.../Python` | Python・CPython incorporated software（mimalloc・SipHash・dtoa ほか `Doc/license.rst` の物）。HACL*・BLAKE2 の記号は無い（`nm`） | Homebrew python@3.13 3.13.18 |
| `libcrypto.3.dylib`・`libssl.3.dylib`・`_ssl`・`_hashlib` | OpenSSL | 配布物の文字列 `OpenSSL 3.6.2 7 Apr 2026`・`opt/openssl@3` → Cellar 3.6.2 |
| `liblzma.5.dylib`・`_lzma` | xz（liblzma は 0BSD） | 配布物の文字列 `5.8.4`・Cellar xz 5.8.4 |
| `libmpdec.4.dylib`・`_decimal` | mpdecimal（`--with-system-libmpdec` = Homebrew の dylib） | 配布物の文字列 `4.0.1`・`MODULE__DECIMAL_LDFLAGS` = Cellar mpdecimal 4.0.1 |
| `libtommath.1.dylib` | libtommath（Unlicense・表示の義務なしだが別のファイルなので行を足す〔Q2・Q3〕。`libtcl9.1.dylib`・`libtcl9tk9.1.dylib` だけが読み込む = Homebrew の tcl-tk の依存・Q3） | tcl-tk の依存 = libtommath・Cellar 1.3.0 |
| `libtcl9.1.dylib`・`_tcl_data`・`tcl9`（`http`・`msgcat`・`platform`・`tcltest`・`tdbc/sqlite3` の `.tm`） | Tcl（`tcl.txt` は Cellar tcl-tk 9.1.0 の `license.terms` と diff 一致）。`_tcl_data/cookiejar0.2/public_suffix_list.dat.gz` は Mozilla の Public Suffix List（MPL 2.0・ファイルの先頭に MPL の表示があり、ソース形式のまま Tcl の配布物として入る。義務の判定 = 受け取った人に MPL が適用されることを知らせる義務はファイル自身の表示が果たす → `tcl.txt` に足さない・暫定 60 v0.8） | 配布物の文字列 `9.1.0` |
| `libtcl9tk9.1.dylib`・`_tk_data`・`_tkinter` | Tk / Python。`libtcl9tk9.1.dylib` に NanoSVG（Mikko Mononen・zlib License・SVG の画像の読み込み・`nm` で `nsvg` 63 個）が静的に入る。義務の判定 = zlib License はバイナリでの表示を求めない → `tk.txt` に足さない（暫定 60 v0.8）。task_03 の deep-reviewer の指摘で追記 | 配布物の文字列 `9.1.0` |
| `_md5`・`_sha1`・`_sha2`・`_sha3` | CPython incorporated software（HACL*。`Makefile` の `-I Modules/_hacl`・`nm` に `Hacl_*`） | Python 3.13.18 |
| `_blake2` | CPython incorporated software（BLAKE2 の参照実装・CC0。`Modules/_blake2/impl`・`Doc/license.rst` に無い） | Python 3.13.18 |
| `zlib`・`binascii`・`_bz2`・`pyexpat`・`_ctypes`・`readline`・`_objc`・`MacOS/keyseq` が参照する `/usr/lib` の libz・libbz2・libexpat・libffi・libedit | 行にしない（macOS の物で同梱されない・`otool -L`） | — |
| 他の `lib-dynload` の `.so`（`_asyncio`・`_codecs_*`・`_json`・`_socket`・`unicodedata` ほか） | Python（第三者のコードを含まない CPython の標準モジュール） | Python 3.13.18 |
| `AppKit`・`CoreFoundation`・`CoreText`・`Foundation`・`HIServices`・`Quartz`・`objc` の `.so` | pyobjc | 既存の行 |
| `Resources/keyseq`・`config`・`pynput`・`rubicon_objc-0.5.7.dist-info`・`base_library.zip`・`LICENSE`・`icon-windowed.icns`・`dist/README.txt`・`dist/sources` | 本体・Python のパッケージの既存の行 | — |

全文の入手元（すべて実測した版のファイルをそのまま写した）:
OpenSSL = Cellar openssl@3 3.6.2 の `LICENSE.txt`（`openssl.txt` と同一）/ xz = Cellar xz 5.8.4 の `COPYING` + `COPYING.0BSD`（liblzma の許諾文）/ mpdecimal = Cellar mpdecimal 4.0.1 の `COPYRIGHT.txt`（4.0.0 と年だけ違う）/ libtommath = Cellar libtommath 1.3.0 の `LICENSE` / CPython incorporated software = python/cpython `v3.13.18` の `Doc/license.rst`「Licenses and Acknowledgements for Incorporated Software」節から末尾まで + 末尾に HACL*（`Modules/_hacl/Hacl_Hash_SHA2.c` の先頭の MIT 表示・Windows と同じ文）と BLAKE2（`Modules/_blake2/impl/blake2b.c` の先頭の CC0 表示）。

## 実施結果（2026-11-24）

- 実装: codex-implementer（Luna high）= JSON の 5 行・`mac_names`・`_NON_PYPI_NAMES`・README の macOS 手順 5。全文 4 ファイルはメインが配置（`cpython_incorporated_macos.txt` の `license.rst` の部分は v3.13.18 の原本と diff 一致）。
- reviewer: 採用（全文 4 ファイルを Cellar の原本と diff 一致・dylib 7 個と記録が過不足なく対応）。
- verifier: compileall clean / `tests.test_third_party` 8 件 OK（skip 1 = expat の subTest・Mac に行が無い）/ `tests` 2217 件 OK（skip 33）/ `tests_ui.test_help_window` 25 件 OK / smoke OK。
- 実機目視（ユーザー・2026-11-24）: OK（再ビルドした `dist/keyseq.app` のライセンスの窓に 21 行・各全文。最初のビルドは表の変更前だったため再ビルドした）。→ task_02 完了。

### 追記（2026-11-24・暫定 60 v0.9・ユーザー判断「窓に載せるのは表示の義務がある物だけ」）

上の表のうち、次は**行を外し、記録だけにした**（task_02b）。義務の判定: xz 5.8.4（`liblzma.5.dylib`・0BSD = 表示の条件なし）・libtommath 1.3.0（`libtommath.1.dylib`・Unlicense = パブリックドメイン）・BLAKE2（`_blake2`・CC0）→ 義務なし。全文 `xz_macos.txt`・`libtommath.txt` は削除し、`cpython_incorporated_macos.txt` の BLAKE2 の節を外した（HACL* は残す）。Mac の窓は 19 行。
