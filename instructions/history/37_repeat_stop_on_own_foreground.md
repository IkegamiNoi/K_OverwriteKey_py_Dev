# 暫定仕様 37: アプリの窓が前面のときはキーリピートしない（repeat_stop_on_own_foreground）

> 状態: **未凍結・v0.3・主入力・確定前の Codex 敵対的レビュー待ち**（v0.1 起票時 deep-reviewer「修正して採用」〔中 3・低 6〕を反映 → v0.2 → §7-1 をユーザー確定〔開始時は判定しない〕→ v0.3）。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: [idea_42](../backlog/idea_42_suppress_repeat_on_all_dialogs.md)（2026-10-11・phase 52 完了判定前レビュー〔Codex 敵対的 medium・deep-reviewer L3〕・ユーザーが次フェーズで実装を希望）。
> 番号対応: phase 53 / 暫定 37 / decisions 53。

---

## §1 目的 / 背景

key_hold のキーリピート（phase 52・`features.md` §4.2.12「キーリピート」）の最中に、**アプリ自身のダイアログ（messagebox・ファイル選択・独自ダイアログ）が前面に来たら、リピートした `enter` / `space` 等がそのダイアログを閉じる・意図しない選択をする**のを防ぐ。
phase 52 は実行系のエラーの知らせ（`show_action_error` / `_show_runtime_error`）の前で止めるだけで、UI 操作のダイアログ（保存失敗・確認・お知らせ等）は対象外だった。
**方式 = 前面ウィンドウ判定**: リピートの開始と毎回の送り直しの前に、OS の前面の窓がこのアプリのプロセスの窓かを確かめ、そうなら止める。呼び出し元（ダイアログを出す側）は変えない。
**application（`KeyRepeater`）・infrastructure（前面判定）・presentation（App の配線）。JSON の変更なし。**

### 現状監査（2026-10-11・codex-explorer + メイン実測）

- presentation のモーダル表示: `messagebox.show*` / `ask*` 155 か所・`filedialog` 16 か所・`simpledialog` 1 か所・独自 Toplevel 12 種（いずれも 28 ファイル程度に散在）。**包む共通入口は無い**（`modal.py` の `grab_modal` は独自 Toplevel の grab・フォーカスの管理）
- 独自ダイアログの多くとキー取得は `hook_controller.py:45` の `suspend_hook_for_dialog` でフックを止める → `stop_hook` → `HeldInputs.release_all` でリピートも止まる。**messagebox / filedialog の大半はフック停止を通らない**（例: `keyseq/presentation/controllers/config_io/sequence_file_io.py:89` の保存失敗）
- リピートの抑止の口 = `application/key_repeat.py` の `KeyRepeater`（`start` :40 は `_suppress_count` で断る・`_fire` :77 は世代と `_suppress_count` を見て止める・`resume_after_text` :107 は `start` を呼ぶ）。`begin_suppress` / `end_suppress` を使うのは `app.py` の `repeat_suppressed` / `_show_runtime_error` と `hook_controller.py` の `show_action_error`
- 前面の窓の取得の既存: `infrastructure/ime_control.py:44-66`（`GetForegroundWindow` → `GetWindowThreadProcessId`）/ `presentation/modal.py:16-31`（`_is_app_foreground`・メイン窓の HWND と比べる）
- フックの `on_error`（`hook_controller.py:135,198`）は開始時・custom input 有効化時の事前条件 / 登録失敗だけで呼ばれ、`after(0)` で表示する（稼働中の非同期の呼び出しは見当たらない・開始の前に `release_all` 済み）
- テストで messagebox を扱うファイル 32 個（呼び出し元を変えないため波及しない）

## §2 確定事項（ユーザー 2026-10-11）

