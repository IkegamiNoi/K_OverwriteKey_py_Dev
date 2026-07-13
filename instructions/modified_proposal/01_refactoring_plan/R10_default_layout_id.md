# R10 申し送り

- `DEFAULT_KEYBOARD_LAYOUT_ID = "us_tkl"` を `domain/config.py` に追加し、domain/application/presentation の既定レイアウト参照を定数化した。
- presentation 側の既存公開名 `DEFAULT_LAYOUT_ID` は残し、domain 定数へのエイリアスにした。
- `"us_tkl"` リテラルは domain 定数定義の 1 件のみになった。
