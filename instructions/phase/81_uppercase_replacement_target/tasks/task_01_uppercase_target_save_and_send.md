# task_01_uppercase_target_save_and_send

## 目的

キーマップの置換先に英字の大文字（`A`〜`Z`）を保存・判定し、小文字と同じキーに Shift を足して送れるようにする（暫定 61 §3・§4）。
あわせて macOS の Shift の足し方の判定に、key_hold などアプリが送って押したままの修飾キーを含める（§4・記号と英字で共通）。
**domain / application / infrastructure（input_gateway・os_backend）のみ・presentation は変えない（task_02）・JSON スキーマの型は不変**。

## 対象範囲（domain・application・infrastructure）

### `keyseq/domain/config.py`

- 関数 `normalize_mapping_target(value: Any) -> str` を新設する（`coerce_key_name` の近く）。
  - 文字列でなければ `""`。trim した結果が ASCII の英字 1 文字の大文字（`"A"`〜`"Z"`）ならそのまま返す。それ以外は `normalize_key_name`（trim + 小文字化 + 別名）の結果を返す。
  - 全角・アクセント付きの文字は対象外（小文字化の規則のまま）。
- `_normalize_keymap_mappings`（`:328`）の置換先（`target`）を `normalize_mapping_target` に替える。置換元（`source`）は `normalize_key_name` のまま。

### `keyseq/application/keymap_service.py`

- 置換先の取得（`:239`）・`set_mapping` の `target`（`:288`）と前の値（`:293`）を `normalize_mapping_target` に替える。`a` → `A` の付け替えは「変更あり」になる（`previous != target`）。置換元は変えない。

### `keyseq/application/input_router.py`

- 置換の判定（`:143`）の置換先の正規化を `normalize_mapping_target` に替える（`SendKeyAction.target_key` が `"A"` になる）。トリガー・停止・トグル・切替の判定は変えない。

### `keyseq/infrastructure/os_backend/windows/keyboard_backend.py`

- `resolve_send`: 名前が ASCII の英字 1 文字の大文字なら、**小文字の名前で解いた結果と同じ kind / values** の `KeySend` を、`key="A"`（元の大文字）で返す（大文字の名前のまま keyboard の表で解かない・暫定 61 §4）。
- `press_send` / `release_send`: `keyboard` の kind で `send.key` が英字 1 文字の大文字なら、小文字の名前で押す / 離す（`keyboard.press(send.key.lower())`）。他の名前は今のまま。
- `needs_shift`: `send.key` が英字 1 文字の大文字なら `True`。それ以外は今の `_needs_shift` のまま（phase 74 の記号は変えない）。

### `keyseq/infrastructure/os_backend/macos/keyboard_backend.py`

- `resolve_send`: 名前が ASCII の英字 1 文字の大文字なら、小文字の名前で VK を引き（`vk_for_name(key.lower(), jis=...)`）、`KeySend("mac_shift", (vk,), key)` を返す。`SHIFTED_*` の表には足さない（どちらでもよいと暫定 61 にあるが、この形に決める）。小文字の `a` は今のまま `mac`。
- 送信済みの修飾の問い合わせを足す（下の契約）: `_sent_modifiers` から作るフラグ（`_send_flags()`）で、Shift の有無と Control / Option / Command の有無を返す。

### `keyseq/infrastructure/os_backend/contracts.py` / `windows/keyboard_backend.py`

- `KeyboardBackend` に `sent_modifiers_down(self) -> tuple[bool, bool]` を足す（戻り値 = (Shift を送って押したままか, Ctrl / Alt / Windows〔macOS は Control / Option / Command〕を送って押したままか)）。
  - macOS: 上の実装。Windows: `(False, False)`（Windows の `is_shift_down` / `is_ctrl_alt_win_down` は OS のキーの状態を読み、送ったキーも含まれる見込みのため・実機確認は task_03）。
- テスト用の偽の keyboard バックエンドがあれば同じメソッドを足す（`grep -rn "def needs_shift" tests tests_ui` で確かめる）。

### `keyseq/infrastructure/input_gateway.py`

- `send_mapped_key`（`:80`）: Shift を足すかの判定を「`needs_shift` が真」かつ「物理の Shift（`window.is_shift_down()`）も**送信済みの Shift**も無い」かつ「物理の Ctrl / Alt / Windows も**送信済み**のそれも無い」に変える（`kb.sent_modifiers_down()` を使う）。送り方（Shift 押下 → キー → 離し → Shift 離し・足した Shift は必ず離す）は変えない。

