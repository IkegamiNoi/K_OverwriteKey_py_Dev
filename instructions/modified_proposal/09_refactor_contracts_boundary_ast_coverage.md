# 提案書 09: phase 13（公開面の逆戻り防止テストの検査範囲の拡張）後のリファクタ

> `/refactor_check`（`.claude/commands/refactor_check.md`）の判定 = **推奨**。
> **ユーザー承認前に実装しない**。判定の記録は
> [decisions_archive/13](../../.claude_data/state/decisions_archive/13_contracts_boundary_ast_coverage.md)。
> 状態: **承認済・実施完了**（2026-09-08・独立ミニ計画「**計画10**」として実施。
> 項目 0 = `d9be5d8` / 項目 1・2 = `5eb986b`。**挙動不変**）。
> ※ 提案書の採番 09 と「**計画09**」（`/spec_split` による正本の INDEX 分割）は**別物**。本書は提案書 09。

## 判定の要約

PHASE_BASE = `90db223`（phase 13 起票コミット）。対象 = **変更 1 ファイル**
（task_01 / 01b で **+102 / -10**、task_01c で **+48 / -19**。**`keyseq/` の差分は 0**＝本フェーズはテストのみ）。
メトリクスは `verifier` 実測 + task_01c 後にメインが再測。

- **M2 該当（→ 項目 1）**: `tests/test_config_service_contracts.py:29` の `collect_forbidden_refs` が
  **PHASE_BASE 時点 27 行 → 現在 100 行**（task_01c 適用前は 92 行）。
  `refactor_check` の M2 のうち **「40 行以上変更した既存関数のうち 80 行超」に該当**する
  （base 時点で存在した関数なので「追加した関数」側には当たらない。**この一本で該当**）。
  **「既存の巨大関数は対象外」の除外にも当たらない**（base 時点は 27 行で巨大ではなかった）。
  `.claude/rules/implementation.md` の予防目安（関数 30 行）も大きく超えている。
  **task_01b の `reviewer`・phase 完了レビューの `deep-reviewer` も同じ点を挙げている**。
- **M6 は非該当だが関連として項目 2**: 新規コードに `"config_service"` の直値が 3 箇所
  （`:82,85,87`）。既存定数 `CONFIG_SERVICE_PACKAGE`（`:11`）の**末尾セグメントと同じ文字列**だが、
  **定数の値そのものとは同値ではない**ため M6 の「既存定数と同じ値の直値」には当たらない。
  ただし片方だけ変えるとずれるため、**項目 1 の分割と同時なら安く直せる**。
- **M1 / M3 / M4 / M5 非該当**: M1 = ファイルは 227 行（閾値 600 行に遠い）/
  M3 = **独立項目にしない**（`prefix` 判定 + 先頭セグメント ≠ `contracts` の同型は `:72` / `:93-94` /
  `:98-99` / `:119-121` の **4 箇所**あり「3 個目以降」と読む余地はあるが、**項目 1 の分割で吸収される**。
  M2 で既に「推奨」判定のため結論は変わらない）/
  M4 = 列挙型ボイラープレートの増加なし（`INTERNAL_MODULE_NAMES` は不変）/
  M5 = 申し送りコメントの新規追加なし（grep 一致 0 件）。

## 項目 0（先行・**必須**）: 期待メッセージを固定する安全網を先に足す

**対象**: `tests/test_config_service_contracts.py:174-227`（自己検証メソッド）

**何が問題か**: 現在の自己検証は **禁止 13 例に対して `assertTrue`（非空）**、
**許可 13 例に対して `assertEqual([], ...)`** しか見ていない。
**戻り値の件数・メッセージ文字列・畳み込みの先勝ち順序を固定していない**ため、
項目 1 の分割で次が変わってもテストが通ってしまい、**「挙動保存」を主張できない**:

- 経路ラベル（`R1` / `R2` / `R3` / `R4` / `attribute`）の入れ替わり
- 同一行に複数経路が当たる場合の**先勝ちの変化**
  （例: `from keyseq.application import config_service` + `config_service.orphan_scan` は
  現在**素の名前検査が先に走り** `attribute config_service.orphan_scan` を返すが、
  エイリアス経路が先になると `attribute keyseq.application.config_service.orphan_scan` に変わる。
  **キーが同じ `(行番号, モジュール名)` なので `setdefault` の先勝ちだけが結果を決めている**）
- 同一行から複数違反が出る場合の件数

**どう変えるか**: 禁止 13 例を **`assertEqual(collect_forbidden_refs(...), [期待メッセージ...])`** へ変更する
（許可側は現状のままで十分）。**これは分割の前に単独で入れる**（分割と同時にやらない。
先に固定してこそ「分割前後で同一」を主張できる）。

**完了条件**: 変更前のコードで **`tests` 417 pass** のまま通ること
（＝現在の実際の出力を写し取る。**期待値を後から都合よく書き換えない**）。

**指摘元**: `deep-reviewer` M-5 / `codex-adversarial-reviewer` ③。

## 項目 1（M2）: `collect_forbidden_refs` を経路ごとの純関数へ分割

**対象**: `tests/test_config_service_contracts.py:29-128`

**何が問題か**: 1 関数に**エイリアス表の構築 / import 3 経路（R1・R2・R3）/ 相対 import（R4 + 縮退）/
属性チェーンの解決と畳み込み**が同居し 100 行。経路を 1 つ足すたびに同じ関数が伸びる構造で、
**どの経路の判定を直しているのかがレビューで追いにくい**（実際 phase 13 では 3 回続けて同じ関数を触った）。

**どう変えるか**（挙動保存・戻り値の形式も不変）:

