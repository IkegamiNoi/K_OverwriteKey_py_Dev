# task_11c_macos_minimize_grab_custody

## 目的

aqua（Tk 9.1）で、App の最小化中にモーダルの grab を預かる処理（`install_minimize_grab_custody`）が働くようにする。暫定 57 §5.4 の表の「最小化とモーダル」の行（**v0.17・ユーザー承認が前提**）に従う。`test_modal_grab` の 4 件と `test_minimize_grab_custody` の失敗（`mac_test_baseline.md`）を解消する。

- **presentation 限定**（`keyseq/presentation/modal.py`）。domain / application / infrastructure は変えない。OS の判定はしない（Windows でも同じコードが走り、Windows の結果は変わらない）。

## 原因（メイン実測・Tk 9.1 aqua・2026-11-16）

1. **順序**: `iconify()` の中で App の `<Unmap>` が先に届き、その時点で transient の子はまだ表示中（`winfo_viewable()` = 1）。子が隠れるのは `iconify()` から戻った後（`after(0)` の時点では 0）。今の `take_custody`（`modal.py:47-66`）は「保持者が非表示なら預かる」なので、`<Unmap>` の時点で判断すると預からない。
2. **入れ子**: aqua は App の直接の transient だけを隠す。孫（ダイアログを親にした transient）は最小化しても表示のまま。Windows は入れ子も隠れる（`test_minimize_grab_custody` は Windows で pass）。

## 対象範囲（presentation 限定・`modal.py` のみ）

### `keyseq/presentation/modal.py`

- `install_minimize_grab_custody` の `take_custody`:
  - `<Unmap>` では `_app_minimized = True` にして、預かる判断を `app.after(0, ...)` へ遅らせる（`event.widget is not app` は今どおり無視）。
  - 遅らせた処理: App がまだ最小化中（`_app_minimized` が真）のときだけ、次を順に行う。
    1. **隠し漏れの窓を隠す**: 台帳 `_active_modals` の窓のうち、存在して `winfo_viewable()` が真の窓を `withdraw()` し、新しいモジュール変数 `_hidden_by_minimize: list[tk.Toplevel]` に開いた順で記録する（Windows では既に隠れているので何もしない）。
    2. **預かり**: 今の `take_custody` の本体（保持者を引き、存在して非表示なら `grab_release()` して `_custody_window` に記録）をそのまま行う。
  - 遅らせた処理の前に `<Map>` が来た（`_app_minimized` が偽）なら何もしない。
- `return_custody`（`<Map>`）の先頭で、`_hidden_by_minimize` の窓を記録した順に `deiconify()` し（破棄済み・`TclError` は飛ばす）、リストを空にする。その後に今の処理（grab を戻す・`after_idle` でフォーカスを戻す）。
- `grab_modal` の `restore_grab`（窓の破棄）で、その窓を `_hidden_by_minimize` からも除く。
- 関数はおおむね 30 行以内（`.claude/rules/implementation.md`）。遅らせた処理は `install_minimize_grab_custody` の内側の関数か、モジュールの private 関数にする。

### 設計メモ / 制約

- 実測: `after(0)` の時点で直接の子は非表示・孫は表示のまま → `withdraw()` で非表示にでき、`<Map>` で `deiconify()` すると元どおり表示され grab の保持者も変わらない（メインの実測・2026-11-16）。
- `withdraw()` するのは台帳 `_active_modals` に載っている窓だけ（`grab_modal` で開いたモーダル）。台帳外の窓（ヘルプ・キーボードUI など）には触れない。
- `_hidden_by_minimize` に入れた窓をフォーカスの戻し（`_restore_modal_focus`）が見るのは今どおり `<Map>` の後の `after_idle`（`deiconify()` の後）。
- テストのための状態のリセット（`tests_ui` の setUp / tearDown が `modal._custody_window` などを戻している箇所）に、`_hidden_by_minimize` も足す。

## 読むファイル

- `keyseq/presentation/modal.py`（全体・編集対象）
- `tests_ui/test_modal_grab.py:1-60`（setUp と窓の作り方）・`:100-200`（失敗している 4 件）
- `tests_ui/test_minimize_grab_custody.py:40-135`（`_restore_app`・`_minimize`・a1・a2）
- `instructions/history/57_mac_support.md` §5.4 の表（v0.17 で足す行）
- `instructions/phase/75_mac_support/mac_test_baseline.md`（tests_ui の表の `test_minimize_grab_custody`・`test_modal_grab`）

## 含まない

- メイン / キーボードUIが最前面のときダイアログが後ろへ回る件（トリガーの追加ダイアログの記録開始・「取得」・「未保存があります」の確認）→ task_11e
- 割り当て禁止の文言 → task_11d
- 最小化の伝わり方そのものを OS ごとに変えること（backend の追加）。今回は台帳の窓だけを presentation で隠す

