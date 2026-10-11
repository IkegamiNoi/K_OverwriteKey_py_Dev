# decisions_archive / phase 53: アプリの窓が前面のときはキーリピートしない

対応表: phase 53 / 暫定 37（v0.4・凍結）/ decisions 53。起票元: [idea_42](../../../instructions/backlog/idea_42_suppress_repeat_on_all_dialogs.md)（2026-10-11・phase 52 完了判定前レビュー〔Codex 敵対的 medium・deep-reviewer L3〕から分離）。
完了 2026-10-11。application / infrastructure / presentation（配線のみ）。JSON の変更なし。ダイアログを出す側は変えない。
正本 = `features.md` §4.2.12「キーリピート」の「アプリの窓が前面なら止める」/ `key_input.md` §7.7 / 地図 = `codebase_map.md` の phase 53 の項。

## 確定した設計判断（ユーザー）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | 方式 = 前面ウィンドウ判定（OS の前面の窓が自プロセスなら止める） | messagebox を起動時に包む = ファイル選択・独自ダイアログが漏れ暗黙的 / 共通入口へ置き換え = 155+16 か所の差し替えとテスト 32 ファイル前後へ波及 |
| 2 | 止めた後は再開しない（押したままは保つ） | 前面が戻ったら再開 = 条件が複雑 |
| 3 | メイン画面が前面でもリピートしない | — |
| 4 | 判定は送り直しの発火時だけ（開始・text の後のやり直しでは判定しない）（v0.3・起票時 deep-reviewer 中） | 開始時も判定 = 前面の切替直後の押す行で永久に始まらない |
| 5 | 前面の窓が NULL なら止める・Win32 の例外 / Windows 以外は止めない（ログ初回だけ）（v0.4・確定前 Codex 敵対的 medium） | 取得不能をすべて止めない = 切替途中の NULL で送る / すべて止める = 続けて起きる例外でリピートが使えなくなる |
| 6 | 判定と送信の間の競合（1 回分がアプリの窓へ届き得る）は受容（v0.4・確定前 Codex 敵対的 medium） | 判定を重ねる = 幅は無くせない |

## 結果（タスク）

- task_01 前面判定・`KeyRepeater` の `is_blocked`・App の配線（codex-implementer・reviewer 採用・tests 1501 / tests_ui 942 / smoke pass）。実機目視 §8-9〜11 OK
- task_02 統合確認（deep-reviewer 採用〔low 5・保留 / 除外〕・codex-reviewer 指摘なし）
- task_03 正本反映・暫定 37 凍結

## 完了判定前レビュー（task_03）

- deep-reviewer 修正して採用 → 転記の誤り（H1: codebase_map の phase 53 の項が phase 52 の項を分断 / L1: キーボード表示の窓の列挙漏れ / L2: `is_blocked` の例外の扱いの未記載）を修正。L3（凍結ヘッダの予定形の文）は暫定 35・36 と同じ形のため変更なし
- Codex 敵対的 approve（指摘なし）

## /refactor_check

**不要**（verifier 計測・メイン判定。keyseq/ 3 ファイル +57 / -1）。
M1: 600 行超は `app.py`（721・+3）のみ / M2: なし / M3: 「例外のログを初回だけ」のフラグが 2 か所（3 か所未満で非該当）/ M4〜M6: なし。
