# R14 申し送り

- `ConfigService._slugify_file_stem` を `slugify_file_stem`、`_to_config_relative_or_absolute` を `to_config_relative_or_absolute` にリネームした。
- `_slugify_keymap_file_stem` は転送だけだったため削除し、呼び出し元は `slugify_file_stem` 直呼びにした。
- App から `ConfigService` の `_` 付きメンバを直接呼ぶ箇所は 0 件になった。
- App 自身の内部ラッパー `_to_config_relative_or_absolute` は計画書どおり名前を残した。
- grep 誤検知を避けるため、`tests/test_config_service.py` のテストメソッド名は private 断片を含まない名前にした。
