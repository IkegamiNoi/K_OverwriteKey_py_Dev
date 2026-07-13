# R7 申し送り

- Tk keysym から keyboard 表記への変換を `keyseq/presentation/tk_keys.py` に集約した。
- `App` / `ActionDialog` / `TriggerDialog` / `KeymapEditDialog` は既存メソッドを残し、共通 helper に委譲する形にした。
- `KeyboardWindow` は既存のスキャンコードフォールバックを維持し、辞書だけ共通定数を参照する形にした。
- 計画書の `git grep -c "control_l" -- keyseq` は既存の `keyseq/application/key_state_manager.py` の修飾キー別名にもヒットする。これは Tk keysym マップではなく、application から presentation helper へ依存させるのは層違反になるため変更していない。
