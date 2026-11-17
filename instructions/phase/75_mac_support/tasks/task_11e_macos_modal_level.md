# task_11e_macos_modal_level

## 目的

aqua（Tk 9.1）で、メイン（やキーボードUI）が最前面のとき、モーダルのダイアログがクリックでその後ろへ回らないようにする。暫定 57 §5.4 の表の「最前面とモーダル」の行（**v0.18・ユーザー承認が前提**）に従う。

- 変更は infrastructure（`os_backend` の契約・Windows / macOS の backend）と presentation の `modal.py` の呼び出し 1 か所。domain / application は変えない。Windows の動作は変えない。

## 原因（メイン実測・2026-11-17）

- メインに `-topmost` を付けるとレベルは 19。`grab_modal` で開くダイアログ（transient）は、NSWindow の子の窓としてつながったときにレベル 19 を受け継ぐ。
- **grab を持つダイアログの中をクリックすると、Tk がダイアログのレベルを 0 に戻す**。記録のボタンに限らず、何もしないボタンや余白でも起きる。素の Tk でも起きる（transient だけなら起きない・transient + `grab_set` で起きる）。ダイアログはメイン（19）の後ろへ回る。
- ダイアログに `-topmost` を付けても直らない（transient の窓は付けた時点でレベル 0 になる）。
- クリック・フォーカスの後に `after(0)` でダイアログのレベルを親の NSWindow と同じにすると、保たれる。メインをクリックしてもダイアログが手前に残る（実測）。
- 「未保存があります」など `parent` なしの messagebox がメインの後ろに出る件は別の原因（アプリ全体のアラート = レベル 8）で、task_11f が扱う。

## 対象範囲

### `keyseq/infrastructure/os_backend/contracts.py`

- `WindowBackend` に `keep_level_with_parent(self, window: tkinter.Misc) -> bool: ...` を足す（docstring: 窓のレベルを transient の親に合わせ続ける。不要な OS は何もせず True・例外を出さない）。

### `keyseq/infrastructure/os_backend/windows/backend.py`

- 何もせず True。

### `keyseq/infrastructure/os_backend/macos/backend.py`（`MacWindowBackend`）

- `keep_level_with_parent(window)`: `window.bind(seq, handler, add="+")` を `"<ButtonPress>"`・`"<ButtonRelease>"`・`"<FocusIn>"`・`"<Map>"` に登録して True。登録の失敗は False（ログ 1 回）。
- handler は `event.widget` が窓自身か子孫のどれでも `window.after(0, reapply)` を予約する（同じ窓で予約が残っていれば足さない・id を保持）。
- `reapply`: `native = ns_window_for(window)`、親 = `native.parentWindow()`。どちらかが None なら何もしない。`native.level() < parent.level()` のときだけ `native.setLevel_(parent.level())`。例外は握ってログ 1 回（`_..._failure_logged` の流儀）。窓が破棄済み（`winfo_exists()` が偽・`TclError`）なら何もしない。
- 下げる方向には触らない（親の最前面が外れたら、Tk が子の窓をつなぎ直すときに受け継ぐレベルに任せる）。

### `keyseq/presentation/modal.py`

- `grab_modal` で、`disable_minimize_button(window)` の隣で `get_backend().window.keep_level_with_parent(window)` を呼ぶ（戻り値は使わない）。

### 設計メモ / 制約

- 親は Tk の transient の主ではなく **NSWindow の `parentWindow()`**（Tk が子の窓としてつないだ相手）を使う。つながっていないとき（最小化の直前に外した後など・task_11c）は何もしない。
- 実測の probe: クリックの後 `after(0)` で親と同じレベルにすると、ダイアログのクリック・メインのクリックの後もダイアログが手前。
- キーボードUIが最前面のときの「取得」の件（キーボードUIから開いたダイアログが後ろへ回る）も同じ原因の見込み。本タスクの目視で確かめ、直らなければ報告して止める（キーボードUIの最前面の監視 `layout_controller.py:160-190` との関わりを調べる）。

## 読むファイル

- `keyseq/infrastructure/os_backend/contracts.py:90-130`（`WindowBackend`）
- `keyseq/infrastructure/os_backend/macos/backend.py`（`MacWindowBackend`・`disable_minimize_button` / `order_out` / `_reapply_overlay_click_through` の流儀）
- `keyseq/infrastructure/os_backend/windows/backend.py:40-60`
- `keyseq/presentation/modal.py`（`grab_modal`）
- `tests/test_macos_window_backend.py`・`tests/test_os_backend_contracts.py`（偽物の作り方）
- `instructions/history/57_mac_support.md` §5.4 の表（v0.18 で足す行）

