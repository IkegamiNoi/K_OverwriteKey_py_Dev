# task_01_grid_ops_domain

## 目的

keymap の `grid` に任意キー `ops`（枠の操作キー）を加え、正規化・保存・読み出し・検査の純関数を domain に置く（暫定 41 §3・§4・§8「OK の検査」「自動割当・振り直し」）。
あわせて枠のキーの読込時の固定の予約キーを**修飾キーだけ**に縮め、操作キーとの重なりは検査関数の引数で扱う。
**domain 限定**（`keyseq/domain/screen_grid/` のみ）。application / presentation / infrastructure は変えない（既定の引数で今の呼び出し元の挙動を保つ）。JSON スキーマ変更あり（`grid.ops`・後方互換）。

## 対象範囲（domain 限定・`keyseq/domain/screen_grid/`）

### 新規 `ops.py`

* 定数
  * `GRID_OPS: tuple[str, ...] = ("deepen", "back", "click", "next_screen", "up", "down", "left", "right")`（この順が操作どうしの重なりの優先順位・暫定 41 §5）
  * `DEFAULT_OPS: Mapping[str, str]` = deepen `space` / back `backspace` / click `enter` / next_screen `tab` / up `up` / down `down` / left `left` / right `right`（読み取り専用にする。`types.MappingProxyType` 等）
  * `FIXED_BACK_KEY = "esc"` / `FIXED_CLICK_KEY = "num enter"` / `FIXED_OP_KEYS = frozenset({FIXED_BACK_KEY, FIXED_CLICK_KEY})`
* `normalize_ops(raw: Any) -> tuple[dict[str, str], tuple[str, ...]]`
  * 戻り値 = (8 操作すべてを持つ正規化済みの dict, 既定へ戻した操作名のタプル〔`GRID_OPS` の順〕)
  * raw が dict でなければ全操作が既定・戻した操作 = `GRID_OPS` 全部（呼び出し側が「dict でない」ログを出す）
  * 操作ごとに独立に判定: 値が文字列でない / `grid_key_name` 後に空 / 修飾キー（`MODIFIER_KEY_NAMES`）/ 固定の操作キー（`FIXED_OP_KEYS`）なら既定・戻した操作に入れる。無い操作は既定（**戻した操作には入れない**）
  * 未知の操作名は捨てる。**操作どうし・枠のキー・予約キーとの重なりでは戻さない**
* `ops_of(grid: Any) -> dict[str, str]`: 実行時の守りの読み出し。`grid` が dict でない・`ops` が無い・不正でも 8 操作を既定で埋めて返す（`normalize_ops(...)[0]`・ログなし）
* `ops_to_json(ops: Mapping[str, str]) -> dict[str, str] | None`: 8 操作すべてが `DEFAULT_OPS` と同じなら `None`、違えば 8 操作すべてを `GRID_OPS` の順で持つ dict
* `operation_keys(ops: Mapping[str, str]) -> frozenset[str]`: 8 操作のキー ∪ `FIXED_OP_KEYS`
* `default_operation_keys() -> frozenset[str]`: `operation_keys(DEFAULT_OPS)`
* `validate_ops(ops: Mapping[str, str], reserved: Collection[str], frame_keys: Collection[str]) -> list[str]`（編集の窓の OK 用・暫定 41 §8）
  * 操作ごとに（`GRID_OPS` の順で）: 空 / 修飾キー / 固定の操作キー / 先の操作と重複 / 予約キー（`reserved` を `grid_key_name` したもの）/ 枠のキー（`frame_keys`）と重なり、を理由つきで返す
  * 文言は「操作キー（<日本語の操作名>）: …」。操作名 = 深くする / 戻る / クリック / 次の画面へ / 上へ / 下へ / 左へ / 右へ（`OP_LABELS` として公開。task_04 のパネルでも使う）

### `normalize.py`

* `FIXED_RESERVED_KEYS` を**廃止**し、`_key_error` の固定の予約キーの判定を `MODIFIER_KEY_NAMES` にする（理由の文言 = 「修飾キー {key!r} です」）
* `normalize_grid`: `raw` に `"ops"` があれば `normalize_ops` に通す
  * `ops` が dict でなければ警告ログ 1 回（「Invalid screen grid ops; using defaults」相当）
  * dict で戻した操作があれば警告ログ 1 回（戻した操作名を並べる）
  * `ops_to_json` が `None` でなければ `normalized["ops"]` に入れる（既定と同じなら書かない）。`"ops"` が無ければログなし・書かない
* 既存のキー（`enabled` / `monitors` / `sub` / `label_position`）の扱いは変えない

### `assignment.py`

* `_normalized_reserved` の固定分を `MODIFIER_KEY_NAMES` に替え、**操作キーも塞ぐ**: 各関数にキーワード専用引数 `op_keys: Collection[str] | None = None` を足し、`None` なら `default_operation_keys()` を使う
  * 対象: `next_free_key` / `reassign_top_keys` / `auto_fill_sub_keys` / `validate_top` / `validate_sub`
  * 既定の引数で今の呼び出し元（`presentation/dialogs/grid_editor_window.py`）は変更なしで、enter / space 等の既定の操作キーを今までどおり拒否・飛ばす
