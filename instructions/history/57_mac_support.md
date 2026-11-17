# 暫定仕様 57: macOS 対応（mac_support）

> 状態: **未凍結・v0.15・主入力（ユーザー確定済・実装着手可）**。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: ユーザー要望（2026-11-09）。番号対応: phase 75 / 暫定 57 / decisions 75。
> 版: v0.1 起票 → v0.2 deep-reviewer「修正して採用」の H1〜H6・M1〜M8・L1〜L5 を反映 → v0.3 §8 Q0〜Q8 をユーザー確定 → v0.4 Codex 敵対的レビューの 3 件（配送の滞留・独自レイアウトの送信・JIS の記号キー）を反映（ユーザー 2026-11-09）→ v0.5 v0.4 の再レビュー（Codex 敵対的）の 1 件 = アクションを捨てるときの状態の復元を反映（ユーザー 2026-11-10）→ v0.6 task_06 の probe の結果を §4.1 に記録し §5・§8 Q1・Q4・§9 を改訂（ユーザー 2026-11-11: IME は取得中に TIS で英字へ切替・JIS 専用キーは文書値で段階 ③ へ）。続けて Codex 敵対的レビューの 4 件（修飾キーのフラグの左右別・送信フラグの分離・TIS 切替の失敗と戻し方・NSWindow の取り違え）を反映し §9 に 11・12 を追加（ユーザー 2026-11-11）。 → v0.7 ディスパッチャの契約を §5.1.1 に追加（段階 ① の区切り M1・M2。task_08 を OS 非依存の受け渡し〔task_08〕と CGEventTap〔task_08b〕に分割・ユーザー 2026-11-13）。続けて Codex 敵対的レビューの 3 件（あふれた後の素通しの継続 = 過負荷の印・世代の不一致では on_discard を呼ばない・取得のフックの受付拒否）を反映。再レビューの 3 件（受付拒否したキーの up まで素通し・優先の処理にフックの稼働番号・切替の予約番号）を反映。3 回目の 1 件（素通し中のキーがある間は取得のフックを解除しない）を反映して確定（ユーザー 2026-11-13）。 → v0.8 Mac 用のレイアウトの見本 2 つ（`us_mac` / `jis_mac`）を §5.3.2 に追加・fn は置かない（ユーザー 2026-11-14）。続けて Codex 敵対的レビューの 1 件（§9 の 13 と Q5 の Command の割り当て禁止の矛盾）とメインの確認 1 件（JIS の判定に jis_mac を含める）を反映・CapsLock は禁止の色で置く（ユーザー 2026-11-14）。 続けて task_09 の起票レビューの 1 件（物理の Shift が押されているときの Shift の要る文字の送信）を §5.1 に反映（ユーザー 2026-11-14）。 → v0.9 task_09a の Mac 目視を受けて §5.1 の送るフラグを「物理側（押されていて抑止中でない）+ 送信側（自分が down を送った）」に改訂（ユーザー 2026-11-14）。 → v0.10 修飾キーの表示名の適用範囲を §5.3.3 に追加（task_09a の Mac 目視・ユーザー 2026-11-14）。 → v0.11 Mac の修飾キーのキー名を `command` / `option` に分け（§5.3.4）、§5.3.3 の表示名の差し替えを廃止・§8 Q2・Q7 と §5.3.2 を改訂（task_09c の Mac 目視・ユーザー 2026-11-15）。Codex 敵対的レビュー 3 回（Windows でも `command` / `option` を拒否する互換性の変更・置換元の受付の口・トリガー / hotkey / `key_hold` の拒否の時点・修飾キー単独の読み飛ばし・`key_hold` の全キー名の検査の維持）を反映して確定（ユーザー 2026-11-15）。 → v0.12 task_09b の Mac 目視を受けて §5.3.2 を改訂: fn を禁止のキーとして置く・矢印は右 Shift の下・jis_mac の右 Option の位置は fn（ユーザー 2026-11-15）。続けて §5.1 に Windows で作った Caps Lock の切替キーが Mac で拒否されることを記録（ユーザー 2026-11-15）。§5.2 に task_10 の実測（同じプロセスでの再試行が成功）を記録（2026-11-15）。 → v0.13 task_11 の Mac 目視を受けて §5.4 のリピート間隔の取得元を NSEvent からグローバル設定の `InitialKeyRepeat` / `KeyRepeat` に変更（ユーザー 2026-11-15）。 → v0.14 task_11a の Mac 目視を受けて §5.4 のマウス操作を改訂: 回数つきのクリック・ドラッグ・押したままの移動を Quartz で送る・横スクロールの符号（ユーザー 2026-11-15）。 → v0.15 task_11b の起票前の実測で §4.1・§5.4 の NSWindow の引き方を `Tk_MacOSXGetNSWindowForDrawable` に訂正・§3.2 に `make_click_through_overlay` の透明色を追加・`Capabilities` の無効化の UI は目視で動かない機能が見つかったときに起票（ユーザー 2026-11-16）。 → v0.16 task_11b の Mac 目視を受けて §3.2・§5.4 のクリック透過を改訂: aqua は透かす色を黒に塗り替え、窓全体を半透明（`-alpha` 0.5）にする（Tk 9.1 は `-transparent` の窓に描画すると透明の部分が不透明な黒になると実測・ユーザー 2026-11-16）。 → v0.17 task_11c の起票前の実測で §5.4 に「最小化とモーダル」の行を追加（ユーザー 2026-11-16）。 → v0.18 task_11e の起票前の実測で §5.4 に「最前面とモーダル」の行を追加し、Mac 目視の後にモーダルの間はメインの最前面を外す作りへ改訂（ユーザー 2026-11-17）。 → v0.19 task_11f の起票前の実測で §5.4 に「メッセージの窓」の行を追加（ユーザー 2026-11-17）。 → v0.20 §5.3.4 の割り当て禁止の文言を両 OS 共通に決定（task_11d・ユーザー 2026-11-17）。 → v0.21 §6.1 にレイアウトの見本のコピーの時機（keylayout のフォルダが無いときだけ）と `app_data_root` の開発実行時の値を追加（task_12 の起票・ユーザー 2026-11-17）。 → v0.22 §6.3 を追加（配布物の中身とライセンスの表示 = 表の OS 列・アイコンは既定・見本は 5 本・README の記載・ユーザー 2026-11-18）。続けて Codex 敵対的レビューの 2 件（pynput の差し替えは onedir だけでは成り立たない・GPL / LGPL の依存の対応するソース）を反映（ユーザー 2026-11-18）。再レビューは approve（残りの確認は task_13a / 13 / 13b の確認項目へ）。

---

## §1 目的 / 背景

Windows 専用で動いている keyseq を macOS でも同様に動かす。OS ごとの実装を切り分け、Windows / macOS それぞれでアプリとしてビルドできるようにする。

### 現状監査（2026-11-09・macOS 27.2 / arm64 で実測）

- `.venv` の Python 3.15 は `_tkinter` を読み込めず GUI が起動しない。
- `keyboard` のフックは macOS では `OSError: Error 13 - Must be run as administrator`。`_darwinkeyboard.py` に suppress の実装は無い（grep 0 件）。
- `tests` は 1758 件実行・失敗 53・エラー 37・skip 9（Windows の実績は 1951 件）。原因は `_tkinter` のロード失敗、`keyboard` の `Unknown key name`、`ctypes` の属性欠如、パス区切りの差など（レビュー時の分析）。
- ビルド設定と `.ico` / `.icns` は追跡ファイルに無い。Windows のビルドも新規に用意する。
- Win32 の実体: `infrastructure/win32_window.py`、`input_gateway.py`（`SendInput` / `keybd_event` / `SystemParametersInfoW`）、`ime_control.py`、`own_ime_status.py`。`keyboard` の import は `input_gateway.py` のみだが、private API（`_os_keyboard`:63、`_listener`:157,199）にも依存する。
- infrastructure の外から Win32 依存に触れる箇所:
  - `presentation/modal.py:18`（`WinDLL` の直接呼び出し）
  - `win32_window` の import: `main.py:5`、`presentation/app.py:104`、`keyboard_window.py:15`、`screen_grid/grid_overlay_window.py:7`、`screen_grid/screen_grid_controller.py:10`、`controllers/keymap_panel/keymap_panel_controller.py:13`
  - `own_ime_status` の import: `presentation/key_capture_ime.py:8`
  - `presentation/tk_keys.py:36` `numpad_name_from_tk_event`（Windows の Tk keycode と extended ビットが前提）
- `pynput` の利用は `action_dialog.py:7` の `mouse` のみ。
- **キー名の決定順**（`application/input_router.py:183-198`）: テンキー → レイアウトの `scan_code` → `event.name`。レイアウトの `scan_code` は jis 6 行・jis_test 4 行のみで us_tkl / de は 0 行。多くのキーは `event.name` で決まる。保存データもキー名。
- テンキーと拡張キーは走査コードが重複し、`is_keypad` と extended の組で区別する（`domain/numpad_keys.py`、`input_gateway.py:432-445`）。
- フックスレッドから `after` を直接呼んでいる（`presentation/controllers/hook_controller.py:307`）。
- 設定の場所は `__file__` 基準（`presentation/app.py:117-119`）。再起動は `[sys.executable, *sys.argv]`（`infrastructure/app_relaunch.py:10`）。どちらもビルド後は成立しない。
- 既定プリセットは domain に定数で持つ（`domain/config.py:34-38` 等）。
- Tk: `grid_overlay_window.py:40` の `-transparentcolor` は Windows 専用の属性。

## §2 確定事項（ユーザー 2026-11-09・方針承認）

- **4 段階で進める**: ①OS 境界の整備（Windows の動作は不変）→ ②macOS で起動 → ③macOS の入力実装 → ④ビルド。
- **macOS の入力は `pyobjc` の CGEventTap で実装する**。`pyobjc` の追加は macOS のみ。**Windows の入力は `keyboard` のまま変えない**。
- **修飾キーは `Win` → `Command` に対応させる**。
- **macOS で再現できない機能は、代替を調べたうえで、無理なものは macOS で無効にして仕様に明記する**。
- **ビルドは PyInstaller**。Windows は `.exe`、macOS は `.app`。クロスビルドはせず、それぞれの OS で実行する。
- **署名はまずアドホック署名**。Apple Developer の証明書による配布は本フェーズの対象外。

## §3 OS 境界（段階 ①）

### §3.1 配置

