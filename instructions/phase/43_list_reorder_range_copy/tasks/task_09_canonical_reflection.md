# task_09_canonical_reflection

## 目的

暫定 30（v0.9）を正本へ昇格し、phase 43 を閉じる（`.claude/rules/task_execution.md`「フェーズ完了時」）。**文書作業のみ（メイン）・コード不変**。

## 対象範囲

- 正本: 暫定 30 §12 の列挙どおり（`features.md` §4.1・§4.2.3・§4.2.9・§4.3・§4.6・保存の節 / `key_input.md` §7.3 /
  `data_schema.md` §5.13.1・§5.13.5 / `codebase_map.md`）。v0.5〜v0.9 を含める。
  とくに v0.8（§5.1 の呼び出し先は今入っているフレーム）と v0.9（§6.4 切替キーのまとめて設定）は、`features.md` §4.3 の追加・個別読込の規則
  （「1 つずつ設定」の記述）を置き換える。`codebase_map.md` には task_08 の分（`keymap_list_edit.py`）と task_08a の分（`application/keymap_switch_batch.py`・
  `dialogs/keymap_switch_batch_dialog.py`・`keymap_add_flow.py` の 1 経路化）を含める
- フェーズ完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）と指摘の対応
- 暫定 30 の凍結 / `decisions_archive/43_list_reorder_range_copy.md` / decisions.md のアーカイブ索引 / current.md の完了記載（次採番の明記）/ `/refactor_check`
- 起票元 idea: なし（ユーザー要望 2026-10-02）

## 含まない

- コードの変更（レビューで修正が要る場合は枝番タスクを起票する）

## 確認

- 正本の各節が暫定 30 §12 の列挙を漏れなく含む（レビューで照合）
- `features.md` §4.3 に「1 つずつアクティブにして設定」の旧記述が残っていない

## 完了条件

- 上記をすべて実施し、レビュー 2 種の結果と `/refactor_check` の判定を完了報告に含める（文書のみのため reviewer は deep-reviewer で代える）。
- 実機目視: なし（task_02〜08a で実施済み）。
