# R13 申し送り

- `_refresh_keymap_switch_ui` エイリアス定義と全呼び出しを削除した。
- 呼び出し箇所はいずれも同じ処理ブロック内で `_refresh_keymap_list_ui` を実行済みだったため、最終表示状態は変わらない。
- 削除時に一度インデント崩れが出たが、修正後に compileall / unittest / smoke を通している。
