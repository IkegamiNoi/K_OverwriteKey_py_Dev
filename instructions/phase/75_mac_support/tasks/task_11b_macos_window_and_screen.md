# task_11b_macos_window_and_screen

## 目的

macOS の窓と画面の口を実装する（暫定 57 §5.4 の表「モニタ一覧」「クリック透過」「窓の重なり順」・表の下の「Tk の窓から NSWindow を引く」・§3 の `Capabilities`）。今の `MacWindowBackend` は `foreground_own_window` が None、`place_window_below` / `make_click_through_overlay` が False、`list_monitor_rects` が空、`window_handle` が `winfo_id()`（`macos/backend.py:437-441`）。このため Mac では、カーソルグリッドが使えず、キーボードUIの最前面の解除（ダイアログの下へ回す・`layout_controller.py:160-190`）と、モーダルの前面の判定（`modal.py:13-21`）が働かない。

- 主に infrastructure（`os_backend/macos/`）。契約の変更は `make_click_through_overlay` の 1 か所だけ（下記）。それに合わせて `windows/backend.py` と presentation の `grid_overlay_window.py` を変える。application・domain は変えない。
- OS の判定は backend の中だけで行う（presentation で OS を見ない）。

## メインの実測（2026-11-16・Mac・起票前）

- **NSWindow を一意に引く方法**: Tk の公開の C 関数 `Tk_MacOSXGetNSWindowForDrawable` を ctypes で引いた（`ctypes.CDLL(None)` で見つかる・Tk 9）。`winfo_id()` を渡すと NSWindow のポインタが返る。`objc.objc_object(c_void_p=ptr)` で `TKWindow` になる。同じ位置・同じ大きさの 2 つの窓（ルートと Toplevel）でも、別の NSWindow（`windowNumber` 17109 / 17110）を返した。→ **位置の照合は使わない**（§5.4 の表の下の「一意に決まる引き方」はこれで満たす）。
- `NSApp.keyWindow()` は前面の自分の窓（上の例では Toplevel）を返す。
- `wm attributes` に `-transparent` がある。`-transparent 1` と背景 `systemTransparent` を Toplevel と Canvas に設定できた（`-transparentcolor` は無い）。
- `NSScreen.screens()` の `frame` は、主画面が原点 (0, 0)・下が原点（主画面の高さ 1084 = Tk の `winfo_screenheight`）。

## 対象範囲

### 契約（`os_backend/contracts.py`）

- `make_click_through_overlay(self, window, transparent_color: str) -> bool` に変える。意味は「`window` のうち `transparent_color` で塗った部分を透けて見えるようにし、窓全体をクリック透過にする。できたら True」。
- 他の口の署名は変えない。`Capabilities` のフィールドは変えない。

### Windows（`windows/backend.py`）

- `make_click_through_overlay(window, transparent_color)`: 先に `window.attributes("-transparentcolor", transparent_color)` を呼ぶ（今の presentation の `grid_overlay_window.py:40` から移す）。その後は今と同じく `win32_window.make_click_through_overlay(window.winfo_id())` を呼ぶ。`TclError` は False。**Windows の動作は変えない**（呼ぶ順番も今と同じ: 透明色 → スタイル）。

### presentation（`screen_grid/grid_overlay_window.py`）

- `window.attributes("-transparentcolor", _TRANSPARENT)`（`:40`）を消し、`make_click_through_overlay(window, _TRANSPARENT)` に渡す。それ以外は変えない。

### macOS（`macos/backend.py`・新規 `macos/ns_window.py`）

- 新規 `macos/ns_window.py`:
  - `ns_window_for(widget) -> object | None`: `widget.winfo_toplevel()` の `winfo_id()` を `Tk_MacOSXGetNSWindowForDrawable` に渡し、NSWindow を返す。関数が見つからない・NULL・例外なら None（ログは初回 1 回）。関数は `ctypes.CDLL(None)` から 1 回だけ引いて覚える（restype / argtypes = `c_void_p`）。テスト用に、関数と `objc` を注入できるようにする。
  - **UI スレッドからだけ呼ぶ**（AppKit）。呼び出し元（`modal.py`・`layout_controller.py`・`grid_overlay_window.py`・`screen_grid_controller.py`）は今どれも UI スレッド。
