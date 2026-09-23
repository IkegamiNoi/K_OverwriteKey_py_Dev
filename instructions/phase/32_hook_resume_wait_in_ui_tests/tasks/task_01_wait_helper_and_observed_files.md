# task_01_wait_helper_and_observed_files

## 目的

ダイアログ破棄後のフック再開は `after(0)` で予約される（`keyseq/presentation/controllers/hook_controller.py:57`）。
tests_ui の「`app.update()` 1 回 → カウント / 再開呼び出しの確認」を、**実時間の期限まで待つヘルパ**へ置き換える
（phase.md「確定」案 A）。本タスクはヘルパ・ヘルパ自身のテスト・**flaky 観測済みの 5 ファイル**への適用まで。

**tests_ui 限定・production 不変・`escape_delivery.py` 不変・正本改訂なし**。
正本 `key_input.md` §7.2「停止要求は閉じ方によらずちょうど 1 回解除」の検証は弱めない
（`resume.assert_called_once_with()` はそのまま残す）。

## 対象範囲（tests_ui 限定）

### `tests_ui/hook_resume_wait.py`（新規）

```python
def wait_for_hook_pause_count(test_case, app, expected, *, timeout=2.0):
    """期限まで Tk のイベントを処理し、フック停止カウントが expected になるのを待つ。"""
```

- **最初に必ず `app.update()` を 1 回呼んでから**判定する（置き換え前の「update 1 回 → 確認」より弱くしないため）。
- 以降、`app.hook.get_hook_pause_count() == expected` になるまで `app.update()` を回す。
  **期限は `time.monotonic()` の実時間**で切る（回数上限にしない）。busy wait を避けるため 1 周ごとに `time.sleep(0.001)` 程度を挟む
  （手本 = `tests_ui/escape_delivery.py` の `acquire_focus`）。
- 期限切れは `test_case.fail(...)` で、**期待値・現在値・経過秒・timeout** をメッセージに含める。
- 読むのは `app.update` と `app.hook.get_hook_pause_count` だけ（ほかの属性に依存しない。テストで軽い代役を渡せるようにする）。

### `tests_ui/test_hook_resume_wait.py`（新規・ヘルパ自身の決定的テスト）

実 `App` は作らない。`tk.Tk()` を 1 つ作り（`withdraw`）、`types.SimpleNamespace(update=root.update, hook=<カウントを返す代役>)` をヘルパへ渡す。

1. カウントを `root.after(50, ...)` で 1 → 0 にする → ヘルパが pass し、戻った時点でカウントが 0。
2. カウントが変わらない（1 のまま）・`timeout=0.1` → `self.failureException` が出て、メッセージに期待値 `0` と現在値 `1` が入る。
3. 最初から期待値 → pass し、`update` が**少なくとも 1 回**呼ばれている（呼び出し回数を数える代役で確認）。

### 観測済み 5 ファイルへの適用

**置き換えの形**: 「`self.app.update()` → カウントが X であることの確認」の組を
`wait_for_hook_pause_count(self, self.app, X)` へ置き換える。直後の `resume.assert_called_once_with()` ・
結果の確認（`result` / `action` / grab 等）は**そのまま残し、ヘルパより後に置く**。
ヘルパと同じ内容になった `assertEqual(get_hook_pause_count(), X)` は削ってよい。
send_escape の直後など `update()` を挟まずに `resume.assert_called_once_with()` している箇所は、その前にヘルパを 1 行入れる。

行番号は HEAD `a1f1323` 時点。

- `tests_ui/test_dialog_teardown_flows.py`
  - 置換: `:91-92`（subTest 冒頭）/ `:101-102` / `:115-116`（subTest 冒頭）/ `:141-144` / `:158-161`（`send_escape` 後・ヘルパを挿入）
  - `:186-189`（t4a）: `update()` をヘルパ（0）へ置き換え、**`:187-188` の「再開しない」確認はヘルパより後**に置く
    （再開処理が実際に走った後でないと否定確認が素通りする）。
