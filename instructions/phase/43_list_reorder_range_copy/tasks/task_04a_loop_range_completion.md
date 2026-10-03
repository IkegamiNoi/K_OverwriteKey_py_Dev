# task_04a_loop_range_completion

## 目的

出力シーケンスの複製ボタン・Ctrl+C で、範囲にループの片側だけが含まれるときは拒否せず、元の一覧の対の行を範囲の外に補って閉じる
（暫定 30 v0.5 §3.4・§4.3。task_04 の実機目視でのユーザー提案）。
**domain に純関数 1 つ + presentation の呼び出し 2 か所。application 不変・スキーマ不変。**

## 対象範囲（domain の純関数追加 + presentation の配線）

### `keyseq/domain/sequence_editing.py`

- 新規 `closed_loop_range(actions: Sequence[Any], start: int, end: int) -> list[Any]`:
  `actions[start:end+1]` に、`analyze_loops(actions).pairs` で対になっているが片側だけ範囲内にある行の相手を補った並びを返す
  - 範囲内の「終わり」の相手の始まりが `start` より前 → 範囲の先頭の前に置く / 範囲内の「始まり」の相手の終わりが `end` より後 → 範囲の末尾の後に置く
  - 補う行が複数なら元の一覧の添字の昇順（先頭の前の始まりも、末尾の後の終わりも）
  - 返すのは元の行オブジェクトそのもの（写しは呼び出し側が作る。現行の `safe_deepcopy` / `ListClipboard.copy` のまま）。元の `actions` は変えない
  - `structure.unmatched`（相手のいない行）は補わずそのまま含める（`paste_violation` が `PASTE_UNBALANCED_LOOP` で拒否する）
  - 範囲が不正（`start > end` / 範囲外）なら `ValueError`

### `keyseq/presentation/controllers/trigger_panel/action_edit.py`

- `duplicate_action`・`copy_actions` の `actions[start : end + 1]` を `closed_loop_range(actions, start, end)` に置き換える（`paste_actions` は不変）
- `_show_append_violation` の `PASTE_UNBALANCED_LOOP` の文言を「対になっていないループの始まり / 終わりは複製 / 貼り付けできません。」に変える

### テスト（追加・修正まで）

- `tests/test_sequence_editing.py`: `closed_loop_range` の単体テスト
  - `[L1始, T1, T2, L1終]` の `T2..L1終`（添字 2..3）→ `[L1始, T2, L1終]`（同一オブジェクト）
  - 始まりだけ（`L1始..T1`）→ `[L1始, T1, L1終]`
  - `[L1始, A, L1終, L2始, B, L2終]` の `A..B`（1..4）→ `[L1始, A, L1終, L2始, B, L2終]`
  - 入れ子 `[L1始, L2始, A, L2終, L1終]` の `L2終..L1終`（3..4）→ `[L1始, L2始, L2終, L1終]` / `A..A` → `[A]`（補わない）/ `L2始..A`（1..2）→ `[L2始, A, L2終]`
  - 閉じた範囲・ループなしはそのまま / 相手のいない終わり（`[A, L終]` の 1..1）は補わずそのまま / 元の一覧が変わらない / 不正な範囲は ValueError
- `tests_ui/test_sequence_copy_paste.py`:
  - `test_invalid_loop_and_standalone_appends_show_reason_without_mutating` の前半（始まり側だけをコピー → 拒否）は v0.5 で拒否されなくなるため、
    「相手のいないループの行（例 `[A, loop_end]` の loop_end）をコピー → 貼らず案内（文言は「対になっていない」を含む）」に書き換える（後半の戻すの検査は維持）
  - 追加: 複製ボタンで `[L始, T1, T2, L終]` の `T2..L終` を選ぶ → 末尾に `L始, T2, L終` の 3 行が付き、`count` が元と同じ・3 行が選択範囲（`refresh_actions(select=(4, 6))`）
  - 追加: Ctrl+C で始まり側だけ → 保管庫の内容が閉じている（`paste(CLIP_ACTIONS)` が対を含む）→ 別のトリガーへ Ctrl+V で貼れる。コピー後に元の対の行を編集しても保管庫は変わらない

### 設計メモ / 制約

- 対の判定は `analyze_loops` の `pairs` / `reverse_pairs` を使い、独自に括弧を数えない
- 深さ・戻す / 先頭への判定は現行の `paste_violation` のまま（補った後の並びに対して働く）

## 読むファイル

- 暫定仕様 `instructions/history/30_list_reorder_range_copy.md` §3.4・§4.3
- `keyseq/domain/sequence_editing.py`（全体）
- `keyseq/domain/sequence_control.py:1-110`（`LoopStructure` / `analyze_loops`）
- `keyseq/presentation/controllers/trigger_panel/action_edit.py:116-180`
- `tests/test_sequence_editing.py:190-230`（paste_violation のテストの書き方）
- `tests_ui/test_sequence_copy_paste.py`（全体）

## 含まない

- トリガー一覧・キーマップ一覧の複製 / 貼り付け（task_07・task_08）/ 移動の規則（§4.2）の変更
- 貼り付け（Ctrl+V）時の補完（保管庫は閉じた範囲を持つため不要）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_sequence_editing tests_ui.test_sequence_copy_paste` が全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: `L始 → T1 → T2 → L終` で `T2 → L終` を複製 → `L始 → T2 → L終` が末尾に付く / 始まり側だけの Ctrl+C → 別のトリガーへ Ctrl+V。
