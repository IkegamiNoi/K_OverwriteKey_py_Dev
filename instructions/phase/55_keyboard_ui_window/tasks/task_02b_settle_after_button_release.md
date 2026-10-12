# task_02b_settle_after_button_release

## 目的

task_02 の実機目視で、ドラッグで縮めると意図より大きく・広げると意図より小さくなる不具合が出た。ドラッグ中（ボタンを押したまま止まった間）に当てた補正が Windows の対話的サイズ変更に上書きされ、基準がずれるため。
**マウスのボタンが押されている間は補正しない**（暫定 39 v0.4 §5「補正」）。
**infrastructure に 1 関数追加・presentation（`app.py` の注入 / `layout_controller.py` の受け渡し / `keyboard_window.py`）。domain / application 不変・スキーマ不変。**

## 対象範囲（infrastructure 1 関数 + presentation 3 ファイル + テスト）

### `keyseq/infrastructure/input_gateway.py`

- モジュール関数 `is_mouse_button_down() -> bool` を `is_own_process_foreground` の近くに追加:
  - 非 Windows（`sys.platform != "win32"`）→ False
  - 共有 windll を変更しない専用の user32（`_foreground_process_api` と同じく `@cache` の小関数で `ctypes.WinDLL("user32").GetAsyncKeyState`・argtypes `[ctypes.c_int]`・restype `ctypes.c_short`）
  - `VK_LBUTTON = 0x01` / `VK_RBUTTON = 0x02` のどちらかで最上位ビット（`& 0x8000`）が立っていれば True（物理ボタン。左右入れ替え設定に依らないため両方を見る）
  - 例外は吸収して False。初回だけ `_logger.exception` で記録（`is_own_process_foreground` の `_foreground_error_logged` と同じ作法・別フラグ）

### `keyseq/presentation/app.py`

- `from keyseq.infrastructure.input_gateway import (...)` に `is_mouse_button_down` を加える
- KeyboardWindow へ渡すため、`self.layout = LayoutController(self)`（:228）より前に `self.is_mouse_button_down = is_mouse_button_down` を置く（App の属性として注入）

### `keyseq/presentation/controllers/layout_controller.py`

- `KeyboardWindow(...)` の生成（:51 付近）に `is_mouse_button_down=getattr(self._app, "is_mouse_button_down", None)` を渡す

### `keyseq/presentation/keyboard_window.py`

- `__init__` にキーワード引数 `is_mouse_button_down: Callable[[], bool] | None = None` を追加し保持する
- `_settle_size` の先頭（予約を消した直後・state 判定の前）で、`is_mouse_button_down` が callable かつ True を返したら `after(RESIZE_SETTLE_MS, self._settle_size)` で置き直して戻る（`_size_base` を変えない）。呼び出しの例外は False 扱い（補正を進める）
- それ以外の補正の規則（task_02）は変えない

### テスト

- `tests/test_input_gateway_repeat.py` の `OwnProcessForegroundTests`（:96〜）の書き方にならい、`is_mouse_button_down` のテストを追加（新規クラス・同ファイル）: 左だけ押下 → True / 右だけ押下 → True / どちらも未押下 → False / API 例外 → False（ログは 1 回）/ 非 Windows → False
- `tests_ui/test_app_ui_flows.py`: キーボードUIの `_settle_size` を、`is_mouse_button_down` が True を返す差し替えで呼ぶと `geometry` が呼ばれず予約が置き直されること・False なら従来どおり補正されることを確認する（大きさを base からずらしてから呼ぶ。`patch.object` で `geometry` と `winfo_width` / `winfo_height` を差し替えてよい）

### 設計メモ / 制約

- 判定は予約の発火時だけ行う（ポーリングを増やさない）
- WM_SIZING / サブクラス化はしない（スコープ外のまま）
- 余計な整形変更をしない

## 読むファイル

- `instructions/history/39_keyboard_ui_window.md` §5「補正」
- `keyseq/infrastructure/input_gateway.py:1-30`（import・logger）と `:85-117`（`_foreground_process_api` / `is_own_process_foreground`・手本）
- `keyseq/presentation/app.py:76-80`・`:126-133`・`:226-230`
- `keyseq/presentation/controllers/layout_controller.py:36-61`
- `keyseq/presentation/keyboard_window.py`（全体・編集対象）
- `tests/test_input_gateway_repeat.py:96-165`（手本）
- `tests_ui/test_app_ui_flows.py:2324-2345`（既存のキーボードUIテスト）

## 含まない

- 「キーボードUIを常に手前」・一時解除（task_03）
- 正本・codebase_map の更新（task_05）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（新規 5 ケース以上）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **ユーザーの実機目視**（暫定 39 §6 の 8: 縦 / 横 / 斜めのドラッグで、ドラッグ中に止まってから離しても意図どおりの大きさで比率へ合う）で task_02 と合わせて完了とする。
