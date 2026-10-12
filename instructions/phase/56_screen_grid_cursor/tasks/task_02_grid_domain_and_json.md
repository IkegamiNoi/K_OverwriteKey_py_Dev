# task_02_grid_domain_and_json

## 目的

keymap の任意キー `grid`（枠の形）を扱う domain の純関数群を作り、JSON の読込・正規化・保存の全経路で `grid` を保持する（暫定 40 §3・§5・§8.2 の数値規則）。
**domain の新規モジュール + 既存の正規化・読込・保存の 4 経路への最小の追加のみ。application の状態機械・infrastructure・presentation は不変。JSON スキーマ変更あり（任意キー `grid`・後方互換）。**

## 対象範囲（domain 新規 + JSON の 4 経路 + テスト）

### 新規 `keyseq/domain/screen_grid.py`（tkinter・Win32 に依存しない）

- 定数
  - `DEFAULT_TOP_KEYS = (("q","w","e","r"), ("a","s","d","f"), ("z","x","c","v"))` と、それから作る既定の最上段（3 段 × 4 列・比率は等分）
  - 既定の細分化 `rows=3, cols=3, keys=("q","w","e","a","s","d","z","x","c")`
  - `FIXED_RESERVED_KEYS`: `enter` / `num enter` / `space` / `esc` / `backspace` / `tab` ∪ 修飾キー（`domain/key_hold.py:12` `MODIFIER_KEY_NAMES` を流用）
  - `AUTO_ASSIGN_ORDER`: `q w e r t y u i o p a s d f g h j k l ; z x c v b n m , . / 1 2 3 4 5 6 7 8 9 0`（§5）
  - `MIN_SUBDIVIDE_PX = 4`（§4.3）・`MIN_EDIT_CELL_PX = 8`（§8.2・編集時のドラッグの下限。本タスクでは定数のみ）・細分化の行数・列数の範囲 1〜9
- 形のモデル: 不変の dataclass（例 `GridCell(w, key)` / `GridRow(h, cells)` / `TopLayout(rows)` / `SubLayout(rows, cols, keys)`）と、JSON 形（dict）との相互変換
- `monitor_identifier(left, top, right, bottom) -> str`: `<幅>x<高さ><左><上>`・左と上は符号付き（例 `(0,-768,1024,0)` → `"1024x768+0-768"`・`(0,0,1920,966)` → `"1920x966+0+0"`）（§3・task_01 の確定 3）
- `normalize_grid(raw) -> dict | None`（§3 の読込規則）
  - `raw` が dict でなければ `None`（= `grid` 無し・枠 OFF）
  - 戻りの形は常に `{"enabled": bool, "monitors": {識別子: {"rows": [...]}}, "sub": {"rows": R, "cols": C, "keys": [...]}}`（`enabled` は bool 以外なら false / `monitors` が dict でなければ空 / `sub` が無い・不正なら既定）
  - 最上段の形は**画面ごと**に検査し、不正（段 0・列 0・`h`/`w` が正の数でない〔bool は数として扱わない〕・形の中でのキーの重複・空のキー・固定の予約キー）ならその画面の記録を落とす（= 既定を使う。§3「その形だけ既定へ戻す」）。細分化も同様に不正なら既定（行数・列数が範囲外・R×C < 2・キーの数が R×C と違う・重複・空・固定の予約キー）
  - 正常なら段の `h` の和・各段の `w` の和をそれぞれ 1 へ正規化する。キー名は `normalize_key_name`（`domain/config.py:84`）で正規化
  - 既定へ戻した形ごとに `logging.getLogger(__name__).warning` を 1 回（理由と画面の識別子 / sub）
  - **設定で変わる予約キー（停止・トグル・直接切替キー）は読込時に見ない**（§3・§5）
  - 入力を変更しない（深い写しで組む）
- `top_layout_for(grid: dict | None, monitor_id: str) -> TopLayout`（記録が無ければ既定）/ `sub_layout_of(grid) -> SubLayout`
- 矩形（画面座標の整数・`(left, top, right, bottom)`・右と下は含まない）
  - `top_cell_rects(region, layout) -> list[list[(rect, key)]]`（段ごと）: 境界は比率の累積和 × 幅（高さ）を丸めて求め、隙間・重なりを作らない（最後の境界は必ず領域の端）
  - `sub_cell_rects(region, sub) -> list[(rect, key)]`（読む順）: 等分・同じ丸め方
  - `rect_center(rect) -> (x, y)` = `((left + right) // 2, (top + bottom) // 2)`
  - `can_subdivide(rect, sub) -> bool`: 細分化した 1 枠の幅または高さが `MIN_SUBDIVIDE_PX` 未満になるなら False
- キーの割当（§5）
  - `next_free_key(used: set[str], reserved: set[str]) -> str`: `AUTO_ASSIGN_ORDER` の順で used・reserved・`FIXED_RESERVED_KEYS` に無い最初のキー。無ければ `""`
  - `reassign_top_keys(layout, reserved) -> TopLayout`: 段 1〜3 に Q 段（`q w e r t y u i o p`）/ A 段（`a s d f g h j k l ;`）/ Z 段（`z x c v b n m , . /`）を左から、段 4 に数字段（`1 2 … 9 0`）、足りない分・段 5 以降は `next_free_key` で埋める（重複させない・reserved を飛ばす）
  - `auto_fill_sub_keys(rows, cols, reserved) -> tuple[str, ...]`: 細分化の行数・列数の変更時の埋め直し（`next_free_key` を読む順に）
