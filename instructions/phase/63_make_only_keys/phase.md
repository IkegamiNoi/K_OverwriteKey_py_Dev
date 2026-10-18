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
- 主入力（暫定仕様）: [46_make_only_keys.md](../../history/46_make_only_keys.md)（v0.3・ユーザー確定済）。
- モード: **暫定仕様先行モード**。番号対応: phase 63 / 暫定 46 / decisions 63。

## 確定（ユーザー 2026-10-18〜19）

- 押下だけのキーは、走査コード 241 / 242 の表で見分ける（暫定 46 §2）
- 押下と離しの見分け方（案 B）
  - 押していないときの押下 = 押した
  - 押している間の押下は 16 ms 待つ
  - 16 ms 以下の 2 回組 = 離した
  - 保険 = 次の押下で経過時間を見る（§3.2・§3.3）
- **リピートあり**（直接置換で別のキーに置き換えるときに要るため）
- 名前は `extra_scan_codes`（暫定 45 v0.4 の設計 + Codex 指摘 2 件）。jis.json に 241 / 242
- 送信は不変（123 / 121）
- 起票時のレビュー: deep-reviewer の指摘 14 件と、Codex 敵対的レビューの 4 件を反映
  - ロックの中で Tk を呼ばない
  - 世代つきの予約
  - 覚えるのは 2 つ
  - 実の `up` で押下状態を外す
  - 16 ms ちょうどは「離した」

## スコープ

### 含む

- `extra_scan_codes`（暫定 46 §4）
- 走査コードの表と状態機械（§3）
- `hook_controller` の分岐・タイマーのワーカー・時計・世代つきの予約・消去（§3.1・§3.2 注 4）
- 実機目視（§6 #5）
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
  - **実装後にユーザーの実機目視**（§6 #5）
- task_04: 正本反映（§8）・暫定 46 の凍結・`decisions_archive/63_make_only_keys.md`・decisions.md の索引・current.md の完了記載・idea_52 を INDEX_done へ・`/refactor_check`・完了判定前レビュー

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点:
  - 状態機械の遷移が §3.2 の表どおり（16 ms ちょうど・古い押下・遅れた満了・早い満了・`up`）
  - ロックの中で Tk を呼ばない
  - 世代で古い予約・タイマーを捨てる
  - 覚えるのは 2 つ（戻り値と actions の有無）
  - 停止要求の間は素通し（§7.2）
  - 241 / 242 以外のキーの経路が変わらない
  - application が keyboard・tkinter を import しない
- 完了判定前: `deep-reviewer` + `codex-adversarial-reviewer`