- `MacWindowBackend`:
  - `window_handle(window)`: `ns_window_for(window)` の `windowNumber()`（int）。引けなければ None。
  - `foreground_own_window()`: `NSApp.keyWindow()` が None でなく、アプリが前面（`NSApp.isActive()`）なら、その `windowNumber()`。それ以外は None。例外は None（ログは初回 1 回）。
  - `place_window_below(window, above)`: `above` は `windowNumber`。`ns_window_for(window)` の `orderWindow_relativeTo_(NSWindowBelow, above)`。引けない・`above` が int でない・例外なら False。
  - `list_monitor_rects()`: `NSScreen.screens()` の各 `frame()` を左上原点に直す。主画面（`screens()[0]`）の高さを H とすると、`(x, H - (y + h), x + w, H - y)`、主画面かどうか = 先頭かどうか。座標は int に丸める。例外は空リスト（ログは初回 1 回）。Windows と同じく作業領域ではなく画面全体（`frame`）。
  - `make_click_through_overlay(window, transparent_color)`: `window.attributes("-transparent", True)` → `window` と子孫のウィジェットのうち、背景が `transparent_color` のものを `systemTransparent` に変える → `ns_window_for(window).setIgnoresMouseEvents_(True)`。どれかが失敗したら False。
  - AppKit（`NSApp` / `NSScreen` / `NSWindowBelow`）は遅延 import で、注入できるようにする（`appkit=None` の既存の形）。
- `create_backend()` の `Capabilities`: `click_through_window=True`・`window_stacking=True`（`status_icon` / `ime_control` は変えない）。

### 無効化の UI

- 新しい UI は作らない。クリック透過を作れないときは、今の失敗の経路（`grid_overlay_window.py:42` の `screen_grid.overlay.click_through_failed` → カーソルグリッドが始まらず通知）がそのまま「無効化」になる。モニタ一覧が空のときも、今の経路（対象のモニタが無い）のまま。
- `Capabilities` を読んで UI を消す処理は今どこにも無い（調査・メイン確認）。本タスクでも足さない。目視で Mac で動かない機能が見つかったら、報告して止める（その時点で無効化の UI を起票する）。

### テスト

- `tests/test_os_backend_contracts.py`: 署名の検査（`transparent_color` の追加）・Mac の factory の `Capabilities` の期待値・Windows の委譲（`attributes("-transparentcolor", ...)` を呼んでから `make_click_through_overlay(winfo_id)`・`TclError` で False）。
- 新規 `tests/test_macos_window_backend.py`（Tk なし・偽 AppKit / 偽の Tk の関数）: `ns_window_for` の NULL / 例外 / 関数が無い → None・ログ 1 回 / `window_handle` / `foreground_own_window`（前面でない・keyWindow が None・例外）/ `place_window_below`（`NSWindowBelow` と `above` を渡す・失敗で False）/ `list_monitor_rects` の座標の変換（主画面と、主画面の上・左・右にある 2 枚目）/ `make_click_through_overlay` の背景の置き換えと `setIgnoresMouseEvents_(True)`・失敗で False。Windows でも走る（`sys.platform` で skip しない）。
- `tests_ui/test_screen_grid_overlay.py`: `make_click_through_overlay` の偽物の署名を合わせる。`-transparentcolor` を前提にした検査があれば、backend の偽物の呼び出しの検査に置き換える。基準線の失敗 4・エラー 9 が減るかを報告する。

## 読むファイル

- `instructions/history/57_mac_support.md` §3（`:60-75`）・§4.1 の窓の行（`:123`）・§5.4 の表と表の下（`:294-315`）
- `keyseq/infrastructure/os_backend/contracts.py:92-123`
- `keyseq/infrastructure/os_backend/macos/backend.py`（`MacWindowBackend` `:410-450`・`create_backend` `:595-610`・`MacKeyboardBackend` の `appkit` / `foundation` の注入の形）
- `keyseq/infrastructure/os_backend/windows/backend.py:44-62`
- `keyseq/presentation/screen_grid/grid_overlay_window.py:25-50`・`screen_grid_controller.py:35-40`
- `keyseq/presentation/controllers/layout_controller.py:160-190`・`keyseq/presentation/modal.py:13-21`（呼び出し側の期待）
- `tests/test_os_backend_contracts.py`（Mac の factory と Windows の委譲のテスト）・`tests_ui/test_screen_grid_overlay.py:1-60`

