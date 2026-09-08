# task_01c_relative_alias_binding

## 目的

**相対 import で束縛したエイリアス経由の内部モジュール参照が検査を素通りする穴と、
同名エイリアスの上書きで違反が消える穴を塞ぐ。**
`deep-reviewer`（H-1）と `codex-adversarial-reviewer`（medium ①②）が**独立に指摘**した点で、
**ユーザー判断により本フェーズ内で是正する**（2026-09-08）。

- **変更対象は `tests/test_config_service_contracts.py` の 1 ファイルのみ**。
  **プロダクションコード（`keyseq/` 配下）は 1 行も変更しない**。**仕様変更なし**。
- **実測済みの現象**（メイン確認・`package="keyseq.presentation"`）:
  - `from ..application import config_service as cs` + `cs.orphan_scan` → **検出 0 件**
  - `from .. import application as app` + `app.config_service.orphan_scan` → **検出 0 件**
  - 参考: **絶対 import の同型**（`from keyseq.application import config_service as cs`）は**検出される**
    ＝ **絶対と相対で非対称**になっている。
  - 違反する `import ... as cs` の後に別スコープで許可の `... contracts as cs` があると
    **後の束縛が前を上書き**して違反が消える → **検出 0 件**。
- 原因は、エイリアス表の構築が **`node.level == 0`（絶対 import）だけ**を登録していること
  （`tests/test_config_service_contracts.py:38`）と、表が**モジュール全体で単一の辞書**であること（`:32`）。

## 対象範囲（`tests/test_config_service_contracts.py` 限定）

### 1. エイリアス表へ相対 import を登録する

- `ImportFrom` の **`level > 0` も登録対象**にする。解決には **task_01b の R4 と同じロジック**
  （`package` から `level - 1` 個の末尾セグメントを落として `node.module` を連結）を使う。
  - **R4 の解決処理と重複実装しない**。共通の小さなヘルパ（例: `_resolve_relative_module(package, node)`）へ
    切り出して**両方が同じ実装を見る**ようにする（片方だけ直すとずれるため）。
  - 例: `package="keyseq.presentation"` + `from ..application import config_service as cs`
    → `cs` = `keyseq.application.config_service`
  - 例: `package="keyseq.presentation"` + `from .. import application as app`
    → `app` = `keyseq.application`
- **解決できない場合（`package` が空 / `level` が深すぎる）は登録しない**（誤った絶対名を作らない）。
  この縮退は**限界として docstring に残す**（下記 4）。

### 2. 同名エイリアスの上書きを防ぐ

- エイリアス表を **`dict[str, set[str]]`（名前 → 束縛先の集合）**にする。
- 属性チェーンの解決では、**その名前に束縛されたいずれかの候補が内部モジュールへ解決されたら違反**とする
  （保守的側に倒す）。**スコープ解析は行わない**（AST 全体で 1 つの表のまま）。
- **違反メッセージは 1 件に畳む**（既存の `(行番号, 内部モジュール名)` キーをそのまま使う。
  同じ行から複数候補が当たっても 2 件出さない）。

### 3. 既存検査は変更しない

- **R1 / R2 / R3 / R4 / R4-fallback・素の名前の属性検査は一切変更しない**。
  本タスクは**エイリアス表の構築だけ**を直す。
- 既存の自己検証ケース（**禁止 10 例 / 許可 11 例**）は**内容を変えない**。

### 4. 自己検証ケースの追加（既存メソッド内・**新規メソッドを作らない**）

- **禁止例に 3 件追加**（**非空**を返すこと）:
  1. `("from ..application import config_service as cs\ncs.orphan_scan", "keyseq.presentation")`
  2. `("from .. import application as app\napp.config_service.orphan_scan", "keyseq.presentation")`
  3. 同名エイリアスの上書き: 違反する束縛と許可の束縛が**同じ名前**に来る 2 行の例
     （例: `import keyseq.application.config_service as cs` の後に
     `from keyseq.application.config_service import contracts as cs`）
