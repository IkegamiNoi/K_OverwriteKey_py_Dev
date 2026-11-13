# task_09_macos_key_send

## 目的

macOS の `MacKeyboardBackend` の**送信**（`resolve_send` / `press_send` / `release_send` / `identity_of` / `needs_shift` / `press_shift` / `release_shift` / `send_native_hotkey` / `write_text`）を実装する（暫定 57 §5.1「自分が送るイベント」「送信の修飾」・§5.3「送信の解決順」・§5.4 のキー送信・文字送信）。
あわせて受信を**選択中のレイアウトに合う名前**にし（§5.3・§5.3.1・§5.3.2 の `jis_mac` を含む JIS の判定）、テンキーを受信・送信の表に足す。

- **infrastructure の `os_backend/`（主に `macos/`）と、レイアウトを backend へ知らせる 1 か所の呼び出し（presentation の `layout_controller.py`）に限る**。domain・application・JSON スキーマは不変。pyobjc の import は `macos/` の中に閉じる。
- Windows の動作は変わらない（`windows/` は新しい契約の何もしない実装を足すだけ）。
- Tk のキー取得・表示・入力ソースの切替は task_09a。

## 対象範囲（`os_backend/` + `layout_controller.py` の 1 か所）

### `contracts.py`

- `KeyboardBackend` に `set_layout_key_ids(key_ids: frozenset[str]) -> None` を足す。docstring: 「選択中のレイアウトのキーの id の集合。受信名をレイアウトに合わせる OS（macOS）だけが使う。フックのスレッドから読むので、実装は値の差し替えだけで済ませる」。

### `windows/keyboard_backend.py`

- `set_layout_key_ids` を何もしない実装で足す（Windows の受信名は keyboard ライブラリと既存のレイアウトの `scan_code` で決まっており変えない）。

### `presentation/controllers/layout_controller.py`

- `_refresh_active_layout` の最後で、`get_backend().keyboard.set_layout_key_ids(...)` に `_active_layout` のキーの id の集合を渡す（起動時の最初の確定とレイアウトの切替の両方がここを通る）。例外は吸収してログに残す（レイアウトの切替を止めない）。

### `macos/key_table.py`

