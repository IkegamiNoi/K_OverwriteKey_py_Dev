# task_01_windows_rows

## 目的

Windows の配布物に入る C ライブラリを第三者ライセンスの表に載せる（暫定 60 §3・§4・§4.1・§6 Q1〜Q5・§7 の 1・3〜10 の Windows 分）。**変更はデータ（`third_party.json`・全文の `.txt`）・テスト（`tests/test_third_party.py`）・手順書（`packaging/README.md` の Windows 節）に限る。`keyseq/` のコードと JSON の形は変えない。**

## 対象範囲（データ・テスト・手順書のみ）

### 全文の `.txt`（メインが配置済み・上流のファイルをそのまま写した物）

`keyseq/presentation/help/content/third_party/` に次を置いた（入手元は下の「棚卸しの記録」の表）。実装者は**中身を変えない**。

`bzip2.txt`・`cpython_incorporated.txt`・`expat.txt`・`libffi.txt`・`mpdecimal.txt`・`openssl.txt`・`xz.txt`・`zlib.txt`・`zlib-ng.txt`・`zstandard.txt`

### `keyseq/presentation/help/content/third_party/third_party.json`

Windows の Python の行（`"name": "Python", "version": "3.14.6"`）の直後、Tcl の行の前に、次の 10 行をこの順で足す（暫定 60 §3 = 大文字小文字を無視した ABC 順）。すべて `"platforms": ["win32"]`。他の行は変えない。

| name | version | license | file |
|---|---|---|---|
| bzip2 | 1.0.8 | bzip2 License | bzip2.txt |
| CPython incorporated software | 3.14.6 | Various (see text) | cpython_incorporated.txt |
| expat | 2.8.1 | MIT License | expat.txt |
| libffi | 3.4.4 | MIT License | libffi.txt |
| mpdecimal | 4.0.0 | BSD 2-Clause License | mpdecimal.txt |
| OpenSSL | 3.5.7 | Apache License 2.0 | openssl.txt |
| xz | 5.2.5 | Public Domain | xz.txt |
| zlib | 1.3.1 | zlib License | zlib.txt |
| zlib-ng | 2.2.4 | zlib License | zlib-ng.txt |
| Zstandard | 1.5.7 | BSD 3-Clause License | zstandard.txt |

### `tests/test_third_party.py`

1. `test_bundled_notices_are_complete_unique_and_ordered`（:21-39）の `windows_names` を、上の 10 行を `"Python"` と `"Tcl"` の間に入れた列へ更新する。`mac_names` は変えない（task_02）。
2. `test_library_versions_match_installed_distributions`（:41-53）の除外（:45 の `{"Python", "Tcl", "Tk"}`）に、C ライブラリの行の名前（上の 10 行の name）を加える。名前の集合はモジュール定数（例 `_NON_PYPI_NAMES`）にしてよい。Mac の行（task_02 で足す libtommath 等）は task_02 で加える。
3. 新しいテスト `test_c_library_versions_match_runtime` を足す。形は `test_python_tcl_and_tk_versions_match_runtime`（:55-73）にそろえる（`load_third_party()` で実行中の OS の行を取り、名前で引く）。照合する物と比べ方:
   - `OpenSSL`: `ssl.OPENSSL_VERSION` の 2 語目（例 `"OpenSSL 3.5.7 9 Jun 2026"` → `"3.5.7"`）
   - `Zstandard`: `compression.zstd.zstd_version`（`compression.zstd` を import できない Python ではこの項目だけ skip）
   - `mpdecimal`: `_decimal.__libmpdec_version__`（`decimal` の属性は使わない。`_decimal` を import できなければ失敗にする）
   - `expat`: `pyexpat.EXPAT_VERSION` の `expat_` を除いた部分（例 `"expat_2.8.1"` → `"2.8.1"`）
   - 実行中の OS に行が無い名前は、その項目だけ `subTest` 内で skip する（Mac の行は task_02 で入る）。
   - 照合しない物（libffi・zlib-ng・zlib・bzip2・xz・CPython incorporated software）はテストに書かない。

### `packaging/README.md`（Windows 節）