## 含まない

- aqua のモーダル（`test_modal_grab`）・`test_minimize_grab_custody`・トリガーの追加ダイアログが後ろへ回る件（task_11c）。ただし本タスクで `foreground_own_window` が動き始めるので、`test_modal_grab` の結果が変わったら報告する
- 割り当て禁止の文言（task_11d）
- `Capabilities` を読んで UI を消す処理（上の「無効化の UI」）
- 状態のアイコン・IME の `Capabilities`

## 確認

Mac（verifier）:
- compile clean。
- `tests` の失敗 / エラーが基準線（2108 件・失敗 1〔test_third_party〕・エラー 0）から増えない。
- smoke pass。
- tests_ui を 1 本ずつ: `test_screen_grid_overlay`（減った数）・`test_modal_app_foreground`・`test_help_window`・`test_modal_grab`（変化を報告）。

Windows: task_09〜11a の Windows 検証と合わせて行う。`tests`（委譲のテスト）と `tests_ui/test_screen_grid_overlay`。目視 = カーソルグリッドが今どおり透けてクリックが通ること。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- `codebase_map.md` を追従する（メイン）: Mac の backend の行（`:39`）・`make_click_through_overlay` の署名・カーソルグリッドの節。`mac_test_baseline.md` の `test_screen_grid_overlay` の行も追従する。
- 実機目視（Mac・本タスクで実施）:
  1. カーソルグリッドを開始すると、画面にグリッドが重なり、グリッドの下が透けて見える。グリッドの上のクリックが下の窓へ通る。グリッドの操作（キーでの絞り込み・クリック）が今の仕様どおりに動く。
  2. モニタが 2 枚あれば、それぞれの位置と主画面が正しい（1 枚なら 1 枚で確認）。
  3. キーボードUIの「最前面に表示」を有効にしてダイアログを開くと、キーボードUIがダイアログの下へ回る（ダイアログを隠さない）。閉じると最前面に戻る。
  4. 最小化から戻したときなど、モーダルのダイアログにフォーカスが戻る（`modal.py` の前面の判定）。

## 起票レビュー（reviewer「修正して採用」2026-11-16）の反映 — 上の記述に優先する

- **H1（`window_handle` が None）**: `layout_controller.py:169-175` は、`main` か `keyboard` が None だと、前面が自分の窓でも `is_dialog = True` と誤判定する（最前面を外して `place_window_below` まで走る）。`modal.py:18` は安全。
  - → presentation の `layout_controller.py` に「`main is None or keyboard is None` なら `is_dialog = False`」のガードを足す（対象範囲に追加・Windows は常に int なので影響なし）。
  - 契約の `window_handle` に「引けなければ None」を docstring で明記する。
- **M1（暫定 57 v0.15・ユーザー承認が前提）**:
  - §4.1:123 と §5.4 の表の下の「NSWindow の引き方」を、`Tk_MacOSXGetNSWindowForDrawable` に訂正する（メインの実測を記録）。
  - §3.2 に `make_click_through_overlay(window, transparent_color)` の意味を 1 行足す。
  - phase.md:83 の「無効化の UI」は、「目視で動かない機能が見つかったら起票」と書き換える。`Capabilities` を True にする根拠は目視 1〜4 の pass。
  - 承認が無いうちは実装しない。
- **M2（Windows の順番）**: 今は `-transparentcolor` → `update_idletasks()` → スタイル（`grid_overlay_window.py:40-42`）。そこで Windows の `make_click_through_overlay` は、`-transparentcolor` の後に `window.update_idletasks()` を呼んでから `win32_window.make_click_through_overlay` を呼ぶ。presentation の `update_idletasks()` はそのまま残す（二重になるが無害）。
  - 失敗の型の変化: 前は `attributes` の `TclError` がそのまま送出されたが、これからは False になり、`RuntimeError(click_through_failed)` に変わる。カーソルグリッドが始まらず通知が出る点は同じ。tests_ui で確かめる。
