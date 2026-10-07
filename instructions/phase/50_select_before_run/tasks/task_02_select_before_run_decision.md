# task_02_select_before_run_decision

## 目的

暫定 34 §3・§4・§7・§8 の判定を application に実装する: 選ぶだけの押下・戻す・先頭へだけの除外・長押し（リピート）の無視・単発の待機明けの選び直しの変更。
**application 限定（presentation の配線は task_03）。注入口は省略可能で、省略時は機能 OFF・従来と完全に同じ。**

## 対象範囲（application 限定）

### `keyseq/application/input_router.py`

- `TriggerAction` に `repeat: bool = False` を足す。`handle()` で、その down を `KeyStateManager` に渡す**前**にそのキーが既に押下中だったら `repeat=True`（:81 の `handle_event` の前に押下状態を見る）。他のアクション・suppress の決定は変えない

### `keyseq/application/action_executor.py`

- `TriggerAction` を runner へ渡すとき `repeat` も渡す（`on_trigger` の呼び出し :199-200 付近）。`on_trigger` のコールバックの形を `(key, repeat)` 等へ広げ、既存の呼び出し側・テストが壊れないようにする（既定値で互換）

### `keyseq/application/sequence_runner/sequence_runner.py`（注入口・押下の入口）

- コンストラクタに省略可能な 2 つを足す（既定 None）:
  - `get_selected_trigger_key: Callable[[], str | None]` — 一覧で選ばれている行が**有効な行**ならそのキー（正規化後）、そうでなければ None
  - `is_select_before_run_enabled: Callable[[], bool]` — アクティブな構成セットの全体の設定（runtime の `select_before_run`）
  - どちらかが None なら選んでから実行の判定は行わない（機能 OFF）
- `handle_key(key, repeat=False)`: 選ぶだけにしたキー（`self._select_only_key`）と同じキーの `repeat=True` の押下は**何もせず return**（控えの破棄もしない）。それ以外の押下では `_select_only_key` を None に戻してから従来の処理へ（§2-9・暫定 34 §3「リピートの無視」）

### `keyseq/application/sequence_runner/input_acceptance.py`（判定）

- `_accept_key` の「アクションが空なら return」（:185-187）の**直後**、連続実行の分岐（:188-）の**前**に判定を入れる:
  - 対象 = 注入あり かつ（全体の設定 ON または トリガーの `select_before_run` が真）かつ **`_is_standalone_control(actions)` でない**（§2-7）
  - 対象で、`get_selected_trigger_key()` が K でない → **選ぶだけ**: `self._select_trigger(K)` / `notify_message` に「{K} を選びました（もう一度押すと実行します）」（K は正規化後）/ `self._select_only_key = K` / return。
    実行状態（位置・周回・保留・戻す履歴・直前のトリガー・一時停止中のもの・他の待機の保留）を一切変えない
- 判定は 1 か所の小さなメソッドにまとめる（例 `_select_only_if_needed(key, trigger) -> bool`）

### `keyseq/application/sequence_runner/send_wait.py`（待機明け・§2-8）

- :66 の `self._select_trigger(key)` を、注入あり（`get_selected_trigger_key` が None でない）のときは **今選ばれている有効な行のキーが key のときだけ**呼ぶ（待機の間に選択が変わっていたら選び直さない。runner は待機を積んだ実行の後に key を選んでいるので、「待機の始まりの選択 = key」と同値）。注入なしなら従来どおり常に呼ぶ
- 他の `_select_trigger` の呼び出し（実行後・連続実行・呼び出し・file_line）は変えない

### テスト（tests/）

- 新規 `tests/test_sequence_runner_select_before_run.py`（既存の `tests/test_sequence_runner.py` の runner の作り方を手本）:
  ①注入なし・全体 OFF / トリガー OFF なら従来どおり即実行 ②全体 ON で選ばれていないキー → 選ぶだけ（select が呼ばれ・メッセージ・位置 / 周回 / 履歴 / 直前のトリガー不変）→ 選ばれた状態で押すと実行
  ③全体 OFF・トリガーの `select_before_run` だけ ON ④戻す・先頭へだけのトリガーは全体 ON でも即実行 ⑤処理中の一時停止 / 一時停止中の連続実行の再開 / 押したトリガー自身の待機中の無視は従来どおり（選ぶだけにならない）
  ⑥連続実行のトリガーの 1 回目（選ぶだけ）で一時停止中のものを捨てない・他のトリガーの単発の待機の保留を取り消さない ⑦グレーの重複行（get_selected_trigger_key が None）なら選ぶだけ
  ⑧リピート: 選ぶだけにした K の repeat=True は無視・repeat=False の次の押下で実行・他キーの押下で無視が終わる・選ばれている K の repeat=True は従来どおり実行に使われる
  ⑨待機明け: 待機中に選択が K 以外になっていたら選び直さない・K のままなら選び直す・注入なしなら従来どおり
- `tests/test_input_router.py`: 押下中のキーの 2 回目の down は `repeat=True`・up の後の down は `repeat=False`・suppress / 他のアクションは不変
- 既存テストは注入なしのため挙動不変のはず。落ちたら原因を報告（期待値を勝手に変えない）

## 読むファイル

- `instructions/history/34_select_before_run.md` の §2・§3・§4・§7・§8
- `keyseq/application/input_router.py`・`keyseq/application/key_state_manager.py`（全体）・`action_executor.py:20-80, 180-205`
- `keyseq/application/sequence_runner/sequence_runner.py:30-80, 295-310`・`input_acceptance.py:120-207`・`send_wait.py:20-70`
- テストの手本: `tests/test_sequence_runner.py`（runner の作り方・待機）・`tests/test_input_router.py`

## 含まない

- presentation の配線（注入・UI・チェックボックス・dirty）は task_03
- 正本の改訂（task_05）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- 追加したテストを含めて tests 全体・tests_ui 全体・`-m tests.smoke_app` pass（注入なしなので tests_ui は不変のはず）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視: task_03 でまとめて