## 確認

- Mac（`../../../.venv/bin/python`）:
  - `-m compileall -q keyseq tests tests_ui` が clean
  - `-m unittest discover -s tests` が基準線どおり（2115 件前後・失敗 1〔`test_third_party`〕・エラー 0）
  - tests_ui を 1 本ずつ: `test_modal_grab`（失敗 4 → 0）・`test_minimize_grab_custody`（失敗 25 → 0。止まる場合は報告）・`test_modal_app_foreground`・`test_app_ui_flows`・`test_help_window` が失敗 0
  - `-m tests.smoke_app` が pass
- テストを足す（`tests_ui/test_modal_grab.py`）: 孫の transient（ダイアログを親にした `grab_modal` の窓）が最小化で非表示になり grab が預けられ、復帰で表示と grab が戻ること・遅らせた処理の前に `<Map>` が来たら何もしないこと。
- Windows: task_09〜11c の Windows 検証で `test_modal_grab`・`test_minimize_grab_custody` が今どおり失敗 0。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視（Mac・本タスクで実施）:
  1. トリガーの追加ダイアログ → その中からさらにダイアログ（例: プリセット管理 → 確認）を開いた状態でメインを最小化すると、全部のダイアログが隠れる。
  2. Dock から戻すと、ダイアログが元どおり表示され、いちばん内側のダイアログで操作（キー入力・クリック）でき、メインは操作できない。
  3. 内側のダイアログを閉じると、外側のダイアログが操作できる。
- `mac_test_baseline.md` の `test_modal_grab`・`test_minimize_grab_custody` の行を追従する（メイン）。`codebase_map.md` の modal の記述に「最小化で台帳の窓を隠す」を足す（メイン）。

## 起票レビュー（reviewer「修正して採用」2026-11-16）の反映 — 上の記述に優先する

- **H-1（隠す対象と条件を絞る）**: `grab_modal` は親なしでも呼ばれる（`welcome_window.py:35` = 初回起動で root を withdraw 中）。`root.withdraw()` でも `<Unmap>` が来て `_app_minimized` が真になる。
  - 遅らせた処理は `app.wm_state() == "iconic"` のときだけ行う（withdraw や偽の `<Unmap>` では何もしない）。
  - `withdraw()` するのは、台帳の窓のうち **`wm_transient()` の鎖をたどると app に届く窓**だけ（親なしの窓・台帳外の窓には触れない）。
- **M-1（保留の漏れ・二重）**: `<Unmap>` ごとの `after` の id を保持し、`<Map>` で `after_cancel` する。`<Unmap>` が続いても保留は 1 つ（既にあれば足さない）。`_custody_window is not None` の早期 return は遅らせた処理の側で行う。
- **M-2（テストの状態のリセット）**: `_hidden_by_minimize`（と保留の id の変数を作るならそれも）を `tests_ui/test_modal_grab.py:11-19` と `tests_ui/test_minimize_grab_custody.py:28-34` の setUp で `patch.object` する。
- **M-3（遅延と既存テスト）**: 既存テストは `iconify()` の後 `update()` 1 回で預かりを assert する（`test_modal_grab.py:100-128`・`:130-152`・`:184-204`・`test_minimize_grab_custody.py:76-82`）。`update()` 1 回で `after(0)` まで済むかを、実装の後に verifier の結果で確かめる（足りなければテストの `update()` を増やさず、メインへ報告）。a4（`test_minimize_grab_custody.py:151-169`）は直接の子が OS で隠れている前提で、`deiconify` / `lift` / `focus_force` が 0 回のままであること。
- **M-4（戻す順）**: `<Map>` の時点で直接の子が再表示済みでなく、孫の `deiconify()` が効かない場合に備え、記録した窓の `deiconify()` は `app.after_idle` で行ってよい（a2 で検出する）。その場合も grab を戻す処理はその後にする。
- **L-1（テスト）**: `test_modal_grab.py` に孫の窓を作るヘルパーを足す（`make_window` は root の直接の子だけ・`:30`）。破棄は内側から。「遅らせた処理の前に `<Map>`」は `event_generate("<Unmap>")` の後に update せず `event_generate("<Map>")` で書く。偽の `<Unmap>`（iconic でない）では台帳の窓を隠さないことも 1 件足す。
- **L-2（読むファイル）**: `keyseq/presentation/welcome/welcome_window.py:20-40`・`keyseq/presentation/app.py:376`（`install_minimize_grab_custody` の呼び出し）を足す。`tests_ui/test_minimize_grab_custody.py` は `:28-34`・`:40-135`・`:151-327`。

