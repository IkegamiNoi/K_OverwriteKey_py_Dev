# task_03b_review_followups

## 目的

task_03 の二次レビュー（`deep-reviewer`）の採用分を反映する（ユーザー判断 2026-09-19）。

- **指摘 1（中）**: ドラッグの 4 キーが **JSON の互換処理を通っても残る**ことを見るテストが無い（UI テストは `initial` を直接渡しており永続化経路を通らない）。
- **指摘 2（中）**: 種別を hotkey / text へ戻して `mouse_click` へ戻す**復帰**のテストが無く、
  `action_dialog.py:368` の `_sync_drag_ui()` 結線を消しても既存テストが落ちない。
- **指摘 4（低）**: `drag_speed` が **NaN** のときクランプが素通りし、`duration_sec = nan` が `moveTo` へ渡る（`.venv` で実測確認）。

**application 1 行 + tests / tests_ui のみ**。UI と infrastructure の挙動は変えない。

## 対象範囲

### `keyseq/application/action_executor.py`（1 行のみ）

- `_execute_mouse_drag` の `if speed <= 0:` を **`if not (speed > 0):`** に変える（NaN も既定 1000 へ倒れる）。
  **他の行は変更しない**（メッセージ・分岐・クランプ式はそのまま）。

### `tests/test_action_executor_drag.py`（追記）

- `test_missing_or_invalid_speed_uses_default` のパターンに **`float("nan")` と文字列 `"nan"`** を追加する
  （どちらも既定 1000 として扱われ、`duration_sec` が距離 ÷ 1000 のクランプ結果になること）。
  例: 距離 500・速度 NaN → `duration_sec = 0.5`。

### `tests/test_domain_config.py`（追記）

- `ensure_config_compatibility`（既存の素通しテストが手本）に、**ドラッグの 4 キー
  （`drag` / `to_x` / `to_y` / `drag_speed`）を持つ `mouse_click` アクション**を含む config を通し、
  **4 キーが値もろとも残る**ことを検証するテストを 1 本追加する。**既存テストは変更しない**。

### `tests_ui/test_action_dialog_drag.py`（追記）

- **種別の往復**テストを 1 本追加する（既存テストは変更しない）:
  1. 種別 `mouse_click` + ドラッグ ON にする
  2. 種別を `text` にして `_sync_capture_ui()` を通す
  3. 種別を `mouse_click` へ戻して `_sync_capture_ui()` を通す
  4. **回数欄が `disabled` のまま**・**X / Y ラベルが「掴む位置 X」「掴む位置 Y」のまま**・
     離す位置と速度の欄が表示されたままであることを確認する
  - **`_sync_drag_ui()` を直接呼ばない**（結線を通す経路を検証するテストのため。これが指摘 2 の要点）。

### 設計メモ / 制約

- **挙動を変えるのは NaN の 1 行だけ**。それ以外の production コードは触らない。
- 既存テストの期待値は変えない。落ちたら**期待値を弱めず**報告する。
- **python を実行しない**（この環境では起動できない）。テストの実行は `verifier` が行う。
- **`git checkout --` / `git restore` / `git stash` を使わない**。

## 読むファイル

1. `keyseq/application/action_executor.py:145-155`（編集対象の 1 行）
2. `tests/test_action_executor_drag.py`（全体・追記対象）
3. `tests/test_domain_config.py` の `ensure_config_compatibility` 系テスト（手本 + 追記対象）
4. `tests_ui/test_action_dialog_drag.py`（全体・追記対象）
5. `keyseq/presentation/dialogs/action_dialog.py:360-372`（`_sync_capture_ui` の結線。読むだけ）

## 含まない

- 記録のみ / 保留にした指摘（`click_mouse` 側の FAILSAFE 検出力 / 速度欄の `int()` 判定 /
  `instate` ガード / リスナーの TclError）= **task_03** の記録へ。
- 正本昇格・実機目視・フェーズ完了処理 = **task_03**。

## 確認

実行は `verifier`。python は `..\..\..\.venv\Scripts\python.exe`。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests.test_action_executor_drag -v` / `-m unittest tests.test_domain_config -v` が全 pass。
3. `-m unittest tests_ui.test_action_dialog_drag -v` が全 pass。
4. `-m unittest discover -s tests` が全 pass（**478 から増えていること**）/ `-m unittest discover -s tests_ui` が全 pass（**445 から増えていること**）。
5. `-m tests.smoke_app` が SMOKE OK。
6. **変異検査**（ファイルのコピーで退避 → 編集 → コピーで復元）:
   - `action_dialog.py:368` の `self._sync_drag_ui()` の呼び出しを削除すると、**追加した往復テストが失敗する**。
   - `action_executor.py` の `if not (speed > 0):` を `if speed <= 0:` へ戻すと、**追加した NaN のケースが失敗する**。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は **task_03** でまとめて実施する。