1. **方式 = 前面ウィンドウ判定**（キー入力の行き先 = OS の前面の窓が、このアプリのプロセスの窓なら止める）。ダイアログを出す側は変えない。今後増えるダイアログも自動で対象になる
2. **止めた後は再開しない**（前面がアプリ以外に戻っても再開しない。押したままは保つ。phase 52 の知らせの扱いと同じ）
3. **アプリのメイン画面が前面のときもリピートしない**（アプリ自身へ文字を連打する用途は無い想定）
4. 「常に前面」の設定とは無関係（表示が最上位なだけでキー入力は受けないため、前面の窓で判定する）。他のアプリが前面の間にアプリがダイアログを出しても、Windows が前面を奪わせなければキーはそのアプリへ届き続けるので止めない（ユーザーがダイアログを前面にした時点で止まる）
5. **開始時（`start`・text の後のやり直し）には前面を判定せず、送り直しの発火時だけ判定する**（v0.3・起票時 deep-reviewer 中・ユーザー確定）。アプリの画面から実行したシーケンスが前面を切り替えた直後の押す行でも始まるようにするため。アプリが前面なら 1 回目の発火で止まる

## §3 判定

- **アプリの窓が前面** = `GetForegroundWindow` の窓の**プロセス ID が自プロセス**（`GetWindowThreadProcessId` → `GetCurrentProcessId` / `os.getpid()` と比較）。メイン窓・独自ダイアログ・messagebox・ファイル選択・キーボード表示の窓（`keyboard_window.py`）を区別しない
- **判定できない場合**（前面の窓が無い〔NULL〕・取得の例外・Windows 以外）は「アプリの窓ではない」として扱う（＝止めない・phase 52 までの挙動。リピートは付加機能で、判定の失敗で押す / 離すの安全側の動作は変わらないため）
- 判定は infrastructure に 1 関数で置き、`KeyRepeater` へ注入する（application は Win32 に依存しない）
- 補足: 従来のコンソール窓（conhost）から起動した場合、コンソール窓の前面でも自プロセスと判定され得る（止まるだけで害はない・Windows Terminal では起きない）。ツールチップ（`hover_tooltip.py`・overrideredirect）は前面にならない。キーボード表示の窓は `focus_force` するため対象に含めるのが妥当

## §4 実行

### 4.1 開始（開始時には判定しない・§2-5）
- `KeyRepeater.start`（§4.2.12 の開始・切替）・text の後のやり直し（`resume_after_text` → `start`）では**前面を判定しない**（従来どおり始める）。
  アプリの窓が前面なら、**1 回目の発火**（待ち 250〜1000 ms の後・§4.2）で送らずに止まる。これで §2-3（メイン画面が前面ならリピートしない）を満たす
- 理由: アプリの画面から実行したシーケンスが前面を切り替えた直後（alt+tab の hotkey 等）に押す行を送ると、開始時の判定では切替が済む前に判定して始まらず、§2-2 で二度と始まらない。発火時なら待ちの間に切替が済む

### 4.2 送り直し
- 予約の発火（`_fire`）で、世代・抑止の確認の後、**送る前に前面を確かめ、アプリの窓が前面なら止めて**終える（送らない・予約を取り直さない・再開しない）
- 前面の確認は毎回の送り直しの直前に行う（間隔 33〜400 ms ごと。`GetForegroundWindow` 等は軽い呼び出し）

### 4.3 既存の仕組みとの関係
- phase 52 の**知らせの前に止める・表示中の抑止**（`begin_suppress` / `end_suppress`）は**残す**（知らせのダイアログが前面に来ない場合でも止める・表示中の開始を断る既存の保証を変えない）
- フック停止・`release_all` 等の止める入口（§4.2.12）は変えない
- 止めるのは**リピートだけ**。押したままのキー・押す / 離すの送信・hotkey / text 等の送信は前面に関係なく従来どおり

## §5 UI

変更なし（設定は追加しない）。

## §6 責務の置き場（実装の方針）

- **前面判定** = infrastructure（例: `infrastructure/input_gateway.py` のモジュール関数 `is_own_process_foreground()`・`keyboard_repeat_timing` と同じ形）。`GetForegroundWindow() -> HWND` / `GetWindowThreadProcessId(HWND, POINTER(DWORD)) -> DWORD` の `argtypes` / `restype` を明示し、共有の `windll` の属性を書き換えない（`modal.py:15-21` と同じく `@cache` + `ctypes.WinDLL("user32")` の専用インスタンス）。例外は吸収して偽。**判定の失敗はログを出さない**（発火ごと〔33 ms〜〕に呼ばれるため）
- **`KeyRepeater`** = コンストラクタに任意の `is_blocked: Callable[[], bool] | None`（既定 None = 判定しない＝既存テストの形を保つ）を足し、`_fire` でだけ呼ぶ（`start` では呼ばない・§4.1）。呼び出しの例外は吸収して「ブロックしない」（ログは出さない）
- **App の配線** = `app.py` の `KeyRepeater(...)` の生成で `is_blocked=is_own_process_foreground` を渡す

