# idea_14_config_service_public_surface.md

## 概要

**presentation が `application/config_service/` の内部モジュールから定数・結果型を直接 import している**。
公開面（`ConfigService` の委譲メソッド）を通す規定に対する例外が積み上がっており、
**定数と結果型を置く「公開面モジュール」を 1 つ決めて集約する**のが本ネタ。

## 起票経緯（2026-09-08）

出所: **phase 11 task_07 の二次レビュー指摘 B-2**（`deep-reviewer`）。
暫定仕様 10 §3-11 の「presentation から `config_service` の内部モジュールを直参照しない」に対し、
実装が判定名・理由コードの定数と結果のデータクラスを直 import していた。

**ユーザー判断（2026-09-08）= 条項側に例外を明記し、実装は変えない**。
評価は「今回の修正コスト」ではなく**今後の実装コスト**で行い、次の理由で本 idea へ分離した。

- **`__init__.py` への再輸出（案 B）は今後のコストが最も高い**。定数を足すたびに
  **定義 + 再輸出の 2 箇所**を触ることになり、**828 行で分割保留中の `__init__.py`** をさらに太らせる。
- **公開面モジュールを新設（案 C）が長期的には最良**だが、**payoff は phase 10 分も変換して初めて出る**
  （2 形式が併存すると次に触る人がどちらに倣うか迷う）。フェーズ末の文書タスクへ混ぜる性質ではない。
- **現状（案 A）の実害は「実装モジュールを改名・分割したとき import 文を直す」だけ**で、
  **`ImportError` で即座に露見する**（黙って壊れない）。

## 現状（2026-09-08 実測）

`presentation` → `config_service` 内部モジュールの直 import は **import 文 7 / 定数 33 / 型 7**。

| presentation 側 | 参照先モジュール | 定数 / 型 |
|---|---|---|
| `controllers/config_io/orphan_sweep_io.py` | `orphan_scan` | 1 / 0 |
| `controllers/config_io/reference_cleanup_io.py` | `parent_refs_cleanup` | 2 / 0 |
| `orphan_sweep_text.py` | `orphan_scan` / `quarantine` / `reference_scan` | 15 / 2 |
| `quarantine_manage_text.py` | `quarantine_manage` | 10 / 3 |
| `reference_cleanup_text.py` | `parent_refs_cleanup` | 5 / 2 |

**phase 10 由来（`reference_cleanup_*`）が定数 7 / 型 2**、**phase 11 由来が残り**。

## 提案

- `config_service` に**公開面モジュールを 1 つ新設**し（例: 判定名・理由コード・結果データクラスの定義場所）、
  **定義そのものをそこへ移す**（実装モジュール側がそこから import する）。
  再輸出の二重管理を作らないことが要点。
- presentation は**その 1 パスと `ConfigService` だけ**を知る形にする。
- **phase 10 分（`reference_cleanup_text.py` / `reference_cleanup_io.py`）も同時に変換する**
  （2 形式の併存を残さない。これをやらないなら着手しない）。

## 想定スコープ

- **含む**: 公開面モジュールの新設と定数・結果型の移動、application 内の import 付け替え、
  presentation 5 ファイルの import 付け替え、`tests` / `tests_ui` の追随、
  正本 `spec_detail/architecture.md` §3.2 の例外記述の削除。
- **含まない**: 関数・ロジックの移動、`ConfigService.__init__.py` の分割（別途追跡中）、
  委譲メソッドの API 変更。
- **影響レイヤ**: application（定義場所）+ presentation（import のみ）。**挙動不変**。
- **仕様変更**: 依存方向の条項（`architecture.md` §3.2）から例外が消える方向のため、
  **着手時に正本の更新を伴う**。
- **優先度**: 低〜中（挙動不変・実害は改名時の機械修正のみ）。
  **着手トリガー**: ①`config_service` の実装モジュールを再度分割・改名するとき
  ②presentation からの直 import がさらに増えるとき ③`__init__.py` の分割に着手するとき。

## 関連

- 分離元: [phase 11](../phase/11_orphan_child_file_sweep/phase.md) task_07 の
  [integration_result.md](../phase/11_orphan_child_file_sweep/integration_result.md) §3-3 B-2。
- 正本: `spec_detail/architecture.md` **§3.2**（依存ルールと当面の例外）/ `codebase_map.md`。
- 判断の経緯: `.claude_data/state/decisions_archive/11_orphan_child_file_sweep.md`。
