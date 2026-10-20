# phase.md

## フェーズ名

押下だけが続けて届くキー（make_only_keys）

## フェーズの目的

外付けの JIS キーボードの無変換・変換のように、**離しを送らず押下だけが届くキー**（走査コード 241 / 242）を、フックで「押した / リピート / 離した」に組み直す。
これにより、キーボードUI の直接置換で、無変換・変換を BackSpace・矢印などの別のキーに置き換えて使えるようにする。
名前は、レイアウトの行の受け取り用の追加の走査コード `extra_scan_codes` で付ける。

- 影響レイヤ:
  - domain: 走査コードの表
  - application: 状態機械
  - presentation: `hook_controller.on_input_event` の分岐・`keyboard_layouts` の照合・`LayoutController`・`app.py` の組み立て
- infrastructure・送信は不変
- **JSON スキーマの追加あり**（レイアウトの JSON の任意キー `extra_scan_codes`。既存キーは不変。設定・キーマップの JSON は不変）

- 起票元: [idea_52](../../backlog/idea_52_make_only_keys.md)（2026-10-18・phase 62 の実機目視から分離）。
- 主入力（暫定仕様）: [46_make_only_keys.md](../../history/46_make_only_keys.md)（v0.5・ユーザー確定済 2026-10-20。v0.3 = 2026-10-19 確定・task_03 の実機目視の NG で v0.4・task_03d・03e の実機目視の NG で v0.5 へ改訂）。
- モード: **暫定仕様先行モード**。番号対応: phase 63 / 暫定 46 / decisions 63。

## 確定（ユーザー 2026-10-18〜19）

- 押下だけのキーは、走査コード 241 / 242 の表で見分ける（暫定 46 §2）
- 押下と離しの見分け方（案 B）
  - 押していないときの押下 = 押した
  - 押している間の押下は 16 ms 待つ
  - 16 ms 以下の 2 回組 = 離した
  - 保険 = 次の押下で経過時間を見る（§3.2・§3.3）
- ~~リピートあり~~ → **リピートなし**（v0.4・2026-10-20。送信の最中の物理の押下が OS へ素通りするため・送信の見直しは idea_53）/ 押下だけのキーの直接置換の枠は**灰色がかった緑**（§3.4）/ 「押した」から待ち時間 − 100 ms より前の単独の押下は片方の「離した」（§9 #3）
- 名前は `extra_scan_codes`（暫定 45 v0.4 の設計 + Codex 指摘 2 件）。jis.json に 241 / 242
- 送信は不変（123 / 121）
- 起票時のレビュー: deep-reviewer の指摘 14 件と、Codex 敵対的レビューの 4 件を反映
  - ロックの中で Tk を呼ばない
  - 世代つきの予約
  - 覚えるのは 2 つ（v0.4 で戻り値だけに）
  - 実の `up` で押下状態を外す
  - 16 ms ちょうどは「離した」

## スコープ

### 含む

- `extra_scan_codes`（暫定 46 §4）
- 走査コードの表と状態機械（§3）
- `hook_controller` の分岐・タイマーのワーカー・時計・世代つきの予約・消去（§3.1・§3.2 注 4）
- 実機目視（§6 #6）
- 正本反映（§8）

### 含まない（後送り）

- 半角/全角・かな の届き方の見直し / キーの取得（Tk）で特殊キーを取る（idea_50）/ 同じレイアウトの写し（idea_51）
- 「キーを個別にフックする」設定での押下だけのキー / 241 / 242 以外の押下だけのキー / アプリの Mac 対応（§7）

## このフェーズで読むファイル

1. 暫定仕様 46（全節）
2. `keyseq/application/input_router.py`（:87-149 `handle`）・`keyseq/application/key_state_manager.py`
3. `keyseq/presentation/controllers/hook_controller.py`（:45-52 停止要求・:130-170 開始 / 停止・:289-312 `on_input_event` / `_execute_reserved_action`）
4. `keyseq/presentation/app.py`（:130-260 の組み立て）
5. `keyseq/infrastructure/input_gateway.py:109` `keyboard_repeat_timing`
6. `keyseq/presentation/keyboard_layouts.py`・`keyseq/presentation/controllers/layout_controller.py`（`extra_scan_codes`。手本 = 戻した 722a1e9 の差分）
7. 正本: `key_input.md` §7.1 / §7.2 / §7.3 / §7.7・`features.md` §4.6

## タスク

- task_01: `extra_scan_codes`（暫定 46 §4）
  - phase 62 で戻した 722a1e9 のコード・テスト・jis.json の 5 ファイル分を当て直す（`git revert 6f7995e` は文書まで戻るので使わない。実装・レビュー済みの差分で §4 と同じ内容）
  - Codex 指摘 2 件は規定のみで、コードは変えない
- task_02: 走査コードの表（domain）と状態機械（application）・単体テスト（§3・§6 #1）
- task_03: `hook_controller` の分岐・タイマーのワーカー・時計・世代つきの予約・消去・`app.py` の組み立て・結合テスト（§3.1・§3.2・§6 #2）
  - **実装後にユーザーの実機目視**（§6 #5）→ NG（リピート中の IME の切替・離しても止まらない）
- task_03c: 押下だけのキーの判定の経過を時刻つきで出すデバッグ出力（計測用・挙動は不変）→ 計測で原因を特定し暫定 46 v0.4 へ（2026-10-20）
- task_03d: 状態機械を v0.4 に合わせる（リピートなし・片方の離し・覚えるのは戻り値だけ）（§3.2・§3.3・§6 #1〜#2）
- task_03e: キーボードUI の押下だけのキーの直接置換の枠を灰色がかった緑に（§3.4・§6 #5）
  - task_03d・03e の後の実機目視で、長押しの途中の取り違えからの連鎖（リピートのように出続ける）を計測 → 暫定 46 v0.5 へ（2026-10-20）
- task_03f: 状態機械を v0.5 に合わせる（離した直後の押下は押し続けの続き）（§3.2 注 5・§3.3・§6 #1〜#2）
  - **task_03f の後にユーザーの実機目視**（§6 #6）→ OK（2026-10-20）→ 色の最終判断
- task_04: 正本反映（§8）・暫定 46 の凍結・`decisions_archive/63_make_only_keys.md`・decisions.md の索引・current.md の完了記載・idea_52 を INDEX_done へ・`/refactor_check`・完了判定前レビュー

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点:
  - 状態機械の遷移が §3.2 の表どおり（16 ms ちょうど・古い押下・遅れた満了・早い満了・`up`）
  - ロックの中で Tk を呼ばない
  - 世代で古い予約・タイマーを捨てる
  - 覚えるのは戻り値だけ（v0.4）・押し続けている間は `handle` を呼ばない・片方の離しの境目
  - 停止要求の間は素通し（§7.2）
  - 241 / 242 以外のキーの経路が変わらない
  - application が keyboard・tkinter を import しない
- 完了判定前: `deep-reviewer` + `codex-adversarial-reviewer`
