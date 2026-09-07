# phase.md

## フェーズ名

config_service の公開面の集約（config_service_public_surface）

## フェーズの目的

**presentation が `application/config_service/` の内部モジュールから判定名・理由コード・結果型を
直接 import している状態を解消し、公開面モジュール `contracts.py` に定義ごと集約する。**
正本 `architecture.md` §3.2 が認めている**当面の許容例外を、実装ごと解消して条項から消す**。

- **対象レイヤ**: **application**（定義場所の移動）+ **presentation**（import の付け替えのみ）。
  domain / infrastructure は不変。
- **スキーマ変更**: **なし**。**挙動不変**（判定名の値・理由コードの値・表示文言・保存 JSON を変えない）。
- **本フェーズはリファクタ**であり、機能追加・API 変更を含まない。
- 起票元: [idea_14](../../backlog/idea_14_config_service_public_surface.md)（2026-09-08 起票・
  phase 11 task_07 の `deep-reviewer` 指摘 B-2 から分離）。
- 主入力（暫定仕様）: [11_config_service_public_surface.md](../../history/11_config_service_public_surface.md)
  （**v0.3・ユーザー確定済**）。
- モード: **暫定仕様先行モード**。番号対応: **phase 12 / 暫定 11 / decisions_archive 12**。

## 確定（ユーザー 2026-09-08）

暫定仕様 11 §2 が正。要点のみ再掲する（**条項の正は暫定仕様 11**）。

- **公開面 = `config_service/contracts.py`**（新設）。**`config_service` 内の他モジュールを import しない**
  （stdlib は可）。実装モジュール側がこれを import する**一方向**。
- **定義そのものを移す**（再輸出の二重管理を作らない）。参照は **`from . import contracts` +
  `contracts.NAME`**（既存 house style。`from .contracts import NAME` は採らない）。
- **置くのは「presentation へ出す種類」= 判定名・理由コード・結果型（定数 34 / 型 9）**。
  パス表記・ファイル名・状態の内部表現（`QUARANTINE_DIR_NAME` / `UNIT_ID_PATTERN` / `ENTRY_*` /
  `CANDIDATE_DIRS` 等）は実装側に残す。
- **phase 10 由来の分（`reference_cleanup_text.py` / `reference_cleanup_io.py`）も同時に変換する**
  （2 形式を併存させない。やらないなら本フェーズを起こさない）。
- **`__init__.py` へ定数を置かない / re-export もしない**（828 行・分割保留中）。
- **テストは実装モジュールの直接 import を許す**（ただし移した定数・型は `contracts` から取る）。
- **`ConfigService` の型注釈は触らない**。
- **値の重複（`"invalid_unit_id"` / `"no_manifest"`）は意図的であり統合しない**。

## スコープ

### 含む

- `config_service/contracts.py` の新設と、**定数 34 / 型 9 の定義の移動**。
- application 5 モジュール（`parent_refs_cleanup` / `reference_scan` / `orphan_scan` / `quarantine` /
  `quarantine_manage`）の参照形式の統一。
- presentation 5 ファイルの import 付け替え。
- `tests` / `tests_ui` の該当参照（**import 22 文 + `manage.QuarantineUnit(...)` のような属性参照形**）の追随。
- **逆戻り防止テスト 3 本**（共有モジュール参照の固定 / presentation の参照先の AST 走査。
  **R1〜R3 + 属性アクセスの 4 経路**と**自己検証ケース**を含む）。
- 正本反映（`architecture.md` §3.2 の例外条項と idea_14 追跡行の削除 / `codebase_map.md`）。

### 含まない（後送り）

- `keyseq/application/save_plan.py` の `ACTION_*` を presentation が import している件（5 ファイル）。
  `config_service` の外であり、`architecture.md` §3.2 の条項対象でもない。
