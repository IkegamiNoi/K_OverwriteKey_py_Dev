# task_02_boundary_tests

## 目的

**公開面（`contracts`）を迂回して内部モジュールへ戻る変更を、テストで落ちるようにする。**
根拠は phase.md タスク 2 + 暫定仕様 11 **§3-4**。

- **プロダクションコードは変更しない**（テストの追加と、task_01 の残りの整形のみ）。
- task_01 で定義は移し終えているため、**本タスクは「逆戻りを検出できる状態」を作るだけ**。

## 対象範囲

### 1. 新規テストファイル `tests/test_config_service_contracts.py`

**テストメソッドは 3 本**（下記 1-1 / 1-2 / 1-3）。既存ファイルへは足さない
（公開面の境界という独立した関心事のため。発見性を優先する）。

#### 1-1. 実装モジュールが `contracts` を見ていることの固定

`parent_refs_cleanup` / `reference_scan` / `orphan_scan` / `quarantine` / `quarantine_manage` の 5 本について:

- `assertIs(module.contracts, contracts)`（**同一オブジェクト**を見ていること）
- **task_01 で移した名前（定数 34 / 型 9）の `hasattr` が偽**であること
  （名前の一覧は `contracts` 側から機械的に取る。**ハードコードした 43 個の羅列にしない**）
- **移していない内部仕様の名前は残っていること**を併せて確認する
  （`quarantine`: `QUARANTINE_DIR_NAME` / `MANIFEST_FILE_NAME` / `UNIT_ID_PATTERN` /
  `ENTRY_PLANNED` / `ENTRY_MOVED` / `ENTRY_FAILED`）。
  **「全部移してしまう」方向の退行も落ちるようにする**。

見本: `tests/test_orphan_scan.py` の `test_real_boundary_uses_shared_module_without_legacy_alias` /
`test_candidate_dirs_use_shared_module_without_legacy_alias`（`assertIs` + `hasattr` 偽の形）。

#### 1-2. presentation の参照先の固定（AST 走査）

`keyseq/presentation/` 配下の**全 `.py`** を `ast` で走査し、**禁止パターンが 0 件**であることを確認する。
検査は**モジュールレベルの純関数**（例: `collect_forbidden_refs(source: str) -> list[str]`）に切り出し、
1-3 から再利用する。

検出する 4 経路（暫定仕様 §3-4）:

- **R1**: `from keyseq.application.config_service import X` — **X が `ConfigService` / `contracts` 以外**なら違反
  （`orphan_scan` などのサブモジュール名を弾く。**この形は接頭辞一致では捕まらない**）
- **R2**: `from keyseq.application.config_service.<sub> import ...` — **`<sub>` が `contracts` 以外**なら違反
- **R3**: `import keyseq.application.config_service.<sub>` — 同上（**`ast.Import` も見る**）
- **属性アクセス**: `ast.Attribute` で **`config_service.<内部モジュール名>`** の形
  （`__init__.py` が内部モジュールを属性公開しているため、この経路が残る）

**検査対象は `keyseq.application.config_service` 関連のみ**。
`keyseq.application.save_plan` / `keymap_service` / `app_state` などは**検査しない**
（presentation は現に import しており、フェーズのスコープ外）。

**docstring に検査の限界を明記する（MUST）**: **動的 import（`importlib` / `__import__`）や、
変数へ束縛し直した後の間接参照は検出できない**。本テストは**静的に書かれた参照の逆戻りを防ぐ**もの。

#### 1-3. 検査関数の自己検証

**禁止パターンを文字列のソースとして与え、1-2 の検査関数が確かに検出する**ことを確認する
（R1 / R2 / R3 / 属性アクセスの**各 1 例**）。**許可パターン**
（`from keyseq.application.config_service import ConfigService, contracts` /
`from keyseq.application.save_plan import ACTION_SAVE`）で**誤検出しない**ことも確認する。

**これが無いと、検査関数が常に空リストを返す実装でも 1-2 が通ってしまう**。

### 2. task_01 のレビュー指摘の解消（非ブロッキング分）

`tests/test_orphan_sweep_text.py` 冒頭の `contracts` からの import が、
元の 3 モジュール由来のまま**3 ブロックに分かれている**。**1 ブロックへ統合する**（import 文のみの整形）。

## 対象外（触らない）

- **プロダクションコード全般**（`keyseq/` 配下）。本タスクはテストのみ。
- 既存テストのアサーション変更・削除・skip 化。
- 正本 `instructions/` の更新（**task_03**）。
- 動的 import の検出（**検査の限界として docstring に明記するだけ**）。
- `keyseq/application/save_plan.py` 由来の import の規制（スコープ外）。

## 確認

1. 新規テスト 3 本が**現状のコードで pass** する。
2. **1-3 の自己検証が実際に効いている**こと（検査関数が空を返す実装にすると 1-3 が落ちる形になっている）。
3. `verifier` の実測で **`tests` が 414 → 417**（**+3**）、**`tests_ui` は 288 のまま**、
   `compileall` clean / smoke pass。**それ以外の件数変動があれば退行を疑う**。
4. `tests/test_orphan_sweep_text.py` の `contracts` import が 1 ブロックになっている。
5. `reviewer` による別視点レビューを通過（`.claude/rules/review.md` の 5 観点）。

## 完了条件

- 上記「確認」1〜5 をすべて満たす。
- **プロダクションコードの差分が 0 行**であること（`git diff -- keyseq/` が空）。
- 残課題・想定外の差分があれば完了報告に明記する。
