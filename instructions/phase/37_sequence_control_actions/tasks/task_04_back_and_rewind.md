# task_04_back_and_rewind

## 目的

暫定仕様 26 §8（戻す・先頭へ）を実装する。task_02 で「素通り」にしてある `back` / `rewind` を置き換える。
- §8.1 戻す履歴: ステップ開始時に位置・周回スタックを控え、ステップ中のカウンター操作を**差分**で控える（§2-16）。ステップ終了時に状態が変わっていれば
  履歴へ 1 段積み（上限 100・古いものから捨てる）、**直前のトリガー**をこのトリガーにする。エラーで止まったステップ・待機の取り消しも積む。
- §8.2 戻す: 直前のトリガーの履歴を 1 段降ろし、位置・周回を戻し、カウンター操作を逆順に打ち消す（別トリガーの変更は残る・負になってもそのまま）。
- §8.3 先頭へ: 直前のトリガーの位置を 0・周回と履歴を消す（カウンターは変えない）。
- §8.4 対象が無いとき（未設定 / 自分自身 / アクティブなトリガー一覧に無い / 単発の待機中）は何もせず一時メッセージ。
- back / rewind が対象へ行った変更は、実行したトリガーの履歴・直前のトリガーに数えない。対象の選択は押したトリガーの選択より後。
- §4.3・§4.4: 位置変更・編集で履歴を消す / 履歴と直前のトリガーは実行位置と同じ契機で消す・付け替える。

**application 中心**。presentation は一時メッセージの配線だけ。domain は変更しない。

## 対象範囲（application 中心・presentation は配線のみ）

### `keyseq/application/sequence_history.py`（新規）

戻す履歴を runner から分離して置く（runner は 268 行で肥大を避ける）。
- `HistoryEntry`（dataclass）: 位置 / 周回スタック / カウンター差分の列（`(名前, 差分)`。+1 は `+1`、0 にした操作は `-k`〔k = 0 にする前の値〕）。
- `StepSnapshot`（dataclass）: ステップ開始時の位置・周回スタック（と `trigger_set_id` / key）。
- 積む・降ろす・消す・上限 100 の処理と、差分の打ち消し（`counters[name] -= delta` を逆順）を関数で持つ。
- 「状態が変わったか」の判定（位置・周回の差分、またはカウンター差分が 1 つ以上）。

### `keyseq/application/sequence_steps.py`

- カウンター操作の差分を `StepOutcome`（と待機をまたぐ `StepResume`）に積んで返す（`counter_inc` → `+1` / `counter_reset` → `-k`）。
- `back` / `rewind` に到達したら、呼び出し側が渡すコールバック（例: `on_control: Callable[[str], None] | None`）に op を渡して次の行へ進む
  （`advance` は他のトリガーの状態に触れない。コールバックが無ければ従来どおり素通り）。

### `keyseq/application/app_state.py`

- 履歴: `trigger_set_id` → key → `list[HistoryEntry]`（`loop_frames` と同じ持ち方）。直前のトリガー `last_trigger: tuple[str, str] | None`。
- `reset_indices` / `forget_trigger_set` で履歴と（該当する）直前のトリガーを消す。`rekey_trigger_set` で履歴を付け替え、直前のトリガーの id も新しい id へ。

### `keyseq/application/sequence_runner.py`

- ステップ開始時に `StepSnapshot` を取り、ステップ終了時（通常アクションの実行後・`perform_action` が False・エラー・通常アクション無しで終了・
  単発の待機の取り消し）に `sequence_history` で積む判定をし、積んだら `last_trigger` を更新する。
  待機をまたぐステップは開始時の控えと差分を保留中ステップ（単発）/ runner の続き状態（連続）に持たせる。
- `back` / `rewind` のコールバック: 対象 = `last_trigger`。§8.4 に当たれば一時メッセージ（`notify_message` コールバック）を出して何もしない。
  - 文言: 対象なし・自分自身・一覧に無い → 「戻す対象のトリガーがありません」/ 待機中 → 「対象のトリガーが待機中のため操作できません」。
  - back: 対象の履歴を 1 段降ろして復元（位置・周回を保存・カウンター差分を打ち消し）。履歴が空なら何もしない。
  - rewind: 対象の位置 0・周回と履歴を消す。
  - 対象の選択（`select_trigger(target)`）は、押したトリガーの選択（既存の `finally` 等）の**後**に行う。
