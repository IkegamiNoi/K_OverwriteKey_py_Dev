# 暫定仕様 47: 送信の最中の物理の入力を素通りさせない（send_without_dropping_physical_input）

> 状態: **保留（2026-10-21・ユーザー判断・未確定・実装しない）・v0.2**（v0.1 → 起票時 deep-reviewer「修正して採用」15 件を反映）。
> 保留の理由: keyboard の内部 3 か所の差し替えと版の固定に頼る作りで維持の負担が大きい / 実害は送信の最中に押したときだけでまれ（無変換・変換は phase 63 で抑え済み）。§6 は未確認のまま。再開時は §1 の現状監査を裏取りし直してから §6 を確認する（phase は未起票）。
> 本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: [idea_53](../backlog/idea_53_send_without_dropping_physical_input.md)（2026-10-20・phase 63 task_03 の実機目視の NG の計測から分離）。2026-10-21 ユーザーが着手を判断。

---

## §1 目的 / 背景

アプリが送信している最中に届いた**物理の**キー入力が、アプリのフックで判定されずに OS へ素通りする。
押下だけのキー（無変換・変換）ではこれで IME が切り替わり、離しの 2 回組も崩れる（phase 63 はリピートなしで頻度を下げただけ）。
**自分の送信だけを見分けてフックの判定から除き、物理の入力は送信の最中でもいつも判定する**。

### 現状監査（2026-10-21・keyboard 0.13.5 の実体を直読み・deep-reviewer が裏取り）

keyboard（`.venv/Lib/site-packages/keyboard/`）:
- **送信の間、物理の入力も含めて全部素通し**: `__init__.py:233` `direct_callback` は `is_replaying` なら即 `return True`（判定にも押下の記録 `_pressed_events`〔:244-250〕にも渡さない）。`is_replaying` を立てるのは `send`（:377-389）と `restore_state`（:801-811）だけ。インスタンス属性で、`init` で偽に初期化（:205）
- `write`（:819-866）は Windows では `exact=True`: 先に `stash_state()`（:784-794）で押下中のキーを離し（**`is_replaying` を立てない** = その離しは keyboard の判定と記録の更新を通り、アプリのフックにも届く〔今は送信ガード中なので素通し〕）、`\n` `\b` は `send`、他の文字は `type_unicode`。`restore_state_after=False`（アプリの指定）なので押し直さない
- **低レベルフックで目印を捨てる**: `_winkeyboard.py:531-548` `low_level_keyboard_handler` は `KBDLLHOOKSTRUCT`（:54-60。`flags` と `dwExtraInfo`）から vk / scan_code / 拡張ビットだけを取る。`VK_PACKET` と「注入 + 0x20」は判定に回さず素通し（:537）。**`ULONG_PTR = POINTER(DWORD)`（:35）のため `dwExtraInfo` はポインタ型で読める**（整数との `==` は常に偽）
- フックの登録: `prepare_intercept` が `LowLevelKeyboardProc(low_level_keyboard_handler)`（:551）→ `SetWindowsHookEx`（:554）。どちらも**呼ぶ時点でモジュールの属性として引く**ので差し替えが効く。`keyboard.hook(suppress=True)` → `start_if_necessary`（`_generic.py:28-46`）→ リスナーのスレッドで `listen` → `prepare_intercept`。`listening` は一度真になると戻らない
- 送信: `press` / `release` → `_send_event`（:577-588）→ `keybd_event(vk, code, type, 0)`（dwExtraInfo = 0）/ `type_unicode`（:596-613）→ `SendInput`（dwExtraInfo = None・`VK_PACKET`）。`__init__` は `_os_keyboard.press` 等を呼ぶたびに引く（:122 でモジュールのまま import）
- `direct_callback` は修飾キーの偽の押下（:278）をフックのスレッドから送ることがあるが、`blocking_hotkeys`（`add_hotkey`）があるときだけで、アプリは使っていない

