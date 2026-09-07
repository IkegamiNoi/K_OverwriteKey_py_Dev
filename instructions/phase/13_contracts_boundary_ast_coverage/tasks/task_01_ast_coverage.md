# task_01_ast_coverage

## 目的

**公開面の逆戻り防止テストの AST 検査が素通りする「静的な 3 経路」を塞ぐ。**
根拠は phase.md「スコープ / 含む」（A-1 / A-2）+ 起票元
[idea_15](../../../backlog/idea_15_contracts_boundary_ast_coverage.md)「現状」。

- **変更対象は `tests/test_config_service_contracts.py` の 1 ファイルのみ**。
  **プロダクションコード（`keyseq/` 配下）は 1 行も変更しない**。
- **仕様変更なし**。正本 `instructions/common/spec_detail/architecture.md` §3.2 の条項は**不変**で、
  **その条項を守れているかの検査精度を上げるだけ**。
- 現状の検査は `collect_forbidden_refs`（`:19-45`）。自己検証ケースは `:87-106`、
  「検査の限界」の docstring は `:20-23`。

## 対象範囲（`tests/test_config_service_contracts.py` 限定）

### 1. `collect_forbidden_refs` の拡張

現在の検査（**維持する**）:

- **R1**: `from keyseq.application.config_service import X` で **X が `ConfigService` / `contracts` 以外**
- **R2**: `from keyseq.application.config_service.<sub> import ...` で **`<sub>` が `contracts` 以外**
- **R3**: `import keyseq.application.config_service.<sub>` で **`<sub>` が `contracts` 以外**
- **属性アクセス（素の名前）**: `ast.Attribute` で `config_service.<内部モジュール名>`
  （`node.value` が `ast.Name` かつ `id == "config_service"`）

**追加する検査**:

- **A-2（エイリアス表の構築）**: モジュール内の `ast.Import` / `ast.ImportFrom` を先に走査し、
  **束縛名 → モジュールの完全修飾名**の対応表を作る。少なくとも次の 4 形を解決すること:
  - `import keyseq.application.config_service` → `keyseq` = `keyseq`（**`asname` なしの `import a.b.c` が
    束縛するのは先頭の `a` だけ**）
  - `import keyseq.application.config_service as cs` → `cs` = `keyseq.application.config_service`
  - `from keyseq.application import config_service` / `... as cs` →
    `config_service` / `cs` = `keyseq.application.config_service`
  - `from keyseq import application` / `... as app` → `application` / `app` = `keyseq.application`
- **A-1（属性チェーンの完全修飾名解決）**: `ast.Attribute` の連鎖を**末端の `ast.Name` まで辿って
  ドット結合**し、先頭の名前をエイリアス表で置換して**完全修飾名**を得る。
  得られた名前が **`keyseq.application.config_service.<内部モジュール名>`** に一致（またはそれで始まる）なら違反。
  - 例: `import keyseq.application.config_service` +
    `keyseq.application.config_service.quarantine_manage.delete_quarantine_unit(...)` → **違反**
  - 例: `from keyseq import application` + `application.config_service.orphan_scan` → **違反**
  - 例: `from keyseq.application import config_service as cs` + `cs.orphan_scan` → **違反**
- **違反メッセージ**: 既存の形式（`f"{lineno}: <経路> <名前>"`）に揃える。
  経路ラベルは既存の `R1` / `R2` / `R3` / `attribute` を流用してよい（新設する場合も既存と同じ粒度にする）。
- **重複の畳み込み**: `ast.walk` は入れ子の `ast.Attribute` を複数回訪れるため、
  **同一 (行番号, 解決した内部モジュール名) は 1 件に畳む**（同じ違反が 2 件以上出ない）。

### 2. 自己検証ケースの追加（既存メソッド `test_collect_forbidden_refs_detects_each_route_and_allows_public_imports` 内）

- **禁止例に 3 件追加**（それぞれ `collect_forbidden_refs` が**非空**を返すこと）:
  1. `"import keyseq.application.config_service\nkeyseq.application.config_service.orphan_scan.scan()"`
  2. `"from keyseq import application\napplication.config_service.orphan_scan"`
  3. `"from keyseq.application import config_service as cs\ncs.orphan_scan"`
- **許可例に 3 件追加**（それぞれ**空リスト**を返すこと）:
  1. `"import keyseq.application.config_service\nkeyseq.application.config_service.contracts.ORPHAN_CANDIDATE"`
  2. `"from keyseq import application\napplication.config_service.contracts"`
  3. `"from keyseq.application import config_service as cs\ncs.contracts"`
