# task_03a_strengthen_tests

## 目的

task_03 の統合レビュー（deep-reviewer「修正して採用」・codex-reviewer P3 × 3・2026-11-25・ユーザー判断「推奨どおり」）で採用した、テストの検出力の補強。
**テストのみ・keyseq/ は変えない**。根拠は暫定 61 §4・§5・§7-1・§7-7b。

## 対象範囲（テストのみ）

**既存テストの途中に差し込まない（各クラスの最後へ）。既存テストの期待値は 1 の 1 件以外変えない。apply_patch で編集し、Python で書き換えない。**

1. `tests_ui/test_keyboard_key_text.py` の `test_uppercase_mapping_displays_case_and_skips_layout_lookup`（task_02 で追加）: 差し替えた `key_display_name` の比較を、本物（`keyboard_layouts.py:31` で小文字化して引く）と同じく大小を区別しない形（`name.strip().lower() == "a"`）にする。期待値（キー `1` の枠 = `"A"`・キー `2` の枠 = `"x-name"`）は変えない。これで大文字の迂回を外すと落ちるテストになる。
2. `tests/test_macos_keyboard_backend.py` の `MacKeyboardSendTests` の最後へ: 既存の偽 Quartz（`setUp` の `fake_quartz()`）で、
   - `self.keyboard.press_send(self.resolve("shift"))` の後 `sent_modifiers_down()` が `(True, False)`、`release_send` の後 `(False, False)`。`command` で `(False, True)` → 離して `(False, False)`。
   - **gateway を通した通しの確認**: `input_gateway.get_backend` を、`keyboard=self.keyboard`・`window`（`is_shift_down` / `is_ctrl_alt_win_down` が偽）の SimpleNamespace に patch し、`press_send(shift)` の後に `InputGateway().send_mapped_key("A")` を呼ぶ。`CGEventPost` で送られたイベントに、追加の Shift の押下 / 離し（VK 56 のキーイベント）が無く、送った後も `56` が `self.keyboard._sent_modifiers` に残る。`InputGateway` の `resolve_send` が使うレイアウトの解決は既存の他のテストの patch の仕方に合わせる（必要なら `resolve_send` だけ `self.resolve("A")` を返す patch でよい）。
3. `tests/test_config_service.py` の `test_round_trip_preserves_content`（`:61`）と同じクラスの最後へ: `make_runtime_data()` のキーマップの `mappings` に大文字と小文字を混ぜて（例: `{"x": "A", "y": "b"}` を足す）`save_runtime_data` → `load_runtime_data_from_keymap_set_path` で往復し、読み込んだキーマップの `mappings` に `"x": "A"`・`"y": "b"` が残る。保存されたキーマップのファイル（`user/keymaps/<name>.json`）の中身にも `"A"` が書かれている。
4. `tests_ui/test_keyboard_window_scan_code.py` の最後へ: Shift を押していても英字以外の 1 文字（`"1"`）は変わらない（`self._record("1", True)` → `"1"`）。

## 読むファイル

- `tests_ui/test_keyboard_key_text.py:95-165`・`keyseq/presentation/keyboard_layouts.py:25-36`
- `tests/test_macos_keyboard_backend.py:1-60`（偽 Quartz）・`:473-485`・`:550-600`・`:740-770`
- `keyseq/infrastructure/input_gateway.py:70-110`・`keyseq/infrastructure/os_backend/macos/keyboard_backend.py:180-260`
- `tests/test_config_service.py:1-130`（`make_runtime_data` と往復のテスト）
- `tests_ui/test_keyboard_window_scan_code.py:25-45`・`:135-180`

## 含まない

- keyseq/ の変更・正本の更新（task_04）・実機目視（task_03）
- リピート停止の直接テスト（deep 3）: `HeldInputs` は gateway の `resolve_send` + `identity_of` で照合し（`held_inputs.py:87-90`）、`A` と `a` の識別の一致は両 OS のテスト（task_01）で確かめているため、偽の gateway で重ねて書かない（メイン判断）

## 確認

- verifier（Windows・tests_ui は 1 本だけ・`taskkill` 禁止）: `compileall` clean / 追加・変更したテストが実行され pass / `unittest discover -s tests` 全 pass / 変更した tests_ui の 2 モジュール pass
- メインで 1 の検出力を確かめる: `keyboard_window.py` の大文字の迂回を一時的に外すと 1 のテストが落ちること（verifier に一時変更を依頼しない・メインが scratchpad のコピーで確かめるか、reviewer がコードの読みで確かめる）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
