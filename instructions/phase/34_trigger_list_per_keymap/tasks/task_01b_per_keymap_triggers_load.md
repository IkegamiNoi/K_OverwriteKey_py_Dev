# task_01b_per_keymap_triggers_load

## 目的

暫定仕様 25 §3（データモデル）と §4.1・§4.3・§4.5（読込と移行）を実装し、**runtime のトリガー一覧をキーマップごとに保持する**。
task_01 で作った口（`keyseq/domain/keymap_triggers.py`）の中身を「アクティブキーマップの `triggers`」へ差し替え、
全参照を追従させる。単一 JSON の Import / Export もキーマップごとの形にする（往復を壊さないため・暫定 §3.2 / §6 Export）。

**JSON スキーマ変更（読込側 + Export）**。domain（正規化・`DEFAULT_CONFIG`・口）/ application（split 読込・単一 JSON・keymap_service）/
presentation（新規作成・Import・例の復元・読込完了の通知）に跨る。

### 暫定（task_02 まで）

保存計画・payload は task_01 の付け替えにより**口 = アクティブキーマップの一覧**を読むため、保存すると
**アクティブキーマップのトリガー一覧だけが従来どおり 1 つの trigger_set として書かれ、keymap_set の `trigger_set_path` がそれを指す**
（旧形式での保存）。再読込では §4.1-2 の移行でアクティブキーマップへ戻る。**アクティブ以外のキーマップのトリガー一覧は保存されない**。
task_02 で解消する。本タスクでこの暫定を直そうとしない。

## 対象範囲

### domain

- `keyseq/domain/keymap_triggers.py`: 口の中身を差し替える。
  - `get_active_triggers(data)` = `active_keymap_id` が指すキーマップ要素の `triggers`（list なら**同一オブジェクト**）。
    アクティブが無い / `triggers` が list でない → 新しい `[]`（格納しない）。
  - `ensure_active_triggers(data)` = アクティブキーマップの `triggers` を setdefault 相当で確保して返す。
    キーマップが 0 個なら §4.1-4 の自動作成（下記 `keymap_service` の関数と同じ規則。domain 側に純関数として置き、keymap_service が使う）を行ってから確保する。
  - `set_active_triggers(data, triggers)` = アクティブキーマップの `triggers` へ代入（無ければ自動作成してから）。
  - docstring を「アクティブキーマップの保持を読む口」へ更新。
- `keyseq/domain/config.py`:
  - `DEFAULT_CONFIG` を新形式へ: トップレベル `triggers` は `[]`、`keymaps` = 1 要素（`id`=`keymap_1` / `label`=`""` / `mappings`={} /
    `triggers`=現行の例のトリガー 2 件）/ `active_keymap_id`=`keymap_1`（暫定 §4.3「例の復元は移行として扱わない」）。
  - `ensure_config_compatibility`:
    - `keymaps[]` 要素の `triggers` を保持し、現行のトップレベル `triggers` と**同じ正規化**を要素ごとに適用する
      （非 list は `[]`・その場合も「キーあり」のまま = 暫定 §3.2）。内部キー（sequence 系・下記の trigger_set 系）も保持する。
    - **共有の保持**: 入力で複数のキーマップが**同一オブジェクト**の `triggers` を持つなら、出力でも同一オブジェクトにする（`id()` で memo）。
    - 最古形式（`trigger_key`）の変換はこれまでどおり先に行う（168-182）。
    - **移行（§4.1-2〜4）は `ensure_config_compatibility` の中で行わない**（呼び出しが多数あり runtime で毎回走るため）。
      下記 `migrate_single_json_triggers` を単一 JSON の読込経路からだけ呼ぶ。トップレベル `triggers` は正規化して残す（読むのは移行関数だけ）。
  - 新規の純関数（同ファイル or `keymap_triggers.py`。置き場は実装判断でよいが domain 内）:
    - `ensure_at_least_one_keymap(data) -> dict | None` — キーマップ 0 個なら §4.1-4 の規則で 1 つ作り（`id` は既存採番〔`keymap_N`〕/
      `label`=`""` / `mappings`={} / 切替キーなし）アクティブにする。作ったらその要素を返す。
    - `migrate_single_json_triggers(data) -> str` — 単一 JSON の §4.1-2: アクティブキーマップが `triggers` キーを**持たない**とき
      トップレベル `triggers` をそこへ移す。戻り値は状態（`"none"` = トップレベルが空 / `"migrated"` / `"unused"` = アクティブが既に持つ）。
      実行後トップレベル `triggers` は `[]`。先に `ensure_at_least_one_keymap` を呼ぶ。

