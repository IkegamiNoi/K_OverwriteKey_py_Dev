# phase.md

## フェーズ名

公開面の逆戻り防止テストの検査範囲の拡張（contracts_boundary_ast_coverage）

## フェーズの目的

**phase 12 で作った公開面の逆戻り防止テスト（`tests/test_config_service_contracts.py`）の AST 検査が、
動的 import でも変数経由でもない「静的な記述」のまま素通りする 3 経路を塞ぐ。**
`ast.Attribute` の連鎖を**完全修飾名へ解決**し、`import` / `from ... import` の
**`asname`（エイリアス束縛）を追跡**する形へ拡張する。

- **対象レイヤ**: **テストのみ**（`tests/`）。**プロダクションコード（`keyseq/`）は変更しない**。
- **スキーマ変更**: なし。**挙動不変**（アプリの動作・UI 文言・保存 JSON は一切変わらない）。
- **仕様変更**: なし。正本 `architecture.md` §3.2 の条項は**不変**で、**その検査精度を上げるだけ**。
- 起票元: [idea_15](../../backlog/idea_15_contracts_boundary_ast_coverage.md)（2026-09-08 起票・
  phase 12 のフェーズ完了レビューで `deep-reviewer` M-3 と `codex-adversarial-reviewer` が
  **独立に同じ穴**を指摘したものを分離）。
- 主入力（暫定仕様）: **なし（直接改訂モード）**。設計は idea_15「提案（方向性）」の**案 A**が出発点。
- モード: **直接改訂モード**。番号対応: **phase 13 / 暫定仕様なし / decisions_archive 13**。

## 確定（ユーザー 2026-09-08）

- **idea_15 の案 A（検査の強化）を採る**（案 B = 文言の正確化のみ、は不採用）。
- phase 12 の暫定仕様 11 は**凍結済のため後追い改訂しない**。本フェーズの設計判断は
  `decisions_archive/13_contracts_boundary_ast_coverage.md` に記録する。

## スコープ

### 含む

- `tests/test_config_service_contracts.py` の `collect_forbidden_refs` の拡張:
  - **A-1**: `ast.Attribute` の連鎖を末端から結合して**完全修飾名**へ解決し、
    `keyseq.application.config_service.<内部モジュール>` で終わる参照を違反とする
    （`import keyseq.application.config_service` + `keyseq.application.config_service.orphan_scan.X` /
    `from keyseq import application` + `application.config_service.orphan_scan` の 2 経路）。
  - **A-2**: `Import` / `ImportFrom` の **`asname` を収集**して別名 → 実体のマップを作り、
    `from keyseq.application import config_service as cs` + `cs.orphan_scan` を解決する。
- **自己検証ケースの追加**: 上記 3 経路の**禁止例**と、対応する `contracts` 参照の**許可例**
  （例: `import keyseq.application.config_service` + `keyseq.application.config_service.contracts.X` /
  `from keyseq.application import config_service as cs` + `cs.contracts`）。
- **docstring の「検査の限界」の更新**（残る限界＝動的 import / 実行時に組み立てた名前 のみになるよう書き直す）。
- `decisions_archive/13` の作成・`current.md` の完了記載・idea_15 の `INDEX_done.md` 移動・`/refactor_check`。

### 含まない（後送り）

- **プロダクションコード（`keyseq/` 配下）の変更**。本フェーズはテストのみ。
- **検査対象範囲の拡大**: 検査するのは引き続き **`keyseq/presentation/` 配下**の
  **`keyseq.application.config_service` 関連の参照のみ**。`save_plan` / `keymap_service` /
  `app_state` などは対象にしない（phase 12 の暫定仕様 §6 と同じ線引き）。
- **動的 import（`importlib` / `__import__`）や実行時に組み立てた名前の検出**（原理的な限界として据え置き）。
- 正本 `architecture.md` §3.2 の条項変更（**条項は不変**。phase 12 完了レビューの L-1
  〔presentation 側ファイル名の列挙が陳腐化しやすい〕も本フェーズでは扱わない）。