- `reset_loop_frames(key)`（位置変更・編集時に呼ばれる）で、そのキーの履歴も消す（§4.3）。トリガー削除時（task_03 で `cancel_pending_wait` を呼ぶ箇所）でも履歴を消す。
- コンストラクタに `notify_message: Callable[[str], None] | None = None`（キーワード・既定 None）を追加。
- 行数が増えるなら、戻す・先頭への処理を `sequence_history.py` 側へ寄せて runner を 300 行未満に保つ。

### presentation（配線のみ）

- `keyseq/presentation/app.py`: `SequenceRunner` に `notify_message=lambda msg: self._set_flash_message(msg)` を渡す。
- `keyseq/presentation/controllers/trigger_panel_controller.py`: `delete_trigger` / `rename_trigger` で周回スタックを消す・付け替える既存箇所に合わせて、履歴も同様に扱う
  （runner か AppState の公開メソッド経由。直接 dict を触る箇所を増やさない）。

### テスト

- `tests/test_sequence_history.py`（新規）: 積む条件（変化なしは積まない）/ 上限 100 / 差分の打ち消し（+1・0 にした操作・逆順・別トリガーの変更が残る例
  〔A: 0→1, B: 1→2, A を戻す → 1〕〔A: 5→0, B: 0→1, A を戻す → 6〕・負になってもそのまま）。
- `tests/test_sequence_steps.py`（追記）: カウンター差分の記録・待機をまたいだ記録 / back・rewind でコールバックが呼ばれ次の行へ進む。
- `tests/test_sequence_runner.py`（追記）: 単発で 1 段ずつ戻る（位置・周回・カウンター）/ 位置 0 で履歴が空なら何もしない / 先頭へ（位置 0・履歴消去・カウンター不変）/
  直前のトリガーの更新規則（`[back]` だけのトリガーは直前にならない・エラーで止まったステップは直前になる）/ §8.4 の 4 条件で一時メッセージのみ /
  対象の選択が押したトリガーの後 / 位置変更・編集・削除・`reset_indices`・`rekey_trigger_set` での履歴と直前の扱い / 待機の取り消しで 1 段積む / 連続実行のステップも積む /
  back・rewind を含まないシーケンスの挙動不変。

### 設計メモ / 制約

- 復元した位置・周回は、次のステップ開始時の整合検査（§4.3）の対象になる（戻した後のシーケンスが編集されていても壊れない）。
- 連続実行中は他のトリガーの押下が無視される（現行）ため、連続実行中の対象を戻す経路は無い。
- `sequence_history.py` は tkinter・presentation を import しない。

## 読むファイル

- `instructions/history/26_sequence_control_actions.md` §2-9・§2-16・§4.2〜§4.4・§7（取り消し時の履歴）・§8（仕様）
- `keyseq/application/sequence_steps.py` / `keyseq/application/sequence_runner.py` / `keyseq/application/app_state.py`（編集対象・全体）
- `keyseq/presentation/app.py:196-215`（runner の組み立て）/ `:297-310`（`_set_flash_message`）
- `keyseq/presentation/controllers/trigger_panel_controller.py` の `rename_trigger` / `delete_trigger`（`rg -n` で位置を特定し範囲指定）
- `tests/test_sequence_runner.py` / `tests/test_sequence_steps.py`（既存テストの書き方・偽のタイマー）

## 含まない

- file_line → task_05 / 編集 UI → task_06 / 一覧の表示（周回・カウンター値・色）→ task_07 / 正本反映 → task_08
- キーマップ一時停止での待機の取り消し（§7 の契機外）

## 確認

- 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` がエラー無し。
- 単体: `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sequence_history tests.test_sequence_steps tests.test_sequence_runner -v` が全 pass。
- 退行: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`・`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass、
  `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass。
- `wc -l keyseq/application/sequence_runner.py` が 300 未満。`grep` で `sequence_history.py` に `tkinter` / `keyseq.presentation` の import が無い。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_07 でまとめて実施。