## §7 確認事項（ユーザー判断）

なし（v0.2 の §7-1 は 2026-10-11 にユーザー確定・§2-5 へ移した）。

## §8 受け入れ条件（ドラフト）

自動テスト（偽の `after`・偽の前面判定）:
1. 前面判定が真のとき、リピートが有効な押す行で押すは送り、予約はするが **1 回目の発火で送らずに止まる**。前の対象のリピートは §4.2.12 どおり止まる（§4.1・§4.2）
2. リピート中に前面判定が真になると、次の発火で送らずに止まり、以後偽に戻っても再開しない（§4.2・§2-2）
3. text の後のやり直しで前面判定が真なら、やり直した後の 1 回目の発火で止まる（§4.1）
4. 前面判定が例外 / 未注入のときは従来どおりリピートする（§3・§6）
5. 前面判定の関数: 前面の窓のプロセス ID が自プロセスなら真・他なら偽・前面の窓が無い / 例外 / Windows 以外なら偽（Win32 の呼び出しは偽物に差し替える）（§3）
6. App の配線: `app.key_repeater` に `is_own_process_foreground` が注入されている（§6）
7. phase 52 の抑止（知らせの前に止める・表示中の抑止）の既存テストが通る。**本物の App の `key_repeater` を使う tests_ui（`tests_ui/test_key_hold_presentation.py` の抑止のテスト）は前面判定を偽に差し替える**（テストの Tk 窓が前面だと抑止が壊れていても通ってしまうため）（§4.3）
8. 既存テスト（tests / tests_ui / smoke）が通る

実機目視（ユーザー・ホスト OS）:
9. **アプリのダイアログ（例: シーケンスの保存失敗・確認）を開いたままメモ帳へ移り**、トリガーで `enter` のリピートを始めてから、ダイアログをクリックして前面にするとリピートが止まり、ダイアログが勝手に閉じない。閉じた後も再開しない（ボタン操作でダイアログを出すとメイン窓が前面になった時点で §2-3 により止まり、ダイアログの経路を区別できないため、この手順で確かめる）
10. メモ帳が前面のままリピートしている間は、従来どおり止まらずに連続入力される（phase 52 §8-12 の再確認）
11. アプリのメイン画面を前面にしてリピートが有効な押す行を実行するとリピートしない（押す・離すは効く）

## §9 スコープ外（本フェーズでやらない）

- ダイアログを出す側の変更（共通入口への置き換え・messagebox の差し替え）
- 前面がアプリ以外に戻ったときの再開（§2-2）
- 前面判定によるリピート以外の送信の抑止（押す / 離す・hotkey・text 等）
- マウスのボタンの連打・アプリ独自のリピート間隔（phase 52 のスコープ外のまま）

## §10 正本反映（フェーズ末昇格・予定）

- `features.md` §4.2.12「キーリピート」（開始・送り直しの前面判定・再開しない・「知らせのダイアログとリピート」の対象の範囲の記述〔phase 52 で「UI 操作のダイアログは対象外（idea_42）」とした行〕を更新）
- `key_input.md` §7.7 の key_hold の送信の下位項目「キーリピートの送り直し」（前面判定の取得方法・判定できない場合）
- `codebase_map.md`（phase 52 の項の `KeyRepeater` の注入に `is_blocked` を追記・前面判定の関数）
- 実装（予定）: `infrastructure/input_gateway.py` / `application/key_repeat.py` / `presentation/app.py` / テスト

## 関連

- [idea_42](../backlog/idea_42_suppress_repeat_on_all_dialogs.md) / phase 52（[暫定 36](36_key_hold_auto_repeat.md)〔凍結〕・[decisions_archive/52](../../.claude_data/state/decisions_archive/52_key_hold_auto_repeat.md)）
- 正本 `features.md` §4.2.12「キーリピート」/ `key_input.md` §7.7
