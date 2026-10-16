# decisions_archive / phase 61: キーボードUI の取得で VK を走査コードへ変換する

対応表: phase 61 / 暫定なし（直接改訂モード）/ decisions 61。起票元: idea_47（2026-10-16・phase 59 暫定 43 の起票時の deep-reviewer の指摘 → メインがコードの経路を実測して確認）。
完了 2026-10-17。presentation のみ（`keyboard_window._normalize_tk_key`・`keyboard_layouts.resolve_layout_key_id_from_scan_code`）。**JSON スキーマ不変**。フックの実行時・送信・画面の枠の編集の窓の名前の解決は不変。
正本 = `key_input.md` §7.4「キーボードUI の編集のキーの名前」/ 地図 = `codebase_map.md`（`keyboard_layouts.py`・`keyboard_window.py` の行）。

## 確定した設計判断（ユーザー 2026-10-16〜17）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | VK を `win32_window.vk_to_scan_code` で走査コードへ変換してからレイアウトを引く（画面の枠の編集の窓と同じ） | keysym の表に F キーを足すだけ = JIS の特殊キーの経路が直らない |
| 2 | 変換後は**レイアウトの `scan_code` だけ**で引き、既知の特殊キーの表へは落とさない（特殊キーはレイアウトのファイルに閉じ込める方針の第一歩） | 既知の表まで引く（フックと名前を揃える）= US 入力配列の「`」（走査コード 41）が `zenkaku_hankaku` になる（整合チェックの reviewer 指摘）。ユーザーは「JIS の特殊キーは jis.json に閉じ込めたい」 |
| 3 | フックの実行時・送信の既知の表の扱いは idea_49 へ分離 | 本フェーズで変える = 送信は keyboard ライブラリが `kana`・`zenkaku_hankaku` を知らず表が要る・後方互換の評価が要る |
| 4 | phase 61 は F キーの修正で完了・JIS の特殊キーの取得は idea_50 へ分離（2026-10-17） | 本フェーズで直す = Tk のイベントからは判別できず、フックで走査コードを読む等の設計変更が要る |

## タスク中の判断

### 【起票】モード = **直接改訂**（1 ファイルの不具合修正・正本は 1 項の追記・タスク 2）
- 整合チェックの reviewer: 修正して採用（既知の表へ落とすと US の「`」が `zenkaku_hankaku` になる）→ メインの裏取りでフックの実行時も既知の表で同じ名前と判明 → ユーザーへ 2 案を説明 → ユーザー判断 = レイアウトだけで引く（#2）・idea_49 を起票
### 【task_01】Codex 実装・tests 1689 / 対象 12 件 / smoke OK・tests_ui は `test_compact_window` の 3 件のみタイミング系で失敗（全体実行 1136 秒・単独再実行で 8 件 OK・reviewer も無関係と判断）・reviewer 採用
### 【task_01 実機目視】F1 / F10 / F12 は置換される（OK）。JIS の特殊キーは取れない → 確認用の窓で実測（2026-10-16〜17）
- 通常: 4 キーとも keysym `??`・VK 229（`VK_PROCESSKEY`）。IME が OFF でも同じ。`ImmGetVirtualKey` も 0xE5
- 入力コンテキストを外す: 無変換 = 0x1A（`VK_IME_OFF`）・変換 = 0x16（`VK_IME_ON`）〔MS-IME のキーの割り当てに従う・走査コード 241 / 242〕・半角/全角 = 押す 0xF4 / 離す 0xF3・かな = 0xF2（走査コード 112）
- Tk のイベントは物理の走査コードを持たない → JIS の特殊キーは VK から確実に逆算できない → ユーザー判断で idea_50（取得中にフックで物理の走査コードを読む案を推奨として記録）
- 確認用の窓の「入力コンテキストを外す」ボタンのクリックが 2 回とも記録されなかった（処理は自動呼び出しで正常を確認・原因は不明）→ 開いた時点で外す版で実測

### 【task_02 /refactor_check】不要（2026-10-17）
- 範囲 `git diff 8e9fbc8..HEAD -- keyseq/`（2 ファイル・+26 / -3）。M1（最大 `keyboard_window.py` 544 行 +11）・M2・M4・M5（0 件）・M6 は非該当。M3 は走査コードの `int()` の try が 2 か所（3 か所未満）

### 【task_02 完了判定前レビュー】Codex 敵対的 needs-attention（中 1）/ deep-reviewer 完了可（低 7）→ ユーザー確定（2026-10-17）
- 中（採用 → task_01b）: 外部レイアウトにテンキーの id（例 `num 0`）と `scan_code` 82 を書くと、拡張キーの Insert（VK 45 → 走査コード 82）がキーボードUI で `num 0` に化ける。フックの実行時（`input_router.py:190-193`）にある「レイアウトの名前がテンキー名なら採らない」ガードがキーボードUI に無かった → 同じガードを追加
- 低（採用・文書）: L1（JIS の特殊キーが `??` になるのは全入口共通と「判別できないキー」へ）/ L2（MS-IME で実測の条件）/ L3（phase.md の目的に未達）/ L4（current.md の phase 59 の残件の追従・地図への言及）/ L5（task_02 の codebase_map の文言を実態に）/ L6（本欄）
- 保留: L7（US 入力配列で jis.json を選んだときの「`」= `zenkaku_hankaku`・キーボードUI の `grave` が送信で通じるか = idea_45 / idea_49 の領域）
- 残存リスク: tests_ui の `test_compact_window` の 3 件が全体実行の遅いときにタイミングで落ちる（単独再実行で OK・今回の変更と無関係・記録のみ）
