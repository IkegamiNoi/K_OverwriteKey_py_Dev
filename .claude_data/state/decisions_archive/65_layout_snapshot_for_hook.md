# decisions_archive / phase 65: 受け取りと送信が同じレイアウトの写しを使う

対応表: phase 65 / 暫定 48（v0.3・凍結）/ decisions 65。起票元: idea_51（2026-10-18・暫定 45 の Codex 敵対的レビューから分離）。
完了 2026-10-21。presentation（`LayoutController` の写し）+ application（`held_inputs`・`key_repeat`）+ infrastructure（`input_gateway` の `KeySend`）。**JSON スキーマ不変**。
正本 = `key_input.md` §7.1「フックの実行時のキー名の出どころ」・§7.7「レイアウトの写し」「押したままのキーは押したときの送り方で送る」・受容 / `features.md` §4.6「レイアウトの JSON の `scan_code`」/ 地図 = `codebase_map.md` の LayoutController・phase 51・phase 52・キーの送信の節。

## 確定した設計判断（ユーザー 2026-10-21）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | 受け取り・送信・キーボードUI を `LayoutController` の写し 1 つ（不変・UI スレッドだけで 1 回の代入で差し替え）へそろえる。フックのスレッドはファイルを読まず Tk も触らない | 打鍵ごとの読み直し（従来）= フックのスレッドでファイル I/O と Tk 操作・送信と食い違う |
| 2 | 外部レイアウトの JSON の変更は選び直し（ドロップダウンで同じレイアウトを選んでも）・読み直しのときだけ反映 | ファイルの監視 = 範囲外（§8） |
| 3 | 押したままのキーは押したときの送り方（`KeySend`）で離す・一時的な離しと押し直し・リピート・補償・再試行 | 離す時点で引き直す（従来）= 離しの失敗と切替で元のキーが残り記録も消える |
| 4 | application は `KeySend` を import せず中身を知らない値で持つ | application が型を持つ = 依存方向が増える |
| 5 | 1 打鍵の中で `InputRouter` と `KeyStateManager` が別の写しで名前を引き得るのは受容（Codex 敵対的 medium） | 解決済みの名前を渡す = 範囲が広がる |

## タスク中の判断

### 【起票】モード = 暫定仕様先行（presentation / application / infrastructure・正本は key_input と features・タスク 3）
- 起票前: idea_53 は暫定 47 v0.2 まで起票して保留（ユーザー判断: keyboard の内部への依存が大きく実害がまれ）→ 次候補の idea_51
### 【暫定 48】v0.1 → deep-reviewer 修正して採用（12 件）→ v0.2 → Codex 敵対的 needs-attention 2 件 → ユーザー確定（推奨どおり）→ v0.3
- high（採用）: ユーザーの選び直しで JSON を読み直していなかった → 選択で `reload_keyboard_layouts` を通す（#2）
- medium（受容 = #5）
### 【task_01】codex-implementer・tests 1769 / tests_ui 1122 / smoke OK・reviewer 完了可（低 3: 選択で release_all が最大 2 回〔冪等〕・読込失敗の flash の削除・テストの冗長）
### 【task_02】codex-implementer（1 回目は Codex の利用上限で失敗・ユーザー判断で回復後に再実行）・reviewer 完了可（低 1 = `_repeat_failed` の届かない分岐 → 削除）・verifier 1 回目 fail（既存テスト 11 件の期待が未追従・実装は正しい）→ テスト修正 → tests 1778 / tests_ui 1122 / smoke OK
### 【task_03 実機目視】暫定 48 §7-7 ①②（JSON を書き換えても選び直すまで不変・選び直すと変わる / 押したまま別のレイアウトへ選び直すと離れる）= ユーザー OK（2026-10-21）
### 【task_03 完了判定前レビュー】Codex 敵対的 approve（指摘なし）/ deep-reviewer 修正要（軽微・中 1・低 9）→ ユーザー確定（2026-10-21・推奨どおり）
- 中 1（採用）: フェーズ末の残作業（本書・INDEX・current.md・/refactor_check）→ 実施
- 低 2（修正して採用 → task_03a）: `identity_of` の末尾が未定義名 `key` を参照（届かない分岐・届けば NameError）→ `send.key`・テスト 1 件
- 低 4・6・7・8（修正して採用・文書）: 窓の間に押したキーは「残り得る」（id も変わる読み直しでは 2 回目の解放で離れる。暫定 48 は凍結時の補足で記載）/ key_hold の送信と解決の順に「押したときの送り方」を参照 / features に「同じレイアウトでも離れる」/ 暫定 48 の改訂履歴の並び
- 保留: 低 3（`HeldInput.send` が None のときの扱いがまちまち・今はキーの記録は必ず send を持つ）/ 低 5（id も変わる読み直しで解放の失敗の窓が 2 回出得る・phase 62 からの挙動・選択でも通るようになった）/ 低 9（= refactor_check の M3）/ 低 10（`_repeat_failed` の記録の送り方を直接確かめるテストが無い）
### 【task_03a】メインが直接修正（1 行 + テスト 1 件・軽微）・compileall clean / tests 1779 pass（skip 7）/ smoke OK（verifier）・tests_ui は presentation 不変のため task_02 の 1122 pass を使う・reviewer 採用（指摘なし）
### 【task_03 /refactor_check】推奨に該当・ユーザー判断で保留（2026-10-21）
- 範囲 `git diff df7fe61..HEAD -- keyseq/`（4 ファイル・+98 / -48）。M1（最大 `input_gateway.py` 440 行）・M2・M4・M5・M6 は非該当
- M3 該当: `held_inputs.py` の `resolve_send` → `identity_of` → `("key", scan, extended)` の 3 行組が 3 か所（:87・:182・:202）→ 内部関数 1 つで済む小さな整理。効果が小さいので保留し current.md の「別タスク化候補」に記載