- **M3（細部）**:
  - **一度も表示していない窓の `windowNumber` は -1**（メイン実測。表示した後に withdraw した窓は番号を保つ）。0 以下は None として扱う。
  - `NSApp` ではなく `NSApplication.sharedApplication()` を使う。
  - borderless（`overrideredirect`）の窓は key にならず、`foreground_own_window` がメインの窓を返すことがある。`layout_controller` では安全側（`is_dialog` が偽）に倒れる。
  - `place_window_below` は、`apply_keyboard_topmost` で floating のレベルを外した後に呼ぶ（今の順・`layout_controller.py:180-187`）。transient の子窓扱いで order が無視されないかは、目視 3 で見る。
- **M4（テスト）**:
  - `tests_ui/test_screen_grid_overlay.py:141` の `attributes("-transparentcolor")` の検査は、偽の `styles` に渡った第 2 引数が `"#ff00fe"` であることの検査に置き換える（`:140` の背景の検査は残す）。
  - `tests/test_os_backend_contracts.py:97` の期待値を `Capabilities(True, True, False, False)` にする。
  - Windows の委譲のテストは、`attributes("-transparentcolor", color)` → `update_idletasks()` → `win32_window.make_click_through_overlay` の**呼び出しの順**を `Mock` で検査する。`test_os_backend_contracts.py` の Windows のテストは `sys.platform != "win32"` で skip されるので、Windows 検証で必ず走らせる（Mac でも走る形にできるなら、そうしてよい）。
  - `test_macos_window_backend.py` に足す項目: `windowNumber` が 0 以下 → None / `list_monitor_rects` の 2 枚目が上・下・左・右 / `screens()` が空 → 空リスト / `-transparent` の `TclError` と `ns_window_for` が None → False / `layout_controller` のガード（presentation のテストは `tests/` に Tk なしで書けなければ tests_ui に 1 件）。
  - 座標の丸めは `round`。
- **L1**: 背景の置き換えは、`cget("background")` を大文字小文字を無視して比べる。`background` を持たない子（ttk 等）の `TclError` は飛ばす（失敗にしない）。
- **L2**: `ns_window_for` の結果は保持せず、毎回引く（非所有のポインタ・窓の破棄後に使わないため）。
- **L3**: `test_modal_grab` の変化の報告は目視 4 とセットで見る。

## 改訂（Mac 目視・ユーザー判断 2026-11-16）— 上の記述に優先する

- **目視の結果**: 1 = NG（グリッドの下が見えない）・2 = 未確認（2 枚目のモニタが無い）・3 = キーボードUIはダイアログの下へ回る（OK）。「取得」を押すとダイアログがメインとキーボードUIの後ろへ回る件は task_11c の既知の症状・4 = OK。
- **1 の原因（メイン実測）**: Tk 9.1 の aqua は、`-transparent` の窓に描画すると透明の部分が不透明な黒になる（Canvas でも Frame でも同じ・窓だけを撮った画素の透明度で確認）。`-alpha` は効く。
- **直し方（暫定 57 v0.16 §3.2・§5.4・ユーザー判断 A）**: `MacWindowBackend.make_click_through_overlay` は `-transparent` と `systemTransparent` をやめる。
  - 子孫を辿って `transparent_color` の背景を `#000000` に塗り替える（大文字小文字を無視・`background` を持たない子は飛ばす・L1 のまま）。
  - `window.attributes("-alpha", 0.5)` で窓全体を半透明にする（値は backend の定数）。
  - `setIgnoresMouseEvents_(True)` はそのまま。どれかの失敗で False（今と同じ）。
  - Windows と presentation は変えない。
- **テスト**: `tests/test_macos_window_backend.py` の `test_click_through_recolors_descendants_and_handles_failures` を合わせる（背景が `#000000`・`-alpha` 0.5・`-transparent` を呼ばない・`-alpha` の `TclError` で False）。
- **目視（やり直し）**: 1 = グリッドの下が暗く透けて見え、クリックが下の窓へ通る・線とキーの文字が読める。キーで絞り込んだとき、選んだ範囲の外の塗り（`_SHADE`）が見分けられる（reviewer 指摘 1・見分けられなければ OS 別の色の話として別タスクでユーザー判断）。2 は 2 枚目のモニタがあるときに確認する（未確認のまま完了にしてよい・ユーザー判断待ち）。
- **レビュー（reviewer「修正して採用」2026-11-16）**: 必須の修正なし。指摘 1 を目視 1 に追加。指摘 2（`cell_label.py:6` のコメント）・指摘 3（テストの穴は外側の `except` で False になり実害なし）は対応しない。