```text
keyseq/infrastructure/os_backend/
  __init__.py      # get_backend(): sys.platform で実装を選ぶ（keyseq/ 内の唯一の分岐点）
  contracts.py     # Protocol と Capabilities
  windows/         # win32_window / ime_control / own_ime_status と keyboard 利用部の移動先
  macos/           # 段階 ② でスタブ、段階 ③ で実装
```

- `sys.platform` の分岐は **`keyseq/` 内では** `os_backend/__init__.py` の 1 か所に限る。テストの `skipUnless` は対象外。Tk の差は `tk windowingsystem` で判定する（§4）。
- Win32 と `keyboard` の import は `windows/`、`pyobjc` は `macos/` に閉じる。選ばれた OS でだけ import する。
- 旧パスの横流しモジュールは残さない（`file_organization_rules.md`）。
- presentation は `os_backend` の公開面だけを参照する。

### §3.2 境界（Protocol）

| 境界 | 責務 | 現在の実体 |
|---|---|---|
| `KeyboardBackend` | フック登録・解除（抑止つき）、押下・解放・ホットキー・文字送信、キー名の検証と解決、送信の種別（`KeySend.kind`）、`identity_of`、Shift 要否（`_needs_shift`）、自分の送信の判定、リピート間隔（`keyboard_repeat_timing`） | `input_gateway.py` |
| `MouseBackend` | カーソル位置・移動、クリック、ドラッグ、スクロール、クリック位置の取得（`action_dialog.py` の用途） | `input_gateway.py`、`action_dialog.py` |
| `WindowBackend` | 自プロセスが前面か・前面の自窓、モニタ一覧、クリック透過の窓、窓の重なり順、物理状態（`is_mouse_button_down` / `is_shift_down` / `is_ctrl_alt_win_down`） | `win32_window.py`、`modal.py` |
| `TkKeyTranslator` | Tk イベントの解釈（テンキー名・VK → 走査コード・VK → 文字・修飾 keysym） | `tk_keys.py`、`win32_window.vk_to_scan_code` / `vk_to_char` |
| `ImeBackend` | 文字送信時の IME 制御、キー取得時の自アプリの IME 制御 | `ime_control.py`、`own_ime_status.py` |
| `AppIdentity` | 起動時の OS 固有設定、設定のルート（§6.1）、アプリの再起動 | `win32_window.set_app_user_model_id`、`app_relaunch.py` |

- `InputGateway` の公開メソッドは維持し、application から見た契約を変えない。
- 窓を受ける API は **Tk の窓オブジェクトを引数にする**（HWND の int を Protocol に出さない）。Windows 実装の内部で HWND に変換する。
- モニタ一覧の座標は左上原点・Tk と同じ座標系を契約とする（`NSScreen` は実装内で変換する）。
- **v0.15**: クリック透過は `make_click_through_overlay(window, transparent_color)` とし、「`transparent_color` で塗った部分を透かし、窓全体をクリック透過にする」までを backend が持つ（Windows = `-transparentcolor`・aqua = **v0.16** 透かす色を黒に塗り替えて窓全体を `-alpha` 0.5 の半透明にする〔下が暗く透けて見える・線と文字も半透明〕。presentation で OS を見ないため）。`window_handle` は引けなければ None。
- `Capabilities`（dataclass）は OS ごとに無い**機能**を宣言し、presentation が UI を無効化するのに使う。**v0.15**: macOS はクリック透過・窓の重なり順を実装するので True にする（根拠 = task_11b の Mac 目視）。無効化の UI は、目視で動かない機能が見つかったときに起票する（それまでは、作れないときの今の失敗の経路〔カーソルグリッドが始まらず通知〕を無効化とみなす）。
- フックスレッドから UI スレッドへの受け渡しは、注入するディスパッチャで行う（契約は §5.1.1）。Windows は現状の `after` のまま。

### §3.3 段階 ① の進め方と不変条件

- Windows の動作とテスト件数を変えない（tests 1951 / tests_ui 1270 / smoke pass）。patch 先の変更は許容し、テストの削除で件数を減らさない。
- テストの 29 ファイル・約 340 箇所が移動対象を参照するため、次の順に分けて**タスクごとに Windows の標準検証 4 種をゲートにする**: ime / own_ime → win32_window → input_gateway の分解 → presentation の切替。
- Mac で取れる保険として次を追加する: AST による import 境界の検査（§10-1 の自動化）、公開シンボルと Protocol の一致テスト。

## §4 macOS で起動（段階 ②）

- Tk を使える Python の `.venv` を用意する（Q1）。
- 依存を環境マーカーで分ける（`keyboard; sys_platform == "win32"` 等）。
- Tk の差分は `tk windowingsystem` で判定し、presentation の 1 か所にまとめる:
  - 右クリックは Tk 9 の aqua でも `<Button-3>`（§4.1）。右クリックの切替は不要（task_05c で task_05 の切替を撤去）。中クリックは未実測で、既存の `<Button-2>` のバインドのまま task_11 で確認する。
  - メニューのアクセラレータと範囲選択等の `Control` バインドは aqua では `Command`。
- **段階 ③ の前に probe する**（結果は §4.1。v0.6 で §5 を改訂済み）:
  1. CGEventTap の修飾キー（§5.1）、抑止、タイムアウト、必要な権限
  2. aqua の Tk の `keycode`、`overrideredirect`、`winfo_id` と NSWindow の対応
  3. フックスレッドからの Tk 呼び出し
  4. `TIS` / `NSWorkspace` のスレッド条件
- Windows 専用テストは `skipUnless` を付ける。macOS のテスト基準は §7。

- Mac のフォント（`.AppleSystemUIFont`）は Windows より大きく、次の 2 点を変える（ユーザー判断 2026-11-12・task_07d）: ①起動時の既定の窓の高さ = `max(820, 3 枠がスクロールバーなしで収まる高さ)`（画面の高さ〔`wm_maxsize`〕で頭打ち）。**aqua のときだけ適用**し、Windows は従来どおり 820（フォントの増分・低い画面でも変えない。段階 ② の区切り M3・ユーザー判断 2026-11-13・task_07e）②キーボードUIのキーの文字のフォントは aqua では Helvetica（既定のフォントでは仕様の下限 7px でも「Home」が 1u = 27px のキーに収まらない。下限 7px は変えない）。

### §4.1 probe の結果（task_06・2026-11-11）

環境: macOS 27.2 / arm64・US 配列の内蔵キーボード・Homebrew の Python 3.13.18・Tk 9.1.0・pyobjc 13.0。入力ソースはことえり（ローマ字入力）。

| 項目 | 結果 | 反映先 |
|---|---|---|
| 権限 | 未許可では active の tap（`kCGEventTapOptionDefault`）の `CGEventTapCreate` が NULL。listen-only は作成だけ成功する。作成の試行でシステムの許可ダイアログが出て、許可後に**新しいプロセス**では作成に成功した。開発実行での許可の対象は親のアプリ（Claude / ターミナル） | §5.2 |
| 抑止 | コールバックが `None` を返すと、そのキーは前面アプリ（Tk）へ届かない | §5.1 |
| 修飾キー | `kCGEventFlagsChanged` の keycode は 左 Command 55・右 Command 54・左 Shift 56・右 Shift 60・左 Option 58・左 Control 59・fn 63（右 Option 61・右 Control 62・CapsLock 57 は未実測）。左右はフラグの機種依存ビット（左 Command `0x08`・右 Command `0x10`・左 Shift `0x02`・右 Shift `0x04`・左 Option `0x20`・左 Control `0x01`）で区別できる | §5.1 |
| 修飾キーの抑止 | Command の FlagsChanged を抑止しても、**続く文字キーのイベントには Command のフラグが付いたまま届き**、前面アプリは Command+文字として扱った。その離しも抑止すると、セッションの修飾状態に Command が残り、別のアプリで通常の入力ができなくなった（ユーザー目視） | §5.1 |
| タイムアウト | コールバックが 1.5 秒かかる呼び出しが 2 回続くと `kCGEventTapDisabledByTimeout` が届いた（1 回では届かない）。`CGEventTapEnable(tap, True)` で 4 回とも復帰した | §5.1 |
| 停止時の通知 | 自分で `CGEventTapEnable(tap, False)` したときも `kCGEventTapDisabledByUserInput` がコールバックへ届く | §5.1 |
| 送信 | `CGEventSetFlags` で Command を付けた文字キー単体、Command キーの down / up で挟んだ文字キーのどちらも Command+文字になった。`kCGEventSourceUserData` に付けた印は自分の tap で読めた | §5.1・§5.4 |
| 自動リピート | 文字キーの長押しで、最初の keyDown は `kCGKeyboardEventAutorepeat` = 0、続くリピートの keyDown は 1（task_08b・2026-11-14） | task_08b（リピートも `down` で渡す） |
| 修飾キー（task_08b・2026-11-14） | 右 Command 54 / `0x10`（共通ビット `0x100000`）・右 Shift 60 / `0x04`・左 Shift 56 / `0x02`・左 Control 59 / `0x01` を再確認。手元の内蔵キーボードには**右 Option・右 Control のキーが無い**ため 61 / `0x40`・62 / `0x2000` は文書値のまま（外付けキーボードで実測できたら追記）。**CapsLock を 2 回押しても listen-only の tap に FlagsChanged（vk 57）は 1 件も届かなかった**（入力ソースはことえり。CapsLock が入力ソースの切替に割り当てられている等の可能性・原因は未確定）。CapsLock は常に素通しのため実装への影響は無い | task_08b |
| スレッド | tap のコールバック（CFRunLoop のスレッド）から `NSWorkspace.frontmostApplication` と `TISCopyCurrentKeyboardInputSource` を呼べ、前面の切替にも追従した | §5.4 |
| Tk の `after` | mainloop 中にメインスレッドが 1.5 秒止まると、別スレッドからの `after` の呼び出しも約 1.3 秒ブロックした。mainloop の外では `RuntimeError` | §5.1 の根拠 |
| メインスレッドの停止 | メニューを開いたまま・窓のドラッグ中もメインスレッドの `after(10)` の刻みは 0.2 秒以上止まらず、キューの排出の遅延は最大 0.047 秒 | §5.1 |
| Tk の `keycode` | aqua では `(vk << 24) | …| 文字コード`（例 `;` = `0x2900003B`・`a` = `0x61`）。**IME がかな入力のときは上位 8 ビットが `0xFF` になり vk が失われる**（keysym も `prolongedsound`・`??` 等） | §5.3・Q4 |
| Tk の修飾 keysym | Command = `Meta_L` / `Meta_R`、Option = `Alt_L`、Control = `Control_L`、Shift = `Shift_L` / `Shift_R`、fn = `Super_L` | §5.3（task_09） |
| マウスのボタン | 右クリック = `<Button-3>`（中クリックは未実測） | §4 |
| fn | fn 単独の押下・離しで FlagsChanged（vk 63・フラグ `0x800000`）に加えて vk 179 の down / up が届く。F キー（例 vk 109）には fn のフラグ `0x800000` が付く | task_08（fn を修飾キーと誤認しない） |
| 未実測 | 右 Option 61・右 Control 62（キーの無い機種・task_08b で確認できず）→ 外付けキーボードを用意できたとき。CapsLock 57 が届く条件（task_08b で届かず）→ 必要になったとき。テンキーの vk・Tk の keycode（手元に無い）→ task_09。英数 / かな・JIS 専用キーの受信と Tk の記録（US 配列の機種）→ JIS キーボードを用意できたとき（§9 の 10）。中クリックの番号（押していない）→ task_11 | 各タスク |
| Dock のアイコン | `iconphoto` で Dock のアイコンが変わる（ユーザー目視） | §5.4 |
| 窓 | `overrideredirect` は効く。`winfo_id` / `wm frame` の値を pyobjc のオブジェクトとして扱うとプロセスが落ちる。NSWindow は `NSApp.windows()` の `TKWindow` の位置（Cocoa の座標は下が原点）で対応が取れた（**v0.15 で訂正: 位置の照合は使わない。Tk の公開の C 関数 `Tk_MacOSXGetNSWindowForDrawable` を ctypes〔`CDLL(None)`〕で引き `winfo_id()` を渡すと、同じ位置・大きさの窓でも別の NSWindow が返った・一度も表示していない窓の `windowNumber` は -1・task_11b の起票前の実測 2026-11-16**）。`wm attributes` に `-transparentcolor` は無く `-transparent` がある | §5.4（task_11） |
| Tk 9 の長さ | task_05b の Canvas・PanedWindow の `sashwidth` のほか、PanedWindow の `handlepad` / `handlesize`、Scale の `length` / `sliderlength` / `width` も単位つき。アプリはこれらを使っていない（grep 0 件） | 対応不要 |