### application

- `keyseq/application/keymap_service.py`: `ensure_active_keymap` の自動作成（id=`default` / label=`Default`・260-269）を
  `ensure_at_least_one_keymap` の規則へ統一する。
- `keyseq/application/config_service/split_loading.py`（split 読込・暫定 §4.1）:
  - 土台 `new_default_data()` の `keymaps` / `triggers` / `active_keymap_id` を**引き継がない**（例データが混ざらないこと・v0.1 M1）。
  - keymap ファイルの `trigger_set_path`（§5.1 の型規則・非文字列は空）を読み、非空なら `load_trigger_set` で読んでその要素の `triggers` にする。
    **同じ解決済みパスは 1 回だけ読み、同一オブジェクトを共有**する。読めない場合は現行の `load_trigger_set` の失敗時の扱いをそのキーマップに適用
    （旧形式では補わない）。
  - キーマップ要素に trigger_set の内部キー（`_trigger_set_source_path` / `_trigger_set_parent_refs`）を持たせる（共有なら同値）。
  - `ensure_at_least_one_keymap` → keymap_set の `trigger_set_path`（旧形式）を §4.1-2 の規則で扱い、状態を runtime の内部キー
    **`_legacy_trigger_set`** = `{"state": "none"|"migrated"|"unused"|"same", "path": <旧値>, "keymap_id": <アクティブ id>}` に記録する
    （暫定 §4.4 の表の 4 状態。`same` = アクティブが旧値と同じファイルを参照済み。定数は `ConfigService.INTERNAL_*` に並べる）。
    `migrated` のときは旧 trigger_set を読んでアクティブキーマップへ付ける。
  - **暫定（task_02 まで）**: 保存側が読むトップレベルの `_trigger_set_source_path` / `_trigger_set_parent_refs` は、
    **アクティブキーマップの一覧の値**を入れる（旧形式から移行したならその値）。runtime のトップレベル `triggers` は `[]`。
- `keyseq/application/config_service/__init__.py`:
  - `new_empty_data`（55）: キーマップ 1 つ（トリガー空）の状態を返す（暫定 §4.3 新規作成）。
  - 単一 JSON の読込経路（`load` 等 Import が使う経路）で `migrate_single_json_triggers` を呼ぶ。
  - `save_trigger_set_file`（266-288）: `data.get("triggers")` を口（`get_active_triggers`）経由へ付け替える（task_01 の列挙漏れ）。
  - Export の `_sanitize_runtime_for_storage`（471-502）: 各 `keymaps[]` 要素の `triggers` から sequence 系内部キーを除き、
    要素から trigger_set 系内部キーを除く。トップレベル `triggers` は `[]`。`_legacy_trigger_set` も除く。
    共有実体は各キーマップへ同内容を書く（暫定 §6）。
- `keyseq/application/config_service/save_plan_execution.py:53-57`: task_01 reviewer の参考指摘（常に真の `isinstance`）を簡素化
  （`get_active_triggers(data) if isinstance(data, dict) else []`）。挙動は変えない。

### presentation

- `controllers/config_io/keymap_set_io.py`:
  - 新規作成（57 付近）: キーマップ 1 つ・トリガー空になること（`new_empty_data` の変更で満たされるなら追加変更は不要）。
  - Import: 単一 JSON 経路の移行が効くこと（上記 application 側で満たす）。
  - 例の復元（628 付近）: `DEFAULT_CONFIG` 新形式でそのまま動くこと。
  - **暫定 §4.5 の通知**: 構成セットの読込完了時、`_legacy_trigger_set.state == "unused"` なら情報ダイアログで
    「旧形式のトリガー一覧 <パス> は使われていません（トリガー一覧の読込から個別に読み込めます）」を出す（読込完了メッセージの後・上書きされない位置）。
    `same` / `none` / `migrated` では出さない。起動時の自動読込でも出す（起動完了後に 1 回）。