`## Windows` の手順 4（収集結果の照合）の後に、出荷ごとの棚卸しの手順を 1 段落で足す（暫定 60 §4.1・Q4）。書くこと:
- `dist/keyseq/` を再帰的にたどり、`.dll`・`.pyd`・`.exe` と `_internal/_tcl_data`・`_tk_data`・`tcl8` を一覧にし、各項目を `third_party.json` の行か表示しない理由に対応づける。対応づけられない物があれば出荷しない。
- DLL・pyd は CPython のインストール先（`sys.base_prefix` と `DLLs`）の同名ファイルとハッシュを比べ、同じなら CPython の `PCbuild/get_externals.bat`（その版のタグ）の版を根拠にする。`OpenSSL`・`Zstandard`・`mpdecimal`・`expat` は `tests/test_third_party.py` の照合も通す。表の版と合わなければ出荷しない。
- Python の本体に組み込まれた第三者のコードは `PCbuild/pythoncore.vcxproj`（その版）で確かめ、`Doc/license.rst` に無い物は `cpython_incorporated.txt` の末尾に表示を足す。

### 設計メモ / 制約

- 全文に ` — ` を含めない（`tests_ui/test_help_window.py:255` が件数をこの文字列で数える）。配置済みの 10 ファイルは確認済み（0 件）。
- `keyseq/presentation/help/third_party.py` は変えない（追加のキーは拒否される・`platforms` は既存のまま使える）。

## 読むファイル

1. `instructions/history/60_bundled_c_library_licenses.md` §3・§4・§4.1
2. `keyseq/presentation/help/content/third_party/third_party.json`（全体）
3. `tests/test_third_party.py`（全体・編集対象）
4. `packaging/README.md`（`## Windows` 節・L3〜16）

## 含まない

