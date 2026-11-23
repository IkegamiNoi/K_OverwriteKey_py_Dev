# phase.md

## フェーズ名

同梱の C ライブラリのライセンス（bundled_c_library_licenses）

## フェーズの目的

配布物に入る C ライブラリ（DLL / dylib と、拡張モジュール・Python の本体に静的に入る第三者のコード）を、ライセンスの窓の第三者ライセンスの表に載せ、出荷ごとに配布物と表を突き合わせる手順を整える。**変更はデータ（`third_party.json` と全文の `.txt`）・テスト（`tests/test_third_party.py`）・手順書（`packaging/README.md`）にとどめ、コードは変えない見込み。JSON スキーマは変えない。**

- 起票元: [idea_65](../../backlog/idea_65_bundled_c_library_licenses.md)。
- 主入力（暫定仕様）: [60_bundled_c_library_licenses.md](../../history/60_bundled_c_library_licenses.md)（v0.6・ユーザー確定済）
- モード: **暫定仕様先行モード**。番号対応: phase 79 / 暫定 60 / decisions 79。

## 確定（ユーザー 2026-11-23〜24）

暫定 60 §2・§6 のとおり。要点:

- 案 A = C ライブラリごとに OS ごとの行（必ず `platforms` 付き）と全文。範囲は静的に取り込まれた物も含める。
- VC++ ランタイムは行にしないが、入手元と再頒布の条件・満たす根拠を記録する（Q1）。
- 表示の義務が無い物（xz・libtommath）も載せる（Q2）。Tcl / Tk の DLL に静的に入る物は Tcl / Tk の行で扱い、別のファイルで入る物（`zlib1.dll`）は行を足す（Q3）。
- Python の本体に組み込まれたコードは OS ごとに 1 行「CPython incorporated software」。全文 = `Doc/license.rst` の該当節 + そこに無い組み込みのコード（Windows の HACL* は必須）（Q5）。
- 出荷ごとに配布物を棚卸しして表と突き合わせる（§4.1）。版の根拠は配布物そのものか、収集元と同じだと確かめたビルドの入力。合わなければ出荷しない。

## スコープ

### 含む

- `keyseq/presentation/help/content/third_party/third_party.json` の行の追加（Windows・Mac）と全文の `.txt`（新規）
- `tests/test_third_party.py`（C ライブラリの版の照合の追加・PyPI 照合からの除外・一覧の期待値）
- `packaging/README.md` の Windows / macOS の節（出荷ごとの棚卸しの手順）
- 各 OS の棚卸しの記録（タスク定義の記録欄）
- フェーズ末の正本反映（`features.md`「バージョン情報・ライセンス」）

### 含まない（後送り）

暫定 60 §8 のとおり（ビルドの手順・`.spec` の変更・配布物を自動検査するテスト・`test_help_window` の変更・Python のパッケージの行の見直し・配布物の README の変更）。

## このフェーズで読むファイル

1. 暫定 60 全体（§3 行の規則・§4 / §4.1・§6・§7）
2. `keyseq/presentation/help/content/third_party/third_party.json`・同フォルダの `python.txt`（Windows）/ `python_macos.txt`（Mac）
3. `keyseq/presentation/help/third_party.py`（読み込みの検査。変更しない）
4. `tests/test_third_party.py`（21-39 一覧の固定値・41-53 PyPI の照合・55- Python / Tcl / Tk の照合の形）
5. `tests_ui/test_help_window.py:255`（全文に ` — ` を含めない制約の根拠）
6. `packaging/README.md`（Windows L3〜・macOS L17〜）
7. 正本 `instructions/common/spec_detail/features.md`「バージョン情報・ライセンス」（1076〜1095 行あたり。task_03 で改訂）

## タスク

- task_01: **完了（2026-11-24・実機目視 OK〔ライセンスの窓 25 行〕・codex-implementer〔Luna high〕+ 全文はメインが配置・reviewer 採用・tests 2279 / tests_ui test_help_window 25 / smoke pass）。VC++ はユーザー判断で配布物の README に一文を追記済み（暫定 60 v0.7）** **Windows の行**（Windows で実施）。配布物の棚卸し（§4.1）・未実測の版（libffi・zlib-ng・xz）の確定・VC++ の DLL の入手元と条件・実際の配り方で条件を満たす根拠の記録（利用者への対応が要るとわかったら、ユーザー判断と対応が済むまで出荷しない）・Windows の行と全文・「CPython incorporated software」（HACL* 含む）・`tests/test_third_party.py`（照合の追加・除外・一覧の期待値）・`packaging/README.md` の Windows 節。標準検証 4 種とライセンスの窓の目視
- task_02: **実装・検証済み（2026-11-24・codex-implementer〔Luna high〕+ 全文はメインが配置・reviewer 採用・tests 2217 / test_help_window 25 / smoke pass）・実機目視待ち** **Mac の行**（Mac で実施）。Mac のビルドで棚卸し（拡張モジュールの中の HACL* の有無を含む）・Mac の行と全文・一覧の期待値・`packaging/README.md` の macOS 節。Mac のテストとライセンスの窓の目視
- task_03: **統合確認と正本反映**。暫定 60 の正本への昇格（§9）と凍結・`decisions_archive/79`・`current.md` の完了記載・idea_65 の INDEX_done への移動・`/refactor_check`

## レビュー方針

共通観点（`.claude/rules/review.md`）に加え、次を確認する。

- 変更がデータ・テスト・手順書に収まり、`third_party.py` などのコードと JSON の形が変わっていないこと
- 棚卸しの記録で、配布物の全バイナリと Tcl / Tk のデータ・拡張が行か表示しない理由に対応づき、版の根拠が配布物に結びついていること
- 各全文が実測した版の上流のライセンスファイルと一致し、` — ` を含まないこと
