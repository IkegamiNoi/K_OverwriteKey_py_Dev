# task_01_action_type_button_coercion

## 目的

アクション要素の `type` / `button` が非文字列だと読み手の `.strip()` で `AttributeError` になる問題を、
**読込時の正規化 `normalize_actions` で §5.1「型不正の共通規則」に従わせて**解消する（idea_27 + `type`）。
直接改訂モードのため、**正本 `data_schema.md` §5.11 の改訂を実装より先に行う**（phase.md「確定」）。

**domain 限定（`keyseq/domain/config.py`）・application / presentation 不変・JSON スキーマ不変**。

## 対象範囲（正本 §5.11 + domain `normalize_actions` + 単体テスト）

### 1. 正本 `instructions/common/spec_detail/data_schema.md` §5.11（**先行・メインセッションが実施**）

- §5.11.1 の `label` の段落の後へ追記:
  - `type` / `button` も**非文字列なら空扱い**（§5.1）。**キーが無いときは補わない**（空文字のキーを足さない）。
    文字列は trim する（小文字化はしない。判定側が大文字小文字を区別しない）。
  - **`type` が空 / 上表以外の値のときは `value` を文字列として入力する**（`text` と同じ動き。
    一覧表示は `value` を表示する）。現行挙動の明文化（正本には idea へのリンクを書かない。変更検討は
    [idea_35](../../../backlog/idea_35_unknown_action_type_handling.md)）。
- §5.11.2 の `button` 行を置き換え:
  「`left` / `right` / `middle`（大文字小文字は区別しない）。空 / これ以外の値は `left` として扱う
  （非文字列は §5.1 により空扱い）」 = **「（非文字列は未定義）」を削除**。

### 2. `keyseq/domain/config.py` の `normalize_actions`（**実装委任**）

- 既存の `a["label"] = coerce_label(a.get("label"))` に加え、
  **`"type"` / `"button"` がキーとして存在する場合のみ** `a[key] = coerce_label(a[key])` を適用する。
- キーが無い要素にはキーを追加しない（`label` は既存どおり常に付与。これは変えない）。

### 3. `tests/test_domain_config.py` の `NormalizeActionsTest`（**実装委任**）

- 下記「確認」の単体テスト項目を追加する。既存テストは変更しない。

### 設計メモ / 制約

- **`coerce_key_name` を使わない**（小文字化で保存値が変わる。読み手が `.lower()` 済み）。`coerce_label` を使う。
- **`label` と非対称なのは意図どおり**: `label` は既存挙動で常に付与、`type` / `button` は存在時のみ
  （`button` を持たない hotkey / text アクションに `"button": ""` が増えると保存出力が変わる）。
- 読み手（`action_executor.py:51` / `:119`・`domain/config.py:323` の `format_action_list_item`・
  presentation の 3 箇所）は**無修正**。全読込経路が `normalize_actions` を通るため（§5.11 冒頭）。
- 依存方向: domain 内で完結（新規 import なし）。

## 読むファイル

1. `keyseq/domain/config.py:84-85`（`coerce_label`）/ `:144-155`（`normalize_actions`・編集対象）
2. `tests/test_domain_config.py:39-88`（`NormalizeActionsTest`・追加先と書き方の手本）
3. 正本 `instructions/common/spec_detail/data_schema.md` §5.1「型不正の共通規則」（`:21-44`）/ §5.11（`:373-400`）
4. `keyseq/application/action_executor.py:50-64` / `:112-128`（読み手の確認のみ・編集しない）

## 含まない

- runtime 内部キー（パス系 3 種）の正規化・§5.7 注記削除・内部キーの書き手の棚卸し（**task_02**）
- フェーズの締め（decisions_archive/30・current.md・INDEX → INDEX_done・`/refactor_check`。**task_02**）
- `action_executor.py` / presentation の読み手の書き換え（入口で守るため不要）
- 空 / 未知の `type` の挙動変更・ダイアログの空 `type` = hotkey との食い違い（**idea_35**）
- `x` / `y` / `clicks` / `drag` / `to_x` / `to_y` / `drag_speed` / `value` の型規則
- `codebase_map.md` の更新（関数の責務は変わらない）

## 確認

- 追加する単体テスト（`NormalizeActionsTest`）:
  1. `type` が非文字列（`None` / `0` / `False` / `[]` / `{}` / `123` / `["a"]` / `{"a": 1}`）→ `""`
  2. `button` が非文字列（同上）→ `""`
  3. `type` / `button` の文字列は trim され、**大文字小文字は保持**（`"  Mouse_Click "` → `"Mouse_Click"`）
  4. `type` / `button` を**持たない**要素にキーが追加されない（`{"type": "text", "value": "a"}` に `button` が生えない /
     `{"value": "a"}` に `type` が生えない）
  5. 非文字列の `type` を持つ要素が**除去されない**（要素は残る。§5.11.1）
- 実測（`verifier`・`.venv` python）:
  - `compileall -q keyseq main.py tests tests_ui` clean
  - `-m unittest discover -s tests` 全 pass（件数は追加分だけ増えること）
  - `-m unittest discover -s tests_ui` 全 pass
  - `-m tests.smoke_app` pass
- `git diff` で production の変更が `keyseq/domain/config.py` の `normalize_actions` 内のみであること

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 正本 §5.11 の改訂が**実装より前のコミット位置**にあるか、同一コミットで先に記述されていること。
- 実機目視は**不要**（UI 経路からは非文字列の `type` / `button` を作れない。手編集 JSON のみの経路で、単体テストで固定する）。
