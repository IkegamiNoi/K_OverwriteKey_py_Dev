# task_11_macos_foreground_and_repeat_timing

## 目的

macOS の backend のスタブのうち、前面の判定とリピート間隔を実装する（暫定 57 §5.4 の表「前面の判定（フックスレッド）」「リピート間隔」・§4.1 の実測「tap のスレッドから `NSWorkspace.frontmostApplication` を呼べた」）。

- 今の Mac は `MacWindowBackend.is_own_process_foreground()` が常に False、`MacKeyboardBackend.repeat_timing()` が常に `(500, 33)`。このため Mac では、自分の窓が前面でもリピートが止まらず（`application/key_repeat.py:89-97`）、キー取得のフック（`presentation/key_capture_hook.py:166`）がキーを拾わない。
- infrastructure（`os_backend/macos/`）限定。contracts・application・presentation・Windows の backend は変えない。

## 対象範囲（`keyseq/infrastructure/os_backend/macos/backend.py` とテストのみ）

### `MacWindowBackend.is_own_process_foreground()`

- `NSWorkspace.sharedWorkspace().frontmostApplication()` の `processIdentifier()` が `os.getpid()` と等しければ True。
- 意味は Windows（`windows/win32_window.py:230-239`）に揃える: 前面のアプリが取れない（None）ときは True、例外のときは False（ログは初回の 1 回だけ。`_physical_flags` の流儀）。
- AppKit は遅延 import（`from AppKit import NSWorkspace`）。テスト用に注入できるようにする（`__init__` の引数 `appkit=None` 等。既存の `quartz=None` と同じ形）。
- tap のスレッドと UI スレッドの両方から呼ばれる（§4.1 で tap のスレッドから呼べることは実測済み）。状態は持たない。

### `MacKeyboardBackend.repeat_timing()`

- `NSEvent.keyRepeatDelay()` と `NSEvent.keyRepeatInterval()`（秒の float）をミリ秒の int にして `(delay, interval)` を返す（四捨五入・1 未満は 1）。
- 取れない（例外・0 以下・数でない）値は、その値だけ既定値（delay 500・interval 33。Windows の `_DEFAULT_REPEAT_*` と同じ値）に置き換える。例外のログは初回の 1 回だけ。
- AppKit は遅延 import・テスト用に注入できるようにする（`MacKeyboardBackend` の既存の注入の形に合わせる）。
- 毎回読む（キャッシュしない。Windows と同じく呼ぶたびに OS の設定を読む）。

### テスト（`tests/test_macos_keyboard_backend.py` に追加、または `tests/test_macos_window_backend.py` を新規）

- Tk なし・AppKit は偽物を注入。Windows でも走る（`sys.platform` で skip しない）。

## 読むファイル

- `instructions/history/57_mac_support.md` §4.1 の表（`:105-125`）・§5.4 の表（`:294-312`）
- `keyseq/infrastructure/os_backend/macos/backend.py`（`_physical_flags` `:35-44`・`MacKeyboardBackend` の `__init__` と `_native_api`・`:290`・`MacWindowBackend` `:305-330`・`:455-470`）
- `keyseq/infrastructure/os_backend/windows/win32_window.py:225-240`・`windows/keyboard_backend.py:35-45,289-299`（意味の手本）
- `keyseq/application/key_repeat.py:85-100`・`keyseq/presentation/key_capture_hook.py:160-175`（呼び出し側の期待）
- `tests/test_macos_keyboard_backend.py`（注入の流儀）

## 含まない

- マウス・クリック位置の記録・M4（task_11a）
- モニタ一覧・クリック透過・窓の重なり順・NSWindow・`Capabilities` と無効化の UI（task_11b）
- aqua のモーダル・`test_minimize_grab_custody`（task_11c）
- 割り当て禁止の文言（task_11d）
- `foreground_own_window()` ほか `MacWindowBackend` の他のスタブ
- 依存の追加（`pyobjc-framework-Cocoa` は `requirements.txt` に darwin のマーカーつきで既にある）

## 確認

Mac（verifier）: compile clean・`tests` が基準線（失敗 6・エラー 10）から増えない・smoke pass。
- tests: 前面の pid が自分 → True・他 → False・`frontmostApplication()` が None → True・例外 → False で 2 回目以降はログしない・`repeat_timing` が 0.5 / 0.033 秒 → `(500, 33)`・0.25 / 0.015 → `(250, 15)`・片方の例外 / 0 以下 → その値だけ既定値・両方の例外 → `(500, 33)`。
- tests_ui: `tests_ui` のうち key_repeat / key_capture_hook に関係するものがあれば 1 本ずつ（無ければ省略を報告）。
Windows: task_09〜10 の Windows 検証と合わせて `tests`（Windows の backend は無変更）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。`codebase_map.md` の Mac の backend の行（前面の判定・リピート間隔がスタブである旨の記述があれば）を追従（メイン）。
- 実機目視（Mac・本タスクで実施）:
  1. 「システム設定 > キーボード」のリピートの速さ / 開始までの時間を変え、リピートのアクションの間隔が追従する（アプリの再起動なしで次の押下から）。
  2. 自分の窓が前面のとき、リピートのトリガーを押してもリピートしない（Windows と同じ）。他のアプリが前面ならリピートする。
  3. 自分の窓が前面のとき、キーの取得（キー取得のフックを使う欄）でキーが拾える。

