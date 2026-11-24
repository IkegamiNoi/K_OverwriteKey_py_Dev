# decisions_archive: phase 79 同梱の C ライブラリのライセンス

暫定仕様先行モード（[暫定 60](../../../instructions/history/60_bundled_c_library_licenses.md) v0.9・凍結）・JSON スキーマ不変・コード変更なし（データ・テスト・手順書のみ）・2026-11-24 完了。起票元 = [idea_65](../../../instructions/backlog/idea_65_bundled_c_library_licenses.md)。正本 = `features.md`「バージョン情報・ライセンス」・`codebase_map.md`。

要点: 配布物に入る C ライブラリ（DLL / dylib と、Python の本体・拡張モジュールに静的に入る第三者のコード）のうち、**バイナリで配るときの表示の義務がある物だけ**を `third_party.json` に OS ごとの行で載せる（Windows の窓 21 行・Mac 19 行・JSON 29 行・全文 26 個）。義務の無い物は行にせず、棚卸しの記録に義務の判定を残す。出荷ごとに配布物を棚卸しし（`packaging/README.md`・結果は `packaging/inventory/<版>.md`）、対応づけられない物か版の不一致があれば出荷しない。

## タスクと実装エージェント

- task_01（Windows）13d9b795 / 814dbabe / 051b2544 = codex-implementer（Luna high）+ 全文はメインが配置・reviewer 採用・目視 OK（当時 25 行）。DLL・pyd 26 個が CPython のインストールとハッシュ一致。
- task_02（Mac）2c788338 / bdcf4cb6 = codex-implementer（Luna high）+ 全文はメイン・reviewer 採用・目視 OK（当時 21 行）。
- task_03 前半 de55da8a = 正本の下書き・完了判定前レビュー（deep-reviewer 修正要 / codex-adversarial-reviewer needs-attention）の採否一覧（`instructions/phase/79_bundled_c_library_licenses/task03_review_decisions.md`）。
- task_02a（Mac）179f5deb = レビューの採否の反映（v0.8）・codex-implementer（Luna high）+ メイン 1 行・reviewer 採用。
- task_02b（Mac）a54229fe / 7c749bbe = 義務がある物だけ（v0.9）・codex-implementer（Luna high）・reviewer 修正して採用・Mac の目視 OK（19 行）。
- task_01a（Windows）6dad0314 = 最終のコードで標準検証 4 種 pass（tests 2279・skip 9 / `test_third_party` skip 0 / tests_ui 1321 / smoke）・再ビルドの配布物に PSL 無し・目視 OK（21 行）・reviewer 採用。
- task_03 後半（本記録）= 正本昇格の仕上げ・暫定 60 凍結・本アーカイブ・current.md・idea_65 の移動・refactor_check。

### 【起票・暫定 60 §6】Q1〜Q5（2026-11-23・ユーザー確定）
- Q1 VC++ ランタイム = 行にしない（条件は `python.txt` の Microsoft の条項で読める）。v0.7: 配布物の README（`packaging/README_dist.txt`・日英）に Microsoft の条項が適用され再頒布時は再頒布可能コードの条件に従う旨の一文を足し、出荷停止を解く → **採用**
- Q2 義務の無い物も載せる → v0.9 で**覆す**（下記）
- Q3 Tcl / Tk の DLL・データに入る物は Tcl / Tk の行に対応づける → **採用**（v0.8 で「義務がある物だけ全文に足す」へ改訂）
- Q4 `packaging/README.md` に出荷ごとの棚卸しの手順 → **採用**（v0.8 で記録先 = `packaging/inventory/<版>.md`・初回は出荷時に作る）
- Q5 Python の本体・拡張に組み込まれた物は OS ごとに 1 行「CPython incorporated software」（`Doc/license.rst` の節 + そこに無い物のうち義務がある物 = 両 OS とも HACL*）→ **採用**
- Codex 敵対的レビュー（v0.4・v0.5）: 拡張モジュールの中の第三者のコードも棚卸し・版の根拠を配布物に結びつける・VC++ の条件を満たす根拠と出荷の停止 → **採用** /「全文の制約を外す」→ **除外**

