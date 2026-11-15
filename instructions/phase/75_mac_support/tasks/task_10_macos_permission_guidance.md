# task_10_macos_permission_guidance

## 目的

macOS の権限（アクセシビリティ）の確認と案内、実行中の権限の喪失・tap の障害からのフックの停止と通知を実装する（暫定 57 §5.2・§5.1「tap の障害・権限の喪失はフックの停止として扱う」・task_08b から送った事項）。

- Windows の動作は変えない（Windows の backend は新しい口で何もしない / 常に許可済みを返す）。
- OS の判定は backend の中だけ。presentation / application は backend の口を通す。
- 新しい文言は `ja.json` と `en.json` の両方に足す（`ui_terms.md`・ソースに日本語を書かない）。

## 対象範囲

### backend（`keyseq/infrastructure/os_backend/`）

- `contracts.py` の `KeyboardBackend`（または適切な Protocol）に次の口を足す:
  - `input_permission_granted() -> bool`: 入力の権限があるか。macOS = `AXIsProcessTrusted()`（`ApplicationServices`・遅延 import・取れなければ True を返して tap の作成の成否に任せる）。Windows = 常に True。
  - `open_input_permission_settings() -> bool`: システム設定のアクセシビリティの画面を開く。macOS = `open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"`（`subprocess`・失敗は False）。Windows = 何もせず False。
  - 実行中の障害の通知: フックの登録に障害時のコールバックを渡せるようにする（例 `register_global_hook(callback, *, suppress, on_failure=None)`、または `set_hook_failure_listener(callback)`。どちらかを選んで報告）。Windows は呼ばない。
- `macos/event_tap.py`:
  - `start()`: tap の作成の前に `input_permission_granted()` が偽なら、tap を作らずに権限不足を表す例外を出す（`OSError` の派生など。上位で権限の案内に切り替えられる型・属性にする）。`CGEventTapCreate` が NULL のときも同じ例外にする（§5.2: 判定は `AXIsProcessTrusted` と `CGEventTapCreate` の成否）。
  - `kCGEventTapDisabledByTimeout` / `ByUserInput`（自分の `stop()` 中でないとき）: 今の再有効化と掃除に加えて、`input_permission_granted()` が偽なら再有効化せずに障害を通知する（権限の喪失）。再有効化したのに有効にならない（`CGEventTapIsEnabled` が偽）ときも障害を通知する。
  - CFRunLoop のスレッドが例外で終わったとき（今はログだけ）も障害を通知する。
  - 障害の通知は tap のスレッドから呼ばれる。通知の後の入力は素通し（例外時は素通しの既存の契約）。通知は 1 回の稼働につき 1 回。
- `macos/backend.py`: 上の口を `EventTap` へつなぐ。

### application / presentation

- `application/hook_coordinator.py`: フックの開始の失敗のうち権限不足の例外は、今の `start_failed` ではなく権限の案内の文言で `on_error` に渡す（例 `application.hook.permission_required_title` / `..._body`）。ほかの例外は今のまま。
- `presentation/controllers/hook_controller.py`:
  - 権限の案内を出すとき、「システム設定を開く」を選べるダイアログにし、選んだら `open_input_permission_settings()` を呼ぶ（開けなければ手で開く案内の文言）。ダイアログの置き場所は既存のダイアログの作法に合わせる（`messagebox.askyesno` 等で足りるならそれでよい）。
  - 実行中の障害の通知を受けたら、既存の `_handle_overload` と同じく**優先の経路で**フックを止め（世代の更新は停止の処理の中）、権限がなければ権限の案内、あれば「入力の監視が止まった」旨の通知を出す（新しい文言）。1 回だけ。
  - 許可後の再試行は「フック開始」の再操作（自動では再開しない）。
- 案内の本文には次を含める: アクセシビリティで許可すること・開発実行（python から起動）では許可の対象がターミナルまたは python になること・許可後に「フック開始」をもう一度押すこと・それでも開始できなければアプリを再起動すること（同じプロセスでの再試行の可否は本タスクの目視で実測する）。入力監視（`CGPreflightListenEventAccess`）は本文で触れるだけ（§5.2）。

### 依存

- `requirements.txt` に `pyobjc-framework-ApplicationServices; sys_platform == "darwin"` を足す（今は pynput の推移依存・段階 ② の区切り L8）。

## 読むファイル

- `instructions/history/57_mac_support.md` §5.1（tap の障害の条項・`:130-150` 付近）・§5.1.1（優先の経路）・§5.2
- `keyseq/infrastructure/os_backend/macos/event_tap.py`（全体）・`macos/backend.py:80-130`・`os_backend/contracts.py:20-64,110-135`・`windows/keyboard_backend.py`（`register_global_hook` の周辺）
- `keyseq/application/hook_coordinator.py:20-90`
- `keyseq/presentation/controllers/hook_controller.py:130-200,300-400`（`start_hook`・`_handle_overload`）
- `keyseq/shared/i18n/locales/ja.json:800-815`・`en.json:800-815`・`instructions/common/spec_detail/ui_terms.md`（用語）
- `requirements.txt`・`tests/test_hook_coordinator.py`・`tests/test_macos_keyboard_backend.py`

