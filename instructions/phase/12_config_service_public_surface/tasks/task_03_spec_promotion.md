# task_03_spec_promotion

## 目的

**phase 12（config_service の公開面の集約）の正本反映とフェーズ完了処理を行う最終タスク。**
根拠は phase.md タスク 3 + 暫定仕様 11 **§7**（正本反映）+ `.claude/rules/task_execution.md`
「フェーズ完了時」。

- **文書のみのタスク**。`keyseq/` / `tests/` / `tests_ui/` の**コード差分は 0 行**。
- 正本 `instructions/common/spec_detail/architecture.md` §3.2 の**当面の許容例外を削除**し、
  実装済みの公開面（`config_service/contracts.py`）を正本の規定にする。
- スキーマ変更なし・挙動不変（task_01 / task_02 で実装済み）。

## 対象範囲（文書限定・コード不変）

### 1. `instructions/common/spec_detail/architecture.md` §3.2（**必須**）

- **例外条項（`:16-19`）と idea_14 の追跡行（`:20-21`）を削除**する。
- presentation の条項を、公開面 = **「`ConfigService` の委譲メソッド + `config_service.contracts`」**
  と規定する形へ書き換える。
- **`config_service` 限定表現を保つ**（**`application` 一般へ広げない**。広げると
  presentation → `keyseq/application/save_plan.py` の `ACTION_*` 参照 5 件が新規違反になる。
  同件は暫定仕様 §6 でスコープ外）。
- §3.2 の他の箇所（依存ルール本体 / application → presentation 非参照）は**触らない**。

### 2. `instructions/common/codebase_map.md`（`config_service` パッケージ表）

- 表へ **`contracts.py` の行を追加**し、件数表記を **12 → 13** に更新する（`:264` 付近の
  「責務ごとに 12 ファイル」）。
- 行の内容: **判定名・理由コード・結果型の唯一の定義**（定数 34 / 型 9）。
  **`config_service` 内の他モジュールを import しない**（依存は実装モジュール → `contracts` の一方向）。
  **presentation はここと `ConfigService` の委譲メソッドだけを見る**（暫定仕様 §7）。
- `candidate_dirs.py` の行と件数 11 → 12 の是正は**起票時に先行実施済**（計画08 の取りこぼし）。
  **本タスクでは再度触らない**。

### 3. 暫定仕様 11 の凍結

`instructions/history/11_config_service_public_surface.md` の冒頭「状態」ブロックを
**凍結済み表記**へ書き換える（暫定仕様 10 の凍結ヘッダと同形）:

- 状態 = **凍結済（2026-09-08・phase 12 完了・v0.3）**・**経緯の参照用**・
  **本書の条項を実装の根拠に引かない**。
- **正本 = `spec_detail/architecture.md` §3.2 + `codebase_map.md`**（`config_service` パッケージ表）。
- 昇格時の判断は `decisions_archive/12_config_service_public_surface.md`。
- **版履歴・本文の条項は書き換えない**（凍結ヘッダの追記のみ）。

### 4. `.claude_data/state/decisions_archive/12_config_service_public_surface.md`（新規）

`decisions.md` の phase 12 節（`:485` 以降）を集約する。既存アーカイブ
（`11_orphan_child_file_sweep.md`）の構成に倣い、少なくとも次を含める:

- 起票時の確定 §4-A〜D / `deep-reviewer` の H-1・H-2 / `codex-adversarial-reviewer` の AST 検査の穴 /
  `codebase_map.md` 取りこぼしの先行是正。
- task_01（定義移動と全参照の付け替え・**1 コミットの原子的変更**）と
  task_02（逆戻り防止テスト **3 本**・4 経路 + 自己検証）の結果と各レビュー判定。
- **`/refactor_check` の判定**（本タスク 7 の結果を末尾に記載）。
- あわせて `decisions.md` の「アーカイブ索引」表へ **`12_config_service_public_surface` の行を追加**し、
  phase 12 節の本文は**索引 + アーカイブへ集約**する（既存フェーズと同じ扱い）。

### 5. `instructions/phase/current.md`

- 「現在の参照先」を **phase 12 完了**の記載へ差し替え、**旧フェーズ（phase 11）の要約行は削除**する
  （`current.md`「フェーズ完了時の指示」）。
- 「次採番」節を更新: **次フェーズ = `13_<topic>`** / 暫定仕様の次採番 = **`12_<topic>`**
  （11 は凍結済と明記）。
- **アクティブなフェーズが無い状態**にし、次フェーズ未確定であることを明示する。

### 6. `instructions/backlog/INDEX.md` → `INDEX_done.md`

