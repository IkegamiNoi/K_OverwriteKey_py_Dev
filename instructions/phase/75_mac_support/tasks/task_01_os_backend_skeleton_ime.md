# task_01_os_backend_skeleton_ime

## 目的

暫定 57 §3.1・§3.2・§3.3 の段階 ① の最初のタスク。`keyseq/infrastructure/os_backend/` の骨格と契約を作り、
Windows の IME の 2 モジュールを移動して `ImeBackend` の裏へ入れる。あわせて import 境界の AST テストと、公開シンボルと Protocol の一致テストを追加する。

**レイヤ制約**: infrastructure と presentation の `key_capture_ime.py` のみ。domain / application 不変・JSON スキーマ不変・Windows の動作不変。テストの件数を減らさない（patch 先の変更は可）。

## 対象範囲（infrastructure + `key_capture_ime.py`・テスト・地図）

### 新規 `keyseq/infrastructure/os_backend/contracts.py`

標準ライブラリのみ import する（tkinter は `TYPE_CHECKING` の下でだけ）。

- `class ImeBackend(Protocol)`:
  - `disable_for_text(self) -> object | None`（戻り値は不透明な予約）
  - `restore_after_text(self, reservation: object | None, character_count: int) -> None`
  - `restore_ime_now(self) -> None`
  - `get_own_open_status(self, window: tkinter.Misc) -> bool | None`
  - `set_own_open_status(self, window: tkinter.Misc, is_open: bool) -> bool`
- `@dataclass(frozen=True) class Capabilities`: 既定値なしの bool 4 つ（§5.4 の「無理な場合」に対応）= `click_through_window` / `window_stacking` / `status_icon` / `ime_control`
- `@dataclass(frozen=True) class OsBackend`: `capabilities: Capabilities` / `ime: ImeBackend`

他の Protocol（`KeyboardBackend` / `MouseBackend` / `WindowBackend` / `TkKeyTranslator` / `AppIdentity`）は**このタスクでは定義しない**（中身のない Protocol を置かない。実体を移すタスクで足す）。

### 新規 `keyseq/infrastructure/os_backend/__init__.py`

- `__all__ = ["Capabilities", "ImeBackend", "OsBackend", "get_backend"]`（contracts から再輸出）
- `get_backend() -> OsBackend`: 初回にロック内で 1 回だけ生成してキャッシュ（`_backend`）。`sys.platform == "win32"` のときだけ**関数の中で** `keyseq.infrastructure.os_backend.windows.backend` を import して `create_backend()` を呼ぶ。それ以外は `RuntimeError`（macOS は task_05）
- **`keyseq/` 内で `sys.platform` を読むのは、最終的にここだけ**（§3.1）

### 新規 `keyseq/infrastructure/os_backend/windows/__init__.py`（空）・`windows/backend.py`

- `class WindowsImeBackend`: `ImeBackend` を満たす。`ime_control` / `own_ime_status` の**モジュール属性経由**で委譲する
  - `get_own_open_status` / `set_own_open_status` はこのクラスの中で `int(window.winfo_id())` に変換して `own_ime_status` を呼ぶ。`winfo_id()` が例外（ルートの破棄の途中など）のときは `logging` の warning（`exc_info=True`）を残し、それぞれ `None` / `False` を返す
- `create_backend() -> OsBackend`: Capabilities はすべて `True`

### 移動（旧パスに横流しを残さない・§3.1）

- `keyseq/infrastructure/ime_control.py` → `keyseq/infrastructure/os_backend/windows/ime_control.py`
- `keyseq/infrastructure/own_ime_status.py` → `keyseq/infrastructure/os_backend/windows/own_ime_status.py`
- 移動先では `sys.platform` のガードと `import sys` を削除する（`win_dll is None` の判定は残す）。それ以外のロジックは変えない

### `keyseq/infrastructure/input_gateway.py`

`from keyseq.infrastructure import ime_control` をやめ、`from keyseq.infrastructure.os_backend import get_backend` にする。
`write_text` と `restore_ime_now` の 3 か所を `get_backend().ime.…` に置き換える（`restore_ime_now` は既存の try の中で `get_backend()` も呼ぶ）。他は変えない。

### `keyseq/presentation/key_capture_ime.py`

- `own_ime_status` の import をやめ、`from keyseq.infrastructure.os_backend import get_backend` にする
- `KeyCaptureImeTracker.__init__` の `get_open` / `set_open` の既定値を `None` にし、`None` なら**インスタンス生成時に** `get_backend().ime.get_own_open_status` / `set_own_open_status` を使う（import 時に backend を生成しない）
- `GetOpen` / `SetOpen` の第 1 引数を窓オブジェクト（`object`）にする。`self._hwnd` を `self._root: object | None` へ替え、ルートの窓オブジェクトを保持して渡す（`int(root.winfo_id())` はここから消える）。呼び出しの順序と分岐は変えない

### テスト