アプリ:
- 送信（`keyseq/infrastructure/input_gateway.py`）は 3 系統: keyboard の `send` / `press` / `release` / `write`（:278-344）・拡張キーの `ctypes.windll.user32.keybd_event`（:132-146・argtypes なし）・テンキーとレイアウトの走査コードの自前 `SendInput`（:160-187・`_KEYBDINPUT.dwExtraInfo` は `c_size_t`〔:60〕で 0）。自前の 2 系統は `_listener.is_replaying` を自分で立てて戻す（keyboard の押下の記録に載せないため・`key_input.md:216`）
- フックの登録は `hook_coordinator.py:65`（`register_global_hook`・suppress=True）だけ。`InputGateway` の生成は `app.py:137`（フックの登録より前）
- **送信ガードの素通し**: `input_router.py:87-90` は `_send_guard_count > 0` なら route を作らず `accept=True`（停止キーも判定せず、`key_state_manager` も更新しない〔:97 より前〕）。`tests/test_input_router.py:172-175` が固定。`_send_guard_count` を読むのは `input_router.py:89` とデバッグ出力 `hook_controller.py:323` と出口の判定 `action_executor.py:360` だけ（配線 `app.py:183`・`:366`）
- スレッド: フックの判定（`hook_controller.on_input_event`）は keyboard の**フックのスレッド**で同期に走り、アクションは `app.after(0, …)` で **UI スレッド**に積む（`hook_controller.py:294-313`）
- 正本の受容・前提: `key_input.md:90`（押下だけのキーはリピートなし）・:113-114（押下だけのキーの覚えた決定・送信ガード中）・:126・:216・:220-221 / `features.md:387`・:446-447・:703 / `codebase_map.md:772`
- 依存: `requirements.txt` の keyboard は**版の指定なし**（実体は 0.13.5）

## §2 確定事項（ユーザー 2026-10-21）

- idea_53 を phase 65 で扱う・暫定仕様先行モード
- （以下は §6 の確認後に追記）

## §3 方式（推奨 = 案 A1）

### §3.1 案の比較

| 案 | 中身 | 評価 |
|---|---|---|
| **A1（推奨）** | 自分の送信すべてに目印（`dwExtraInfo`）を付け、keyboard の低レベルフックの**手前で**目印のある入力だけを判定から外す（OS へ通す）。`is_replaying` と送信ガードの素通しをやめる | keyboard の内部の差し替えは 3 点（フックの関数型・送信関数・`is_replaying`）。送信の経路・押下の記録に載らない扱いは今と同じ |
| A2 | 送信を全部自前の `SendInput` に統一 + A1 のフック側 | 送信側の書き直しが大きい。フック側は A1 と同じだけ要る |
| A3 | keyboard のフックをやめ自前の低レベルフックに置き換える | 名前の表・押下の記録・suppress を作り直す。最大 |
| B | 送信の最中の物理の入力を覚え、送信の後で判定し直す | **単独では成り立たない**（自分の送信と物理の入力を見分けるには A1 と同じ目印が要る）。遅れと順序の崩れも出る |

### §3.2 A1 の中身（infrastructure に新規モジュール 1 つ = 「keyboard の差し替えの口」）

1. **目印**: 定数 `KEYSEQ_INJECT_MARK`（**31 bit 以内**の非 0 の整数）を差し替えの口に 1 か所で定義する
2. **送信に目印を付ける**:
   - 自前の `SendInput`: `_KEYBDINPUT.dwExtraInfo` に目印（`c_size_t` のまま）
   - 自前と keyboard の `keybd_event`: **専用の `WinDLL("user32")`** に `keybd_event` の argtypes（第 4 引数 = `c_size_t`）を設定して使い、第 4 引数に目印を渡す（共有の `windll` は書き換えない・`key_input.md` §7.7 の前面判定と同じ方針）
   - keyboard の送信は `keyboard._winkeyboard._send_event` を「同じ処理で第 4 引数だけ目印にする」関数へ差し替える（`send` / `press` / `release` / `write` の `\n` `\b` / `stash_state` / `restore_*` がすべて通る）
   - `type_unicode` は差し替えない（`VK_PACKET` は目印の有無に関係なく keyboard が判定から外す・:537）
