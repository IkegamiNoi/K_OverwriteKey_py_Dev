# task_01_capture_ime_foundation

## 目的

キーの取得中に IME を OFF にするための土台を作る（暫定 44 §4・§5・§6）。
自アプリの IME の開閉を読む・変える**状態なしの口**（infrastructure）と、取得の寿命（数・印・開始 / 終了の冪等・`<Destroy>`）を持つ**部品**（presentation）、`??` の判定関数、案内の文言の変更。
**入口への配線はしない（task_02・task_03）。application・domain・`ime_control.py`（送信側）不変・JSON スキーマ不変。**

## 対象範囲（infrastructure 新規 1・presentation 新規 1 + 既存 2・テスト新規 2 + 既存 1）

### `keyseq/infrastructure/own_ime_status.py`（新規）

自アプリの UI スレッドの入力コンテキストの開閉を読む・変える。状態を持たない（暫定 44 §4.1・§4.4・§6）。

* Win32 の薄い包み `_Win32OwnImeApi`（imm32 の `ImmGetContext` / `ImmReleaseContext` / `ImmGetOpenStatus` / `ImmSetOpenStatus`。`argtypes` / `restype` を明示）。Windows 以外・`WinDLL` なしは `OSError` で生成失敗
* 公開関数:
  * `get_open_status(hwnd: int) -> bool | None` — `ImmGetContext(hwnd)` → `ImmGetOpenStatus` → `ImmReleaseContext`（finally）。コンテキストが取れない・API がない・例外は `None`
  * `set_open_status(hwnd: int, is_open: bool) -> bool` — 同様に `ImmSetOpenStatus`。成功で `True`、それ以外は `False`
* API の生成は初回に 1 回（失敗は warning を 1 回ログし以後 `None` / `False`）。例外は握りつぶさず `_logger.exception` で記録して `None` / `False` を返す
* テストで API を差し替えられるようにする（例: 関数に `api` 引数の既定 `None` → 既定の API、または API を返す内部関数を差し替え可能に）

### `keyseq/presentation/key_capture_ime.py`（新規）

取得の寿命の部品（暫定 44 §4.2・§4.3・§6）。取得は UI スレッドだけで完結するためロックは不要。

* クラス `KeyCaptureImeTracker(get_open, set_open)` — `get_open(hwnd) -> bool | None` / `set_open(hwnd, is_open) -> bool` を注入（既定は `own_ime_status` の 2 関数）
  * 状態: 取得中の入口（`owner` → 登録した `<Destroy>` の情報）・「アプリが OFF にした」印・IME の操作に使う hwnd
  * `begin(owner: object, window) -> None`
    * `owner` が取得中なら**何もしない**（数も問い合わせも変えない・§4.2 開始の冪等）
    * hwnd = **ルートの窓**（`window.nametowidget(".")`）の `winfo_id()`（Tk の窓はすべて同じ入力コンテキストを共有し、破棄途中の窓の HWND を使わないため。暫定 44 §1 probe）
    * `get_open(hwnd)` が `True` なら `set_open(hwnd, False)`。成功したら印を立てる（立っていれば立てたまま）。`None`・失敗は IME に触らず取得は続ける（§4.4）
    * `owner` を取得中にし、`window.bind("<Destroy>", ..., "+")` で終了を結ぶ。ハンドラは **`event.widget is window` のときだけ** `end(owner)` を呼ぶ（§4.2・前例 `hook_controller.py:57-64`）
  * `end(owner: object) -> None`
    * `owner` が取得中でなければ**何もしない**（印にも触らない）
    * `owner` を外し、登録した `<Destroy>` を外す（`unbind("<Destroy>", funcid)`。窓が既に破棄済みの `TclError` は無視）
    * **取得中の入口が 0 になったときだけ**: 印が立っていれば `get_open(hwnd)` が `False` のとき `set_open(hwnd, True)`、印を下ろす（`True`〔手で ON にした〕・`None` なら戻さず印を下ろす）。数が残る終了では印に触らない
  * `is_capturing(owner) -> bool`（テスト・入口の確認用）
* モジュールの既定のインスタンスと関数 `begin_key_capture(owner, window)` / `end_key_capture(owner)`（入口はこれを呼ぶ）。既定のインスタンスは初回に作る（`ime_control._get_controller` と同じ形）

