# task_09a_macos_tk_capture_display

## 目的

macOS の**Tk のキー取得**（`MacTkKeyTranslator`・aqua の修飾 keysym）、取得中の**入力ソースの切替**（暫定 57 §8 Q4）、キー名の **`Command` / `Option` の表示**（§5.3 末尾）を実装する。task_08b から移した修飾キーの抑止の目視（③④）もここで行う。

- 変更は `os_backend/macos/`（Tk の解釈・入力ソース）と presentation の Tk のキー名の正規化（`tk_keys.py`）、表示の差し替えの口（`domain/key_symbols.py` は OS 判定を持たず、presentation の組み立てで注入）に限る。application・JSON スキーマは不変。pyobjc の import は `macos/` の中に閉じる。
- Windows の動作は変わらない。
- 前提: task_09（受信の表の JIS の名前・テンキー・`set_layout_key_ids`）が済んでいる。

## 対象範囲

### `macos/backend.py`（`MacTkKeyTranslator`）

aqua の Tk の `keycode` は `(vk << 24) | … | 文字コード`（§4.1）。上位 8 ビットを vk として task_09 の表（`key_table.key_for_vk`・選択中のレイアウトの JIS 判定を含む）で解釈する。上位 8 ビットが `0xFF`（IME の入力中で vk が失われた）なら解釈しない。

- `numpad_name(keycode, state)`: vk がテンキーならその名前（`numpad_keys.py` の名前）、それ以外は `""`。
- `vk_to_scan_code(vk)`: 引数は Tk の `keycode` そのもの（`keymap_panel_controller.py:467` の呼び方）。上位 8 ビットの vk を表で引き、互換の `scan_code`、無ければ `None`。
- `vk_to_char(vk)`: 同じく表の名前が 1 文字ならその文字、それ以外は `""`。
- JIS 判定は `MacKeyboardBackend` が持つ値（task_09 の `set_layout_key_ids`）を読む。`create_backend` で `MacKeyboardBackend` の参照を `MacTkKeyTranslator` のコンストラクタへ渡し、その JIS 判定の属性を読む（表の解釈は `key_table` の関数だけで行い 2 か所に書かない）。

### `presentation/tk_keys.py`（修飾 keysym・§4.1 の「Tk の修飾 keysym」）

- aqua では Command = `Meta_L` / `Meta_R`、Option = `Alt_L`（右は `Alt_R` の見込み）、Control = `Control_L`、Shift = `Shift_L` / `Shift_R`、**fn = `Super_L`**。
- `normalize_tk_keysym` / `normalize_key_hold_tk_keysym` の表に `meta_l` / `meta_r` → `windows`（key_hold は `left windows` / `right windows`）を足す。**aqua のときだけ** `super_l` / `super_r` を「取れないキー」（`UNRESOLVED_KEY_NAME` = `??`）として扱い、`windows` にしない（fn を Command と誤認しない）。aqua の判定は `tk_platform.is_aqua(widget)` を使う（`sys.platform` を見ない）。`normalize_tk_key_event` は `event.widget` から判定し、widget の無い呼び出し（テスト等）は従来どおり。
- 既存の Windows の対応（`super_l` → `windows` 等）は変えない。

### `macos/backend.py`（`MacImeBackend`・§8 Q4 の入力ソースの切替）

`KeyCaptureImeTracker`（`key_capture_ime.py:34-100`）は取得の開始で `get_own_open_status(root) is True` なら `set_own_open_status(root, False)` を呼び、終了（全取得の終わり・1 回だけ）で `get_own_open_status(root) is False` なら `set_own_open_status(root, True)` を呼ぶ。この既存の流れに乗せる（入れ子は tracker がすでに外側の 1 回にまとめている）。

- `get_own_open_status(window) -> bool | None`: 現在の入力ソース（`TISCopyCurrentKeyboardInputSource`）が ASCII 可能でなければ `True`、ASCII 可能なら `False`。取れなければ `None`。
- `set_own_open_status(window, False)`: 元の入力ソースを記録し、ASCII 可能な入力ソース（`TISCopyCurrentASCIICapableKeyboardInputSource`）へ切り替え（`TISSelectInputSource`）、**読み直して切替先になったかを確かめる**。なっていれば切替先を記録して `True`、失敗なら記録を消して `False`（取得は止めない・vk が失われたキーは `??`）。
- `set_own_open_status(window, True)`: 記録があり、**現在の入力ソースが記録した切替先と同じときだけ**元の入力ソースへ戻す（取得中にユーザーが自分で変えたら戻さない）。どちらでも記録を消す。戻したら `True`。
- 例外は `logging` で残して `None` / `False` を返す（取得を止めない）。`Capabilities.ime_control` は変えない（文字送信は IME を経由しない・Q4）。`disable_for_text` / `restore_after_text` / `restore_ime_now` は何もしないまま。
- TIS の関数は Carbon（pyobjc の `HIToolbox` または `Carbon`）から遅延 import する。入手できない場合は `None` / `False` を返す（Windows のテストでは import しない）。

### `domain/key_symbols.py` + 組み立て（`Command` / `Option` の表示・§5.3 末尾）

- `key_symbols.py` に修飾キーの表示名の差し替え表を持たせる（既定は空 = 今の表示のまま）。`set_modifier_display_names(mapping: dict[str, str])` で差し替える。`display_key_name` はキー名を `+` で区切らずに受け取る今の契約のまま、名前の中の語 `windows` → `Command`・`alt` → `Option` を差し替え表で置き換える（`alt gr` は置き換えない。保存するキー名は変えない）。domain に OS 判定を入れない。
- 差し替え表の中身は `OsBackend` の項目（`modifier_display_names: dict[str, str]`。Windows は空・macOS は上の 2 語）として持ち、App の組み立て（`presentation/app.py` の既定プロファイルを注入しているところと同じ場所）で 1 回だけ渡す。
- 対象は `display_key_name` を通る表示（トリガーのキー〔`domain/config.py:471`〕・`key_hold` の表示〔`key_hold.py:130-132`〕・キーボードUIで割り当てたキー名の表示〔`keyboard_window.py:467`。枠の印字はレイアウトの `label` が先に使われるので変わらない〕）だけ。ホットキーのラベル・プリセットの表示・エラーの文言は変えない。

