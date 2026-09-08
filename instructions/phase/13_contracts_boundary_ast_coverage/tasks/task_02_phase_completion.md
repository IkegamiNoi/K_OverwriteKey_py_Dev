# task_02_phase_completion

## 目的

**phase 13（公開面の逆戻り防止テストの検査範囲の拡張）の記録とフェーズ完了処理を行う最終タスク。**
根拠は phase.md「タスク」2 + `.claude/rules/task_execution.md`「フェーズ完了時」。

- **文書のみのタスク**。`keyseq/` / `tests/` / `tests_ui/` の**コード差分は 0 行**。
- **正本 `instructions/common/spec_detail/` の改訂は不要**（本フェーズは仕様変更を伴わず、
  `architecture.md` §3.2 の条項は不変で**検査精度を上げただけ**）。**この判断自体を記録に残す**。

## 対象範囲（文書限定・コード不変）

### 1. `.claude_data/state/decisions_archive/13_contracts_boundary_ast_coverage.md`（新規）

`decisions.md` の phase 13 節を集約する。既存アーカイブ（`12_config_service_public_surface.md`）の
構成に倣い、少なくとも次を含める:

- **起票時の判断**: モード = **直接改訂**（3 条件を満たす。仕様変更がないため暫定仕様を起こさない）/
  idea_15 の**案 A（検査の強化）を採用**（案 B = 限界記述のみ、は不採用）/ 起票時に固定した期待値
  （**テストメソッド 3 本 = `tests` 417 件のまま** / **presentation は違反 0 件なので拡張後も全 pass** /
  **`keyseq/` 差分 0 行**）。
- **task_01**: A-1（完全修飾名解決）/ A-2（`asname` 追跡）/ **既存の「素の名前」検査を残して和集合**にした理由
  （presentation に import 由来でない `config_service` という名前の変数が実在する。
  **【訂正】起票時に書いた「31 箇所」は誤りで実測は 29 箇所**〔`ast.Name` 21 / `ast.arg` 8〕）/
  **重複の畳み込み**（同一 行番号 × 内部モジュール名）/ `reviewer` = **修正要（docstring 1 文）→ 是正済**。
- **task_01b**（**ユーザー判断で本フェーズへ追加した枝番**）: R4（相対 import の解決）と
  **R4-fallback**（解決不能時に末尾一致へ縮退＝**素通しにしない**）/ 呼び出し側の `package` 算出 /
  **兄弟参照 16 件を誤検出しないこと**を許可例で固定 / 深さの実測（level=4 検出 / level=3 非検出）/
  `reviewer` = **完了可**（参考指摘 2 件のうち docstring 1 件は反映・関数長は `/refactor_check` へ）。
- **拡張後に残る限界**（docstring に明記済。**task_01c 追加後は 4 つ**）: 動的 import / 実行時に組み立てた名前 /
  **代入による再束縛**（`x = config_service` の `x`）。加えて **`package` 空 + `from . import X` 形**は
  縮退判定できない（presentation の走査では `package` を必ず渡すので発生しない）。
- **正本反映が不要という判断**とその根拠。
- **`/refactor_check` の判定**（本タスク 5 の結果を末尾に記載）。
- あわせて `decisions.md` の「アーカイブ索引」表へ **13 の行を追加**し、phase 13 節の本文は
  **索引 + アーカイブへ集約**する（phase 12 と同じ扱い）。

### 2. `instructions/phase/current.md`

- 「現在の参照先」を **phase 13 完了**の記載へ差し替え、**旧フェーズ（phase 12）の要約行の扱いは
  current.md「フェーズ完了時の指示」に従う**（直前 / その前の 2 件までに整理する）。
- **アクティブなフェーズなし**（次フェーズ未確定）とし、次採番 = **`14_<topic>`** を明記する。
- 「次フェーズ候補（参考）」に残っている **phase 11 / 12 完了の未反映**（phase 12 完了レビューの L-4）は
  **本タスクの対象外**（触らない）。

### 3. `instructions/backlog/INDEX.md` → `INDEX_done.md`

- idea_15 の行を `INDEX.md`「ネタ一覧」から**削除**し、`INDEX_done.md`「完了・クローズ一覧」へ**移動**する。
- 状態列を**完了**（phase 13 へのリンク + 成果の要約 + `decisions_archive/13` へのリンク）へ更新する。
- **ファイル本体 `idea_15_contracts_boundary_ast_coverage.md` は移動しない**。