### テスト（追加・更新）

- 既存テストでトップレベル `runtime["triggers"]` を期待しているものは、**口（`get_active_triggers`）経由の期待へ更新**する
  （スキーマ変更に伴う期待値更新。アサーションを緩めない）。
- 新規（`tests/` 配下。ファイル名は実装判断）:
  1. `ensure_config_compatibility`: `keymaps[].triggers` の正規化・非 list → `[]`・内部キー保持・**共有の同一性保持**。
  2. `ensure_at_least_one_keymap` / `migrate_single_json_triggers` の 3 状態。
  3. split 読込: 旧形式 keymap_set（keymap ファイルに `trigger_set_path` なし）→ アクティブにだけ付く / アクティブ以外は空 /
     キーマップ 0 個 → 自動作成に付く / keymap 側参照が別ファイル → `unused`・旧は付かない / 同ファイル → `same` /
     2 つの keymap が同じ trigger_set → 同一オブジェクト / 土台の例データが混ざらない。
  4. 単一 JSON: 旧形式 Import → アクティブへ / `keymaps[].triggers` あり → そのまま / Export → `keymaps[].triggers`・トップレベル `[]`・
     内部キーなし / Export → Import の往復でキーマップごとのトリガーが保たれる。
  5. `DEFAULT_CONFIG` / `new_empty_data` がキーマップ 1 つ。
  6. 口: アクティブを切り替えると `get_active_triggers` が別の一覧を返す。

### 設計メモ / 制約

- トリガーの正規化は既存の関数をキーマップ要素ごとに流用し、規則を複製しない。
- presentation の直参照は task_01 で 0 件になっている。新たに `"triggers"` リテラルを presentation に書かない（静的テストが落ちる）。
- 移行は「読込元ファイルの内容」で判定し、runtime の土台を見ない（暫定 §3.3）。

## 読むファイル

- `instructions/history/25_trigger_list_per_keymap.md` §3・§4（§4.2・§4.4 は状態記録のため参照のみ）
- `keyseq/domain/keymap_triggers.py`（全体）/ `keyseq/domain/config.py:20-75, 160-320`
- `keyseq/application/keymap_service.py:70-110, 250-275`
- `keyseq/application/config_service/split_loading.py:270-520`
- `keyseq/application/config_service/__init__.py:30-70, 255-300, 462-505`（単一 JSON の読込経路は `load` から辿る）
- `keyseq/presentation/controllers/config_io/keymap_set_io.py:50-60, 540-640`
- 手本のテスト: `tests/test_domain_config.py:1-60` / `tests/test_config_service.py:1-60`

## 含まない

- 保存計画・payload のキーマップ単位化、keymap ファイルへの `trigger_set_path` 書込み、keymap_set `trigger_set_path` の書き値（§4.4）、
  移行先を未保存にする（§4.2）、`_parent_refs`、既定ファイル名（**task_02**）
- 個別「トリガー一覧 / キーマップ」の保存・読込の規則（**task_03**。`save_trigger_set_file` は付け替えのみ）
- 参照辿り・孤児棚卸し（task_04）/ 入力判定・重複（task_05）
- アクティブ切替時の再描画・シーケンス実行位置のキーマップ単位化・連続実行中の切替禁止（**task_06**）/ 改名（task_07）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（期待値更新分を含む・skip 7 据え置き）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass
- `git grep -n '"triggers"' -- keyseq/presentation` が 0 件
- 期待値を変更した既存テストの一覧と、各変更がスキーマ変更（トップレベル → アクティブキーマップ）によるものであることを報告に含める

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_06 以降でまとめて実施（本タスク単独では UI の切替が未対応のため）。
