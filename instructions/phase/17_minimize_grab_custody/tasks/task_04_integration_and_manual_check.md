# task_04_integration_and_manual_check

## 目的

phase 17 の全差分（起票 + task_01 / 02 / 02b / 03）について**統合確認**と**二次レビュー**を行い、
**ユーザーによる実機目視**で暫定仕様 15 §6-1 / §6-2 の受け入れ条件（自動テストで再現できない部分）を
確認する。判定と根拠は `instructions/phase/17_minimize_grab_custody/integration_result.md` へ記録する
（**本タスクの判定の正はこのファイル**）。

**production の変更は行わない**（是正が必要と判明した場合は枝番タスクを起票して分ける）。

## 対象範囲

### 1. 統合確認（`verifier` へ委任）

- `compileall -q keyseq main.py tests tests_ui`
- `unittest discover -s tests` / `unittest discover -s tests_ui`
- `tests.smoke_app`
- 新規・変更モジュールの単独実行（`test_minimize_grab_custody` / `test_modal_grab` /
  `test_nested_modal_grab` / `test_dialog_teardown_flows` / `test_dialog_transient_parent` /
  `test_app_ui_flows`）
- **一括実行を 2 回以上**行い、[idea_18](../../backlog/idea_18_escape_delivery_flaky_test.md) 由来の
  flaky（`test_dialog_teardown_flows` の Escape 取りこぼし）と**本フェーズ由来の失敗を切り分ける**
- テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されていないこと

### 2. 二次レビュー（`agent_selection.md` の「統合テスト・複数タスクを跨ぐ動作確認時」）

- **`deep-reviewer`**（フェーズ横断・opus）— 観点は `.claude/rules/review.md` の 5 観点 +
  **ガードの欠落 / phase 14・16 の資産への影響 / 復元時に窓を触っていないか / スコープ逸脱**
  （phase.md「レビュー方針」）。**暫定仕様 15 v0.5 の §3-2(8) が §3-2(1)〜(7) と矛盾しないか**も見る。
- **`codex-reviewer`**（標準レビュー）— 別モデルの視点。
- **指摘は提示のみ**。採否はユーザー判断（`agent_selection.md`）。

### 3. ユーザーによる実機目視（**メインセッションは実施できない**）

以下 5 項目を提示し、結果を受け取って `integration_result.md` へ記録する。

| # | 手順 | 期待 |
|---|---|---|
| M1 | ダイアログ（例: アクション編集）を開いたまま **Win+D** → タスクバー / Win+D で戻す | **アプリが復元できる** |
| M2 | M1 の復元後 | **モーダル性が残る**（背面の操作ができない） |
| M3 | M1 の復元後 | **中間のダイアログも含めて全窓が表示されている**（消えていない） |
| M4 | **3 段ネスト**（アクション編集 → プリセット編集 → 上書き確認）で最小化 → 復元 | M1〜M3 と同じ。**閉じたときの LIFO 復元も従来どおり** |
| M5 | **通常の最小化ボタン**（タイトルバー）でも同じ手順 | M1〜M3 と同じ |

- **stdlib ダイアログ（`messagebox` / `filedialog`）が開いている状態は対象外**（症状が残るのは既知・確定済）。
- 目視で問題が出た場合は**枝番タスク（task_04b 等）を起票**して是正する（本タスクで実装しない）。

### 4. 記録

`integration_result.md` を新規作成し、**統合確認の結果表 / 二次レビューの判定と指摘 /
実機目視の結果 / 未解決事項**を記録する（生ログは載せない）。

## 含まない

- **production コードの変更**（是正が必要なら枝番タスクへ分ける）
- 正本反映（`features.md` §4.6 / `codebase_map.md`）・暫定仕様 15 の凍結・
  `decisions_archive` の作成・`/refactor_check` → **task_05**
- [idea_18](../../backlog/idea_18_escape_delivery_flaky_test.md) の是正（切り分けのみ行う）
- stdlib ダイアログ経路への対応（スコープ外・確定済）

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. 統合確認の全項目 pass（flaky が出た場合は**本フェーズ由来でないことの切り分け結果**を記載）
2. `deep-reviewer` / `codex-reviewer` の判定を取得し、**ブロッキング指摘が残っていない**
3. **実機目視 M1〜M5 の結果がユーザーから報告され、記録されている**
4. `integration_result.md` が作成されている

## 完了条件

- 上記確認をすべて満たす。**実機目視で問題が出た場合は、是正タスクの起票までを本タスクに含める**
  （是正の実装は別タスク）。
- 本タスクの別視点レビューは **`deep-reviewer` + `codex-reviewer` の二次レビューをもって充当する**
  （`reviewer` は重ねない = `agent_selection.md`「どちらか一方」）。