## 改訂 2（目視 1 のやり直し・ユーザー 2026-11-16）— 上の記述に優先する

- **目視の結果**: 下が暗く透けて見える・線と文字が読める・絞り込みの塗りが見分けられる = OK。**クリックが下の窓へ届かない = NG**。目視 2（2 枚目のモニタ）は保留でよい（ユーザー判断）。
- **原因（メイン実測）**: Tk 9.1 は窓を表示する（deiconify）たびに `ignoresMouseEvents` を False に戻す。deiconify の中で `<Map>` と after_idle が走った後に戻すので、それらでかけ直しても効かない。deiconify から戻った後（`after(0)`）にかけ直すと、withdraw → deiconify・geometry・描画・lift の後も True を保つ。
- **直し方**: `MacWindowBackend.make_click_through_overlay` は、今の `setIgnoresMouseEvents_(True)` に加え、`window.bind("<Map>", handler, add="+")` を登録する。handler は `event.widget is window` のときだけ `window.after(0, reapply)` を予約する。`reapply` は `ns_window_for(window)` を引き直して（L2・保持しない）`setIgnoresMouseEvents_(True)` を呼ぶ。引けない・例外はログ 1 回で握る（フックではないが、表示の処理を落とさない）。
  - presentation と Windows は変えない。暫定 57 §5.4 の表の「クリック透過」の行に「表示のたびにかけ直す」を足す（v0.16 の範囲・メイン）。
- **テスト**: `tests/test_macos_window_backend.py` に 1 件足す（Tk なし）: `bind` が `"<Map>"`・`add="+"` で呼ばれる / handler に別の widget の event → `after` を呼ばない / 窓自身の event → `after(0, ...)` を予約し、その関数を呼ぶと `setIgnoresMouseEvents_(True)` / `ns_window_for` が None や例外でも送出しない。
- **目視（やり直し）**: カーソルグリッドの開始中に、グリッドの上のクリックが下の窓へ届く。グリッドを止めて再開した後も届く。

## 改訂 3（クリックの目視・ユーザー 2026-11-16）— 上の記述に優先する

- **目視の結果**: グリッドの上のクリックが下の窓へ届く・止めて再開した後も届く = OK。NG は 3 件。
  - (a) カーソルグリッドでクリックした後、グリッドがクリックした先の窓の後ろへ回る。
  - (b) メインの「最前面」が有効のとき、グリッドがメインの後ろへ回る。
  - (c) メインの「最前面」が有効のとき、「未保存があります」のダイアログが前面に来ない → task_11c（メインが最前面のときダイアログが後ろへ回る件と同じ種類）。本タスクでは扱わない。
- **(a)(b) の原因（メイン実測）**: Tk 9.1 の `-topmost` は窓のレベルを 19 にするが、`overrideredirect` の窓は表示（deiconify）のたびにレベルを 0 に戻す。`setLevel_(NSStatusWindowLevel)`（25）は表示し直した後も保つ。ただし `-topmost` を設定し直すと 19 に戻る。
- **直し方**: `MacWindowBackend.make_click_through_overlay` と、改訂 2 のかけ直し（`<Map>` の後の `after(0)`）の両方で、`setIgnoresMouseEvents_(True)` と一緒に `setLevel_(AppKit.NSStatusWindowLevel)` を呼ぶ（AppKit は `self._get_appkit()` から取る）。presentation と Windows は変えない。暫定 57 §5.4 の表の「クリック透過」の行に「レベルは NSStatusWindowLevel」を足す（v0.16 の範囲・メイン）。
- **テスト**: `tests/test_macos_window_backend.py` の既存の 2 件（`test_click_through_recolors_descendants_and_handles_failures`・`test_click_through_reapplies_after_map`）に、`setLevel_` が `NSStatusWindowLevel` で呼ばれる検査を足す。
- **目視（やり直し）**: グリッドでクリックした後も、グリッドが前に残る。メインの「最前面」が有効でも、グリッドがメインの前に出る。
- **レビュー（reviewer「採用」2026-11-16）**: 必須の修正なし。注意: グリッドの窓へ表示の後に `-topmost` を設定し直すとレベルが 19 に戻り (a)(b) が再発する（今はその経路なし・`grid_overlay_window.py:34` は `make_click_through_overlay` の前）。