- idea_14 の行を `INDEX.md`「ネタ一覧」から**削除**し、`INDEX_done.md`「完了・クローズ一覧」へ**移動**する。
- 状態列を**完了**（phase 12 へのリンク + 成果の要約 + `decisions_archive/12` へのリンク）へ更新する。
- **ファイル本体 `idea_14_config_service_public_surface.md` は移動しない**（`INDEX_done.md` の運用ルール）。

### 7. `/refactor_check` の実行

- `.claude/commands/refactor_check.md` に従う。**メトリクス収集（手順 1〜2・M1〜M6）は `verifier` へ委任**、
  **判定（手順 3 以降）と提案書起票はメイン**（`.claude/rules/agent_selection.md`）。
- 判定結果（不要 / 推奨）を**完了報告と `decisions_archive/12` の末尾に記載**する。
- **提案書の起票は判定が「推奨」かつユーザー承認後**。本タスク内で無断実施しない。

### 設計メモ / 制約

- **`architecture.md` §3.2 は phase 11 でも触った条項**（presentation の内部モジュール非参照）。
  **条項そのものは残し、例外と追跡行だけを消す**（条項ごと消すと規律が失われる）。
- **正本反映は「実装済みの事実の転記」**。ここで新しい規約を発明しない（発明が要るなら
  `.claude/rules/spec_change_workflow.md` に従いユーザーへ報告）。
- 編集は**必ず worktree 側のパス**で行う（main 側を編集するとコミットから漏れる）。

## 含まない

- **`keyseq/` / `tests/` / `tests_ui/` のコード変更**（task_01 / task_02 で完了済。本タスクは文書のみ）。
- `save_plan.ACTION_*` の presentation 直 import の是正（暫定仕様 §6・スコープ外。
  **`architecture.md` の表現を `application` 一般へ広げない**理由でもある）。
- `config_service/__init__.py`（828 行）の分割（`current.md` の別タスク化候補で追跡）。
- `/refactor_check` が「推奨」と判定した場合の**提案書の起票と実施**（判定の記載までが本タスク。
  起票はユーザー承認後）。
- 次フェーズ（`13_<topic>`）の起票・方針決定（ユーザー確認事項）。

## 確認

1. `architecture.md` §3.2 に **`idea_14` の文字列が 0 件**（`grep -n "idea_14" instructions/common/spec_detail/architecture.md`）。
   例外条項（「例外（当面の許容）」）も 0 件。
2. `architecture.md` §3.2 に **`contracts`** が公開面として記載され、**`config_service` 限定表現**が
   保たれている（`application` 一般への一般化がない）。
3. `codebase_map.md` の `config_service` 表に **`contracts.py` の行がある**こと、
   **件数表記が 13** で**表の行数と一致**すること（表の行を数えて照合）。
4. `instructions/history/11_config_service_public_surface.md` の冒頭が**凍結済み表記**であること。
5. `.claude_data/state/decisions_archive/12_config_service_public_surface.md` が存在し、
   `decisions.md` の「アーカイブ索引」に **12 の行がある**こと。
6. `instructions/backlog/INDEX.md` に **idea_14 の行が無く**、`INDEX_done.md` に**ある**こと
   （`grep -n "idea_14" instructions/backlog/INDEX.md instructions/backlog/INDEX_done.md`）。
7. `current.md` の「現在の参照先」が phase 12 完了・次フェーズ未確定を示し、
   **旧フェーズ（phase 11）の要約行が消えている**こと。次採番 = `13_<topic>` / 暫定 `12_<topic>`。
8. **コード差分が 0 行**（`git diff --stat -- keyseq tests tests_ui main.py` が空）。
9. `verifier` の実測で**退行がない**こと（`.venv` の python で実行）:
   `compileall` clean / `tests` **417 pass（skip 7）** / `tests_ui` **288 pass（skip 0）** / smoke pass。
   （文書のみの変更のため件数は task_02 完了時から不変であること自体が確認点）
10. `/refactor_check` を実行し、判定結果を完了報告へ記載した。

## 完了条件

- 上記「確認」1〜10 をすべて満たす。
- **フェーズ完了判定のレビューを通過**: `deep-reviewer`（Opus・複数タスクを跨ぐ差分 / フェーズ完了判定）
  **＋ Codex レビュー（`codex-adversarial-reviewer`）の 2 本立て**
  （`.claude/rules/agent_selection.md`。Codex 不可時は報告のうえ Claude 側へ縮退可）。
- **実機目視は不要**（挙動不変・UI 文言不変。暫定仕様 §5-11）。**本タスクで実施しない**。
- 残課題・想定外の差分があれば完了報告に明記する。
