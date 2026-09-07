# task_01_contracts_module

## 目的

**公開面モジュール `config_service/contracts.py` を新設し、判定名・理由コード・結果型の定義を移して、
全参照を一度に付け替える。** 根拠は phase.md タスク 1 + 暫定仕様 11 **§3-1 / §3-2 / §3-5-1**。

- **挙動不変**（判定名の値・理由コードの値・表示文言・保存 JSON を変えない）。
- **1 コミットの原子的変更**にする。段階を分けてはならない（下記「なぜ分割できないか」）。
- **レイヤ**: application（定義場所の移動）+ presentation（import の付け替えのみ）。domain / infrastructure は不変。

### なぜ分割できないか（暫定仕様 §3-5・起票時レビュー H-1）

`SOURCE_REDIRECTED` / `SOURCE_DIRECTORY_UNREADABLE` は**定義元 `reference_scan.py:10-11` では未使用**で、
実際の書き手は `orphan_scan.py:168,179`（`reference_scan.SOURCE_*` のモジュール属性参照）。
**定義だけ先に移すと、その時点で presentation / tests の旧 import が `ImportError`** になり、
途中段階が green にならない。**定義の移動と全参照の付け替えは同時に行う**。

## 対象範囲

### 1. `keyseq/application/config_service/contracts.py`（新規）

**`config_service` 内の他モジュールを import しない**（`dataclasses` などの stdlib は可）。
先行実績 `path_boundary.py` / `candidate_dirs.py` と同じ「葉モジュール」。

**移す定義（定数 34 / 型 9）** — 由来モジュールごとにまとめ、由来が分かるコメントを付ける:

| 由来 | 定数 | 型 |
|---|---|---|
| `parent_refs_cleanup` | `CLEANUP_TARGET` / `CLEANUP_ALL_STALE` / `CLEANUP_PROTECTED` / `CLEANUP_SKIP` / `PRUNE_FAILURE_UNREADABLE` / `PRUNE_FAILURE_INVALID_DATA` / `PRUNE_FAILURE_SAVE_FAILED` | `ParentRefsCleanupInspection` / `ParentRefsPruneResult` |
| `reference_scan` | `SOURCE_MISSING` / `SOURCE_UNREADABLE` / `SOURCE_REDIRECTED` / `SOURCE_DIRECTORY_UNREADABLE` | `ReferenceScanResult` |
| `orphan_scan` | `ORPHAN_CANDIDATE` / `ORPHAN_REFERENCED` / `ORPHAN_PROTECTED` / `ORPHAN_EXCLUDED` / `KIND_KEYMAP` / `KIND_TRIGGER_SET` / `KIND_SEQUENCE` / `KIND_HOTKEY_PRESETS` | `OrphanEntry` / `OrphanScanResult` |
| `quarantine` | `QUARANTINE_MANIFEST_WRITE_FAILED` / `QUARANTINE_MOVE_FAILED` / `QUARANTINE_UNIT_DIR_FAILED` / `QUARANTINE_ROOT_REDIRECTED` / `QUARANTINE_SOURCE_REJECTED` | `QuarantineResult` |
| `quarantine_manage` | `RESTORE_SKIPPED_EXISTS` / `RESTORE_REJECTED_TARGET` / `RESTORE_SOURCE_MISSING` / `RESTORE_FAILED` / `RESTORE_ABORTED_INVALID_ID` / `RESTORE_ABORTED_NO_MANIFEST` / `DELETE_REJECTED_INVALID_ID` / `DELETE_REJECTED_IS_ROOT` / `DELETE_REJECTED_NO_MANIFEST` / `DELETE_FAILED` | `QuarantineUnit` / `QuarantineRestoreResult` / `QuarantineDeleteResult` |

**移さない（実装モジュールに残す）**: `QUARANTINE_DIR_NAME` / `MANIFEST_FILE_NAME` / `UNIT_ID_PATTERN` /
`ENTRY_PLANNED` / `ENTRY_MOVED` / `ENTRY_FAILED` / `CANDIDATE_DIRS` / `RESERVED_DIR`（`candidate_dirs.py` のまま）/
`_PlannedMove` ほか private。

**値は 1 文字も変えない**（`"invalid_unit_id"` と `"no_manifest"` が**別名で同値なのは意図的**。
**統合すると `quarantine_manage_text.py` のラベル分岐が壊れる**）。
dataclass はフィールド名・型・`frozen=True` を含め**現状のまま移す**。

