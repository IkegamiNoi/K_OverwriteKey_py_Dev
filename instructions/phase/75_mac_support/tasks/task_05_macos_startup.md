# task_05_macos_startup

## 目的

暫定 57 §4 の段階 ② の最初。macOS で GUI が起動し主要画面を操作できる状態にする（§9-3 の前半）。
`os_backend` に macOS のスタブを足して `get_backend()` が darwin で返るようにし、依存を環境マーカーで分け、Tk の差（右クリック・`Control` → `Command`）を presentation の 1 か所で吸収する。
契約テストの `windows.*` の import をモジュール先頭から外し、macOS で収集時に落ちないようにする（段階 ① の区切りレビュー M5）。

**レイヤ制約**: infrastructure の `os_backend/` と presentation・テスト・`requirements.txt` のみ。domain / application 不変・JSON スキーマ不変・**Windows の動作不変**（Windows では修飾キーは `Control`・右クリックは `<Button-3>` のまま）。Windows のテスト件数を減らさない（基準 tests 1971 / tests_ui 1270）。

## 対象範囲

### 環境（メインセッション / ユーザー。実装委任の対象外）

- python.org 版 Python 3.13 でリポジトリルートの `.venv` を作り直す（§8 Q1）。`tkinter.TkVersion` が 8.6 であること・`requirements.txt` が入ることを確かめる

### `requirements.txt`

```text
keyboard; sys_platform == "win32"
pyautogui
pynput
pyobjc-framework-Quartz; sys_platform == "darwin"
pyobjc-framework-Cocoa; sys_platform == "darwin"
```

pyobjc は task_06 の probe で使う（本タスクではコードから import しない）。

### `keyseq/infrastructure/os_backend/__init__.py`

`sys.platform == "darwin"` で `keyseq.infrastructure.os_backend.macos.backend.create_backend()` を遅延 import して返す。それ以外は従来どおり `RuntimeError`。

### 新規 `keyseq/infrastructure/os_backend/macos/`（`__init__.py` 空・`backend.py`）

`contracts.py` の 6 Protocol を満たすスタブ。**`pyobjc` / `ctypes` / `keyboard` を import しない**（標準ライブラリのみ）。メソッド名・引数名は Protocol と一致させる（契約テストが検出）。

| クラス | 振る舞い |
|---|---|
| `MacKeyboardBackend` | `register_global_hook` / `register_key_hook` は `OSError`（文言は英語・「task_08 で実装」の趣旨はコメントのみ）→ 既存の `start_hook` の失敗経路に乗る。`unregister_hook` は何もしない。`repeat_timing` は `(500, 33)`。送信系（`resolve_send` / `press_send` / `release_send` / `identity_of` / `needs_shift` / `press_shift` / `release_shift` / `send_native_hotkey` / `write_text`）は `NotImplementedError` |
| `MacMouseBackend` | 全メソッド `NotImplementedError`（task_11） |
| `MacWindowBackend` | `is_own_process_foreground` False / `foreground_own_window` None / `window_handle` は `window.winfo_id()` / `place_window_below` False / `list_monitor_rects` は `[]` / `make_click_through_overlay` False / `is_mouse_button_down`・`is_shift_down`・`is_ctrl_alt_win_down` は False |
| `MacTkKeyTranslator` | `numpad_name` は `""` / `vk_to_scan_code` は None / `vk_to_char` は `""`（task_09） |
| `MacImeBackend` | `disable_for_text` None / `restore_after_text`・`restore_ime_now` は何もしない / `get_own_open_status` None / `set_own_open_status` False（§8 Q4） |
| `MacAppIdentity` | `apply_process_identity` は何もせず True（§5.4）/ `relaunch` は `OSError` のインスタンスを返す（task_12） |

`create_backend()` は `Capabilities(False, False, False, False)` で組み立てる。

### 新規 `keyseq/presentation/tk_platform.py`（Tk の差の唯一の判定点・§4）

- `is_aqua(widget) -> bool`: `widget.tk.call("tk", "windowingsystem") == "aqua"`
- `primary_modifier(widget) -> str`: aqua なら `"Command"`、それ以外は `"Control"`
- `right_click_sequence(widget) -> str`: aqua なら `"<Button-2>"`、それ以外は `"<Button-3>"`
- `accelerator_text(widget, windows_text: str) -> str`: aqua なら `"Ctrl+"` を `"Command-"`、`"Alt+"` を `"Option-"`、`"Shift+"` を `"Shift-"` に置き換えた文字列、それ以外は引数のまま
- `sys.platform` を使わない（AST テストの対象）

### presentation の置き換え（Windows では生成される文字列が今と同一）