## 含まない

- `parent` なしの messagebox がメインの後ろに出る件（「未保存があります」など 162 か所）→ task_11f
- 割り当て禁止の文言 → task_11d
- ダイアログを開いたままメインを閉じられる件 → idea_59

## 確認

- Mac（`../../../.venv/bin/python`）: `-m compileall -q keyseq tests tests_ui` が clean / `-m unittest discover -s tests` が基準線どおり（2119 件前後・失敗 1〔`test_third_party`〕）/ tests_ui を 1 本ずつ（`test_modal_grab`・`test_minimize_grab_custody`・`test_modal_app_foreground`・`test_app_ui_flows`・`test_help_window`・`test_task06_keymap_management_ui`）が失敗 0 / `-m tests.smoke_app` が pass。
- テストを足す:
  - `tests/test_os_backend_contracts.py`: 署名・Windows は True。
  - `tests/test_macos_window_backend.py`（Tk なし・偽の窓と NSWindow）: 4 つの bind が `add="+"` で登録される / handler が `after(0, ...)` を 1 つだけ予約する / reapply が親のレベルより低いときだけ `setLevel_(親のレベル)` / 親が None・窓が破棄済み・例外で送出しない / 登録の失敗で False。
  - `tests_ui/test_modal_grab.py`: `grab_modal` が backend の `keep_level_with_parent` を窓を渡して呼ぶ（backend を patch）。
- Windows: task_09〜11e の Windows 検証で、契約のテストと `test_modal_grab` が失敗 0。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視（Mac・本タスクで実施）:
  1. メインの「最前面に表示」をオンにしてトリガーの追加ダイアログを開き、ダイアログの中（記録のボタン・余白）をクリックしても、ダイアログがメインの前にある。キーの記録を始めても前にある。
  2. 同じ状態でメインをクリックしても、ダイアログがメインの前にある。
  3. 「キーボードUIを最前面に表示」をオンにし、キーボードUIからダイアログを開いて「取得」を押しても、ダイアログがメインとキーボードUIの前にある（NG なら報告して止める）。
  4. 最前面がオフのときの動作が今までどおり（ダイアログが前・task_11c の最小化が OK）。
- `codebase_map.md` の modal / macOS backend の記述を追従する（メイン）。

## 起票レビュー（reviewer「修正して採用」2026-11-17）の反映 — 上の記述に優先する

- **M1**: 暫定 57 v0.18 の行（§5.4・「最小化とモーダル」の次）と版の履歴をユーザー承認の後に足してから着手する。
- **M2（子孫のイベント）**: `window.bind` は Toplevel のバインドタグなので子孫のクリック・フォーカス・Map も届く。ダイアログ内のどこをクリックしても Tk がレベルを戻すので、`event.widget` で絞らない。予約は 1 窓につき最大 1 つ・reapply は `level()` の比較だけで、`setLevel_` は低いときだけ。
- **M3（予約の id）**: `self._level_reapply_ids: dict[object, str]`（キー = Tk の窓オブジェクト・`str(window)` は使わない）。reapply の先頭（`finally`）で pop・`winfo_exists()` が偽なら pop して何もしない。登録済みの窓（`self._level_windows` などで同一性を記録）に再度呼ばれたら何もせず True（冪等）。テスト: 予約が残っている間は 2 回目の handler が `after` を呼ばない / reapply の後は再び予約できる / 二重の `keep_level_with_parent` で bind が増えない。
- **M4（最小化から戻した後）**: 完了条件の目視に足す: 最前面オンで、ダイアログを開いたままメインを最小化して戻しても、ダイアログが前にある（task_11c との組み合わせ）。NG なら報告して止める。
- **M5（キーボードUIの「取得」）**: 読むファイルを `keyseq/presentation/controllers/layout_controller.py:158-190`（`_watch_topmost_tick`・grab があればキーボードUIの最前面を外す `:179-186`）に訂正して足す。「取得」で開くダイアログの transient の親（メインかキーボードUIか）を、実装の前にメインが確かめて報告に書く。目視 3 が NG なら報告して止める。
- **M6（入れ子）**: 目視に足す: トリガーの追加ダイアログ → その中から開くダイアログ（例: プリセット管理）でも、内側のダイアログの中をクリックした後、両方がメインの前にある。
- **L1〜L5**: bind は `add="+"`（キーワード）で可。ログのフラグは `_level_reapply_failure_logged`（reapply / handler）と `_level_bind_failure_logged`（登録）。handler も `try/except Exception` でログ 1 回にし、Tk のコールバックから例外を出さない。テストの偽の NSWindow（`level()` / `parentWindow()` / `setLevel_`）は別に作る。読むファイルに `keyseq/infrastructure/os_backend/macos/ns_window.py` を足す。`grab_modal` は初期化の最後に呼ばれる前提（`modal.py` の docstring）。
- **L6（Windows）**: Windows 検証は `keep_level_with_parent` が True を返す単体テストと `test_modal_grab` が失敗 0（実機目視は不要）。
- **M5 の確認（メイン・2026-11-17）**: 「取得」はアクションの編集ダイアログ（トリガーの追加ダイアログ）のマウスの位置の取得（`action_dialog.py:398-420`・`get_backend().mouse.capture_next_click`）で、ダイアログを開くのはメイン（`ActionDialog(app, ...)`・transient の親 = App）。押した時点のダイアログの中のクリックでレベルが 0 に戻るのは同じ原因なので、本タスクで直る見込み。目視 3 で確かめる。

