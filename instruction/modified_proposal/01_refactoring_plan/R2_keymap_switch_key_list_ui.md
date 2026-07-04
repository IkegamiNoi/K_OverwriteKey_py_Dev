# R2 申し送り

- `app.py` から未到達のキーマップ切替キー専用リスト UI ハンドラ群を削除した。
- `keymap_switch_key_listbox` 関連参照、専用キャプチャ状態、専用ソートヘルパは 0 件になった。
- `KeymapEditDialog` 経由で使う `_validate_keymap_switch_assignment` は定義と呼び出しの 2 件を残している。