- `views/menu_bar.py`: `accelerator=` の 5 か所を `accelerator_text(app, "...")`、91〜100 行の `<Control-…>` を `primary_modifier(app)` で組み立てる
- `views/full_view/keymap_box.py:35-37` / `trigger_box.py:34-37` / `sequence_box.py:39-42` / `compact_view/sequence_frame.py:35-36` / `help/help_tab_view.py:91-92` / `listbox_range_drag.py:106` の `<Control-…>` を同様に組み立てる
- `keyboard_window.py:143`・`help/help_tab_view.py:95` の `<Button-3>` を `right_click_sequence(...)` にする
- 中ボタンの `"<Button-2>"` 系（`call_view_controller.py:54`・`compact_pane_layout.py:32`・`pane_layout_controller.py:61`・`call_view_frame.py:36-37`）は**変えない**（aqua の中ボタン番号の扱いは task_06 の probe で確かめる）

### テスト

- `tests/test_os_backend_contracts.py`（M5）: `windows.*` の import をモジュール先頭から外し、Windows 実装を使うテストは `@unittest.skipUnless(sys.platform == "win32", ...)` のクラスへ移す（テストは削除しない・Windows での件数は不変）。`test_non_windows_platform_raises` は `sys.platform = "linux"` で `RuntimeError` を確かめる形に変える
- 同ファイルに OS 非依存で走る macOS スタブのテストを追加: 6 クラスのメソッド名・引数名が Protocol と一致 / `create_backend()` の組み立てと `Capabilities` がすべて False / darwin で `get_backend()` が macOS のスタブを返す / フック登録が `OSError`
- `tests/test_os_backend_boundary.py`: 変更不要の見込み（macOS スタブが標準ライブラリだけなら通る。落ちたら報告）
- 新規 `tests/test_tk_platform.py`: `widget.tk.call` を Mock で `"win32"` / `"aqua"` にして 4 関数の戻り値（`accelerator_text` は `"Ctrl+Shift+S"` → `"Command-Shift-S"`・`"Ctrl+Alt+P"` → `"Command-Option-P"`）
- 既存の menu_bar 等のテストは、Windows で文字列が同一なので変更不要の見込み（落ちたらテストではなく実装の差を疑う）

### `instructions/common/codebase_map.md`

`os_backend` の節に `macos/backend.py`（スタブ）、presentation の節に `tk_platform.py` を 1〜2 行で追記する。

### 設計メモ / 制約

- 編集は apply_patch。互換の `getattr` / `inspect` を足さない
- macOS 以外の Tk 判定（`tk windowingsystem`）を `tk_platform.py` 以外に書かない
- 起動時に呼ばれる経路（`main.py:12` の `apply_process_identity`・`keyboard_repeat_timing`）は例外を出さない値にしてある。それ以外の経路の macOS での失敗は本タスクでは扱わない（下記「含まない」）

## 読むファイル

- `instructions/history/57_mac_support.md` §3.2・§4・§5.4・§8 Q1/Q4
- `keyseq/infrastructure/os_backend/__init__.py`・`contracts.py`・`windows/backend.py`（スタブの手本）
- `tests/test_os_backend_contracts.py`・`tests/test_os_backend_boundary.py:30-90`
- `keyseq/presentation/views/menu_bar.py:1-30,85-100`、上記の置き換え対象の各行の前後 5 行
- `keyseq/presentation/controllers/hook_controller.py:133-165`（フック開始の失敗経路の確認のみ）

## 含まない

- probe（tap・修飾キー・aqua の keycode・中ボタン番号・Dock のアイコン）と暫定 57 の改訂（task_06）
- 既定プリセットのプロファイル注入・macOS のテスト基準線の記録（task_07）
- CGEventTap のフック・送信・`TkKeyTranslator` の実装（task_08・task_09）、権限の案内（task_10）
- マウス操作・カーソルグリッド等の macOS 実装と無効化の UI（task_11）、再起動（task_12）
- `-transparentcolor` 等のカーソルグリッドの Tk 属性（task_11）
- `.claude/rules/python_rules.md` の Mac の実行コマンド（task_14）
- `spec_detail/` の更新（task_14）

## 確認

**Mac**（メイン / verifier・`../../../.venv/bin/python`）:

- `-c "import tkinter; print(tkinter.TkVersion)"` が 8.6
- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_os_backend_contracts tests.test_os_backend_boundary tests.test_tk_platform` が失敗 0（収集時の ImportError なし）
- `-m unittest discover -s tests` を走らせ、件数・失敗・エラー・skip を記録する（基準線の確定は task_07。本タスクは収集時エラーが `test_os_backend_contracts` から出ないこと）
- `main.py` を起動し、メイン画面・メニュー・キーボードUI が開き、フック開始でエラーのダイアログが出て落ちないこと（ユーザー目視）

**Windows**（ユーザーが Windows 機で・`..\..\..\.venv\Scripts\python.exe`）: 標準検証 4 種（tests 1971 件以上 + 新規分・skip 7 / tests_ui 1270 / smoke pass）。Windows 機で行うまで本タスクは完了扱いにしない。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視: Mac の起動確認は本タスクで実施（ユーザー）。Windows は標準検証 4 種のみ（目視は段階 ② の区切りでまとめて）。
