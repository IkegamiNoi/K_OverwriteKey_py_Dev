# task_05d_send_escape_deadline

## 目的

`send_escape` のフォーカス確保ループを**実時間の期限（deadline）方式**へ変える
（暫定仕様 22 **v0.6 §6.1**・ユーザー確定 2026-09-23。`deep-reviewer` 指摘 M2）。

- **tests_ui 限定。production（`keyseq/`）を変更しない**。
- 検証内容は変えない（**閉じることを実配送で確かめる**という性質を保つ）。

## 背景（裏取り済み）

現行 [`tests_ui/escape_delivery.py:13-23`](../../../../tests_ui/escape_delivery.py) は

```python
for attempt in range(1, attempts + 1):   # attempts=20
    dialog.focus_force()
    app.update()
    focused = app.focus_get()
    if ...: break
else:
    raise TimeoutError("dialog did not acquire focus")
```

で、**試行間に実時間の待ちが無い**。

- `focus_force()` は OS / WM への**要求**にすぎず、フォーカス移動の通知が返るまでに時間がかかる。
- `app.update()` は**今キューにあるイベントを処理して即戻る**（新しい通知の到着を待たない）。

→ 20 回のループが **CPU 速度で数ミリ秒未満に消化されうる**。
`attempts=20` は「20 回粘る」ではなく実質「**一瞬だけ試す**」になっている。
現状 fail していないのはこの環境の応答が速く 1〜2 周目で取れているからで、
**負荷条件やマシンが変われば成立しない**。

## 対象範囲（`tests_ui/escape_delivery.py` のみ）

`send_escape(test_case, app, dialog, *, attempts=20, timeout=2.0)` の
**フォーカス確保段階**を deadline 方式へ変更する。

### 変更内容

1. **確保段階に実時間の期限を設ける**。既存の `timeout` は破棄待ち専用なので、
   **確保用の期限を別に持つ**（引数名は `focus_timeout` 等。既定 **2.0 秒**を目安）。
2. ループは「期限に達するまで」回す。各周で
   `dialog.focus_force()` → `app.update()` → `app.focus_get()` の確認を行い、
   **確認が失敗したら短い実時間待ち（10ms 程度）を入れてから次の周へ進む**。
3. **待ちの間も `app.update()` を回し続ける**（`time.sleep` だけで止めない。
   UI スレッドを止めるとフォーカス通知の処理自体が進まない）。
4. **応答が速い回は 1 周目で抜ける**こと（待ちに入る前に成功するため実行時間が変わらない）。
5. 失敗時の診断に **経過秒と試行回数の両方**を残す（現行の `attempts=N/M` に加えて
   `focus_elapsed` 相当を出す）。失敗メッセージが「期限まで粘っても取れなかった」と読めるようにする。

### `attempts` 引数の扱い

- **削除してよい**（期限で切るため回数の上限は不要）。ただし**呼び出し側で明示指定している箇所が
  あれば追従する**（`grep -rn "send_escape(" tests_ui/` で確認する）。
- 後方互換のための引数残置はしない（`.claude/rules/file_organization_rules.md`
  「恒久的な互換レイヤーは禁止」）。

### 設計メモ / 制約

- **`skipTest` は使わない**（確保できなければ診断付きで `test_case.fail`）。現行の方針を維持する。
- **破棄待ち段階（既存の `timeout`）のロジックは変えない**。
- 例外の捕捉は現行どおり `(tk.TclError, KeyError, TimeoutError)` に限定する（握りつぶさない）。
- ヘルパは `unittest` の TestCase に依存させない（失敗通知は引数の `test_case.fail`）。
- 関数は 30 行以内を目安にする。超えるなら確保段階を小さな内部関数へ切り出す。

## 読むファイル

- `instructions/history/22_dialog_keyboard_focus.md` の **§6 / §6.1**
- `tests_ui/escape_delivery.py`（全体。**唯一の編集対象**）
- `grep -rn "send_escape(" tests_ui/` の結果（呼び出し側の引数指定の有無を確認するため）

## 含まない

- **production（`keyseq/`）の変更**。
- 破棄待ち段階の仕様変更。
- **`after(0)` のフック再開 family の対策**（= [idea_33](../../../backlog/idea_33_hook_resume_after_idle_flaky_test.md)。
  本フェーズでは直さない。ユーザー判断 2026-09-23）。
- 呼び出し側テストの検証内容の変更（引数の追従以外は触らない）。
- 正本 `instructions/common/` の更新（task_06）。
- 実機目視（task_05 でまとめて 1 回）。

## 確認

`.venv` の python を使う（`..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

1. `python -m compileall -q keyseq` が clean。
2. `python -m unittest discover -s tests` 全 pass（556・skipped 7 から不変）。
3. `python -m unittest discover -s tests_ui` 全 pass（**507 から不変**）。
4. **実行時間が伸びていないこと**: `send_escape` を使うテストのうち 2 件を単独で 5 回ずつ実行し、
   **所要時間が変更前と同等**であること（応答が速い回は 1 周目で抜ける設計の確認）。
   変更前の値は `git stash` せずに `git show HEAD:tests_ui/escape_delivery.py` を
   一時ファイルへ出して比較するのではなく、**変更後の絶対値が 1 テストあたり数秒以内**であれば可とする。
5. **負荷下（busy loop 4 本）で `python -m unittest tests_ui.test_dialog_escape_binding` を 6 回**
   実行し **fail 0**（§8-7 の Escape family 判定）。
6. `git diff --stat keyseq/` が**空**。
7. `python -m tests.smoke_app` が `SMOKE OK`。

## 完了条件

- 確認 1〜7 が pass（実測は `verifier`。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（重点観点 = 検証内容を弱めていないか / `skipTest` を入れていないか /
  例外を握りつぶしていないか / production 無変更か / 互換のための引数残置をしていないか）。
- **実機目視は本タスクでは行わない**（task_05 でまとめて実施）。
