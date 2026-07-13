# R5 申し送り

- 到達不能だった chain 実行系を `SequenceRunner` / `AppState` / `App` から削除した。
- `git grep -in "chain" -- keyseq` は 0 件になった。
- `run_to_end` の実行・停止ロジックには触れていない。