- Mac の行・全文・`mac_names`・macOS 節（task_02）
- 正本 `features.md` の改訂・暫定 60 の凍結・`decisions_archive/79`（task_03）
- `third_party.py`・`tests_ui/test_help_window.py`・`.spec` の変更（暫定 60 §8）
- VC++ ランタイムの行（Q1 で行にしない）。再頒布の条件の判断は下の記録とユーザー確認で扱う

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_third_party -v` が pass（新しい照合 4 項目が Windows で pass・skip 無し〔Zstandard は 3.14 で import できる〕）
- `tests` 全体（`unittest discover -s tests`）・`tests_ui` の `test_help_window`・`-m tests.smoke_app` が pass
- ライセンスの窓の目視（Windows・ユーザー）: 一覧に 25 行（既存 15 + 10）・各行の全文が出る

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は本タスクで実施（ユーザー）
- 受け入れ条件 10（VC++）は下の記録のとおり**未解決 = Windows 版は出荷停止**とし、ユーザーの判断を仰ぐ（判断と対応はこのタスクの完了とは切り離し、出荷前に済ませる）

---

## 棚卸しの記録（2026-11-24・メイン実測）

対象 = `dist/keyseq/`（2026-11-22 のビルド・コミット 20bd231a・`.venv` = Python 3.14.6・PyInstaller 6.22.3。C ライブラリは CPython のインストールのまま）。`_internal` の DLL・pyd 26 個はすべて CPython のインストール先（`C:\Users\ikega\AppData\Local\Python\pythoncore-3.14-64` と `DLLs`）の同名ファイルと SHA-256 が一致。

| 配布物の項目 | 表示する行 / 表示しない理由 | 版の根拠 |
|---|---|---|
| `keyseq.exe` | PyInstaller（ブートローダ） | `requirements-build.txt` |
| `python314.dll` | Python・CPython incorporated software（mimalloc・HACL* ほか）・zlib-ng（静的・`zlib` はビルトイン） | Python 3.14.6 / `PCbuild/pythoncore.vcxproj`（v3.14.6）に `Modules\_hacl\*.c` と `zlib-ng.lib`・`get_externals.bat` = zlib-ng-2.2.4 |
| `libcrypto-3.dll`・`libssl-3.dll`・`_ssl.pyd`・`_hashlib.pyd` | OpenSSL | FileVersion 3.5.7・`get_externals.bat` = openssl-bin-3.5.7 |
| `libffi-8.dll`・`_ctypes.pyd` | libffi | `get_externals.bat` = libffi-3.4.4 |
| `zlib1.dll` | zlib（`tcl86t.dll` だけが読み込む・Tcl 用） | FileVersion 1.3.1 |
| `_bz2.pyd` | bzip2（静的） | `get_externals.bat` = bzip2-1.0.8 |
| `_lzma.pyd` | xz（静的・liblzma 5.2.5 はパブリックドメイン） | `get_externals.bat` = xz-5.2.5 |
| `_zstd.pyd` | Zstandard（静的） | `get_externals.bat` = zstd-1.5.7・`compression.zstd.zstd_version` |
| `_decimal.pyd` | mpdecimal（静的） | `get_externals.bat` = mpdecimal-4.0.0・`_decimal.__libmpdec_version__` |
| `pyexpat.pyd` | expat（静的・`Modules/expat`） | `pyexpat.EXPAT_VERSION` = expat_2.8.1 |
| `tcl86t.dll`・`_tcl_data`・`tcl8` | Tcl（libtommath 等は Tcl の DLL に静的・Q3）。`_tcl_data/tzdata` は IANA の tz データ（パブリックドメイン） | FileVersion 8.6.15 |
| `tk86t.dll`・`_tk_data`・`_tkinter.pyd` | Tk / Python | FileVersion 8.6.15 |
| `VCRUNTIME140.dll`・`VCRUNTIME140_1.dll` | 行にしない（Q1）。条件は下 | FileVersion 14.42.34438.0 |
| 他の `.pyd`（`_asyncio`・`_multiprocessing`・`_overlapped`・`_queue`・`_socket`・`_wmi`・`select`・`unicodedata`） | Python（第三者のコードを含まない CPython の標準モジュール） | Python 3.14.6 |
| `_internal/keyseq`・`config`・`pynput`・`base_library.zip`・`LICENSE`・`sources`・`README.txt` | 本体・Python のパッケージの既存の行 | — |

全文の入手元（すべて取得した版のタグのファイルをそのまま写した）:
OpenSSL = openssl/openssl `openssl-3.5.7` の `LICENSE.txt`（NOTICE は無い）/ libffi = libffi/libffi `v3.4.4` の `LICENSE` / zlib-ng = zlib-ng/zlib-ng `2.2.4` の `LICENSE.md` / zlib = madler/zlib `v1.3.1` の `LICENSE` / xz = tukaani-project/xz `v5.2.5` の `COPYING` / Zstandard = facebook/zstd `v1.5.7` の `LICENSE`（BSD を選択）/ expat = python/cpython `v3.14.6` の `Modules/expat/COPYING` / mpdecimal = python/cpython-source-deps `mpdecimal-4.0.0` の `COPYRIGHT.txt` / bzip2 = python/cpython-source-deps `bzip2-1.0.8` の `LICENSE` / CPython incorporated software = python/cpython `v3.14.6` の `Doc/license.rst`「Licenses and Acknowledgements for Incorporated Software」節から末尾まで + 末尾に HACL*（`Modules/_hacl/Hacl_Hash_SHA2.c` の先頭の MIT 表示。`Doc/license.rst` に無いため）。

### VC++ ランタイム（受け入れ条件 10・Q1）

- 入手元: CPython 3.14.6 のインストール（python.org の配布物）に同梱の `vcruntime140.dll`・`vcruntime140_1.dll` を PyInstaller がそのまま集めた（SHA-256 一致）。
- 適用される条件（Microsoft Learn「Redistributing Visual C++ Files」2026-04-15 更新・「Determining which DLLs to redistribute」）: 再頒布は「ライセンスを持つ Visual Studio の利用者」に限られ Microsoft Software License Terms に従う / 再頒布できるのは Redist.txt・REDIST の一覧に載ったファイルだけ / アプリのフォルダへの配置はできるが非推奨（更新の責任が配布者に移る）。配布者の義務の条文（Distributable Code 節）はページから取得できず未確認。第三者（CPython）経由で得た DLL の扱いには言及が無い。
- CPython の `python.txt:281-296`: Microsoft Distributable Code を含む物を配るなら、配布者と利用者に Microsoft の要件と同等以上にそれを守る条項への同意を求めよ。
- **判定: 未解決**。実際の配り方で条件を満たす根拠がまだ無い。**ユーザーの判断と対応が済むまで Windows 版は出荷しない**（暫定 60 §7 の 10）。
- **ユーザー判断（2026-11-24）: 配布物の README に一文を足す**（CPython と同じ扱い）。`packaging/README_dist.txt`（Windows の配布物の `README.txt`）の日英に「`_internal/` の `VCRUNTIME140*.dll` は Microsoft Visual C++ ランタイムの再頒布可能ファイルで Microsoft のライセンス条項が適用される・本ソフトウェアを再頒布するなら Microsoft の再頒布可能コードの条件（ライセンスの窓の Python の項 = `python.txt:281-296`）に従う」を追記（メイン・2 行）。満たす根拠 = 同梱の条項（`python.txt`）がライセンスの窓で読め、README で配布者・利用者に条件を示している。法律の専門家の確認ではない。これで受け入れ条件 10 を満たした扱いとし、出荷停止を解く。
