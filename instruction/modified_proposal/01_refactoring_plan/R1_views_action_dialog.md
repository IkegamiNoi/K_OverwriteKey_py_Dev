# R1 申し送り

- `views.py` の重複 `ActionDialog`、`FullView._cur_sel_or`、`CompactView._cur_sel_or` を削除した。
- `ActionDialog` 削除に伴い `messagebox` / `pynput.mouse` / `PresetManagerDialog` の import も不要になったため削除した。
- `views.py` には `ActionDialog` より後に残すコードは無かった。
