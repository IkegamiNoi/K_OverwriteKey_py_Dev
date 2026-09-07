# decisions_archive: 12_config_service_public_surface

> phase 12（config_service の公開面の集約）の判断履歴。**2026-09-08 完了**。**挙動不変のリファクタ**。
> 正本は `spec_detail/architecture.md` **§3.2**（公開面 = `ConfigService` の委譲メソッド +
> `application/config_service/contracts.py`。**当面の許容例外と idea_14 の追跡行を削除**）
> + `codebase_map.md`（`config_service` パッケージ表・**13 ファイル**へ `contracts.py` を追加）。
> 暫定仕様 11（`instructions/history/11_config_service_public_surface.md`・**最終 v0.3**）は**凍結済**
> （経緯の参照用。**条項を実装の根拠に引かない**）。
> 起票元 idea_14 はクローズ（`instructions/backlog/INDEX_done.md`）。検出は phase 11 task_07 の
> `deep-reviewer` 指摘 B-2。
> **スキーマ変更なし・実機目視なし**（挙動不変・UI 文言不変のため。暫定仕様 §5-11）。
> **後続**: [idea_15](../../../instructions/backlog/idea_15_contracts_boundary_ast_coverage.md)（逆戻り防止テストの AST 検査を完全修飾・エイリアス経路まで拡張。フェーズ完了レビューの M-3 から分離）。

---

## 2026-09-08 (phase 12: config_service の公開面の集約・暫定仕様 11)

規範: [`instructions/history/11_config_service_public_surface.md`](../../../instructions/history/11_config_service_public_surface.md)
（**v0.3・ユーザー確定済**）。番号対応: **phase 12 / 暫定 11 / decisions_archive 12**。
起票元 = [idea_14](../../../instructions/backlog/idea_14_config_service_public_surface.md)。

### 【起票時の確定】§4-A〜D（ユーザー 2026-09-08）— **採用**

- **§4-A モジュール名 = `contracts.py`**（`results.py` は実態〔8 割が定数〕とずれ、
  `public_api.py` は関数群を連想させるため不採用）。
- **§4-B 粒度 = 1 ファイルに集約**（定数 34 + dataclass 9 で 120〜140 行見込み。300 行超で分割）。
- **§4-C テストは実装モジュールの直接 import を許す**（ただし**移した定数・型は `contracts` から取る**）。
  `patch.object(quarantine_module.os, ...)` のような monkeypatch 用のモジュール参照を残せるため。
  **(a)(b) で書き換え量はほぼ同じ**（v0.1 の「(b) だけ 20 箇所増える」は誤りで、レビューで訂正）。
- **§4-D `ConfigService` の型注釈は触らない**（別の関心事。混ぜると差分の意図が読みにくい）。

### 【起票時レビュー】`deep-reviewer` = 修正して採用（High 2 / Medium 7）— **全件反映**（v0.2）

- **H-1 = 移行を段階分割できない**。`SOURCE_REDIRECTED` / `SOURCE_DIRECTORY_UNREADABLE` は
  **定義元 `reference_scan.py:10-11` で未使用**（書き手は `orphan_scan.py:168,179` のモジュール属性参照）。
  「定義だけ先に移す」段階で旧 import が `ImportError` になり、途中段階が green にならない。
  → **定義移動と全参照の付け替えを 1 タスク・1 コミットの原子的変更**にした（4 段階 → 3 段階）。
- **H-2 = `from .contracts import NAME` では固定テストが書けない**（名前が実装モジュールへ再束縛され
  `hasattr` が真のまま）。→ **既存 house style `from . import contracts` + `contracts.NAME` に統一**
  （`path_boundary` / `candidate_dirs` と同形。固定テストも `assertIs` + `hasattr` 偽）。
- 員数の訂正（**contracts へ置くのは定数 34 / 型 9**。v0.1 の 33 / 8 は presentation の import 束縛数との
  取り違え）/「何も import しない」→「`config_service` 内の他モジュールを import しない」（dataclass のため
  stdlib は要る）/ 正本反映の取りこぼし（`architecture.md` の idea_14 追跡行 / `codebase_map.md` の件数）。

### 【確定前レビュー】`codex-adversarial-reviewer` = needs-attention（Medium 1）— **修正して採用**（v0.3）

**AST 検査に穴があった**。接頭辞 `keyseq.application.config_service.` だけを見ると
**`from keyseq.application.config_service import orphan_scan` 形**（`tests/test_orphan_scan.py:8-10` に実在）を
見逃す。加えて **`__init__.py:17` が内部モジュールを属性公開**しているため
`config_service.orphan_scan.<名前>` の経路も残る。
→ §3-4 を **R1〜R3 + 属性アクセスの 4 経路**へ拡張し、**動的 import は検出できない限界を明記**、
**禁止パターンを与えて検査関数が落とすことを確認する自己検証ケース**を必須にした。
あわせて移行対象へ**属性参照形（`manage.QuarantineUnit(...)`）**を明記し、tests の直参照を 21 → **22 文**へ補正。

### 【起票時】`codebase_map.md` の取りこぼしを先行是正（メイン判断 2026-09-08）

