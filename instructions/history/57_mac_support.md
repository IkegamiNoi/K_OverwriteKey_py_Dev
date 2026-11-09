# 暫定仕様 57: macOS 対応（mac_support）

> 状態: **未凍結・v0.5・主入力（ユーザー確定済・実装着手可）**。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: ユーザー要望（2026-11-09）。番号対応: phase 75 / 暫定 57 / decisions 75。
> 版: v0.1 起票 → v0.2 deep-reviewer「修正して採用」の H1〜H6・M1〜M8・L1〜L5 を反映 → v0.3 §8 Q0〜Q8 をユーザー確定 → v0.4 Codex 敵対的レビューの 3 件（配送の滞留・独自レイアウトの送信・JIS の記号キー）を反映（ユーザー 2026-11-09）→ v0.5 v0.4 の再レビュー（Codex 敵対的）の 1 件 = アクションを捨てるときの状態の復元を反映（ユーザー 2026-11-10）。

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
- `Capabilities`（dataclass）は OS ごとに無い**機能**を宣言し、presentation が UI を無効化するのに使う。
- フックスレッドから UI スレッドへの受け渡しは、注入するディスパッチャで行う（§5.1）。Windows は現状の `after` のまま。

### §3.3 段階 ① の進め方と不変条件

- Windows の動作とテスト件数を変えない（tests 1951 / tests_ui 1270 / smoke pass）。patch 先の変更は許容し、テストの削除で件数を減らさない。
- テストの 29 ファイル・約 340 箇所が移動対象を参照するため、次の順に分けて**タスクごとに Windows の標準検証 4 種をゲートにする**: ime / own_ime → win32_window → input_gateway の分解 → presentation の切替。
- Mac で取れる保険として次を追加する: AST による import 境界の検査（§10-1 の自動化）、公開シンボルと Protocol の一致テスト。

## §4 macOS で起動（段階 ②）

- Tk を使える Python の `.venv` を用意する（Q1）。
- 依存を環境マーカーで分ける（`keyboard; sys_platform == "win32"` 等）。
- Tk の差分は `tk windowingsystem` で判定し、presentation の 1 か所にまとめる:
  - 右クリックは aqua では `<Button-2>`（`keyboard_window.py:143`、`help_tab_view.py:95` が対象。両方バインド済みの箇所は変更なし）。
  - メニューのアクセラレータと範囲選択等の `Control` バインドは aqua では `Command`。
- **段階 ③ の前に probe する**（結果次第で §5 を改訂する）:
  1. CGEventTap の修飾キー（§5.1）、抑止、タイムアウト、必要な権限
  2. aqua の Tk の `keycode`、`overrideredirect`、`winfo_id` と NSWindow の対応
  3. フックスレッドからの Tk 呼び出し
  4. `TIS` / `NSWorkspace` のスレッド条件
- Windows 専用テストは `skipUnless` を付ける。macOS のテスト基準は §7。

## §5 macOS の入力（段階 ③）

### §5.1 フックとスレッド

- 専用スレッドで CFRunLoop を回し、**単一の CGEventTap**（active）を実行する。`register_global_hook` / `register_key_hook` の重ね合わせは backend 内で合成する。
- 抑止の判定はコールバック内で同期で完結させる。**コールバックから Tk を呼ばない**。アクションと UI 更新は `queue.SimpleQueue` に積み、メインスレッドが排出する（Tk の `after` がメインスレッドを待つと、メニュー表示中などにコールバックが止まり全キー入力が遅延するため）。
- **配送の滞留の規則**（UI が止まっている間の入力を後からまとめて実行しない）:
  - キューに上限件数と有効期限を設ける（値は probe の結果で確定する）。期限切れのアクションは実行せず捨てる。
  - **アクションを捨てるときは（期限切れ・世代の不一致のどちらでも）、予約時に変更した状態を必ず元に戻す**。`SelectKeymapAction` は `_keymap_switch_in_progress` を解除する（立ったままだと `input_router.py:118` で通常の入力が素通しのままになる）。フラグが立っている間は新しい切替を予約できないため、予約は同時に 1 つで、識別子は持たせない。
  - フックの停止、tap の障害、権限の喪失のときは世代を更新し、古い世代のアクションを捨てる。
  - 上限を超えたら新規の抑止をやめて素通しにし、フックを停止状態へ移して知らせる。
  - 停止キーとフックの停止の通知は、通常のアクションのキューとは別の経路で優先して処理する。
- 例外時は素通しにする（抑止しない）。解除時は tap を無効化して CFRunLoop を止める。
- `kCGEventTapDisabledByTimeout` / `ByUserInput` を受けたら tap を再有効化し、**無効化中に解放を取りこぼした可能性があるため押下状態を掃除する**。
- Secure Input 中はイベントが届かない。この間はフックの動作を保証しない。
- 自分が合成したイベントは `kCGEventSourceUserData` の印で識別する。Windows の送信時ガードと同じ契約を `KeyboardBackend` で満たす。
- **修飾キー**は `kCGEventFlagsChanged` で届くため、keycode とフラグから左右別の down / up を導いて上位へ渡す。CapsLock は別扱い。修飾キーの抑止後のフラグ残り、送信時の `CGEventSetFlags` の要否は probe で決める。
- 自動リピートは `kCGKeyboardEventAutorepeat` で判定し、Windows と同じく down を繰り返して渡す。