- 新規 `tests/test_os_backend_boundary.py`（OS 非依存・ソースを AST で読む）。`keyseq/` 配下の全 `.py` を走査し:
  1. `sys.platform` の参照（`from sys import platform` を含む）は `os_backend/__init__.py` の 1 か所のみ
  2. `ctypes` / `winreg` / `msvcrt` / `keyboard` の import は `os_backend/windows/` のみ、`objc` / `Quartz` / `AppKit` / `Foundation` / `CoreFoundation` / `ApplicationServices` / `HIServices` / `Cocoa` の import は `os_backend/macos/` のみ
  3. `os_backend` の外からは `keyseq.infrastructure.os_backend` のパッケージ直下だけを import してよい（`.windows` / `.macos` / `.contracts` への直接参照は不可。`from keyseq.infrastructure.os_backend import windows` も不可）
  4. `os_backend/__init__.py` は `.windows` / `.macos` をモジュールのトップレベルで import しない
  - 未移行のファイルは定数の許可リストに**ファイルと違反の種類の組**で書く: `infrastructure/win32_window.py`（sys.platform・ctypes → task_02）/ `infrastructure/input_gateway.py`（sys.platform・ctypes・keyboard → task_03）/ `presentation/modal.py`（ctypes → task_04）。**許可リストの項目が実際には違反していなければ失敗する**テストも置く（移したら消さざるを得ないようにする）
  - 判定関数はソース文字列を受け取れる形にし、違反の例・違反でない例（各規則）の検出を確かめるテストを置く
- 新規 `tests/test_os_backend_contracts.py`: `WindowsImeBackend` の公開メソッド集合と `ImeBackend` のメンバー集合の一致・引数名の一致 / `Capabilities` の既定値なし / `get_backend` のキャッシュ（生成 1 回）と非 Windows の `RuntimeError`（`sys.platform` を patch・`_backend` を None に patch）/ `WindowsImeBackend` の `winfo_id` 変換と例外時の `None` / `False`
- 既存テストの修正（**削除しない**）:
  - `tests/test_ime_control.py` / `tests/test_own_ime_status.py`: import 先とロガー名を新パスへ。`sys.platform` の patch は `ctypes.WinDLL` を `None` にする patch（`create=True`）へ置き換える（「使えない環境」の検証は残す）
  - `tests/test_input_gateway_send.py`: `input_gateway.ime_control` の patch を、`input_gateway.get_backend` が `.ime` に Mock を持つオブジェクトを返す patch へ置き換える
  - `tests/test_key_capture_ime.py`: 窓オブジェクトが渡る前提へ期待値を直す（`test_uses_root_window_hwnd_not_capturing_window_hwnd` はルートのオブジェクトが渡ることを確かめる）
  - `tests_ui/test_capture_ime_entries.py` / `tests_ui/test_capture_hook_entries.py`: hwnd の数値を前提にしていれば同様に直す

### `instructions/common/codebase_map.md`

`ime_control.py` / `own_ime_status.py` を参照する箇所（38・839〜840・846・883・888 行付近）のパスを新パスへ直し、38 行付近に `os_backend/`（`get_backend()`・`contracts.py`・`windows/`）の 1 行を足す。

### 設計メモ / 制約

- 既存ファイルの編集は apply_patch で行う（Python で編集しない）。互換のための `getattr` / `inspect` の逃げ道を足さない
- 新規の Python ファイルのコメント・docstring・文字列は英語（`tests/test_no_japanese_ui_literals.py`）
- 改行コードは対象ファイルの既存のものに合わせる
- `keyboard.write` や `ImeController` の動作を変えない

## 読むファイル

- `instructions/history/57_mac_support.md` §3.1〜§3.3
- `keyseq/infrastructure/ime_control.py` / `own_ime_status.py`（移動対象）
- `keyseq/infrastructure/input_gateway.py:15-25,419-452`
- `keyseq/presentation/key_capture_ime.py`
- `tests/test_ime_control.py:1-15,335-360` / `tests/test_own_ime_status.py` / `tests/test_input_gateway_send.py:300-365` / `tests/test_key_capture_ime.py`
- `tests_ui/test_capture_ime_entries.py:1-70`
- `instructions/common/codebase_map.md:38,839-846,883-888`

## 含まない

- `win32_window` の移動と `WindowBackend` / `AppIdentity`（task_02）
- `input_gateway` の分解と `KeyboardBackend` / `MouseBackend`（task_03）
- `modal.py`・`tk_keys.py`・`action_dialog.py`・ディスパッチャ（task_04）
- `macos/` の作成（task_05）
- 正本 `spec_detail/` の更新（task_14）

## 確認

`.venv` の python（`..\..\..\.venv\Scripts\python.exe`）で実行する（verifier）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests`: 失敗 0・実行件数は基準線 1951 + 新規テスト分以上・skip 7
- `-m unittest discover -s tests_ui`: 失敗 0・1270 件以上（単独実行）
- `-m tests.smoke_app` が pass（tests_ui と並行しない）
- `git grep -n "infrastructure import ime_control\|infrastructure import own_ime_status\|infrastructure\.ime_control\|infrastructure\.own_ime_status"` が 0 件
- 実行後に `config/config.json` の mtime が変わらず、worktree ルートに `user/` / `quarantine/` / `keymap_set_history*.json` が生成されていない

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は本タスクでは行わない（段階 ① の完了時に、IME オンでの文字送信とキーの取得をユーザーがまとめて確認する）。