### 【task_03 完了判定前レビュー】deep 修正要 / Codex needs-attention の採否（2026-11-24・ユーザー判断）
- A-1 Tcl / Tk にまとめた物（libtommath・NanoSVG・PSL）の表示 → **(b) の考え方**: 義務が無いか果たされている（Unlicense・zlib License・MPL 2.0 でファイル自身の表示がソース形式の通知の義務を果たす）ので `tcl.txt` / `tk.txt` は変えず記録に判定を残す（v0.8・確定済みの条件 8 を緩める変更をユーザーの指示で行った）
- A-2 VC++ の出荷停止の解除（Codex の再提起）→ **v0.7 を維持**
- A-3 棚卸しの記録先 → `packaging/inventory/<版>.md`
- B 4〜9（xxHash ほかの表示を `zstandard.txt` に・`otool -tX`・Zstandard の照合を行がある OS で必須に・手順書に Tcl / Tk の静的コード・PSL の扱い・下書きの補い）→ **採用**（task_02a）
- C（Windows の再検証・PSL の有無）→ task_01a で実施。Windows の Tcl 8.6.15 には cookiejar が無い

### 【v0.9】窓に載せるのは表示の義務がある物だけ（2026-11-24・ユーザー判断・Q2 を覆す）
- 外した行: Windows の bzip2・xz 5.2.5・zlib・zlib-ng、Mac の xz 5.8.4・libtommath（全文 6 個を削除）。Mac の CPython incorporated software の全文から BLAKE2（CC0）の節を外す。HACL*（MIT）は残す → **採用**（task_02b）
- 義務の判定: bzip2 License・zlib License = 条件はソースでの表示の保持だけで謝辞は必須ではない / xz 5.2.5 = パブリックドメイン / 0BSD・Unlicense・CC0 = 表示の条件なし

### 【task_03 仕上げのフェーズ完了判定前レビュー】deep-reviewer 完了可（中 1・低 8）の採否（2026-11-24・メイン）
- 1 current.md の前フェーズの残件の連結・2 本記録の refactor_check の「keyseq 無変更」の書き方・4 暫定一覧の 60 の表記・5 task_03 の定義に完了時の注記・6 採否一覧の見出しと BLAKE2 の注記・7 phase.md の「含まない」に VC++ の一文の例外・8 session.md の更新 → **採用**（文書のみ）
- 3 Zstandard / mpdecimal の照合が import できなければ失敗する点を正本に書く・9 本記録の v0.4 の Codex 指摘の書き分け → **保留**（テストの細目・情報は Q1 / Q4 / Q5 側にある）
- Codex 敵対的レビューは task_03 前半（de55da8a）で実施済み。その指摘は task_02a・02b・01a で反映し、仕上げの差分（文書のみ）には再実施していない

### 残存リスク（記録・未解決ではない扱い）
- 義務の判定は各ライセンスの条文の読みで、**法律の専門家の確認ではない**
- VC++ ランタイム: Microsoft の Distributable Code の条文そのものは未確認（Microsoft の公式の説明と CPython の条項に拠る）
- 静的に入るライブラリのソースごとの著作権表示まで走査したのは Zstandard（xxHash・threading・divsufsort）だけ。他の静的ライブラリは LICENSE の写しに拠る
- テストは開発用の `.venv` の値を見るだけで、配布物との一致は出荷ごとの棚卸し（手作業）が担う

### refactor_check（メイン実測・PHASE_BASE 8f8cf221^）
- Python の変更 = `tests/test_third_party.py` のみ（176 行・+41 / -3）。`keyseq/` の Python コードは無変更（`third_party.json` と全文の `.txt` = データのみ）→ M1〜M6 該当なし → **不要**
