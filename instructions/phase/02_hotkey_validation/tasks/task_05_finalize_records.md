# task_05_finalize_records

## 目的

フェーズ 02_hotkey_validation の**最終タスク（正本反映・記録）**。暫定仕様
[01_hotkey_validation.md](../../../history/01_hotkey_validation.md) §8 と
`.claude/rules/task_execution.md`「フェーズ完了時」に従い、暫定仕様の**正本昇格 + 凍結**、
記録類（decisions_archive / current.md / INDEX 移動）、`/refactor_check` 判定を行う。

**実装コードは変更しない**（task_04 で完了・挙動不変を確認済）。**文書作業のみ**
（フェーズ末の正本反映タスクはメインセッションが直接行ってよい＝`.claude/rules/agent_selection.md`）。

## 対象範囲（文書・記録のみ）

### 1. 暫定仕様の昇格・凍結（§8）

- **正本 `instructions/common/spec_detail/` への昇格**: 昇格要否は spec_detail に hotkey 検証の仕様節が
  あるかで決まる（§8「要調査」）。Explore 調査の結論に従う:
  - **記載あり** → 担当層の記述を移設後（domain=文法検査 / application=`HotkeyService` / presentation=薄い委譲）へ更新。
  - **記載なし** → 挙動不変のため**昇格不要**。その旨を decisions_archive に根拠付きで記録。
- **暫定仕様の凍結**: `instructions/history/01_hotkey_validation.md` の状態を「**凍結**（v1.0・正本反映済 or
  昇格不要確定）」へ更新（版歴に凍結行を追記）。
- **§6-11 の文言補正**（ユーザー承認済・2026-07-18）: 受け入れ条件 §6-11 を実装に合わせて補正する。
  「アクション編集ダイアログで…正規化されて保存される」は不正確なので、
  「**プリセットダイアログ＝保存時に検証・正規化される／アクション（シーケンス）＝実行時に正規化される。
  アクション保存時の正規化・検証は [idea_03](../../../backlog/idea_03_action_hotkey_save_normalization.md)
  で対応予定**」と明記する（idea_03 実施を前提とした文言）。

### 2. `instructions/common/codebase_map.md` 更新（§8）

- 「主な責務」に **`HotkeyService`（application 層・hotkey の合成 + キー名検証）** と
  **`keyseq/domain/hotkey.py::validate_hotkey_syntax`（domain・純粋な文法検査）** を追記。
- App の責務（現 line 91「dialogs 向け契約（`validate_hotkey` …）」）を、
  **`validate_hotkey` は `HotkeyService.validate` への薄い委譲**である旨に整理
  （検証ロジックの実体は App にない）。

### 3. `.claude_data/state/decisions_archive/02_hotkey_validation.md` 作成

- フェーズの判断履歴を集約（既存 `decisions_archive/01_view_ref_cleanup.md` の書式に準拠）。
  含める: モード（暫定仕様先行）/ 設計案 C 採用 / parts 再構成廃止 / 命名 / 安全網テスト残置 /
  敵対的レビューの MemoryError 指摘却下 / **task_04 実機目視で判明したアクション非対称 → idea_03 分離 +
  §6-11 補正**（ユーザー判断 A/B）/ `/refactor_check` 判定 / コミット一覧 / 検証・レビュー結果。

### 4. `.claude_data/state/decisions.md` アーカイブ索引に 1 行追加

- `| 02_hotkey_validation | [02_hotkey_validation.md](decisions_archive/02_hotkey_validation.md) | <概要> |`

### 5. `instructions/phase/current.md` 更新

- 「現在の参照先」を 02 から差し替え（**旧フェーズ 02 の要約行は削除**し、要約は decisions_archive へ集約）。
- フェーズ 02 完了を反映。「次採番」= 次フェーズ **`03_<topic>`**（次候補は idea_02）。

### 6. `instructions/backlog/INDEX.md` の idea_01 を完了にして `INDEX_done.md` へ移動

- idea_01 の状態を「**完了**（02_hotkey_validation フェーズ 2026-07-18・正本反映 or 昇格不要確定 →
  リンク）」に更新し、行を `INDEX_done.md` へ移動（ファイル本体は `backlog/` に残す）。
- idea_03 は**未着手のまま INDEX.md に残す**（本フェーズでは着手しない）。

### 7. `/refactor_check` の実行と判定記載

- `/refactor_check`（`.claude/commands/refactor_check.md`）を実行。メトリクス収集（M1〜M6）は
  `verifier` へ委任し、判定はメインで行う。結果（要否）を decisions_archive とフェーズ完了報告に記載。

## 設計メモ / 制約

- **実装コード（`keyseq/`）・テストは一切変更しない**。変更するのは `instructions/` と
  `.claude_data/state/` 配下の文書のみ。
- 昇格の有無は Explore の spec_detail 調査結論に厳密に従う（勝手に spec_detail を新設・改変しない。
  `.claude/rules/spec_change_workflow.md`「独断で spec_detail を修正しない」）。
- §6-11 補正はユーザー承認済（2026-07-18）の範囲のみ。恒久設計の追加はしない（idea_03 前提の文言に留める）。

## 含まない

- idea_03（アクション hotkey の保存時正規化）の実装・設計確定（別フェーズ・未着手）。
- 単キー検証の統一（暫定仕様 §7 スコープ外）。
- `keyseq/` 配下の実装・テストの変更（task_01〜04 で完了）。
- 次フェーズ（03）の起票（本タスクでは current.md の次採番明記まで。起票は次フェーズ着手時）。

## 確認

- **昇格判断の裏取り**: Explore の spec_detail 調査結論（記載あり/なし）を decisions_archive に明記。
- **リンク健全性**: 追加・更新した相対リンク（decisions.md 索引 / current.md / INDEX_done.md /
  §6-11 の idea_03 リンク）が実在ファイルを指すこと。
- **INDEX 整合**: idea_01 が INDEX.md から消え INDEX_done.md に 1 行ある。idea_03 は INDEX.md に残る。
- **凍結の明示**: `history/01_hotkey_validation.md` の状態が「凍結」になっている。
- **`/refactor_check`**: 判定（要否）が出て decisions_archive に記載されている。
- **実装コード無変更**: `git diff -- keyseq/ tests/ tests_ui/` が**空**（文書のみの差分）。
- **標準検証**（文書のみの変更だが退行がないことの確認）: `verifier` で
  compile clean / tests 77 / tests_ui 16 / smoke pass（`.venv` python）。

## 完了条件

- 上記「確認」がすべて pass。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点。重点: 昇格判断の妥当性・記録の正確性・
  リンク健全性・実装コード無変更・§6-11 補正がユーザー承認範囲内か）。
- フェーズ完了報告に `/refactor_check` の判定結果を含める（CLAUDE.md）。
- 実機目視: **不要**（文書作業のみ・挙動に影響しない。実挙動の目視は task_04 で実施済）。
- 本タスク完了をもって**フェーズ 02_hotkey_validation を完了**とする。
