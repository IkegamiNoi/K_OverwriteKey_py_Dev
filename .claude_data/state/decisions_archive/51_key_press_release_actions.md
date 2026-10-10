# decisions_archive / phase 51: キーの押下 / 解放アクション（key_hold）

対応表: phase 51 / 暫定 35（v0.9・凍結）/ decisions 51。起票元: [idea_23](../../../instructions/backlog/idea_23_key_press_release_actions.md)（2026-09-18・ユーザー要望・2026-10-09 着手決定）。
完了 2026-10-11。domain / application / infrastructure / presentation。アクションの種類 `key_hold` を追加（後方互換）。text / file_line の送信の例外が止まる系に・送信後に keyboard が修飾キーを押し直さない・停止中は予約済みの入力を実行しない（既存の挙動の変更）。
正本 = `data_schema.md` §5.11.1・§5.11.9 / `features.md` §4.2・§4.2.3・§4.2.8・§4.2.12・§4.5・§4.6 / `key_input.md` §7.7 / 地図 = `codebase_map.md` の phase 51 の項。

## 確定した設計判断（ユーザー）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | 種類は 1 つ（`key_hold` + `edge`）。対象 = 単キー（修飾キーを含む）とマウスのボタン・座標は任意 | `key_down` / `key_up` の 2 種類 = 一覧・ダイアログ・検証の分岐が 2 か所に |
| 2 | 押したままは押下をまたいでよい。止まる経路すべてで自動で離す（入口の関数の単位で決める） | 経路の列挙 = 漏れる |
| 3 | 持ち主 = 押したトリガー（最上段）のキー。呼び出し先の末尾・停止の行の区切り・戻す・押下の合間では離さない。先頭へ・最後の行の停止は離す（v0.2・v0.7） | 呼び出し先の末尾で離す = 押すだけの下請けを呼べない |
| 4 | 一時停止で離し、再開で押し直さない | 押し直す = 一時停止中のユーザー操作と衝突 |
| 5 | 同じキー = 実際に送る対象（スキャンコード + 拡張フラグ）。押すは毎回送り送る前に記録・失敗なら補償の離す（v0.3・Codex 敵対的） | キー名の一致 = `ctrl` と `left ctrl` を別扱い |
| 6 | text / file_line は押したままのキーに関係なく文字どおり入力（送る間だけ離して押し直す・失敗なら押し直さず止まる系）（v0.4〜v0.6・task_01 の probe） | そのまま送る = 改行・バックスペースが修飾キーと組み合わさる |
| 7 | 本機能の送信は keyboard の押下記録に載せない・text の送信後に keyboard に修飾キーを押し直させない（v0.4〜v0.5・probe で右 ctrl が左 ctrl として残る既存の不具合を発見） | — |
| 8 | キーマップの切替（実際に変わるとき）・アクティブの削除はすべて離す独立した入口（v0.8・統合レビュー H1。`reset_indices` が呼ばれる前提が誤り） | 持ち主に一覧の id を持つ = 変更が大きい |
| 9 | 「1 キーを記録」は修飾キーの左右を区別（v0.8） | — |
| 10 | 停止中・キーマップ一時停止中は予約済みのトリガー・直接置換を実行しない（v0.9・完了判定前 Codex 敵対的 high。既存の種類にも効く） | — |
| 11 | 離す送信が失敗したものは集合に残し次の自動の解放で送り直す（v0.9・Codex 敵対的 high = deep M2） | 失敗でも外す = 表示から消えて二度と離さない |
| 12 | 呼び出し先の中の停止の行による連続実行の一時停止では離さない（v0.9・deep M1・区切り扱い） | 一時停止として離す |
| 13 | 現状維持で注記: hotkey の送信の例外では離さない / text の後の押し直しの失敗は止まる系（v0.8） | — |
| 14 | キーリピート（合成の押下は Windows がリピートしない）は idea_41 へ分離（task_05 の実機目視） | — |

## 結果（タスク）

| タスク | 内容 | 実装 |
|---|---|---|
| task_01 | probe（合成の押下中のトリガー判定・text・左右の ctrl）→ v0.4〜v0.5 | メイン実測 |
| task_02 | domain（定数・検証・一覧の書式） | codex-implementer・reviewer 採用 |
| task_03 | HeldInputs・key_hold の実行・text の前後の離す / 押し直す | codex-delegating-implementer（サブエージェント 3）・reviewer 完了可 |
| task_04 | 自動で離す入口・持ち主（最上段）の受け渡し | codex-delegating-implementer（サブエージェント 3）・reviewer 完了可 |
| task_05 | 画面（ダイアログ・一覧の書式・押下中の表示）・解放の配線 | codex-delegating-implementer・reviewer 完了可・実機目視 OK |
| task_06 / 06a | 統合確認（deep-reviewer 要修正 H1 / codex-reviewer P2×2）→ キーマップの切替 / 削除で離す・記録の左右・一時的な離すの途中失敗・一時停止の finally | codex-implementer・reviewer 採用・実機目視 OK（右 ctrl は VirtualBox のゲストでは届かずホストで確認） |
| task_07 / 07a | 正本反映・凍結・完了判定前レビュー → 停止後の予約済み入力・解放失敗の保持 | 07a: codex-implementer・reviewer 採用（file_line の解放エラーの知らせはメインで修正） |

検証（最終・task_07a 後）: tests 1447（skipped 7）/ tests_ui 935 / smoke pass。

## 完了判定前レビュー（task_07）

- **deep-reviewer: 修正要（正本の文言のみ）** → M1（ユーザー判断・判断 12）・M2（= Codex high 2）・M3（text の送信の例外は止まる系を `data_schema.md` §5.11.1 に）・L2 / L3（codebase_map の入口の列挙）・L6（§6 の受容 2 点）を反映。L1 は task_07a で修正。L4・L7 は見送り（実害なし）
- **codex-adversarial-reviewer: needs-attention（high 2）** → ユーザー判断で 2 件とも採用（判断 10・11・task_07a）

## 統合レビューの低（task_06）の扱い

- 正本反映で扱った: L3（拡張キーの記録の扱いは hotkey にも効く）・L4（`owner_scope` 方式）・L8（codebase_map）・L11（設定の反映はフック停止を通る）
- 見送り: L5・L7・L9（実害なし）

## /refactor_check

**不要**（verifier 計測・メイン判定。keyseq/ 21 ファイル +830 / -69）。
M1: 600 行超かつ +100 行以上なし（`app.py` 688 +21・`trigger_panel_controller.py` 642 +8）/ M2: なし（最大は新規 `action_key_hold_fields.py` の `__init__` 80 行）/ M3: `_release_owner` の 20 か所は入口単位の設計どおりの 1 行呼び出しで非該当 /
M4: 種類の追加による分岐で、全列挙の組み直しは増えていない / M5: なし / M6: mouse の `("left", "right", "middle")` は phase 50 以前からの直値。
