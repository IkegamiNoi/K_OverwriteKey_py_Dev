# task_02_icon_foundation

## 目的

アイコンの反映（task_03）の土台を作る。暫定 54 §3.1（判定の切り出し）・§4.3（印の形）・§6（`bundled_paths` の昇格）を実装する。
**presentation 限定・domain / application / infrastructure 不変・JSON スキーマ不変・ステータス欄の表示は変えない**（判定の置き場を移すだけ）。

## 対象範囲（presentation 限定・表示の変更なし）

### `keyseq/presentation/help/bundled_paths.py` → `keyseq/presentation/bundled_paths.py`（移動）

- `git mv` で移す。`bundled_root()` の `parents[3]` を **`parents[2]`** に直す（同じ場所〔リポジトリのルート〕を返す）。
- `status_icon_dir() -> Path` を足す: `bundled_root() / "keyseq" / "presentation" / "status_icon" / "images"`（フォルダは作らない）。
- 旧パスの横流し（re-export）は残さない。利用元の import をすべて新しいパスへ: `help/help_content.py:10` ・ `help/third_party.py:7` ・ `tests/test_help_content.py:10` ・ `tests/test_third_party.py:12`。

### `keyseq/presentation/status_text.py`

- `HookDisplayState = Literal["on", "off", "paused"]` と
  `hook_display_state(hook_active: bool, custom_input_enabled: bool) -> HookDisplayState` を足す（OFF 優先: `hook_active` が偽 → `"off"` / `custom_input_enabled` が偽 → `"paused"` / それ以外 → `"on"`）。
- `HOOK_STATE_LABELS: dict[HookDisplayState, str] = {"on": "ON", "off": "OFF", "paused": "一時停止"}`。

### `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`

- `update_status`（409-415 行）の判定を `hook_display_state(...)` と `HOOK_STATE_LABELS` に置き換える。**文言は今と同じ**（`ON` / `OFF` / `一時停止`）。それ以外は変えない（アイコンの反映は task_03）。

### `keyseq/presentation/status_icon/__init__.py`・`badge_shapes.py`（新規・Tk 非依存）

- 定数: `BADGE_COLORS: dict[HookDisplayState, str] = {"on": "#1E9E3E", "off": "#D93025", "paused": "#F2B400"}` ・ `BADGE_BACKGROUND = "#FFFFFF"`。
- `badge_pixels(size: int, state: HookDisplayState, *, full: bool = False) -> dict[tuple[int, int], str]`: 暫定 54 §4.3 のとおり。
  `(x, y)` → 色。`full=False` は右上の領域（`s = max(7, int(size × 0.45 + 0.5))`）、`full=True` は §4.2 の印だけ（`s = size`）。
  領域 `s × s` を白で塗り、内側 `b`（size < 32 で 1・以上で 2）を除いた `iw = s − 2b` に形を描く:
  ON = 領域の中心・直径 `iw` の円（画素の中心 `(x + 0.5, y + 0.5)` が円の内側〔距離 ≤ iw / 2〕なら緑）/ OFF = `iw × iw` の赤 /
  一時停止 = すき間 `g = max(1, int(iw × 0.2 + 0.5))`・棒の幅 `bw = (iw − g) // 2`・高さ `iw`・余りの左 = 余り // 2。
- `pixel_runs(pixels: dict[tuple[int, int], str], size: int) -> list[tuple[int, int, tuple[str, ...]]]`: 行ごとに連続する画素を `(x_start, y, colors)` にまとめる（`PhotoImage.put` を行単位で呼ぶため）。
- `__init__.py` は空（または公開面の再輸出のみ）。

### テスト（追加・更新）

- `tests/test_status_text.py`: `hook_display_state` の 4 通り（`(False, False)` / `(False, True)` → off・`(True, False)` → paused・`(True, True)` → on）・`HOOK_STATE_LABELS`。
- `tests/test_badge_shapes.py`（新規）: 16 / 32 の領域の位置（右上・`s` = 7 / 14）・48 で `s` = 22・`full=True` の大きさ・白の下地が領域いっぱい・
  OFF の内側が `iw × iw` の赤・一時停止の棒（16 で x = 1–2 と 4–5 が黄・3 が白〔領域の左端を 0 とした座標〕）・
  **16 の ON の画素パターンを固定**（iw = 5 の円: 内側 5×5 のうち四隅が白・残り 21 画素が緑）・`pixel_runs` のまとめ方。
- `tests/test_help_content.py` ・ `tests/test_third_party.py`: import 先の変更だけ（`bundled_root()` が同じ場所を返すことは既存の `test_version_and_bundled_paths` で確かめられる）。

### 設計メモ / 制約

- `badge_shapes.py` は tkinter を import しない（tests から純粋に試す）。四捨五入は `int(x + 0.5)`（`round` は使わない）。
- 形の判定はステータス欄と同じ判定を使う（`hook_display_state` 以外で状態を決めない）。

## 読むファイル

- `instructions/history/54_taskbar_status_icon.md` §3.1・§4.2・§4.3・§6・§7
- `keyseq/presentation/help/bundled_paths.py`（全体）
- `keyseq/presentation/status_text.py`（全体）・`tests/test_status_text.py`（全体）
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:1-30, 405-450`
- `keyseq/presentation/help/help_content.py:1-15` ・ `keyseq/presentation/help/third_party.py:1-12`
- `tests/test_help_content.py:1-20, 71-80` ・ `tests/test_third_party.py:1-25`

## 含まない

- `StatusIcon`（画像の読込・合成・`iconphoto`）・サンプル画像・`update_status` へのアイコンの反映・起動時の設定（task_03）
- `set_app_user_model_id`・`main.py` の変更（task_03）
- 正本・codebase_map の更新（task_05）

## 確認

- `compileall -q keyseq main.py tests tests_ui` が clean
- `unittest discover -s tests` 全 pass（新規・更新のテストを含む）
- `unittest discover -s tests_ui` 全 pass（ステータス欄の文言が変わらないこと）
- `git grep "presentation.help.bundled_paths"` が 0 件
- `-m tests.smoke_app` OK

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視はなし（表示の変更がないため。アイコンの目視は task_05）。
