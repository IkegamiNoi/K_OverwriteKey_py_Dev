# 暫定仕様 60: 同梱の C ライブラリのライセンス（bundled_c_library_licenses）

> 状態: **未凍結・v0.2・主入力**（v0.1 起票 → v0.2 deep-reviewer「修正して採用」の 1〜13 を反映・2026-11-23）。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: [idea_65](../backlog/idea_65_bundled_c_library_licenses.md)（2026-11-22・phase 75 task_13b / 13c の同梱一覧の照合）。
> 番号対応: phase 79 / 暫定 60 / decisions 79。

---

## §1 目的 / 背景

配布物（PyInstaller の onedir）には、Python の実行環境が抱えて入る C ライブラリが含まれる。BSD / MIT 系のライセンスは、**バイナリで配るときも著作権表示と許諾文を添えること**を求めている。この条件は配布したかどうかで決まり、DLL か静的リンクかは関係ない。今の第三者ライセンスの表（`third_party.json`）には、これらの行が両 OS とも無い。本フェーズで、配布物に入る C ライブラリをライセンスの窓に載せる。

### 現状監査（2026-11-23）

- 表の正本: `keyseq/presentation/help/content/third_party/third_party.json`（正本 `features.md`「バージョン情報・ライセンス」節）。行のキーは `name` / `version` / `license` / `file` と任意の `platforms`（`win32` / `darwin`）だけで、他のキーは読み込みで拒否される（`keyseq/presentation/help/third_party.py` の `_parse_entries`）。正本の同節には「表に無い同梱の C ライブラリ（OpenSSL 等）の扱いは idea_65（未決）」とある。
- Windows の Python の行の全文 `python.txt`（676 行）は、Windows 版 CPython が同梱している `LICENSE.txt` と同じもの。その中にあるのは、PSF などの Python 本体のライセンス・「Additional Conditions for this Windows binary build」（Microsoft の再頒布可能コード = VC++ ランタイム）・bzip2・libffi・Zstandard・見出しの無い Apache License 2.0 の全文（418 行〜・OpenSSL 3 の `LICENSE.txt` と見られる）・Tcl/Tk 系の条項。**zlib・xz・mpdecimal・expat の節は無い**。CPython の本体に組み込まれた第三者のコード（`Doc/license.rst`「Licenses and Acknowledgements for Incorporated Software」に載る mimalloc・HACL* など）の文も無い（mimalloc / HACL の語は 0 件）。
- Mac の Python の行の全文 `python_macos.txt`（277 行）は Python 本体のライセンスだけで、**第三者の節は一つも無い**。
- Windows の配布物（`dist/keyseq/_internal/`・2026-11-22 のビルド・Python 3.14.6・PyInstaller 6.22.3）の実測:

| ライブラリ | 入り方 | 版（実測） | 実測の方法 |
|---|---|---|---|
| OpenSSL | `libcrypto-3.dll`・`libssl-3.dll` | 3.5.7 | `ssl.OPENSSL_VERSION`・DLL の FileVersion |
| libffi | `libffi-8.dll` | 未実測（DLL に版の情報が無い） | — |
| zlib-ng | `python314.dll` に静的（`zlib` はビルトインのモジュール） | 未実測（`zlib.ZLIB_RUNTIME_VERSION` = `1.3.1.zlib-ng` は zlib 互換 API の版で zlib-ng 自体の版ではない） | — |
| zlib | `zlib1.dll`（読み込むのは `tcl86t.dll` だけ・Tcl 用） | 1.3.1 | DLL の FileVersion |
| CPython に組み込まれた第三者のコード | `python314.dll` に静的（mimalloc・HACL* ほか） | Python の版に従う | DLL 内の文字列の検索で mimalloc・HACL を確認 |
| VC++ ランタイム | `VCRUNTIME140.dll`・`VCRUNTIME140_1.dll` | 14.42.34438.0 | DLL の FileVersion |
| bzip2 | `_bz2.pyd` に静的 | 1.0.8（`python.txt` の記載） | Python からは取れない |
| xz（liblzma） | `_lzma.pyd` に静的 | 未実測 | Python からは取れない |
| Zstandard | `_zstd.pyd` に静的 | 1.5.7 | `compression.zstd.zstd_version` |
| mpdecimal | `_decimal.pyd` に静的 | 4.0.0 | `decimal.__libmpdec_version__` |
| expat | `pyexpat.pyd` に静的 | 2.8.1 | `pyexpat.EXPAT_VERSION` |

  sqlite3 は配布物に入っていない（`sqlite3.dll` は収集されない）。
