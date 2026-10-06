# task_04_canonical_reflection

## 目的

暫定 32（v0.3）を正本へ昇格し、phase 46 を閉じる（`.claude/rules/task_execution.md`「フェーズ完了時」）。**文書作業のみ（メイン）・コード不変**。

## 対象範囲

- 正本: 暫定 32 §10 の列挙どおり
  - `features.md` §4.2.6（対象 = `target` があればそれ・無ければ直前のトリガー / 判定の順序 / 直前のトリガー不変 / メッセージ）・§4.2.10（2 回押しの対象 = T）・
    §4.1（キー変更で戻す・先頭への `target` も追従）・§4.6「一覧の表示形式」（`[back] → f5` ほか §6）「出力シーケンスの編集」（チェック・ドロップダウン・OK 時の拒否 4 文言）
  - `data_schema.md` §5.11.6（`back` / `rewind` のキー欄を `target` へ。空の `target` の実行時の文言は呼び出しと行を分ける）
  - `codebase_map.md`「出力シーケンスの制御アクション」節（`sequence_control.control_target`・`domain/control_target.py`・`apply_control` の対象の決定・ダイアログの配線）
- フェーズ完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）と指摘の対応
- 暫定 32 の凍結 / `decisions_archive/46_back_rewind_target.md` / decisions.md のアーカイブ索引 / current.md の完了記載（次採番の明記）/ `/refactor_check`
- 起票元 idea: なし（ユーザー要望 2026-10-06）

## 読むファイル

- `instructions/history/32_back_rewind_target.md`（全体）
- `.claude_data/state/decisions.md` の phase 46 節・phase.md の task_01〜03 の完了記載
- 正本の該当節（`features.md` §4.1・§4.2.6・§4.2.10・§4.6 / `data_schema.md` §5.11.6 / `codebase_map.md`「出力シーケンスの制御アクション」節）

## 含まない

- コードの変更（レビューで修正が要る場合は枝番タスクを起票する）
- 暫定 32 §9 のスコープ外・案 B（空の履歴で破棄したときに選択を移す）

## 確認

- 正本の各節が暫定 32 §2〜§6 と §10 の列挙を漏れなく含む（レビューで照合）
- 正本に「戻す・先頭への対象は常に直前のトリガー」とだけ読める旧記述が残っていない

## 完了条件

- 上記をすべて実施し、レビュー 2 種の結果と `/refactor_check` の判定を完了報告に含める（文書のみのため reviewer は deep-reviewer で代える）。
- 実機目視: なし（task_03 で実施済み・2026-10-06 ユーザー OK）。
