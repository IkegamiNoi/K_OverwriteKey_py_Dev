# task_02_held_send_record

## 目的

押したままのキー（key_hold・キーリピート）は**押したときの送り方で**離す・一時的に離して押し直す・送り直す（暫定 48 §4）。今は離す時点のレイアウトでキー名を引き直すため、離しの失敗と切替が重なると別の走査コードへ送って成功扱いになり、元のキーが押されたまま残る。
**infrastructure（`input_gateway.py` の送り方の値と公開関数）+ application（`held_inputs.py`・`key_repeat.py`）。application は infrastructure を import しない。presentation・JSON スキーマは不変。**

## 対象範囲（infrastructure + application + テスト）

### `keyseq/infrastructure/input_gateway.py`

- 不変の値 `KeySend`（`@dataclass(frozen=True)`）: `kind`（"numpad" / "extended" / "keyboard" / "layout"）・`values`（`_resolve_key` の結果のタプル。extended は vk と走査コード）・`key`（キー名。keyboard の種類はキー名で `keyboard.press` / `release` するため）
- `InputGateway` に公開関数:
  - `resolve_send(key: str) -> KeySend`（`_resolve_key` を包む。不明なキーは今と同じ ValueError）
  - `press_send(send: KeySend)` / `release_send(send: KeySend)`（今の `press_key` / `release_key` の本体をこちらへ移す）
  - `identity_of(send: KeySend) -> tuple[int, bool]`（今の `key_identity` の本体）
- 既存の `press_key(key)` / `release_key(key)` / `key_identity(key)` は `resolve_send` + 上の関数で書き直す（**送り方・挙動・呼び出し元は不変**）

### `keyseq/application/key_repeat.py`

- 送信の callback を `send(identity, key)` に変える（`set_callbacks` の型 :35-41・呼び出し :101）。key は表示・エラー用に残す。他の挙動は不変

### `keyseq/application/held_inputs.py`

- `HeldInput` に `send: object | None = None` を足す（キーボードのときだけ。中身を知らない値として持ち、gateway へ返すだけ。**infrastructure を import しない**）
- `press_key(owner, key, ...)`: `send = self.input_gateway.resolve_send(key)` を 1 回だけ呼び、identity は `("key", *self.input_gateway.identity_of(send))`。`_record` に send を渡す。送信は `press_send(send)`、補償の離しは `release_send(send)`
- 記録の送り方を使う送信（今のレイアウトで引き直さない）:
  - `_release_records`（`release_owner` / `release_all` / `release_keyboard`）・`_suspend_keyboard`: `release_send(record.send)`
  - `resume_keyboard`: 公開の `press_key` を経由せず、記録の send で `press_send` する内部の道筋（identity・送り方を引き直さない）。押し直しの失敗の補償（補償の離しが成功すれば記録を消す）は今と同じ
  - `_send_repeat(identity, key)`: `self._records.get(identity)` の send で `press_send`。**記録が無い（または send が None）なら送らずリピートを止める**（`self._repeater.stop()`）
  - `_repeat_failed`: identity の記録があればその send で離し記録を消す。無ければ今と同じ `release_key(key)`
- `release_key(key)`: 今のレイアウトで identity を引き（`_key_identity(key)`）、**記録があればその send で `release_send`**、無ければ今と同じく `input_gateway.release_key(key)`。解決できないキー名は今と同じ ValueError
- `_key_identity(key)` は `resolve_send` + `identity_of` で作る（`key_identity` を使い続けてもよい）

### テスト（偽 gateway・偽リピーターの更新を含む）

