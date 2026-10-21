# task_02_capture_hook

## 目的

暫定 49 v0.4 §3-1〜§3-6・§3-8 の「取得用のフック」と、§3-6・§3-7 の受け渡しの口（`begin_key_capture` の `on_hook_key`・世代・渡し先）を作り、`App` で設定する。
**presentation 限定（新モジュール 1 つ + `key_capture_ime.py` + `app.py` の配線）・domain / application / infrastructure は不変（既存の口を使うだけ）・スキーマ不変。8 入口の受け取りは task_03（本タスクでは入口は `on_hook_key` を渡さないので、名前は渡し先が無く捨てられる）。**

## 対象範囲（presentation 限定）

### 新規 `keyseq/presentation/key_capture_hook.py`: `KeyCaptureHook`

- コンストラクタは呼び出し可能な値だけを受け取る（infrastructure を import しない）:
  `register_hook(callback) -> handle`（`suppress=True` の登録）/ `unregister_hook(handle)` / `resolve_name(scan_code) -> str`（レイアウトの名前・無ければ空）/ `numpad_name(scan_code, is_keypad) -> str | None` / `is_foreground() -> bool` / `after(ms, func)` / `repeat_delay_ms() -> int` / `clock() -> float`（秒・既定 `time.monotonic`）/ `deliver(name, generation)`（UI スレッドで呼ばれる受け渡し先）/ `get_generation() -> int`
- `activate()`（UI スレッド・owner が 0 → 1）: 登録が無ければ `register_hook` で登録（あれば使い回す・§3-1）。余韻の確認を止める
- `deactivate()`（UI スレッド・owner が 1 → 0）: 押下中（§3-4）が無ければすぐ外す。あれば余韻（§3-5）に入り、`after` で 100 ms ごとに確認し、押下中が無くなった・または deactivate から 5 秒たったら外す（その間に activate されたら余韻をやめて登録を残す）
- `shutdown()`: 余韻を含めて即座に外す（`App.on_close` から）
- フックの callback（フックのスレッド・**Tk を触らない**・例外は吸収して True）:
  1. `event_type` が down / up 以外は True
  2. 対象の判定（§3-2 の順）: `is_foreground()` が偽 → True / `numpad_name(scan_code, is_keypad)` が名前を返す → True / `resolve_name(scan_code)` が空 → True / 名前が `esc` か `domain.key_hold.MODIFIER_KEY_NAMES` に含まれる（`is_modifier_key` で判定してよい）→ True
  3. 対象なら: 押下中の表（走査コード → 最後の押下の時刻）をロックの下で更新する。down で、表に無い・または最後の押下から一定時間（`repeat_delay_ms() + 200` ms）を超えていれば「新しい押下」→ 表を更新し、**活性中（owner > 0）のときだけ** `after(0, lambda: deliver(name, generation))` で渡す（`generation` は callback の中で `get_generation()` を読んだ値）。一定時間以内なら表の時刻だけ更新して渡さない。up は表を変えない（§3-4・離しでは外さない）。`after` が例外なら捨てる。いずれも **False を返して抑止**
  4. 余韻の間（owner = 0）は、押下中の表にある走査コードのイベントだけ抑止し（False・表の時刻は更新する）、それ以外は True（受け渡しはしない）
- 押下中の表の項目は、最後の押下から一定時間を超えたら「押下中でない」とみなす（読むときに時刻で判定してよい）

### `keyseq/presentation/key_capture_ime.py`

