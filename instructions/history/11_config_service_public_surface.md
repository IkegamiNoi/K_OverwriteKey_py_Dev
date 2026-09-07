# 暫定仕様 11: config_service の公開面（判定名・理由コード・結果型）の集約（config_service_public_surface）

> 状態: **未凍結・v0.3・ユーザー確定済（実装着手可）・主入力**。本書がこのフェーズの確定設計
> （フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: [idea_14](../backlog/idea_14_config_service_public_surface.md)（2026-09-08 起票・
> phase 11 task_07 の `deep-reviewer` 指摘 B-2 から分離）。
> 番号対応: **phase 12 / 暫定 11 / decisions_archive 12**。
> 版履歴: v0.1 起票（2026-09-08）→ **v0.2**（同日・`deep-reviewer` = **修正して採用** を反映）:
> ①**H-1: 段階 1 で「presentation と tests が無変更でも動く」は成立しない**
> （`SOURCE_REDIRECTED` / `SOURCE_DIRECTORY_UNREADABLE` は `reference_scan` 内で未使用のため、
> 定義を移した時点で旧 import が `ImportError` になる）→ **移行を 3 段階へ再構成し、
> 定義移動と全 import 付け替えを 1 タスク・1 コミットの原子的変更にした**
> ②**H-2: `from .contracts import NAME` 形式は `hasattr` が真のままで固定テストが書けない**
> → **既存 house style（`from . import contracts` + `contracts.NAME`）に統一**
> ③員数の訂正（**contracts へ置くのは定数 34 / 型 9**。v0.1 の 33 / 8 は presentation の import 束縛数と
> 取り違えていた）④「何も import しない」→「**`config_service` 内の他モジュールを import しない**」
> （dataclass のため stdlib は要る）⑤AST テストの検査範囲の明確化
> ⑥§4-C のコスト比較の訂正 ⑦正本反映の取りこぼし（`architecture.md` の追跡行 / `codebase_map.md` の件数）。
> → **v0.3**（同日・`codex-adversarial-reviewer` = **needs-attention**〔Medium 1〕を反映 + **§4 をユーザー確定**）:
> ①**AST 検査の穴を塞いだ**。接頭辞 `keyseq.application.config_service.` だけを見ると
> **`from keyseq.application.config_service import orphan_scan` 形**（`tests/test_orphan_scan.py:8-10` に実在）を
> 見逃す。加えて **`__init__.py:17` が内部モジュールを属性公開している**ため
> `config_service.orphan_scan.<名前>` の経路も残る → **§3-4 を 3 ルール + 属性アクセス検査 +
> 検査の限界の明記 + 自己検証ケース**へ書き換えた
> ②**移行対象に属性参照形（`manage.QuarantineUnit(...)` 等）を明記**（`tests/test_quarantine_manage.py` に多数）
> ③監査数値の補正（tests の直 import は**パッケージ直下からのモジュール名 import を含めて 22 文**）
> ④**§4-A〜D をユーザー確定**（`contracts.py` / 1 ファイル集約 / テストは実装モジュール直参照可 /
> 型注釈は触らない）→ §2 へ移動。

---

## §1 目的 / 背景

**presentation が `application/config_service/` の内部モジュールから定数と結果型を直接 import している
状態を解消し、「どこを見れば presentation との契約が分かるか」を 1 箇所に定める。** 挙動は変えない。

正本 `architecture.md` §3.2 は「presentation は `config_service` の内部モジュールを直接参照しない」と
規定しつつ、**当面の許容例外**として定数と結果型の import を認めている（phase 11 task_08 で
ユーザー確定）。本フェーズはその例外を**実装ごと解消して条項から消す**。

### 現状監査（2026-09-08・メイン + `deep-reviewer` 実測）

- **presentation → 内部モジュールの直 import は 5 ファイル / import 文 7**。
  束縛される名前は **定数 33（重複を除くと 30）/ 型 7**（同じ名前を複数ファイルが取るため差が出る）。
  - `orphan_sweep_text.py:1,10,18` ← `orphan_scan`（定数 6 / 型 1）・`quarantine`（定数 5 / 型 1）・
    `reference_scan`（定数 4）
  - `quarantine_manage_text.py:3` ← `quarantine_manage`（定数 10 / 型 3）
  - `reference_cleanup_text.py:1` ← `parent_refs_cleanup`（定数 5 / 型 2）
  - `config_io/orphan_sweep_io.py:3` ← `orphan_scan`（`ORPHAN_CANDIDATE`）
  - `config_io/reference_cleanup_io.py:3` ← `parent_refs_cleanup`（`CLEANUP_TARGET` / `CLEANUP_ALL_STALE`）
