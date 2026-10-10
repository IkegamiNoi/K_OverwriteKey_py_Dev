# task_01_domain_and_os_timing

## 目的

暫定 36 の domain と infrastructure の部品（§3・§4.6・§5 の一覧の書式・§6 の OS のリピート設定）。application・presentation の配線は含まない（task_02・03）。JSON の読込は変えない（`repeat` は実行時に判定）。

## 対象範囲

### domain `keyseq/domain/key_hold.py`
- `MODIFIER_KEY_NAMES`（frozenset）: keyboard の `all_modifiers` の 13 名（`alt` / `alt gr` / `ctrl` / `shift` / `windows` と `left` / `right` つき）+ 別名
  `altgr` / `cmd` / `command` / `control` / `left control` / `right control` / `left menu` / `left win` / `right win` / `win` / `option`（2026-10-11 に keyboard の `_canonical_names` から実測した、修飾キーに当たる別名）。
  domain は keyboard を import しない（直書きの集合）
- `is_modifier_key(name: str) -> bool`: trim + 小文字で集合を引く
- `wants_repeat(action) -> bool`: `action.get("repeat") is True`（bool の True だけ）
- `is_repeat_enabled(action) -> bool`: `parse_key_hold` が成功し、押す（`edge` = down）・キーボードの行・`wants_repeat`・修飾キーでない、のすべてを満たすとき True（暫定 36 §4.1「リピートが有効な押す行」）
- `format_key_hold_value`: `is_repeat_enabled` が True の行は末尾に ` (リピート)`（半角の括弧・先頭に半角空白）を付ける（例 `[押す] a (リピート)`）。それ以外・不正な行の `[key_hold] …` は従来どおり（§5）

### infrastructure `keyseq/infrastructure/input_gateway.py`
- `keyboard_repeat_timing() -> tuple[int, int]`（待ち ms, 間隔 ms）: Windows では `ctypes.windll.user32.SystemParametersInfoW` で `SPI_GETKEYBOARDDELAY`（0x16・UINT）と `SPI_GETKEYBOARDSPEED`（0x0A・DWORD）を読む
  - 換算: 待ち = 250 × (n + 1)（n = 0〜3）/ 間隔 = round(1000 / (2.5 + n × 27.5 / 31))（n = 0〜31。n = 0 → 400・n = 31 → 33）
  - 範囲外の値・呼び出しの失敗（戻り値 0・例外）・Windows 以外は**それぞれ**既定値（待ち 500・間隔 33）。片方だけ失敗したら、成功した方は換算値を使う
  - 換算は純関数に分けてテストできるようにする（例: モジュール内の `repeat_delay_ms(n)` / `repeat_interval_ms(n)`）

### テスト
- tests: `is_modifier_key`（全 24 名 + 大文字・前後空白・`a` / `enter` / `menu` は False）/ `wants_repeat`（True / False / 無し / `"true"` / 1）/
  `is_repeat_enabled`（押す + キー + True のみ True。離す・マウス・修飾キー・別名 `control`・`repeat` 無し・不正な行は False）/
  一覧の書式（` (リピート)` の有無・修飾キーには付かない・不正な行は従来どおり）/
  換算（n = 0・1・3、n = 0・15・31）・範囲外・`SystemParametersInfoW` の失敗（ctypes を差し替え・片方だけ失敗）・Windows 以外（`sys.platform` の差し替え）の既定値
- 既存の一覧の書式のテスト（`tests/test_key_hold.py`・`tests_ui/test_key_hold_presentation.py` 等）が変わらず通ること（`repeat` の無い行の書式は不変）

## 読むファイル

- `instructions/history/36_key_hold_auto_repeat.md` §3・§4.1・§4.6・§5・§6
- `keyseq/domain/key_hold.py`（全体）・`keyseq/infrastructure/input_gateway.py`（全体）
- `tests/test_key_hold.py`・`tests/` の input_gateway のテスト（ctypes の差し替えの手本があれば）

## 含まない

- `KeyRepeater`・`HeldInputs` / `ActionExecutor` の変更（task_02）・App の配線・ダイアログ（task_03）・正本の改訂（task_05）

## 確認

- 上記テスト（実行は verifier）・reviewer（5 観点）