### 2. application 5 モジュールの参照差し替え

`parent_refs_cleanup.py` / `reference_scan.py` / `orphan_scan.py` / `quarantine.py` / `quarantine_manage.py`。

- **`from . import contracts` と書き、`contracts.ORPHAN_CANDIDATE` のようにモジュール属性で参照する**。
  **`from .contracts import ORPHAN_CANDIDATE` 形は禁止**（名前が実装モジュールへ再束縛され、
  task_02 の「旧定義が残っていない」固定テストが書けなくなる）。既存の
  `from . import candidate_dirs, path_boundary`（`orphan_scan.py:6-7`）と同じ形。
- **型注釈での相互参照も差し替える**（例: `quarantine.py:75,103,112,159` の `orphan_scan.OrphanEntry`
  → `contracts.OrphanEntry`）。
- **内部仕様の参照はそのまま**（例: `quarantine_manage.py:55,69` の `quarantine.UNIT_ID_PATTERN` /
  `quarantine.MANIFEST_FILE_NAME` は**変更しない**）。
- **関数の呼び出しは変えない**（`orphan_scan.scan_orphans` / `quarantine.quarantine_root` 等はそのまま）。

### 3. presentation 5 ファイルの import 付け替え

`orphan_sweep_text.py` / `quarantine_manage_text.py` / `reference_cleanup_text.py` /
`controllers/config_io/orphan_sweep_io.py` / `controllers/config_io/reference_cleanup_io.py`。

- **`from keyseq.application.config_service import contracts`** の 1 本にまとめ、
  参照は `contracts.NAME` にする（**`from ...contracts import NAME` 形は presentation でも使わない**。
  task_02 の AST 検査を単純に保つため）。
- **実装モジュール（`orphan_scan` / `quarantine` / `quarantine_manage` / `reference_scan` /
  `parent_refs_cleanup`）への import を 1 つも残さない**。

### 4. `tests` / `tests_ui` の追随

- 対象は **`from keyseq.application.config_service...` の該当 import 27 行**と、
  **属性参照形 29 箇所**（`tests/test_quarantine_manage.py` の `manage.QuarantineUnit(...)` /
  `manage.DELETE_REJECTED_IS_ROOT` など）。
- **移した定数・型は `contracts` から取る**（`contracts.QuarantineUnit(...)` 等）。
- **実装モジュールの直接 import は残してよい**（ユーザー確定 §4-C = (a)）。
  `patch.object(quarantine_module.os, ...)` のような **monkeypatch 用のモジュール参照はそのまま**。
- **既存テストのアサーションを緩めない**。件数を減らさない。

## 対象外（触らない）

- **`config_service/__init__.py`**（828 行）。**定数を置かない・re-export もしない・型注釈も変えない**
  （§4-D 確定）。ただし **`:17` の `from . import ...` に `contracts` を足す必要はない**
  （実装モジュール側が import するため）。
- `keyseq/application/save_plan.py` の `ACTION_*`（presentation が import しているが**スコープ外**）。
- **task_02 の逆戻り防止テスト**（別タスク。ここでは追加しない）。
- 正本 `instructions/` の更新（**task_03**）。
- 判定ロジック・ガード条件・命名・関数分割・型注釈の追加などの「ついで」の改善。

## 確認

1. `contracts.py` が `config_service` 内の他モジュールを import していない。
2. **定数 34 / 型 9 が `contracts.py` にあり、実装モジュール側に同名定義が残っていない**。
3. 実装モジュール 5 本が **`from . import contracts` + `contracts.NAME`** の形になっている。
4. presentation 5 ファイルに**実装モジュールへの import が 1 つも無い**。
5. **値が 1 つも変わっていない**（`"invalid_unit_id"` / `"no_manifest"` の重複も**そのまま**）。
6. `verifier` の実測で **`tests` / `tests_ui` が着手時の基準件数から減らず pass**、
   `compileall` clean、smoke pass。**worktree ルートへ `user/` `quarantine/` が生成されない**。
7. `reviewer` による別視点レビューを通過（`.claude/rules/review.md` の 5 観点）。

## 完了条件

- 上記「確認」1〜7 をすべて満たす。
- **1 コミットにまとまっている**（定義移動と全参照の付け替えが分割されていない）。
- 残課題・想定外の差分があれば完了報告に明記する。
