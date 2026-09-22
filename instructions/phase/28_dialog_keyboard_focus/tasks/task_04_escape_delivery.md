# task_04_escape_delivery

## 目的

Escape 依存テストの flaky（[idea_18](../../../backlog/idea_18_escape_delivery_flaky_test.md)）を解消する
（暫定仕様 22 §6）。**テストのみの問題**で、production コードは変更しない。

- **tests_ui 限定**。`keyseq/` 配下に差分を出さない。
- idea_18 の案 B（配送後に待つだけ）では直らないことは実測済み。**「フォーカスを確保できたことを
  確認してから送る」**が正しい対処（下記 §診断結果）。

## 診断結果（2026-09-22・メインが probe で実測。§6 の「先に診断を置く」に相当）

`tests_ui` は**テストクラスごとに `App`（`tk.Tk`）を作る**ため、同一プロセス内に**複数の Tk
アプリケーション**が存在する。制御下で再現した結果:

| # | 条件 | 結果 |
|---|---|---|
| 1 | 他に Tk アプリなし・`focus_force()` あり | 閉じる |
| 2 | **別の Tk アプリが OS フォーカス保持**・`focus_force()` あり | 閉じる（1 回で奪い返せた） |
| **3** | **別アプリ保持・`focus_force()` なし** | **`focus_get()` が `None`・Escape 未配送・ダイアログ生存** |
| 4 | 別アプリ保持・**確保を確認してから送信** | 1 回で確保 → 閉じる |

**確定した機序**: Tk はキーイベントを**フォーカス窓へ再配送**するため、
**そのダイアログを持つ Tk アプリが入力フォーカスを持っていないと Escape は破棄される**。
既存テストは `focus_force()` を呼んでいるが、**効いたかを確認せずに送っている**ため、
奪い返しが間に合わない回に落ちる（= 失敗は「配送が遅い」ではなく「配送先が違う」）。
**待つだけでは直らない**（届かなかったイベントは後から来ない）。

## 対象範囲（tests_ui 限定）

### 1. 新規 `tests_ui/escape_delivery.py`（共通ヘルパ）

関数 1 つ。例:

```python
def send_escape(test_case, app, dialog, *, attempts=20, timeout=2.0):
    ...
```

手順は次の順で、**各段階で失敗したら診断情報を添えて `test_case.fail(...)` する**（黙って通さない）:

1. **フォーカスの確保**: `dialog.focus_force()` → `app.update()` を上限 `attempts` 回まで繰り返し、
   **`app.focus_get()` がダイアログ配下になったことを確認**してから次へ進む。
   確保できなければ fail（診断 = `app.focus_get()` / `app.focus_displayof()` / 試行回数）。
2. **送信**: `dialog.event_generate("<Escape>")` → `app.update()`。
3. **破棄待ち**: `dialog.winfo_exists()` が False になるまで、`app.update()` を回しつつ
   **上限 `timeout` 秒**までポーリングする。上限到達なら fail
   （診断 = 経過秒 / `app.focus_get()` / `dialog.winfo_exists()`）。

- **`skipTest` はしない**（ここは「閉じること」を検証する場なので、skip で緑にしない）。
- ヘルパ自身が `unittest` の TestCase に依存しないよう、失敗の通知は引数で受けた
  `test_case.fail(...)` を使う。

### 2. 対象 4 テストの移行（既存の `focus_force` + `event_generate` を置き換える）

| ファイル:行 | テスト |
|---|---|
| `tests_ui/test_dialog_teardown_flows.py:144` | `test_t2_escape_resumes_quarantine_once` |
| `tests_ui/test_orphan_sweep_flow.py:532` | `test_escape_and_window_close_keep_result_false`（`close="escape"` の分岐） |
| `tests_ui/test_quarantine_manage_flow.py:311` | `test_escape_and_window_close_keep_action_empty`（`close="escape"` の分岐） |
| `tests_ui/test_keymap_set_history_flow.py:304` 付近 | close 経路（`test_close_routes_restore_hook_and_parent_grab`） |

