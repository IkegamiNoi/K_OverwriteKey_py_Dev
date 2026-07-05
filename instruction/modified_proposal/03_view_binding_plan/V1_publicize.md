# V1: コントローラ属性の公開名化と tests_ui の新契約化

- 実施日: 2026-07-05

## 実施内容

1. `App.__init__` のコントローラ保持属性 8 個を公開名へリネーム（app.py 内の委譲メソッド本体も追従）:
   `_dirty_tracker`→`dirty_tracker` / `_stop_key_capture`→`stop_key_capture` / `_toggle_key_capture`→`toggle_key_capture` / `_config_io`→`config_io` / `_layout`→`layout` / `_keymap_panel`→`keymap_panel` / `_trigger_panel`→`trigger_panel` / `_hook`→`hook`
2. App 調整役メソッド 6 個を公開名化（参照元 views / 各コントローラ / tests_ui も追従）:
   `_toggle_stop_key_capture`→`toggle_stop_key_capture` / `_toggle_toggle_key_capture`→`toggle_toggle_key_capture` / `_start_stop_key_capture`→`start_stop_key_capture` / `_start_toggle_key_capture`→`start_toggle_key_capture` / `_mark_sequence_dirty`→`mark_sequence_dirty` / `_mark_keymap_dirty`→`mark_keymap_dirty`
3. `tests_ui/test_app_ui_flows.py` の呼び出し経路を新契約へ書き換え（アサーション不変）。対応表どおり 9 種を置換。
4. 委譲メソッドの削除は行っていない（公開名化のみ。二重経路で動作）。

## 完了条件の確認（重要な申し送り）

- `git grep -nE "self\._hook\b|self\._trigger_panel|..." -- keyseq` は **keyboard_window.py の `self._layout` 5 件のみ残存**。
  - これは `KeyboardWindow` クラス自身のインスタンスフィールド（`resolve_keyboard_layout()` の戻り値＝解決済みレイアウトオブジェクト）であり、App の `LayoutController` とは**完全に無関係**。§1.2 の付け替え対象外。リネームしてはならない。
  - よって App のコントローラ属性については完了条件（0 件）を満たす。
- `tests/test_dirty_state.py` の `test_mark_sequence_dirty_*` / `test_mark_keymap_dirty_*` は DirtyStateTracker を直接検証するテスト関数名であり、App の調整役メソッド参照ではない。置換対象から除外した（正しい）。

## 検証結果

- compile OK / tests 59 OK / tests_ui 9 OK / SMOKE OK
- 手動確認（GUI 操作）は自動実行環境のため未実施。標準検証で代替。
