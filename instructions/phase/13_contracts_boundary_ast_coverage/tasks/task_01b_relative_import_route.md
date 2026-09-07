# task_01b_relative_import_route

## 目的

**相対 import 経由（`from ...application.config_service import orphan_scan`）で内部モジュールへ戻る参照が、
AST 検査を素通りする穴を塞ぐ。** 現在の R1 / R2 / R3 はいずれも
**絶対 import の完全修飾名（`keyseq.application.config_service…`）で始まる形しか見ていない**ため、
相対 import は `node.module` が `application.config_service`（level > 0）となり一致しない。

- **task_01 の完了後にユーザー判断で追加した枝番タスク**（2026-09-08・本フェーズに含める判断）。
- **変更対象は `tests/test_config_service_contracts.py` の 1 ファイルのみ**。
  **プロダクションコード（`keyseq/` 配下）は 1 行も変更しない**。
- **仕様変更なし**。正本 `architecture.md` §3.2 の条項は**不変**で、**検査精度を上げるだけ**。
- **現状の実害はない**（`keyseq/presentation/` の相対 import は**同一パッケージ内の兄弟参照 16 件のみ**で、
  `keyseq.application` へ到達するものは **0 件**。house style は絶対 import）。**将来の逆戻りを防ぐ**のが目的。

## 対象範囲（`tests/test_config_service_contracts.py` 限定）

### 1. `collect_forbidden_refs` のシグネチャ変更

```python
def collect_forbidden_refs(source: str, package: str = "") -> list[str]:
```

- `package` = **その `source` が属するパッケージのドット表記**
  （例: `keyseq/presentation/controllers/config_io/orphan_sweep_io.py` なら
  `"keyseq.presentation.controllers.config_io"`）。**モジュール名自身は含めない**。
- **既存の呼び出し形（`collect_forbidden_refs(source)`）を壊さない**（第 2 引数は既定値つき）。

### 2. 相対 import（`node.level > 0`）の解決と検査

- **R4（解決できる場合）**: `package` を `.` で分割し、**`level - 1` 個の末尾セグメントを落として**
  基準パッケージを求め、`node.module`（あれば）を連結して**絶対モジュール名**を得る。
  - 例: `package="keyseq.presentation"`・`from ..application.config_service import orphan_scan`
    （level=2 / module=`application.config_service`）→ `keyseq.application.config_service`
  - 得られた絶対名に対して、**R1 / R2 と同じ判定**を適用する
    （`== CONFIG_SERVICE_PACKAGE` なら import 名が `ConfigService` / `contracts` 以外で違反 /
    `prefix` で始まるなら先頭セグメントが `contracts` 以外で違反）。
  - `from . import X` のように `node.module` が `None` の形も扱う
    （基準パッケージ自体が `config_service` なら `X` が内部モジュール名で違反）。
- **R4-fallback（解決できない場合）**: `package` が空、または **`level` が `package` の深さを超える**ときは
  絶対名を組み立てられない。この場合は **`node.module` の末尾側のパターン一致**で判定する
  （`config_service` というセグメントを含み、その次のセグメントが `contracts` 以外なら違反。
  `config_service` で終わるなら import 名が `ConfigService` / `contracts` 以外で違反）。
  **「解決できないから素通し」にしない**のが本タスクの要点。
- **既存の R1 / R2 / R3・属性アクセス検査（素の名前 / 完全修飾 / エイリアス）は一切変更しない**。
  相対 import は**追加の経路**として扱う。
- 違反メッセージは既存の形式（`f"{lineno}: <経路> <名前>"`）に揃え、経路ラベルは **`R4`** とする。

### 3. 呼び出し側（`test_presentation_uses_only_config_service_public_surface`）

- 走査する各ファイルについて **`package` を実パスから算出して渡す**。
  リポジトリルート（`Path(__file__).resolve().parents[1]`）からの相対パスを `.` 連結し、
  **ファイル名自身（`.py` の stem）は除く**。`__init__.py` の場合は**そのファイルが置かれた
  ディレクトリ自体がパッケージ**なので、同様に親ディレクトリまでを連結する
  （`keyseq/presentation/controllers/config_io/__init__.py` → `keyseq.presentation.controllers.config_io`）。
- **走査対象・アサーションは変更しない**（`forbidden == []`）。

### 4. 自己検証ケースの追加（既存メソッド内・**新規メソッドを作らない**）

