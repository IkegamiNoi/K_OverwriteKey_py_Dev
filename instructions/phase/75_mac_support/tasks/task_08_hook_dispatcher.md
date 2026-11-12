# task_08_hook_dispatcher

## 目的

フックのコールバック（フックのスレッド）から UI スレッドへ処理を渡す**ディスパッチャ**を、暫定 57 §5.1.1（v0.7）の契約で作り、`HookController` と `KeyCaptureHook` をそれ経由に切り替える（段階 ① の区切り M1・M2）。
macOS 用のキュー版（上限・期限・世代・優先の経路）もここで作るが、CGEventTap 自体は task_08b。

- **presentation 限定**（+ `os_backend` の `OsBackend` に項目 1 つ）。domain・application・JSON スキーマは不変。
- **Windows は即時版（`after(0)`）で動作不変**。Windows で実装・テストできる。

## 対象範囲（presentation + `OsBackend` の項目追加）

### `keyseq/infrastructure/os_backend/contracts.py`・`windows/backend.py`・`macos/backend.py`

- `OsBackend` に `queued_hook_dispatch: bool = False` を足す（既定値つきで末尾へ。既存の位置引数を崩さない）。
- `macos/backend.py` の `create_backend()` は `queued_hook_dispatch=True`。Windows は既定の `False` のまま（明示してもよい）。

### `keyseq/presentation/hook_dispatcher.py`（新規）

暫定 57 §5.1.1 の 2 実装と生成関数。Tk を import しない（`after` と時計を受け取る）。

- `HookDispatcher`（Protocol）: `dispatch(run, *, on_discard=None, priority=False) -> bool` / `invalidate() -> None` / `close() -> None`。
- `ImmediateHookDispatcher(after)`: `after(0, run)`。常に `True`。`on_discard` は呼ばない・`priority` は無視・`invalidate()` / `close()` は何もしない。
- `QueuedHookDispatcher(after, clock=time.monotonic, *, limit=64, ttl_s=1.0, interval_ms=10)`:
  - `queue.SimpleQueue` を通常用・優先用の 2 本。通常用の要素は `(run, on_discard, 積んだ時刻, 世代)`。通常用の件数は自前のカウンタ（ロックつき）で数え、`limit` に達していたら `False` を返して積まない。優先用は数えない・捨てない。
  - `dispatch` はどのスレッドからでも呼べる。**`dispatch` の中で `after` を呼ばない**（Tk を呼ばない）。
  - 排出（UI スレッド）: `start()` で `after(interval_ms, 排出)` を始め、排出の最後に次を予約する。排出は優先用を空になるまで処理してから、**排出開始時点の通常用の件数分**を処理する。通常用は、世代が違えば何も呼ばずに捨て、積んだ時刻から `ttl_s` を超えていれば `on_discard`（あれば）を呼んで捨て、それ以外は `run` を呼ぶ（世代の判定が先）。
  - `invalidate()`: 世代を 1 進める（ロックつき）。
  - `close()`: 以後の排出の予約をやめる（`after` の戻り値の取り消しは任意。予約済みの排出が来たら何もせず戻る）。
  - `run` / `on_discard` の例外は `logging` で残して吸収し、排出を続ける。`after` の予約の例外も吸収してログに残す。
- `create_hook_dispatcher(after, *, queued: bool) -> HookDispatcher`: `queued` ならキュー版を作って `start()` し、そうでなければ即時版。

### `keyseq/presentation/app.py`

- `backend.queued_hook_dispatch` で `create_hook_dispatcher(self.after, queued=…)` を 1 つ作り、`self.hook_dispatcher` に置く。`KeyCaptureHook(...)` の生成（295 行付近）より前に作る。
- `KeyCaptureHook(...)` に `dispatch=self.hook_dispatcher.dispatch` を渡す（`after=self.after` は待ちの確認用に残す）。
- `HookController(self, dispatch=self.hook_dispatcher)` を渡す（316 行付近）。
- `on_close` で `self.hook.begin_shutdown()` の後に `self.hook_dispatcher.close()`（例外は吸収）。

### `keyseq/presentation/controllers/hook_controller.py`

- 引数 `dispatch` の型を `HookDispatcher | None` に改める。`None` のときは `ImmediateHookDispatcher(app.after)`（既存のテストの `HookController(app)` が従来どおり動く）。
  既存のテストが `dispatch=` に**関数**を渡している箇所（`tests/test_hook_coordinator.py:76` 付近）は、テスト側を新しい型に合わせて直す（件数を減らさない）。
- 状態を 3 つ足す（フックのスレッドから読み書きするため、単純な int / `threading.Event` で持つ）:
  - **フックの稼働番号**: `start_hook` で登録に成功する前に 1 進める。
  - **切替の予約番号**: `SelectKeymapAction` を渡すたびに 1 進める。
  - **過負荷の印**: `start_hook` の先頭で下ろす。
- `on_input_event`:
  - 先頭で過負荷の印が立っていれば `True`（素通し）を返し、`make_only_keys` にも `input_router` にも渡さない。
  - 各アクションの渡し方（`_schedule_make_only_routes` も同じ規則）:
    - `SelectKeymapAction` = `on_discard` に「渡した時点の予約番号が現在と同じときだけ `_clear_keymap_switch_in_progress()`」。
    - `StopHookAction` = `priority=True`。`run` は渡した時点の稼働番号を持ち、実行時に番号が変わっていれば何もしない。
    - その他 = 従来どおり（`on_discard` なし）。
  - `dispatch` が `False` を返したら: 過負荷の印を立て、同じイベントの残りのアクションは渡さず、そのイベントは `True`（素通し）を返す。フックの停止を `priority=True` で **1 回だけ**渡す（印を立てた呼び出しだけが渡す）。停止の `run` は稼働番号を確かめ、一致すれば `stop_hook()` の後に知らせ（下記）を出す。
  - `_schedule_make_only_routes`（タイマーからの経路）で `False` が返ったときも同じ扱い（素通しを返す相手は無いので、印と停止だけ）。
