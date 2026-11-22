# decisions_archive: phase 75 macOS 対応

暫定仕様先行モード（暫定 57 v0.25 凍結）・JSON スキーマ不変（キー名の語彙と既定データのみ OS で分ける）・2026-11-22 完了。

要点: OS 依存を `keyseq/infrastructure/os_backend/`（`windows/` = Win32 + keyboard・`macos/` = pyobjc + CGEventTap）に閉じ、`sys.platform` の分岐を `get_backend()` の 1 か所に限定。Mac の Command / Option は `command` / `option` の別のキー名で、両 OS で他方の名前を拒否（Windows の `command` / `cmd` / `option` の別名も廃止）。フックから UI への受け渡しは Mac だけキュー版（上限 64・期限 1.0 秒）。aqua のメニューの処理は after(0) で遅らせて待ち行列で 1 つずつ。配布は PyInstaller の onedir（Windows の exe・Mac の `.app`〔識別子 `io.github.ikegaminoi.keyseq`〕・依存のソースの同梱・pynput の差し替え口）。本体のライセンスは GPL v3 以降。昇格先は暫定 57 の冒頭の状態行。

以下は phase 75 の作業中に `decisions.md` に書いた記録をそのまま移したもの（日付ごとの節）。

## 2026-11-10 (phase 75: macOS 対応・暫定 57)

### 【段階 ① の区切り】実機目視（Windows）で問題なし（2026-11-10・ユーザー報告）
- 対象: task_01〜04（Windows 固有のコードを `os_backend/windows/` へ移した・動作不変の確認）。IME オンの文字送信 / キーの取得 / キー置換とシーケンス / マウス操作とクリック位置の取得 / キーボードUIの常に手前 / カーソルグリッド / 言語の「今すぐ再起動」。

### 【段階 ① の区切り】deep-reviewer の M1〜M5 → すべて推奨どおり採用（2026-11-10・ユーザー判断「推奨でよい」）
- M1 `KeyCaptureHook` の `after` がディスパッチャ未対応 → task_08 で直す（Windows の動作は変わらない）
- M2 ディスパッチャの型で §5.1 の「捨てるときの復元」を渡せない → task_08 で暫定 57 と併せて改訂
- M3 フックの契約が Protocol に未記載 → 段階 ② の前に `os_backend/contracts.py` の `KeyboardBackend` へ docstring を追記（実施済み）
- M4 pyautogui / pynput / 再起動の実装が `windows/` にしかない → task_11・task_12 で OS 共通の置き場を決める
- M5 契約テストが module 先頭で `windows.backend` を import → task_05 で分離（§7）
- 反映先: `instructions/phase/75_mac_support/phase.md` のタスク一覧へ追記。

### 【task_05】macOS の Python は Homebrew の 3.13 + `python-tk@3.13`（Tk 9.1）に変更（2026-11-10・ユーザー判断）
- 暫定 57 §8 Q1（python.org 版 3.13・Tk 8.6 系）からの変更。理由 = ユーザーが brew で導入することを選んだ（python.org 版は未導入）。
- 実測: Python 3.13.18 / Tk 9.1.0 / pyautogui 0.9.54・pynput 1.8.2・pyobjc-framework-Quartz/Cocoa 13.0。`.venv` はリポジトリルートに作り直し済み。
- 影響: Tk 9 由来の差が出ないかを task_06 の probe の観点に足す。PyInstaller での可否は task_13 で確認。暫定 57 の Q1 の文言は task_06 の改訂で反映する。

## 2026-11-11 (phase 75: task_05c・task_06)

### 【task_05c】Tk 9 の aqua の右クリックは `<Button-3>` → `right_click_sequence` を撤去して起票・実装（2026-11-11・ユーザー判断「task_05c で直す」）
- task_06 の probe で実測（3 回とも `<Button-3>`）。task_05 の `<Button-2>` 切替は Tk 8.6 の aqua 前提の誤り。

### 【task_06】probe の結果で暫定 57 を v0.6 へ改訂（2026-11-11・ユーザー判断）
- Q4: かな入力中は Tk の keycode から vk が失われる → キー取得中だけ TIS で英字へ切替（推奨どおり。tap から vk を取る案は不採用）。
- §5.3.1: US 配列は実測・JIS 専用キーは Apple の定数による文書値で段階 ③ へ進む（JIS の実測は JIS キーボードを用意できたとき。§9 の 10）。
- §5.1 のキュー: 上限 64 件・期限 1.0 秒（メニュー表示中・ドラッグ中もメインスレッドは止まらなかったため）。
- Codex 敵対的レビュー 4 件 → 推奨どおり採用（3 は修正して採用 = 切替に失敗しても取得は止めず `??`。レビュー案の「取得を中止」は不採用）。

### 【task_07】task_07 を分割・Q2 の詳細を確定（2026-11-11・ユーザー判断「推奨どおり」）
- task_07 = macOS のテストの基準線と tests_ui の対処（sashwidth 4 か所を含む）／task_07b = 既定プリセットの注入（Q2）。
- 既定の選択: domain に既定データの型と Windows / macOS の 2 組（データのみ）、`OsBackend` が持ち App の組み立てで `ConfigService` へ渡す（Tk の aqua で選ぶ案は不採用）。
- macOS の中身: プリセット = Command+Tab・Command+Space・Command+Q・Command+W・Command+H・Command+M・Option+Command+Esc・Ctrl+↑／サンプル = Command+C/V・Command+Tab・行選択 Command+← / Command+Shift+→（暫定 57 Q2 に追記）。

## 2026-11-12 (phase 75: task_07)

### 【task_07】aqua で最小化しても入れ子の transient ダイアログが隠れない → task_11 へ（ユーザー判断「task_11 に回す」）
- 実測: 直接の transient は最小化で withdrawn になるが、transient の transient は表示されたまま（3 秒待っても）。`test_minimize_grab_custody` は失敗 25 件、または止まる（揺れる）。
- 基準線では既知の失敗として記録し、Mac で tests_ui を流すときは除外する（§7 の skip の対象ではないため skip は付けない）。