- 検証（編集の窓の OK 用・§5）
  - `validate_top(layout, reserved) -> list[str]` / `validate_sub(sub, reserved) -> list[str]`: 空のキー・形の中の重複・固定の予約キー・`reserved`（呼び出し側が渡す停止 / トグル / 直接切替キー）を、どの枠かが分かる理由の文字列で返す（空なら OK）。段 0・列 0・比率の不正も返す

### 既存の 4 経路（`grid` を保持するだけ。それ以外の挙動を変えない）

- `keyseq/domain/config.py:311` `_normalize_keymaps`（または `:283` `_normalize_keymap_compat_fields`）: 元の keymap に `"grid"` があり `normalize_grid` が dict を返したら、正規化後の keymap に `"grid"` を入れる（`None` なら入れない）。`grid` の無い keymap の出力は今と同一
- `keyseq/application/config_service/__init__.py:156` `_normalize_loaded_keymap`（個別読込・取り込み）: 組み立てる `keymap` に、`raw_keymap` に `"grid"` があればその深い写しを入れる（正規化は直後の `ensure_config_compatibility` に任せる）
- `keyseq/application/config_service/split_loading.py:448` の `loaded_entry["keymap"]`（個別 JSON の読込）: 同上
- `keyseq/application/config_service/split_payloads.py:507` `build_keymap_file_payload`（保存）: `keymap` に `"grid"` があれば `payload["grid"]` へ深い写しを入れる（無ければ書かない = 既存ファイルに差分を出さない）
- 単一 JSON の書き出しは `ensure_config_compatibility` 経由で `grid` が残ることをテストで確かめる（コードの変更が要らなければ変えない）

### テスト

- 新規 `tests/test_screen_grid.py`: `monitor_identifier`（正・負の座標）/ `normalize_grid`（dict でない → None・`enabled` の型・既定の補い・比率の正規化・画面ごとに不正な形だけ落ちる・sub の不正 → 既定・固定の予約キー・重複・空・bool の比率・入力不変）/ `top_cell_rects`・`sub_cell_rects`（隙間・重なり無し・端が領域と一致・負の座標の領域）/ `can_subdivide` の境界（4px）/ `next_free_key`・`reassign_top_keys`（4 段・5 段・reserved を飛ばす・重複なし）・`auto_fill_sub_keys` / `validate_top`・`validate_sub`（各理由）
- 既存の JSON のテストに追加（新規メソッド・既存は変えない）: 個別 JSON の読込 → 保存で `grid` が保たれる（`tests/test_per_keymap_triggers_load.py` または `tests/test_config_service.py` の既存の書き方に合わせる）/ 取り込み（`_normalize_loaded_keymap` 経由）で保たれる / 単一 JSON の正規化で保たれる（`tests/test_domain_config.py`）/ **`grid` の無い keymap の保存ペイロードに `grid` キーが出ない** / 不正な `grid` で例外にならない

### 設計メモ / 制約

- domain に UI ライブラリ・ctypes を入れない。`logging` は標準ライブラリなので可
- 複製・貼り付けは既存の deepcopy でそのまま写るので触らない（§3・`keymap_triggers.py:20-31`・`list_clipboard.py:24,29`）
- 既定の形は JSON に書かない（`monitors` に記録の無い画面は既定）。`sub` は正規化後の dict に常に入れてよい（`grid` を持つ keymap だけが対象のため既存ファイルに差分は出ない）
- ファイルが 300 行を大きく超えるなら、形のモデルと正規化 / 矩形と割当で 2 ファイルに分けてよい（`keyseq/domain/screen_grid/` パッケージ・`.claude/rules/file_organization_rules.md`）

## 読むファイル

- `instructions/history/40_screen_grid_cursor.md` §3・§4.3（Space の 4px）・§5・§8.2（細分化の範囲・既定に戻す）
- `keyseq/domain/config.py:80-95`・`:255-340`（正規化の書き方と `_normalize_keymaps`）
- `keyseq/domain/key_hold.py:1-40`（`MODIFIER_KEY_NAMES`）
- `keyseq/application/config_service/__init__.py:156-232`
- `keyseq/application/config_service/split_loading.py:425-460`
- `keyseq/application/config_service/split_payloads.py:507-540`
- テストの手本: `tests/test_domain_config.py` の冒頭 40 行・`tests/test_per_keymap_triggers_load.py` の冒頭 60 行

## 含まない

- 枠の操作の状態機械・世代・suppress する集合・`input_router` への組み込み・フックの開始 / 再開の条件（task_03）
- モニタの列挙・カーソル移動 / クリック・枠の窓（task_04）
- ダイアログの「枠を使う」・`grid` の作成（task_05）/ 編集の窓とドラッグ（task_06）
- 正本 `data_schema.md` 等への反映（task_08）・`codebase_map.md` の更新（task_08 でまとめる）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_screen_grid` と、追加した既存 JSON テストのモジュールが pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass（既存の失敗があれば今回と無関係か切り分けて報告）
- `grid` の無い keymap の読込 → 保存のペイロードが変更前と同一（テストで確認）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は不要（task_04・task_06 でまとめて実施）
