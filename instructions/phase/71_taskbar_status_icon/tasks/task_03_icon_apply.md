# task_03_icon_apply

## 目的

状態に応じて窓のアイコンを差し替え、タスクバーに出す。暫定 54 §3.2（反映の位置と規則）・§3.3（AppUserModelID）・§4.1・§4.2・§4.4（画像）・§5（子窓 = `-default` だけ）を実装する。
**presentation + infrastructure の 1 関数 + `main.py`・domain / application 不変・JSON スキーマ不変・新規依存なし**。

## 対象範囲（presentation・infrastructure の 1 関数・main.py）

### `keyseq/presentation/status_icon/status_icon.py`（新規）

- `class StatusIcon`:
  - `__init__(self, root: tk.Misc, image_dir: Path)`: 土台の画像を読み、3 状態分の画像を作って保持する。**例外を外へ出さない**（失敗はログに残し、印だけのアイコンへ倒す）。
    - 読込（§4.1）: `image_dir` の `app_icon_*.png` を**ファイル名の昇順**で `tk.PhotoImage(master=root, file=…)` で読む。フォルダが無ければ 0 枚。
      使うのは**実際の画像が正方形で辺が 16 / 32 / 48** のものだけ。同じ辺は最初の 1 枚。それ以外・読めないものは使わず `logging` で残す。
    - 合成: 土台ごとに同じ大きさの新しい `PhotoImage` を作り、`copy` で土台を写してから `badge_shapes.badge_pixels(size, state)` を `pixel_runs` で行ごとに `put` する。
    - 使える土台が 0 枚（§4.2）: 16 と 32 の透過の `PhotoImage` に `badge_pixels(size, state, full=True)` を描く。
    - 3 状態（`"on"` / `"off"` / `"paused"`）の画像のタプルを辞書で保持する（参照を持ち続ける・§4.4）。
  - `apply(self, state: HookDisplayState) -> None`（§3.2）:
    - 前回と同じ状態なら何もしない。
    - そうでなければ、前回の状態を `None` にしてから `root.iconphoto(True, *images)` を 1 回呼ぶ。成功したときだけ前回の状態を記録する。
    - 例外は吸収してログに残す（呼び出し元のステータス欄の更新を止めない）。
    - **子窓へ個別に `iconphoto` を呼ばない**（§5）。
- `keyseq/presentation/status_icon/__init__.py`: 必要なら `StatusIcon` を再輸出（公開面の定義のみ）。

### `keyseq/presentation/status_icon/images/`

- サンプル `app_icon_16.png` / `app_icon_32.png` は**メインセッションが作成済み**（触らない）。

### `keyseq/presentation/app.py`

- `__init__` で `self.title(...)`（139 行）の直後に `self.status_icon = StatusIcon(self, status_icon_dir())` を作り、`self.status_icon.apply("off")` を呼ぶ（UI の構築より前・フック開始前は OFF）。

### `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`

- `update_status`: `hook_display_state(...)` の結果を変数に取り、文言（`HOOK_STATE_LABELS`）を作った**直後・簡易表示の分岐より前**に、
  `status_icon = getattr(self._app, "status_icon", None)` が `None` でなければ `status_icon.apply(state)` を呼ぶ（SimpleNamespace のフェイク App では何もしない）。

### `keyseq/infrastructure/win32_window.py`

- `set_app_user_model_id(app_id: str) -> bool` を足す: `_guarded("app_user_model_id", False, …)` で、`ctypes.WinDLL("shell32").SetCurrentProcessExplicitAppUserModelID`（argtypes = `[wintypes.LPCWSTR]`・restype = `ctypes.HRESULT` 相当の `ctypes.c_long`）を呼び、戻り値 0 で真。
  `_ERROR_MESSAGES` に `"app_user_model_id": "AppUserModelID の設定に失敗しました"` を足す。Windows 以外は偽（`_guarded` の既存の挙動）。

### `main.py`

- `APP_USER_MODEL_ID = "keyseq.app"` を定義し、`main()` で `App()` を作る**前に** `set_app_user_model_id(APP_USER_MODEL_ID)` を呼ぶ（戻り値は使わない）。

### テスト（追加）

- `tests/test_win32_window.py`: `set_app_user_model_id` — 成功（0）で真・非 0 で偽・例外で偽（ログは 1 回）・Windows 以外で偽（既存のテストの `patch.object(win32_window.sys, "platform", …)` の作法に合わせる）。
- `tests_ui/test_status_icon.py`（新規）: 実の Tk ルートに対し `wm_iconphoto`（`iconphoto`）を差し替えて呼び出しを記録する方式（§7）:
  - 同じ状態の 2 回目は呼ばない / 状態が変われば `default=True`（第 1 引数が真）で 1 回呼ぶ。
  - 失敗の後の再試行: 1 回目の `iconphoto` が例外 → 同じ状態の次の `apply` で再び呼ぶ。
  - 「ON 成功 → OFF で失敗 → ON」で ON を呼び直す。
  - 画像: 一時フォルダに 16 / 32 の正方形・24 の正方形・16×32 の長方形・壊れたファイルを置き、使われるのが 16 と 32 だけであること（画像の大きさで確認）/ フォルダが無い・使える画像が 0 枚 → 16 と 32 の印だけ。
  - 合成した画像の右上の画素が印の色・左下の画素が土台の色（`PhotoImage.get`）。
  - `update_status` の結線: App（既存の tests_ui の App の作り方に合わせる）でフックの状態を変えて `update_status` を呼ぶと、`status_icon.apply` が `"on"` / `"off"` / `"paused"` で呼ばれる。簡易表示中も呼ばれる。`status_icon` を持たないフェイク App で例外にならない。

### 設計メモ / 制約

- `PhotoImage` は `master=root` で作る（ルートごと・モジュールで共有しない）。
- `status_icon.py` は infrastructure を import しない（AppUserModelID は `main.py` から呼ぶ）。
- 既存の `update_status` の文言・それ以外の処理は変えない。

## 読むファイル

- `instructions/history/54_taskbar_status_icon.md` §3.2・§3.3・§4・§5・§7
- `keyseq/presentation/status_icon/badge_shapes.py`（全体）・`keyseq/presentation/status_text.py`（全体）・`keyseq/presentation/bundled_paths.py`（全体）
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:405-430`
- `keyseq/presentation/app.py:1-60, 100-145`
- `keyseq/infrastructure/win32_window.py:1-70`・`main.py`
- `tests/test_win32_window.py:1-75`（作法の手本）
- `tests_ui/test_status_tooltip.py`（App を作る tests_ui の手本・冒頭の作り方のみ）

## 含まない

- 正本・codebase_map の更新・実機目視（task_05）
- 統合確認・二次レビュー（task_04）
- サンプル画像の作り直し（ユーザーが後で差し替える）

## 確認

- `compileall -q keyseq main.py tests tests_ui` が clean
- `unittest discover -s tests` 全 pass（`set_app_user_model_id` のテストを含む）
- `unittest discover -s tests_ui` 全 pass（`test_status_icon.py` を含む）
- `-m tests.smoke_app` OK
- `git grep -n "iconphoto" keyseq` が `status_icon.py` の 1 か所だけ（子窓へ個別に呼んでいない）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_05 でまとめて実施（タスクバー・子窓・3 状態の見え方）。