### 【task_07 後】§7 の skip の範囲と「要調査」10 件の担当（2026-11-12・ユーザー判断「推奨どおり」）
- 暫定 57 §7: skip を許す範囲に「Windows のパスの意味（`\` 区切り・大文字小文字の同一視。Q8 で対象外）を検証するテスト」を加える（task_07 の C-3 の 8 件の根拠）。
- tests_ui の「要調査」10 件（Tk 9 / aqua の寸法の差と見られる）は枝番 task_07d で調査・修正する（task_07b の後・段階 ③ の前）。

### 【task_07d】Mac のフォントの差への対処（2026-11-12・ユーザー判断）
- 既定の窓の高さ = max(820, 3 枠が収まる高さ)（推奨どおり。受容案は不採用）。
- キーの文字: aqua では Helvetica（仕様の下限 7px は変えない。下限を 6px に下げる案・受容案は不採用）。最初の推奨「縮める」は既存の縮小が下限 7px で止まるため成立せず、選択肢を出し直した。
- 暫定 57 §4 に追記。

### 【段階 ② の区切り】deep-reviewer（修正して採用）・Codex 標準レビュー（指摘 0）の採否（2026-11-12〜13・ユーザー判断）
- M3 起動時の既定の高さ（task_07d）が aqua に限定されておらず Windows でもフォントの増分・低い画面で変わる → **aqua だけに限る**（ユーザー判断「aqua だけに限る」。Windows は従来どおり 820）。暫定 57 §4 の注記を合わせて改める。
- M2 `listbox_range_drag` の封じが aqua で効かない（`<<SelectAll>>` = Command+A・Listbox のクラスバインドは aqua でも Control+Shift+Home/End）→ 修正して採用。M2・M3 は枝番 task_07e で直す。
- M4 codebase_map の追従・L2 後続タスクへの送り事項・L3 phase.md の文書のずれ → 採用（task_07e でメインが文書を直す）。
- L1 tests_ui の基準線を task_08 の前にモジュールごとに再計測して確定値にする → 採用。M1 Windows の標準検証 4 種と目視（05c・07c・07・07b・07d・07e）はユーザーが Windows を使える時にまとめて（task_08 の着手前）。 → **2026-11-13 実施・すべて OK**（tests 1997 / 0 / 0 / skip 7・tests_ui 1271 / 0 / 0・smoke OK・目視 6 項目 OK）。
- L4〜L6・L9 は参考（保留）。L7 Command+Option+P の発火は task_09 の目視へ・L8 pyobjc の明記は task_10 へ。
- 承認: 進め方「この進め方で（推奨）」。

### 【task_08 起票前】task_08 の分割とディスパッチャの契約 = 暫定 57 v0.7（2026-11-13・ユーザー判断「推奨でよい」）
- 分割: task_08 = OS 非依存の受け渡し（ディスパッチャの型の改訂・即時版 / キュー版・HookController と KeyCaptureHook の切替。Windows で実装・テスト可）/ task_08b = CGEventTap のフック・修飾キー・§4.1 の未実測の実測（Mac）。
- 契約（暫定 57 §5.1.1）: `dispatch(run, *, on_discard=None, priority=False) -> bool` + `invalidate()`。選択は `OsBackend.queued_hook_dispatch`（Windows False = `after(0)` の即時版で動作不変 / macOS True = キュー版・10 ms 排出）。
- Codex 敵対的レビュー 3 回の採否（すべて推奨どおり採用）: 1 回目 = 過負荷の印（あふれた後は停止まで全イベント素通し）・世代の不一致では on_discard を呼ばず停止側が戻す・取得のフックの受付拒否は素通し / 2 回目 = 受付拒否したキーは up まで素通し・優先の処理にフックの稼働番号・切替の予約番号（期限切れの解除は番号一致時のみ。実行完了時の解除は従来どおり）/ 3 回目 = 素通し中のキーがある間は取得のフックを解除しない（4 回目は省略して確定・ユーザー判断）。

### 【task_08 完了】reviewer 採用（2026-11-13）
- 既存テストの新契約への追従（tests_ui 3・tests 1。件数を減らさない最小修正）→ 採用（タスク定義の「テストを新しい型に合わせて直す」と同趣旨・メイン判断）。
- reviewer 参考 1（解除と競合した素通し中の残留）→ 修正して採用（`_handle is not None` のときだけ素通し中へ入れる・メイン）/ 参考 2（排出中のモーダルで排出が止まる）→ 保留（task_08b の Mac 実機で確認）/ 参考 3（予約番号の加算の競合）→ 除外（実害小）/ `hook_controller.py` 459 行 → 報告のみ（分割しない）。
- 完了: Windows compile clean / tests 2022・失敗 0・エラー 0・skip 7 / tests_ui 1271・失敗 0・エラー 0 / smoke OK・目視 OK（キー置換・シーケンス・停止キー・キーマップの切替・キーの記録・ユーザー）。

### 【task_08b 起票】受信の vk の表の前倒しと CapsLock の扱い（2026-11-13・ユーザー判断「推奨でよい」）
- 受信側の vk の表（vk → 互換 scan_code・is_keypad・name。US の名前で固定・§5.3.1 の JIS 専用キーを含む・テンキーは除く）を task_09 から task_08b へ前倒し（Mac で抑止・停止キー・修飾キーの左右を 08b の時点で目視できるように）。JIS 選択中のレイアウトに合う受信名・テンキー・送信・Tk のキー取得は task_09 のまま。
- CapsLock は常に素通しし、上位へは `name=""` で渡す（暫定 57 §5.1 の「別扱い」を確定。Mac では CapsLock を元キーに割り当てられない）。
- フックの合成は Windows の keyboard ライブラリの `direct_callback` と同じ = 全体の抑止フックを登録順に呼び最初の False で抑止・後続を呼ばない → 次にキー単位の抑止フック（`keyboard/__init__.py:236`・`:253` をメインが実物で確認）。
- 起票の整合レビュー（reviewer）: 修正して採用 → 必須 2 件（us_tkl の Mac に無い id の除外と修飾キーの id ↔ 受信名の対応・Quartz の遅延 import）と参考 3・4・5・6（通す flagsChanged もフラグの付け直し・CapsLock の届き方の注記・合成の順を実物に合わせる・phase.md の task_09 / task_10 の境界）をすべて反映。

### 【task_08b 実装】reviewer 修正して採用・probe の実測（2026-11-14・Mac）
- reviewer 中（表に無い vk〔テンキー・F13 以降・vk 179〕がフックの抑止を返しても素通し）→ ユーザー判断「仕様どおり直す」= 常に素通しは CapsLock 57・fn 63 だけ。低（死んだ `_pressed_keys`・未知の flagsChanged を fn ビットで判定・テストの reload）→ 修正して採用（codex-implementer）。参考（CGEventSetFlags の省略・tap 開始前の押下・`_lifecycle` 保持中の stop の再入・`vk_for_name` の大小文字）→ 保留。
- 既存テスト `test_macos_stub_contracts_and_factory` の OSError 前提は新契約で不成立（権限ありの Mac で実 tap が作られる）→ 偽の EventTap で開始・停止を確かめる形へ修正して採用（メイン・5 行）。
- probe: 自動リピートは初回 0・以降 1。右 Option・右 Control は内蔵キーボードに無く文書値のまま。CapsLock は 2 回押下で tap に何も届かず（原因未確定・常に素通しなので影響なし）。暫定 57 §4.1 に記録。
- Mac 目視（2026-11-14・ユーザー）: ①②⑥ OK。③④（左 Command・左 Shift の抑止）はキーボードUIで修飾キーを登録できず未確認（`TkKeyTranslator` の修飾 keysym が task_09）→ ユーザー判断「task_09 へ移す」。⑤は未報告。別件: キーボードレイアウトが Windows 用で Mac 向けのキーが一部無い（暫定 57 Q7 = レイアウト JSON 不変の範囲外）→ 無いキーの一覧をユーザーから受けて扱いを決める（未決）。

### 【task_08b 完了・task_09b 追加】Mac 用のレイアウトの見本 = 暫定 57 v0.8（2026-11-14・ユーザー判断「この案で追記」）
- task_08b 完了: Windows 検証 pass（compile clean / tests 2065・失敗 0・エラー 0・skip 7 / smoke OK・verifier）。
- 既存の見本（jis / us / de）は Windows 用で Command・Option・fn が無い（ユーザー報告）→ Mac 用の見本 `us_mac` / `jis_mac` を足す（§5.3.2）。JSON の形式と id の語彙は変えない（Q7 の範囲内・Command = `windows_*`・Option = `alt_*`・英数 / かな = `muhenkan` / `henkan`）。
- fn は置かず位置を空ける（常に素通しで割り当てできないため。表示だけのキーは形式の拡張になるので採らない）。
- 時期: task_09b（task_09 の後）。§9 に 13 を追加。
- Codex 敵対的レビュー（needs-attention・1 件）と採否（ユーザー「すべて推奨どおり」）: 中 = §9 の 13 が Q5（Command の割り当て禁止・`features.md` §4.6）と矛盾 → 13 を「Command・CapsLock は禁止の色で置換元キーにできない / Option・Control・英数・かなは動く」に分けて採用。メインの確認 = JIS の受信名の判定に `jis_mac_sample` を含める（同梱の layout_id は `jis` 等で `welcome_result.py:4` も id で判定）→ 採用。CapsLock は置かない → 既存の id で禁止の色として置くに変更（採用）。

### 【task_09 起票】task_09 / 09a の分割と起票レビューの採否（2026-11-14）
- 分割（メイン）: task_09 = 送信・選択中のレイアウトに合う受信名（`set_layout_key_ids`・JIS の判定 = id に `yen` / `ro`）・テンキー・物理の Shift / Ctrl / Alt / Win の状態 / task_09a = Tk のキー取得・入力ソースの切替（Q4）・Command / Option の表示（`key_symbols` へ組み立てで注入）・08b から移した目視 ③④（③は Q5 のため JSON に直接書いた既存データで行う・`features.md` §4.6 で既存データは検査しない）。
- メインの判断: 送信だけの別名（`windows` / `left shift` 等）・`send_native_hotkey` は常に False（既存の代替の経路）・`MacWindowBackend.is_shift_down` / `is_ctrl_alt_win_down` を task_09 へ前倒し（phase 74 の Shift の足し方に要る）。
- reviewer（修正して採用）: 必須 1 = JIS の逆引きが 2 表の重なりで None になる → 1 枚の表で引く・`jis` は既定値つき（採用）/ 必須 2 = 物理 Shift 押下中に Shift の要る文字が `1` になる → ユーザー判断「推奨どおり付ける」= 物理の Shift が押されていれば送るキーに Shift の共通ビットを付ける（暫定 57 §5.1 に例外として追記）/ 参考 2〜7（09b の yen・ro の要件・§9 の対応表・JIS 判定の共有の機構・domain の表のテスト隔離・契約テストのフィールド列挙・ホットキーの `!` の差は完了報告へ）を採用。参考 1（Shift 表と別名を昇格時に §5.3 へ）は task_14 で。

### 【task_09 実装】reviewer 修正して採用（2026-11-14・Mac）
- 実装: codex-delegating-implementer（Sol medium + Luna サブエージェント 2 体・自己申告）。10 ファイル（`os_backend/` + `layout_controller.py` の 1 か所 + テスト）。
- reviewer（修正して採用）: 中 = `write_text` がコードポイント 20 個で分割（Mac の上限は UTF-16 の 20 単位）→ ユーザー判断「推奨どおり直す」= UTF-16 の単位で詰めて文字を割らない（`_unicode_chunks`）/ 低 = `_physical_flags` の失敗ログが送信ごとに出る → 最初の 1 回だけ（同判断）/ 低 = None 検査の重複・`_EXTENDED_VKS` の数値列は見送り / 参考 = JIS 選択中の `\` は名前で引けない（`yen` / `ro` に移る・実害小）。修正は codex-implementer。
- Codex の新テストの期待値の誤り 1 件（write_text の押下・離しの 2 回を数えていない）をメインが修正（実装は正しい）。
- 差（タスク定義どおり残す）: ホットキー経路の Shift の要る文字（例 `ctrl+!`）に Shift を足さない。テンキー 16 個の vk・JIS の対応は文書値のまま未実測。
- Mac 実機目視（2026-11-14・ユーザー）: タスク定義の確認 1〜6 すべて OK（置換・`!`・物理 Shift 押下中の `!`・抑止中の `ctrl+c`・文字送信・自分の送信の再捕捉なし・キュー版・テンキー）。残りは Windows 検証。

### 【task_09a 実装】reviewer 修正して採用・TIS は ctypes（2026-11-14・Mac）
- 実装: codex-delegating-implementer（Sol medium + Luna 1 体・自己申告）。
- reviewer（修正して採用）: 高 = TIS を pyobjc の `HIToolbox` / `Carbon` から import する前提が不成立（venv に無い・メインが実測で `ModuleNotFoundError` を確認。ctypes で Carbon を読むと現在の入力ソースの ID が取れることも実測）→ ユーザー判断「推奨どおり」= ctypes（`macos/input_source.py`・依存追加なし・pynput と同じ方式）・同一判定は入力ソースの ID の文字列・参照は CFRelease・入手失敗のログは 1 回。タスク定義を改訂 / 中 = CF オブジェクトの `==` 比較 → ID 比較で解消 / 低 = `tk_keys` の `hasattr` → `getattr`（同判断）/ 低 = private 属性の読み取り（タスク定義どおり許容）。
- tests_ui のテンキー 4 件（Windows の Tk keycode 96 / 97 前提）は Windows 以外で skip（同判断・Mac の同じ確認は `tests/test_macos_tk_key_translator.py`）。
- 修正後の確認でメインが直した点: Codex の修正に IndentationError（`_restore_capture_source` の return）と `get_own_open_status` の口の入手失敗の分岐の欠け → メインが修正。テストの期待値の誤り 2 件（tk_keys の widget に `object()`・IME の解放の数）と境界テストの `ctypes` の許可（`macos/` にも許す）をメインが修正（実装は正しい）。tests は 2049 件・失敗 6・エラー 10（基準線どおり。IME のテストを 6 件へまとめ直したため 2054 から減）。
- 実機 probe: ctypes の口で現在の入力ソースの ID が取れ、切替・戻しが True（入力ソースが英字だったため、かなからの実際の切替は目視 2 で確かめる）。
- 未決（仕様の判断待ち）: macOS では `caps lock` がキーの表に無く（常に素通し・§5.1）、既存の Caps Lock の切替キーが変わっていなくても `validate_key_name` の「不明なキー名」で再検証を通らない（`tests_ui/test_prohibited_assign_keys_ui.py:166`・`features.md` §4.6 の「既存データは検査しない」と Mac だけ食い違う）。

### 【task_09a 目視後の修正】暫定 57 v0.9 §5.1・reviewer 修正して採用（2026-11-14・Mac）
- Mac 目視 1 回目: 2・5 の右クリック OK。1 の「切替キー・トリガーで修飾キーを記録」は確認項目の誤り（修飾キー単独は記録しない = Windows と同じ）。不具合 = 修飾キーを置換先にした割り当てが効かない・物理 Command / Shift + 置換キーが組み合わさらない・一覧で `windows` / `alt` のまま・Command+Option+P が開かない。
- 判断（ユーザー「推奨どおり」）: §5.1 を v0.9 へ改訂。通すキー・自分が送るキーのフラグ = 物理側（押されていて抑止中でない）+ 送信側（自分が down を送った）。Windows の OS の修飾状態に揃える。`write_text` は送信側だけ（文字入力がショートカット化しないため）。
- 実装: codex-implementer（3 回の resume）。メイン修正 1 件（空の ModifierState で物理側が落ちる → 純関数 `modifier_flags`）。reviewer 修正して採用: 中 = 一覧の置換を hotkey の値だけに・中 = `_sent_modifiers` 専用ロック（write_text 中に tap が待たされない）・低 = write_text の扱いを仕様に明記 → ユーザー「推奨どおり直す」→ 反映。

### 【task_09a 再目視・task_09c 起票】暫定 57 v0.10 §5.3.3（2026-11-14・Mac）
- 再目視: 4③④・5 OK。3 のうちキーボードUIで置換先に修飾キーを記録できないのは `keyboard_window.py:618` の当初（2026-03）からの読み飛ばしで Windows も同じ → idea_57 へ分離（ユーザー「推奨どおり」）。取得の欄で `windows` / `alt` のまま → 表示の適用範囲を仕様に定める。
- §5.3.3（v0.10）: 差し替え表は組み立てで 1 回注入・各箇所は `key_symbols` を通すだけ。適用 = 一覧・停止 / トグル・記録専用の欄（表示用の変数を別に持つ）・キーボードUIのタイトル・キー名を差し込むすべての文言。適用しない = 手で打てる欄。記号の表示（正本 §4.6）とは別の規則。Codex 敵対的レビュー 1 件（実在しない「キーマップ編集のキー置換一覧」）を反映して確定（ユーザー）。正本 §4.6 の同じ記述はフェーズ末に直す。
- task_09c 起票レビュー（reviewer 修正して採用）: 中 3（文言の対象を「すべて」へ・比較は元のキー名・停止 / トグルの表示用の変数は `ui_vars` に 1 回）・低 3 を反映（ユーザー「推奨どおり反映」）。

### 【task_09c 実装】reviewer 採用（2026-11-14・Mac）
- codex-delegating-implementer（サブエージェント 2 名・自己申告）。判定候補: keyboard_layouts.py（レイアウトの id）・save_plan_execution.py（保存計画の識別子）は対象外、action_control_fields / keymap_switch_batch / call_context / hotkey_service / sequence_steps / input_acceptance は対象（値がトリガーキー・切替キー・hotkey の構成キー）。
- メイン修正 1 件: 新規 tests_ui のテストデータに keymaps の km1 が無く切替キーが引けなかった（`keymap_service.py:219`）。
- reviewer 採用。低 3 件は任意のため反映しない（保留）: L1 ダイアログの `key_var` に master が無い（既存）・L2 `call_context` の chain を要素ごとでなく連結後に置き換え（要素はキー名だけで実害なし）・L3 正規表現が名前の語にも効くがキー名の箇所にだけ適用。

### 【暫定 57 v0.11 起票】Mac の修飾キーのキー名を `command` / `option` に分ける（2026-11-15・Mac・確定）
- 出所: task_09c の Mac 目視（ユーザー）。hotkey の値の欄に `windows+left`、一覧に `Command+left` と混在。Q8（各 OS で作った設定だけ保証）を踏まえ、名前を共用せず OS ごとに分けるべきとの判断（ユーザー「骨子どおり起票」）。
- 内容（§5.3.4）: `windows` → `command`・`alt` → `option` の語単位で Mac 専用の名前。Mac は `windows` / `alt`、Windows は `command` / `option` を不明なキーとして拒否（変換・別名なし）。§5.3.3 の表示名の差し替え（task_09a / 09c）を廃止。Mac の既定データ・レイアウトの見本（task_09b）は新しい名前で持つ。Q2・Q7 を改訂。
- 同時に判明: hotkey の記録で Option+a が `å` になる（`action_dialog.py:450` が keysym を使う）→ v0.11 確定後に task_09d で修正。キーボードUIで置換先に修飾キーを記録できないのは idea_57（既知）。
- Codex 敵対的レビュー（needs-attention・2 件・メインが `ファイル:行` を実測確認）→ ユーザー判断 2026-11-15: high（Windows で `command` / `option` が既に別名として通る〔`features.md:426`・`key_hold.py:33-41`〕）= **Windows でも拒否する**（互換性の変更として既存データは保持・自動変換なし・正本の別名の列挙はフェーズ末に直す）。medium（置換元は `validate_key_name` を通らない〔`keyboard_window.py:565`・`keymap_panel_controller.py:636-660`〕）= 推奨どおり backend の受付の口を置換元の編集開始と割り当て確定で使う。§9 に 14 を追加。
- Codex 敵対的レビュー 2 回目（needs-attention・medium 2 件・メインが実測確認）→ ユーザー「推奨どおり反映」2026-11-15: ①トリガーは確定時・hotkey / `key_hold` は保存時に他方の OS の修飾キーの名前だけ検査（正本 `key_input.md` の「保存時に検査しない」の例外）・切替 / 停止 / トグルは記録の確定時 ②修飾キー単独の読み飛ばしを domain の修飾キーの判定に揃える（`trigger_dialog.py:126`・`key_capture.py:155`・`keyboard_window.py:618` 等の固定の並び）。§9 に 15 を追加。
- Codex 敵対的レビュー 3 回目（medium 1 件・起票の誤り = `key_hold` の OK 時の全キー名の検査〔`action_dialog.py:309-317`〕を狭めていた）→ ユーザー「直して確定」2026-11-15: hotkey だけ他方の OS の修飾キーの名前を保存時に追加検査・`key_hold` は既存の全検査を維持。**v0.11 確定**。次 = task_09d（Option+å）と §5.3.4 の実装タスクの起票。

### 【task_09d 実装】reviewer 修正して採用・Mac 目視 OK（2026-11-15・Mac）
- hotkey / key_hold の記録で Mac の Option の文字（`å` / `≤`）を物理キーの名前へ。判定 = `event.char` が非 ASCII 1 文字 等・引き方 = レイアウトの走査コード → `vk_to_char`・記号は `KEY_SYMBOLS` の逆引き（§4.6 の単語名）。
- 経緯: 当初の「keycode を先に引く」は記号キーで §4.6 と食い違う（`ctrl+,`・key_hold が `,` を拒否）→ ユーザー「推奨どおり絞る」。目視で直らず（LayoutController の取り違え・`lessthanequal`・us_tkl に走査コードなし）→ `event.char` と `vk_to_char` へ。
- Windows でも `event.char` の判定が効く（de / 北欧 / 非ラテン / AltGr）→ ユーザー判断「Windows も含める」。従来の記録は送れない名前のため悪化しない見込み。Windows はドイツ語入力で目視（未実測）。

### 【task_09e 実装】reviewer 採用（2026-11-15・Mac）
- codex-delegating-implementer（Sol medium + Luna high 3 体・自己申告）・51 ファイル。Mac の受信 / 送信 / Tk の記録（backend の `TkKeyTranslator.modifier_name`・Windows は旧表と同じ）・既定データ（Q2）・語彙（key_hold / 割り当て禁止 / key_state_manager / input_router）を command / option 系へ。表示名の差し替え（task_09a / 09c）を撤去（tests_ui/test_modifier_display_scope.py 削除・test_key_symbols 3 件削除 1 件置換）。sample_install は既定データ経由で変更不要。
- reviewer 採用。低 1（contracts.py の未使用 `field`）はメインが削除。参考 = `normalize_tk_keysym` の `widget` 引数が未使用・`key_state_manager` の `command` の寄せ先変更は Windows で実害なし（Windows の smoke で確認）。
- Mac 目視は task_09f の後にまとめて（§9 の 13〜15）。tests_ui の Caps Lock 1 件は既知の未決。

### 【task_09f 実装】reviewer 採用・Mac 目視 OK（2026-11-15・Mac）
- codex-delegating-implementer（Sol medium + Luna high 3 体・自己申告）・23 ファイル。backend の `accepts_key_name`（Mac = Windows の名前・Windows = Mac の名前を拒否・`resolve_send` の先頭）・入口（キーボードUIの禁止の色と編集開始・置換元の確定・トリガーの追加 / キー変更・hotkey の保存は他方の修飾キーだけ・切替 / 停止 / トグルの記録）・修飾キー単独の読み飛ばしを `is_modifier_key` に統一。メインがテストの前提の誤り 2 件を修正（hotkey_presets は構成セットに無い・トリガーのキーは小文字）。
- reviewer 採用。低 3（keyboard_window の InputGateway 直呼び・新入口のエラー文言で値が重なる・Windows の AltGr の hotkey 記録の目視）は任意で未対応。
- Mac 目視 OK（task_09e と合わせて。停止キーの欄は修飾キーを記録しないため対象外 = 目視項目の誤り）。§9 の 13 は task_09b の後。
- ユーザー提案: hotkey の保存時も全要素を `validate_key_name` で検査（ホワイトリスト）→ phase 75 の範囲外として既存の idea_03 に追記（重複起票しない）。

### 【task_09b 実装】reviewer 採用・Mac 目視 OK・暫定 57 v0.12（2026-11-15・Mac）
- codex-implementer（2 回）で `config/user/keylayout/us_mac.json` / `jis_mac.json` とテスト。reviewer 採用（指摘 = ↑ / ↓ を半分の高さに → メイン修正）。
- Mac 目視でユーザー指示: 矢印は右 Shift の下でよい・JIS の右 Option の位置は fn・fn はグレーアウトで置いてよい → **暫定 57 v0.12**（§5.3.2: fn を id `fn` で実機の位置に置き、`key_identifiers.PROHIBITED_ASSIGN_KEY_NAMES` に `fn` を足して禁止の色）。仕様改訂は小さくユーザー指示どおりのため Codex 敵対的レビューは行わず reviewer の再レビュー（採用）で代えた。正本 features.md §4.6 の列挙への `fn` / `command` 系の追記はフェーズ末（§11 に明記）。
- 再目視 OK。

### 【Caps Lock の未決】案 B（2026-11-15・Mac）
- Mac のキー表に `caps lock` が無い（§5.1 で常に素通し）ため、Windows で作った設定の `caps lock` は Mac で不明なキーとして拒否される（切替キーを変えずに確定しても拒否）。ユーザー判断「案 B」= 仕様差として暫定 57 §5.1 に記録（§8 Q8 の非保証）。案 A（Mac のキー表に検証だけ通る `caps lock`）は動かない切替キーを通すため不採用。
- `tests_ui/test_prohibited_assign_keys_ui.py` の `test_switch_validation_rejects_new_caps_but_allows_unchanged_caps` はキー名の検査を patch して OS に依らない形に（目的 = 割り当て禁止の除外の判定）。reviewer 採用。Mac の tests_ui の既知の失敗が 0 になる。

### 【task_10 実装】reviewer 採用・Mac 目視 OK（2026-11-15・Mac）
- 起票レビュー（reviewer 修正して採用）: H1 = 登録失敗でも start() が True で稼働中になる既存の不具合 → ユーザー判断「両 OS で直す」。H2 = 権限不足は標準の PermissionError で見分ける。M1 = 障害は set_hook_failure_listener（register_global_hook の署名は不変）。M2 = on_permission_required。M3 = ロック外で通知。
- 実装: codex-delegating-implementer（Sol medium + Luna high）・17 ファイル・文言 6 キー（ja / en）・requirements.txt に pyobjc-framework-ApplicationServices（darwin）。メイン修正 = tests_ui/test_sequence_control_review_fixes.py の偽の app に input_gateway（task_09f の取りこぼし）・event_tap の `_notify_failure` で停止中の通知を捨てる（reviewer の任意の指摘・古い稼働の通知が再開後のフックを止める競合）。
- reviewer 採用。任意で未対応 = Windows の keyboard 由来の PermissionError が権限の案内になる（H2 の取り決めどおり・稀）・listener の二重設定（無害）。
- Mac 目視 OK: 権限なしで案内・開始されない・システム設定が開く / 同じプロセスでの再試行が成功（§5.2 に記録）/ 稼働中に外すと、外した後の最初のキー入力で停止して案内 1 回（そのキーは素通し・ポーリングはしない・ユーザー確認）。

### 【task_11 実装】reviewer 採用・Mac 目視 OK・暫定 57 v0.13（2026-11-15・Mac）
- task_11 を 5 本（11 前面の判定・リピート間隔 / 11a マウス / 11b 窓と画面・無効化 / 11c aqua のモーダル / 11d 割り当て禁止の文言）に分割（ユーザー「この分け方で起票」）。起票レビュー reviewer 修正して採用（注入 `appkit=None`・値の丸め・tap のスレッドから repeat_timing も呼ばれる）。
- 実装: codex-implementer（Luna high）。前面の判定 = `NSWorkspace.frontmostApplication` の pid（取れなければ真・例外は偽）。
- **仕様変更（直接改訂・ユーザー「推奨どおり変える」）**: Mac 目視 1 でリピートの速さが設定に追従せず。`NSEvent.keyRepeatDelay` / `keyRepeatInterval` は Tk の起動後もシステム設定を反映しない（0.5 / 0.083 秒固定）とメインが実測 → 暫定 57 v0.13 §5.4 = グローバル設定の `InitialKeyRepeat` / `KeyRepeat`（`CFPreferencesAppSynchronize` の後に毎回読む・15 ms 単位）。注入は `foundation=None`。メインがテストの期待値の並びの誤り 1 件を修正。reviewer 採用・Mac 再目視 OK。
- task_11c へ送った（Mac 目視から・ユーザー 2026-11-15）: メインが最前面のときトリガーの追加ダイアログが記録開始で後ろへ回る。キーボードUIの件は目視 3 の文言（「自分の窓が前面」）の不正確さから来た誤読で不具合ではない（ユーザー指摘: キーボードUIはクリックして使うのでメインが前面のままにはならない）→ 送らない。

### 【task_11a 実装】reviewer 採用・Mac 目視 OK・暫定 57 v0.14（2026-11-16・Mac）
- M4: pyautogui / pynput の実装を `os_backend/pyautogui_mouse.py`（`PyAutoGuiMouseBackend`）へ移し、Windows / Mac が継承（中身は同一・reviewer が移動前と照合）。codex-implementer（Luna high）。
- **仕様変更（直接改訂・ユーザー「この案で直す」）**: Mac 目視 2・3 で NG。pyautogui の Mac 実装は回数つきのクリックに `kCGMouseEventClickState` を付けず、押した後の移動も MouseMoved で送る。macOS は送った down を物理のボタンの状態に数えないため、手で動かしてもドラッグにならない → 暫定 57 v0.14 §5.4 = 回数つきのクリック・ドラッグ・押す / 離すを Quartz で送り、押すの保持中は listen-and-modify の tap（`macos/mouse_hold_tap.py`）で MouseMoved を Dragged に書き換える（物理の down / up で終える・作れなければ今の動作）。横スクロールは wheel2 の符号が逆だった（縦は正しい・送ったイベントにナチュラルなスクロールの設定は効かない）。
- スクロールの向きの設定はユーザー要望で idea_58 に分離。中クリック（目視 4）は試せるマウスが無く未確認。
- 物理状態の差（記録）: `is_mouse_button_down` は物理のボタンだけ。自分の mouse_down の保持中は Windows = True・Mac = False。
- メイン修正: テストの patch 先・backend の固定・契約のテストが継承したメソッドを数える・import 漏れ・停止の予約の競合（同じ tap のときだけ止める）。

### 【task_11b 実装】reviewer 採用・Mac 目視 OK・暫定 57 v0.15 / v0.16（2026-11-16・Mac）
- 起票レビューの H1（`window_handle` が None のときの誤判定）は presentation にガードを足して採用。M1 は v0.15（ユーザー承認）。
- Mac 目視でカーソルグリッドの下が見えない → Tk 9.1 の `-transparent` は描画すると黒になると実測。ユーザー判断 A = 窓全体を `-alpha` 0.5 の半透明（v0.16）。
- 続けてクリックが下へ届かない → Tk が表示のたびに `ignoresMouseEvents` を戻す。グリッドが後ろへ回る → レベルも表示のたびに 0 へ戻る。どちらも `<Map>` の後の `after(0)` でかけ直す（改訂 2・3・reviewer 採用）。
- メインが最前面のとき「未保存があります」が前に来ない件と「取得」でダイアログが後ろへ回る件は task_11c へ。2 枚目のモニタの目視は保留（ユーザー判断）。

### 【task_11c 実装】reviewer 採用・Mac 目視 OK・暫定 57 v0.17（2026-11-17・Mac）
- 起票前の実測で、最前面のときダイアログが後ろへ回る件は単体で再現しないため task_11e へ分割（ユーザー判断）。v0.17 = 最小化とモーダルの行（ユーザー承認）。
- 実装中・目視で 5 回改訂（いずれもメインの実測で原因を特定）: 復元も `after(0)` へ遅らせる（ユーザー承認）／ダイアログの最小化ボタンを無効（ユーザー判断 A）／withdraw しても NSWindow が残るので `order_out`／Tk が隠した窓も `order_out`・内側から（子の窓が表示中だと親は消えない）／しまう直前に子の窓のつながりを外す（残像）。普段から外すとメインのクリックでダイアログが後ろへ回るので、しまう直前だけ。
- 隠し方を足すだけの改訂（`order_out`・内側から・つながりを外す）は、表に出る動作を変えないためユーザー承認を待たずに進め、報告した。
- 最前面のときメインのクリックでダイアログが後ろへ回る件は task_11e に追加。

### 【task_11e 実装】reviewer 完了可・Mac 目視 OK・暫定 57 v0.18（2026-11-17・Mac）
- 起票前の実測: grab を持つ transient のダイアログの中をクリックすると Tk がレベルを 0 に戻す（素の Tk でも）。parent なしの messagebox はアプリ全体のアラート（レベル 8）→ task_11f へ分割（ユーザー判断）。
- 1 回目の実装（クリック・描き直しの後にレベルをかけ直す `keep_level_with_parent`）は Mac 目視でちらつき・取りこぼし。本物のクリック 12 回の比較（かけ直し 12 回後ろ / run loop の待ちの前で揃える 1 回 / 最前面を外す 0 回）からユーザー判断 B = モーダルの間はメインの最前面を外す（v0.18 の行を書き直し・承認）。
- reviewer の F1（Windows でもかけ直しが走る）を反映し、`releases_topmost_during_modal` が真の OS でだけかけ直す。エラーダイアログを前面に出す要件（ユーザー）は task_11f。

### 【task_11f 実装】reviewer 修正して採用・Mac 目視 OK・暫定 57 v0.19（2026-11-17・Mac）
- messagebox を `presentation/message_box.py` の 1 つの入口に通す（import の 1 行だけを置き換え・呼び出しは変えない＝既存テストの多くが生き残る）。parent を補う・エラーと警告は前面化（ユーザー要件）・メッセージの窓の間は最前面を外す（キーボードUIを含む）。v0.19 はユーザー承認。
- verifier で characterization の tests_ui 2 本が落ちた（偽の窓の AttributeError・parent が足されて引数が合わない）→ 実装は parent 探しを `_default_parent()` に切り出し例外を広く受ける、テストは setUp で `_default_parent` を None に差し替え（期待値は変えない）。

### 【task_11d 実装】reviewer 採用・Mac 目視 OK・暫定 57 v0.20（2026-11-17・Mac）
- 割り当て禁止の文言 3 つ・ヘルプの説明（理由をキーごとに）・プリセットのヒントを両 OS 共通に（案 A・OS で切り替えない・application 層の文言も同じキーのまま）。ヘルプを含めたのは起票レビュー M1 とユーザー判断。
- 目視 1（Command の置換元）・2（Caps Lock の切替キー）は、Mac では枠が禁止の色でクリックできない・Caps Lock を記録できないため画面から出せず、テストで代えて完了（ユーザー判断）。
- 目視の際の新しい発見（ダイアログから開いたヘルプに入力できない）は idea_60。

### 【Windows 検証 task_09〜11f】テスト側の取りこぼし 3 件を修正・Windows 目視 OK（2026-11-17・Windows）
- Mac では skip / 未実行だったテストの追従漏れ 3 件（pyautogui の patch 先・messagebox の parent・スタブ App の input_gateway）をテストだけ直した（reviewer 採用）。
- Win+D で入れ子のプリセット追加が白くなる件は phase 75 前の main でも起きる → idea_61（ユーザー確認）。task_09d はドイツ語入力を省き記号キーの記録で確認（ユーザー判断）。

### 【task_12 起票】暫定 57 v0.21（2026-11-17・ユーザー確定）
- レイアウトの見本のコピーは `user/keylayout` が無いときだけ（消した見本を戻さない・ユーザー判断）。一時フォルダへコピーして改名（起票レビュー M1）。
- Q3 の Mac の `~/Library/Application Support/keyseq/` はルートで、設定はその下の `config/`（Windows と同じ相対構造・起票レビュー M2 を受けてユーザー確定）。
- 再起動は os_backend 共通の `app_relaunch.py` へ移し Mac も使う。`.app` の `open -n` は task_13 の実測で決める。

### 【task_12 完了 / task_13 系の起票】暫定 57 v0.22（2026-11-18・ユーザー確定）
- task_12 は Windows 目視（開発実行の言語切り替え＝再起動）OK で完了。
- §6.3 を追加: ライセンスの表に OS の列（実行中の OS の行だけ表示・照合）・アイコンは既定（差し替え口だけ）・見本は 5 本（jis_test.json を除く）・README と手順書（本体のソースの入手先とタグ・PyInstaller の例外）。すべて推奨案をユーザーが選択。
- Codex 敵対的レビュー 1 回目 high 2 件 → ユーザー判断: pynput は `.py` のまま置いて差し替えを実測（onedir だけでは差し替えられない）・GPL / LGPL の依存は同梱した版のソースのアーカイブを配布物に入れる。2 回目 approve。PyInstaller のランタイムの hook の Apache-2.0 も載せる。
- タスク分割: task_13a（表の OS 列の仕組みと Windows の行）→ task_13（packaging・Windows のビルド・PyInstaller の行）→ task_13b（Mac のビルド・Mac の行〔pyobjc・Python / Tcl / Tk〕）。

### 【本体のライセンスの表記】GPL v3 以降・暫定 57 v0.23（2026-11-18・ユーザー判断）
- 画面は「GNU General Public License v3」だけで「のみ / 以降」が曖昧だった（ChatGPT の指摘をユーザーが持ち込み、メインが裏取り）。ユーザー判断で **v3 以降**。ja / en の `help.license.header`・`help.version.content` を直した（メインの文言修正・tests 失敗 0・test_help_window pass）。README（task_13）と正本 features.md（task_14）も揃える。
- 同じ指摘のうち `{organization}` の残り（pymsgbox / pytweening / pyperclip）は配布元の原文どおり（`.venv` の dist-info で確認）なので直さない。GPL 全文の重複・licenses/ への集約は不要（義務は変わらない）。

### 【task_13a 完了 / アイコンの別ライセンス】方針のみ・保留（2026-11-18・ユーザー判断）
- task_13a は Windows 目視 OK（ライセンスの窓に 14 行・見出しとバージョン情報が v3 以降）で完了。ライセンス本文は英語の原文 1 つだけで、ja / en で訳しているのは窓の見出し・一覧の見出し・読めないときの文言だけ（残す）。
- 独自のアイコンは GPL に含めず、別のライセンス（`ASSETS_LICENSE.md`・公式の配布物の一部としてだけ再配布可・他での利用と改変は許可制）にする方針（ユーザー案）。今はアイコンが PyInstaller の既定なので**未着手**。独自のアイコンを入れるときに暫定 57 / 正本へ条項を足し、`ASSETS_LICENSE.md`・README・LICENSE の除外の明記を一緒に入れる。文中の「GPL v3.0」は本体の表記（v3 以降）に合わせる。
- 同じ日（ユーザー判断）: 表（`third_party.json`）のライセンス名を英語の固有名に統一（`BSD 3 条項ライセンス` → `BSD 3-Clause License`・`GNU GPL v3 以降` → `GNU GPL v3 or later`）。表は言語で切り替わらず英語設定でも日本語が出ていたため。訳し分けはしない。正本 `features.md:1056` の一覧は task_14 で揃える（tests の test_third_party・test_help_window pass）。
- 同じ日: task_13 を起票（reviewer 修正して採用 = `.gitignore` の `*.spec` を `packaging/` だけ解除〔H1〕・ソースの検査を .spec の 1 つの定数に〔M1〕・sdist の取得の代替〔M2〕・datas をファイルの種類で列挙〔M3〕・`DISTPATH`〔M4〕）。起票時の判断（暫定 57 に無い細部）: exe の名前 `keyseq`・タグ `v<__version__>`・同梱の README は日英 1 ファイル・Windows の .spec で macos の backend を excludes・ソースのアーカイブが無ければビルドを止める・表の PyInstaller の行は両 OS。
- 同じ日: task_13 実装（ユーザー許可で PyInstaller 6.22.3 を `.venv` へ・sdist は pip download が Python 3.14 で止まったため PyPI から直接取得し SHA256 を照合）。reviewer 修正して採用 → メインが反映（版を `keyseq/__init__.py` から正規表現で読み cwd に依存しない・手順書に取得方法とファイル名の形・upx を無効〔再現性〕・ソースの前方一致を `<名前>-<版>.` に）。

### 【task_13b 起票】暫定 57 v0.24（2026-11-22・ユーザー判断）

- task_13b（Mac のビルド）を起票。reviewer 修正して採用（rubicon-objc の行は無条件に書き、収集されなければ 4 か所から外す・表の変更の Windows 検証は残課題として task_14 の起票で拾う・pynput の差し替えの実測は `Contents/MacOS/keyseq` を直接起動して PID で終了・版を揃える 4 点に 2 つの `.spec`・識別子を変えない旨）。
- 起票時の判断: Mac の `.spec` は Windows と共通化しない（Windows で再ビルドしないと確かめられないため）・README と `sources/` は `.app` の外（署名を壊さない）・`pyobjc` の行の版の照合は `pyobjc-core` に対応づけ・`requirements-build.txt` の両 OS の 10 個の win32 マーカーを外す・Homebrew の dylib はユーザー判断へ・`open -n` は実測で不具合が出たときだけ。
- ユーザー判断: `.app` の識別子 = `io.github.ikegaminoi.keyseq`（以後変えない）・未公証の `.app` の開き方を配布物の README に書く（§10 の署名・公証の対象外は維持）。→ 暫定 57 v0.24。
- 準備（ユーザー許可）: Mac の `.venv` へ PyInstaller 6.22.3・`pip download` は Python 3.13 で通った。Tcl / Tk の文書は Homebrew の版と今の `tcl.txt` / `tk.txt` が同文のため共用。
- 同じ日: task_13b 実装（codex-implementer + メインの補い〔`target_arch` / `argv_emulation` を BUNDLE から EXE へ・手順書に pip download のコマンド・README_dist の pynput のパスを Resources に〕）。verifier（Mac）: compile clean / tests 2141 件（`test_app_data_roots` のエラー 1 → 下）・test_third_party 7 件 pass / smoke OK / tests_ui test_help_window OK / ビルド成功（PyInstaller 6.22.3 で Tk 9.1 を同梱できた）・codesign --verify pass。reviewer 修正して採用（README_dist の pynput のパス）→ 反映・再ビルド OK。
- 実測: datas と pynput の実体は `Contents/Resources`（`Frameworks` からは symlink）。pynput の差し替えは再署名の有無どちらでも直接起動で効いた（README は再署名を案内したまま）。rubicon-objc は収集される（行は残す）。libffi は同梱されない（`/usr/lib/libffi.dylib`）。
- ユーザー判断: task_12 で書かれた `test_app_data_roots` が Mac で Windows の backend を import して落ちていた → 本タスクで Windows / Mac の 2 テストに分けた（Windows 側は win32 以外で skip）。Windows での実測は残課題。
- 表に無い同梱の C ライブラリ（OpenSSL・liblzma・libmpdec・libtommath。Windows の exe にも同種あり）は両 OS 共通の既存の漏れ。推奨 = Mac の一覧を記録し、Windows の作業時に Windows 側も洗い出して両 OS 分を 1 本で起票（ユーザーの返答待ち）。

### 【task_11g 起票】暫定 57 v0.25（2026-11-22・ユーザー判断）

- task_13b の Mac 実機確認で、メニューの処理の中から開いたモーダル（言語の切り替えの確認・`choice_dialog.py:62`）が戻らない不具合（開発実行でも起きる・faulthandler で特定・`after(0)` で遅らせると直ることを probe で確認）→ ユーザー判断「メニューの処理を一拍遅らせる」・Mac だけ。§5.4 に「メニューの処理」の行・task_11g を起票（reviewer 修正して採用 = tests_ui の invoke の漏れ〔test_help_window・test_ui_language〕・patch の with の内側で update・項目数の数え方・終了の目視）。
- Codex 敵対的レビュー（needs-attention・中 3）→ ユーザー判断「推奨どおり」: ①終了が確定したら（`on_close` の destroy の直前）残った予約をすべて取り消す・終了をキャンセルしたら予約は走らせる ②遅らせるのはモーダルを開き得る項目だけ（add_command 全部と言語のラジオ）・物理キー名のチェックボタンとフォントのラジオは即時 ③tests_ui の漏れは反映済み。
- Codex 敵対的レビュー 2 回目（needs-attention・high 2 / medium 1。メインが実測で裏付け = チェックボタンの保存が構成フォルダの外で `ask_choice` を開く〔`layout_controller.py:290-294`・`keymap_set_io.py:777-787`〕・待ちの間に後の after が走る〔Tk で `first-start → second → first-end`〕）→ ユーザー判断「推奨どおり」: 物理キー名は表示と反映を即時・保存だけ遅らせる（構成セットが変わっていたら保存しない）・遅らせた処理は App の待ち行列で 1 つずつ・終了の確定で待ち行列を捨てる・`on_close` の再入を防ぐ。README の zip の例は 3 点を揃える形に修正（メイン）。
- Codex 敵対的レビュー 3 回目（needs-attention・high 1 / medium 3。メインが裏付け = Command+S は待ち行列を通らず保存を直接呼ぶ〔`app.py:628-632`〕・バージョン情報は閉じるのを待たない〔`version_dialog.py:31`〕）→ ユーザー判断「4 件とも本タスクで直す」: ①aqua のショートカット（新規・保存・別名保存・読込・プリセット編集）もメニューと同じ待ち行列を通す ②物理キー名の反映で未保存の印を立てる ③目視 6 を「保存場所の確認を開いたまま新規作成と終了」に差し替え・目視 7 を追加 ④README の zip は毎回空のフォルダで作り、展開した .app の署名を検査する。
- Codex 敵対的レビュー 4 回目（needs-attention・high 1 / medium 1。メインが裏付け = 画面の保存ボタンは保存を直接呼ぶ〔`file_frame.py:16`〕・モーダルは `grab_set`〔`modal.py:254`〕）→ ユーザー判断: ①経路ごとに待ち行列へ入れるのをやめ、待ち行列は grab（モーダル）がある間は次を始めない形に（ショートカットを待ち行列に通す 3 回目の変更は取り消し）②Mac の `.spec` は毎回 `dist/sources/` を空にして今の版のアーカイブだけを入れる（メインが修正・再ビルド OK）。Windows の `.spec` の同じ修正は次の Windows 作業の残課題。
- Codex 敵対的レビュー 5 回目（needs-attention・high 2。メインが裏付け = 最小化でダイアログを残したまま grab を外す〔`modal.py:103-136`〕・ソースの照合が前方一致で `.sha256` だけでも通る）→ メインが反映（「ダイアログの間はメニューを待たせる」というユーザー判断の実装の精度の修正）: 待ち行列の判定を `grab_current()` から既存の `modal.is_modal_active()`（ダイアログが閉じるまで + メッセージの窓）に変更・Mac の `.spec` はファイル名全体を `<名前>-<版>.tar.gz|.zip` で照合（`.sha256` だけではビルドが止まることを実測）。Windows の `.spec` の同じ照合は次の Windows 作業の残課題。
- 同じ日: task_11g 実装（codex-implementer 2 回 + メインの補い〔`_closing` を `__init__` で初期化・`cancel_all` の例外を `tk.TclError` に・テストの偽の after と Mock の使い回しの誤り・共有の App で destroy を patch した on_close の後に `_closing` を戻す tests_ui 3 本〕）。reviewer 修正して採用（テストの不足・確認より前の例外で `_closing` が残る）→ 対応 → 再確認で採用。verifier（Mac）: tests 2157・失敗 0・エラー 0・skip 32 / smoke OK / tests_ui 8 本 pass。Mac 目視と Windows 検証は未実施。
- 同じ日: task_11g の Mac 目視 1〜7 OK（ユーザー）→ task_11g 完了。目視の際の要望 = 保存パネルを最初から広げた形で出す → idea_64 を起票（ユーザー判断）。
- 同じ日: task_13b の実機確認（作り直した .app）: 再ビルドの後、許可してもいつまでも権限の案内が出た → `tccutil reset Accessibility io.github.ikegaminoi.keyseq` で消して許可し直すと動いた（署名が変わり古い許可が効かない）。要る許可はアクセシビリティだけ（`AXIsProcessTrusted` と event tap）。手順書と配布物の README の再許可の書き方を具体的にした（README_dist の「入力監視」の記述は誤りだったので削除）。実機確認 1〜4 OK。5 はサンプル・カーソルグリッド・マウスのドラッグ・ダブルクリック・押して離すドラッグ OK、テンキーのサンプルの A・R・F（→ plus・9・6）でエラー（調査中）。
- 同じ日: テンキーのサンプルのエラー（`Unknown key name: 'plus'` / `'asterisk'` / `'slash'`）の原因 = Mac の backend が記号キーの名前（`key_symbols.py` の 34 個・`yen`・`ro` 以外）を拒否する。開発実行でも起きる既存の不具合で、暫定 57 §8 Q7 案 A（既存のキー名をそのまま使う）との乖離（仕様変更フラグ A）。推奨 = B（実装を直す・枝番 task_09g）→ ユーザー判断待ち。
- 同じ日: ユーザー提案 = 記号キーのキー名は文字（`/`・`+`）を正にし、名前のほうを読み替える（初版の実装中で互換は気にしない・良いコードを優先）。メインは賛成（レイアウトの JSON は文字・名前は Tk の keysym と keyboard ライブラリの都合で入り込んだ形）。範囲が複数ファイル・Windows の実測も要るので、暫定 57 v0.26 の条項を先に起票する進め方を提案中。
- 同じ日: 暫定 57 §5.3.5（v0.26 案）の Codex 敵対的レビュー = needs-attention（high 2・medium 3・メインが裏付け）。キー名に入力用（物理キー）と出力用（出す文字）が混ざっていることが本質で、文字に揃えるだけでは解決しない。推奨 = 今はサンプルのテンキーを物理のテンキーのキー名に直すだけ・整理は idea（idea_45 と統合）→ ユーザー判断待ち。
- 同じ日（ユーザー判断「分けて進める」）: 暫定 57 §5.3.5（v0.26 案）は取り下げ（コミット前の下書きを戻した）。サンプルのテンキーの置換先を `num add` / `num multiply` / `num divide` に直した（`domain/config.py:108-110`・`tests/test_sample_config.py`・Mac で送れることを実測）。キー名の入力用 / 出力用の整理は idea_45 に追記（新しい idea は作らない）。既存のサンプルを使っている利用者は、「サンプルを復元」で作り直す必要がある。
- 同じ日: サンプルの修正の後、作り直した .app でテンキーのサンプルが動いた → task_13b の実機確認 1〜5 すべて OK。保存パネルが固まる件は今回は再現せず（task_11g のメニューの処理の遅延で解決した見込み）→ メニューとボタンの両方の経路をユーザーが確認中。
- 同じ日: メニューとボタンの両方の経路で保存パネルが固まらないことをユーザーが確認 → task_11g で解決として閉じる。`open -n` は不要と判定（今の再起動で keyseq が 1 つだけ起き直り、Dock も 1 つ・前面・置換が動く＝実機確認 3）。前回のレビュー後の差分（.spec のソース・README の再許可・サンプルのテンキー）は reviewer 完了可 → **task_13b 完了**。Windows 検証の残課題 = test_third_party・test_os_backend_contracts（test_app_data_roots の分割）・test_sample_config・requirements-build.txt・task_11g（tests と tests_ui）・Windows の `.spec` の `dist/sources` の空にし方とアーカイブの照合（Mac と同じ修正）・テンキーのサンプル（A / G / T）の実機・C ライブラリ（OpenSSL 等）の洗い出しと両 OS 分の起票。

### 【Windows 検証 task_11g / 13b・task_13c】（2026-11-22・Windows）

- Windows 検証（verifier）: compile clean / tests 2219 件・失敗 0・skip 7（test_third_party・test_os_backend_contracts の分割後の test_app_data_roots・test_sample_config・MenuCommandQueue を含む）/ tests_ui 1300 件 OK / smoke OK。`requirements-build.txt` の win32 とマーカー無しの 12 件は `.venv` の版と一致。
- task_13c（起票・実装 = codex-implementer）: Windows の `.spec` の `collect_distribution()` を Mac と同じに（`<名前>-<版>.tar.gz|.zip` のファイル名全体で照合・`dist/keyseq/sources/` を毎回空にして一致したものだけ copy2）。verifier: 古いファイルと `dummy.sha256` は入らない・`.sha256` だけではビルドが止まる・exe 起動 OK。reviewer 採用。手順書の Windows 節の照合の記述を新しい挙動に合わせた（メイン）。
- 同梱の C ライブラリ（Windows = OpenSSL〔libcrypto / libssl〕・libffi・zlib・VC++ ランタイム・静的に入る bzip2 / xz / zstd / mpdecimal / expat。Mac = OpenSSL・liblzma・libmpdec・libtommath）は両 OS 分を idea_65 に起票（task_13b の推奨どおり 1 本で）。
- Windows の実機確認（テンキーのサンプル A / G / T の置換先 `num add` / `num multiply` / `num divide`）= OK（2026-11-22・ユーザー）→ Windows 検証の残課題はすべて完了。次 = task_14。
- task_14（正本反映）を起票（2026-11-22）。reviewer 修正して採用 = 暫定 57 の状態行を「凍結・v0.25」に・current.md の idea 採番も直す・同じ差分に reviewer と deep-reviewer を重ねない（deep-reviewer + Codex 敵対的に一本化）・確認の grep を広げる・features.md の Mac の保存先・サンプルのテンキー・help_ja:932 の確認・phase.md の完了記載（すべて反映）。

### 【task_14】正本反映・フェーズ完了（2026-11-22）

- ヘルプのカーソルグリッドの素通しの 1 文を両 OS 共通に（「Ctrl・Alt・Option・Windowsキー・Commandキー」・ユーザー確定）。`help_ja.json:932`（左右の修飾キー）は Mac の Option / Command の左右（`option` / `right option` 等）に触れておらず足りない → 文言の案をユーザーに提示（判断待ち）。
- 正本へ昇格: `architecture.md` §3.6（新設）・`key_input.md` §7.9（新設）と §7.1・§7.3・§7.4・§7.7 の macOS の参照・`features.md` §4.8（新設）と §4.3 割り当て禁止・§4.2.12 の修飾キーの別名・§4.5・§4.6 の見本と配布物とライセンスの表・`data_schema.md` §5.14・`ui_terms.md` §2・`nonfunctional.md`・`codebase_map.md`・`app_overview.md`・`README.md`・`python_rules.md`（Mac の .venv）。暫定 57 を v0.25 で凍結。
- 検証（verifier・Windows）: compile clean / tests 2219 件 失敗 0 / test_help_window 25 件 / smoke OK。
- `/refactor_check`（PHASE_BASE = 47132f80）: 推奨 = M1（`macos/backend.py` 791 行・新規）・M2（`modal.install_minimize_grab_custody` 98 行）→ 提案書 28（`instructions/modified_proposal/28_refactor_mac_support.md`）。M4 は新しい型の構築が各 OS に 1 回ずつで非該当・M6 は未測定。実施の時期はユーザー判断。
- deep-reviewer（フェーズ完了判定）: 修正要（中 4・低 8）→ 反映: M1 `Capabilities` の記述を実装どおりに（Mac は status_icon / ime_control を False・未参照）/ M2 JIS の判定 = レイアウトの id に `yen` か `ro` / M3 features §4.6 の id の表に command / option の行と Mac の見本のラベル / M4 features §4.7 の素通しに command / option / L1 §4.2.12 の別名を Windows に限定 / L2 key_input §7.3 の修飾キーの一覧 / L3 ライセンスの表の行数と版の照合のテスト / L5 §4.8 のメニューの処理の on_close の再入と言語のラジオボタン。L6（入力監視の案内・クリック位置の取得の共存・Mac の見本の Caps Lock と fn の位置・§7 のテストの skip の基準）は経緯・作り方に近いので昇格しない。L4（help_ja:932）はユーザー判断待ち。§9 の 1〜15 と §11 の列挙は昇格先の対応表で漏れなし（13 は M3 で補った）。
- Codex 敵対的レビュー（フェーズ全体・needs-attention）: high 2 / medium 3。メインが裏付け = ①修飾キーの up の送信失敗で `_sent_modifiers` に残る（`macos/backend.py:260-264`）②tap の再有効化で消すのは tap 内の状態だけで `KeyStateManager` に伝わらない（`macos/event_tap.py:193-194`）④`mouse_up` がボタンを問わず保持の tap を止める（`macos/backend.py:405`）。③キュー版の排出がエラーダイアログで止まる間の期限切れ・⑤配布ビルドが収集物の版を照合しない、は設計上の弱点の指摘。採否はユーザー判断待ち。
- ユーザー判断（2026-11-22）: Codex の 5 件は idea_66 に起票（phase 75 では直さない）/ help_ja:932・help_en の「左右の修飾キー」に Mac の Option・Command の左右の名前の 1 文を足す（反映済み）/ 提案書 28 は phase 75 の追加タスク task_15 として実施（Windows で実装・検証 → Mac の確認で phase 75 を閉じる）。→ task_14 完了。

### 【task_15】提案書 28 のリファクタ（2026-11-22・Windows）

- 起票: reviewer 修正して採用（`_physical_flags` は window も使う → keyboard_backend に 1 つ置き window が import・ロガーはモジュールごと・patch 先と遅延 import のテストの書き換え・grep を広げる）→ 反映。
- 実装: codex-delegating-implementer（Sol medium・Luna サブエージェント 2 体・自己申告）。`macos/backend.py` を 22 行の `create_backend` だけにし、`keyboard_backend` / `mouse_backend` / `window_backend` / `tk_key_translator` / `ime_backend` / `app_identity` へ分割（再輸出なし）。`modal.install_minimize_grab_custody` の入れ子 5 関数をモジュール関数へ。
- verifier（Windows）: compile clean / tests 2219 件 失敗 0 skip 7 / tests_ui 1300 件 OK / smoke OK / modal.py の最大の関数 77 行。reviewer 採用（本文は元と同一・patch 先は使う側）。参考 = 未使用の `_LOG` 3 つ・`create_backend` の関数内 import（どちらもそのまま）。
- 残り: Windows 目視（ダイアログを開いたまま最小化して戻す）と Mac の確認 3（Mac の作業時）。
- Windows 目視（2026-11-22・ユーザー）: プリセット管理 → プリセット追加を開いたまま Win+D → 戻すと、プリセット追加が白いまま（idea_61 と同じ既存の症状・phase 75 前の main でも起きる）。プリセット管理の窓は閉じられ、開き直せば通常どおり動く → 確認 4 は OK（既存の症状のみ）。残り = Mac の確認 3。
- Mac の確認 3（2026-11-22・Mac・verifier）: compile clean / tests 2157 件 失敗 0 エラー 0 skip 32（mac_test_baseline の基準線と一致）/ tests_ui の test_minimize_grab_custody・test_modal_grab・test_nested_modal_grab 81 件 OK / smoke OK。実機目視（フック開始・置換・メニュー・ダイアログを開いたままの最小化と戻し）OK（ユーザー）→ **task_15 完了・phase 75 完了**。