### 4. `.claude_data/state/session.md` / `handoff.md`

- フェーズ完了と**次フェーズ未確定**を反映する（`/save_state` → `/save_handoff`）。
- `resume_hints` の phase 13 分は**完了版の要点**（R1〜R4 + 属性アクセスの検査範囲・**残る限界**〔**task_01c 追加後は 4 つ**〕）へ圧縮する。

### 5. `/refactor_check` の実行

- `.claude/commands/refactor_check.md` に従う。**メトリクス収集（手順 1〜2・M1〜M6）は `verifier` へ委任**、
  **判定（手順 3 以降）と提案書起票はメイン**。**PHASE_BASE = `90db223`**（phase 13 起票コミット）。
- **`reviewer` の参考指摘「`collect_forbidden_refs` が約 90 行」をここで判定する**
  （M2 は「80 行超の**関数の新規発生**」。本関数は phase 12 からの既存関数を拡張したものなので、
  **M2 の定義に照らして該当するかを明示的に判断し、結果を記録に残す**）。
- 判定結果（不要 / 推奨）を**完了報告と `decisions_archive/13` の末尾に記載**する。
- **提案書の起票は判定が「推奨」かつユーザー承認後**。本タスク内で無断実施しない。

### 設計メモ / 制約

- **正本反映は行わない**（仕様変更がないため）。「念のため `architecture.md` に追記」もしない
  （条項は phase 12 で確定済み。触るなら `.claude/rules/spec_change_workflow.md` に従いユーザー確認が先）。
- 編集は**必ず worktree 側のパス**で行う（main 側を編集するとコミットから漏れる）。
- **`decisions.md` は「アーカイブ索引」+ 計画 NN 節だけを残す**運用（完了フェーズの節は本体に残さない）。

## 含まない

- **`keyseq/` / `tests/` / `tests_ui/` のコード変更**（task_01 / task_01b で完了済）。
- **正本 `spec_detail/` の改訂**（不要。この判断自体は記録する）。
- 検査の追加強化（残る限界の解消。**task_01c 追加後は 4 つ**）。**必要になったら新規 idea として起票する**。
- phase 12 完了レビューの保留分（L-1 / L-4 / L-8）の是正。
- `/refactor_check` が「推奨」と判定した場合の**提案書の起票と実施**（判定の記載までが本タスク）。
- 次フェーズ（`14_<topic>`）の起票・方針決定（ユーザー確認事項）。

## 確認

1. `.claude_data/state/decisions_archive/13_contracts_boundary_ast_coverage.md` が存在し、
   `decisions.md` の「アーカイブ索引」に **13 の行がある**こと。`decisions.md` に **phase 13 節の本文が残っていない**こと。
2. `decisions_archive/13` の**相対リンクが解決できる**こと
   （`.claude_data/state/decisions_archive/` からは `../../../instructions/...`。phase 12 で踏んだ誤りの再発防止）。
3. `instructions/backlog/INDEX.md` に **idea_15 の行が無く**、`INDEX_done.md` に**ある**こと
   （`grep -n "idea_15" instructions/backlog/INDEX.md instructions/backlog/INDEX_done.md`）。
4. `current.md` が **phase 13 完了・次フェーズ未確定・次採番 14** を示していること。
5. **コード差分が 0 行**（`git diff --stat -- keyseq tests tests_ui main.py` が空）。
6. `verifier` の実測で**退行がないこと**: compileall clean / `tests` **417 pass（skip 7）** /
   `tests_ui` **288 pass（skip 0）** / smoke pass。
7. `/refactor_check` を実行し、判定結果（**関数長 90 行の扱いを含む**）を完了報告と
   `decisions_archive/13` へ記載した。

## 完了条件

- 上記「確認」1〜7 をすべて満たす。
- **フェーズ完了判定のレビューを通過**: `deep-reviewer`（Opus）**＋ Codex レビュー
  （`codex-adversarial-reviewer`）の 2 本立て**（`.claude/rules/agent_selection.md`。
  Codex 不可時は報告のうえ Claude 側へ縮退可）。
- **実機目視は不要**（テストのみの変更）。**本タスクで実施しない**。
- 残課題・想定外の差分があれば完了報告に明記する。
