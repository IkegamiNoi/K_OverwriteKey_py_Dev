# task_05_spec_promotion_and_close

## 目的

暫定 62（v0.4・task_04 の受容を §6 に追記済み）を正本へ昇格して凍結し、フェーズ 82 を閉じる（`.claude/rules/task_execution.md`「フェーズ完了時」）。文書のみ（メインが直接行う）。

## 対象範囲（文書のみ）

- 正本 `instructions/common/spec_detail/features.md`:
  - §4.5「一時的な案内」に一時メッセージ欄の下敷き
  - 「ステータスの見切れのツールチップ」に下敷きへの追従（T2）
  - 最小の高さに「下敷きも 1 行分」（T3）と、改行を含む名前の受容
  - §4.6「キーの文字」の枠の文字の決め方
  - 新しい節「レイアウトの JSON の `key_symbols`」（読込の規則と判定の順〔T5〕・JSON の同じキーの重複・警告・描き直し〔削除の後の保存失敗を含む〕・受容）
  - 「記号キーのキー名の表示」の使う箇所（T1）・配列固有のキーの書き分け・逆引き
  - 「選び直すまで反映しない」から受容への参照
- 正本 `instructions/common/codebase_map.md`: phase 82 の節（T4）
- `ui_terms.md` は変更なし（文言の一覧と新しい用語を持たない）・`data_schema.md` は対象外（レイアウトの JSON の書式が無い）
- 暫定 62 の凍結・`decisions_archive/82_layout_key_symbols.md`・decisions.md の索引・current.md の完了記載（次採番 phase 83 / 暫定 63 / decisions 83 / 提案書 31 / idea 72）・idea_63 を `INDEX_done.md` へ
- 完了判定前レビュー（deep-reviewer・Codex 敵対的）と `/refactor_check`

## 読むファイル

- 暫定 62・`.claude_data/state/decisions.md` の phase 82 の節・`instructions/phase/82_layout_key_symbols/task_04_pending_decisions.md` §3

## 含まない

- コードの変更（提案書 30 の実施はユーザー判断で別に起票する）

## 確認

- 完了判定前レビュー 2 本の指摘の採否が決まっていること（ユーザー 2026-11-26「推奨どおり」）
- `/refactor_check` の判定（推奨 → 提案書 30）

## 完了条件

- 上記の文書が揃い、完了判定前レビューの採用分を反映している（文書のみのタスクなので、完了判定前レビューを本タスクの別視点レビューとする）。