### テスト

- `tests/test_macos_tk_key_translator.py`（新規・pyobjc 不要）: aqua の keycode から vk を取り出す / テンキーの名前 / `vk_to_scan_code`・`vk_to_char` / 上位 8 ビットが `0xFF` なら解釈しない / JIS を選択中は vk 33 → `@`。
- `tests/test_tk_keys.py` に追加: aqua で `Meta_L` → `windows`（key_hold は `left windows`）/ aqua で `Super_L` → `??` / aqua でない場合の `Super_L` → `windows` は不変。
- `tests/test_macos_ime_backend.py`（新規・TIS の関数を偽物に差し替える）: 切替して読み直しで確かめる / 切替失敗で `False`・記録なし / 戻すのは切替先のままのときだけ / ユーザーが変えたら戻さない / 例外で取得を止めない。
- `tests/test_key_symbols.py` に追加: 差し替え表が空なら不変 / `left windows` → `left Command`・`alt` → `Option`・`alt gr` は不変。差し替えるテストは `tearDown` で空の表へ戻す（domain のモジュールの状態が他のテストへ漏れない）。
- `tests/test_os_backend_contracts.py`: `OsBackend` のフィールド名を完全一致で検査している箇所（20〜25 行付近）に `modifier_display_names` を足し、両 OS が持つことを確かめる。

## 読むファイル

- `instructions/history/57_mac_support.md` §4.1 の「Tk の `keycode`」「Tk の修飾 keysym」の行（117〜118 行）・§5.3（179〜200 行）・§8 Q4（297〜302 行付近）
- `keyseq/infrastructure/os_backend/macos/backend.py`（全体）・`macos/key_table.py`（task_09 後の全体）
- `keyseq/infrastructure/os_backend/contracts.py:74-100`（`ImeBackend`・`TkKeyTranslator`）と `OsBackend` の定義
- `keyseq/infrastructure/os_backend/windows/tk_key_translator.py`（手本）
- `keyseq/presentation/tk_keys.py`（全体）・`tk_platform.py:1-12`
- `keyseq/presentation/key_capture_ime.py:30-100`
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:461-476`（`vk_to_scan_code` / `vk_to_char` の呼び方）
- `keyseq/domain/key_symbols.py`・`presentation/app.py:117`（既定プロファイルの注入箇所）・`contracts.py:114-125`（`OsBackend`）

## 含まない

- 送信・受信の表・JIS の判定（task_09）
- Mac 用のレイアウトの見本（task_09b）
- 割り当て禁止の文言（「Windowsキー・Caps Lock・AltGr は…」）の Mac 向けの言い換え（task_11 の無効化の UI と合わせて扱う。本タスクでは変えない）
- 権限の案内（task_10）・`repeat_timing` と残りの機能（task_11）

## 確認

Windows（`.venv\Scripts\python.exe`。verifier が実行）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_macos_tk_key_translator tests.test_tk_keys tests.test_macos_ime_backend tests.test_key_symbols tests.test_os_backend_contracts tests.test_key_capture_ime` が失敗 0
- `-m unittest discover -s tests` が失敗 0・エラー 0
- `-m unittest discover -s tests_ui` が失敗 0（`tk_keys.py`・`app.py` に触れるため。同時に 1 本だけ）
- `-m tests.smoke_app` が pass

Mac（`../../../.venv/bin/python`）:

- `tests` が基準線から増えない・smoke pass
- 実測: テンキーがあれば Tk の keycode（§4.1 の未実測の行）。右 Option の keysym（`Alt_R` の見込み）。結果は暫定 57 §4.1 へメインが追記
- 実機目視（ユーザー）:
  1. 取得（キーマップの切替キー・置換元キー・トリガー）で文字キー・記号キー・矢印・修飾キー（Shift・Control・Option）が記録でき、Command は禁止のキーとして拒否される（Q5・`is_prohibited_assign_key`）。fn は `??` で記録されない
  2. かな入力のまま取得を始めても物理キーが記録され、取得の終了後に元の入力ソースへ戻る。取得中に自分で入力ソースを変えたら戻さない（§9 の 12）
  3. 一覧・キーボードUIで `windows` / `alt` の付く名前が `Command` / `Option` と表示される（保存されたキー名は変わらない）
  4. task_08b から移した目視: ③ 左 Command を元キーにした既存の割り当て（Q5 で新規には作れないため、設定 JSON に直接書いたもの = 既存データの扱い `features.md` §4.6）を抑止しても、続く文字キーが Command+文字にならず、抑止を外した後に別のアプリで通常に入力できる ④ 左 Shift を抑止・右 Shift を素通しで、右 Shift の大文字が打てる・左右の離す順を変えても修飾が残らない
  5. キーボードUIの右クリックで割り当てが消える（task_05c の残り）・Command+Option+P でプリセット管理が開く（段階 ② の区切り L7）

## 完了条件

- 上記の Windows・Mac の確認 pass・**reviewer 採用**。
- 実機目視は Mac で本タスクで実施（ユーザー）。
- `instructions/common/codebase_map.md` の os_backend 節・`tk_keys.py`・`key_symbols.py` の記述に追従（メイン）。