3. **フックの手前で目印の入力を外す**: `keyboard._winkeyboard.LowLevelKeyboardProc` を「Python の関数 `f` を受け取り、`g(nCode, wParam, lParam)` = 『`lParam.contents.flags & LLKHF_INJECTED`（0x10）**かつ** `dwExtraInfo` を整数で読んだ値（`ctypes.cast(lParam.contents.dwExtraInfo, c_void_p).value`・0 は None）== 目印』なら `CallNextHookEx(None, nCode, wParam, lParam)` を返す、それ以外は `f(nCode, wParam, lParam)` を返す」で包んで**元の関数型で返す**関数へ差し替える
   - 包む側で例外が出たら `f` へ渡す（keyboard の握りつぶし :544-546 と同じ扱い）
   - 包んだ CFUNCTYPE の参照は keyboard 側が保持する（`keyboard_callback`・atexit :558）。差し替えの口でも保持する
   - 目印の入力は keyboard の判定・押下の記録・アプリのフックのどれにも渡らない（= 今の `is_replaying` と同じ扱い）
4. **`is_replaying` を効かなくする**: `keyboard._listener` のクラスに `is_replaying` のデータ記述子（getter は常に偽・setter は無視）を置く（keyboard の `send` / `restore_state` / `init` の書き込みが効かない形）。**目印が有効なとき（§3.2-6）だけ入れる**。自前の送信で `_listener.is_replaying` を立てて戻す処理（`input_gateway.py:132-146`・:160-187）は、**目印が有効なときは行わない**（縮退時は今のまま行う）
5. **送信ガードの素通しをやめる**（application）: `input_router.handle` の `_send_guard_count > 0` の早期 return を、**目印が有効なときは行わない**（縮退時は今のまま）。目印が有効かは、infrastructure から `own_input_marked: Callable[[], bool]` を `InputRouter` へ注入して知る（`app.py:183` の配線・application は infrastructure を import しない）。送信ガードのカウンターは縮退時の素通しとデバッグ出力のために残す
6. **入れる時機と縮退**: `InputGateway` の生成時（`app.py:137`・フックの登録 `hook_coordinator.py:65` より前）に差し替えの口の `install()` を 1 回呼ぶ。**次の全部が揃ったときだけ 3 点（2 の `_send_event`・3・4）をまとめて入れ、目印を有効にする**。1 つでも欠ければ何も入れず目印は無効（今の挙動のまま・ログは 1 回）:
   - `keyboard.__version__`（または配布の版）が 0.13.5
   - `_winkeyboard` に `_send_event` / `LowLevelKeyboardProc` / `KBDLLHOOKSTRUCT`（`flags` と `dwExtraInfo`）があり、`keyboard._listener` がある
   - `_listener.listening` が偽（keyboard のリスナーがまだ始まっていない）
   - Windows
7. **keyboard の版**: `requirements.txt` で `keyboard==0.13.5` に固定する（§6 Q2）
8. テスト用に、入れた差し替えを元へ戻す `uninstall()`（または patch の文脈）を用意する（プロセス全体の書き換えのため・縮退のテストや tests_ui / smoke と干渉させない）

### §3.3 変わる挙動（目印が有効なとき）

- 送信の最中に届いた物理の入力は**その場で判定する**（suppress・`key_state_manager` の更新も送信の外と同じ規則）。アクションは今と同じく `after(0)` で UI スレッドに積まれ、**今の送信が終わってから**実行する
- 停止キー・トグルキー・切替キーも送信の最中に判定する（今は素通り）。停止は今の送信が終わってから効く（長い text の途中では止まらない・§6 Q3）
- **送信の最中のキーリピート**（OS の自動リピートの押下 = `repeat` 判定の押下）の扱いは §6 Q5（溜めると送信の後でまとめて実行され、トリガーが長い text なら連鎖して長引く）
- 自分の送信は今と同じくアプリのフックにも keyboard の押下の記録にも載らない（phase 51 の右 ctrl の不具合を防ぐ `key_input.md:216` は保たれる）。送った置換先を自分で拾って置換し直すループも起きない
- **`write` の前の `stash_state` の離し**は目印付きになり keyboard の記録から消えなくなる: 手で押し続けているキーは text の送信の後も keyboard の `_pressed_events` に残る（手で離したときに消える・次の `write` でもう一度離す）。今は記録から消えている＝受容（実害は小さい）
- 他のアプリが注入した入力（目印なし）は物理の入力と同じに判定する（今は送信の間だけ素通り）
- `VK_PACKET`（文字の送信）と「注入 + 0x20」の素通しは keyboard の規則のまま