## §5 macOS の入力（段階 ③）

### §5.1 フックとスレッド

- 専用スレッドで CFRunLoop を回し、**単一の CGEventTap**（active）を実行する。`register_global_hook` / `register_key_hook` の重ね合わせは backend 内で合成する。
- 抑止の判定はコールバック内で同期で完結させる。**コールバックから Tk を呼ばない**。アクションと UI 更新は `queue.SimpleQueue` に積み、メインスレッドが排出する（Tk の `after` がメインスレッドを待つと、メニュー表示中などにコールバックが止まり全キー入力が遅延するため）。
- **配送の滞留の規則**（UI が止まっている間の入力を後からまとめて実行しない）:
  - キューに上限件数と有効期限を設ける。**上限 = 64 件・有効期限 = 1.0 秒**（積んだ時刻から排出時刻まで。§4.1 で通常の遅延は最大 0.05 秒・メニュー表示中とドラッグ中もメインスレッドは止まらなかったため、期限切れは重い処理などの異常時だけに起きる値とする）。期限切れのアクションは実行せず捨てる。
  - **アクションを捨てるときは、予約時に変更した状態を必ず元に戻す**。`SelectKeymapAction` は `_keymap_switch_in_progress` を解除する（立ったままだと `input_router.py:118` で通常の入力が素通しのままになる）。**期限切れ**で捨てるときは、捨てる側が戻す。ただし印は停止以外（入力の無効化 `toggle_custom_input_enabled` 等）でも下ろされ、その後に別の予約が立ちうるため、**予約ごとに番号を持たせ、期限切れで印を下ろすのは自分の番号が現在の予約番号と一致するときだけ**とする（v0.7）。**世代の不一致**で捨てるときは、世代を更新した側（フックの停止。`stop_hook` / `start_hook` は印を先に下ろす）が戻し、捨てる側は何もしない。切替の実行が終わったときの印の解除（`action_executor`）は従来どおり（Windows と同じ・本書の対象外）。
  - フックの停止のときは世代を更新し、古い世代のアクションを捨てる。tap の障害・権限の喪失はフックの停止として扱う（世代の更新は停止の処理の中で行う）。
  - 上限を超えたら新規の抑止をやめて素通しにし、フックを停止状態へ移して知らせる。停止が実行されるまでの間も、以後の入力はすべて素通しにする（§5.1.1 の過負荷の印）。
  - 停止キーとフックの停止の通知は、通常のアクションのキューとは別の経路で優先して処理する。
  - 上記の受け渡しの契約は §5.1.1。
- 例外時は素通しにする（抑止しない）。解除時は tap を無効化して CFRunLoop を止める。
- `kCGEventTapDisabledByTimeout` / `ByUserInput` を受けたら tap を再有効化し、**無効化中に解放を取りこぼした可能性があるため押下状態を掃除する**。ただし backend 自身が停止のために無効化したとき（§4.1: 自分の無効化でも `ByUserInput` が届く）は再有効化しない。停止は tap の参照を先に外してから無効化し、コールバックは参照が無ければ何もしない。
- コールバックは同期の判定だけで即座に返す（§4.1: 1.5 秒の遅延が 2 回続くとタイムアウトで無効化された）。
- Secure Input 中はイベントが届かない。この間はフックの動作を保証しない。
- 自分が合成したイベントは `kCGEventSourceUserData` の印で識別する。Windows の送信時ガードと同じ契約を `KeyboardBackend` で満たす。
- **修飾キー**は `kCGEventFlagsChanged` で届くため、keycode（§4.1）とフラグの機種依存ビットから左右別の down / up を導いて上位へ渡す。CapsLock は別扱い: **常に素通し**し、上位へは表に無いキーと同じく `name=""` で渡す（macOS では CapsLock を元キーに割り当てられない・ユーザー判断 2026-11-13・task_08b）。Mac のキー表に `caps lock` は無いため、Windows で作った設定にある `caps lock`（切替キー・停止 / トグルキー・置換先・出力・個別読込 / 貼り付けで持ち込む切替キー）は、Mac では不明なキーとして検査（`validate_key_name`）や実行時に拒否される（切替キーを変えずに確定しても拒否・その切替キーは Mac では元々動かない・§8 Q8 の非保証の範囲・ユーザー判断 2026-11-15）。
- **修飾キーの抑止とフラグ**（§4.1: FlagsChanged の抑止だけでは後続のキーに Command が付いたまま届き、セッションの修飾状態に残って別アプリの入力が壊れた）:
  - backend は修飾キーごとに**左右別に**「物理的に押されている」「抑止中（down を抑止した）」を持つ。修飾キーの down を抑止したら対になる up も抑止し、両方を通すか両方を止めるかを揃える。
  - 送るフラグの元になる修飾は 2 つ（どちらも左右別）: **物理側** = 物理的に押されていて抑止中でない修飾 / **送信側** = backend が自分で down を送り、まだ up を送っていない修飾（置換先の修飾キー・ホットキーの挟み・`key_hold` を含む）。機種依存ビットは両者の和の側だけ、共通ビット（Shift・Control・Option・Command）は和の左右のどちらかがあるときだけ立てる。Windows で OS が持つ修飾の状態（抑止したキーは OS に届かず、自分が送った down は届く）に揃える（v0.9・ユーザー 2026-11-14・task_09a の Mac 目視: 修飾キーを置換先にした割り当てと、物理の Command / Shift + 置換したキーが効かなかった）。
  - **通過させる物理キーのイベント**（自分の印が無いもの）は、フラグを `CGEventSetFlags` で「物理側 + 送信側」に付け直す。例: 左 Shift を抑止中で右 Shift を素通しで押している → 共通の Shift と右 Shift のビットは残る。`y` → `shift` の置換で `y` を押している間に押した物理の `a` には Shift が付く。
  - **自分が送るイベント**（印つき）のフラグも「物理側 + 送信側」で決める。抑止中の物理の修飾は混ざらない。例: `ctrl` を元キーにして抑止しながら `ctrl+c` を送る → 送る `c` には（挟みの）Control を付ける。物理の Command を押したまま `a` → `b` の置換キーを押す → 送る `b` に Command を付ける。
  - 例外: Shift の要る文字（例 `!`）を送るときに物理の Shift が押されていれば（アプリが Shift を足さない場合・phase 74）、送るキーに Shift の共通ビットを付ける（Windows では OS の Shift の状態が効いて `!` になるのと揃える。v0.8・ユーザー 2026-11-14・task_09 の起票レビュー。v0.9 で物理側を混ぜる規則に含まれるが、物理の Shift が抑止中でも付ける点だけが残る）。
  - 文字の送信（`write_text` = Unicode の文字列のイベント）のフラグは送信側だけにし、物理側を混ぜない（物理の Command 等が付くと文字入力がショートカットになるため。v0.9・task_09a の目視後の修正の reviewer 指摘）。
- 送信の修飾は、修飾キーの down / up を合成して挟む方式（Windows と同じ）とし、送るキーのフラグは上記で決めた値を `CGEventSetFlags` で明示する（§4.1: 挟むだけでも指定だけでも有効だったが、抑止中の物理の修飾が混ざらないように明示する）。
- 自動リピートは `kCGKeyboardEventAutorepeat` で判定し、Windows と同じく down を繰り返して渡す（値は §4.1 で未確認・task_08 で実測する）。

### §5.1.1 ディスパッチャの契約（v0.7・段階 ① の区切り M1・M2）

フックのコールバック（フックのスレッド）から UI スレッドへ処理を渡す口。presentation に置き、App の組み立てで 1 つ作って `HookController` と `KeyCaptureHook` に渡す。

- 呼び出し: `dispatch(run, *, on_discard=None, priority=False) -> bool`
  - `run`: UI スレッドで 1 回だけ実行する処理。
  - `on_discard`: `run` を**期限切れ**で実行せずに捨てたときに、UI スレッドで 1 回だけ呼ぶ。世代の不一致で捨てたときは呼ばない（§5.1: 世代を更新した停止の処理が状態を戻す）。`run` と `on_discard` の両方が呼ばれることはない。
  - `priority`: 停止キー（`StopHookAction`）とフックの停止の通知に使う。通常のキューとは別に持ち、排出のたびに通常のキューより先に処理する。上限・期限・世代の対象外（捨てない）。ただし呼び出し側は、積んだときの**フックの稼働番号**（`HookController` が `start_hook` のたびに進める）を `run` に持たせ、実行時に番号が変わっていれば何もしない（停止と再開の後に、古い停止の要求が新しいフックを止めないため・v0.7）。
  - 戻り値 `False` = 受け付けなかった（通常のキューが上限 64 件に達している）。`run` も `on_discard` も呼ばれない。
