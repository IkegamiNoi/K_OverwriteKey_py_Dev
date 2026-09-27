# task_07c_eager_system

## 目的

暫定仕様 26 v0.4 §2-20・§4.1（先行処理）を実装する。実機目視で「単発実行の『次に実行』が system の行を指し、実際にはその前の通常アクションが実行される」
ズレが見つかったため、**通常アクションを実行した直後に、続く system をその場で処理**して、位置を次に実行される行へ進める。

- 先行処理するのは **loop_start / loop_end / counter_inc / counter_reset** だけ。**wait / back / rewind / エラーになる行**（対応崩れ・深さ超過・回数不正・未定義 op・
  カウンター名が空）に達したら、**処理せずその行で止める**（エラーは通知しない。次の押下の通常処理で通知される）。10,000 の上限に達したら黙って止める。
- 末尾に達したら位置 0・周回を空にし、**単発**ではその押下でまだ先頭へ回っていなければ先頭から同じ規則で続ける（連続は停止し、先頭は処理しない）。
- 先行処理は「この押下の開始位置に達したら終える」規則の**対象外**（先頭へ 1 度だけ・10,000 は適用）。§4.1 の例（`[カウンター+1, A]`）の動きになること。
- 先行処理はそのステップに含める: カウンター差分は同じステップの差分に加え、戻す履歴の 1 段 = 通常アクション + 先行処理。

**application 限定**（`sequence_steps.py` と `sequence_runner.py`）。presentation・domain は変更しない（表示は既存の再描画で位置どおりになる）。

## 対象範囲（application 限定）

### `keyseq/application/sequence_steps.py`

- `settle_after_normal(actions, position, frames, counters, *, allow_wrap: bool) -> SettleOutcome`（名前は任意）:
  `after_normal_action` で得た位置から上記の規則で先行処理し、最終の位置・周回スタック・カウンター差分（`(名前, 差分)` の列。task_04 と同じ表現）・先頭へ回ったかを返す。
  - 対象の op の処理は既存の `_loop_start` / `_loop_end` / `_counter` の規則と同じ結果になること（重複実装しない。エラーになる場合は「処理せず止まる」へ置き換えるため、
    既存関数を「事前に判定できる形」に分けるか、写しで試してから確定する等、状態を壊さない方法にする）。
  - 呼び出し側の `counters` を直接更新する（差分も返す）。

### `keyseq/application/sequence_runner.py`

- 単発（通常の押下・待機の続き）: 通常アクションの成功後に `after_normal_action` → `settle_after_normal(allow_wrap=<この押下でまだ先頭へ回っていない>)` → 位置・周回を保存し、
  先行処理の差分をステップの差分に加えてから履歴を積む。
- 連続: 通常アクションの成功後に同様に先行処理（`allow_wrap=False`）。位置が 0 になったら従来どおり停止、そうでなければ間隔の後に次のステップ。
- `perform_action` が False のとき・エラーのときは先行処理しない（位置はその行に残る・従来どおり）。
- 行数は 340 行未満に保つ。

### テスト

- `tests/test_sequence_steps.py`（追記）: 先行処理の単体（ループ終わりで戻る / ループを抜けて次の通常アクション / カウンター +1・0 に / 待機・戻す・先頭へで止まる /
  エラー行で止まり通知しない・状態を変えない / 末尾 → 先頭へ回る〔単発〕・回らない〔`allow_wrap=False`〕/ 先頭へ 1 度だけ / 10,000 で止まる / 差分の記録）。
- `tests/test_sequence_runner.py`（追記）: 単発 `[loop×3, A, loop_end]` で押すたびに位置が A・周回 1→2→3 と進み、3 回で抜ける / `[counter+1, A]` の n が実行回数と一致 /
  戻すで先行処理ぶんも打ち消される / 待機の続きの後も先行処理される / 連続実行で先行処理後に末尾なら停止 / 位置が待機・戻すの行で止まる /
  system を含まないシーケンスの挙動不変（既存テストが変更なしで通ること）。
- 既存テストの期待値が先行処理で変わる場合は、**仕様 v0.4 に沿うように**直す（変えた理由をテスト名かコメントに残す）。

## 読むファイル

- `instructions/history/26_sequence_control_actions.md` §2-20・§4.1・§8.1（仕様）
- `keyseq/application/sequence_steps.py` / `keyseq/application/sequence_runner.py`（編集対象・全体）
- `keyseq/application/sequence_history.py`（差分と commit の扱いのみ）
- `tests/test_sequence_steps.py` / `tests/test_sequence_runner.py`（既存テスト）

## 含まない

- presentation・domain の変更 / 正本・codebase_map → task_08

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` がエラー無し。
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`・`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass、`..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass。
- `wc -l keyseq/application/sequence_runner.py` が 340 未満。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（ユーザー）**: task_07b の H1（一覧にフォーカスを置いたまま押しても周回が進む）と、本タスクの「次に実行」の選択が実行される行を指すこと。