### §5.2 権限

- 起動時に権限を確認する（`AXIsProcessTrusted`。入力監視も必要かは probe）。
- 未許可、または `CGEventTapCreate` が NULL のときは既存の `start_hook` の失敗経路（`hook_controller.py`）に乗せ、案内ダイアログからシステム設定の該当画面を開けるようにする。
- 許可後は「フック開始」の再操作で再試行する（アプリの再起動を要する場合は案内する。probe で決める）。実行中に権限が外れた場合は tap の無効化と同じく処理し、フックを停止状態にして案内する。
- 開発実行では許可の対象がターミナル / python になることを手順に書く。文言は `ja.json` / `en.json` の両方に足す。

### §5.3 キーの識別

`macos/` に **`vk ↔ (scan, extended, is_keypad, event.name)` の 1 表**を持つ。

- 受信: vk から互換の `scan_code` / `is_keypad` / `name` を作って上位へ渡す。domain・application・レイアウト JSON は変えない（§8 Q7）。
- 送信の解決順: ①既知のキー名 → vk を直接引く ②無ければレイアウトの id → `scan_code`（`_resolve_layout_scan_code` の既存の経路）→ 表で一意に決まる vk。scan だけで複数の vk に当たる場合（テンキーと拡張キーの重複等）と表に無い場合は、Windows の未知のキーと同じ検証エラー（`ValueError`）にする。
- 検証（`validate_key_name`）・送信・`identity_of` は同じ解決結果を使う。scan から vk への逆変換は上記 ② に限る。
- `name` は既存の語彙に合わせる: `ctrl` / `alt` / `left windows` / `right ctrl` / `right alt` / `right windows` 等（`key_input.md` §7.1）。

| Windows のキー名 | macOS の物理キー |
|---|---|
| `left windows` / `right windows` | 左 / 右 Command |
| `alt` / `right alt` | 左 / 右 Option |
| `ctrl` / `right ctrl` | 左 / 右 Control |
| 無変換 / 変換（走査コード 123 / 121） | 英数 / かな（JIS 配列） |

- 文字キーの `name` は**選択中のレイアウトに合う名前**を backend で作る（例: JIS を選択中は、US の `[` の位置が `@`）。入力ソースのかな状態には左右されない。レイアウトの切替は既存の写しの更新（`LayoutController`）に合わせて反映する。
- **段階 ③ の開始条件**: JIS / US の記号キーについて、物理キー・受信名・Tk の記録名・レイアウトの id・送信結果の対応表を実測で確定する。
- 表に 241 / 242 を出さないことで、押下だけの組み直し（`make_only_keys`）は自動で対象外になる。
- 表に無いキー（fn、keypad `=` / Clear、F13 以降など）は `name=""` で上位へ渡し、素通しする（`input_router.py` の既存動作）。Tk の記録では `??` のまま。
- UI: `windows` は macOS では `Command`、`alt` は `Option` と表示する（表示のみで、保存するキー名は変えない）。

### §5.4 機能対応

| 機能 | macOS の実装 | 無理な場合 |
|---|---|---|
| キー送信 | `CGEventCreateKeyboardEvent` + `CGEventPost`（フラグは §5.1） | — |
| 文字送信 | `CGEventKeyboardSetUnicodeString` | — |
| リピート間隔 | `NSEvent.keyRepeatDelay` / `keyRepeatInterval` | 既定値 |
| スクロール | `CGEventCreateScrollWheelEvent` | — |
| マウス操作 | `pyautogui` を維持 | — |
| クリック位置の取得 | `MouseBackend`（§5.1 の tap と共存できる形で実装） | — |
| 前面の判定（フックスレッド） | `NSWorkspace.frontmostApplication` の pid（スレッド条件は probe） | — |
| モニタ一覧 | `NSScreen`（座標変換あり） | — |
| 物理状態 | `CGEventSourceButtonState` / `CGEventSourceFlagsState` | — |
| クリック透過 | Tk の `-transparent` + `NSWindow.ignoresMouseEvents` | カーソルグリッドを無効化 |
| 窓の重なり順 | `NSWindow.orderWindow` | 無効 |
| Tk のキー取得 | aqua の `keycode` を §5.3 の表で解釈（`TkKeyTranslator`） | 取れないキーは `??` |
| IME | Q4 | Q4 |
| 状態のアイコン | Tk の `iconphoto` が Dock に反映されるか probe | Dock の状態表示を無効化 |
| AppUserModelID | 何もしない | — |

## §6 ビルド（段階 ④）

### §6.1 設定のルート

- `AppIdentity.app_data_root()` を 1 か所に新設し、`presentation/app.py:117-119`・`config_paths.py` の `base_dir` 依存をこれに揃える。
- ビルド後の保存先: Q3。開発実行は現状どおり。
- レイアウトの見本は読み取り専用の同梱物とし、初回にユーザーの設定フォルダへコピーする。