- Mac（Homebrew の Python 3.13.18・phase 75 task_13b の照合）: OpenSSL・liblzma・libmpdec・libtommath が dylib で入る。libffi は OS のものを使い同梱されない。静的に入る物と各版は Mac のビルドで実測する（§5）。

## §2 確定事項（ユーザー 2026-11-23）

- **案 A**: C ライブラリごとに `third_party.json` へ行を足し、各ライセンス全文を `third_party/*.txt` に置く。OS ごとの出し分けは既存の `platforms` で行う。
- **範囲**: DLL / dylib として入る物に加え、**拡張モジュールに静的に取り込まれた物も含める**（各 OS のビルドで実測して確定する）。Python の本体（`python3XX.dll` / libpython）に組み込まれた第三者のコードの扱いは §6 Q5。
- **モード**: 暫定仕様先行（本書 → phase 79）。

## §3 表の行の決め方

- **JSON の形は変えない**。キーは既存の 4 つと `platforms` だけ（スキーマ不変・読み込みのコードも変えない）。
- **1 ライブラリ = OS ごとに 1 行**。C ライブラリの行には**必ず `platforms` を付ける**（両 OS に同じ版が入っていても、`platforms` の無い行にはしない。並びを OS ごとに保つため。`third_party.py` は JSON の順で並べて OS で絞るだけ）。
- **並び**: 各 OS の Python の行の直後に、その OS の C ライブラリの行を**大文字小文字を無視した ABC 順**で置く（Windows では Python と Tcl の行の間に入る）。
- **`name`**: 上流の名前（`OpenSSL`・`libffi`・`zlib-ng`・`zlib`・`bzip2`・`xz`・`Zstandard`・`mpdecimal`・`expat`・`libtommath`）。
- **Zstandard** は BSD 3-Clause と GPLv2 の二重ライセンスのうち BSD を選ぶ（`license` = `BSD 3-Clause License`・全文は `LICENSE` だけで `COPYING` は入れない）。
- **`license`**: 英語の固有名で、言語で切り替えない（既存の行と同じ）。版ごとにライセンスが変わる物（例: xz は 5.6 から 0BSD）は、実測した版のライセンスにする。
- **`version`**: 実測した版を書く（必須キーのため空にはできない）。Python から取れない物は、その OS の CPython のビルドが使った版（CPython の外部ライブラリの定義・Homebrew の formula など）で確定し、確定の根拠を §5 のタスクの記録に残す。
- **`file`**: `<name の小文字>.txt`。OS で全文が同じ版なら 1 つのファイルを両 OS の行で共有してよい（Tcl / Tk と同じ）。版で全文が違うときは `<name>_macos.txt` のように分ける。
- **全文の入手元**: 実測した版の上流のライセンスファイル（OpenSSL は `LICENSE.txt`、ほかは各リポジトリの `LICENSE` / `COPYING`）。`python.txt` に既に節がある物（bzip2・libffi・Zstandard）も、行ごとの全文を別に置く（`python.txt` は CPython 同梱のままにし、手を入れない）。
- **全文の制約**: 全文に ` — `（前後に空白のあるダッシュ）を含めない。`tests_ui/test_help_window.py:255` が一覧の件数をこの文字列の数で数えているため。含まれる全文が見つかったらタスクで止めて相談する。