## 改訂（実装中の実測・ユーザー承認 2026-11-16）— 上の記述に優先する

- Mac は `<Map>` の時点で App の直接の子をまだ表示し直していない（`<Map>` の中・`after_idle` では非表示、`deiconify()` の後と `after(0)` では表示中）。`<Map>` の中で grab を戻すと保持者を見つけられず、預かりの記録だけが消える。
- `return_custody` は `_app_minimized = False` と保留の取り消しをした後、`after(0)` で戻す処理（記録した窓の再表示 → `_return_grab(app, shown)`）を予約する（id を保持・`<Unmap>` で `after_cancel`・二重に予約しない）。予約した処理は App が最小化中でない（`wm_state() != "iconic"`）ときだけ行う。暫定 57 v0.17 の行も同じに直した。

## 改訂 2（Mac 目視・ユーザー判断 A 2026-11-16）— 上の記述に優先する

- **目視の結果**: 2・3 は OK。1 は NG: 入れ子のダイアログを開いた状態で「最小化」すると、外側のダイアログ（プリセット管理 / トリガーの追加ダイアログ）が残る。
- **原因（メイン実測・実際の App のダイアログ）**: メインの最小化（`iconify()`・メインの NSWindow の `miniaturize_`）では全部隠れる。ダイアログ自身の最小化ボタンを押すと、その 1 枚だけが Dock へしまわれ、App は最小化されない（`wm_state` は normal）ので、ほかのダイアログが残り、預かりも走らない。Windows の transient には最小化ボタンが無い。
- **直し方（暫定 57 v0.17 の行に追記）**: `grab_modal` で開く窓は最小化ボタンを無効にする。
  - `keyseq/infrastructure/os_backend/contracts.py` の `WindowBackend` に `disable_minimize_button(self, window: tkinter.Misc) -> bool` を足す（無効にできた / 不要なら True・できなければ False）。
  - Windows（`windows/backend.py`）は何もせず True。
  - macOS（`macos/backend.py` の `MacWindowBackend`）は `window.attributes("-stylemask")` から `"miniaturizable"` を除いた列を `window.attributes("-stylemask", ...)` で設定し True。`TclError` などの例外は False（ログは 1 回・既存の `_..._failure_logged` と同じ流儀）。実測: 設定は withdraw → deiconify・`resizable` の後も保つ。
  - `keyseq/presentation/modal.py` の `grab_modal` で、grab を取る前に `get_backend().window.disable_minimize_button(window)` を呼ぶ（戻り値は使わない・例外は出ない契約）。
- **テスト**:
  - `tests/test_os_backend_contracts.py` の署名の検査に足す・Windows は True。
  - `tests/test_macos_window_backend.py` に 1 件（Tk なし・`attributes` の Mock）: `miniaturizable` を除いた列で設定・`TclError` で False。
  - `tests_ui/test_modal_grab.py` に 1 件: `grab_modal` が backend の `disable_minimize_button` を窓を渡して呼ぶ（backend を patch）。
- **目視（やり直し）**: ダイアログ（トリガーの追加・プリセット管理・確認）の黄色のボタンが押せない。メインの最小化で全部隠れ、戻すと元どおり（目視 1〜3）。

## 改訂 3（Mac 目視・2026-11-16）— 上の記述に優先する

- **目視の結果**: 1・3・4 は OK。2 は NG のまま（メインの黄色のボタンで、2 枚ならトリガーの追加ダイアログ、3 枚ならプリセット管理が残る）。
- **原因（メイン実測・実際の App のダイアログ・`performMiniaturize:` を run loop から）**: 遅らせた処理は正しく走り、残る窓を `withdraw()` して記録しているが、Tk の状態が withdrawn になっても NSWindow は `isVisible` が真のまま（メインのしまう動作の途中・400 ms 遅らせても同じ）。`withdraw()` の後に `orderOut_` を呼ぶと隠れ、メインを戻した後の `deiconify()` で再び表示される。
- **直し方**:
  - `WindowBackend` に `order_out(self, window: tkinter.Misc) -> bool` を足す。Windows は何もせず True。macOS は `ns_window_for(window)` が引ければ `orderOut_(None)` して True・引けない / 例外は False（ログ 1 回）。
  - `modal.py` の遅らせた処理で、窓を `withdraw()` した直後に `get_backend().window.order_out(window)` を呼ぶ。
- **テスト**: `tests/test_os_backend_contracts.py`（Windows は True）・`tests/test_macos_window_backend.py`（`orderOut_(None)`・None / 例外で False）・`tests_ui/test_modal_grab.py`（隠した窓ごとに `order_out` を呼ぶ・backend を patch）。
- **目視（やり直し）**: 目視 2（メインの黄色のボタンで、入れ子のダイアログが全部隠れる）と 3（戻すと元どおり）。