- **許可例に 2 件追加**（**空リスト**を返すこと）:
  1. `("from ..application.config_service import contracts as c\nc.ORPHAN_CANDIDATE", "keyseq.presentation")`
  2. `("from .. import application as app\napp.config_service.contracts", "keyseq.presentation")`

### 5. docstring の限界記述を実態へ更新

本タスク適用後に**実際に残る限界だけ**を書く:

1. 動的 import（`importlib` / `__import__`）
2. 実行時に組み立てた名前（`getattr(pkg, name)` / 文字列連結）
3. **代入による再束縛**（`x = config_service` の `x`）
4. **縮退時**（`package` を渡さない / `level` が深すぎる）は相対 import を解決できないため、
   **エイリアス登録もされず**、`from . import X` 形も末尾一致で判定できない
   （**presentation の走査では `package` を必ず渡すので発生しない**）

**「エイリアス解決は絶対 import だけ」という趣旨の記述は削除する**（本タスクで解消するため）。

### 設計メモ / 制約

- **誤検出を出さないこと**が最優先。とくに:
  - 相対・絶対いずれの経路でも **`contracts` への参照を違反にしない**
  - **同一パッケージ内の兄弟参照**（`from .io_dialogs import IoDialogs`。presentation に 16 件実在）を
    エイリアス表に載せても、**内部モジュールへ解決されないので違反にならない**こと
  - `ConfigService` の公開クラス定数 `INTERNAL_*` を違反にしない
- **テストメソッドは 3 本のまま**（既存メソッドへケースを足す）。→ **`tests` の件数は 417 のまま**が期待値。
- **既存アサーションを緩めない**（`INTERNAL_MODULE_NAMES` の実ファイル一致 / 移した 43 名の `hasattr` 偽 /
  内部仕様 6 名の残存）。
- **検査対象範囲を広げない**（走査は `keyseq/presentation/` 配下のみ・対象は `config_service` 関連のみ）。

## 含まない

- **プロダクションコード（`keyseq/` 配下）の変更**。
- **スコープ解析**（関数・クラス単位でのエイリアス有効範囲の追跡）。**保守的な集合判定で足りる**とする。
- **代入による再束縛の追跡**（限界として残す）。
- `collect_forbidden_refs` の**分割リファクタ**（提案書
  [09_refactor_contracts_boundary_ast_coverage](../../../modified_proposal/09_refactor_contracts_boundary_ast_coverage.md)・
  **未承認**。本タスクでは行わない。ただし 1 のヘルパ切り出しは**重複実装を避けるため**に必要な最小分割）。
- 記録・`current.md`・`INDEX_done.md` の更新（**task_02**。本タスクの成果も task_02 で記録する）。

## 確認

1. **`verifier` の実測**（`.venv` の python。worktree ルート）:
   - `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が **417 pass（skip 7）**
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が **288 pass（skip 0）**
   - `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass
2. **穴が塞がったことの実測**（メインが行う）: 目的節に挙げた**素通り 3 例が検出される**こと。
3. **誤検出がないことの実測**（メインが行う）: 追加した許可 2 例が空を返すこと。
   **絶対 import 側の既存挙動が変わっていない**こと（既存の禁止 10 例 / 許可 11 例が同じ判定）。
4. **素通しでないことの実測**（メインが行う）: `keyseq/presentation/` の 1 ファイルへ
   **相対 import + エイリアス**の禁止参照を仕込むと該当テストが **FAIL** し、復旧で pass に戻ること。
   **`keyseq/` に差分を残さない**。
5. `git diff -- keyseq main.py tests_ui` が**空**。

## 完了条件

- 上記「確認」1〜5 をすべて満たす。
- **`reviewer` による別視点レビューを通過**（`.claude/rules/review.md` の 5 観点 +
  phase.md「レビュー方針」の誤検出・検出漏れ・限界記述の観点）。
- **実機目視は不要**（テストのみの変更）。
- 残課題・想定外の差分があれば完了報告に明記する。
