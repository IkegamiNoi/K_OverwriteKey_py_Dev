# task_04_call_view_summary

## 目的

呼び出し先の表示枠（task_05・06）に渡す**要約**と、runner から UI へ知らせる**口**を application 側に作る（暫定 31 v0.5 §5.2・§5.3・§10-7・§10-8 の application 側）。
**application 限定（新規 `application/call_view.py` + `sequence_runner/`）。presentation の枠・配線（app.py）は task_05。実行の挙動は変えない。**

## 対象範囲

### 新規 `keyseq/application/call_view.py`（純粋なデータと組み立て）

- 不変の値 `CallViewSummary`（`@dataclass(frozen=True)`）:
  - `path: tuple[str, ...]` = 呼び出し元のキーから最上段までのキー（正規化後の小文字。例 `("f1", "f5", "f7")`）
  - `actions: tuple[dict, ...]` = **最上段の呼び出し先の開始時点の写し**の行（表示の側が書き換えないよう**深い複製**）
  - `position: int` = 最上段の位置（`▶` の行）
  - `loop_frames` = 最上段の周回（表示の `[loop] 2/3` 用の写し）
  - `counters: Mapping[str, int]` = 表示に使うカウンターの値の写し（`(=値)` 用）
- `build_call_view_summary(ctx: CallContext, counters) -> CallViewSummary | None`（文脈に段が無ければ None）

### `keyseq/application/sequence_runner/`（runner）

- `SequenceRunner.__init__` に任意の注入 **`notify_call_view: Callable[[CallViewSummary | None], None] | None = None`** を足す（既存の `update_status` と同じ形。None なら何もしない）
- **表示する文脈の選び方**（§5.2）: runner が「止まった文脈」を止まった順に覚える（識別 = 単発は `(trigger_set_id, key)`・連続実行は 1 つの固定の識別）。
  - **止まった**とき（単発の呼び出しの一時停止〔ステップの押下の合間を含む〕・連続実行の一時停止で文脈がある〔停止の行による一時停止を含む〕）に、その識別を末尾へ移す
  - 文脈が**無くなった**とき（成功・打ち切り・エラー・捨てる・フック停止・構成セットの読込等 = `on_runtime_reset`）に、その識別を消す
  - 表示する文脈 = 覚えている中で**最後に止まったもの**。無ければ None
- **開いている状態**（§5.2）: 「止まった」ときに開き（表示する文脈が決まる）、覚えている文脈が 1 つも無くなったら閉じる（None を知らせる）。**処理中に新しく開くことはしない**（一括の呼び出しが流れているだけでは開かない）
- **知らせる契機**（§5.3）: 開いている間、次のたびに `notify_call_view(要約)` を呼ぶ（UI スレッドから。runner の処理は既に UI スレッド）:
  表示する文脈が変わった / その文脈の位置・周回が変わった（文脈の 1 ステップのたび）/ **カウンターの値が変わり得るとき**（どのトリガーのステップの後・戻す / 先頭への後・保留の反映の後）/ 閉じた（None）
  - 同じ要約を続けて知らせないための比較はしてよい（しなくてもよい）。重い処理にしない
- 既存の `update_status` / `refresh_actions` の呼び出しは変えない

### テスト（追加・修正まで）

- 新規 `tests/test_call_view.py`: `build_call_view_summary` の経路（入れ子の 3 段で `("f1","f5","f7")`）・写しが深い複製（要約の行を書き換えても文脈が変わらない）・位置と周回・カウンターの写し・段が無ければ None
- `tests/test_sequence_runner_call.py`（偽の `notify_call_view` で受け取った列を確かめる）:
  - 一括の呼び出しが最後まで流れるだけでは何も知らせない（開かない）
  - ステップの単発: 1 押下目の後に要約（位置 = 次の行）/ 2 押下目で位置が進む / 呼び出しの成功で None
  - 連続実行の停止の行で一時停止 → 要約 / 再開して処理中も位置の変化を知らせる / 終わったら None
  - 2 つの文脈（単発の合間と連続実行の一時停止）があるとき、**最後に止まったもの**を出す。それが無くなると残りの方を出す
  - 表示中の文脈が止まっている間に、**別のトリガーがカウンターを変える**と、同じ文脈の要約がカウンターの新しい値で知らされる
  - フック停止（`cancel_pending_waits` / `stop_run_to_end`）・`discard_paused`・構成セットの読込（`on_runtime_reset`）で None
  - `notify_call_view` を渡さない（None）runner でも既存のテストが通る

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §5.2・§5.3
- `keyseq/application/call_context.py`（`CallContext`・`CallFrame`）
- `keyseq/application/sequence_runner/sequence_runner.py:28-80`・`:280-340`
- `keyseq/application/sequence_runner/{input_acceptance,call_wait,call_run_to_end}.py`（一時停止・再開・捨てる・完了の箇所）
- `keyseq/application/app_state.py`（`pending_steps`・`counters`）
- 手本のテスト: `tests/test_sequence_runner_call.py`

## 含まない

- presentation の枠・境界線・`app.py` の配線・高さの保存（task_05）/ 省略表示（task_06）/ 正本反映（task_07）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass（tests_ui は verifier 1 つで実行）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視: なし（UI は task_05 で目視）。