## 改訂 4（Mac 目視・2026-11-17）— 上の記述に優先する

- **目視の結果**: 2 枚（トリガーの追加 → プリセット管理）は全部隠れる（一瞬ちらつく）・戻すと元どおり = OK。3 枚（→ 確認）は、プリセット管理が残る。
- **原因（メイン実測・実際の確認ダイアログ）**: 遅らせた処理の時点で、プリセット管理は Tk が既に withdrawn にしている（`winfo_viewable` が偽）ので飛ばされるが、NSWindow は表示のまま。トリガーの追加と確認は、こちらが withdraw + `order_out` して隠れる。戻すと 3 枚とも Tk が表示し直す。
- **直し方**: 遅らせた処理で、App に届く台帳の窓のうち、存在して `winfo_viewable()` が偽の窓にも `get_backend().window.order_out(window)` を呼ぶ（`withdraw()` も記録もしない）。表示中の窓は今どおり withdraw + `order_out` + 記録。
- **テスト**: `tests_ui/test_modal_grab.py` に 1 件（backend を patch・Tk が隠した直接の子にも `order_out` が呼ばれ、`_hidden_by_minimize` には入らない）。既存の `test_minimize_calls_order_out_for_each_hidden_window` の期待（呼ばれた窓 = 記録した窓）は、記録した窓が呼ばれた窓に含まれる、に直す。
- **目視（やり直し）**: 3 枚の状態でメインの黄色のボタン → 全部隠れる・戻すと元どおり。
- **追記（メイン実測・2026-11-17）**: aqua の Tk は transient を NSWindow の子の窓（`addChildWindow`）としてつなぐ。子の窓が表示中だと親に `orderOut_` しても消えない（確認 → プリセット管理の順に呼ぶと消える）。遅らせた処理は台帳を**内側から**（`reversed(_active_modals)`）たどって withdraw / `order_out` し、`_hidden_by_minimize` には今どおり**開いた順**で記録する（再表示は外側から）。

## 改訂 5（Mac 目視・2026-11-17）— 上の記述に優先する

- **目視の結果**: ダイアログは全部隠れる・戻すと元どおり = OK。NG: メインをしまうと Dock に入るが、画面にもメインの絵が残る（操作できない）。
- **原因（メイン実測・本物のクリック）**: aqua の Tk は transient を NSWindow の子の窓（`addChildWindow`）としてつなぐ。子の窓がつながったままメインをしまうと、WindowServer にメインが表示中として残る（`CGWindowListCopyWindowInfo` の OnScreen に残る）。modal の隠す処理を止めても起きる・ダイアログが無ければ起きない。隠すタイミングを 1.2 秒まで遅らせても、しまった後につながりを外しても消えない。
- **直し方**: しまう直前の `NSWindowWillMiniaturizeNotification` で、メインの子の窓のつながりを再帰的に外す（`removeChildWindow_`）と残像が出ない。戻すと Tk がつなぎ直す（実測）。普段から外すと、メインのクリックでダイアログがメインの後ろへ回るので、外すのはしまう直前だけ。
  - `WindowBackend` に `install_minimize_preparation(self, window: tkinter.Misc) -> bool` を足す。Windows は何もせず True。
  - macOS: `ns_window_for(window)` の NSWindow に、`NSNotificationCenter.defaultCenter()` で `NSWindowWillMiniaturizeNotification`（object = その NSWindow）の観測者を登録する。観測者（`NSObject` の小さなサブクラス・`macos/` の新規モジュールでよい）は通知の窓の `childWindows()` を再帰的に `removeChildWindow_` する。観測者は backend が保持する（解放されないように）。同じ窓へ二重に登録しない。引けない / 例外は False（ログ 1 回）。観測者の中の例外は握ってログ 1 回。
  - `modal.py` の `install_minimize_grab_custody(app)` の最初で `get_backend().window.install_minimize_preparation(app)` を呼ぶ。
- **テスト**: `tests/test_os_backend_contracts.py`（Windows は True）・`tests/test_macos_window_backend.py`（Tk なし・偽の AppKit / 通知センター: 登録の引数・二重登録しない・観測者が子の窓を再帰的に外す・引けないと False）・`tests_ui/test_modal_grab.py`（`install_minimize_grab_custody` が backend の `install_minimize_preparation` を app で呼ぶ）。
- **目視（やり直し）**: 3 枚の状態でメインの黄色のボタン → メインもダイアログも画面から消え、残像が無い・戻すと元どおり・ダイアログを開いた状態でメインをクリックしてもダイアログがメインの後ろへ回らない。