- `config_service/__init__.py`（828 行）の分割（`current.md` の別タスク化候補で追跡）。
- ダイアログ / IO クラス / `*_text.py` の同型スケルトンの共通化
  （phase 11 の `/refactor_check` で候補送り。着手時は
  [idea_10](../../backlog/idea_10_nested_modal_grab_restore.md) と合流させる）。
- 委譲メソッドの API 変更・型注釈・機能追加・文言変更。
- 動的 import（`importlib`）経由の逆戻り検出（**検査の限界として暫定仕様 §3-4 に明記済**）。

## このフェーズで読むファイル

1. `instructions/history/11_config_service_public_surface.md`（**主入力・v0.3**）
2. `keyseq/application/config_service/` の 5 モジュール
   （`parent_refs_cleanup.py` / `reference_scan.py` / `orphan_scan.py` / `quarantine.py` /
   `quarantine_manage.py`）— **定義の所在と相互参照**
3. `keyseq/application/config_service/path_boundary.py` / `candidate_dirs.py`
   — **葉モジュールの先行実績（形の見本）**
4. `keyseq/application/config_service/__init__.py:17`（内部モジュールの属性公開）と委譲メソッド 11 本
5. `keyseq/presentation/orphan_sweep_text.py` / `quarantine_manage_text.py` /
   `reference_cleanup_text.py` / `controllers/config_io/orphan_sweep_io.py` / `reference_cleanup_io.py`
6. `tests/test_orphan_scan.py:389-404`（**既存の固定テストの書き方**）
7. `instructions/common/spec_detail/architecture.md` §3.2 / `instructions/common/codebase_map.md`
   の `config_service` パッケージ表

## タスク

1. **task_01 公開面の新設と全参照の付け替え** — `contracts.py` を新設して定数 34 / 型 9 の**定義を移し**、
   application 5 モジュール・presentation 5 ファイル・`tests` / `tests_ui` の参照を**一度に**付け替える。
   **1 コミットの原子的変更**（暫定仕様 §3-5。段階を分けると
   `SOURCE_REDIRECTED` のように定義元で未使用の定数が途中で `ImportError` になる）。
2. **task_02 逆戻り防止テスト** — 共有モジュール参照の固定（`assertIs` + `hasattr` 偽）と、
   presentation の参照先の AST 走査（**R1〜R3 + 属性アクセス**・**自己検証ケース付き**）。
3. **task_03 正本反映（最終タスク）** — `architecture.md` §3.2 の**例外条項と idea_14 追跡行の削除**
   （**`config_service` 限定表現を保つ**）/ `codebase_map.md` へ `contracts.py` を追加し件数を 12 → 13 へ /
   暫定仕様 11 の**凍結** / `decisions_archive/12_config_service_public_surface.md` の作成 /
   `current.md` の完了記載（次採番の明記）/ `backlog/INDEX.md` の idea_14 を `INDEX_done.md` へ移動 /
   `/refactor_check` の実行。

> タスク定義ファイルは着手するタスクから順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点は次のとおり。

- **挙動不変を最優先で疑う**。判定名・理由コードの**値**が変わっていないか、
  `quarantine_manage_text.py` のラベル分岐が壊れていないか（**同値の理由コードを統合していないか**）。
- **依存方向**: `contracts.py` が `config_service` 内の他モジュールを import していないか。
  実装モジュールが `from . import contracts` + `contracts.NAME` 形式に揃っているか。
- **移行の取りこぼし**: 属性参照形（`manage.QuarantineUnit`）・型注釈での相互参照・
  `patch(...)` の文字列指定など、**import 文以外の経路**。
- **逆戻り防止テストが素通しになっていないか**（自己検証ケースが実際に検出しているか）。
- タスク単位は `reviewer`、フェーズ完了判定は `deep-reviewer` + Codex レビューの 2 本立て
  （`.claude/rules/agent_selection.md`）。**実機目視は不要**（挙動不変・UI 文言不変。暫定仕様 §5-11）。
