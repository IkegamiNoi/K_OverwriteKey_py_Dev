# task_08b_macos_event_tap

## 目的

macOS の `MacKeyboardBackend` のフック（`register_global_hook` / `register_key_hook` / `unregister_hook`）を、**単一の CGEventTap**（active）で実装する（暫定 57 §5.1）。
修飾キーの左右別の down / up と抑止時のフラグの付け直し（§5.1「修飾キーの抑止とフラグ」）、tap の無効化からの復帰、**受信側の vk の表**（§5.3「受信」・§5.3.1。ユーザー判断 2026-11-13 で task_09 から前倒し）を含む。
§4.1 の未実測（右 Option 61・右 Control 62・CapsLock 57 の FlagsChanged・自動リピートの値）を Mac で実測し、暫定 57 §4.1 に記録する（段階 ② の区切り L2）。

- **infrastructure の `os_backend/macos/` 限定**。domain・application・presentation・JSON スキーマは不変。pyobjc の import は `macos/` の中に閉じる（§9 の 1・`tests/test_os_backend_boundary.py`）。
- 受け渡し（ディスパッチャ・配送の滞留の規則）は task_08 で済んでいる。本タスクは backend 側だけ。
- Windows の動作は変わらない（`windows/` に触らない）。

## 対象範囲（`keyseq/infrastructure/os_backend/macos/` 限定・新規 3 ファイル + `backend.py`）

### `macos/key_table.py`（新規・純粋なデータと関数。pyobjc を import しない）

- 受信の表 `vk → MacKey(scan_code: int, is_keypad: bool, name: str)`。
  - 対象: `config/user/keylayout/us_tkl.json` の id のうち **Mac に物理キーがあるもの**（英字・数字・記号・F1〜F12・Esc・Tab・修飾キー 8 つ・Space・Enter・Backspace・矢印・Home / End / PageUp / PageDown・Delete・`insert` = Help vk 114〔`scan_code` 82・`is_keypad=False`〕）と §5.3.1 の行。vk は Apple の `kVK_*` 定数（`Events.h`）の値。
  - us_tkl の id のうち表に出さないもの: `print screen`・`scroll lock`・`pause`・`menu`（Mac に物理キーが無い）・`caps lock`（下記）。
  - `scan_code` / `is_keypad` / `name` は、**Windows の keyboard ライブラリが同じ物理位置のキーで渡す値**と同じにする（例: 左 Shift = 42 / `shift`、右 Shift = 54 / `right shift`、左 Control = 29 / `ctrl`、右 Control = 29 / `right ctrl`、左 Option = 56 / `alt`、右 Option = 56 / `right alt`、左 Command = 91 / `left windows`、右 Command = 92 / `right windows`、矢印は 72 / 75 / 77 / 80 で `is_keypad=False`）。名前は §5.3 の表と `key_input.md` §7.1 の語彙に従う。
  - 名前は **US の id**（`us_tkl`）で固定する。ただし修飾キー 8 つはレイアウトの id（`shift_l` / `shift_r` / `ctrl_l` / `ctrl_r` / `alt_l` / `alt_r` / `windows_l` / `windows_r`）ではなく上の §5.3 の語彙の名前にし、id と受信名の対応を表で持つ（テストも同じ対応を使う）。§5.3.1 の JIS 専用キー（vk 93 `yen`・94 `ro`・102 `muhenkan`・104 `henkan`）は表の値で入れる（互換の `scan_code` は 125 / 115 / 123 / 121）。vk 95・vk 10 は表に出さない。
  - **表に出さないキー**: テンキー（task_09 で実測して追加）・fn（vk 63）・vk 179・CapsLock（vk 57）・F13 以降・keypad の `=` / Clear。
