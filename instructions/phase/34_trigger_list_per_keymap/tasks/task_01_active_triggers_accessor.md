# task_01_active_triggers_accessor

## 目的

暫定仕様 25 §3.3「UI・入力判定・フック開始検証は**アクティブキーマップのトリガー一覧を service 経由で取得**する
（`app.data["triggers"]` の直参照をやめる）」の**前段**として、runtime のトリガー一覧を読み書きする**唯一の口**を domain に作り、
既存の直参照（約 30 箇所）をその口経由へ付け替える。

**本タスクは挙動不変**（口の実装は現行どおりトップレベル `triggers` を読み書きする）。保持場所をキーマップごとへ移すのは
task_01b で、そのとき口の中身だけを差し替えれば全参照が追従する状態にするのが目的。
**JSON スキーマ不変・保存 / 読込の結果不変・UI 不変**。

## 対象範囲（domain 新規 1 ファイル + 参照の付け替えのみ・挙動不変）

### 新規 `keyseq/domain/keymap_triggers.py`

runtime データ（`dict[str, Any]`）に対する純関数のみ（UI・I/O 依存なし）:

- `get_active_triggers(data) -> list[dict[str, Any]]` — 現行は `data.get("triggers")` が list ならそれ（**同一オブジェクト**を返す。
  呼び出し側が in-place で append / 削除している箇所があるため、コピーを返さない）。list でなければ `[]`（新しい list）。
- `ensure_active_triggers(data) -> list[dict[str, Any]]` — `setdefault` 相当（list でなければ `[]` を格納してそれを返す）。
  現行の `data.setdefault("triggers", [])` の置き換え先。
- `set_active_triggers(data, triggers: list[dict[str, Any]]) -> None` — 現行は `data["triggers"] = triggers`。
- モジュール docstring に「task_01b でキーマップごとの保持へ差し替える口。トップレベル `triggers` を直接触らないこと」を書く。

### `keyseq/application/trigger_service.py`

- `TriggerService.get_triggers` を `get_active_triggers` への委譲にする（名前・シグネチャは据え置き）。

### 付け替え（読み取り → `get_active_triggers` / setdefault → `ensure_active_triggers` / 代入 → `set_active_triggers`）

- presentation:
  - `controllers/trigger_panel_controller.py:56,83,95,117,259,370,443`
  - `keyboard_window.py:95`
  - `controllers/hook_controller.py:124,174,210`
  - `controllers/dirty_state.py:86,107`
  - `controllers/config_io/child_save_plan.py:84` / `child_save_rows.py:163`
  - `controllers/config_io/keymap_set_io.py:57,477,486,502,628`（477 は `kind` による分岐の trigger 側だけを口経由へ）
  - `controllers/config_io/trigger_set_file_io.py:62,146`
- application（runtime を読む箇所のみ）:
  - `config_service/save_plan_execution.py:53-57`（`data` と `normalized` の双方を口で読む）/ `:249` / `:306`
  - `config_service/split_payloads.py:201`
  - `config_service/orphan_scan.py:36` / `config_service/parent_refs_cleanup.py:126`
- 付け替え後、**`keyseq/presentation/` 配下に文字列リテラル `"triggers"` が 0 件**になること。

### テスト（追加）

- `tests/test_keymap_triggers.py`（新規）: 3 関数の単体テスト（list あり → 同一オブジェクト / 無い・非 list → `[]` /
  `ensure` が格納して同一オブジェクトを返す / `set` が格納する）。
- 逆戻り防止の静的テスト（`tests/test_keymap_triggers.py` 内でよい）: `keyseq/presentation/**/*.py` を走査し、
  文字列リテラル `"triggers"` が 0 件であることを確かめる（`ast` で `Constant` の値を見る。コメント・docstring は対象外で可）。

### 設計メモ / 制約

- **付け替えは機械的に行い、周辺ロジックを変えない**（条件分岐・例外処理・変数名はそのまま）。
- 置き場を domain にするのは、application の config_service と presentation の双方から同じ口を使うため
  （config_service は現状 `TriggerService` を import していない。domain は両方から参照可能で依存方向を壊さない）。
- 口の関数は `keyseq/domain/config.py` へ足さず新規モジュールにする（config.py は正規化の責務・既に大きい）。
- **読込・正規化でトリガー一覧を組み立てる箇所は付け替えない**（task_01b）:
  `domain/config.py` の `triggers` 正規化（168-212）/ `split_loading.py:311,460,501` /
  `config_service/__init__.py:55,266-288,475-487` / `reference_scan.py:143`（ファイルの中身を読む）/
  `orphan_scan.py:14`（形状定義）。

## 読むファイル

- `instructions/history/25_trigger_list_per_keymap.md` §3.3（目的の根拠のみ）
- `keyseq/application/trigger_service.py`（全体・編集対象）
- 付け替え対象の各ファイルは**上記の行の前後 10 行程度のみ**（全体を読まない）
- `tests/test_trigger_service.py:1-40`（テストの書き方の手本）

## 含まない

- トリガー一覧の保持場所をキーマップごとへ移す・読込と移行・単一 JSON の Import・`DEFAULT_CONFIG` の新形式化・
  `ensure_active_keymap` の統一・共有実体（**task_01b**）
- 保存計画・payload のキーマップ単位化（task_02）/ 個別保存・読込・Export（task_03）/ 参照辿り（task_04）
- 入力判定の優先順位・重複の扱い（task_05）/ キーマップ管理 UI（task_06）/ 改名（task_07）
- `TriggerService` のメソッド名・シグネチャの変更、`find_trigger_by_key` 等のロジック変更

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass（件数 = 既存 577 + 新規分・skip 7 は据え置き）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass（537・件数不変）
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass
- `git grep -n '"triggers"' -- keyseq/presentation` が 0 件
- 既存テストの期待値を変更していないこと（挙動不変の確認。`git diff --stat -- tests tests_ui` は新規ファイルのみ）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は不要（挙動不変）。task_06 以降でまとめて実施。