## §4 版の照合のテスト

- `tests/test_third_party.py` に、**Python から版を取れる C ライブラリ**の照合を足す。対象 = OpenSSL（`ssl.OPENSSL_VERSION`）・Zstandard（`compression.zstd.zstd_version`。無い Python では skip）・mpdecimal（`decimal.__libmpdec_version__`）・expat（`pyexpat.EXPAT_VERSION`）。形は既存の `test_python_tcl_and_tk_versions_match_runtime` にそろえる（`load_third_party()` で実行中の OS の行を取り、名前で引いて実行時の値と照合し、行が無ければ skip）。
- 照合の比べ方（実行時の文字列から版の部分を取り出す規則）はタスク定義で決める。
- 版を取れない物（libffi・zlib-ng・zlib・bzip2・xz・libtommath）はテストで照合しない。版を上げたときの確認の手順は `packaging/` の手順書に書く（§6 Q4）。
- **既存の照合からの除外**: `test_library_versions_match_installed_distributions`（`tests/test_third_party.py:41-53`）は Python / Tcl / Tk 以外の全行を `importlib.metadata.version(name)` で照合する。C ライブラリの行をその除外の集合に加える（同名の PyPI パッケージと取り違えないため）。
- **一覧の固定値**: `test_bundled_notices_are_complete_unique_and_ordered`（`tests/test_third_party.py:21-39`）は OS ごとの名前の列を固定しているので、行を足したタスクで期待値を更新する。

## §5 タスクの分け方（予定）

1. **Windows の行**（task_01）: §1 の未実測の版（libffi・zlib-ng・xz）を確定し、Windows の行と全文・§4 のテスト（照合の追加・除外・一覧の期待値）・`packaging/README.md` の Windows 節（Q4）を入れる。Windows の検証（標準検証 4 種）とライセンスの窓の目視。
2. **Mac の行**（task_02・Mac で実施）: Mac のビルドで同梱の dylib と静的に入る物・各版を実測し、Mac の行と全文・一覧の期待値・`packaging/README.md` の macOS 節を入れる。Mac のテストとライセンスの窓の目視。
3. **正本反映**（task_03）: §9 の昇格・本書の凍結・decisions_archive/79・current.md・idea_65 の INDEX_done への移動・refactor_check。

## §6 確認事項（ユーザー判断）

- **Q1 VC++ ランタイムを行に載せるか**: 提案 = **載せない**。VC++ ランタイムの再頒布の条件は、表示を求めるものではなく、再頒布の仕方の条件（改変しない・Microsoft の商標を使わない等）。その条件は `python.txt` の「Additional Conditions for this Windows binary build」に既に載っていて、窓で読める。ライセンス文を持つ OSS ではないため、他の行と形がそろわない。
- **Q2 libtommath（Mac・Unlicense）と xz（0BSD / パブリックドメイン）のように表示の義務が無い物も載せるか**: 提案 = **載せる**。何が入っているかを一覧で確かめられることを優先する（§2 の「範囲」の趣旨）。
- **Q3 Tcl / Tk のために入る物**: 提案 = **一般則として「別のファイルで入る物は行を足し、Tcl / Tk の DLL に静的に入っている物は Tcl / Tk の行の配布物として扱う」**。Windows の `zlib1.dll`（`tcl86t.dll` だけが読み込む）は別のファイルなので `zlib` の行を足す。`tcl86t.dll` に静的に入る libtommath は行を足さない。Mac の libtommath は別の dylib で入るので行を足す（Q2。Python ではなく Homebrew の tcl-tk の依存の可能性があり、出所は task_02 で実測する。並びは §3 のとおり Python の行の直後でよい）。
- **Q4 `packaging/` の手順書**: 提案 = `packaging/README.md` の Windows / macOS の節に「C ライブラリの版の確認」の手順（§4 で照合しない物の確かめ方）を 1 段落ずつ足す。
- **Q5 Python の本体に組み込まれた第三者のコード**（mimalloc・HACL*・SipHash・dtoa など。CPython の `Doc/license.rst`「Licenses and Acknowledgements for Incorporated Software」に載る物）: 提案 = **OS ごとに 1 行「CPython incorporated software」を足し**、全文はその版の `Doc/license.rst` の該当節をテキストにした物にする（`version` = その OS の Python の版・`license` = `Various (see text)`）。理由 = 本体に入る物は Python の版で決まり、ライブラリごとに行を分けると行数が膨らむうえ、版を個別に実測できない。expat・libffi・zlib など §3 の行と重なる物があっても、重複は許す（§3 の行は配布物の中身の一覧、この行は CPython の謝辞の写しという役割の違い）。

