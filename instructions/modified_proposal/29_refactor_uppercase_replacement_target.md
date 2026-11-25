# 29_refactor_uppercase_replacement_target

phase 81（置換先に英字の大文字）の `/refactor_check` で「推奨」になった、英字 1 文字の大文字の判定の重複の集約案。**挙動は変えない**。ユーザー承認前に実施しない。

判定（PHASE_BASE = `2fa77e03`・keyseq の変更 9 ファイル・+54/-19）: M3 = 該当（下の R1・R2）/ M1 = `keymap_panel_controller.py` 691 行・`keyboard_window.py` 657 行は 600 行超だが増分 +2 / +7 で非該当 / M2・M4・M5・M6 = 該当なし。

## 項目 0: 安全網の確認

- 対象は phase 81 で足したテストが覆っている: `tests/test_domain_config.py`（`MappingTargetNormalizationTest`）・`tests/test_input_gateway_send.py`・`tests/test_macos_keyboard_backend.py`・`tests/test_config_service.py`（往復）・`tests_ui/test_keyboard_key_text.py`・`tests_ui/test_keyboard_window_scan_code.py`。
- 実施前後に verifier で Windows の `compileall` / `tests` 全件 / 上の tests_ui の 2 モジュール / smoke が pass。Mac の backend の変更を含むため、Mac で `tests/test_macos_keyboard_backend.py` を流す（実機目視は不要の見込み）。

## R1: 「英字 1 文字の大文字か」を domain の 1 関数にする

- 対象（いずれも phase 81 で追加）: `keyseq/domain/config.py:139`・`infrastructure/os_backend/macos/keyboard_backend.py:188`・`infrastructure/os_backend/windows/keyboard_backend.py:193`・`:230`・`:242`・`:260`・`presentation/keyboard_window.py:471`（7 か所）
- 問題（M3）: `len(x) == 1 and "A" <= x <= "Z"` が 3 層 7 か所にある。置換先の大文字の範囲（例: 対象の文字を広げる）を変えるときに全部を直す必要がある。
- どう変えるか: `domain/config.py` に `is_uppercase_mapping_target(value: str) -> bool` を置き、`normalize_mapping_target` と各所から呼ぶ（infrastructure → domain の依存は既存〔`os_backend/*/backend.py` が `domain.default_profile` を import〕と同じ向き）。

  ```python
  def is_uppercase_mapping_target(value: str) -> bool:
      return len(value) == 1 and "A" <= value <= "Z"
  ```

  - `keyboard_window.py:633` の `"a" <= key <= "z"`（記録時の小文字の判定）は意味が違う（記録した名前が英字か）ので対象外。
- 完了条件: 項目 0 が pass・`grep -rn '"A" <=' keyseq` が `domain/config.py` の 1 件だけ。
- リスクと戻し方: import の循環（`domain/config.py` は infrastructure を import しないため起きない見込み）。1 コミットで行い、失敗したら revert。
- 依存: なし。

## R2: Windows の press / release で送る名前を 1 つの補助にする

- 対象: `keyseq/infrastructure/os_backend/windows/keyboard_backend.py:230`・`:242`
- 問題（M3）: `send.key.lower() if <大文字> else send.key` の同じ式が press と release にあり、片方だけ直すと押しと離しのキーが食い違う（リピートが止まらない等）。
- どう変えるか: 同ファイルに `_keyboard_name(send: KeySend) -> str` を置き、press / release から呼ぶ（R1 の関数を使う）。
- 完了条件: 項目 0 が pass。
- リスクと戻し方: R1 と同じ。
- 依存: R1 の後（同じコミットでよい）。