- **関数・ロジックの直参照は 0 件**。実行はすべて `ConfigService` の委譲メソッド（phase 11 の 9 本 +
  phase 10 の `inspect_parent_refs` / `prune_parent_refs` = **計 11 本**）を経由する。
  **依存方向そのものは壊れていない**。
- 5 モジュールが持つ定数は **public 40 / private 2**、型は **public 9 / private 1**（`_PlannedMove`）。
  これに `candidate_dirs.py` の 2 定数を足すと定数 44。
- **`SOURCE_REDIRECTED` / `SOURCE_DIRECTORY_UNREADABLE` は定義元（`reference_scan.py:10-11`）では未使用**で、
  実際の書き手は `orphan_scan.py:168,179`（`reference_scan.SOURCE_*` のモジュール属性参照）。
  **移行順序に効く**（§3-5・H-1）。
- **`tests` / `tests_ui` からの直 import は 5 モジュール限定で 22 文**。
  内訳は**モジュールパス指定**（`from ...config_service.quarantine import ...`）と
  **パッケージ直下からのモジュール名 import**（`from keyseq.application.config_service import
  orphan_scan as orphan_scan_module`・`tests/test_orphan_scan.py:8-10` 等）の 2 形式がある。
  さらに **`manage.QuarantineUnit(...)` のような属性参照で型を使う箇所**が
  `tests/test_quarantine_manage.py` に多数あり、**これらも付け替え対象**になる。
- 既に**共有の葉モジュールが 2 つある**: `path_boundary.py`（13 行・境界判定）/
  `candidate_dirs.py`（7 行・候補側ディレクトリ。計画08 で新設）。**本フェーズの新モジュールも同じ形**。
  **参照は `from . import path_boundary` + `path_boundary.NAME` 形式**（`orphan_scan.py:6-7` /
  `quarantine.py:9-10` / `quarantine_manage.py:7`）で、固定テストは
  `assertIs(module.<名前>, <モジュール>)` + 旧名の `hasattr` 偽（`tests/test_orphan_scan.py:389-404`）。
- `config_service/__init__.py` は **828 行**で分割保留中。**ここに定数を置かない / re-export もしない**
  （1 行委譲のみという既存方針。`current.md` の別タスク化候補で追跡中）。

## §2 確定事項（ユーザー 2026-09-08）

- **今後の実装コストで評価する**（今回の修正コストでは評価しない）。この基準で
  **`__init__.py` への再輸出案は不採用**（定数を足すたびに定義 + 再輸出の 2 箇所を触ることになり、
  分割保留中の 828 行ファイルをさらに太らせる）。
- **phase 10 由来の分（`reference_cleanup_text.py` / `reference_cleanup_io.py`）も同時に変換する**。
  2 形式が併存すると次に触る人がどちらに倣うか迷うため、
  **phase 10 分をやらないなら本フェーズ自体を起こさない**。
- **挙動不変**。判定ロジック・ガード条件・文言・保存 JSON は変更しない。
- **公開面モジュール名 = `contracts.py`**（§4-A）。中身が「判定名・理由コード・結果型」= presentation との契約。
- **粒度 = 1 ファイルに集約**（§4-B）。定数 34 + dataclass 9 で **120〜140 行**の見込み
  （`implementation.md` の新規 300 行目安に収まる）。**300 行を超えたら分割**する。
- **テストは実装モジュールを直接 import してよい**（§4-C = (a)）。
  ただし**移した定数・型は `contracts` から取る**。`patch.object(quarantine_module.os, ...)` のような
  **monkeypatch 用のモジュール参照は実装モジュール経由で残してよい**。
- **`ConfigService` の委譲メソッドの型注釈は触らない**（§4-D = (a)）。本フェーズは定義場所の集約に絞る。

## §3 設計本文

### §3-1 公開面モジュールの新設

- `keyseq/application/config_service/` 直下に**公開面モジュールを 1 つ新設**する。
  名前は **`contracts.py`**（中身 = presentation との契約。`utils` / `helper` 等の雑多名は禁止）。
- **`config_service` 内の他モジュールを import しない**（`dataclasses` などの stdlib は可）。
  実装モジュール側がこれを import する **一方向**（循環しない）。
- **定義そのものを移す**（再輸出の二重管理を作らない）。移動後、実装モジュール側に同名の定義を残さない。
- **参照形式は既存 house style に揃える**: 実装モジュールは **`from . import contracts`** と書き、
  **`contracts.ORPHAN_CANDIDATE` のようにモジュール属性で参照**する。
  `from .contracts import ORPHAN_CANDIDATE` 形式は**採らない**
  （名前が実装モジュールの名前空間へ再束縛され、§3-4 の「旧定義が残っていない」を判定できなくなる）。