- `stop_hook`: 既存の処理に `invalidate()` を加える（`_clear_keymap_switch_in_progress()` の直後）。
- 知らせ: 過負荷で止めたことを `messagebox.showwarning` で出す。文言キーは `hook.overload.title` / `hook.overload.body`（`ja.json` と `en.json` の両方。表記は `instructions/common/spec_detail/ui_terms.md` に従う。例: 「入力の処理が追いつかないため、フックを停止しました。」）。

### `keyseq/presentation/key_capture_hook.py`

- 引数 `dispatch: Callable[..., bool]` を足す（`after` は待ちの確認用に残す）。
- `_queue_delivery` は `self._dispatch(lambda: self._deliver(name, generation))` に替え、戻り値を `_handle_event` へ返す。
- **素通し中**の記録（走査コードの集合）を足す（暫定 57 §5.1.1）:
  - `dispatch` が `False` を返した down は、`_pressed` に**残さず**素通し中に入れ、`True`（抑止しない）を返す。
  - 素通し中の走査コードのイベントは、取得の有無にかかわらず `True` を返す。その up で素通し中から外す。
  - `deactivate()` と待ちの確認（`_check_idle`）は、素通し中のキーも押下中と同じに数えてフックを残す（上限は既存の 5 秒）。
  - 素通し中を消すのは、その up とフックを実際に解除したとき（`_unregister_locked`・`shutdown`）だけ。
- 即時版では `dispatch` が常に `True` なので、従来と同じ動作になる。

### テスト

- `tests/test_hook_dispatcher.py`（新規・偽の `after` と時計で）: 即時版（`after(0)`・常に `True`・`on_discard` を呼ばない）/ キュー版（上限 64 で `False`・優先は上限外・優先が先に実行・期限切れで `on_discard`・世代違いは何も呼ばない・`run` の例外を吸収して続く・`close()` 後は排出しない・`dispatch` が `after` を呼ばない）。
- `tests/test_hook_coordinator.py`（`HookController`）: `SelectKeymapAction` の `on_discard` は予約番号が一致するときだけ印を下ろす（予約 A → 印を下ろす → 予約 B → A の期限切れで B の印が残る）/ `StopHookAction` は `priority=True` で、再開後（稼働番号が違う）は何もしない / `dispatch` が `False` → 素通し・過負荷の印・停止は 1 回だけ・印の間は `input_router` を呼ばない・`start_hook` で印が下りる / `stop_hook` が `invalidate()` を呼ぶ / 引数なしは即時版。
- `tests/test_key_capture_hook.py`: `dispatch` が `False` の down は素通しで `_pressed` に残らない / 同じキーのリピートの down と up も素通し・up で外れる / 素通し中のキーがある間は `deactivate()` でフックを外さない / 解除で素通し中が消える / `True` のときの既存の動作は不変。
- `tests/test_os_backend_contracts.py`: `queued_hook_dispatch` が Windows `False`・macOS `True`。

## 読むファイル

- `instructions/history/57_mac_support.md` §5.1（127〜149 行付近）・§5.1.1
- `keyseq/presentation/controllers/hook_controller.py`（全体）
- `keyseq/presentation/key_capture_hook.py`（全体）
- `keyseq/presentation/app.py:104-120`・`:180-240`・`:290-320`・`:879-900`
- `keyseq/infrastructure/os_backend/contracts.py:105-125`・`macos/backend.py`・`windows/backend.py:85-100`
- `keyseq/application/input_router.py:10-50`（アクションの型）・`:110-130`（切替の印）
- `tests/test_hook_coordinator.py`・`tests/test_key_capture_hook.py`（既存の書き方）
- `keyseq/shared/i18n/locales/ja.json` / `en.json` の `hook.send_error.*` 付近・`instructions/common/spec_detail/ui_terms.md`（文言の表記）

## 含まない

- CGEventTap・修飾キー・tap の障害と権限の喪失からの停止・§4.1 の未実測の実測（task_08b）。
- vk の表・キーの識別・送信（task_09）。権限の案内（task_10）。
- `application/action_executor.py` の切替の実行完了時の印の解除（従来どおり・暫定 57 §5.1）。
- `HeldInputs` の `on_change` などフックの経路以外の `after` の置き換え。
- `hook_controller.py` の分割（404 行。増分が大きくなる場合は報告のみ）。

## 確認

Windows（`.venv\Scripts\python.exe`。verifier が実行）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_hook_dispatcher tests.test_hook_coordinator tests.test_key_capture_hook tests.test_os_backend_contracts` が失敗 0
- `-m unittest discover -s tests` が失敗 0・エラー 0（件数は 1997 + 追加分）
- `-m unittest discover -s tests_ui` が失敗 0・エラー 0（1271 件以上）
- `-m tests.smoke_app` が pass

Mac（次に Mac を使うとき・task_08b の前）: `tests` が基準線（失敗 6・エラー 10）から増えない・smoke pass。

## 完了条件

- 上記の Windows の確認 pass・**reviewer 採用**。
- 実機目視（Windows）: キー置換・シーケンス・停止キー・キーマップの切替・キーの取得が従来どおり（ユーザー）。Mac のキュー版の実機での動作は task_08b でまとめて確認する。
- `instructions/common/codebase_map.md` の `hook_controller.py`・`key_capture_hook.py`・os_backend 節に追従（メイン）。