- `KeyCaptureImeTracker.begin(owner, window, on_hook_key=None)`: `on_hook_key`（`Callable[[str], None] | None`）を owner の記録に持つ。**begin の呼び出しのたびに世代を 1 進める**（取得中の owner の再度の開始も含む。再度の開始では IME に触らない既存の挙動は不変・`on_hook_key` が渡されていれば差し替え・「最後に開始した」の順を最後へ）
- `end(owner)`: 実際に終わったとき（owner が記録にあった）だけ世代を 1 進める
- owner が 0 → 1 / 1 → 0 になったら、設定された取得用のフック（`set_capture_hook(hook)` で設定・既定 None）の `activate()` / `deactivate()` を呼ぶ。None なら何もしない
- `generation`（読み取り）と `deliver(name, generation)`（UI スレッド）: 世代が違えば捨てる。取得中の owner の窓のどれかから `focus_get()` を取り（例外・None なら捨てる）、その `winfo_toplevel()` と owner の窓の `winfo_toplevel()` が一致する owner のうち最後に開始したもので、`on_hook_key` があるものへ名前を渡す。無ければ捨てる。`on_hook_key` の例外は吸収してログ
- モジュール関数: `begin_key_capture(owner, window, on_hook_key=None)` / 既存の `end_key_capture` / 新規 `configure_capture_hook(hook)`（既定の tracker に設定）/ `shutdown_capture_hook()`（設定済みなら `shutdown()`）

### `keyseq/presentation/app.py`

- `self.layout` を作った後で `KeyCaptureHook` を作り `configure_capture_hook` する: `register_hook=lambda cb: self.input_gateway.register_global_hook(cb, suppress=True)` / `unregister_hook=self.input_gateway.unregister_hook` / `resolve_name=self.layout.resolve_key_name_from_scan_code` / `numpad_name=numpad_name_from_event` / `is_foreground=is_own_process_foreground` / `after=self.after` / `repeat_delay_ms=lambda: keyboard_repeat_timing()[0]` / `deliver` と `get_generation` は既定の tracker のもの
- `on_close` の終了処理で `shutdown_capture_hook()` を呼ぶ（例外は吸収・既存の finally の連鎖を壊さない）

### テスト（tests・偽の値だけで・本物のフックを入れない）

- 新規 `tests/test_key_capture_hook.py`: 登録 / 使い回し / 解除・対象の判定の順（前面でない・テンキー・名前なし・esc・修飾キーは True）・対象は down / up とも False・新しい押下だけ渡す（一定時間以内の押下・up の後の押下は渡さない・一定時間の後は渡す）・活性中でないときは渡さない・余韻（押下中のキーだけ抑止・押下中が無くなったら外す・5 秒で外す・余韻中の activate で残す）・`after` の例外・callback の例外で True・shutdown
- `tests/test_key_capture_ime.py` に追加: 世代（begin のたび・再度の開始・実際の end だけ）・activate / deactivate の呼び出し（0 → 1・1 → 0・重複は呼ばない）・deliver（世代違い・フォーカスの窓の一致・最後に開始したもの・`on_hook_key` 無し・focus_get の例外で捨てる）

## 読むファイル

1. `instructions/history/49_capture_jis_special_keys.md`（§3・§5）
2. `keyseq/presentation/key_capture_ime.py`（全体）
3. `keyseq/presentation/app.py:80-90`（import）・`:136-150`・`:196-210`（`keyboard_repeat_timing` の使い方）・`:255-265`（`self.layout`）・`:737-771`（`on_close`）
4. `keyseq/presentation/controllers/hook_controller.py:294-315`（フックのスレッドから `after(0)` の手本）
5. `keyseq/infrastructure/input_gateway.py:256-262`（`register_global_hook`）・`keyseq/domain/numpad_keys.py:30-45`・`keyseq/domain/key_hold.py:10-95`（`MODIFIER_KEY_NAMES` / `is_modifier_key`）
6. `tests/test_key_capture_ime.py`（偽の窓の手本）

## 含まない

- 8 入口が `on_hook_key` を渡す・受け取った名前の記録（task_03）
- 正本の更新（task_04）

## 確認

- `compileall` clean / `unittest discover -s tests` 全 pass（新規分を含む）/ `unittest discover -s tests_ui` 全 pass（既存の 1122 件・tests_ui は tracker を差し替えるので本物のフックは入らない）/ smoke pass
- 差分の直読み: フックのスレッドの callback が Tk・`after` 以外の UI を触らない / 素通しはすべて True を明示 / application・infrastructure・domain の変更が無い

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視: task_04 でまとめて実施。
