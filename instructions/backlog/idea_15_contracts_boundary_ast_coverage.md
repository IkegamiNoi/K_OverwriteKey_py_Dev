# idea_15_contracts_boundary_ast_coverage.md

## 概要

**公開面の逆戻り防止テスト（`tests/test_config_service_contracts.py`）の AST 検査に、
静的な記述のまま素通りする 3 経路がある**。`ast.Attribute` を**末端からドット結合して
完全修飾名で判定**し、`import` / `from ... import` の **`asname`（エイリアス束縛）を追跡**する形へ
拡張して、**将来の逆戻りを取り逃がさない**ようにする。**プロダクションコードは変更しない**（テストのみ）。

## 起票経緯（2026-09-08）

出所: **phase 12（config_service の公開面の集約）のフェーズ完了レビュー**。
`deep-reviewer` の指摘 **M-3** と `codex-adversarial-reviewer` の medium 指摘が**独立に同じ穴**を挙げた。
ユーザー判断で **phase 12 では残存リスクの記録のみとし、検査強化は本 idea へ分離**
（暫定仕様 11 は凍結済みのため後追い改訂しない）。
判断の記録は
[decisions_archive/12_config_service_public_surface.md](../../.claude_data/state/decisions_archive/12_config_service_public_surface.md)。

## 現状

`tests/test_config_service_contracts.py:19-45` の `collect_forbidden_refs` は
暫定仕様 11 §3-4 の **4 経路**（R1: パッケージ直下からのモジュール名 import / R2: サブモジュール指定 /
R3: `ast.Import` / 属性アクセス `config_service.<内部モジュール>`）を検査する。
**仕様には準拠している**が、次の 3 つは**動的 import でも変数経由でもない静的な記述**にもかかわらず
検出されない（`.venv` の python で `collect_forbidden_refs` を直接呼んで**実測確認済**・いずれも `[]`）:

1. `from keyseq.application import config_service as cs` + `cs.orphan_scan`
   — `:41-44` が `node.value.id == "config_service"` に固定されているため
2. `import keyseq.application.config_service`（**パッケージ名ちょうど**）+
   `keyseq.application.config_service.orphan_scan.X`
   — `:35-39` は接頭辞より深い名前だけを見るのでこの import 自体は許可され、続くドット参照は
   `ast.Attribute` の入れ子（`node.value` が `ast.Name` でない）ため未検出
3. `from keyseq import application` + `application.config_service.orphan_scan`

**現在の `keyseq/presentation/` にこの形の参照は 0 件**（`import keyseq…` /
`from keyseq(.application) import …` の行が無い）。したがって**今の実装は違反しておらず、
将来の逆戻りを取り逃がすだけ**の欠落。

docstring（`:20-23`）の「検査の限界」は動的 import と変数経由のみを挙げており、
**上記の静的経路が抜けている**点も併せて是正対象。

## 提案（方向性・要設計）

- **案 A（推奨）**: `ast.Attribute` の連鎖を末端から結合して**完全修飾名**（例:
  `keyseq.application.config_service.orphan_scan`）へ解決し、`config_service` パッケージの
  内部モジュール名で終わる参照を違反とする。あわせて `Import` / `ImportFrom` の **`asname` を集めて
  別名 → 実体のマップ**を作り、`cs.orphan_scan` 形も解決する。
  **自己検証ケース（`:87-106`）へ上記 3 経路の禁止例と、対応する `contracts` 参照の許可例を追加**する。
- **案 B**: 検査を強化せず、**docstring と正本の限界記述を正確化するだけ**に留める（規約とレビューで担保）。
- どちらでも **`INTERNAL_MODULE_NAMES` とパッケージ実ファイル一覧の一致アサーション**
  （`:71-76`）は維持する。

## 想定スコープ

- **含む**: `tests/test_config_service_contracts.py` の検査関数・自己検証ケース・docstring。
- **含まない**: プロダクションコード（`keyseq/` 配下）/ `contracts.py` の内容 /
  検査対象範囲の拡大（`keyseq.application.save_plan` 等は引き続き対象外）/
  動的 import（`importlib` / `__import__`）の検出（**原理的な限界として据え置き**）。
- **影響レイヤ**: テストのみ。**仕様変更なし**（正本 `architecture.md` §3.2 の条項は不変で、
  その**検査精度を上げるだけ**）。着手時は 1 タスク規模の見込み。