### §3.4 縮退時（目印が無効）

今の挙動のまま（keyboard の `is_replaying`・自前の送信の `is_replaying`・送信ガードの素通し）。§1 の受容（`key_input.md:216`・:220-221）は縮退時に限って残る。

## §4 押下だけのキーのリピート（§6 Q4・推奨 = 本フェーズでは戻さない）

phase 63 のリピートなし（`key_input.md:90`）は送信の素通りへの対処だったが、凍結した暫定 46 v0.5 の状態機械はリピートなしを前提に作られている（覚えた決定は accept だけを持つ・押し続けの続き・片方の離し・46 :90-93・:157）。v0.3 の「リピート」の規定は v0.4 で撤回され本文に無い。また v0.5 の NG（フックの詰まりでリピートを離しの 2 回組と取り違える）と 46 §9 #7（241 / 242 が全て抑止されていても IME が切り替わった・原因未特定）は送信の素通りと無関係に残る。
**推奨: 本フェーズでは戻さず、A1 の実機目視（押下だけのキーを送信と重ねても IME が切り替わらないか）の結果を見てから別フェーズ（idea_54 と合わせて）で扱う。** 枠の色（灰色がかった緑・`features.md:703`）も変えない。

## §5 テスト方針

- infrastructure（差し替えの口）: 包んだ関数が「注入 + 目印」の `KBDLLHOOKSTRUCT` を `f` へ渡さず `CallNextHookEx` を返す / 目印なし・注入なし・目印が違う値は `f` へ渡す / 包む側の例外は `f` へ / 差し替えた `_send_event` と自前の `keybd_event` / `SendInput` が目印を入れる（偽の `user32` で受けて検査）/ `is_replaying` の記述子は書き込みを無視して偽 / 揃わないとき（版違い・属性なし・`listening` が真）は何も入れない / `uninstall()` で元へ戻る
- application: 目印が有効なら送信ガード中でも判定し `key_state_manager` を更新する / 無効なら今のまま素通し（`tests/test_input_router.py:172-175` は無効のときの期待として残し、有効のときの期待を足す）
- 既存: `tests/test_input_gateway_send.py:304-376`（`is_replaying` の設定・復元）は縮退時の期待として残し、有効時の期待（立てない・目印を入れる）を足す
- 並行の観点: フックのスレッドで判定中に UI スレッドで送信している状態（偽のフックの呼び出しを送信の最中に差し込む）
- **実機目視（必須）**: hotkey・直接置換・text（長い 1 行）の送信中に押したトリガーが送信の後で動く / 置換のループが起きない / phase 51（右 ctrl を押したまま text → 左 ctrl が残らない）・phase 52（key_hold のリピート中の打鍵）のやり直し / 押下だけのキーを送信と重ねても IME が切り替わらないか（§4 の判断材料・記録のみ）

## §6 確認事項（ユーザー判断）

- **Q1 方式**: 案 A1 でよいか（推奨。理由 §3.1）
- **Q2 版の固定と縮退**: `keyboard==0.13.5` に固定し、差し替えの条件が揃わなければ今の挙動へ戻す（推奨）。代案 = 揃わなければ起動を止める（安全側だが使えなくなる）。残存リスク: 縮退の判定は版と属性しか見ないため、意味の変わった版は検出できない（固定で防ぐ）
- **Q3 停止キーの効き方**: 送信の最中に押した停止キーは、今の送信（長い text の 1 行など）が終わってから効く（推奨 = 受容。送信の途中で止めるのは送信の作りの変更が要る）
- **Q4 押下だけのキーのリピート**: 本フェーズでは戻さない（推奨・§4）。代案 = 本フェーズで戻す（§4 にリピートありの状態表を新しく書き起こす必要がある）
- **Q5 送信の最中のキーリピート**: 送信の最中に届いた **`repeat` の押下**（押し続けによる OS の自動リピート）は、suppress は通常どおり判定するが**アクションは積まない**（推奨。長い送信の後にまとめて実行される・連鎖を防ぐ）。最初の押下（repeat でない）と離しは通常どおり積む。代案 = 全部積む（送信の外と同じ）

