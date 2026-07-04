# R6 申し送り

- `app.py` と `keyboard_window.py` のローカル `normalize_key_name` 定義を削除し、`keyseq.domain.config.normalize_key_name` に統一した。
- 呼び出し名は変えず import 先だけを変更しているため、挙動は同一。