レビューが検出。`:264` が「11 ファイル」のままで、**計画08 で新設した `candidate_dirs.py` の行が無かった**
（`instructions/common/` 全体に記載 0 件）。**計画08 の取りこぼし**なので phase 12 の作業に混ぜず、
**起票と同時に是正**した（件数 11 → 12 + 行の追加）。phase 12 では `contracts.py` の追加と 12 → 13 のみ扱う。

### 【task_01】公開面の新設と全参照の付け替え（**1 コミットの原子的変更**）— `reviewer` = 完了可

- `contracts.py` を新設し、**定数 34 / 型 9 を定義ごと移動**（再輸出の二重管理を作らない）。
  **`__future__` と `dataclasses` だけを import する葉モジュール**。
- application 5 モジュール（`parent_refs_cleanup` / `reference_scan` / `orphan_scan` / `quarantine` /
  `quarantine_manage`）+ presentation 5 ファイル + `tests` / `tests_ui` を**一度に**付け替え。
- **内部仕様は実装側に残した**（`QUARANTINE_DIR_NAME` / `MANIFEST_FILE_NAME` / `UNIT_ID_PATTERN` /
  `ENTRY_*` / `CANDIDATE_DIRS` / `RESERVED_DIR`）。
- **同値の理由コード（`"invalid_unit_id"` / `"no_manifest"`）は統合していない**（意図的な重複。
  統合するとラベル分岐が壊れる）。
- 検証: compile clean / `tests` 414（skip 7・**着手時の基準値と同値**）/ `tests_ui` 288 / smoke pass。
  **前コミットとの全定数値比較で消失・変更なし**、dataclass のフィールドも不変。
- 非ブロッキング指摘 1 件（`tests/test_orphan_sweep_text.py` の `contracts` import が 3 ブロックに分裂）は
  **task_02 で解消**。

### 【task_02】逆戻り防止テスト（**プロダクション差分 0 行**）— `reviewer` = 完了可

- `tests/test_config_service_contracts.py`（新規・**3 メソッド**）:
  ①実装 5 モジュールが `contracts` を見ていることの固定（`assertIs` + **移した 43 名の `hasattr` 偽**。
  名前は `vars(contracts)` から**動的に取る**＝ハードコード列挙にしない）+ **移していない内部仕様 6 名の残存確認**
  （「全部移してしまう」方向の退行も落とす）②presentation の **AST 走査**（R1 / R2 / R3 / 属性アクセスの
  4 経路）③**検査関数の自己検証**（禁止 4 例を検出し、許可 5 例を誤検出しない）。
- **メインが 1 点強化**: `INTERNAL_MODULE_NAMES` がハードコードのため、**新モジュールが増えると
  属性アクセス経路だけ静かに素通りする**。**パッケージの実ファイル一覧とずれたら落ちる**
  アサーションを追加した（メソッド数は 3 本のまま）。
- **素通しでないことを実測で確認**: `orphan_sweep_text.py` へ禁止 import を仕込むと
  該当テストが **FAIL**（`R1 ... orphan_scan` を検出）、復旧で 3 本とも pass。`keyseq/` に差分は残らない。
- **検査の限界**: 動的 import / 変数へ束縛し直した後の間接参照は検出できない（docstring に明記済・暫定仕様 §3-4）。
  **フェーズ完了レビューで、静的な記述でも素通りする 3 経路を実測**（`deep-reviewer` M-3 / Codex medium）:
  ①`from keyseq.application import config_service as cs` + `cs.orphan_scan`（`:41-44` が `config_service` 名固定）
  ②`import keyseq.application.config_service`（パッケージ名ちょうど）+ `keyseq.application.config_service.orphan_scan.X`
  ③`from keyseq import application` + `application.config_service.orphan_scan`。
  **暫定仕様 §3-4 の 4 経路仕様には準拠**しており、**現在の presentation にこの形の参照は 0 件**（`keyseq/presentation` に `import keyseq…` / `from keyseq(.application) import …` が無い）。**残存リスクとして記録**し、検査強化はユーザー判断で後続へ回す。
- 検証: compile clean / `tests` **417**（414 → **+3**・skip 7）/ `tests_ui` 288 / smoke pass。
- あわせて**暫定仕様 §5-7 の 2 行を訂正**（テスト本数 2 → 3 本 / 期待件数 416 → 417）。
  task_02 の対象範囲外の差分だが、設計は起票時点で 3 本と決めていたため古い記述を合わせたもの。

### 【task_03】正本反映とフェーズ完了処理（**コード差分 0 行**）

- `architecture.md` **§3.2**: **例外条項（当面の許容）と idea_14 の追跡行を削除**し、
  公開面を「`ConfigService` の委譲メソッド + `config_service/contracts.py`」と規定。
  **実装モジュールの直参照は定数・型・関数のいずれも不可**へ。
  **`config_service` 限定表現を保った**（`application` 一般へ広げると presentation →
  `save_plan.ACTION_*` の 5 件が新規違反になる。同件は暫定仕様 §6 でスコープ外）。