### §3-2 公開面へ置くもの / 置かないもの

**置く = presentation へ出す契約**（判定名・理由コード・結果型）。**合計 定数 34 / 型 9**:

| 由来 | 定数 | 型 |
|---|---|---|
| `parent_refs_cleanup`（phase 10） | `CLEANUP_TARGET` / `CLEANUP_ALL_STALE` / `CLEANUP_PROTECTED` / `CLEANUP_SKIP` / `PRUNE_FAILURE_*`（3）= **7** | `ParentRefsCleanupInspection` / `ParentRefsPruneResult` = **2** |
| `reference_scan` | `SOURCE_MISSING` / `SOURCE_UNREADABLE` / `SOURCE_REDIRECTED` / `SOURCE_DIRECTORY_UNREADABLE` = **4** | `ReferenceScanResult` = **1** |
| `orphan_scan` | `ORPHAN_*`（4）/ `KIND_*`（4）= **8** | `OrphanEntry` / `OrphanScanResult` = **2** |
| `quarantine` | `QUARANTINE_MANIFEST_WRITE_FAILED` / `QUARANTINE_MOVE_FAILED` / `QUARANTINE_UNIT_DIR_FAILED` / `QUARANTINE_ROOT_REDIRECTED` / `QUARANTINE_SOURCE_REJECTED` = **5** | `QuarantineResult` = **1** |
| `quarantine_manage` | `RESTORE_*`（6）/ `DELETE_*`（4）= **10** | `QuarantineUnit` / `QuarantineRestoreResult` / `QuarantineDeleteResult` = **3** |

**置かない = 内部仕様**（実装モジュールに残す）:
`QUARANTINE_DIR_NAME` / `MANIFEST_FILE_NAME` / `UNIT_ID_PATTERN` / `ENTRY_PLANNED` / `ENTRY_MOVED` /
`ENTRY_FAILED`（マニフェストの内部表現）/ `CANDIDATE_DIRS` / `RESERVED_DIR`（`candidate_dirs.py` のまま）/
`_PlannedMove` ほか private。

> **線引きの基準**: 「**presentation が今使っているか**」ではなく「**presentation へ出す種類か**」で決める
> （判定名・理由コード・結果型 = 出す / パス表記・ファイル名・状態の内部表現 = 出さない）。
> 前者を基準にすると、使われ始めるたびに判断が要る。この基準により、現在 presentation が使っていない
> `ORPHAN_REFERENCED` / `ORPHAN_PROTECTED` / `CLEANUP_PROTECTED` / `CLEANUP_SKIP` /
> `ReferenceScanResult` / `OrphanEntry` も公開面へ置く。

> **値の重複は意図的であり、統合しない**（MUST）。`RESTORE_ABORTED_INVALID_ID` と
> `DELETE_REJECTED_INVALID_ID` は同値 `"invalid_unit_id"`、`RESTORE_ABORTED_NO_MANIFEST` と
> `DELETE_REJECTED_NO_MANIFEST` は同値 `"no_manifest"`。**復元と削除で理由コードの名前空間を分ける設計**で、
> 1 ファイルに並ぶと「同じ値だから 1 本化」されやすいが、**統合すると
> `quarantine_manage_text.py` のラベル分岐が壊れる**（挙動変化）。

### §3-3 presentation 側の規律

- presentation は **`ConfigService` の委譲メソッド**と **`config_service.contracts`** の 2 つだけを知る。
- **実装モジュール（`orphan_scan` / `quarantine` / `quarantine_manage` / `reference_scan` /
  `parent_refs_cleanup`）を presentation から import しない**。
- 正本 `architecture.md` §3.2 の**例外条項は削除**し、「公開面 = `ConfigService` + `contracts`」と書き換える。
  **条項は `config_service` に限定した表現を保つ**（`application` 一般へ広げると、
  presentation → `keyseq.application.save_plan` の 5 件が新規違反になる。§6 でスコープ外とした分と矛盾する）。

### §3-4 旧パス経由の import を塞ぐ

§3-1 の参照形式（`from . import contracts`）を採るため、**移動した名前は実装モジュールの名前空間に
残らない**。そのうえで逆戻りを 2 本のテストで固定する:

1. **共有モジュール参照の固定**（既存実績の形・`tests/test_orphan_scan.py:389-404` に倣う）:
   5 モジュールについて `assertIs(module.contracts, contracts)` と、
   **移した名前の `hasattr` が偽**であることを確認する。