- `tests_ui/test_orphan_sweep_flow.py` — 置換: `:522-523` / `:530-531`
- `tests_ui/test_quarantine_manage_flow.py` — 置換: `:301-302` / `:309-310` / `:325-326`（subTest 末尾）/ `:337-338`
- `tests_ui/test_keymap_set_history_flow.py`
  - `:299` `before = ...` の**直前**にヘルパ（0）を入れる（先行テストの解除予約が残ったまま基準値を取らないため）。
  - `:311-313`: `update()` をヘルパ（`before`）へ置き換え、`:313` は削ってよい。`:312` `assertFalse(winfo_exists())` と `:314` grab はヘルパの後。
  - `:324`（chooser を開いた直後の `== 1`）をヘルパ（1）へ置き換える。
- `tests_ui/test_dialog_escape_binding.py` — 置換: `:87-90` / `:106-109` / `:158-161` / `:202-205` / `:235-238` / `:259-261` / `:282-284`
  （いずれも `send_escape` / `destroy` の後の `update()` → `resume.assert_called_once_with()` → `== 0`）

### 設計メモ / 制約（置き換えてはいけない確認・phase.md「含まない」）

- **破棄直後の「まだ解除されていない」確認**: `test_dialog_teardown_flows.py:98-100`。
- **解除が起きないことの確認**（待っても意味が無い）: `test_dialog_teardown_flows.py:172-174`（t3）/ `:245`（t5。`PresetDialog` は停止しない）/
  `test_dialog_escape_binding.py` の `_assert_escape_stops_without_closing` と `:225-230` / `:277-280`（`resume.assert_not_called()` 側）。
- **同期解除の確認**: `test_dialog_teardown_flows.py` t4b（`:206-225`。「update より前に観測」が要点）。
- **`setUp` のドレイン検査**（`test_dialog_teardown_flows.py:59-60` 等）と `tearDownClass` の `update()`。
- `update()` を伴わない subTest 冒頭の `== 0`（`test_dialog_escape_binding.py:148` / `:190` / `:215` / `:248` / `:264`）は残す
  （直前の subTest 末尾がヘルパで待つようになるため）。
- `resume.assert_called_once_with()` を `assert_called()` 等へ緩めない。期待値（`X`）を変えない。
- 上記以外の箇所で迷ったら**置き換えず**、完了報告に「判断保留」として挙げる。

## 読むファイル

1. `tests_ui/escape_delivery.py`（全体・68 行。実時間期限の手本・変更しない）
2. `keyseq/presentation/controllers/hook_controller.py:40-73`（停止 / 再開 / カウント。読むだけ）
3. 上記 5 ファイルの、列挙した行の前後 ±10 行と各ファイル冒頭の import 節
4. 本タスク定義の「設計メモ / 制約」

## 含まない

- `test_app_ui_flows.py` / `test_hook_controller_teardown.py` / `test_startup_font_characterization.py` への適用・負荷下の反復実行（task_02）。
- `codebase_map.md` への記載・decisions_archive・idea_33 のクローズ（task_03）。
- production コード・`escape_delivery.py` の変更。`setUp` / `tearDownClass` の変更。
- テストの実行（Codex は python を起動できない。実測は verifier）。

## 確認

実行は verifier（`.venv` の python。worktree 相対 `..\..\..\.venv\Scripts\python.exe`）:

1. `python -m compileall -q keyseq tests tests_ui` が clean。
2. `python -m unittest tests_ui.test_hook_resume_wait -v` で 3 件 pass。
3. 対象 5 モジュールを個別に実行してすべて pass
   （`tests_ui.test_dialog_teardown_flows` / `test_orphan_sweep_flow` / `test_quarantine_manage_flow` / `test_keymap_set_history_flow` / `test_dialog_escape_binding`）。
4. `python -m unittest discover -s tests_ui` が全 pass（件数は 532 + 3 = 535 の見込み）。
5. `python -m unittest discover -s tests` が全 pass（577・production 不変の確認）。
6. `git diff --stat` に `keyseq/` と `tests_ui/escape_delivery.py` が**含まれない**。

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点 = phase.md「レビュー方針」: 検証が弱まっていないか / 置き換えてはいけない確認を置き換えていないか /
  実時間の期限 / production 差分なし）。
- 負荷下の反復実行は task_02 でまとめて行う。実機目視は不要（テストのみ）。
