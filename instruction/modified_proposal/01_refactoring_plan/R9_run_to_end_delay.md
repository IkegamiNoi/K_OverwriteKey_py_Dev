# R9 申し送り

- `DEFAULT_RUN_TO_END_DELAY_MS` と `coerce_nonnegative_int` を `domain/config.py` に追加し、run_to_end delay の既定値と非負 int 矯正を一元化した。
- `ConfigService._coerce_nonnegative_int` は既存メソッド名を残し、domain helper へ委譲する形にした。
- `App.update_run_to_end_delay` の `old_v` は計画書どおり、既存の `or default` 挙動を維持している。
- `git grep -n "300" -- keyseq` の残りは定数定義と既存コメントのみ。
