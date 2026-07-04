# R12 申し送り

- stop/toggle key 表示、物理キーラベル表示、キーボードレイアウト UI の同期処理を `_sync_control_vars_from_data` に集約した。
- `new_config` / `_apply_loaded_data_to_ui` / `restore_default` はこの helper を呼ぶ形に置き換えた。
- `_apply_loaded_data_to_ui` の dirty flag 初期化や保存状態更新は従来どおり残している。