- `vk_for_name(name) -> int | None`: 上の表の逆引き（`register_key_hook` 用。1 つに決まらない名前は `None`）。
- 修飾キーの定数: keycode → (修飾の種類, 左右, 機種依存ビット)。§4.1 の実測値（左 Command 55 / `0x08`・右 Command 54 / `0x10`・左 Shift 56 / `0x02`・右 Shift 60 / `0x04`・左 Option 58 / `0x20`・左 Control 59 / `0x01`）と、未実測の右 Option 61 / `0x40`・右 Control 62 / `0x2000`（Apple の `NX_DEVICE*KEYMASK` の文書値。本タスクの実測で確定）。共通ビット Shift `0x20000`・Control `0x40000`・Option `0x80000`・Command `0x100000`。CapsLock `0x10000`・fn `0x800000` は修飾キーの付け直しの対象外。

### `macos/modifier_state.py`（新規・純粋なロジック。pyobjc を import しない）

- `ModifierState`: 修飾キーごとに**左右別に**「物理的に押されている」「抑止中（down を抑止した）」を持つ。
- `on_flags_changed(keycode, flags) -> tuple[event_type, ...] | None`: FlagsChanged の keycode と機種依存ビットから、その修飾キーの down / up を決める（ビットが立った = down・下りた = up）。修飾キーの表に無い keycode（fn 63・CapsLock 57 など）は `None`。
- `mark_suppressed(key, suppressed)`: down を抑止したら抑止中にし、**対になる up も同じ判定にする**（down を抑止したキーの up は callback の結果によらず抑止し、そこで抑止中を下ろす。down を通したキーの up は抑止しない）。
- `rewrite_flags(flags) -> int`: 通過させる物理キーのイベントのフラグを §5.1 の規則で付け直す（機種依存ビットは「押されていて抑止中でない側」だけ残す・共通ビットは左右のどちらかが「押されていて抑止中でない」ときだけ立てる・修飾以外のビット〔CapsLock・fn・テンキーのビット等〕はそのまま）。抑止中の修飾が 1 つも無ければ入力のまま返す。
- `clear()`: 押下・抑止中の記録を全部消す（tap の再有効化・解除の掃除用）。

### `macos/event_tap.py`（新規・pyobjc の Quartz を使う唯一のファイル）

- **Quartz は module 先頭で import しない**（関数内で遅延 import するか、Quartz の関数を引数で注入して既定値の解決を遅延する）。Windows で `macos/backend.py` と `event_tap.py` を import してテストが動くこと（境界テストは `macos/` 内の Quartz の import を許す）。

- `EventTap`: 専用スレッドで CFRunLoop を回し、**単一の active な CGEventTap**（`kCGEventTapOptionDefault`・keyDown / keyUp / flagsChanged）を持つ。
  - `start()`: tap を作ってスレッドを起動する。`CGEventTapCreate` が NULL なら `OSError`（既存の `start_hook` の失敗経路に乗る。権限の案内は task_10）。
  - `stop()`: **tap の参照を先に外してから** `CGEventTapEnable(tap, False)`・CFRunLoop を止め、スレッドを join する（タイムアウトつき）。`ModifierState.clear()`。
  - コールバック（tap のスレッド）: Tk を呼ばない・同期の判定だけで即座に返す。
    - 参照が外れていれば何もせず通す。
    - `kCGEventTapDisabledByTimeout` / `kCGEventTapDisabledByUserInput`: 自分が `stop()` 中でなければ `CGEventTapEnable(tap, True)` で再有効化し、`ModifierState.clear()` と押下の記録の掃除をする（無効化中に解放を取りこぼした可能性があるため）。
    - 自分が合成したイベント（`kCGEventSourceUserData` が `OWN_EVENT_MARK` と一致）は callback へ渡さず通す（Windows の `is_replaying` と同じ契約。定数 `OWN_EVENT_MARK` をここで定義し、送信は task_09 が使う）。
    - keyDown / keyUp: 表で `scan_code` / `is_keypad` / `name` を作る（表に無い vk は `scan_code=0`・`is_keypad=False`・`name=""`）。自動リピートの keyDown も `down` として渡す。
    - flagsChanged: `ModifierState.on_flags_changed` で down / up を導いて渡す（通す flagsChanged にも下記のフラグの付け直しを行う）。**CapsLock（keycode 57）は常に素通し**し、上位へは表に無いキーと同じく `name=""`・`scan_code=0` で渡す（`alphaShift` ビットが立った = `down`・下りた = `up`。ユーザー判断 2026-11-13。`name=`・素通しなので上位への影響は無い。実測で押下ごとの届き方が違えば §4.1 に追記する）。fn（63）は修飾キーとして扱わず、`name=""` で渡して素通し。
    - 抑止の判定は backend の合成（下記）へ 1 回だけ問い合わせて決める。修飾キーの up は上の `mark_suppressed` の規則に従う。
    - 抑止するなら `None` を返す。通すなら、物理キーのイベントは `ModifierState.rewrite_flags` の値を `CGEventSetFlags` で設定してから返す。
    - 例外は `logging` で残し、素通しにする（抑止しない）。
