# task_06_macos_probe

## 目的

暫定 57 §4「段階 ③ の前に probe する」と §5 の「probe で決める」の各項目を Mac 実機（macOS 27.2 / arm64・Homebrew Python 3.13.18・Tk 9.1.0・pyobjc 13.0）で実測し、結果で暫定 57 を改訂する（v0.6）。
§5.3 の **JIS / US の記号キーの対応表**の確定が段階 ③（task_08 以降）の開始条件。
§8 Q1 の文言を Homebrew の Tk 9.1 へ改める（decisions 2026-11-10）。
**実測と暫定仕様の改訂のみ・アプリのコード変更なし**（測定用スクリプトはスクラッチに置き、リポジトリへ入れない）。

## 対象範囲（実測 + `instructions/history/57_mac_support.md` の改訂）

### 実測項目（暫定 57 の参照節）

1. **CGEventTap**（§5.1・§5.2）
   - 必要な権限: `AXIsProcessTrusted` と入力監視（`CGPreflightListenEventAccess`）のどちらが tap の作成・抑止に要るか。許可の対象（開発実行での親プロセス）と、許可後に再起動が要るか（同じプロセスで `CGEventTapCreate` を再試行して成功するか）
   - 抑止（コールバックが `None` を返す）で文字キーが前面アプリへ届かないこと
   - 修飾キー: `kCGEventFlagsChanged` の keycode（左右の Command / Option / Control / Shift・CapsLock・fn）と、フラグから down / up を導けるか。修飾キーを抑止した後に他アプリのフラグが残るか
   - タイムアウト: コールバックを意図的に遅らせて `kCGEventTapDisabledByTimeout` が届くまでの時間と、再有効化で復帰すること
   - 自動リピート: `kCGKeyboardEventAutorepeat` の値
   - 送信: `CGEventCreateKeyboardEvent` + `CGEventPost` で修飾つきの送信（例 Command+A）に `CGEventSetFlags` が要るか。`kCGEventSourceUserData` に印を付けた送信が自分の tap で識別できるか
2. **配送の滞留の規則の値**（§5.1）: コールバックから `queue.SimpleQueue` に積み、メインスレッドが `after` で排出する形で、メニュー表示中・窓のドラッグ中にメインスレッドが止まる時間を測り、キューの上限件数と有効期限の値を提案する
3. **フックスレッドからの Tk の呼び出し**（§4 probe 3）: tap のスレッドから `after` を呼んだときの挙動（例外・停止・遅延）
4. **`NSWorkspace.frontmostApplication` と `TIS` のスレッド条件**（§4 probe 4・§5.4）: tap のスレッドから呼べるか、前面アプリの切替を反映するか
5. **aqua の Tk**（§4 probe 2・§5.4）
   - `<KeyPress>` の `keycode` / `keysym` / `state`（記号キー・修飾キー・テンキー・英数 / かな）
   - `overrideredirect`、`winfo_id` と NSWindow の対応（`NSApp.windows()` から引けるか）
   - `iconphoto` が Dock のアイコンに反映されるか
   - 中ボタン・右ボタンの番号（`<Button-2>` / `<Button-3>`）
   - task_05b 以外の Tk 9 由来の差（長さ以外の `cget` の型・`-transparent` 等の属性）。見つかった差の修正は行わず、担当タスクを決めて記録する
6. **JIS / US の記号キーの対応表**（§5.3・段階 ③ の開始条件）: 記号キーごとに 物理キー（印字）・tap の vk・Tk の記録名（keysym / keycode）・レイアウト `jis` / `us_tkl` の id・`CGEventPost` で送ったときの入力結果。物理配列はユーザーの手元のキーボードで測り、無い配列は入力ソースの切替で代える（その旨を明記）

### 暫定 57 の改訂（v0.6）

- 上記の結果を §4（probe の結果の節を追加）・§5.1〜§5.4 に反映し、「probe で決める」を値・方式に置き換える
- §5.3 に対応表を載せる（大きければ同フォルダの別ファイルへ外出しし、§5.3 からリンク）
- §8 Q1 を Homebrew の Python 3.13 + `python-tk@3.13`（Tk 9.1）へ改める
- 実測の結果、§5 の方式を変える必要がある場合は**改訂前にユーザーへ報告して判断を受ける**（`spec_change_workflow.md`）
- 改訂後に `codex-adversarial-reviewer` を通し（phase.md レビュー方針）、指摘の採否はユーザー

## 読むファイル

1. `instructions/history/57_mac_support.md` §4・§5・§8
2. `keyseq/infrastructure/os_backend/contracts.py`（`KeyboardBackend` の docstring のフックの契約）
3. `keyseq/application/input_router.py:110-125,183-198`（`_keymap_switch_in_progress`・キー名の決定順）
4. `config/user/keylayout/jis.json`・`us_tkl.json` の `keys`（id と `scan_code`）
5. `instructions/common/spec_detail/key_input.md` §7.1（キー名の語彙）

## 含まない

- tap・送信・キー表の実装（task_08・task_09）、権限の案内の UI（task_10）
- Tk 9 の差で見つかったものの修正（担当タスクを記録するのみ。tests_ui の sashwidth は task_07）
- 既定プリセットの注入・macOS のテストの基準線（task_07）
- PyInstaller の確認（task_13）

## 確認

- 実測項目 1〜6 の結果が暫定 57 に記録され、「probe で決める」が残っていない（残す場合は理由と担当タスクを明記）
- 対応表が JIS / US の記号キーを網羅している（`jis.json` / `us_tkl.json` の記号キーの id がすべて載る）
- §8 Q1 が Tk 9.1 の記述になっている
- `codex-adversarial-reviewer` の指摘をユーザーが採否判断し、採用分を反映した

## 完了条件

- 上記確認・**reviewer 採用**（暫定 57 の改訂の差分と実測の根拠）。
- 実機目視: 本タスクで実施（ユーザーの打鍵・権限の許可・Dock の確認）。