- `config_service/__init__.py`（828 行）の分割（`current.md` の別タスク化候補で追跡継続）。

## このフェーズで読むファイル

1. `tests/test_config_service_contracts.py`（**唯一の変更対象**。`collect_forbidden_refs` は `:19-45`、
   自己検証ケースは `:87-106`、docstring の限界記述は `:20-23`）
2. `instructions/backlog/idea_15_contracts_boundary_ast_coverage.md`（**主入力**。素通りする 3 経路の実測結果）
3. `instructions/common/spec_detail/architecture.md` §3.2（**検査が守るべき条項**。**変更しない**）
4. `keyseq/application/config_service/__init__.py:17`（内部モジュールの属性公開＝属性アクセス経路が残る理由）
5. `.claude_data/state/decisions_archive/12_config_service_public_surface.md`
   （phase 12 の判断。**値の重複を統合しない**等の確定事項と、M-3 の経緯）

## タスク

1. **task_01 検査関数の拡張と自己検証の追加** — `collect_forbidden_refs` に完全修飾名の解決（A-1）と
   `asname` の追跡（A-2）を実装し、自己検証ケースへ 3 経路の禁止例・対応する許可例を追加する。
   docstring の限界記述を更新する。**テストメソッド数は 3 本のまま**（既存メソッド内へケースを足す）で、
   **`tests` の件数は 417 のまま変わらない**のが期待値。
   **現在の `keyseq/presentation/` は違反 0 件**なので、拡張後も**全テストが pass すること**が前提
   （落ちたら誤検出を疑う）。
1b. **task_01b 相対 import 経路の追加検査** — `from ...application.config_service import orphan_scan` 形は
   R1〜R3 のいずれにも当たらず素通りするため、`collect_forbidden_refs` に `package` 引数を足して
   **相対 import を絶対モジュール名へ解決**して検査する（解決できない場合は末尾パターン一致へ縮退）。
   **task_01 完了後にユーザー判断で本フェーズへ追加**（2026-09-08）。
2. **task_02 記録とフェーズ完了処理（最終タスク）** — `decisions_archive/13_contracts_boundary_ast_coverage.md`
   の作成 / `current.md` の完了記載（次採番の明記）/ `backlog/INDEX.md` の idea_15 を `INDEX_done.md` へ移動 /
   `/refactor_check` の実行と判定の記載。
   **正本 `spec_detail/` の改訂は不要**（仕様変更がないため。この判断自体を `decisions_archive/13` に記録する）。

> タスク定義ファイルは着手するタスクから順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点は次のとおり。

- **誤検出（false positive）を最優先で疑う**。`contracts` への完全修飾参照・エイリアス経由の
  `contracts` 参照・`config_service` と無関係な同名属性（例: 別モジュールの `orphan_scan` という名前）を
  違反にしていないか。**現在の presentation で 1 件も落ちないこと**が最低条件。
- **検出漏れ（false negative）**: 3 経路それぞれの**自己検証ケースが実際に検出している**か
  （検査関数が常に空リストを返す実装でも通ってしまう形になっていないか）。
- **限界の記述が実態と一致しているか**（拡張後に残る限界だけが docstring に書かれているか）。
- **スコープの逸脱**: `keyseq/` に差分が出ていないか（`git diff -- keyseq` が空）。
  検査対象範囲を `config_service` 以外へ広げていないか。
- **既存アサーションを緩めていないか**（`INTERNAL_MODULE_NAMES` とパッケージ実ファイル一覧の
  一致アサーション・移した 43 名の `hasattr` 偽・内部仕様 6 名の残存確認）。
- タスク単位は `reviewer`、フェーズ完了判定は `deep-reviewer` + Codex レビューの 2 本立て
  （`.claude/rules/agent_selection.md`）。**実機目視は不要**（テストのみの変更）。
