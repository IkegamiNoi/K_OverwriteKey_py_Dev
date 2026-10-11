# task_02_aspect_ratio_resize

## 目的

キーボードUIの窓の縦横比をレイアウトのキー配置に合わせて固定する。ドラッグ中は補正せず、大きさの変化が止まって約 150ms 後に 1 回だけ補正する（暫定 39 §2-3・§5・§6 の 8〜10）。
**presentation 限定・domain / application / infrastructure 不変・スキーマ不変。** task_01（ステータス欄の削除）の後の構成が前提。

## 対象範囲（presentation・新規モジュール 1 + `keyboard_window.py` + テスト）

### 新規 `keyseq/presentation/keyboard_window_size.py`（Tk 非依存の純関数・前例 `compact_window_size.py`）

- 定数: `KEYBOARD_WINDOW_PADDING = 10`（container の padding。`keyboard_window.py` の `ttk.Frame(self, padding=10)` もこの定数を使う）/ `KEYBOARD_WINDOW_MIN_WIDTH = 510` / `RESIZE_SETTLE_MS = 150`
- `layout_aspect(key_specs) -> float | None`: `max(x + w) / max(y + h)`。キーが無い・分母が 0 以下なら None
- `size_from_width(width: int, ratio: float) -> tuple[int, int]`: 窓の内寸の幅から、キャンバス幅 = 幅 − 2×padding、キャンバス高さ = round(キャンバス幅 / ratio)、高さ = それ + 2×padding
- `size_from_height(height: int, ratio: float) -> tuple[int, int]`: 上の逆（幅 = round(キャンバス高さ × ratio) + 2×padding）
- `minimum_size(ratio: float) -> tuple[int, int]`: `size_from_width(KEYBOARD_WINDOW_MIN_WIDTH, ratio)`
- `corrected_size(base: tuple[int, int], current: tuple[int, int], ratio: float) -> tuple[int, int] | None`:
  - 幅も高さも base と同じ → None（移動のみ・補正しない）
  - 幅だけ変わった → `size_from_width(current_w)`
  - 高さだけ変わった → `size_from_height(current_h)`
  - 両方変わった → 今の大きさに収まる最大の形: `size_from_width(current_w)` の高さが `current_h` 以下ならそれ、そうでなければ `size_from_height(current_h)`
  - 結果が最小サイズを下回る（幅 < `KEYBOARD_WINDOW_MIN_WIDTH`）なら `minimum_size(ratio)`
  - 結果が `current` と等しければその値を返す（呼び出し側が「当てない」を判断する）

### `keyseq/presentation/keyboard_window.py`

- 状態（インスタンス属性・winfo に頼らない）: `_ratio: float | None` / `_size_base: tuple[int, int]` / `_resize_job` / `_applied_size: tuple[int, int] | None` / `_suspended: bool`（最大化・最小化中）/ `_ratio_pending: bool`
- 初期化: `geometry("510x210")` と `minsize(510, 210)` を、比率があれば `minimum_size(ratio)` で当てる形に置き換え、`_size_base` をその値にする（比率が無ければ現行値 510×210）
- `self.bind("<Configure>", self._on_window_configure, add="+")`。ハンドラ:
  - `event.widget is not self` → 何もしない（子 widget の Configure を無視。既存の canvas の Configure は従来どおり redraw）
  - `self.state()` が `"zoomed"` / `"iconic"` → 予約を取り消し `_suspended = True` にして戻る（`_size_base` は更新しない）
  - `_suspended` が真（通常状態へ戻った最初の Configure）→ `_suspended = False`、`_size_base = (event.width, event.height)`。`_ratio_pending` なら比率の当て直し（下記）を 1 回行う。補正はしない
  - `_applied_size` が None でない（自分が当てた後の Configure）→ `_size_base = (event.width, event.height)`・`_applied_size = None` にして戻る（OS が丸めても受け入れ・再補正しない）
  - `(event.width, event.height) == _size_base` → 何もしない
  - それ以外 → 予約を取り消して `after(RESIZE_SETTLE_MS, self._settle_size)` を 1 件だけ置く
- `_settle_size`: 予約を消し、今の大きさ（`winfo_width()` / `winfo_height()`）と `_size_base` で `corrected_size` を呼ぶ。None または今の大きさと同じなら `_size_base = 今の大きさ`。違えば `geometry(f"{w}x{h}")` を当て、`_applied_size = (w, h)`・`_size_base = (w, h)`。最大化 / 最小化中なら何もしない
- `update_layout`: 新しい比率を `layout_aspect` で求め、`_ratio` と**違うときだけ**: `_ratio` を更新し、最大化 / 最小化中なら `_ratio_pending = True` で終わり。通常状態なら `_size_base` の幅で `size_from_width` を求めて `minsize(*minimum_size(ratio))` と `geometry` を当て、`_applied_size`・`_size_base` を更新する。比率が同じなら大きさに触らない（設定反映の呼び出しで窓が変わらない）
- `_handle_close`: 予約があれば `after_cancel` してから破棄する
- geometry / minsize / after_cancel の TclError は吸収する（窓の破棄中など）

### テスト

- 新規 `tests/test_keyboard_window_size.py`: `layout_aspect`（通常 / 空）/ `size_from_width`・`size_from_height`（往復で概ね一致・padding の扱い）/ `corrected_size`（移動のみ = None / 幅だけ / 高さだけ / 両方で幅基準が収まる / 両方で高さ基準になる / 最小サイズ未満の引き上げ）
- `tests_ui/test_app_ui_flows.py`: キーボードUIを開いた後、`refresh_keyboard_window()`（同じレイアウト）を呼んでも `geometry` が呼ばれない（`unittest.mock.patch.object` で監視）こと

### 設計メモ / 制約

- 位置は変えない（`geometry` は `WxH` のみ）
- Aero Snap・配置ツールの後に補正されるのは受容（暫定 39 §5）。検出しようとしない
- WM_SIZING / ctypes は使わない（スコープ外）
- 余計な整形変更をしない

## 読むファイル

- `instructions/history/39_keyboard_ui_window.md` §2-3・§5
- `keyseq/presentation/keyboard_window.py`（全体・編集対象。task_01 適用後）
- `keyseq/presentation/compact_window_size.py`（全体・22 行・純関数モジュールの手本）
- `tests/test_compact_window_size.py`（冒頭 30 行・テストの書式）
- `keyseq/presentation/keyboard_layouts.py:20-30`（`KeyboardLayout` / キーの属性）
- `tests_ui/test_app_ui_flows.py:2324-2340`（既存のキーボードUIテスト）

## 含まない

- 「キーボードUIを常に手前」・一時解除・表示欄の変更（task_03）
- 大きさ・位置の保存（スコープ外）
- 正本・codebase_map の更新（task_05）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（新規の純関数テストを含む）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass（geometry 非呼び出しのテストを含む）
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **本タスクでユーザーの実機目視を行う**（暫定 39 §6 の 1・2〔task_01 分〕・8・10）: 縦 / 横 / 斜めのドラッグ後に比率へ合う・ガタつきが無い / キー割当で大きさが変わらない / JIS ⇔ US 切替で比率が変わる / 最大化中の切替と復元 / 最小サイズ付近で振動しない / タイトル表示。
