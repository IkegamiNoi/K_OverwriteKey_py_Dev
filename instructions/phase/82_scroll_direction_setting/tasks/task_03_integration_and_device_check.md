# task_03_integration_and_device_check

## 目的

task_01・task_02 を合わせた統合確認と、Windows / macOS の実機目視（暫定 62 §7-8）を行う。
**検証のみ・コードは変えない**（失敗が出たら原因を切り分けて別タスク〔枝番〕にする）。

## 対象範囲（検証のみ）

### 統合確認（verifier・macOS）

- `../../../.venv/bin/python -m compileall -q keyseq tests tests_ui`
- `../../../.venv/bin/python -m unittest discover -s tests`
- tests_ui はモジュールごとに別プロセスで流す（`instructions/phase/75_mac_support/mac_test_baseline.md`「tests_ui の流し方（Mac）」・通しで流さない・各 `timeout 600`）。
  失敗・エラー・タイムアウトのあったモジュールは、phase 82 より前のコミット `57610a54` の一時 worktree（scratchpad に `git worktree add --detach`）で同じモジュールを流し、**増えた失敗だけ**を今回の変更の問題として扱う（既存の失敗は件数と ID の一致を確かめて既存扱い）。一時 worktree は最後に `git worktree remove` する。
- `../../../.venv/bin/python -m tests.smoke_app`

### 統合レビュー

- `deep-reviewer`（task_01・task_02 を跨ぐ差分 `57610a54..HEAD` のコード）と `codex-reviewer`（標準レビュー・`--base 57610a54`）。指摘の採否はユーザー。

### 実機目視（ユーザー）

Windows・macOS それぞれで:

1. 設定 > スクロールの向き に「縦を反転」「横を反転」があり、「物理キー名を表示」の後・「フォントサイズ」の前にある（英語表示でも `Scroll direction` / `Invert vertical` / `Invert horizontal`）。
2. 両方 OFF で `mouse_scroll` の下 3・右 3 を実行 → 今までどおりの向き。
3. 縦だけ ON → 上下だけが逆になり、左右は変わらない。横だけ ON → 左右だけが逆。
4. 切り替えて再起動 → チェックと向きが保たれる（config.json に `scroll_invert` の両方の値）。
5. macOS: メニューから切り替えても固まらない。
6. 出力シーケンスの一覧・編集ダイアログの向きの表示は変わらない。
7. ヘルプの「主要機能」の mouse_scroll の説明に反転の 1 文がある。

（保存失敗の確認は tests で担保し、実機では行わない。）

## 読むファイル

- `instructions/history/62_scroll_direction_setting.md` §7
- `instructions/phase/75_mac_support/mac_test_baseline.md`（tests_ui の流し方）

## 含まない

- コードの修正（失敗が出たら枝番タスク task_03a 等を起票）
- 正本反映・凍結・decisions_archive・current.md の完了記載（task_04）

## 確認

- compileall clean / tests 全 pass / smoke pass
- tests_ui: phase 82 の前（`57610a54`）と比べて増えた失敗・エラー・タイムアウトが 0
- 統合レビューの指摘の採否がユーザーで決まっている
- 実機目視 1〜7 の結果がユーザーから報告されている（Windows / macOS）

## 完了条件

- 上記確認を満たし、**reviewer 採用**（統合確認の段では `deep-reviewer` が担う・`agent_selection.md`）。
- 実機目視は本タスクで実施（ユーザー）。
