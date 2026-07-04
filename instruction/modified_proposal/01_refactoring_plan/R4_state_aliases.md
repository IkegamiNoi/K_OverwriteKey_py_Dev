# R4 申し送り

- `App` の未使用 state 互換プロパティ 11 個を削除した。
- 使用中の `_selected_trigger_idx` と `_indices` は残している。
- 削除対象は `git grep` で定義以外の参照がないことを確認済み。