- 偽 gateway に `resolve_send` / `press_send` / `release_send` / `identity_of` を足す: `tests/test_held_inputs.py:8`・`tests/test_held_inputs_repeat.py:33`・`tests/test_action_executor_key_hold.py:12`・`tests/test_sequence_runner_key_hold.py:36`（既存の検査が「名前で送った」記録を見ていれば、send の key で同じ記録になるようにする）
- `tests/test_key_repeat.py`・`tests/test_input_gateway_repeat.py`: callback の引数の変更に合わせる
- 追加（`tests/test_held_inputs.py` 等）:
  - 押した後にレイアウト（偽 gateway の解決）を変えても、`release_all` / `release_owner` / `release_keyboard` / `suspend_keyboard` / `resume_keyboard` は**押したときの send** で送る
  - 離しに失敗して残った記録の再試行（`release_all` をもう一度）も押したときの send で送る
  - リピートの送り直しは記録の send で送り、記録が無ければ送らず止まる
  - `release_key(key)` は記録があればその send・無ければ今のレイアウトで離す
- `tests/test_input_gateway_send.py`: `resolve_send` / `press_send` / `release_send` / `identity_of` が今の `press_key` / `release_key` / `key_identity` と同じ送り方になる（keyboard の種類は `keyboard.press(key)` のキー名・extended は vk と走査コード・layout は走査コード）

### 設計メモ / 制約

- `KeySend` は infrastructure に置き、application は型として参照しない（`object` として持つ）
- 押す側で一度解決した send を、記録・送信・補償・identity のすべてに使う（解決を 2 回しない）
- 既存の公開の `press_key` / `release_key` / `key_identity` を消さない（`action_executor` 等の他の呼び出し元のため）

## 読むファイル

1. `instructions/history/48_layout_snapshot_for_hook.md` §4・§5・§7
2. `keyseq/infrastructure/input_gateway.py:1-30`・`:120-222`・`:278-360`
3. `keyseq/application/held_inputs.py`（全体・編集対象）
4. `keyseq/application/key_repeat.py`（全体・編集対象）
5. テスト: 上記「テスト」の各ファイル（偽 gateway の定義部と関係する検査）

## 含まない

- `LayoutController` の写し（task_01 で済み）
- 正本・codebase_map の更新（task_03）
- `action_executor` の送信経路（hotkey・直接置換・text）の変更

## 確認

- 上記「テスト」の追加・修正がすべて pass
- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- `-m unittest discover -s tests` 全 pass / `-m unittest discover -s tests_ui` 全 pass（単独実行）/ `-m tests.smoke_app` pass
- grep: `keyseq/application` に `from keyseq.infrastructure` の追加が無い

## 追加修正（2026-10-21・verifier と reviewer で判明）

実装は正しく、既存テストの期待が新しい作り（記録の送り方で送る）に追いついていない。テストを新しい作りに合わせる + reviewer 低 1:

1. `tests/test_held_inputs_repeat.py:204-213` `test_alias_with_same_identity_stops_repeat_before_release_send`: `release_key("a alias")` は同じ identity の記録（"a" で押した）の送り方で離す（暫定 48 §4-6）。失敗の仕込みと最後の呼び出しの期待を、記録の送り方での離し（偽 gateway の release_send の記録の形）へ直す。テストの意図（離しが失敗してもリピートは先に止まる）は保つ
2. `tests_ui/test_key_hold_presentation.py:66-67`: `Mock(spec=InputGateway)` に `resolve_send.side_effect`（キー名をそのまま返す等の中身を知らない値）と `identity_of.side_effect`（今の `key_identity` と同じ `(ord(key[0]), False)`）を設定する。`release_key` を期待している検査（:151-221 付近）は、押したままのキーの離しが `release_send` になったので `release_send` へ（引数は resolve_send が返した値）
3. `tests_ui/test_task06_keymap_management_ui.py:64-65`・`:204-215`・`:239-247`: `patch.object(self.app.input_gateway, "release_key")` で押したままのキーの離しを数えている箇所は `release_send` を patch し、`assert_called_once` + 引数の `.key == "shift"` を確かめる（押す側を patch している箇所は `press_send` も要るか確認）
4. `keyseq/application/held_inputs.py` `_repeat_failed`: `record.send is None` の分岐（到達しない互換コード）を削除し、記録があれば `release_send(record.send)` + 記録を消す・無ければ `release_key(key)` の 2 分岐にする

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は **task_03 でまとめて実施**（暫定 48 §7-7 ②）。
