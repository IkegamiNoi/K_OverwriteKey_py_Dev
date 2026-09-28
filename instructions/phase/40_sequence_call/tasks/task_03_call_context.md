# task_03_call_context

## 目的

呼び出し文脈（開始時点のコピー + 呼び出しスタック）と「文脈の 1 ステップ」を、runner から独立した application の新規モジュールとして作る（暫定 29 §4.2・§4.4・§4.5 の差分と通知の連鎖）。
**送信・時間待ちの予約はしない**（何を送る / 待つ / 終わったかを返すだけ）。単発（task_04）・連続実行（task_05）の両方がこの口を使う。
**application の新規モジュール + 単体テストのみ・既存ファイルは変更しない**。

## 対象範囲

### `keyseq/application/call_context.py`（新規）

型:
- `CallFrame`（dataclass）: `key: str` / `position: int = 0` / `frames: list[LoopFrame]` / `deferred: list[tuple[str, str]]`（文脈の中の保留）/ `resume: StepResume | None`（文脈の中の待機の続き）。
- `CallContext`（dataclass）: `trigger_set_id: str` / `root_key: str` / `first_target: str` / `snapshot: dict[str, CallEntry | None]`（task_01 の `collect_call_snapshot`）/ `stack: list[CallFrame]` / `started: bool`。
- `CallStep`（dataclass・frozen）: `kind: Literal["action", "wait", "next", "done", "error"]` / `action: dict | None`（kind=action のとき送る行）/ `wait_ms: int | None` /
  `message: str | None`（kind=error）/ `chain: tuple[str, ...]`（通知の連鎖。スタックのキーの列＝呼び出し先の根から最上段まで。呼び出し元は含めない）/
  `counter_deltas: tuple[tuple[str, int], ...]`（**このステップで新しく生じた**カウンターの差分だけ）/ `interval_ms: int | None`（kind=next のとき、次の `call_step` までに置く間隔 = 今の最上段の呼び出し先の間隔）。

関数:
- `start_call(trigger_set_id, root_key, target_key, find_trigger) -> CallContext`: `collect_call_snapshot(target_key, find_trigger)` でコピーを作る（段はまだ積まない）。
- `call_step(ctx, counters) -> CallStep`: 次のアクションまで進める。
  1. `started` でなければ `first_target` の段を積む（下の「段を積む」）。
  2. 最上段で `advance(copy.actions, frame.position, frame.frames, counters, wrap_once=False, resume=frame.resume, deferred_counters=frame.deferred〔resume が無いときだけ渡し、渡したら空にする〕,
     on_control=None, stop_ends_run=False, in_call=True)`。
     - `normal_index` の行が**呼び出し** → その段の位置を呼び出しの行に置き、呼び出し先の段を積んで（下）、同じ `call_step` の中で続ける（入れ子の最初のステップは間隔を置かない）。
     - 通常アクション（hotkey / text / mouse_click / file_line）→ 段の位置をその行に置き `kind="action"`。
     - 待機 → `frame.resume = outcome.resume`・`frame.position = outcome.resume_position`・`frames` を保存し `kind="wait"`。
     - エラー → `kind="error"`（`message` はそのまま・`chain`）。**戻す / 先頭へが 2 行以上に混ざっているときの advance のエラーもこの経路**。
     - 末尾（`reached_end`）→ 段を降ろす（下）。スタックが空になれば `kind="done"`。空でなければ下の段で**呼び出しの行が完了した**ものとして
       `after_normal_action` → `settle_after_normal(..., stop_ends_run=False, in_call=True)`（保留は下の段の `deferred` へ）して、同じ `call_step` の中で続ける。
  3. 差分: `advance` の `counter_deltas` は resume の差分を含む累計なので、**resume の分を除いた新しい分**だけを `CallStep.counter_deltas` に積む（段の降ろしで反映した保留の差分も含める）。
