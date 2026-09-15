# 診断スクリプト（暫定仕様 15 §1 の根拠）

`.venv` の python で実行する（worktree から `..\..\..\..\.venv\Scripts\python.exe`）。
**production コードではない**。暫定仕様 15 の現状監査を再実行可能にするために置いている。

| ファイル | 何を見るか | 操作 |
|---|---|---|
| `diag_win_d.py [nested\|flat]` | Win+D 後の 3 段の窓の状態遷移（500ms ごと） | Win+D → タスクバーで復元 → Ctrl+C |
| `diag_win_d2.py [events\|fix]` | 届くイベント（Map/Unmap/Focus 等）と、対策候補（`<Unmap>` で grab 解除）の A/B | 同上 |
| `probe_iconic.py` | `iconify` 中の `viewable` / 保持者破棄 / `withdrawn` への `grab_set` | なし（自動） |
| `probe_orphan.py` | **`transient` を持たない窓・呼び出し元を破棄された子は最小化で隠れない** | なし（自動） |

実測結果（2026-09-16）は暫定仕様 15 §1「現状監査」の表が正。