### `keyseq/presentation/tk_keys.py`

* `UNRESOLVED_KEY_NAME = "??"` と `is_unresolved_capture_key(name: str) -> bool` を追加（Tk が名前を判別できないキー。暫定 44 §5）

### `keyseq/presentation/hook_button_texts.py`

* `UNKNOWN_CAPTURE_KEY_HINT_TEXT` を **「このキーは取得できません。別のキーを押してください。（Escでキャンセル）」** に変更（暫定 44 §2・§5）。既存テストは定数を参照しているため期待値の変更は不要の見込み

### テスト

* `tests/test_own_ime_status.py`（新規）: 偽の API で get / set の成功・コンテキストが取れない（0）・例外・API なし（Windows 以外）・`ImmReleaseContext` が必ず呼ばれる
* `tests/test_key_capture_ime.py`（新規）: 偽の `get_open` / `set_open` と偽の窓（`bind` / `unbind` / `nametowidget` / `winfo_id` を持つ最小の物。Tk 不要）で
  1. ON で開始 → OFF・終了 → ON へ戻る / OFF で開始 → 終了で何もしない
  2. 開始の冪等（同じ owner の 2 回目の開始は問い合わせもしない）・終了の冪等（2 回目・未開始の終了は何もしない）
  3. 重なり: A 開始（ON→OFF）→ B 開始（OFF のまま）→ A 終了（戻さない・印は残る）→ B 終了（ON へ戻る）
  4. 2 番目の入口の開始で手で ON にされていれば OFF にする
  5. 取得中に手で ON にした → 最後の終了で触らない
  6. `<Destroy>` の絞り込み: 子の破棄（`event.widget` が別）では終了しない・窓自身で終了する
  7. 失敗: `get_open` が `None` → 取得は始まる（取得中になる）・終了で何もしない / `set_open` が `False` → 印を立てない
* `tests/test_tk_keys.py`: `is_unresolved_capture_key` の `??` / 通常のキー名 / 空文字

### 設計メモ / 制約

* 状態（数・印）は presentation の部品が持ち、infrastructure は状態なし（暫定 44 §6・deep-reviewer L2）
* 送信側の `ime_control.py`・`ImeController`・`WM_IME_CONTROL` は使わない・変えない（ctypes の書き方の参考にだけ読む）
* `owner` は入口を表す任意のオブジェクト（例: ダイアログ自身・`(dialog, "hotkey")`）。同一性（`==` / ハッシュ）で扱う
* 新規ファイルは 300 行以内・関数 30 行以内を目安

## 読むファイル

1. `instructions/history/44_ime_off_during_key_capture.md` §4・§5・§6（設計）
2. `keyseq/infrastructure/ime_control.py:1-60,303-338`（ctypes の宣言・Windows 以外の扱い・既定インスタンスの形）
3. `keyseq/presentation/controllers/hook_controller.py:50-64`（`<Destroy>` の絞り込みの前例）
4. `keyseq/presentation/tk_keys.py`（全体・追加先）
5. `keyseq/presentation/hook_button_texts.py`（全体・変更先）
6. `tests/test_ime_control.py`（偽の API の書き方の参考・冒頭 60 行程度）・`tests/test_tk_keys.py`（追加先）

## 含まない

* 入口 #1〜#4 の配線と `??` の統一（各入口の `== "??"` の置き換えを含む）（task_02）
* 入口 #5〜#8 の配線と `??` の統一・実機目視（task_03）
* 統合確認（task_04）/ 正本・`codebase_map.md` の更新（task_05）
* 送信側の IME（`ime_control.py`）の変更 / 取得中のフック再開（idea_48）

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_own_ime_status tests.test_key_capture_ime tests.test_tk_keys -v` が全 pass（上記 1〜7 を含む）
* 既存の `tests`（`unittest discover -s tests`）・`tests_ui`（`unittest discover -s tests_ui`・同時に 1 本だけ）・`-m tests.smoke_app` が全 pass（`tests_ui/test_prohibited_assign_keys_ui.py` の案内の文言を含む）
* 実機の Win32 API を使う確認はしない（入口の配線前のため。実機目視は task_03）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_03 でまとめて実施（本タスクでは行わない）。
