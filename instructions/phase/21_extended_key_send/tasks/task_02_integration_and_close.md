# task_02_integration_and_close

## 目的

phase 21（task_01）の成果を統合確認・二次レビュー・実機目視で確かめ、記録してフェーズを完了する
（`.claude/rules/task_execution.md`「フェーズ完了時」）。**コードは原則変更しない**（レビュー指摘の採用分は枝番タスクで行う）。

## 対象範囲（検証・レビュー・記録）

### 統合確認（`verifier`）

1. `-m compileall -q keyseq main.py tests tests_ui`
2. `-m unittest discover -s tests`
3. `-m unittest discover -s tests_ui`
4. `-m tests.smoke_app`

### 二次レビュー（差分 = `9428fea..HEAD`）

- `deep-reviewer`: 正本 §7.7 と実装の整合 / 拡張キー表の正しさ / 送信順序と例外時の後始末 / 既存挙動（通常の hotkey・text・マウス・キーマップ送信・フックの受け取り）の不変 / テストの検出力。
- `codex-reviewer`: 標準レビュー。
- 指摘は提示のみ。採否はユーザー。

### 実機目視（ユーザー）

1. メモ帳等で hotkey `shift+right` を数回 → 範囲選択される。続けて `ctrl+c` でコピーできる。
2. hotkey `ctrl+shift+end` → 行末〜文末まで選択される。`ctrl+shift+home` も同様。
3. キーマップで適当なキーを `right` / `end` へ割り当て、**物理 Shift を押しながら**そのキーを押す → 範囲選択される。
4. 通常のキーの hotkey（`ctrl+c` / `ctrl+v` / `enter` / `a` 等）と text アクション・マウスクリックが従来どおり動く。
5. フックの停止 / トグルキー・通常トリガーの抑止が従来どおり（送信したキーが自分のトリガーを誤って起動しない）。

### 記録

- `instructions/phase/21_extended_key_send/integration_result.md`（統合確認の件数 / レビューの採否 / 実機目視の結果）。
- `.claude_data/state/decisions_archive/21_extended_key_send.md` + `decisions.md`「アーカイブ索引」へ 1 行 + 本体の phase 21 節を移動。
- `instructions/phase/current.md`: 完了記載（アクティブなし・直近の領域の数行・次採番 phase 22 / decisions 22）。
- `/refactor_check` の実行と判定の記載（メトリクス収集は `verifier`。PHASE_BASE = `9428fea`）。
- 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`（採否はユーザー）。
- 起票元は idea ではない（ユーザー要望）ため INDEX_done への移動は不要。**idea_23 は未着手のまま残す**。

## 読むファイル

1. `instructions/phase/21_extended_key_send/phase.md`
2. `instructions/common/spec_detail/key_input.md` §7.7

## 含まない

- レビュー指摘の修正（ユーザー採否の後、枝番タスク）。
- 押す / 離すアクション（idea_23）・hotkey の書式変更。

## 確認

- 統合確認 4 項目が pass。
- 二次レビュー・完了判定前レビューの指摘の採否がユーザーにより決定済み。
- 実機目視 1〜5 がユーザーにより確認済み。

## 完了条件

- 上記確認を満たし、記録済み・**reviewer 採用**（記録内容の整合確認）。
- 実機目視は本タスクで実施。