- `invalidate()`: 世代を更新する。それまでに受け付けた通常の処理は、排出時にすべて捨てる（`on_discard` は呼ばない）。`HookController.stop_hook` の中でだけ呼ぶ（tap の障害・権限の喪失もフックの停止として扱う）。
- 呼び出し側（`HookController.on_input_event` と押下だけのキーの経路）:
  - `SelectKeymapAction` には `on_discard` として、予約番号が一致するときだけ切替中の印（`_keymap_switch_in_progress`）を下ろす処理を渡す（§5.1 の「捨てるときの復元」）。予約番号は `HookController` が `SelectKeymapAction` を渡すたびに進める。他のアクションは `on_discard` なし。
  - `StopHookAction` は `priority=True`。
  - `dispatch` が `False` を返したら、**過負荷の印**をその場（フックのスレッド）で立て、同じ経路の残りのアクションは渡さず、そのイベントは素通し（`accept = True`）にし、フックの停止を `priority=True` で 1 回だけ渡す。印が立っている間、`on_input_event` は先頭で全イベントを素通しにし、振り分け（`input_router` と押下だけのキーの経路）も呼ばない（押下だけのキーの経路が保存済みの `accept=False` を返し続けるのを避けるため）。印は `start_hook` で下ろす。停止で `invalidate()` が呼ばれ、すでに積んだ処理は捨てられる。即時版は `False` を返さないため、この経路は通らない。
  - `KeyCaptureHook` は取得したキーの受け渡し（コールバックからの `after(0, …)`）をディスパッチャに替える。`dispatch` が `False` を返したら、その走査コードを**素通し中**として記録し（取得済みの記録 `_pressed` とは別・`_pressed` には残さない）、そのイベントと、同じ走査コードの以後のイベント（リピートの down を含む）を対になる up まですべて素通し（抑止しない）にする。素通し中のキーは、取得の終了（`deactivate()`）と待ちの確認で押下中のキーと同じに数え、ある間はフックを解除しない（上限は既存の 5 秒）。素通し中の記録を消すのは、その up と、フックを実際に解除したとき（`shutdown` を含む）だけ（解除後は OS がそのまま流すので down と up の対は崩れない）。取得は一時的なのでフックは止めない。UI スレッドから呼ぶ待ちの確認（`after(100, …)`）は `after` のまま。
- 実装は 2 つ。どちらを使うかは `OsBackend` の項目 `queued_hook_dispatch: bool`（Windows `False` / macOS `True`）で決める（`sys.platform` を見ない）。
  - **即時版**（Windows）: `run` を `after(0, run)` で渡す。常に `True` を返し、捨てない（`on_discard` を呼ばない）。`priority` は無視し、`invalidate()` は何もしない。Windows の動作は変わらない。
  - **キュー版**（macOS）: `queue.SimpleQueue` を通常用と優先用の 2 本持ち、積んだ時刻と世代を添える。UI スレッドが `after` で **10 ms ごと**に排出する（§4.1 の probe と同じ刻み）。排出は優先用をすべて処理してから、その時点で通常用にあるものを処理する。積んだ時刻から 1.0 秒を超えたものは `on_discard` を呼んで捨て、世代が違うものは呼ばずに捨てる（世代の判定を先に行う）。件数の上限は通常用だけに数える。コールバックから Tk を呼ばない。
  - `run` / `on_discard` の例外はログに残して吸収し、排出を続ける。

### §5.2 権限

- 起動時に権限を確認する（`AXIsProcessTrusted`）。active の tap は未許可だと作成できない（§4.1）。判定は `AXIsProcessTrusted` と `CGEventTapCreate` の成否で行い、入力監視（`CGPreflightListenEventAccess`）は案内の文言で触れるだけにする（§4.1 では両方同時に許可され、個別の要否は切り分けていない）。
- 未許可、または `CGEventTapCreate` が NULL のときは既存の `start_hook` の失敗経路（`hook_controller.py`）に乗せ、案内ダイアログからシステム設定の該当画面を開けるようにする。
- 許可後は「フック開始」の再操作で再試行する。同じプロセスでの再試行が成功するかは §4.1 で未確認（新しいプロセスでは成功）。task_10 で実測し、失敗する場合は再起動を案内する。→ **task_10 の Mac 目視（2026-11-15）: 許可後に同じプロセスで「開始（フックON）」を押し直すと開始できた**（案内の本文の再起動は、それでも開始できない場合の予備として残す）。稼働中にアクセシビリティを外しても、その場では tap の無効化の知らせが来ない。外した後の最初のキー入力で知らせが来てフックが止まり、案内が 1 回出る（そのキー入力はトリガーとして実行されず素通し・§5.1 の例外時の素通し）。外した瞬間の検出（権限のポーリング）は行わない（ユーザー確認 2026-11-15）。実行中に権限が外れた場合は tap の無効化と同じく処理し、フックを停止状態にして案内する。
- 開発実行では許可の対象がターミナル / python になることを手順に書く。文言は `ja.json` / `en.json` の両方に足す。

### §5.3 キーの識別

`macos/` に **`vk ↔ (scan, extended, is_keypad, event.name)` の 1 表**を持つ。

- 受信: vk から互換の `scan_code` / `is_keypad` / `name` を作って上位へ渡す。domain・application・レイアウト JSON は変えない（§8 Q7）。
- 送信の解決順: ①既知のキー名 → vk を直接引く ②無ければレイアウトの id → `scan_code`（`_resolve_layout_scan_code` の既存の経路）→ 表で一意に決まる vk。scan だけで複数の vk に当たる場合（テンキーと拡張キーの重複等）と表に無い場合は、Windows の未知のキーと同じ検証エラー（`ValueError`）にする。
- 検証（`validate_key_name`）・送信・`identity_of` は同じ解決結果を使う。scan から vk への逆変換は上記 ② に限る。
- `name` は既存の語彙に合わせる: `ctrl` / `alt` / `left windows` / `right ctrl` / `right alt` / `right windows` 等（`key_input.md` §7.1）。**v0.11: Command / Option だけは Mac 専用の名前にする（§5.3.4）。下表の Command / Option の行は §5.3.4 の表で置き換える。**

| Windows のキー名 | macOS の物理キー |
|---|---|
| `left windows` / `right windows` | 左 / 右 Command |
| `alt` / `right alt` | 左 / 右 Option |
| `ctrl` / `right ctrl` | 左 / 右 Control |
| 無変換 / 変換（走査コード 123 / 121） | 英数 / かな（JIS 配列） |

- 文字キーの `name` は**選択中のレイアウトに合う名前**を backend で作る（例: JIS を選択中は、US の `[` の位置が `@`）。入力ソースのかな状態には左右されない。レイアウトの切替は既存の写しの更新（`LayoutController`）に合わせて反映する。
- **段階 ③ の開始条件**: JIS / US の記号キーについて、物理キー・受信名・Tk の記録名・レイアウトの id・送信結果の対応表を確定する。→ §5.3.1 で確定（US は実測・JIS 専用キーは Apple の定数による文書値。ユーザー判断 2026-11-11）。
- Tk のキー取得（`TkKeyTranslator`）は aqua の `keycode` の上位 8 ビットを vk として §5.3.1 の表で解釈する。上位 8 ビットが `0xFF`（IME の入力中）なら解釈しない（`??`）。キー取得中は Q4 のとおり入力ソースを英字へ切り替えるため、通常はこの状態にならない。
- 表に 241 / 242 を出さないことで、押下だけの組み直し（`make_only_keys`）は自動で対象外になる。
- 表に無いキー（fn、keypad `=` / Clear、F13 以降など）は `name=""` で上位へ渡し、素通しする（`input_router.py` の既存動作）。Tk の記録では `??` のまま。
- ~~UI: `windows` は macOS では `Command`、`alt` は `Option` と表示する（表示のみで、保存するキー名は変えない）。適用する箇所は §5.3.3。~~ → **v0.11 で廃止**。キー名そのものを `command` / `option` にする（§5.3.4）。

#### §5.3.3 修飾キーの表示名の適用範囲（**v0.11 で廃止**・§5.3.4 に置き換え。以下は経緯として残す）（v0.10・task_09a の Mac 目視を受けて・Codex 敵対的レビューの 1 件を反映して確定・ユーザー 2026-11-14）

- **仕組み**: 差し替え表（`OsBackend.modifier_display_names`。Windows は空・macOS は `windows` → `Command`・`alt` → `Option`）を App の組み立てで `domain/key_symbols` へ 1 回注入する（task_09a のまま）。各箇所は `key_symbols` の関数を通すだけで、OS を判定しない。置き換えは語単位（`left windows` → `left Command`・`windows+c` → `Command+c`）で、`alt gr` は置き換えない。保存するキー名・JSON は変えない。Windows では表が空のため、どの箇所も今の表示のまま。
- **記号キーの表示（正本 `features.md` §4.6「記号キーのキー名の表示」・phase 74）とは別の規則**として扱う。§4.6 が「今のキー名のまま」とする欄（hotkey の一覧と入力欄・キーマップ編集のキー置換一覧・切替 / 停止 / トグルキーの欄）は、記号の置き換え（`+` を区切りに使うため）の対象外という意味で、修飾キーの表示名の置き換えは下表に従う。フェーズ末の正本反映で §4.6 にこの区別を書き足し、§4.6 の「キーマップ編集のキー置換一覧」（画面に実在しない。キー置換はキーボードUIの枠で表示する）を直す（Codex 敵対的レビュー・ユーザー 2026-11-14）。
- **適用する箇所**（表示だけ）:

  | 箇所 | 状態 |
  |---|---|
  | トリガー一覧・出力シーケンス一覧の `key_hold`・キーボードUIのキー置換の枠 | 適用済み（task_09a） |
  | 出力シーケンス一覧の `hotkey` の値 | 適用済み（task_09a の目視後の修正） |
  | キーマップ一覧の切替キー（`keymap_panel.entry` の `switch_key`）・停止 / トグルキーの表示 | 本節で追加 |
  | キーボードUIのタイトル（編集中のキー名） | 本節で追加 |
  | キー名を差し込む**すべての**エラー・通知・確認の文言（取得・切替キー・置換元・トリガーの追加 / 編集・フックの開始時の重なり・割り当て / クリアの通知・削除の確認 等。対象の `ファイル:行` は task_09c が 1 行ずつ定める） | 本節で追加（`tr` へ渡すキー名の値〔`key` / `source` / `target` 等〕だけを置き換える。検査・比較・ログ・例外の文字列は元のキー名のまま。文言そのもの〔「Windowsキー・Caps Lock…」等〕は task_11 で扱う。task_09c の起票レビュー・ユーザー 2026-11-14） |
  | 記録専用の入力欄（読み取り専用）: キーマップ編集・まとめて設定の切替キー | 本節で追加。欄には表示名を出し、**記録したキー名は別の変数に持って保存に使う**（欄の文字列を保存値にしない） |

