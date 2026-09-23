# task_02_remaining_files_and_load_run

## 目的

task_01 のヘルパ `tests_ui/hook_resume_wait.py` の `wait_for_hook_pause_count` を、`get_hook_pause_count()` を使う残り 3 ファイルへ適用し
（phase.md「確定」= 破棄後の解除を確かめる箇所すべて）、**負荷下で tests_ui を反復実行して本 family の赤が出ないこと**を確かめる。

**tests_ui 限定・production 不変・ヘルパ本体（`hook_resume_wait.py`）不変・正本改訂なし**。置き換えの形と禁止事項は task_01 と同じ
（`task_01_wait_helper_and_observed_files.md`「観測済み 5 ファイルへの適用」「設計メモ / 制約」）。

## 対象範囲（tests_ui 限定）

行番号は HEAD `9eff5ee` 時点。

### `tests_ui/test_app_ui_flows.py`

- 置換: `:1331-1332`（テスト冒頭の `update()` + `== 0`）/ `:1953-1954`（同）/ `:1960-1962`（`destroy()` 後の `update()` → `== 0`。
  `:1960` は `with` の内側・`:1962` は外側。`:1960` をヘルパ（0）へ置き換え、`:1962` は削ってよい）。

### `tests_ui/test_hook_controller_teardown.py`

このファイルは `self.app` が素の `tk.Tk()` で `hook` 属性を持たない（コントローラは `self.hook`）。
**テストクラスに小さなメソッドを 1 つ足して**ヘルパへ渡す（`setUp` は変えない）:

```python
def wait_pause_count(self, expected):
    wait_for_hook_pause_count(
        self, SimpleNamespace(update=self.app.update, hook=self.hook), expected,
    )
```

- 置換: `:56-57`（`update()` をヘルパ（0）へ・`with` の内側に置く。`:57` は削ってよい。`:58-59` はヘルパの後）/
  `:91-92` / `:106`（`update()` をヘルパ（**1**）へ。`:105` の `== 2` と `:107-111` はそのまま）/ `:113-114` /
  `:123-124`（`with` の内側。`:125` はヘルパの後）。

### `tests_ui/test_startup_font_characterization.py`

- **変更なし**。停止と解除が `messagebox` の前後で**同期**に行われ `after(0)` を経由しない（`:109-136`）。置き換える箇所は無い。

### 設計メモ / 制約（置き換えない確認）

- `test_hook_controller_teardown.py:52-55`（破棄直後・`update_idletasks()` 後も**未解除**＝`after(0)` 遅延の設計そのもの）/
  `:70-71`（`window` 省略時は破棄で解除されない）/ `:87-89`（子の破棄で予約しない）/ `:108-111`（二重の予約・過剰な解除をしない）/
  `:72-77` / `:127-131`（`resume_hook_after_dialog()` の同期呼び出し）。
- `test_app_ui_flows.py:248-254`（同期の入れ子カウンタ）/ `:2293-2296`（キャプチャの同期停止・解除）/
  `:1348-1349`（カウントを確かめていない）。
- `:248` / `:2293` の `update()` を伴わないテスト冒頭の確認は残す（task_01 と同じ扱い。本 family の観測は無い）。
- 迷ったら置き換えず、完了報告に「判断保留」として挙げる。

### 負荷下の反復実行（verifier）

- 負荷 = `.venv` の python で `while True: pass` を **4 プロセス**起動し、測定後に必ず終了させる。
- 測定 A: 対象 8 モジュール + `tests_ui.test_hook_resume_wait` を **1 回の `unittest` 呼び出しでまとめて**実行 × **6 回**。
- 測定 B: `-m unittest discover -s tests_ui` × **1 回**。
- 各回の fail / error をテスト名 + メッセージ要旨で記録する。**本 family の赤 = `get_hook_pause_count()` の不一致 /
  `resume_hook_after_dialog` の呼び出し回数不一致 / ヘルパの期限切れ（`hook pause count: expected=...`）**。

## 読むファイル

1. `tests_ui/hook_resume_wait.py`（全体・21 行）
2. `tests_ui/test_hook_controller_teardown.py`（全体・約 135 行）
3. `tests_ui/test_app_ui_flows.py:1-30`（import 節）/ `:1325-1352` / `:1945-1963`
4. 本タスク定義の「設計メモ / 制約」

## 含まない

- ヘルパ本体・task_01 で変更した 5 ファイル・`escape_delivery.py`・production・`setUp` / `tearDownClass` の変更。
- 原因の A/B 測定（phase.md「確定」で不要と判断済み）。
- `codebase_map.md`・decisions_archive・idea_33 のクローズ・`/refactor_check`（task_03）。
- テストの実行を Codex へ依頼すること（実測は verifier）。

## 確認

verifier（`.venv` の python。worktree 相対 `..\..\..\.venv\Scripts\python.exe`）:

1. `-m compileall -q keyseq tests tests_ui` が clean。
2. `tests_ui.test_app_ui_flows` / `tests_ui.test_hook_controller_teardown` / `tests_ui.test_startup_font_characterization` を個別に実行して全 pass。
3. 負荷なしの標準検証: `-m unittest discover -s tests`（577）/ `-m unittest discover -s tests_ui`（535）/ `-m tests.smoke_app`（SMOKE OK）がすべて pass。
4. 負荷下の測定 A（6 回）・測定 B（1 回）で**本 family の赤が 0 件**。本 family 以外の fail が出たら内容を記録して報告する（完了可否はユーザー判断）。
5. `git diff --stat` に `keyseq/`・`tests_ui/hook_resume_wait.py`・`tests_ui/escape_delivery.py`・`tests_ui/test_startup_font_characterization.py` が含まれない。

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点 = phase.md「レビュー方針」+ `test_hook_controller_teardown.py` の置き換えない確認〔`:52-55` / `:70-71` / `:87-89` / `:108-111`〕が無変更か）。
- 実機目視は不要（テストのみ）。