第 2 引数を渡すケースが必要なため、**既存の禁止例 / 許可例のタプルは
`(source, package)` の組を扱える形へ拡張してよい**（既存の**禁止 7 例 / 許可 8 例**の**内容は変えない**。
起票時に「10 例 / 11 例」と書いていたのは数え間違いで、実測は 7 / 8）。

- **禁止例に 3 件追加**（`collect_forbidden_refs` が**非空**を返すこと）:
  1. `("from ..application.config_service import orphan_scan", "keyseq.presentation")` — R4（解決あり）
  2. `("from ..application.config_service.orphan_scan import ORPHAN_CANDIDATE", "keyseq.presentation")`
  3. `("from ..application.config_service import orphan_scan", "")` — **R4-fallback（解決なし）**
- **許可例に 3 件追加**（**空リスト**を返すこと）:
  1. `("from ..application.config_service import ConfigService, contracts", "keyseq.presentation")`
  2. `("from ..application.config_service.contracts import ORPHAN_CANDIDATE", "keyseq.presentation")`
  3. `("from .io_dialogs import IoDialogs", "keyseq.presentation.controllers.config_io")`
     — **同一パッケージ内の兄弟参照を誤検出しない**こと（presentation に 16 件実在する形）

### 5. docstring の更新

**相対 import も検査対象になったこと**と、**`package` を渡さない場合は末尾パターン一致に縮退する**ことを
明記する。既存の限界（動的 import / 実行時に組み立てた名前 / 代入による再束縛）の記述は**残す**。

### 設計メモ / 制約

- **誤検出を出さないこと**が最優先。とくに **`from .<sibling> import X`（同一パッケージ内）を
  違反にしない**（presentation の 16 件が該当し、落ちると即座に分かる）。
- **`level` の解釈**: `from . import X` は level=1（基準 = `package` 自身）、`from .. import X` は level=2
  （基準 = `package` の親）。**`level - 1` 個を落とす**のが正しい
  （オフバイワンを作らないこと。テストで両方の深さを確認する）。
- **テストメソッドは 3 本のまま**（既存メソッドへケースを足す）。→ **`tests` の件数は 417 のまま**が期待値。
- **既存アサーションを緩めない**（`INTERNAL_MODULE_NAMES` の実ファイル一致 / 移した 43 名の `hasattr` 偽 /
  内部仕様 6 名の残存 / 既存の禁止・許可ケース）。
- **検査対象範囲を広げない**（走査は `keyseq/presentation/` 配下のみ・対象は
  `keyseq.application.config_service` 関連の参照のみ）。

## 含まない

- **プロダクションコード（`keyseq/` 配下）の変更**。
- **動的 import・実行時に組み立てた名前・代入による再束縛の検出**（限界として docstring に書くだけ）。
- 検査対象ディレクトリの拡大（`tests/` 自身の検査など）。
- 正本 `architecture.md` §3.2 の条項変更（**条項は不変**）。
- `decisions_archive/13` の作成・`current.md` の完了記載・idea_15 の `INDEX_done.md` 移動・
  `/refactor_check`（**task_02**）。

## 確認

1. **`verifier` の実測**（`.venv` の python。worktree ルート）:
   - `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が **417 pass（skip 7）**
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が **288 pass（skip 0）**
   - `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass
2. **拡張が実効的であることの実測**（メインが行う）: 追加した禁止 3 例が**非空**、許可 3 例が**空**を返すこと。
3. **素通しでないことの実測**（メインが行う）: `keyseq/presentation/` の任意の 1 ファイルへ
   **相対 import の禁止参照**（例: `from ..application.config_service import orphan_scan` 相当の深さ）を
   一時的に仕込むと `test_presentation_uses_only_config_service_public_surface` が **FAIL** し、
   復旧すると pass に戻ること。**`keyseq/` に差分を残さない**。
4. **誤検出がないことの実測**（メインが行う）: 既存の `from .io_dialogs import IoDialogs` 形（16 件）で
   落ちていないこと（= 1 の `tests` が pass していれば充足）。
5. `git diff -- keyseq main.py tests_ui` が**空**（変更は `tests/test_config_service_contracts.py` のみ）。

## 完了条件

- 上記「確認」1〜5 をすべて満たす。
- **`reviewer` による別視点レビューを通過**（`.claude/rules/review.md` の 5 観点 +
  phase.md「レビュー方針」の誤検出・検出漏れ・限界記述の観点）。
- **実機目視は不要**（テストのみの変更）。
- 残課題・想定外の差分があれば完了報告に明記する。