- `codebase_map.md`: パッケージ表へ **`contracts.py` の行を追加**し件数を **12 → 13**（実ファイル数と一致）。
- 暫定仕様 11 の**凍結** / `current.md` の完了記載 / `backlog/INDEX.md` → `INDEX_done.md`。

### 【フェーズ完了判定レビュー】`deep-reviewer` = 修正して完了可 / `codex-adversarial-reviewer` = needs-attention

**両者が独立に AST 検査の穴を指摘**（下記 M-3）。受け入れ条件 §5-1〜11 は `deep-reviewer` が
**全 11 件を実測で裏取りして OK**（テストも `.venv` で再実測し 417 / 288 / smoke / compileall clean を確認）。
完了チェックリストの取りこぼしなし。

- **M-1 = `architecture.md` の公開面定義が実装事実と食い違う**（**修正して採用・ユーザー確定**）。
  「公開面は委譲メソッドと `contracts.py` の **2 つ**」と閉じて書いたため、presentation が実使用中の
  **`ConfigService` の公開クラス定数 `INTERNAL_*`（31 箇所**・`child_save_rows.py:127,144,159,167,184` /
  `keymap_file_io.py:23-24` 等）が字義上は条項違反に読める。
  → **「`ConfigService` の公開 API（委譲メソッドおよび公開クラス定数 `INTERNAL_*` 等）と `contracts.py`」**へ改めた。
  **内部モジュール直参照の禁止は不変**で規律は緩めていない。
- **L-2 = `contracts` が葉であることが正本の依存ルールに無い**（**修正して採用・ユーザー確定**）。
  `codebase_map.md` にしか無く、将来 `contracts` が実装モジュールを import しても正本上は違反にならなかった。
  → `architecture.md` §3.2 へ **「`contracts.py` は `config_service` 内の他モジュールを import しない
  （依存は実装 → `contracts` の一方向。stdlib は可）」**を 1 行追加。
- **M-3 = 逆戻り防止テストに静的経路の穴 3 件**（**ユーザー判断で本フェーズでは記録のみ → 後続へ分離**）。
  実測で確認済（`collect_forbidden_refs` を直接実行し 3 例とも `[]`）。**暫定仕様 §3-4 の 4 経路仕様には
  準拠**しており、**現在の presentation に該当参照は 0 件**。暫定仕様 11 は凍結済のため後追い改訂せず、
  検査強化は **[idea_15](../../../instructions/backlog/idea_15_contracts_boundary_ast_coverage.md)** として起票。
- **M-2 = `decisions_archive/12` の相対リンク 2 行が壊れていた**（`../../instructions/…` は
  `.claude_data/instructions/…` を指す）→ `../../../instructions/…` へ修正。
- **L-3 / L-6 も修正**（`current.md` の暫定仕様「04〜10 は起票済」→ **04〜11** /
  `phase.md` の「逆戻り防止テスト 2 本」→ **3 本**）。
- **L-1（`architecture.md` が presentation 側ファイル名を列挙）/ L-4（`current.md` の次フェーズ候補が
  phase 11 完了を未反映）/ L-8（`__init__.py:17` の submodule import 一覧に `contracts` が無い）は保留**
  （いずれも実害なし。L-4 は phase 11 完了時の取りこぼしで phase 12 由来ではない）。

### /refactor_check 判定（2026-09-08）= **不要**

対象 = `keyseq/` の変更 **11 ファイル・+263 / -297**（PHASE_BASE = `aaf6d58`。参考: `tests` / `tests_ui` は
12 ファイル・+206 / -72）。メトリクス収集は `verifier` 実測。**M1〜M6 いずれも該当なし**。

- **M1 非該当**: 600 行超のファイルなし（最大は `quarantine.py` 294 行 / 新規 `contracts.py` 126 行）。
- **M2 非該当**: 新規関数なし・80 行超の関数なし。**既存関数の本体ロジックは無変更**
  （定数・型の定義を移し参照名を `contracts.X` へ置換した機械的リネームのみ）。
- **M3 非該当**: 11 ファイルに同じ形の差分（import 差し替え + 参照名変更）が並ぶが、
  **単一目的の機械的置換**であり「同型ブロックのコピペ増殖」ではない。
- **M4 非該当**: `_KIND_LABELS` / `_REASON_LABELS` 等の列挙辞書は**エントリ数・構造とも不変**
  （参照元の定数モジュールが変わっただけ）。
- **M5 非該当**（`-- keyseq` 限定の grep でマッチ 0 件）/ **M6 非該当**（値そのものは不変で集約しただけ）。
- 提案書は作成しない。`current.md` の「別タスク化候補」への追記も不要
  （`config_service/__init__.py` の分割保留は phase 11 の記載で追跡継続）。

### 統合検証（`verifier` 実測 2026-09-08・task_03 完了時）

compileall clean / `tests` **417 pass（skip 7）** / `tests_ui` **288 pass（skip 0）** / smoke pass。
**着手時の基準値（414 / 288）+ task_02 の +3 と一致**し、退行なし。
本タスクは文書のみのため `git diff -- keyseq tests tests_ui main.py` は**空**。