- callback へ渡すイベントは不変の小さな型（`event_type` / `scan_code` / `name` / `is_keypad`。`contracts.py` の `KeyboardBackend` の docstring の契約）。

### `macos/backend.py`

- `MacKeyboardBackend` が `EventTap` を 1 つだけ遅延生成し、登録された hook の一覧（登録順・ロックつき）を合成する。合成の順は Windows の keyboard ライブラリの `direct_callback`（`keyboard/__init__.py:236`・`:253`）と同じ: ①`suppress=True` の全体のフックを登録順に呼び、最初に `False`（または `None`）を返したところで抑止して後続を呼ばない ②次にそのキーの `suppress=True` のキー単位のフックを同じ規則で呼ぶ。
  - `register_global_hook(callback, *, suppress=False)`: 一覧へ足し、最初の登録で `start()`。`suppress=False` の callback は戻り値を見ずに呼ぶ（抑止の判定に加えない）。handle を返す。
  - `register_key_hook(key, callback, *, suppress)`: `vk_for_name(key)` で vk を決め（`None` なら `ValueError`）、その vk の `down` だけを callback へ渡す。`suppress=True` ならそのキーの down / up とも抑止する（Windows の `hook_key` と同じ）。
  - `unregister_hook(handle)`: 一覧から外し、空になったら `stop()`。未知の handle は何もしない。
- `Capabilities` と送信系（`resolve_send` 等の `NotImplementedError`）・`repeat_timing` は変えない（task_09）。

### 実測（Mac・ユーザーとメイン）

- `instructions/phase/75_mac_support/diagnostics/probe_tap_08b.py`（新規・アプリから import しない）: listen-only の tap で flagsChanged の keycode とフラグ（16 進）、keyDown の vk と `kCGKeyboardEventAutorepeat` を標準出力へ出す。
- 実測する項目: 右 Option・右 Control・CapsLock（押す / 離す / もう一度押す）の keycode とフラグ、文字キーの長押しの `kCGKeyboardEventAutorepeat`。結果は暫定 57 §4.1 の表へメインが追記し、`key_table.py` の文書値と違えば直す。

### テスト（Windows でも動くもの。pyobjc を import しない）

- `tests/test_macos_key_table.py`（新規）: 表が `us_tkl.json` の id のうち Mac に物理キーがあるもの（`print screen`・`scroll lock`・`pause`・`menu`・`caps lock` を除く。修飾キーは id と受信名の対応で照合）をすべて覆う / 修飾キー 8 つの `scan_code`・`name` / 矢印の `is_keypad=False` / §5.3.1 の vk の値 / 表に出さないキー（57・63・95・10）/ `vk_for_name` の逆引き。
- `tests/test_macos_modifier_state.py`（新規）: FlagsChanged から左右別の down / up / 修飾以外の keycode は `None` / down を抑止したら up も抑止・通した down の up は通す / `rewrite_flags`（左 Shift 抑止中 + 右 Shift 素通し → 共通の Shift と右 Shift のビットが残る・Command 抑止中 → 後続の文字キーから Command の共通ビットと機種依存ビットが消える・fn と CapsLock のビットは残る・抑止中が無ければ不変・左 Shift 抑止中に右 Shift の flagsChanged を通すとき左 Shift の機種依存ビットが消える）/ `clear()`。
- `tests/test_macos_keyboard_backend.py`（新規・`EventTap` を偽物に差し替える）: 全体のフックを登録順に呼び最初の `False` で後続を呼ばない・全体のフックの後にキー単位のフック / Windows に pyobjc が無くても import できる / `suppress=False` の callback は判定に加えない / 最初の登録で開始・最後の解除で停止 / `register_key_hook` は down だけ渡し未知の名前は `ValueError`。
- `EventTap` のコールバックの分岐（自分の印・再有効化・CapsLock・fn・例外時の素通し）は、Quartz の関数を引数で差し替えられる形にして単体テストする（実 tap の動作は Mac の目視）。