### テスト（`tests/`）

**既存テストの途中に新しいテストを差し込まない（各ファイルの末尾か、既存のクラスの最後へ足す）。apply_patch で編集し、Python で書き換えない。**

- 期待値の変更（暫定 61 §7-8・置換先の大文字は保ち、置換元は小文字）: `tests/test_config_service.py:2090`・`:2097`・`:2101` / `tests/test_domain_config.py:484`・`:497` / `tests/test_keymap_service.py:77-80`。該当のテストの意図（小文字化の確認）を保ち、置換先の大文字だけ期待値を大文字にする。
- 追加:
  - `normalize_mapping_target`: `"A"`→`"A"` / `" B "`→`"B"` / `"a"`→`"a"` / `"F1"`→`"f1"` / `"Shift"`→`"shift"` / `"AB"`→`"ab"` / `"Ä"`（英字以外）→小文字化 / 非文字列→`""`。
  - 読込: `mappings` が `{"X": "A", "Y": "b", "Z": "F2"}` → `{"x": "A", "y": "b", "z": "f2"}`（単一 JSON と split の両方の読込経路が既存のテストにあればその形で）。
  - `KeymapService.set_mapping`: `a` → `A` で「変更あり」・保存される値が `"A"`。
  - `InputRouter`: 置換先 `"A"` の置換で `SendKeyAction(target_key="A")`。
  - `InputGateway.send_mapped_key`（`tests/test_input_gateway_send.py` の偽バックエンドの形）: 送信済みの Shift があれば Shift を足さない / 送信済みの Ctrl 等があれば足さない / どちらも無く `needs_shift` が真なら足す。
  - macOS（`tests/test_macos_keyboard_backend.py`・既存の `a` は Shift 不要のテスト〔`:670`〕の後ろ）: `resolve_send("A")` が `mac_shift` で VK が `a` と同じ・`identity_of` が `a` と同じ / `needs_shift` が真 / `sent_modifiers_down()` が key_hold で送った Shift・Command を反映する。
  - Windows: `resolve_send("A")` の kind / values が `"a"` と同じ・`needs_shift` が真・`identity_of` が `a` と同じ。keyboard ライブラリが要るテストは既存の Windows のテストの形（skip 条件）に合わせる。
  - 契約（`tests/test_os_backend_contracts.py`）: `sent_modifiers_down` が両 OS の keyboard バックエンドにある。

## 読むファイル

- [暫定 61](../../../history/61_uppercase_replacement_target.md) §1・§3・§4（`ファイルパス:行` の起点）
- `keyseq/domain/config.py:115-140`・`:320-340`
- `keyseq/application/keymap_service.py:230-300`・`keyseq/application/input_router.py:135-150`
- `keyseq/infrastructure/input_gateway.py:70-110`
- `keyseq/infrastructure/os_backend/contracts.py:40-70`
- `keyseq/infrastructure/os_backend/windows/keyboard_backend.py:40-60`・`:180-260`
- `keyseq/infrastructure/os_backend/macos/keyboard_backend.py:70-100`・`:180-270`
- 手本のテスト: `tests/test_input_gateway_send.py`（全体）・`tests/test_macos_keyboard_backend.py:640-700`・`tests/test_os_backend_contracts.py:1-60`

## 含まない

- キーボードUI の記録（Shift + 英字 → 大文字）と表示・`keymap_panel_controller.py:633` の割り当ての正規化（task_02）
- 統合確認・実機目視（Windows / macOS・Caps Lock・key_hold の Shift の確認）（task_03）
- 正本・`codebase_map.md` の更新（task_04）
- 置換元・トリガー・hotkey・key_hold のキー名の変更・`SHIFTED_*` の表の変更・Caps Lock を見る処理

## 確認

- verifier（Windows・`.venv`）:
  - 実測: `python -c "from keyseq.infrastructure.os_backend.windows import keyboard_backend as k; print(k._needs_shift('A'), k._needs_shift('a'))"` 相当で、従来の `_needs_shift('A')` の値を記録（暫定 61 §4 の前提の確認。`False` の見込み）
  - `compileall keyseq tests` clean / `unittest discover -s tests` 全 pass（件数・skip を記録）/ `-m tests.smoke_app` pass
  - 変更した / 追加したテストの名前が実行されていること
- 差分の直読み（メイン）: 置換先以外の正規化を変えていないこと・既存テストの途中への差し込みが無いこと

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_03 でまとめて実施。