## §7 受け入れ条件（ドラフト）

1. 目印が有効なとき、自分の送信（hotkey・直接置換・key_hold・キーリピート・text・file_line・keyboard の `stash_state` の離し）はアプリのフックにも keyboard の押下の記録にも載らない（§3.2-2・3）
2. 目印が有効なとき、送信の最中に届いた物理の入力はフックで判定され、suppress の規則どおりに OS へ通す / 止める（§3.3）
3. 送信の最中に押したトリガー・直接置換・停止キーは今の送信の後で実行される（§3.3・Q3）。送信の最中のリピートの押下は Q5 の規則どおり
4. 置換先の送信を自分で拾うループが起きない（§3.3）
5. 差し替えの条件が揃わないときは何も差し替えず、今の挙動に戻る（§3.2-6・§3.4）
6. phase 51・52 の実機目視の項目が通る（§5）
7. tests / tests_ui / smoke が通る

## §8 スコープ外

- 押下だけのキーのリピートの復活・枠の色（Q4 推奨時。idea_54 と合わせて別フェーズ）
- Mac 対応 / 送信の途中で停止する作り（Q3）/ 送信を全部自前の `SendInput` にする作り（案 A2）
- マウスの送信（pyautogui・send_guard の対象外のまま）

## §9 正本反映（フェーズ末昇格・予定）

- `key_input.md` §7.7: :216 の「記録に載らない短い間の物理入力は拾わない」・:220-221 の取りこぼしの受容を、目印の規定（§3.2）・縮退時の受容（§3.4）・`write` の `stash_state` の受容（§3.3）へ置き換え / §7.3 :113-114（押下だけのキーの覚えた決定の「送信ガードの最中でも」・素通しの理由）/ :126（送信の素通りの記述）
- `features.md` :387（「送信は send_guard の中なので判定は起きない」）・:446-447（キーリピートとフックの関係）
- `codebase_map.md` :772（拡張キーは `is_replaying` を立てる）・`input_gateway.py`・差し替えの口の新規モジュール・`InputRouter` の注入
- 実装: `keyseq/infrastructure/input_gateway.py`・新規の差し替えの口・`keyseq/application/input_router.py`・`keyseq/presentation/app.py`（配線）・`requirements.txt`
- テスト: `tests/test_input_gateway_send.py`・`tests/test_input_router.py`・新規（差し替えの口）

## 関連

- [idea_53](../backlog/idea_53_send_without_dropping_physical_input.md) / [idea_54](../backlog/idea_54_ime_switch_on_make_only_keys.md)
- [暫定 46](46_make_only_keys.md)（凍結・§1 実機目視の NG の計測・§9 #7）
- 正本 `key_input.md` §7.1・§7.3・§7.7 / `features.md` §4.2.12・§4.6

## 改訂履歴

- v0.1（2026-10-21）: 起票
- 保留（2026-10-21）: ユーザー判断（ライブラリへの過度な依存・実害がまれ）。phase 65 は起票しない
- v0.2（2026-10-21）: 起票時 deep-reviewer「修正して採用」を反映 = 目印の読み方（ポインタ型・注入ビットも条件に）/ 縮退と `is_replaying` の削除の矛盾（有効時だけ立てない・全部揃ったときだけ入れる・`listening` で判定）/ §4 のリピート復活を別フェーズ推奨へ / `stash_state` の事実誤りと受容 / `type_unicode` の差し替えをやめる / 目印の有無を application へ注入 / 記述子で `is_replaying` を効かなくする / 正本反映の対象を列挙 / 送信ガードの用途の棚卸しを確定 / 送信の最中のリピート（Q5）/ `keybd_event` の argtypes と目印の bit 幅 / 包む側の例外 / `LowLevelKeyboardProc` の差し替えへ（`SetWindowsHookEx` を包むより 1 回の ctypes 越えで済む）/ テストの戻し方と並行の観点