## 読むファイル

- `instructions/history/57_mac_support.md` §4.1（99〜123 行）・§5.1（127〜149 行）・§5.3（178〜227 行）
- `keyseq/infrastructure/os_backend/macos/backend.py`（全体）・`contracts.py:20-56`（`KeyboardBackend` の契約）
- `keyseq/infrastructure/os_backend/windows/keyboard_backend.py:131-160`（Windows のフック登録の形）
- `config/user/keylayout/us_tkl.json`（id の一覧）・`jis.json` の `scan_code` を持つ行
- `keyseq/domain/numpad_keys.py`（テンキーと矢印の走査コードの重なりの参考）
- `tests/test_os_backend_boundary.py`（import の境界）
- `instructions/common/spec_detail/key_input.md` §7.1（キー名の語彙）

## 含まない

- 送信（`resolve_send`・`press_send`・`write_text` 等）・送信の解決順・自分のイベントへの印付け（task_09。印の定数だけ本タスクで定義）
- JIS を選択中のレイアウトに合う名前（vk 33 → `@` など。§5.3.1 の「受信名は選択中のレイアウトの id 列」）・Tk のキー取得（`TkKeyTranslator`）・テンキーの vk の実測と表への追加・`Command` / `Option` の表示・Command の割り当て禁止（task_09）
- 権限の確認と案内・実行中の権限の喪失や tap の障害からのフックの停止の通知（task_10）
- 前面の判定（`MacWindowBackend.is_own_process_foreground` 等）・`repeat_timing` の実装（task_11）
- `presentation/` ・`application/` の変更（task_08 で済み）

## 確認

Windows（`.venv\Scripts\python.exe`。verifier が実行）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_macos_key_table tests.test_macos_modifier_state tests.test_macos_keyboard_backend tests.test_os_backend_boundary tests.test_os_backend_contracts` が失敗 0
- `-m unittest discover -s tests` が失敗 0・エラー 0（2022 件 + 追加分）
- `-m tests.smoke_app` が pass（Windows は `windows/` に触れないため tests_ui は省略してよい）

Mac（`../../../.venv/bin/python`）:

- `tests` が基準線（失敗 6・エラー 10。`mac_test_baseline.md`）から増えない・smoke pass
- 実測（上記の probe）を暫定 57 §4.1 に記録
- 実機目視（ユーザー・権限は開発実行の親アプリに許可済みの前提）: ①フック開始で抑止したキーが前面アプリへ届かず置換先の処理が走る（置換先の送信は task_09 なので、キーマップの切替など送信を伴わない割り当てで確認）②停止キーでフックが止まる ③左 Command を元キーにして抑止しても、続く文字キーが Command+文字にならず、抑止を外した後に別のアプリで通常に入力できる ④左 Shift を抑止・右 Shift を素通しで、右 Shift の大文字が打てる・左右の離す順を変えても修飾が残らない ⑤CapsLock・fn は従来どおり効く ⑥フック停止で tap が外れる（Activity Monitor 等で入力が普通に戻る）

## 完了条件

- 上記の Windows・Mac の確認 pass・**reviewer 採用**。
- 実機目視は Mac で本タスクで実施（ユーザー）。§9 の 11 の `ctrl+c` の送信と、task_08 のキュー版の実機での動作（メニュー表示中の滞留・期限切れ・reviewer の参考 2 = 排出中のモーダルで排出が止まる件）は、送信が入る task_09 の目視でまとめて確認する。
- `instructions/common/codebase_map.md` の os_backend 節（`macos/` の 3 ファイル）に追従（メイン）。
