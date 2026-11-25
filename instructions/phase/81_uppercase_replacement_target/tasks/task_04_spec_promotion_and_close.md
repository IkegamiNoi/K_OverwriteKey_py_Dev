# task_04_spec_promotion_and_close

## 目的

暫定 61 v0.3 を正本へ昇格し、暫定 61 を凍結して phase 81 を閉じる（`.claude/rules/task_execution.md`「フェーズ完了時」）。
**文書のみ**（例外: `contracts.py` の `sent_modifiers_down` に、各 OS の返す値の理由を書くコメントを足す。挙動は変えない）。

## 対象範囲

1. 正本の反映（暫定 61 §9）
   - `data_schema.md` §5.1（キー名の小文字化の文）・§5.6 のキーマップ（`mappings` の正規化の文）・「キー名の読み替え」の行: 置換先の `A`〜`Z` は大文字のまま保つ例外と、後方互換（手書きの `"A"` の動きが変わる・旧版で保存し直すと小文字になる）
   - `key_input.md` §7.4: 置換先の英字の大文字の記録（Shift + `a`〜`z` → 大文字）・送信（小文字の名前で解いて Shift を足す・判定の「表は持たない」の例外）・Caps Lock の受容（見込み・補正しない）・macOS の「押されている」に送信済みの修飾を含めること・Windows の送信済みの修飾が (False, False) の理由（`GetAsyncKeyState` は送ったキーも反映する見込み・deep 4）。§7.9 の macOS の送信の節（Shift の要る文字の判定の表）も合わせる
   - `features.md` §4.6 のキー置換の枠の文字: 大文字の置換先は `key_display_names` を引かず大文字で出す
   - `codebase_map.md`: `normalize_mapping_target`（キー名の正規化の節）と phase 74 の Shift の行に大文字と `sent_modifiers_down` を足す
2. `contracts.py` の `sent_modifiers_down` にコメント（上の理由）
3. 暫定 61 を凍結（状態の行）
4. フェーズ完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`（`--base 2fa77e03`）。指摘の採否はユーザー
5. `decisions_archive/81_uppercase_replacement_target.md` の作成と decisions.md の索引の 1 行（phase 81 の節を消す）
6. `current.md` の完了記載（アクティブ = なし・次採番 phase 82 / 暫定 62 / decisions 82 / 提案書 29 / idea 69）・idea_62 を `INDEX_done.md` へ
7. `/refactor_check`（メトリクス収集は verifier・英字 1 文字の大文字の判定の重複〔deep 6〕を判定に含める）

## 読むファイル

- [暫定 61](../../../history/61_uppercase_replacement_target.md) §3〜§5・§9
- `.claude_data/state/decisions.md` の phase 81 の節
- 正本の該当箇所（`data_schema.md:40-41`・`:280-281`・`:912`／`key_input.md:149-155`・`:317`・`:332`／`features.md:726`／`codebase_map.md:907`・`:964-973`）

## 含まない

- コードの挙動の変更（レビューで欠陥が出たら止めて枝番タスク）
- idea_68（置換元の Shift の面）の着手

## 確認

- 正本の記述が暫定 61 と実装（task_01〜03a）に合っている・実機目視の扱い（Caps Lock は見込み・macOS の目視は未報告）を正本に書いた
- decisions_archive/81 と索引のリンクが実在する・decisions.md に phase 81 の節が残っていない
- current.md の次採番が他の箇所と食い違わない・idea_62 が INDEX.md に無く INDEX_done.md にある
- `contracts.py` のコメントの追加後に `compileall` clean（verifier）

## 完了条件

- 上記確認・完了判定前レビューの採否が決まる・**reviewer 採用**