- `finish_call_action(ctx, counters) -> CallStep`: runner がアクションを送り終えた（file_line は完了が成功した）後に呼ぶ。最上段で
  `after_normal_action` → `settle_after_normal(..., stop_ends_run=False, in_call=True)`（保留は段の `deferred` へ）。位置 0 で末尾に達したら段を降ろし（下）、
  下の段では呼び出しの行が完了したものとして同じ処理を繰り返す。スタックが空になれば `kind="done"`、そうでなければ `kind="next"`・`interval_ms` = 今の最上段の呼び出し先の間隔
  （runner は interval_ms 後に `call_step` を呼ぶ）。
- 段を積む（内部）: 判定順 1) 積むと深さ（スタックの段数）が `MAX_CALL_DEPTH` を超える → エラー「呼び出しの深さが 9 を超えます」/ 2) キーが `root_key` かスタックにある → エラー「呼び出しが循環します（…）」/
  3) コピーの表に無い・None → エラー「呼び出し先のトリガーがありません（f5）」/ 4) コピーのシーケンスが 1 行で戻す / 先頭へ → エラー「戻す・先頭へのトリガーは呼び出せません」/
  5) `target` が空 → エラー「呼び出し先が指定されていません」。エラーの `chain` は積もうとしたキーを含める。問題なければ `CallFrame(key)` を積む。
- 段を降ろす（内部）: その段の `deferred` を `apply_deferred_counters` で反映（差分を積む）して取り除く。
- 補助: `chain_text(chain) -> str`（「呼び出し: f5 > f6」）・`top_interval(ctx) -> int`。

### テスト（`tests/test_call_context.py`・新規）

`find_trigger` は辞書で差し替え、送信は行わない（`call_step` / `finish_call_action` を順に呼んで結果を確かめる）:
1. `[A, B]` を呼ぶ → action A → finish（next・interval=呼び出し先の間隔）→ action B → finish → done
2. 空のシーケンス → すぐ done
3. 入れ子 `f5=[A, call f6, C]`・`f6=[B]` → A → B（入れ子の最初は同じ call_step の中）→ C → done / chain が `("f5", "f6")`
4. 待機 `[A, wait 100, B]` → A → finish → wait(100) → call_step で B
5. 停止は読み飛ばす `[A, stop, B]` → A → B / 無限ループ `[loop∞, A, loop_end]` → error「呼び出し先に無限ループがあります」
6. カウンター: `[counter_inc, A, counter_inc]` → 最初の action の差分に +1 / 末尾の +1 は段を降ろすときに反映され done の差分に入る。待機をまたいで二重に数えない
7. エラー: 深さ 10・循環（根を呼ぶ / スタックのキーを呼ぶ）・参照先なし・戻す / 先頭へだけ・target 空のそれぞれの文言と chain
8. 開始時点のコピー: `start_call` の後に元の辞書のシーケンスを書き換えても実行内容が変わらない / 間隔も開始時点の値
9. ループ内の呼び出し `[loop×2, call f6, loop_end]` → f6 の中身が 2 回

## 読むファイル

- `instructions/history/29_sequence_call.md` §4.2〜§4.5
- `keyseq/domain/call_graph.py`（task_01・`CallEntry` / `collect_call_snapshot`）/ `keyseq/domain/sequence_control.py:1-40`
- `keyseq/application/sequence_steps.py`（`LoopFrame` / `StepResume` / `StepOutcome` / `apply_deferred_counters` / `advance` / `after_normal_action` / `settle_after_normal` のシグネチャと戻り値）
- `tests/test_sequence_steps.py:1-40`（書き方の手本）

## 含まない

- runner への組み込み・予約・送信・保留・再照合・打ち切り（task_04・05）/ UI（task_06〜08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_call_context -v` が全 pass・`unittest discover -s tests` が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 段の積み降ろしと判定順 / 入れ子の最初のステップを同じ呼び出しで進める / 差分を二重に数えない / 保留の反映の時点 / 開始時点のコピー / runner 非依存 / 先取りなし）。