## 起票レビュー（reviewer「修正して採用」2026-11-15）の反映 — 上の記述に優先する

- **中 1（注入）**: `MacKeyboardBackend.__init__` と `MacWindowBackend.__init__`（今はどちらも `quartz=None` だけ・`macos/backend.py:73,306`）に `appkit=None` を足す。AppKit はメソッド内の遅延 import（`from AppKit import NSEvent, NSWorkspace`）で引き、注入があればそれを使う（`MacImeBackend(tis=None)` の `:366-372` の流儀）。新しいローダー関数は作らない。読むファイルの `:455-470` は外す。
- **中 2（値の丸め）**: 秒の生値が有限の数（bool を除く）で 0 より大きければ `max(1, round(x * 1000))`。それ以外（例外・0 以下・NaN・inf・bool・数でない）は、その値だけ既定値。テストに NaN / bool を各 1 件足す。
- **中 3（スレッド）**: `repeat_timing` も tap のスレッドから呼ばれる（`key_capture_hook.py:92-93` の `_timeout_seconds`・`app.py:238` の `repeat_delay_ms`）。`NSEvent.keyRepeatDelay` / `keyRepeatInterval` を tap のスレッドから読む実測は無いので、目視 1 に「リピート中・キー取得中にクラッシュや固まりが無い」を足す。目視 1 で設定の変更に追従しなければ報告して止める。
- **低（テストの置き場）**: 両方とも `tests/test_macos_keyboard_backend.py` に追加（`MacWindowBackend` の既存のテストもここにある。メインが確認）。
- **低（tests_ui）**: `tests_ui/test_capture_hook_entries.py`・`tests_ui/test_capture_ime_entries.py` を 1 本ずつ。tests は `tests/test_key_capture_hook.py`・`tests/test_key_repeat.py` も対象。
- **低（codebase_map）**: `codebase_map.md:39` の「マウス・他の窓系はスタブのまま」を「`is_own_process_foreground`（`frontmostApplication` の pid）と `repeat_timing`（`NSEvent`）も実装。マウス・他の窓系はスタブのまま」に直す。
- **目視 3 の具体**: キーボードUIのキーをクリックして置換元の編集に入り（`keyboard_window.py:589`）、自分の窓が前面の状態で Esc 以外の文字キー・Shift+文字を押すと記録される。トリガーの追加ダイアログ（`trigger_dialog.py:94`）でも同じ。他のアプリを前面にしたときは拾わない。

## 実装後の改訂（2026-11-15・Mac 目視・暫定 57 v0.13）— 上の `repeat_timing` の記述に優先する

目視 1 で、システム設定を変えてもリピートの速さが変わらなかった（落ちる・固まるは無し）。メインの実測: `NSEvent.keyRepeatDelay` / `keyRepeatInterval` は Tk の起動後もシステム設定を反映せず 0.5 / 0.083 秒に固定。一方 `defaults read -g` は `InitialKeyRepeat = 30`・`KeyRepeat = 5`。ユーザー判断「推奨どおり変える」で取得元を変える。

- `repeat_timing` は Foundation の `CFPreferencesAppSynchronize(".GlobalPreferences")` の後に `CFPreferencesCopyAppValue("InitialKeyRepeat" / "KeyRepeat", ".GlobalPreferences")` を読み、値 × 15 を ms にする（delay = `InitialKeyRepeat`・interval = `KeyRepeat`）。毎回読む。
- 有効な値 = 有限の数（bool を除く）で 0 より大きい。ms は `max(1, round(x * 15))`。それ以外（None = 一度も設定を変えていない・例外・0 以下・NaN・inf・bool・数でない）はその値だけ既定値（500 / 33）。例外のログは初回の 1 回だけ。
- 注入は `appkit=None` を `foundation=None` に置き換える（AppKit は `repeat_timing` で使わなくなる。`MacWindowBackend` の `appkit=None` はそのまま）。Foundation はメソッド内の遅延 import（`pyobjc-framework-Cocoa` に含まれる）。
- テスト: `InitialKeyRepeat` 30 / `KeyRepeat` 5 → `(450, 75)`・15 / 2 → `(225, 30)`・None → 既定値・片方の例外 / 0 以下 / NaN / bool → その値だけ既定値・Synchronize の例外 → 両方とも既定値で 1 回だけログ・呼ぶたびに読む。NSEvent のテストは置き換える。
- 目視 1 をやり直す（設定の変更が次の押下から追従するか・体感の速さが OS のリピートと合うか）。
- 目視 3 の文言の訂正（ユーザー指摘 2026-11-15）: 「自分の窓が前面」は「このアプリのどれかの窓（キーボードUI・ダイアログを含む）が前面」の意味。キーボードUIはクリックして使うため、メインの窓が前面のまま置換元の編集をする状況は起きない。
