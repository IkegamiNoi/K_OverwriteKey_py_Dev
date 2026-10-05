# task_01_domain_control_target

## 目的

戻す（`back`）・先頭へ（`rewind`）の任意キー `target` を扱う domain の部品を作る。
`target` の 3 状態（キーが無い / 空 / あり）の判定・一覧の表示（暫定 32 §3・§6）・OK 時の検査（§5 の 4 文言）・
キー変更の書き換え（§2）を純関数で用意する。
**domain 限定（+ 純関数のテスト）。application / presentation のコードは変えない。スキーマは `target` を読むだけ（読込の正規化は変えない）。**

## 対象範囲（domain 限定・新規 1 ファイル + 既存 1 ファイル）

### `keyseq/domain/sequence_control.py`（既存・変更）

- 公開関数 `control_target(action: Mapping[str, Any]) -> str | None` を追加する
  - system の `back` / `rewind` でなければ `None`
  - `target` キーが**無ければ** `None`（= 指定なし・従来どおり直前のトリガー）
  - キーがあり、値が文字列でない・trim して空なら `""`（= 指定ありだが空）
  - それ以外は `target.strip().lower()`（`config.normalize_key_name` と同じ正規化。config が本モジュールを import するため循環を避けてここでは直書きし、その旨を 1 行コメント）
- `_format_system_value` の `OP_BACK` / `OP_REWIND` の分岐を変える（表示名 `[back]` / `[rewind]` は不変）:
  - `control_target(action) is None` → 現行どおり `[back]` / `[rewind]`
  - `resolve_call` あり → `key, label = resolve_call(action.get("target"))`。`label is None` なら `"{表示名} → {key}（参照先なし）"`・それ以外は `"{表示名} → {key}"`（**ラベルは出さない**）。
    ただし `control_target(action) == ""` のときは `resolve_call` を呼ばず `"{表示名} → （参照先なし）"`
  - `resolve_call` なし → `""` なら `"{表示名} → （参照先なし）"`・それ以外は `"{表示名} → {control_target(action)}"`
  - `→` の前後は半角空白 1 つ。`（参照先なし）` は全角括弧で、空のときは `→` の後に半角空白 1 つを置いてから付ける（`[back] → （参照先なし）`）

### `keyseq/domain/control_target.py`（新規）

- `edit_control_target_violation(owner_key: str, target_key: str, find_trigger: Callable[[str], Mapping[str, Any] | None]) -> str | None`
  - 判定順と文言（暫定 32 §5 の表）:
    1. `normalize_key_name(target_key)` が空 → `"対象のトリガーを選んでください"`
    2. `find_trigger(target)` が `None` → `f"対象のトリガーがありません（{target}）"`（target は正規化後）
    3. `target == normalize_key_name(owner_key)` → `"自分自身は指定できません"`
    4. 対象の `actions` がちょうど 1 行で、その行が system の `back` / `rewind` → `"戻す・先頭へのトリガーは指定できません"`
    5. それ以外 `None`（**循環・深さは見ない**。呼び出しを含む・下流の連鎖が深いトリガーも通す）
  - 呼び出しの `call_graph.edit_call_violation` は変えない・流用しない
- `rename_control_targets(actions: Sequence[dict], old_key: str, new_key: str) -> list[dict] | None`
  - `call_graph.rename_call_targets`（`keyseq/domain/call_graph.py:27`）と同じ形: 正規化した old が空・old == new なら `None` /
    各行を `dict(action)` で写し、`control_target(action) == old`（空でない一致）の行だけ `target` を new（正規化後）へ書き換える / 変えた行が無ければ `None`・あれば新しいリスト（元のリスト・dict は変えない）
  - `call` の行は書き換えない（`rename_call_targets` の契約〔call の target だけ〕はそのまま。両方の適用は task_03 の配線で行う）

### テスト（新規 / 既存へ追加）

- `tests/test_control_target.py`（新規）: `edit_control_target_violation` の 4 文言と判定順・呼び出しを含む / 下流が深い / 循環を含むトリガーを拒否しないこと・
  `rename_control_targets` の書き換え（back / rewind・大文字小文字と空白の正規化・call は書き換えない・元を変えない・不要なら None）
- `tests/test_sequence_control.py`（既存へ追加）: `control_target` の 3 状態（キー無し / 空・空白・非文字列 / あり・正規化）と back / rewind 以外で None・
  表示（指定なしは `[back]` / `[rewind]` のまま・resolve_call あり〔ラベルあり / 空 / 参照先なし〕・resolve_call なし・空の target）。既存の `[back]` / `[rewind]` の assert（:184-185）は残す
- `tests/test_list_clipboard.py`（既存へ追加）: `target` を持つ back の行を copy → paste しても `target` が保たれる（§3。既存の写し方のまま・実装変更なし）

### 設計メモ / 制約

- `control_target` は「キーの有無」で `None` と `""` を区別する（`"target" in action`）。読込（`config.py:162`）は非文字列を `""` にするが、domain の関数は読込を経ない値でも同じ結果になるようにする
- 表示の `resolve_call` は呼び出しと同じ口（`trigger_panel_controller.py` の `_resolve_call_target`。空の target なら `("", None)` を返す）を前提にしてよい。presentation の配線は変えない（既に全行に `resolve_call` を渡している）

## 読むファイル

- `instructions/history/32_back_rewind_target.md` §3・§5・§6（§2 のキー変更の追従）
- `keyseq/domain/sequence_control.py`（全体・218 行・編集対象）
- `keyseq/domain/call_graph.py:1-60`（`call_target` / `rename_call_targets` / `edit_call_violation` の形の手本）
- `keyseq/domain/config.py:81-90`（`normalize_key_name` / `coerce_label`）
- `tests/test_call_graph.py:1-75`（テストの書き方の手本）・`tests/test_sequence_control.py:170-200`・`tests/test_list_clipboard.py`

## 含まない

- `apply_control` の対象の決定・判定の順序・直前のトリガー不変（task_02）
- 編集ダイアログ・`action_edit.py` の検査の配線・`trigger_row_edit.py` でのキー変更の書き換えの適用（task_03）
- `call_graph.py` の変更（既存の呼び出しの契約は不変）
- 正本 `spec_detail/`・`codebase_map.md` の更新（task_04）

## 確認

- 新規 / 追加の単体テストが pass: `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_control_target tests.test_sequence_control tests.test_list_clipboard tests.test_call_graph`
- 既存テスト全 pass: `-m compileall -q keyseq tests` / `-m unittest discover -s tests` / `-m unittest discover -s tests_ui` / `-m tests.smoke_app`（いずれも `.venv` の python・verifier が実行）
- `target` の無い `back` / `rewind` の表示が `[back]` / `[rewind]` のまま（既存 assert が通る）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_03 でまとめて実施（本タスクは UI に出ない）。