2. **presentation の参照先の固定**（**新規手法**。リポジトリに AST を使うテストは現在 0 件）:
   `keyseq/presentation/` 配下の全 `.py` を `ast` で走査する。**検査対象は
   `keyseq.application.config_service` に関わる参照のみ**で、`keyseq.application.save_plan` や
   `keyseq.application.keymap_service` 等は**検査しない**（§6 でスコープ外としているため）。
   次の **3 ルール + 属性アクセス**をすべて見る:
   - **R1**: `from keyseq.application.config_service import X` — **X は `ConfigService` と `contracts` のみ許可**。
     **`orphan_scan` などのサブモジュール名を許さない**（この形は
     `tests/test_orphan_scan.py:8-10` に実在し、**接頭辞一致だけの検査では捕まらない**）。
   - **R2**: `from keyseq.application.config_service.<sub> import ...` — **`<sub>` は `contracts` のみ許可**。
   - **R3**: `import keyseq.application.config_service.<sub>` — **同上**（`ast.Import` も検出対象）。
   - **属性アクセス**: `from keyseq.application import config_service` は許可するが、
     **`config_service.<内部モジュール名>` の属性参照を検出して落とす**
     （`__init__.py:17` が内部モジュールを属性公開しているため、この経路が残る）。
     検出は「`ast.Attribute` の `value` が `config_service` という名前で、`attr` が内部モジュール名の集合に
     含まれる」で足りる。
   - **検査の限界を明記する（MUST）**: **動的 import（`importlib` / `__import__`）や、
     変数へ束縛し直した後の間接参照は検出できない**。本テストは**静的に書かれた参照の逆戻りを防ぐもの**で、
     それ以外は規約とレビューで担保する。
   - **テスト自身の自己検証ケースを置く**: 禁止パターン（R1〜R3 と属性アクセスの各 1 例）を
     **文字列のソースとして与え、検査関数が確かに検出する**ことを確認する
     （検査が素通しになっていないことを固定するため）。

### §3-5 移行の手順（挙動不変を保つ）

**定義の移動と全 import の付け替えは 1 つの原子的な変更**にする（H-1）。
段階を分けると、`SOURCE_REDIRECTED` のように**定義元で未使用の定数**が移動した時点で
旧 import が `ImportError` になり、途中段階では green にならない。

1. **`contracts.py` 新設 + 定義の移動 + 全参照の付け替え**（application 5 モジュール /
   presentation 5 ファイル / `tests`・`tests_ui` の該当 import **22 文**）を**一度に**行う。
   付け替えは import 文だけでなく、**`manage.QuarantineUnit(...)` のような属性参照形**
   （`tests/test_quarantine_manage.py` に多数）と、**実装モジュール内の型注釈での相互参照**も対象。
2. **逆戻り防止テスト 2 本を追加**（§3-4）。
3. **正本反映**（`architecture.md` §3.2 / `codebase_map.md`）+ フェーズ完了処理。

## §4 確認事項の決着（ユーザー確定 2026-09-08）

> **4 点とも確定済み**（内容は §2 へ移動）。以下は判断の経緯。


- **§4-A モジュール名 → `contracts.py`**（`results.py` / `public_api.py` は不採用）。
  中身が「判定名・理由コード・結果型」= presentation との契約であり、`results` だと
  実態（8 割が定数）とずれ、`api` は関数群を連想させるため。
- **§4-B 粒度 → 1 ファイルに集約**（機能別 2 分割は不採用）。
  定数 34 + dataclass 9 で **120〜140 行**の見込みで 300 行目安に収まるため。**超えたら分割**する。
- **§4-C テストの扱い → (a) 実装モジュールの直接 import を許す**。
  テストは実装の内部を検証する立場であり、**`patch.object(quarantine_module.os, ...)` のような
  monkeypatch 用のモジュール参照を残せる**ため。**どちらを選んでも「移した定数・型は `contracts` から取る」
  ので書き換え量はほぼ同じ**（v0.1 の「(b) だけ 20 箇所増える」は誤りだった）。
- **§4-D `ConfigService` の型注釈 → (a) 触らない**。委譲 11 本の戻り値は多くが `Any`
  （例外: `collect_unit_paths` は `tuple[str, ...]`、`inspect_parent_refs` は `list[Any]`）だが、
  型注釈は別の関心事で、混ぜると差分の意図が読みにくくなるため**本フェーズでは扱わない**。

## §5 受け入れ条件（ドラフト）