- **JIS の判定**: `is_jis_layout(key_ids) -> bool` = キーの id に `yen` か `ro` があれば JIS（`jis.json` と §5.3.2 の `jis_mac.json` が両方を持つ。`us_tkl` / `de` / `jis_test` は持たない。`layout_id` では判定しない = ユーザーが `jis.json` を写して作ったレイアウトも JIS になる）。
- **JIS の受信名**: §5.3.1 の表の JIS の列で、US と名前が違う vk（50 → `zenkaku_hankaku`・24 → `^`・33 → `@`・30 → `[`・42 → `]`・39 → `:`）の上書き表を持つ。互換の `scan_code` は US と同じ（同じ物理位置）。`zenkaku_hankaku` は `jis.json` の `scan_code` 41 と一致させる。
- `key_for_vk(vk, *, jis: bool) -> MacKey | None`: JIS なら上書き表 → 共通の表の順で引く。
- **テンキー**: Apple の `kVK_ANSI_Keypad*` の文書値で `keyseq/domain/numpad_keys.py` の 16 個の名前を表に足す（`is_keypad=True`・`scan_code` は `numpad_keys.py` の値）。表に無いテンキー（keypad `=`・Clear）は従来どおり出さない。実測は Mac にテンキーがあるときに行い、無ければ文書値のまま完了報告に未実測と書く（§4.1 の未実測の行）。
- `vk_for_name(name, *, jis: bool = False) -> int | None`: 逆引き。**JIS のときは「共通の表から上書きした vk の行を除き、上書き表の行を足した 1 枚の表」で引く**（素直に 2 表を合わせると JIS の `[` `]` が vk 30 / 33 と 42 / 30 の両方に当たって `None` になるため）。その表で 1 つに決まらなければ `None`。`jis` は既定値 `False` にし、既存の呼び出し（`backend.py` の `register_key_hook`・`tests/test_macos_key_table.py`）は JIS の値を渡すよう追従する（`register_key_hook` は登録時の値で決める）。
- **送信だけの別名**（受信名には出さない）: `windows` → 左 Command 55・`left shift` → 56・`left ctrl` → 59・`left alt` → 58（既定のプリセット〔`windows+c` 等・Q2〕と `key_hold` の左右つきの名前〔`tk_keys.py` の `_KEY_HOLD_MODIFIER_KEYSYMS`〕を送れるように。Windows の keyboard ライブラリが同じ名前を受け付けるのと揃える）。`vk_for_name` はこの別名も引く。
- **Shift の要る文字**: US と JIS それぞれで「Shift を押して出る文字 → 元のキーの名前」の表（例 US: `!` → `1`・`@` → `2`・`_` → `-`・`+` → `=`・`{` → `[`・`:` → `;`・`"` → `'`・`?` → `/` 等 / JIS: `!` → `1`・`"` → `2`・`=` → `-`・`~` → `^`・`` ` `` → `@`・`{` → `[`・`+` → `;`・`*` → `:`・`}` → `]`・`_` → `ro`・`|` → `yen` 等）。印字どおりの物理キーの対応で、Windows の `_needs_shift`（keyboard ライブラリの対応）と同じ結果になるものに限る。

### `macos/backend.py`（`MacKeyboardBackend`）

- `set_layout_key_ids`: `is_jis_layout` の結果を属性 1 つへ代入する（フックのスレッドはこれを読むだけ）。`event_tap.py` の受信名の決定は `key_for_vk(vk, jis=...)` に替える。
- `resolve_send(key, resolver)`（§5.3 の解決順）:
  1. Shift の要る文字（上の表）→ 元のキーの vk で `KeySend("mac_shift", (vk,), key)`。
  2. 既知のキー名（`vk_for_name(key, jis=...)`。修飾キーの名前・テンキーの名前を含む）→ `KeySend("mac", (vk,), key)`。
  3. `resolver(key)` の `scan_code`（1〜255 の int）→ 表でその `scan_code` を持つ vk が**1 つだけ**なら `KeySend("mac", (vk,), key)`。テンキーと拡張キーの重なりなどで複数・0 件なら 4 へ。
  4. `ValueError(f"Unknown key name: {key!r}")`（Windows と同じ）。
- `press_send` / `release_send`: `CGEventCreateKeyboardEvent` + `CGEventPost` で送る。全イベントの `kCGEventSourceUserData` に `OWN_EVENT_MARK`（task_08b の定数）を付ける。
  - **フラグ**（§5.1「自分が送るイベント」）: backend が**自分で押している修飾キー**（press_send した修飾で、まだ release_send していないもの。左右別）を記録し、送るすべてのイベントのフラグをその記録だけで決めて `CGEventSetFlags` で明示する（共通ビット + 機種依存ビット・`key_table.MODIFIERS` / `COMMON_FLAGS`）。物理側の押下・抑止の状態（`ModifierState`）は混ぜない。修飾キー自身の press / release もこの記録を更新してからフラグを付けて送る。
  - `mac_shift` は Shift を押して送る（`needs_shift` が True を返し、呼び出し側〔`input_gateway`〕が `press_shift` で挟む既存の流れに乗る。press_send 自体は元のキーだけを送る）。
  - **例外（暫定 57 §5.1・v0.8）**: `mac_shift` を送るとき、物理の Shift が押されていれば（`MacWindowBackend.is_shift_down()` と同じ判定。呼び出し側が `press_shift` しない場合）、送るキーのフラグに Shift の共通ビットを足す（Windows で OS の Shift の状態が効いて `!` になるのと揃える）。Control・Option・Command は物理側を混ぜない。
- `identity_of`: 送るキーの互換の `(scan_code, extended)` を返す。受信の表の `scan_code` と、Windows で同じ物理キーの `identity_of` が返す `extended`（矢印・Home / End / PageUp / PageDown・Insert / Delete・右 Ctrl / 右 Alt・Windows キー・`num enter` / `num divide` が True）と同じ値（`held_inputs.py` が受信のイベントとの照合に使う）。
- `needs_shift`: `send.kind == "mac_shift"`。
- `press_shift` / `release_shift`: 左 Shift（vk 56）の press_send / release_send と同じ。
- `send_native_hotkey`: 常に `False`（`input_gateway` の既存の代替の経路 = キーを 1 つずつ押して離す、に任せる）。
- `write_text`: `CGEventKeyboardSetUnicodeString` で文字列を送る（印つき・フラグは自分の修飾の記録で明示）。長い文字列は 1 イベントに載る長さ（20 文字）ごとに分ける。
### `macos/backend.py`（`MacWindowBackend` の 2 メソッド）

- `is_shift_down` / `is_ctrl_alt_win_down` を `CGEventSourceFlagsState(kCGEventSourceStateHIDSystemState)` の共通ビットで実装する（§5.4「物理状態」。`input_gateway.send_mapped_key` が Shift を足すかどうかの判定に使う = phase 74 の「Ctrl / Alt / Win が押されていれば足さない」。Win = Command・Alt = Option）。例外時は `False`。他の `MacWindowBackend` のメソッドは task_11。

### 共通

- Quartz は task_08b と同じく関数内で遅延 import するか、送信の関数を引数で注入して既定値の解決を遅延する（Windows で `macos/` を import するテストが動くこと）。

### テスト（Windows でも動くもの。pyobjc を import しない）

- `tests/test_macos_key_table.py` に追加: `is_jis_layout`（`jis.json`・`us_tkl.json`・`de.json`・`jis_test.json` の実ファイルの id で判定）/ JIS の上書き 6 個の名前と `scan_code` / テンキー 16 個（`numpad_keys.py` の名前と `scan_code`・`is_keypad=True`）/ `vk_for_name` の JIS あり・なし（JIS で `[`・`]`・`@`・`^`・`:` がそれぞれ 1 つの vk に決まる・US で `[` が vk 33）/ Shift の要る文字の表の代表（US と JIS で `@` の扱いが違う: US は Shift + `2`・JIS は Shift なしの `@` キー）。
- `tests/test_macos_keyboard_backend.py` に追加（送信の関数を偽物に差し替える）: `resolve_send` の解決順 4 段（Shift の要る文字 / 既知の名前 / レイアウトの `scan_code` が 1 つに決まる / 決まらない・無い → `ValueError`）/ 送るイベントすべてに印 / `ctrl` を press_send してから `c` を送ると `c` に Control の共通ビットと左 Control のビットが付き、物理側で Control を抑止中でも変わらない / release_send で記録から外れる / 物理の Shift が押されているとき `!`（`mac_shift`）を送ると Shift の共通ビットが付き、`a`（`mac`）には付かない / `identity_of` の `extended`（矢印・右 Ctrl・`num enter`）/ `send_native_hotkey` が `False` / `write_text` の 20 文字ごとの分割 / `set_layout_key_ids` で受信名が JIS に替わる / 送信の別名（`windows` → 55 等）で `resolve_send` が通る / `is_shift_down`・`is_ctrl_alt_win_down` がフラグの共通ビットで決まる。
- `tests/test_os_backend_contracts.py`: 新しい契約 `set_layout_key_ids` を Windows・macOS の両方が持つ。
- `tests/test_layout_controller_scan_code.py` などレイアウトの切替のテストに、`_refresh_active_layout` が backend へ id の集合を渡すことを 1 件足す（偽の backend）。

## 読むファイル

- `instructions/history/57_mac_support.md` §5.1（128〜150 行の「修飾キーの抑止とフラグ」以降）・§5.3〜§5.3.2（179〜245 行）・§5.4 の表（247〜265 行付近）
- `keyseq/infrastructure/os_backend/macos/`（`backend.py`・`event_tap.py`・`key_table.py`・`modifier_state.py` の全体）
- `keyseq/infrastructure/os_backend/contracts.py:12-56`
- `keyseq/infrastructure/os_backend/windows/keyboard_backend.py:17-49,160-243`（送信の手本・拡張キーの表・`_needs_shift`）
- `keyseq/infrastructure/input_gateway.py:60-145`（`needs_shift` と Shift で挟む流れ・`send_native_hotkey` の代替の経路・`identity_of`）
- `keyseq/domain/numpad_keys.py`（テンキーの名前と走査コード）
- `keyseq/presentation/controllers/layout_controller.py:200-220`（`_refresh_active_layout`）
- `config/user/keylayout/jis.json` の id の一覧
- 既存テスト: `tests/test_macos_key_table.py`・`tests/test_macos_keyboard_backend.py`・`tests/test_os_backend_contracts.py`

## 含まない

- Tk のキー取得（`MacTkKeyTranslator`・aqua の keycode の解釈・`tk_keys.py` の修飾 keysym）・`Command` / `Option` の表示・キー取得中の入力ソースの切替（§8 Q4）（task_09a）
- Mac 用のレイアウトの見本（task_09b）。本タスクの JIS の判定は見本が `yen` / `ro` を持つ前提で、見本そのものは作らない
- Command の割り当て禁止（Q5）: `domain/key_identifiers.py` の `is_prohibited_assign_key` がすでに `left windows` / `right windows` を禁止しており、Command はその名前で受信する（task_08b）ので実装の変更は無い。確認は task_09a の目視
- `repeat_timing` の実装（`NSEvent.keyRepeatDelay` 等・task_11）・マウス・前面の判定・`MacWindowBackend` の `is_shift_down` / `is_ctrl_alt_win_down` 以外（task_11）
- 権限の案内・tap の障害の通知（task_10）
- ホットキー（`send_hotkey` の代替の経路）で Shift の要る文字を含む組み合わせ（例 `ctrl+!`）に Shift を足すこと（`press_key` は `needs_shift` を見ない。Windows の keyboard ライブラリは足すので差が出るが、既定のプリセットに該当が無く実害は小さい。完了報告に差として残す・起票レビュー参考 7）

## 確認

Windows（`.venv\Scripts\python.exe`。verifier が実行）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_macos_key_table tests.test_macos_keyboard_backend tests.test_os_backend_contracts tests.test_os_backend_boundary tests.test_layout_controller_scan_code tests.test_input_gateway_send` が失敗 0
- `-m unittest discover -s tests` が失敗 0・エラー 0（2065 件 + 追加分）
- `-m tests.smoke_app` が pass（`layout_controller.py` に触れるため Windows の tests_ui も 1 回流す: `-m unittest discover -s tests_ui` が失敗 0。同時に 1 本だけ）

Mac（`../../../.venv/bin/python`）:

- `tests` が基準線（`mac_test_baseline.md`）から増えない・smoke pass
- 実機目視（ユーザー）:
  1. 置換: `a` → `b` で別のアプリに `b` が入る。置換先が Shift の要る文字（例 `!`）で `!` が入る。物理の Shift を押したままでも `!` が入る
  2. §9 の 11: `ctrl` を元キーにして抑止しながら `ctrl+c`（または Mac の既定の `windows+c`）を送る割り当てでコピーが動く
  3. シーケンスの文字送信（日本語を含む文字列）が入力ソースによらず入る
  4. 自分の送信がフックで再度拾われない（置換の連鎖・無限ループにならない）
  5. task_08 のキュー版: メニュー表示中に押したキーが後からまとめて実行されない・停止キーが効く（reviewer 参考 2 = 排出中のモーダルで排出が止まる件の確認を含む）
  6. テンキーがあれば: テンキーの `1` と上段の `1` を別のキーとして割り当てられる（無ければ未実測と報告）
- JIS キーボードが無い間の §9 の 10 は単体テスト（文書値）で代え、完了報告に未実測と書く

## 完了条件

- 上記の Windows・Mac の確認 pass・**reviewer 採用**。
- 実機目視は Mac で本タスクで実施（ユーザー）。task_08b から移した ③④（修飾キーの抑止）は、修飾キーをキー取得で登録できるようになる task_09a の目視で行う。
- `instructions/common/codebase_map.md` の os_backend 節（`set_layout_key_ids`・`macos/` の送信）に追従（メイン）。
