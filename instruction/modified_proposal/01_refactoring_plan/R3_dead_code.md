# R3 申し送り

- `ConfigService` の未使用読込/保存互換メソッド、`App._load_if_exists`、`keyboard_layouts` の未使用保存ヘルパ、`AppState.request_main_thread` を削除した。
- 削除前後の grep で、対象シンボルは定義自身または削除対象同士の参照だけであることを確認した。
- `ConfigService.load` / `load_legacy_runtime_data` / `export_runtime_data` / startup 系の使用中メソッドは残している。