* `_check_shape_key`: 修飾キー →「修飾キー {key!r} は使えません」/ 操作キー →「操作キー {key!r} と重なっています」/ 予約キー → 従来どおり「予約キー {key!r} は使えません」（判定順 = 空 → 重複 → 修飾キー → 操作キー → 予約キー）

### `__init__.py`

* `FIXED_RESERVED_KEYS` の再輸出をやめ、`ops.py` の公開面（`GRID_OPS` / `DEFAULT_OPS` / `OP_LABELS` / `FIXED_BACK_KEY` / `FIXED_CLICK_KEY` / `FIXED_OP_KEYS` / `normalize_ops` / `ops_of` / `ops_to_json` / `operation_keys` / `default_operation_keys` / `validate_ops`）を足す

### テスト（`tests/test_screen_grid.py`・必要なら `tests/test_screen_grid_ops.py` を新規）

* 既存の書き換え（暫定 41 §9-9）:
  * `FIXED_RESERVED_KEYS` の import とそれを回すテスト（`:135`）→ 修飾キーを含む形は既定へ戻る / **enter・space・esc・backspace・tab・num enter を含む形は読込で戻らない**、に書き換える
  * `:126` の `["enter", "w"]` の細分化 → 読込で戻らない側へ移す
  * `validate_top` / `validate_sub` の「固定予約」の期待（`:217`・`:239-241`）→「操作キー」の文言へ。修飾キーの拒否の確認を足す
  * `next_free_key` の `{"e", "ENTER"}`（`:188`）は引き続き `r`（既定の操作キーを飛ばすことは文字キーに影響しない）
* 新規:
  * `normalize_ops`: 欠けた操作は既定・不正（非文字列 / 空 / 修飾キー / esc / num enter）は操作ごとに既定・未知の操作名は捨てる・重なりでは戻さない・大文字と前後の空白の正規化・dict でない
  * `normalize_grid`: `ops` が無い / 既定と同じなら出力に `ops` が無い（**既存の `grid` の正規化結果が変わらない**）・既定と違えば 8 操作すべてが出る・警告ログ（`assertLogs`）の回数・入力を書き換えない
  * `ops_of` / `ops_to_json` / `operation_keys`
  * `validate_ops`: 各理由・`GRID_OPS` の順の重複判定・既定の ops は `validate_ops(DEFAULT_OPS, set(), default_top のキー ∪ default_sub のキー)` で空
  * `op_keys` 引数: 付け替えた操作キー（例 `h`）を `next_free_key` / `reassign_top_keys` / `auto_fill_sub_keys` が飛ばし、`validate_top` / `validate_sub` が「操作キー」で拒否する / 既定（None）で enter・space を拒否する

## 設計メモ / 制約

* `ops.py` は `normalize.py` の `grid_key_name` と `..key_hold.MODIFIER_KEY_NAMES` を使う。`normalize.py` → `ops.py`、`assignment.py` → `ops.py` の向き（`ops.py` から `assignment.py` を import しない・循環させない）
* 4 経路の JSON（`domain/config.py` 等）は `grid` を丸ごと `normalize_grid` に通しているので**触らない**（`normalize_grid` が `ops` を扱えば足りる・暫定 41 §4）
* `validate_ops` の `frame_keys` の集め方（今つながる画面 + 既定 + 細分化）は呼び出し側（task_04）の責務。domain は受け取った集合で判定するだけ
* 互換のための別名（`FIXED_RESERVED_KEYS = MODIFIER_KEY_NAMES` 等）を残さない（恒久互換レイヤー禁止）。参照元は `tests/test_screen_grid.py` だけ（実測）

## 読むファイル

* `instructions/history/41_grid_crosshair_nudge.md`（§3・§4・§5「優先順位」・§8「OK の検査」）
* `keyseq/domain/screen_grid/normalize.py`・`assignment.py`・`models.py`・`__init__.py`（全体・編集対象）
* `keyseq/domain/key_hold.py`（`MODIFIER_KEY_NAMES` の定義のみ）
* `tests/test_screen_grid.py`（全体・編集対象）
* `instructions/common/spec_detail/data_schema/5_06_01_keymap_grid.md`（`label_position` の保存の作法）

## 含まない

* セッション・振り分けで操作キーを使うこと・suppress 集合・クリック点の移動（task_02）
* 十字マークの描画（task_03）
* 編集の窓の操作キーの欄・`validate_ops` の呼び出し・`frame_keys` の収集・`op_keys` を渡す配線・結果の取り込み（task_04）
* 正本 `spec_detail/` の改訂・`codebase_map.md`（task_07）

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_screen_grid`（と新規ファイルがあればそれ）が全 pass
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass（既存件数 + 新規）
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass（既知の実行順依存 2 件は current.md「テスト負債」のとおり切り分けて報告）
* `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` OK
* `grep -rn FIXED_RESERVED_KEYS keyseq tests tests_ui` が 0 件

## 完了条件

* 上記確認 pass・**reviewer 採用**
* 実機目視なし（domain のみ・既定の引数で編集の窓の挙動は不変）