## 含まない

- 入力監視（`CGPreflightListenEventAccess` / `CGRequestListenEventAccess`）の判定・要求（本文で触れるだけ・§5.2）
- 権限の自動の再確認・フックの自動の再開
- 前面の判定・`repeat_timing`・クリック透過・NSWindow（task_11）
- ビルド後の `.app` の権限（task_13）

## 確認

Mac（verifier）: compile clean・`tests` が基準線（失敗 6・エラー 10）から増えない・smoke pass・tests_ui は触れたモジュールに関係するものを 1 本ずつ。
- tests（Tk なし・Quartz / ApplicationServices は注入 / 偽物）: 権限なしで `start()` が tap を作らずに権限不足の例外・`CGEventTapCreate` が NULL で同じ例外・disabled を受けて権限があれば再有効化 / 無ければ障害の通知（1 回だけ）・再有効化で有効にならなければ通知・run loop の例外で通知・`hook_coordinator` が権限不足の例外で権限の案内の文言を渡す・Windows の backend の新しい口が True / False を返し通知を呼ばない。
- tests_ui（必要なら）: 実行中の障害の通知でフックが止まり通知が 1 回出る（`_handle_overload` のテストの流儀）。
Windows: task_09〜09f の Windows 検証と合わせて（新しい口が Windows の動作を変えないこと）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。`codebase_map.md` の backend の口・hook_controller の通知の行を追従（メイン）。
- 実機目視（Mac・本タスクで実施）:
  1. 開発実行の python / ターミナルのアクセシビリティを外して「フック開始」→ 権限の案内が出る・「システム設定を開く」でアクセシビリティの画面が開く。
  2. 許可して同じプロセスで「フック開始」を再度押す → 開始できるか（できなければ再起動で開始できるか）。結果を暫定 57 §5.2 に記録する。
  3. フックの稼働中にアクセシビリティを外す → フックが止まり案内が 1 回出る・キー入力が素通しになる（止まらない場合は報告）。

## 起票レビュー（reviewer「修正して採用」2026-11-15）の反映 — 上の対象範囲に優先する

- **H1（既存の不具合・ユーザー判断「両 OS で直す」）**: `HookCoordinator.install_input_event_hook` が `register_global_hook` の例外を内側で受けて `install_failed` を出し、`start()` は True を返すため、登録に失敗しても `hook_active = True`（稼働中の表示）になる（`hook_coordinator.py:31-33,66-77`・`hook_controller.py:160-173`）。→ 登録に失敗したら `start()` が False を返し、稼働中にしない（Windows・Mac とも）。`install_failed` の文言は今のまま（権限不足は下の H2・M2）。上の「今の `start_failed` ではなく」は「今の `install_failed` ではなく」と読み替える。task_08b の定義の「`start_hook` の失敗経路に乗る」も、本タスクで成り立つ。
- **H2（権限不足の見分け方）**: Mac の backend は権限不足（`AXIsProcessTrusted` が偽・`CGEventTapCreate` が NULL）で標準の `PermissionError`（またはその派生を `macos/` 内に定義）を出す。application は `PermissionError` で見分け、`macos` / infrastructure の具象を import しない（完了条件に含める）。Windows の `keyboard` の失敗（`OSError` 等）は `PermissionError` 以外として今の `install_failed` の経路。
- **M1（経路の層）**: 実行中の障害の通知は `KeyboardBackend.set_hook_failure_listener(callback | None)`（Windows は保持するだけで呼ばない）→ `InputGateway.set_hook_failure_listener` / `input_permission_granted` / `open_input_permission_settings`（同名の口・presentation は gateway 経由）。`register_global_hook` の署名は変えない。`HookController.start_hook` が開始の前に listener を設定し、停止で外す。
- **M2（案内の出し方）**: `HookCoordinator.start(..., on_permission_required: Callable[[], None] | None = None)` を足し、権限不足のときは `on_error` の代わりにこれを呼ぶ（None なら今の `on_error`）。`HookController` は `askyesno` 等で「システム設定を開く」を選べるダイアログを UI スレッドで出す。実行中の障害も、権限が無ければ同じダイアログ、あれば別の通知。
- **M3（スレッド）**: 障害の通知は `EventTap` のロック（`self._lock`）の外で呼ぶ。listener の例外はログに残して握りつぶさない（素通しは続ける）。「1 回の稼働につき 1 回」の印は `start()` で戻す。
- **L1**: 新しい文言キーは過負荷（`hook.overload.*`・`ja.json:173` 付近）と別にする（例 `application.hook.permission_required_title` / `_body`・`hook.tap_failure.title` / `.body`）。読むファイルに `ja.json:165-180`・`en.json:165-180` を足す。
- **L3**: 確認に「Windows の backend で `register_global_hook` が従来どおり動く（listener 未設定・設定済みのどちらでも）」と「登録に失敗したとき `start()` が False・`hook_active` が偽のまま」を足す。