### §6.2 形式と同梱

- **onedir 固定**（onefile は一時展開先に設定が残らず、再起動とも相性が悪いため採らない）。
- 定義は `packaging/`（OS ごとの `.spec`・手順・`.ico` / `.icns`）。ビルド用の依存は `requirements-build.txt`。
- 同梱物（`bundled_root` と i18n の `catalog.py` の参照先）は datas の相対配置を揃える。`pynput` は hiddenimports が要る見込み（実測で確定する）。
- 再起動は `AppIdentity` へ移す。frozen 時は argv[0] の重複を除く。`.app` は `open -n` を使うかを実測で決める。
- `Info.plist` には識別子を設定する。再ビルド後に権限の再許可が要る場合があることを手順書に書く。

## §7 テスト方針

- contracts のテストを OS 非依存で作り、backend はモックで検証する。
- tap・権限・Tk の窓は macOS の実機目視（ユーザー）。
- **Windows の退行確認には Windows 実機が必要**（Q0）。§3.3 のタスクごとに 4 種の標準検証を行う。
- macOS の基準: 段階 ② の完了時に `tests` / `tests_ui` の結果を基準線として記録する。skip を許すのは `win32` 実装そのものを検証するテストのみ。

## §8 確定した判断（ユーザー 2026-11-09・Q0〜Q8 はすべて下記の提案どおり）

- **Q0 Windows 実機の確保**（段階 ① の前提）: 提案 = タスクごとに Windows で検証できる状態で進める。用意できない期間は、段階 ① を「import の遅延と選択点の導入のみ（Win32 ファイルの物理移動をしない）」に縮める。
- **Q1 macOS の Python**: 提案 = python.org 版の 3.13（同梱の Tk 8.6 系・正本の実測が 8.6.15 基準）に固定し、PyInstaller が動くことを段階 ② で確認する。
- **Q2 既定プリセット**: Windows の `Ctrl+C` 相当は macOS では `Command+C`。提案 = 既定データをプロファイルとして presentation の組み立て時に注入し、macOS は `Command` 系を用意する（domain に OS 判定を入れない）。既存の設定の自動変換はしない。
- **Q3 ビルド後の設定の保存先**: 提案 = macOS は `~/Library/Application Support/keyseq/`、Windows は `.exe` と同じ場所の `config/`（持ち運びやすさと現行の相対配置の維持）。
- **Q4 IME 制御**: 文字送信は Unicode 送信で IME を経由しない。キー取得は Tk イベントが主経路で、IME がオンだと影響を受ける可能性がある。提案 = macOS では何もしない。キー取得で問題が出たら TIS による入力ソース切替を追加する。
- **Q5 Command キーの割り当て禁止**: 提案 = Windows キーと同じく元キーへの割り当てを禁止する（理由 = システムのショートカットの保護）。
- **Q6 対象 CPU**: 提案 = Apple Silicon（arm64）のみ。
- **Q7 キー識別の方式**（§5.3）: 提案 = 案 A（macOS の vk を既存のキー名・互換走査コードへ変換し、domain とレイアウト JSON を変えない）。案 B（OS ごとのキーコード体系とレイアウト）は domain まで影響が及ぶため採らない。
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
10. macOS の JIS 配列で、`^`・`@`・`:` が JIS のレイアウトの枠で作った割り当てと一致する（§5.3）。

## §10 スコープ外（本フェーズでやらない）

- Apple Developer の証明書による署名・公証、Mac App Store 配布、インストーラ（`.dmg` 等）
- Intel Mac、Linux
- `keyboard` の Windows 実装の置き換え
- CI でのビルド自動化
- OS 間の設定の共有

## §11 正本反映（フェーズ末昇格・予定）

- 正本: `spec_detail/architecture.md`（OS 境界・`bundled_root`）、`key_input.md`（macOS のフック・識別・権限。「Windows 以外」前提の 145・165・253・256・264 行付近）、`features.md`（macOS で無効な機能・443 行付近）、`data_schema.md`（Q3）、`ui_terms.md`（権限の案内の用語）
- 地図: `instructions/common/codebase_map.md`、`app_overview.md`（対応 OS）
- 実装: `keyseq/infrastructure/os_backend/`、`input_gateway.py`、§1 の presentation の各ファイルと `main.py`、`tk_keys.py`、`config_paths.py`、`app_relaunch.py`、`shared/i18n/catalog.py`、`views/menu_bar.py` 等の `Control` バインド群、`domain/config.py`（Q2）、`requirements*.txt`、`packaging/`
- 運用文書: `.claude/rules/python_rules.md` の実行コマンド（Mac の `.venv`。`.claude/` の編集前に `.claude_data/modes/README.md` を読む）、README の対応 OS とビルド手順

## 関連

- 正本: `spec_detail/key_input.md` §7.1・§7.5・§7.7、`data_schema.md`
- 過去フェーズ: phase 54（テンキー）、63（押下だけのキー）、71（タスクバーのアイコン）、41・60（IME）