- **既存の禁止 4 例 / 許可 5 例は削除・変更しない**（追加のみ）。

### 3. docstring の「検査の限界」の更新（`:20-23`）

拡張後に**実際に残る限界だけ**を書く。すなわち **動的 import（`importlib` / `__import__`）と、
実行時に組み立てた名前による参照**（例: `getattr(pkg, name)` / 文字列連結で作ったモジュール名）。
**「変数経由の間接参照は検出できない」という一般的な書き方は、エイリアス束縛を解決できるようになるため
そのままにしない**（解決できない形＝実行時に決まる名前に限定して書く）。

### 設計メモ / 制約

- **素の名前の属性検査（既存）は残す**。`keyseq/presentation/` には
  **`config_service` という名前の変数・引数（`ConfigService` のインスタンス）が実在**し
  （`controllers/config_io/child_save_rows.py:127` の `config_service.INTERNAL_KEYMAP_DIRTY` など 31 箇所）、
  この名前は import 由来でないためエイリアス表に載らない。
  **エイリアス表だけに置き換えると、`config_service.orphan_scan` 形の検出が失われる**。
  **既存の検査と新規の検査は「和集合」**にすること。
- **誤検出を出さないこと**が最優先。とくに次を違反にしない:
  - `contracts` への参照（完全修飾・エイリアス経由を含む）
  - `INTERNAL_*` などの **`ConfigService` の公開クラス定数**（正本 §3.2 で公開 API と規定済み）
  - **エイリアス表に載っていない名前**から始まる属性チェーン
    （import 由来でない同名の変数・属性は解決しない＝違反にしない。上の「素の名前」検査の対象を除く）
- **既存アサーションを緩めない**: `INTERNAL_MODULE_NAMES` とパッケージ実ファイル一覧の一致
  （`:71-76`）/ 移した 43 名の `hasattr` 偽（`:61-63`）/ 内部仕様 6 名の残存（`:64-67`）。
- **テストメソッドは 3 本のまま**（既存メソッドへケースを足す。新規メソッドを作らない）。
  → **`tests` の件数は 417 のまま**が期待値。
- **検査対象範囲を広げない**: 走査するのは `keyseq/presentation/` 配下の `.py` のみ、
  対象は `keyseq.application.config_service` 関連の参照のみ（`save_plan` / `keymap_service` 等は対象外）。

## 含まない

- **プロダクションコード（`keyseq/` 配下）の変更**（本フェーズ全体で対象外）。
- **動的 import・実行時に組み立てた名前の検出**（**限界として docstring に書くだけ**）。
- 検査対象ディレクトリの拡大（`tests/` 自身の検査など）。
- 正本 `architecture.md` §3.2 の条項変更（**条項は不変**。phase 12 完了レビューの L-1 も対象外）。
- `decisions_archive/13` の作成・`current.md` の完了記載・idea_15 の `INDEX_done.md` 移動・
  `/refactor_check`（**task_02**）。

## 確認

1. **`verifier` の実測**（`.venv` の python。worktree ルートで実行）:
   - `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が **417 pass（skip 7）**
     — **件数が変わっていたらメソッドを増減させた疑い**
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が **288 pass（skip 0）**
   - `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass
2. **拡張が実効的であることの実測**（メインが行う）: 追加した禁止 3 例を
   `collect_forbidden_refs` へ直接渡し、**3 件とも非空**が返ること。
   許可 3 例が**空リスト**を返すこと。
3. **素通しでないことの実測**（メインが行う）: `keyseq/presentation/` の任意の 1 ファイルへ
   **禁止例 ①（完全修飾のドット参照）**を一時的に仕込むと
   `test_presentation_uses_only_config_service_public_surface` が **FAIL** し、
   復旧すると pass に戻ること。**`keyseq/` に差分を残さない**（`git diff -- keyseq` が空）。
4. `git diff -- keyseq main.py tests_ui` が**空**（変更は `tests/test_config_service_contracts.py` のみ）。
5. 既存の禁止 4 例 / 許可 5 例と、`INTERNAL_MODULE_NAMES` の一致アサーション・
   `hasattr` 偽・内部仕様 6 名の残存確認が**残っている**こと。

## 完了条件

- 上記「確認」1〜5 をすべて満たす。
- **`reviewer` による別視点レビューを通過**（`.claude/rules/review.md` の 5 観点 +
  phase.md「レビュー方針」の誤検出・検出漏れ・限界記述の観点）。
- **実機目視は不要**（テストのみの変更。phase.md「レビュー方針」）。**本タスクでも task_02 でも実施しない**。
- 残課題・想定外の差分があれば完了報告に明記する。