```python
# 変更後のスケッチ（名前は仮）
_INTERNAL_SEGMENT = CONFIG_SERVICE_PACKAGE.rsplit(".", 1)[-1]   # 項目 2 と同時

def _resolve_relative_module(package, node): ...                # 既存（:19-26）。そのまま
def _build_alias_map(tree, package) -> dict[str, set[str]]: ... # :45-62
def _check_import_nodes(node, package) -> list[str]: ...        # R1 / R2 / R3 / R4 + 縮退（:66-100）
def _check_attribute(node, aliases) -> list[tuple[key, str]]:   # 属性 3 形（:101-126）

def collect_forbidden_refs(source: str, package: str = "") -> list[str]:
    """（docstring は現行のまま。限界の記述も変えない）"""
    tree = ast.parse(source)
    aliases = _build_alias_map(tree, package)
    ...  # 各 _check_* を呼んで結果を連結し、属性は (行番号, モジュール名) で畳む
```

- **公開名（`collect_forbidden_refs`）とシグネチャ・戻り値の文字列形式は変えない**
  （`R1` / `R2` / `R3` / `R4` / `attribute` のラベルと `f"{lineno}: ..."` 形式を保つ）。
- **畳み込み（同一 行番号 × 内部モジュール名）の責務は呼び出し側に残す**。
  **素の名前検査をエイリアスチェーン検査より先に評価する順序も保つ**（項目 0 が固定する）。
- **R1 / R2 は現在すべての `ImportFrom`（相対含む）に適用されている**。分割で `level` による分岐を
  入れると挙動が変わるため、**「R1 / R2 は全 ImportFrom に適用」を維持する**
  （実在しない書き方でしか差は出ないが、挙動保存の観点で明記する。`deep-reviewer` L-8）。
- 補助関数は**モジュール内 private**（`_` 始まり）。**新規ファイルは作らない**
  （テストヘルパは対象テストの近くに置く＝`.claude/rules/file_organization_rules.md` の「局所化」）。

**完了条件**:

```bash
../../../.venv/Scripts/python.exe -m unittest discover -s tests
```

- **`tests` 417 pass（skip 7）**・テストメソッドは **3 本のまま**。
- **項目 0 で固定した期待メッセージが 1 件も変わらない**。
- `keyseq/presentation/` へ各経路の禁止参照を仕込むと **FAIL**、復旧で pass（**分割前と同じ**）。
- `git diff -- keyseq main.py tests_ui` が空。

**リスクと戻し方**: 判定順序が変わると畳み込みのメッセージが入れ替わる（項目 0 が検出する）。
差分は 1 ファイルなので `git checkout -- <file>` で戻せる。

**依存**: **項目 0 を先に完了させること**。項目 2 とは同時実施が望ましい。

## 項目 2（M6 関連・小）: `"config_service"` 直値を定数から導出する

**対象**: `tests/test_config_service_contracts.py:82,85,87`（R4-fallback の縮退判定）

**何が問題か**: `CONFIG_SERVICE_PACKAGE`（`:11`）の**末尾セグメントと同じ文字列**を直値で 3 回書いている。
パッケージ名が変われば片方だけずれ、**縮退判定だけ静かに効かなくなる**。

**どう変えるか**: `_INTERNAL_SEGMENT = CONFIG_SERVICE_PACKAGE.rsplit(".", 1)[-1]` を 1 つ置き、3 箇所を置換する。

**`:104` の `node.value.id == "config_service"` は対象外**（`deep-reviewer` L-5）。
これは**パッケージ末尾セグメントではなく「ソース中の識別子名」**であり意味が違う。
加えて**本フェーズで変更していない行**のため、`refactor_check` の「フェーズで触っていないコードを
提案書の項目に含めない」に触れる。**意図的に残す**。

**完了条件**: 上と同じテストが pass し、**fallback の禁止例が引き続き検出される**こと。

**リスクと戻し方**: 極小。1 ファイルの差分。

## 提案書に含めない項目

- **M3 の同型判定**（`prefix` 判定 + 先頭セグメント ≠ `contracts` が `:72` / `:93-94` / `:98-99` /
  `:119-121` の 4 箇所）は**独立項目にしない**。項目 1 の分割で経路ごとの関数へ寄るため自然に吸収される。
  **共通化自体を目的にしない**（無理にまとめると R1 / R2 / R4 / 属性の判定条件の違いが埋もれる）。
- **検査に残る限界 4 つ**（動的 import / 実行時に組み立てた名前 / 代入による再束縛 /
  縮退時の未解決）の解消は**リファクタではなく機能追加**のため対象外。
  必要になったら**新規 idea として起票**する（`decisions_archive/13`）。
- **素の名前検査の潜在的誤検出**（`ConfigService` に内部モジュールと同名の公開メンバが増えると落ちる）も
  リファクタの範囲外。**残存リスクとして `decisions_archive/13` に記録済**。

## 実施タイミング → **(b) 次フェーズ前の独立ミニ計画「計画10」**（ユーザー確定 2026-09-08）

phase 13 は完了処理まで終えて閉じているため、追加タスクで完了宣言を巻き戻すより独立計画が清い
（計画08 と同じ判断）。**フェーズ番号は消費していない**。

**実施結果**（詳細は `.claude_data/state/decisions.md` の「計画10」節）:

- 項目 0（`d9be5d8`）: 禁止 13 例の期待メッセージを `assertEqual` で固定。
  **書式を変えると FAIL することを実測**（安全網が素通しでない）。
- 項目 1・2（`5eb986b`）: `collect_forbidden_refs` を **100 行 → 26 行**へ分割し、
  `"config_service"` 直値 3 箇所を `_INTERNAL_SEGMENT` へ。
  **分割前後の出力を 95 ケースで機械照合し不一致 0**。`tests` 417 / `tests_ui` 288 / smoke pass。
  `reviewer` = 完了可。
