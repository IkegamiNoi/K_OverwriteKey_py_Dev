# phase 79 task_03 完了判定前レビューの採否（ユーザー判断済・2026-11-24）

deep-reviewer = **修正要** / codex-adversarial-reviewer = **needs-attention**。下の事実の主張はメインが実測で確認済み（✔）。各項の「推奨」で進めてよければ「推奨どおり」と答えてください。

## A. 判断が要るもの

1. **Tcl / Tk の行にまとめた物の表示**（deep 1・2・Codex 3・暫定 60 §7 条件 8「その行の全文に表示が含まれている」）
   - ✔ `tcl.txt` / `tk.txt`（両 OS 共有・40 行）に libtommath（Windows の `tcl86t.dll` に静的）・PSL（MPL 2.0）・NanoSVG（Mac の `libtcl9tk9.1.dylib` に静的・`nm` で `nsvg` 63 個・zlib License）の表示は 0 件。今の正本の下書き（`features.md` の C ライブラリの行の 1 つ目の小項目）は条件 8 を書かずに外している
   - 選択肢: **(a) 推奨** = 表示を追記する。共有をやめて `tcl.txt`（Windows: + libtommath）/ `tcl_macos.txt`（Mac: + PSL の MPL 2.0 の表示）/ `tk_macos.txt`（Mac: + NanoSVG の zlib License）に分ける。JSON の `file` と全文が変わるので Mac の目視をやり直す（Windows の PSL は有無を確かめてから）/ (b) 条件 8 を「表示の義務が無い物・ファイル自身が表示を持つ物は対応づけだけで足りる」に改める（暫定 60 v0.8・仕様を緩める変更）/ (c) 別の行を足す
   - 根拠: 条件 8 は確定済みの設計。(b) は「実装に合わせて仕様を緩める」に当たる
2. **VC++ ランタイムの出荷停止の解除**（Codex 2・`tasks/task_01_windows_rows.md:112-116`）
   - Codex: README の一文は条件の案内だけで、誰がどう保護条項に同意するかの根拠が無い。停止を戻すべき
   - 選択肢: **(a) 推奨** = 今の扱い（v0.7・2026-11-24 のユーザー判断）を維持し、残存リスク（法律の確認ではない・Microsoft の Distributable Code の条文は未確認）を decisions_archive に明記 / (b) 停止に戻して条項を調べ直す
   - 根拠: 判断は済んでおり、新しい事実は無い（Codex の指摘は同じ論点の再提起）
3. **出荷後の棚卸しの記録の置き場所**（deep 4）: **推奨** = `packaging/README.md` の手順 5 に「結果はその版のタグのリリースノート（または `packaging/inventory/<版>.md`）に残す」と書く / 記録不要とする

## B. 推奨 = 採用（判断不要の欠陥の修正。異論が無ければこのまま直す）

4. ✔ **xxHash の表示漏れ**（Codex 1）: `_zstd.pyd` に `lib/common/xxhash.c`（`PCbuild/_zstd.vcxproj:112`・v3.14.6）が入り、その先頭は「Copyright (c) Yann Collet - Meta Platforms, Inc」。`zstandard.txt` に無い → 末尾に xxHash の節（`xxhash.c` 先頭の表示）を足す。Windows の目視をやり直す
5. ✔ **手順書の `otool -t`**（Codex 4）: 先頭にファイルのパスが出るので書いてあるとおりにハッシュすると一致しない（実測は `-X` 付きで一致）→ `otool -tX` と書き、版の根拠は配布物の版の文字列を主に、コードの一致を補いにする
6. ✔ **Zstandard の照合が黙って外れる**（Codex 5・`tests/test_third_party.py:99-104`）: Windows に行があるのに import に失敗すると照合されない → 行がある OS で import できなければ失敗にする（Codex へ実装委任・Windows で検証）
7. **手順書に Tcl / Tk の DLL の静的コードの洗い出しを足す**（deep 3）・**NanoSVG を task_02 の記録へ追記**（deep 2）
8. **暫定 60 v0.8 に PSL の扱いを書き、decisions_archive に記録**（deep 5）
9. 正本の下書きの補い: `cpython_incorporated*.txt` は命名の例外（deep 6）・「`python.txt` は CPython 同梱のままにし手を入れない」を移す（deep 7）・`current.md` / `phase.md` の「v0.6」を v0.7 に（deep 10）

## C. 保留（次の Windows 作業で確かめる）

10. 最終のテストを Windows で流し直す（deep 8）・Windows の `_tcl_data` の PSL の有無（deep 9）

## 進め方（推奨どおりの場合）

B の 4〜9 と A-1(a) の全文分割は **Windows と Mac の両方の作業が要る**（Windows: xxHash の目視・Zstandard の照合の検証・PSL の有無・libtommath の表示 / Mac: `tcl_macos.txt` / `tk_macos.txt` の目視）。task_02a（Mac）・task_01a（Windows）として起票し、その後に task_03 を再開する。

## ユーザー判断（2026-11-24）

- A-1 = **(b) の考え方**（表に並べるのは表示の義務がある物・行への対応づけはライセンスを確かめた対象の記録）。3 件はどれも義務が無いか果たされている（libtommath = Unlicense・NanoSVG = zlib License・PSL = MPL 2.0 でファイル自身の表示がソース形式の通知の義務を果たす）→ `tcl.txt` / `tk.txt` は変えず、記録に義務の判定を残す。暫定 60 v0.8 で Q3 と条件 8 を改訂（確定済みの条件を緩める変更をユーザーの指示で行う）。Mac の CPython の全文の BLAKE2（CC0・義務なし）は残す（→ その後 v0.9〔task_02b〕で外した）
- A-2 = (a) 推奨（v0.7 を維持・残存リスクを decisions_archive に記録）/ A-3 = 推奨（`packaging/inventory/<版>.md`）/ B 4〜9 = 採用 / C = 保留（task_01a）