- **適用しない箇所**: 手で打てる入力欄（トリガーのキー・`key_hold` のキー・`hotkey` の値・アクションの値）。欄の文字列がそのまま保存値になるため、保存されるキー名（`windows` / `alt`）のまま出す。取得ボタンで記録した場合も同じ。ホットキーのラベル・プリセットの表示・ヘルプの本文も変えない。
- 実装は task_09c。適用済みの箇所も、上の仕組み（`key_symbols` の 1 か所の関数）を通っていることを確かめる。

#### §5.3.4 Mac の修飾キーのキー名（v0.11・task_09c の Mac 目視を受けて・ユーザー 2026-11-15）

Command / Option は Windows の `windows` / `alt` と共用せず、Mac 専用のキー名で保存・表示する。表示名の差し替え（§5.3.3）は廃止し、画面にはキー名をそのまま出す。

| Windows のキー名 | Mac のキー名（v0.11） | 物理キー |
|---|---|---|
| `windows`（左右を問わない） | `command` | Command |
| `left windows` / `right windows` | `left command` / `right command` | 左 / 右 Command |
| `alt`（左・左右を問わない） | `option` | Option |
| `left alt` / `right alt` | `left option` / `right option` | 左 / 右 Option |
| `ctrl` / `shift` 系 | 変えない（共通） | Control / Shift |

- **規則**: Windows の語彙の `windows` → `command`・`alt` → `option` の語単位の置き換えで Mac の名前を作る（受信名・送信・`key_hold` の左右・hotkey の修飾キー・レイアウトの id `command_l` / `command_r` / `option_l` / `option_r`）。`alt gr` に対応する Mac の名前は作らない。
- **受け付け（両 OS で他方の名前を拒否する）**（Codex 敵対的レビュー high・ユーザー判断 2026-11-15「Windows でも拒否する」）:
  - Mac で拒否: `windows` / `left windows` / `right windows` / `win` / `left win` / `right win` / `alt` / `left alt` / `right alt` / `left menu`。
  - Windows で拒否: `command` / `left command` / `right command` / `cmd` / `option` / `left option` / `right option`。**これまで Windows で検査を通っていた別名（正本 `features.md` §「キーリピート」の別名の列挙・`domain/key_hold.py` の集合）を外す互換性の変更**であり、`keyboard` へ渡す前に backend で拒否する（`keyboard.key_to_scan_codes` は通してしまうため）。
  - 拒否 = 不明なキー名と同じ扱い（`ValueError`。エラーの文言は既存の不明なキーのもの）。hotkey の各要素・`key_hold` のキー・置換元・置換先・トリガー・切替 / 停止 / トグルキーのすべてに及ぶ。
  - **判定の口**: backend に「その OS で受け付けるキー名か」を返す口を 1 つ設け、`validate_key_name` もこの口を通す。domain / application は OS を判定しない（domain の修飾キーの集合に両 OS の名前を持つのは、語彙としての判定のため）。
  - **置換元の入口**（Codex 敵対的レビュー medium）: 置換元は `validate_key_name` を通らないため、①キーボードUIで置換元の編集を始めるとき（枠のクリック。拒否された枠は割り当て禁止と同じく編集を始めない）②割り当てを確定するとき（置換元・置換先の両方。`assign_keymap_from_keyboard_ui` 等）に上の口で検査する。
  - **トリガー・hotkey・`key_hold` の入口**（Codex 敵対的レビュー 2 回目 medium・ユーザー 2026-11-15）: トリガーは追加・キーの変更の確定時に上の口で検査する（今は検査が無い）。**hotkey** の各要素は、保存時（ダイアログの OK）に**他方の OS の修飾キーの名前だけ**を上の口で検査する。正本 `key_input.md`「hotkey のアクションは保存時にキー名を検査しない」はレイアウトで送れる名前が変わるための規則であり、修飾キーの名前はレイアウトに依らないため、この検査だけを例外として足す（hotkey のそれ以外の名前は今どおり実行時のエラー）。**`key_hold`** は今の OK 時の全キー名の検査（`validate_key_name`・正本 `features.md` の key_hold の項）を維持し、他方の OS の名前はその検査の中で上の口により拒否される（Codex 敵対的レビュー 3 回目 medium・ユーザー 2026-11-15）。切替 / 停止 / トグルキーは記録専用の欄のため、記録の確定時に上の口で検査する。
  - **既存データ**（読み込み）: 他方の OS の名前を含む設定も読み込みでは拒否・変換せず保持する（JSON の後方互換・既存キーは削除しない）。そのキー名は使う時点で上の拒否に当たる（置換・トリガーは効かない・hotkey / `key_hold` は実行時の既存のエラー経路）。Windows で `command` / `option` の別名を保存していた設定がこれに当たり、ユーザーが `windows` / `alt` に直す（自動変換はしない）。
- **domain / application の語彙**: 修飾キーの集合（`key_hold` の修飾キー・hotkey の修飾キーの並び・割り当て禁止・`key_state_manager` の左右の寄せ・`input_router` の修飾キーの一覧 等）に `command` / `option` 系を OS 非依存の語として足す。割り当て禁止（Q5）には `command` / `left command` / `right command` を足す。
- **Tk の記録**: aqua の `Meta_L` / `Meta_R` → `command` 系、`Alt_L` / `Alt_R` → `option` 系（`key_hold` は左右つき）。Windows の Tk の解釈は変えない。修飾キーの名前の決め方は backend（`tk_keys`）から得て、presentation で OS を判定しない。
- **修飾キー単独の読み飛ばし**（Codex 敵対的レビュー 2 回目 medium・ユーザー 2026-11-15）: 記録で修飾キー単独を読み飛ばす判定（今は `ctrl` / `shift` / `alt` / `windows` の固定の並び。トリガー・キーマップ編集・まとめて設定・切替 / 停止 / トグルキー・キーボードUI・hotkey の修飾キーの集め方）を、domain の修飾キーの判定（両 OS の名前を含む）に揃える。hotkey の記録の修飾キーの並び順は `ctrl` → `alt` / `option` → `shift` → `windows` / `command`。`key_hold` の記録（修飾キー単独を左右つきで記録する）は変えない。
- **廃止するもの**: `OsBackend.modifier_display_names`・`key_symbols` の修飾キーの表示名の差し替え（task_09a）と、その適用箇所・記録専用の欄の表示用の変数（task_09c）。表示はキー名そのものに戻す。恒久的な互換レイヤーとして残さない。
- **既定データとサンプル**: Mac の既定データ（Q2 のプリセット・サンプル）は `command` / `option` 系で持つ。Windows の既定データは変えない。phase 75 の途中に Mac で保存した `windows` / `alt` を含む設定は変換しない（開発中のデータ・Q8）。
- **画面の文言**: キー名を差し込む文言・一覧はキー名をそのまま出す（Mac では `command+c` 等）。~~割り当て禁止の文言の Mac 向けの言い換えは task_11 のまま。~~ → **v0.20**: 割り当て禁止の文言（置換元キー・切替キーの 3 つ）とヘルプの説明は、両 OS 共通にし、Windowsキー・Commandキー・Caps Lock・AltGr・fn と書く（OS で切り替えない・task_11d・ユーザー 2026-11-17）。プリセットのダイアログのヒントも、両 OS に合う例（`ctrl+c` / `Ctrl+C`）にする。正本 `features.md` §4.6 の文言は task_14（正本反映）で整える。
- **Windows への影響**: キー名・表示・保存の形式は変わらない。ただし `command` / `cmd` / `option` 系の別名が不明なキーになる（上の「受け付け」。既存の設定に含まれていれば動かなくなる）。正本 `features.md` の別名の列挙はフェーズ末の正本反映で直す。


#### §5.3.1 記号キーの対応表（task_06）

受信名はレイアウトの id と同じ文字列にする（`event.name` の既存の語彙）。「実測」= §4.1 の環境で物理キーを押した / `CGEventPost` で送った結果。「文書」= Apple の `kVK_*` 定数による値で、JIS キーボードを用意できたときに実測して確定する（§9 の 10）。