1. `config_service/contracts.py` が存在し、**`config_service` 内の他モジュールを import していない**（§3-1）。
2. §3-2 の表にある**定数 34 / 型 9 の定義が `contracts.py` にあり**、実装モジュール側に同名定義が
   **残っていない**（`hasattr` が偽・§3-4）。
3. **内部仕様の定数（`QUARANTINE_DIR_NAME` / `UNIT_ID_PATTERN` / `ENTRY_*` 等）は実装モジュールに
   残っている**（§3-2）。
4. 実装モジュール 5 本が **`from . import contracts` + `contracts.NAME`** の形で参照している（§3-1）。
5. **presentation 配下から `config_service.contracts` 以外の内部モジュールへ到達する静的な参照が
   0 件**であることを AST 走査のテストが固定している。**R1〜R3 と属性アクセスの 4 経路すべて**を検査し、
   **禁止パターンを検出できることの自己検証ケース**を持つ（§3-4）。
6. **`tests` / `tests_ui` でも、移した定数・型は `contracts` から import している**（§4-C の但し書き）。
7. `tests` / `tests_ui` / smoke が**着手時の実測件数（追加分を除く）から減らずに pass** し、
   `compileall` が clean。**基準件数は着手時に `verifier` が実測して本節へ記入する**。
8. 正本 `architecture.md` §3.2 から**例外条項と idea_14 の追跡行が消え**、
   公開面が「`ConfigService` + `contracts`」と規定されている（**`config_service` 限定表現を保つ**・§3-3）。
9. `codebase_map.md` の `config_service` パッケージ表に **`contracts.py` の行があり、件数表記が実体と一致**する。
10. **挙動不変**（判定名の値・理由コードの値・表示文言・保存 JSON がいずれも変わらない）。
    **値の重複（`"invalid_unit_id"` / `"no_manifest"`）を統合していない**（§3-2）。
11. **実機目視は不要**（挙動不変・UI 文言不変のため。フェーズ完了判定はテストの実測で行う）。

## §6 スコープ外（本フェーズでやらない）

- `keyseq/application/save_plan.py` の `ACTION_*` を presentation が import している件（5 ファイル）。
  `config_service` の外であり、`architecture.md` §3.2 の条項対象でもない。
- `config_service/__init__.py`（828 行）の分割（`current.md` の別タスク化候補で追跡）。
- ダイアログ / IO クラス / `*_text.py` の同型スケルトンの共通化（phase 11 の `/refactor_check` で候補送り。
  着手するなら [idea_10](../backlog/idea_10_nested_modal_grab_restore.md) と合流させる）。
- 委譲メソッドの API 変更・機能追加・文言変更。

## §7 正本反映（フェーズ末昇格・予定）

- `spec_detail/architecture.md` **§3.2**（**必須**）: 例外条項（`:16-19`）と
  **idea_14 の追跡行（`:20-21`）**を削除し、公開面を「`ConfigService` の委譲メソッド +
  `config_service.contracts`」と規定する。**`config_service` 限定表現を保つ**。
- `instructions/common/codebase_map.md`: パッケージ表へ **`contracts.py` を追加**し、
  **「presentation はここと `ConfigService` だけを見る」**旨を明記する。
  （**`candidate_dirs.py` の行の追加と件数 11 → 12 の訂正は、計画08 の取りこぼしとして
  2026-09-08 に先行実施済**。本フェーズは `contracts.py` の行の追加と件数 12 → 13 のみ）。
- 実装 / テスト: `config_service/contracts.py`（新規）/ 実装モジュール 5 本 / presentation 5 ファイル /
  `tests`・`tests_ui` の該当 import / 逆戻り防止テスト 2 本。
- `.claude_data/state/decisions_archive/12_config_service_public_surface.md` の作成 /
  本書の凍結 / `instructions/phase/current.md` の完了記載 /
  `instructions/backlog/INDEX.md` の idea_14 を `INDEX_done.md` へ。

## 関連

- 起票元: [idea_14](../backlog/idea_14_config_service_public_surface.md)。
  検出は phase 11 task_07 の `deep-reviewer` 指摘 B-2（`integration_result.md` §3-3）。
- 正本: [`spec_detail/architecture.md`](../common/spec_detail/architecture.md) **§3.2**（依存ルール）/
  [`codebase_map.md`](../common/codebase_map.md)（`config_service` パッケージ表）。
- 先行実績: `path_boundary.py`（phase 11 task_07b・境界判定の単一定義）/
  `candidate_dirs.py`（計画08・候補側ディレクトリの単一定義）。**同じ「葉モジュール」方式**。
- 判断の経緯: `.claude_data/state/decisions_archive/11_orphan_child_file_sweep.md`（task_08 の B-2）。
