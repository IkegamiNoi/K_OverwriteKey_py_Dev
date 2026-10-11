# decisions_archive / phase 52: key_hold のキーリピート

対応表: phase 52 / 暫定 36（v0.4・凍結）/ decisions 52。起票元: [idea_41](../../../instructions/backlog/idea_41_key_hold_auto_repeat.md)（2026-10-10・phase 51 task_05 の実機目視・2026-10-11 着手決定）。
完了 2026-10-11。domain / application / infrastructure / presentation。key_hold に任意キー `repeat` を追加（後方互換・キーの無い既存の行はリピートしない）。
正本 = `features.md` §4.2.12「キーリピート」・§4.6 / `data_schema.md` §5.11.9 / `key_input.md` §7.7 / 地図 = `codebase_map.md` の phase 52 の項。

## 確定した設計判断（ユーザー）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | 間隔は OS のキーボード設定（`SystemParametersInfoW`）に合わせる | アプリ独自の間隔設定 = UI が増える |
| 2 | 対象は修飾キー以外（押されている状態だけで効くため） | — |
| 3 | key_hold の押す + キーの行に「リピートする」チェック。新規 ON・キーの無い既存の行は OFF | 既定で全行リピート = phase 51 の行の挙動が変わる |
| 4 | 同時に 1 つだけ・最後に始めたキー（実キーボードと同じ）（v0.3） | 複数同時 = 実キーボードと違う |
| 5 | 一覧で ` (リピート)` を付ける（v0.3） | — |
| 6 | 止める場所は「対象のキーの押す・離す送信の前」の 1 本（v0.2・起票時 deep-reviewer 高） | 経路ごとに列挙 = 漏れる |
| 7 | エラーの知らせの前に止め、表示中は開始・再開・発火をすべて断る（v0.3・v0.4 Codex 敵対的 high） | 止めるだけ = 表示中に次の key_hold 行で始まる |
| 8 | 対象を含む hotkey・直接置換は送る前に止める（v0.4 Codex 敵対的 medium） | — |

## 結果（タスク）

- task_01 domain + OS のリピート設定（codex-implementer・reviewer 採用）
- task_02 `KeyRepeater` と `HeldInputs` / `ActionExecutor`（codex-delegating-implementer・reviewer 修正して採用 → 解けないキー名で hotkey・直接置換を妨げない・再予約の失敗で止める をメインで修正）
- task_03 App の配線・知らせの表示中の抑止・ダイアログ（codex-implementer・reviewer 採用・Mock の App で落ちる抑止の書き方等をメインで修正）。実機目視 §8-12〜14 OK
- task_04 統合確認（tests 1491 / tests_ui 942 / smoke pass・実機目視 §8-15 OK）。task_04-1 で修飾キー判定の `_` 綴りを修正
- task_05 正本反映・暫定 36 凍結

## 統合レビュー（task_04）

deep-reviewer 採用（low 8）/ codex-reviewer P2 1 件 → ユーザー判断:
- 修正して採用（task_04-1）: `left_shift` 等の `_` 綴りが修飾キー判定から漏れていた（keyboard の normalize_name は `_` → 空白）
- 保留: 抑止の begin/end が `hook_controller.py` と `App.repeat_suppressed()` で重複（Mock の App で落ちないよう意図的に選んだ書き方）
- 昇格時に実装へ合わせた: §4.6 の別名は keyboard 実在名（`command` / `left menu` 等）+ `_` の正規化 / §6 の置き場（取得はモジュール関数・知らせの口は `HeldInputs` が持ち `set_callbacks` で渡す）/ text の後の押し直しが一部でも失敗したら再開しない（安全側）

## 完了判定前レビュー（task_05）

- deep-reviewer 修正要 → 転記の誤り（H1: data_schema の例の崩れ / L1: codebase_map phase 51 の項の誤記）を修正。L2（`after` 未注入ならリピートしないの未転記）は保留（テスト用の注入の都合）
- Codex 敵対的 needs-attention（medium: 保存失敗の `showerror` で抑止されない）+ deep-reviewer L3（フック開始の失敗の知らせ）→ **ユーザー判断: phase 52 の範囲は実行系のエラーの知らせと正本に明記して閉じ、全ダイアログの抑止は次フェーズで実装**（[idea_42](../../../instructions/backlog/idea_42_suppress_repeat_on_all_dialogs.md)）

## /refactor_check

**不要**（verifier 計測・メイン判定。keyseq/ 9 ファイル +363 / -9）。
M1: 600 行超は `app.py`（718・+30）のみで +100 未満 / M2: なし / M3: `held_inputs.py` の `_stop_repeat` 呼び出し等は新規の止める処理の 1 行呼び出しで非該当 / M4: 増加なし / M5: なし / M6: `input_gateway.py` の Win32 換算式の直値は同値の既存定数なしで非該当。