| vk | `kVK_*` | US の印字・`us_tkl` の id | JIS の印字・`jis` の id | Tk の keysym（英字入力・US 配列） | 根拠 |
|---|---|---|---|---|---|
| 50 | `ANSI_Grave` | `` ` `` | `zenkaku_hankaku`（Windows 用 JIS キーボードの 半角/全角 の見込み） | `` ` `` | US = 送信のみ実測・JIS = 文書 |
| 27 | `ANSI_Minus` | `-` | `-` | `-` | 実測 |
| 24 | `ANSI_Equal` | `=` | `^` | `=` | US = 実測・JIS = 文書 |
| 33 | `ANSI_LeftBracket` | `[` | `@` | `[` | US = 実測・JIS = 文書 |
| 30 | `ANSI_RightBracket` | `]` | `[` | `]` | US = 実測・JIS = 文書 |
| 42 | `ANSI_Backslash` | `\` | `]` | 送信で press = `¥`・release = `\`（ことえりの「¥ キーで入力する文字」の設定に左右される） | US = 送信のみ実測・JIS = 文書 |
| 41 | `ANSI_Semicolon` | `;` | `;` | `;` | 実測 |
| 39 | `ANSI_Quote` | `'` | `:` | `'` | US = 実測・JIS = 文書 |
| 43 | `ANSI_Comma` | `,` | `,` | `,` | 実測 |
| 47 | `ANSI_Period` | `.` | `.` | `.` | 実測 |
| 44 | `ANSI_Slash` | `/` | `/` | `/` | 実測 |
| 93 | `JIS_Yen` | — | `yen` | US 配列の機種では送っても Tk に届かない | 文書 |
| 94 | `JIS_Underscore` | — | `ro` | 同上 | 文書 |
| 95 | `JIS_KeypadComma` | — | —（id なし・`name=""` で素通し） | 同上 | 文書 |
| 102 | `JIS_Eisu` | — | `muhenkan`（§5.3 の表） | — | 文書 |
| 104 | `JIS_Kana` | — | `henkan`（§5.3 の表） | — | 文書 |
| 10 | `ISO_Section` | —（表に出さない・`name=""`） | — | `§` | 送信のみ実測 |

- 受信名はこの表の「選択中のレイアウトの id」列で決める（例: JIS を選択中に vk 33 → `@`）。互換の `scan_code` は Windows の同じ位置のキーの走査コードを当てる（`yen` 125・`ro` 115・`muhenkan` 123・`henkan` 121・`zenkaku_hankaku` 41 はレイアウトの `scan_code` と一致させる）。
- 送信の結果は入力ソースの配列に従う（§4.1: ことえりの英字入力で US 配列の文字になった）。キー送信は物理キーの送信であり、文字を保証するのは文字送信（`CGEventKeyboardSetUnicodeString`）だけである点は Windows と同じ。


#### §5.3.2 Mac 用のレイアウトの見本（v0.8・ユーザー 2026-11-14）

既存の見本（`jis` / `us_tkl` / `de`）は Windows 用キーボードの並びと表示名（`Win` / `Alt` 等）で、Mac の Command / Option / fn の位置が無い。Mac 用の見本を 2 つ足す。

- 追加するファイル: `config/user/keylayout/us_mac.json`（`layout_id` = `us_mac_sample`）・`jis_mac.json`（`jis_mac_sample`）。表示名は `ui_terms.md` に従う。
- **JSON の形式・既存の id の語彙は変えない**（§8 Q7 の範囲内）。修飾キー・英数 / かなは §5.3 の表どおり既存の id で置く: Command = ~~`windows_l` / `windows_r`~~ → `command_l` / `command_r`・Option = ~~`alt_l` / `alt_r`~~ → `option_l` / `option_r`（v0.11・§5.3.4）・Control = `ctrl_l`（右があれば `ctrl_r`）・英数 = `muhenkan`・かな = `henkan`（`scan_code` は `jis.json` と同じ値）。記号キーの id は §5.3.1 の表の列（US = `us_tkl`・JIS = `jis`）と同じにする。
- 並びは Apple の内蔵キーボード（US / JIS）に合わせ、`label` は Mac の印字（`⌘ Command`・`Option`・`Control`・`英数`・`かな`・`delete`・`return` 等）にする。並びの細部は実装時に実機と照合する。
- ~~**fn は置かず、その位置を空ける**（Mac で常に素通しでキー名が無く、割り当てられそうに見えて動かないことを避ける。表示だけのキーは JSON の形式の拡張になるため採らない）。~~ → **v0.12: fn は id `fn` で実機の位置に置き、割り当て禁止のキー（`domain/key_identifiers.py` の `PROHIBITED_ASSIGN_KEY_NAMES` に `fn` を足す）として禁止の色で出す**（クリックしても編集を始めない・JSON の形式は変えない）。US は左下、JIS は右 Option の位置（JIS の内蔵キーボードは右 Option が無く fn がある）。矢印は右 Shift の下の空き（右 Option / fn の右）に置き、↑ / ↓ は半分の高さで上下に重ねる（ユーザー 2026-11-15）。**CapsLock は既存の id（`caps lock`）で置く**（割り当て禁止のキーとして禁止の色で出る・`features.md` §4.6「割り当て禁止のキー」）。Command（v0.11 で `command_*`）も同じく禁止の色で出て置換元キーにできない（§8 Q5）。Mac の内蔵キーボードに無いキー（PrtSc・Scroll Lock・Pause・Insert・Menu 等）も置かない。
- 既存の見本は変えない。~~Mac で既存の見本を選んだ場合も `Win` / `Alt` の枠は Command / Option として動く（表示名だけ Windows 用のまま）。~~ → v0.11: Mac で Windows 用の見本の `Win` / `Alt` の枠は、キー名が Mac で無効なため割り当てに使えない（§5.3.4・Q8 の非保証の範囲）。
- 見本の同梱と初回のコピーは既存の見本と同じ扱い（§6.1）。~~Windows でも選べる（Command の枠は Windows キーとして動く）。~~ → v0.11: Windows でも選べるが、Command / Option の枠は Windows で無効（§5.3.4）。
- **`jis_mac` は JIS として扱う**: §5.3・§5.3.1 の「選択中のレイアウトに合う受信名」の JIS の判定に `jis_mac_sample` を含める（判定の方法は task_09 で決める。`layout_id` の一致で判定する場合は `jis` と `jis_mac_sample` の両方）。
- JIS の英数 / かなの受信は §5.3.1 の文書値のまま（実測は §9 の 10 と同じく JIS キーボードを用意できたとき）。

### §5.4 機能対応

| 機能 | macOS の実装 | 無理な場合 |
|---|---|---|
| キー送信 | `CGEventCreateKeyboardEvent` + `CGEventPost`（フラグは §5.1） | — |
| 文字送信 | `CGEventKeyboardSetUnicodeString` | — |
| リピート間隔 | ~~`NSEvent.keyRepeatDelay` / `keyRepeatInterval`~~ → **v0.13: グローバル設定（`.GlobalPreferences`）の `InitialKeyRepeat` / `KeyRepeat` を毎回 `CFPreferencesAppSynchronize` してから読み、15 ms 単位として ms に換算**（task_11 の Mac 目視: NSEvent の値は Tk の起動後もシステム設定を反映せず 0.5 / 0.083 秒に固定だった・ユーザー 2026-11-15。15 ms は一般に知られた換算で Apple の公式の記載ではない） | 既定値（値が無い・数でない・0 以下） |
| スクロール | `CGEventCreateScrollWheelEvent`（Pixel 単位・1 ノッチ = 10 px。**v0.14: 横は wheel2 の負 = 右**〔task_11a の Mac 目視で逆だった〕。OS のナチュラルなスクロールの設定は送ったイベントに効かない〔縦が設定オンで正しかった〕。向きの設定は idea_58） | — |
| マウス操作 | `pyautogui` を維持。**v0.14（task_11a の Mac 目視: pyautogui の Mac 実装ではダブルクリックが単独のクリック 2 回になり、ドラッグがクリックになった・ユーザー 2026-11-15）で次の 3 つは Quartz で送る**: ①回数つきのクリック = 各回の down / up に `kCGMouseEventClickState` = 回数目 ②ドラッグのアクション = 途中の位置を `kCG*MouseDragged` で送る ③押すのアクションの保持中 = マウスの移動を監視する tap（listen-and-modify）を立て、届いた `kCGEventMouseMoved` を保持中のボタンの `kCG*MouseDragged` に書き換える（macOS は送った down を物理のボタンの状態に数えないため、手で動かした移動がただの移動になる。Windows は SendInput の down でボタンの状態が立つ）。離すのアクション・保持中のボタンの物理の down / up で tap を止める | ③の tap を作れなければ書き換えずに今の動作（ログは 1 回） |
| クリック位置の取得 | `MouseBackend`（§5.1 の tap と共存できる形で実装） | — |
| 前面の判定（フックスレッド） | `NSWorkspace.frontmostApplication` の pid（§4.1: tap のスレッドから呼べる） | — |
| モニタ一覧 | `NSScreen`（座標変換あり） | — |
| 物理状態 | `CGEventSourceButtonState` / `CGEventSourceFlagsState` | — |
| クリック透過 | **v0.16** 窓全体を `-alpha` 0.5 の半透明（透かす色の部分は黒）+ `NSWindow.ignoresMouseEvents`（Tk 9.1 は表示のたびに戻すので、`<Map>` の後の `after(0)` でかけ直す。窓のレベルも表示のたびに 0 に戻るので、同じ所で `NSStatusWindowLevel` にする〔メインの `-topmost` は 19〕。`-transparentcolor` は aqua に無い。Tk 9.1 の `-transparent` は描画すると透明の部分が不透明な黒になる〔task_11b の Mac 目視・実測〕。NSWindow の引き方は表の下） | カーソルグリッドを無効化 |
| 窓の重なり順 | `NSWindow.orderWindow`（NSWindow の引き方は表の下） | 無効 |
| 最小化とモーダル | **v0.17** aqua は App の最小化で直接の transient だけを隠し、孫（ダイアログを親にした transient）は表示のまま残す。また `iconify()` の中で `<Unmap>` が先に届き、その時点で子はまだ表示中。そこで `<Unmap>` では預かりの判断を `after(0)` へ遅らせる。遅らせた処理は App が最小化中（`wm_state` が iconic）のときだけ行う。`grab_modal` で開いた窓のうち、transient をたどって App に届き、まだ表示中の窓を隠して記録してから、grab を預かる。`<Map>` でも判断を `after(0)` へ遅らせ（App の直接の子は `deiconify()` の後に表示し直されるため・task_11c の実装中の実測）、その時点で、記録した窓を開いた順に表示し直してから grab を戻す。メインがまた最小化されたら、遅らせた処理を取り消す。台帳外の窓と親なしの窓には何もしない。Windows は入れ子も隠れるので動作は変わらない（task_11c の起票前の実測・2026-11-16）。aqua はメインのしまう動作（黄色のボタン）の途中に `withdraw()` しても NSWindow が表示のまま残るので、隠すときは backend の `order_out(window)`（aqua = `orderOut_`・Windows は何もしない）も呼ぶ。aqua の Tk は transient を NSWindow の子の窓としてつなぐ。子の窓がつながったままメインをしまうと、メインの絵が画面に残る（操作できない残像）ので、メインのしまう直前（`NSWindowWillMiniaturizeNotification`）に子の窓のつながりを外す（backend の `install_minimize_preparation(app)`・Windows は何もしない。戻すと Tk がつなぎ直す）。Tk が先に隠した窓（`winfo_viewable` が偽）も NSWindow が残ることがあるので、App に届く台帳の窓は `order_out` だけ呼ぶ（記録はしない・Tk が戻す）（task_11c の Mac 目視・実測）。`grab_modal` で開く窓は最小化ボタンを無効にする（aqua は `-stylemask` から `miniaturizable` を外す・Windows は何もしない〔Windows の挙動は変えない・transient の窓には元から最小化ボタンが無い〕。ダイアログの最小化ボタンでその 1 枚だけが Dock へしまわれ、ほかのダイアログが残るため・task_11c の Mac 目視・ユーザー 2026-11-16） | 変更なし（最小化ボタンを無効にできなければそのまま） |
| 最前面とモーダル | **v0.18** aqua では、grab を持つ transient のダイアログの中をクリックすると、Tk がダイアログのレベルを 0 に戻し、最前面のメイン（レベル 19）の後ろへ回す（後からレベルをかけ直す方式は、ちらつきと取りこぼしがある・task_11e の実測〔本物のクリック 12 回: かけ直し 12 回とも後ろ・run loop の待ちの前で揃える方式 1 回後ろ・最前面を外す方式 0 回〕）。そこで aqua では、`grab_modal` で開いたモーダルがある間だけ、メイン（とヘルプ・ライセンスの窓）の最前面を外し、最後のモーダルを閉じたら設定どおりに戻す（backend の `releases_topmost_during_modal` で判定する。aqua は True、Windows は False）。ダイアログはメインの子の窓なので、同じレベルなら常に前にある。モーダルの間は、他のアプリの窓が上に来ることがある。キーボードUIの最前面は、今どおり grab の間は外れる。`parent` なしの messagebox とエラーを前面に出す件は task_11f で扱う（ユーザー判断 B・2026-11-17） | Windows は変更なし |
| メッセージの窓 | **v0.19** aqua では、`parent` を渡した messagebox はその窓に付くシート（窓と同じレベル）になる。`parent` を渡さない messagebox はアプリ全体のアラート（レベル 8）になり、最前面のメイン（19）の後ろに出る。メッセージの窓の表示中は Tk の `after` が走らない（task_11f の起票前の実測）。そこで presentation の messagebox は 1 つの入口（`message_box`）を通す。①`parent` が無い（または `None` の）呼び出しには、台帳のいちばん内側の表示中のモーダル → 表示中のメイン窓の順で `parent` を補う。どれも無ければ渡さず、既に渡されている `parent` は変えない。②`showerror` / `showwarning` は、出す前に backend の `bring_app_to_front()` でアプリを前面にする（aqua = `NSApplication.activateIgnoringOtherApps_`・Windows は何もしない）。他のアプリを操作中のエラーが背面に隠れないようにするため（ユーザー要件 2026-11-17）。③メッセージの窓の表示中も、モーダルと同じく、メイン・ヘルプ・ライセンスの最前面を外し、キーボードUIの最前面も外す。これは v0.18 の「キーボードUIの最前面は grab の間は外れる」を「モーダルまたはメッセージの窓がある間は外す」に置き換える。判定は backend の `releases_topmost_during_modal` で行い、閉じたら設定どおりに戻す。メッセージの窓の間も、他のアプリの窓が上に来ることがある | Windows は変更なし（`bring_app_to_front` は何もせず、最前面は外さない。`parent` を補うのは、メインが親のとき Tk の既定と同じ） |
| Tk のキー取得 | aqua の `keycode` を §5.3 の表で解釈（`TkKeyTranslator`） | 取れないキーは `??` |
| IME | Q4 | Q4 |
| 状態のアイコン | Tk の `iconphoto`（§4.1: Dock に反映される） | — |
| AppUserModelID | 何もしない | — |

- **Tk の窓から NSWindow を引く**: §4.1 では `NSApp.windows()` の `TKWindow` を窓の位置で照合して対応が取れたが、同じ位置に複数の窓があると一意にならない。task_11 で一意に決まる引き方を確かめる。位置の照合を使う場合、候補が 1 つでなければ（0 または 2 以上）その窓には何も適用せず、その機能は無効と同じ扱いにする（別の窓へ誤って適用しない）。同じ位置に窓が重なる場合を task_11 の確認項目にする。 → **v0.15: `Tk_MacOSXGetNSWindowForDrawable(winfo_id())` で一意に引く（位置の照合は使わない・§4.1）。引けない（NULL・関数が無い）ときはその窓に何も適用しない。窓の識別子は `windowNumber`（0 以下は引けないとみなす）。**

## §6 ビルド（段階 ④）

### §6.1 設定のルート

- `AppIdentity.app_data_root()` を 1 か所に新設し、`presentation/app.py:117-119`・`config_paths.py` の `base_dir` 依存をこれに揃える。
- ビルド後の保存先: Q3。開発実行は現状どおり。
- レイアウトの見本は読み取り専用の同梱物とし、初回にユーザーの設定フォルダへコピーする。
  - **v0.21**: コピーするのは**ユーザーの設定フォルダに `user/keylayout` のフォルダが無いときだけ**（そのとき同梱の見本を全部コピーする・上書きはしない）。利用者が消した見本は戻さない・更新で増えた見本は既にフォルダがある利用者には届かない（ユーザー 2026-11-17）。開発実行では同梱物の場所と設定のルートが同じなので何もしない。
  - **v0.21**: `app_data_root()` は開発実行では今の基点（リポジトリの直下）を返し、設定のルートは今どおりその下の `config/`。ビルド後は Q3 の場所を返し、その下に同じく `config/` を置く（相対の構造を OS で揃える）。**Q3 の Mac の `~/Library/Application Support/keyseq/` はルートで、設定は `keyseq/config/` に置く**（Q3 は Mac の `config/` に触れていなかったのを補う・Windows は Q3 のとおり exe の隣の `config/`）。コピーは一時フォルダへ全件コピーしてから改名し、途中で失敗したら一時フォルダを消す（半端な `keylayout` を残さない・task_12 の起票レビュー）。

### §6.2 形式と同梱

- **onedir 固定**（onefile は一時展開先に設定が残らず、再起動とも相性が悪いため採らない）。
- 定義は `packaging/`（OS ごとの `.spec`・手順・`.ico` / `.icns`）。ビルド用の依存は `requirements-build.txt`。
- 同梱物（`bundled_root` と i18n の `catalog.py` の参照先）は datas の相対配置を揃える。`pynput` は hiddenimports が要る見込み（実測で確定する）。
- 再起動は `AppIdentity` へ移す。frozen 時は argv[0] の重複を除く。`.app` は `open -n` を使うかを実測で決める。
- `Info.plist` には識別子を設定する。再ビルド後に権限の再許可が要る場合があることを手順書に書く。

### §6.3 配布物の中身とライセンスの表示（v0.22・ユーザー 2026-11-18）

- **第三者ライセンスの表**（`keyseq/presentation/help/content/third_party/third_party.json`）の各行に、その配布物に入る OS を持たせる（例 `"platforms": ["win32"]`。無い行は両 OS）。ライセンスの窓は**実行中の OS の行だけ**を出す。実行中の OS は presentation で `sys.platform` を見ずに os_backend から受け取る（§3.1）。
  - 行の増減: `keyboard` は Windows のみ。Mac には `pyobjc`（Mac で同梱する `pyobjc-core` と各 framework）の行を足す。Python / Tcl / Tk は OS ごとに別の行（版が違う。Mac の版は Mac のビルドの環境で確定する）。両 OS に `PyInstaller`（GPL v2 + ブートローダの例外。ランタイムの hook は Apache-2.0 なので、その文書も載せる）の行を足す。同梱一覧は各 OS の実際の収集結果（PyInstaller の出力）と照らし、表に無い依存（例: pyobjc の推移依存・任意に取り込まれる Pillow）があれば行を足す。GPL / LGPL のものは下の「対応するソースの同梱」の対象に加える。
  - `tests/test_third_party.py` の版の照合は**実行中の OS の行だけ**を対象にする（Mac の基準線の `test_third_party` の失敗 1 件はこれで解消する）。
- **アイコン**: 今回は PyInstaller の既定のまま。`.spec` に `.ico` / `.icns` の差し替え口だけを置き、絵は後でユーザーが置く（§6.2 の `.ico` / `.icns` を読み替え）。
- **レイアウトの見本**: 同梱するのは `us_tkl` / `us_mac` / `jis` / `jis_mac` / `de` の 5 本。テスト用の `jis_test.json` は入れない（両 OS 共通）。
- **配布物の README**（同梱）と `packaging/` の手順書に書くこと: 本体（GPL v3）の対応するソースの入手先（公開リポジトリの URL・ユーザーが指定）と**その配布物に対応する git のタグ**・PyInstaller のブートローダの例外・第三者ライセンスはヘルプのライセンスの窓で見られること・同梱した依存のソースの置き場（下）・`pynput` の差し替え方（下）。
- **`pynput`（LGPL v3）の差し替え**（敵対的レビュー high 1・ユーザー 2026-11-18）: onedir でも PyInstaller は Python のモジュールを埋め込みのアーカイブから先に読むため、onedir だけでは差し替えられない。`.spec` で `pynput` だけを**アーカイブに入れず `.py` のファイルとして置く**（`module_collection_mode`）。配布物の中の `pynput` を変更版に置き換えると変更版が読まれることを、各 OS のビルド後に実測する。
- **対応するソースの同梱**（敵対的レビュー high 2・ユーザー 2026-11-18）: 配布ごとに本体へ git のタグを打ち README に書く。同梱する GPL / LGPL の依存（今は `mouseinfo`・`pynput`。表の行の追加で増えたらそれも）は、**同梱した版のソースのアーカイブ**（PyPI のソース配布物）を配布物に入れる（他人のサーバーに頼らない）。ビルド用の依存は `requirements-build.txt` で版を固定する。
- タスクの分け方: 表の OS 列（task_13a・コードとテスト）→ `packaging/` と Windows のビルド（task_13）→ Mac のビルド（task_13b・Mac で実施）。

## §7 テスト方針

- contracts のテストを OS 非依存で作り、backend はモックで検証する。
- tap・権限・Tk の窓は macOS の実機目視（ユーザー）。
- **Windows の退行確認には Windows 実機が必要**（Q0）。§3.3 のタスクごとに 4 種の標準検証を行う。
- macOS の基準: 段階 ② の完了時に `tests` / `tests_ui` の結果を基準線として記録する。skip を許すのは `win32` 実装そのもの、または Windows のパスの意味（`\` 区切り・大文字小文字の同一視。Q8 で OS 間の共有を対象外とした）を検証するテストのみ（ユーザー判断 2026-11-12）。基準線は `instructions/phase/75_mac_support/mac_test_baseline.md`。

## §8 確定した判断（ユーザー 2026-11-09・Q0〜Q8 はすべて下記の提案どおり）

- **Q0 Windows 実機の確保**（段階 ① の前提）: 提案 = タスクごとに Windows で検証できる状態で進める。用意できない期間は、段階 ① を「import の遅延と選択点の導入のみ（Win32 ファイルの物理移動をしない）」に縮める。
- **Q1 macOS の Python**: ~~提案 = python.org 版の 3.13（同梱の Tk 8.6 系）~~ → **Homebrew の Python 3.13 + `python-tk@3.13`（Tk 9.1）**（ユーザー判断 2026-11-10・decisions.md）。Tk 9 の差は presentation の `tk_platform.py` に集める（task_05b・§4.1）。PyInstaller で動くかは task_13 で確認する。
- **Q2 既定プリセット**: Windows の `Ctrl+C` 相当は macOS では `Command+C`。提案 = 既定データをプロファイルとして presentation の組み立て時に注入し、macOS は `Command` 系を用意する（domain に OS 判定を入れない）。既存の設定の自動変換はしない。
  - 詳細（ユーザー判断 2026-11-11・task_07b）: 既定データの型と Windows / macOS の 2 組は domain に置き（データのみ・OS 判定なし）、どちらを使うかは `OsBackend` が持つ。App の組み立てで `ConfigService` へ渡し、`new_base_data` / `new_default_data`・domain の互換処理の既定への戻し・プリセット管理の「既定に戻す」は渡された既定を使う。
  - macOS のホットキー・プリセット（8 件）: `Command+Tab`（~~`windows+tab`~~ → v0.11 `command+tab`。以下同じく `windows` → `command`・`alt` → `option`）・`Command+Space`（`windows+space`）・`Command+Q`（`windows+q`）・`Command+W`（`windows+w`）・`Command+H`（`windows+h`）・`Command+M`（`windows+m`）・`Option+Command+Esc`（`alt+windows+esc` → `option+command+esc`）・`Ctrl+↑`（`ctrl+up`）。
  - macOS のサンプル: `ctrl+c` / `ctrl+v` → `windows+c` / `windows+v`、`alt+tab` → `windows+tab`、行の選択（`home`・`shift+end`）→ `windows+left`・`windows+shift+right`。v0.11: いずれも `windows` → `command` に置き換える（§5.3.4）。
- **Q3 ビルド後の設定の保存先**: 提案 = macOS は `~/Library/Application Support/keyseq/`、Windows は `.exe` と同じ場所の `config/`（持ち運びやすさと現行の相対配置の維持）。
- **Q4 IME 制御**: 文字送信は Unicode 送信で IME を経由しない。キー取得は Tk イベントが主経路で、IME がオンだと影響を受ける可能性がある。提案 = macOS では何もしない。キー取得で問題が出たら TIS による入力ソース切替を追加する。→ **§4.1 で問題を確認（かな入力中は Tk の keycode から vk が失われる）。キー取得の間だけ TIS で入力ソースを英字（ASCII 可能な入力ソース）へ切り替え、終わったら元へ戻す**（ユーザー判断 2026-11-11。Windows の取得中の IME オフと同じ考え方。実装は task_09）。文字送信は従来どおり IME を経由しない。
  - 切替の手順: 取得の開始時に元の入力ソースと切替先を記録し、切り替えた後で現在の入力ソースを読み直して切替先になったかを確かめる（§4.1 で確かめたのは読み取りだけで、切替は task_09 で実測する）。
  - 切替に失敗しても取得は止めない。vk が失われた入力（keycode の上位 8 ビットが `0xFF`）は既存の解釈できないキーと同じく `??` になる（§5.3）。
  - 戻すのは取得の終了時（確定・キャンセル・窓の破棄のどれでも）に 1 回だけ。切替を行った取得の入口が戻す責任を持ち、取得が入れ子になっても外側の 1 回だけが切り替え・戻す。
  - 戻す時点の入力ソースが切替先と違う（取得中にユーザーが自分で変えた）ときは戻さない。切替に失敗していたときも戻さない。
- **Q5 Command キーの割り当て禁止**: 提案 = Windows キーと同じく元キーへの割り当てを禁止する（理由 = システムのショートカットの保護）。
- **Q6 対象 CPU**: 提案 = Apple Silicon（arm64）のみ。
- **Q7 キー識別の方式**（§5.3）: 提案 = 案 A（macOS の vk を既存のキー名・互換走査コードへ変換し、domain とレイアウト JSON を変えない）。案 B（OS ごとのキーコード体系とレイアウト）は domain まで影響が及ぶため採らない。
  - **v0.11 の改訂**（ユーザー 2026-11-15）: 案 A を維持したまま、**Command / Option のキー名だけ** Mac 専用の `command` / `option` 系に分ける（§5.3.4）。JSON の形式は変えず、キー名の語彙を足すだけ。理由 = Q8 で OS 間の設定の共有を保証しないため、名前を共用する利点が無く、表示と保存値の食い違い（§5.3.3）を生むだけだった。
- **Q8 OS 間の設定の共有**: 提案 = 対象外（各 OS で作成した設定だけを保証）。`user\keymaps\main.json` のようなバックスラッシュの相対パス、`C:\` の絶対パスの変換はしない。

## §9 受け入れ条件（ドラフト）

1. `keyseq/` 内の `sys.platform` の分岐が `os_backend/__init__.py` の 1 か所のみ、Win32・`keyboard`・`pyobjc` の import が各 OS の実装内に閉じる（§3.1・AST テスト）。
2. Windows で tests / tests_ui の件数が減らず smoke が pass し、実機の動作が変わらない（§3.3）。
3. macOS で GUI が起動し、主要画面が操作できる。テストが §7 の基準を満たす（§4・§7）。
4. macOS で権限の案内が出て、許可後にキー置換・抑止・修飾キーの左右の区別・シーケンス実行・キーの取得が動く（§5.1〜§5.3）。
5. §5.4 の各機能が動くか、無効化されて UI と仕様に明記されている。
6. Windows の `.exe` と macOS の `.app` がそれぞれビルドでき、別の場所に置いて起動し、設定の保存・再起動・同梱物の表示が動く（§6）。
7. 各 OS で、その OS で保存した既存の設定 JSON が読める（Q8）。
8. macOS で、メニュー表示などの UI 停止から復帰したとき、期限切れのアクションが実行されず、停止操作が効く。切替アクションが期限切れになったあとも、通常の入力と次の切替が動く（§5.1）。
9. macOS で、レイアウトの `scan_code` だけで定義した id を、置換先・ホットキー・`key_hold` で送信できる。解決できない id は検証エラーになる（§5.3）。
10. macOS の JIS 配列で、`^`・`@`・`:` が JIS のレイアウトの枠で作った割り当てと一致する（§5.3）。JIS キーボードを用意できない間は、§5.3.1 の文書値による単体テストで代え、未実測であることを完了報告に明記する（ユーザー判断 2026-11-11）。US 配列で `us_tkl` の記号キーが一致することは実機で確認する。
11. macOS で、`ctrl` を元キーにして抑止しながら `ctrl+c` を送る割り当てでコピーが動く。左 Shift を抑止して右 Shift を素通しにしたとき右 Shift の入力が効き、左右を同時に押して離す順を変えても、抑止を解いた後に修飾キーが押されたまま残らない（§5.1）。
12. macOS で、日本語入力（かな）がオンのままキー取得を始めても物理キーが記録され、取得の終了後に元の入力ソースへ戻る。切替に失敗した場合も取得は止まらず、取れないキーは `??` になる（§8 Q4）。
13. macOS で、Mac 用の見本（`us_mac` / `jis_mac`）を選ぶと Mac の並びと印字で表示され、Command / Option の枠のキー名は `command` / `option` 系（§5.3.4）で、Command と CapsLock と fn（v0.12）の枠は禁止の色で出て置換元キーにできず、Option・Control（JIS は英数・かなも）の枠で割り当てた操作が動く。`jis_mac` を選択中は JIS の受信名になる（§5.3.2。JIS の英数 / かなと受信名は 10 と同じく文書値のテストで代えてよい）。
14. 他方の OS の修飾キーの名前を拒否する（§5.3.4）: Mac で Windows 用の見本の Alt / Win の枠を選んでも置換元の編集が始まらず、`alt` / `windows` 系を置換元・置換先・hotkey・`key_hold`・トリガーに入れると不明なキーのエラーになる。Windows で `command` / `option` 系を入れると同じくエラーになる。他方の OS の名前を含む既存の設定は読み込めて、キー名は保持される。拒否の時点は §5.3.4 の入口のとおり（トリガー = 確定時・hotkey / `key_hold` = 保存時・置換元 = 編集開始と確定時）。`key_hold` の未知のキー名は今どおり OK の時点で拒否される。
15. macOS で、`key_hold` 以外の記録（トリガー・キーマップ編集・まとめて設定・切替 / 停止 / トグルキー・キーボードUI）で Command / Option を単独で押しても記録が確定せず、続けて押したキーが記録される。hotkey の記録は `option+command+esc` のように修飾キーを集めて確定する（§5.3.4）。

## §10 スコープ外（本フェーズでやらない）

- Apple Developer の証明書による署名・公証、Mac App Store 配布、インストーラ（`.dmg` 等）
- Intel Mac、Linux
- `keyboard` の Windows 実装の置き換え
- CI でのビルド自動化
- OS 間の設定の共有

## §11 正本反映（フェーズ末昇格・予定）

- 正本: `features.md` §4.6「割り当て禁止のキー」の判定するキー名の列挙に `command` / `left command` / `right command`（v0.11）と `fn`（v0.12）を足し、文言（「Windowsキー・Caps Lock・AltGr」）を整える（task_09b の reviewer）。`spec_detail/architecture.md`（OS 境界・`bundled_root`）、`key_input.md`（macOS のフック・識別・権限。「Windows 以外」前提の 145・165・253・256・264 行付近）、`features.md`（macOS で無効な機能・443 行付近）、`data_schema.md`（Q3）、`ui_terms.md`（権限の案内の用語）
- 地図: `instructions/common/codebase_map.md`、`app_overview.md`（対応 OS）
- 実装: `keyseq/infrastructure/os_backend/`、`input_gateway.py`、§1 の presentation の各ファイルと `main.py`、`tk_keys.py`、`config_paths.py`、`app_relaunch.py`、`shared/i18n/catalog.py`、`views/menu_bar.py` 等の `Control` バインド群、`domain/config.py`（Q2）、`requirements*.txt`、`packaging/`
- 運用文書: `.claude/rules/python_rules.md` の実行コマンド（Mac の `.venv`。`.claude/` の編集前に `.claude_data/modes/README.md` を読む）、README の対応 OS とビルド手順

## 関連

- 正本: `spec_detail/key_input.md` §7.1・§7.5・§7.7、`data_schema.md`
- 過去フェーズ: phase 54（テンキー）、63（押下だけのキー）、71（タスクバーのアイコン）、41・60（IME）