## §7 受け入れ条件（ドラフト）

1. Windows のライセンスの窓に、§1 の表の C ライブラリ（Q1 の結論に従う）の行と全文が出る（§3・§5 の 1）。
2. Mac のライセンスの窓に、Mac のビルドで実測した C ライブラリの行と全文が出る（§3・§5 の 2）。
3. `third_party.json` の形が変わらず、既存の読み込みとテストが通る（§3）。C ライブラリの行はすべて `platforms` を持ち、各 OS の Python の行の直後に §3 の順で並ぶ。
4. §4 の照合のテストが、実行中の OS の行で通る（Windows と Mac の両方）。C ライブラリの行が `test_library_versions_match_installed_distributions` の対象から外れ、一覧の期待値が更新されている。
5. 各全文が実測した版の上流のライセンスファイルと一致し、版の確定の根拠（実測の方法か参照した定義）がタスクの記録に残っている（§3）。
6. `packaging/README.md` の Windows / macOS の節に C ライブラリの版の確認の手順がある（Q4）。
7. 正本 `features.md` の「idea_65（未決）」の行が、本書の内容で置き換わっている（§9）。

## §8 スコープ外（本フェーズでやらない）

- ビルドの手順・`.spec` の変更（収集の除外の検討を含む）。
- Python のパッケージの行の見直し（既存の行は変えない）。
- 配布物の README の変更（第三者ライセンスは窓で見られる旨が既に書いてある）。
- sqlite3 など配布物に入らない物。

## §9 正本反映（フェーズ末昇格・予定）

- 正本: `instructions/common/spec_detail/features.md`「バージョン情報・ライセンス」節 — 「Windows のみ」「macOS のみ」の各項への C ライブラリの行の追加と件数（今は Windows 15 行・Mac 16 行）の更新・C ライブラリの行の決め方（§3）・1086 行の「JSON の版は `.venv` に入っている版・実行中の Python / Tcl / Tk の版と照合」を §4 の C ライブラリの照合と除外を含む書き方へ・1085 行の「idea_65（未決）」の置き換え。
- 実装: `keyseq/presentation/help/content/third_party/third_party.json`・同フォルダの全文の `.txt`（新規）。コードの変更は無い見込み。
- テスト: `tests/test_third_party.py`（§4 の照合の追加・除外・一覧の期待値）。`tests_ui/test_help_window.py` は件数を `len(notices)` で見ているので追従は不要（§3 の全文の制約だけ守る）。
- 手順書: `packaging/README.md` の Windows / macOS の節（Q4）。
- `instructions/common/codebase_map.md`: third_party の行の説明に変化があれば追従。

## 関連

- [idea_65](../backlog/idea_65_bundled_c_library_licenses.md)
- [暫定 57 §6.3](57_mac_support.md)（配布物の中身とライセンスの表示・凍結）
- [phase 75](../phase/75_mac_support/phase.md)・[decisions_archive/75](../../.claude_data/state/decisions_archive/75_mac_support.md)（task_13b / 13c の同梱一覧の照合）
- 正本 `instructions/common/spec_detail/features.md`「バージョン情報・ライセンス」