- **検証内容は変えない**（フック解除がちょうど 1 回・結果値・grab 復元などの既存アサートはそのまま）。
  置き換えるのは**閉じ方の送信手順だけ**。
- 各テストの `dialog.focus_force()` / `event_generate("<Escape>")` の直書きを**ヘルパ呼び出しへ寄せる**。
- **`setUp` のドレイン検査（`get_hook_pause_count() == 0`）は変更しない**
  （phase 15 task_03 の検出力を保つ。idea_18 の案 C は採らない）。

### 3. 案 A（結線済みハンドラの直呼び）の併用 — **しない**（§2.1-6 の判断をここで確定）

- 理由: 診断で機序が確定し、**再試行つきヘルパで実配送のまま安定させられる**ため、
  配送の検証を捨てる必要がない（案 A は「Escape が実際に届くか」を検証できなくなる）。
- **結線の有無の固定は task_03 で別途入っている**ため、二重に持つ必要もない。
- この判断と理由を**完了報告に明記する**。

### 設計メモ / 制約

- **production は変更しない**（idea_18 はテストのみの問題）。
- 実使用では App がアクティブな状態で Escape を押すため、**テストで `focus_force` を使うこと自体は
  実使用の再現**であり問題ない。**隠してはいけないのは「ダイアログがフォーカスを取らない」欠落**で、
  それは task_02 の `tests_ui/test_dialog_initial_focus.py` が**生成直後**に検査している
  （そちらは `focus_force` をダイアログへ使わない）。役割が違う。
- `time.sleep` を使う場合も `app.update()` を回し続けること（UI スレッドを止めない）。

## 読むファイル

- `instructions/history/22_dialog_keyboard_focus.md` の **§6 / §1.2 / §8-6 / §8-7**
- `instructions/backlog/idea_18_escape_delivery_flaky_test.md`（経緯と過去の実測）
- `tests_ui/test_dialog_teardown_flows.py:140-165`
- `tests_ui/test_orphan_sweep_flow.py:528-548`
- `tests_ui/test_quarantine_manage_flow.py:308-328`
- `tests_ui/test_keymap_set_history_flow.py:295-315`
- `keyseq/presentation/controllers/hook_controller.py:41-75`
  （フック停止・`after(0)` での再開。**読むだけ**）

## 含まない

- **production（`keyseq/`）の変更**。
- `setUp` のドレイン検査の変更（案 C）。
- 案 A（ハンドラ直呼び）への置き換え（上記 3 の判断）。
- task_02 の `tests_ui/test_dialog_initial_focus.py` の変更
  （**ただし task_04 完了後も一括が不安定なら、`_require_app_focus` の `app.focus_force()` が
  後続クラスへ影響していないかを再検討する**。判断は task_05）。
- 正本 `instructions/common/` の更新（task_06）。
- 実機目視（task_05）。

## 確認

`.venv` の python を使う（`..\..\..\.venv\Scripts\python.exe`）。

1. `python -m compileall -q keyseq` が clean。
2. `python -m unittest discover -s tests` が全 pass（556 から不変）。
3. **`python -m unittest discover -s tests_ui` を連続 3 回**実行し、**3 回とも全 pass**
   （502 前後・skipped 0）。**これが idea_18 解消の主たる証拠**
   （直前の実測では 3 回中 1 回しか緑にならなかった）。
4. 移行した 4 テストを**単独で 5 回ずつ**実行して全 pass。
5. `git diff --stat keyseq/` が**空**であること。
6. `python -m tests.smoke_app` が `SMOKE OK`。

## 完了条件

- 上記確認 1〜6 が pass（実測は `verifier`。**Codex に python 実行を依頼しない**）。
  **3 で 1 回でも落ちたら完了にしない**（原因を切り分けてから再判定する）。
- **`reviewer` 採用**（重点観点 = 検証内容を弱めていないか / skip で緑にしていないか /
  ドレイン検査を触っていないか / production 無変更か）。
- **案 A を併用しない判断とその理由**を完了報告に明記する（§2.1-6）。
- **実機目視は本タスクでは行わない**（task_05 でまとめて実施）。
