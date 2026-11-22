# idea_65_bundled_c_library_licenses.md

## 概要

**配布物に同梱される C ライブラリ（OpenSSL 等）を第三者ライセンスの表に載せる**。今の表（`third_party.json`）は Python のパッケージと Python / Tcl / Tk / PyInstaller だけで、Python の実行環境が抱えて入る C ライブラリの行が両 OS とも無い。

## 起票経緯（2026-11-22）

phase 75 task_13b（Mac のビルド）の同梱一覧の照合で見つかり、Windows の作業時に Windows 側も洗い出して両 OS 分を 1 本で起票する扱いにした（`decisions.md`「task_13b」）。Windows 側は task_13c のビルドで洗い出した。

## 現状

- 表: `keyseq/presentation/help/content/third_party/third_party.json`（暫定 57 §6.3 = 同梱一覧は各 OS の実際の収集結果と照らし、表に無い依存があれば行を足す）。
- Windows（Python 3.14・PyInstaller 6.22.3）の `dist/keyseq/_internal/` の DLL のうち表に無いもの: `libcrypto-3.dll`・`libssl-3.dll`（OpenSSL）・`libffi-8.dll`・`zlib1.dll`・`VCRUNTIME140.dll`・`VCRUNTIME140_1.dll`。拡張モジュール（`_bz2`・`_lzma`・`_zstd`・`_decimal`・`pyexpat` 等）が静的に取り込む bzip2 / xz / zstd / mpdecimal / expat は DLL 名からは見えない。
- Mac（Homebrew の Python 3.13.18）: OpenSSL・liblzma・libmpdec・libtommath。libffi は OS のものを使い同梱されない。

## 提案（方向性・要設計）

- 案 A: ライブラリごとに行を足し、各ライセンス文を `third_party/*.txt` に置く（OS 列で出し分け）。
- 案 B: Python の行の文書に、CPython が同梱する C ライブラリのライセンス（CPython の `LICENSE` の第三者の節）を含めて 1 行で済ませ、OpenSSL のように独立して DLL / dylib で入るものだけ行を足す。
- どちらでも、静的に取り込まれたものを含めて何が入っているかは各 OS のビルドで実測して確定する。VC++ ランタイムは再頒布可能パッケージの条件の確認が要る。

## 想定スコープ

- 含む: `third_party.json` の行・`third_party/*.txt`・`tests/test_third_party.py`・ヘルプのライセンスの窓の表示（両 OS）。
- 含まない: アプリのロジック・ビルドの手順の変更（必要なら `.spec` の除外の検討は別）。
- 仕様: 暫定 57 §6.3 の範囲の補い（正本反映後は正本の該当節）。