## 改訂（実装後の実測・2026-11-17）— 上の記述に優先する

- 実際の App で本物のクリックを送ると、レベルはまだ 0 に戻った。記録: クリックを離した後に 19 → 8（こちらのかけ直しで 19）→ ダイアログの描き直し（`<Expose>`）の直前に 0。見張るイベントに `"<Expose>"` を足すと、ダイアログの中・記録のボタン・メインのクリックの後もレベル 19 でダイアログが前（実測）。
- `keep_level_with_parent` の bind に `"<Expose>"` を足す（5 つ）。予約は今どおり 1 窓につき 1 つ（Expose は子ごとに多数届くが、予約が残っていれば足さない）。テストの期待も 5 つに直す。

## 改訂 2（Mac 目視・ユーザー判断 B 2026-11-17）— 上の記述に優先する

- **目視の結果**: 最前面オンで何度もクリックすると、ダイアログがメインの後ろへ回る（ちらつき・たまに安定）。キーボードUIより前には来る（OK）。エラーダイアログ（messagebox）がキーボードUIの後ろになることがある → task_11f。
- **比較（メイン実測・本物のクリック 12 回・ダイアログの中 / 記録のボタン / メインを順に）**: 今の `keep_level_with_parent` = 12 回とも後ろ・run loop の待ちの前で揃える = 1 回後ろ・**モーダルの間はメインの最前面を外す = 0 回**（ちらつきなし）。
- **直し方（暫定 57 v0.18 の改訂後の行）**:
  - `keep_level_with_parent` を取り除く（契約・Windows / macOS の実装・`modal.py` の呼び出し・テスト）。
  - `WindowBackend` に `releases_topmost_during_modal(self) -> bool` を足す（Windows = False・macOS = True）。
  - `modal.py` に、台帳（`_active_modals`）が空 ↔ 空でないに変わったときに呼ぶ通知の口を足す（例: `set_modal_presence_listener(callback)`・登録は 1 つ・`grab_modal` で台帳に積んだ後と `restore_grab` で台帳から外した後に、空かどうかが変わったときだけ呼ぶ・例外は握ってログ）。`is_modal_active()` も足す。
  - `App` は起動時に `modal.set_modal_presence_listener(self._apply_always_on_top)` を登録し、`_apply_always_on_top` が使う最前面の値を「チェック and not (`is_modal_active()` and backend の `releases_topmost_during_modal()`)」にする。ヘルプ・ライセンスの窓（`help.apply_topmost`・`license.apply_topmost`）も同じ値を使う（それぞれが変数を直接読んでいるなら、App の有効値を読む形にする）。キーボードUIの最前面の監視（`layout_controller.py`）は変えない。
- **テスト**: `tests/test_os_backend_contracts.py`（署名・Windows は False〔Windows でだけ走らせる〕）/ `tests/test_macos_window_backend.py`（True）/ `tests_ui/test_modal_grab.py`（台帳が空 ↔ 空でないで通知が 1 回ずつ・入れ子では最初と最後だけ）/ tests_ui の App のテスト 1 件（backend の `releases_topmost_during_modal` を True に patch し、最前面オンでモーダルを開くとメインの `-topmost` が外れ、閉じると戻る。False では外れない）。
- **目視（やり直し）**: 1〜6（最前面オンで何度クリックしてもダイアログがメインの前・ちらつかない・閉じるとメインが最前面に戻る・入れ子・最小化から戻した後・最前面オフ）。
- **完了（2026-11-17）**: verifier pass・reviewer 完了可（F1 = Windows でかけ直しを走らせない・F2 を反映）・Mac 目視 OK。
