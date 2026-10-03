# task_06_sequence_save_identifier

## 目的

同じトリガー一覧に同じキーの行が複数あっても、保存でシーケンスが入れ替わったり消えたりしないよう、シーケンスの保存計画の識別子を
「一覧 id + キー + 同じキーの何番目か」に変え、識別子を作る / 分解する / キーで行を引き当てる全箇所を行単位にする（暫定 30 v0.6 §5.4）。
個別保存 / 一括保存のダイアログで同じキーの行に行番号を併記し、保存の前後で実行中の状態が保たれることをテストで固定する。
**application（save_plan・config_service）+ presentation（config_io・dirty_state）。domain 不変・JSON スキーマ不変。**
計画時の一覧・並びの固定と書き込み直前の照合は task_06a。

## 対象範囲（application + presentation・スキーマ不変）

### `keyseq/application/save_plan.py`

- 識別子の規則（**1 番目は現行と同一**・2 番目以降だけ番号を足す。区切りは現行の `SEQUENCE_KEY_SEPARATOR`）:
  - 新規 `sequence_row_token(trigger_key: str, occurrence: int = 1) -> str`: `occurrence == 1` なら `trigger_key`、2 以上なら `trigger_key + SEP + str(occurrence)`。
    キーが空・区切りを含む・`occurrence < 1` は `SavePlanError`
  - 新規 `split_sequence_row_token(token: str) -> tuple[str, int]`: 上の逆（1 部ならその番号は 1。2 部目が 2 以上の整数でなければ `SavePlanError`）
  - `compose_sequence_key(trigger_set_id, trigger_key, occurrence: int = 1) -> str` = `trigger_set_id + SEP + sequence_row_token(...)`（既存の入力検査は維持）
  - `split_sequence_key(key) -> tuple[str, str, int]`（一覧 id・キー・何番目か）に変更し、**全呼び出し元を 3 要素に追随**させる（2 部 / 3 部とも受け付け、それ以外は `SavePlanError`）
- 新規 `sequence_rows(triggers) -> list[tuple[dict, str, int]]`: 一覧の上から dict の行だけを走査し、`(行, 正規化したキー, 同じキーの何番目か〔1 始まり〕)` を返す。
  正規化は `normalize_key_name`・空キーの行は除く（現行の走査と同じ除外）。**識別子を作る箇所はすべてこれを使い、キーごとの数え方を一か所にする**

### `keyseq/application/config_service/`

- `split_payloads.py:319-389`: 各行の `plan_key` を `sequence_rows` の何番目かを使って作る（一覧 id ありは `compose_sequence_key(id, key, n)`、なし〔個別保存〕は `sequence_row_token(key, n)`）
- `save_plan_execution.py`:
  - `normalize_save_runtime`（25-36）: 入力検査は現行のまま（キーに区切りが無いことの検査）
  - `:355`・`:373`: `split_sequence_key(...)[0]` の追随
  - `:476-491`（一括保存の後処理）: 行を `sequence_rows` で走査し `compose_sequence_key(id, key, n)` で引く（**同じキーの行に別の行のパス・参照元を付けない**）
- `keymap_save_plan.py:170-185`（`_clear_saved_sequence_states`）: キーが一致する全行ではなく、識別子の行（キー + 何番目か）だけの印を外す
- `child_file_io.py:121-138`（個別保存の後処理）: `by_key` をキーではなく `item["key"]`（行の token）で引き、行を `sequence_rows` で走査して token で対応させる

### `keyseq/presentation/controllers/`

- `config_io/child_save_plan.py:99-112`（`_sequence_keys`）: キーを一意化せず、`sequence_rows` の各行の識別子を返す
- `config_io/child_save_rows.py:179-198`: 識別子を `sequence_rows` の何番目かで作る。**同じ一覧に同じキーが 2 行以上あるときは、表示名の末尾に `（N 行目）`**（N = その一覧での行の位置・1 始まり）を付ける。1 行だけなら現行どおり
- `config_io/keymap_set_io.py:398`・`:472-487`: `split_sequence_key` の追随。`_has_source_path` は識別子の行（キー + 何番目か）だけを見る。`_blocked_labels` は行ごとの識別子で表示名を作る（同じキーの 2 行目以降も上と同じ `（N 行目）` 付き）
- `config_io/trigger_set_file_io.py:146-169`: 個別保存の行・選択・計画のキーを `sequence_row_token`（キー + 何番目か）にする（現行の `split_sequence_key(...)[1]` = キーだけ、をやめる）
- `dirty_state.py:150-160`: 除外判定を行ごとの識別子（`sequence_rows` の何番目か）で行う

### テスト（追加・修正まで）

- `tests/test_save_plan.py`: token / 識別子の往復・1 番目が現行と同一・不正値（空キー・区切り入り・番号 0 / 1 / 非整数の 3 部目）の拒否・`sequence_rows` の数え方（空キー・dict 以外を飛ばす・正規化で同じになるキーを同じキーとして数える）
- 既存テストの `split_sequence_key` 2 要素前提の箇所を 3 要素へ追随
- 新規 `tests/test_duplicate_key_sequence_save.py`（または既存の保存テストへ追加）: 同じ一覧に同じキーの行が 2 つあり actions が異なる構成で
  - 一括保存 → 読込で、2 行のシーケンスが入れ替わらず両方残る（別ファイルに保存され、各行の読込元のパスが自分のファイルを指す）
  - 個別保存でも同様・保存後の未保存の印は各行の分だけ外れる
  - 2 行目だけを「保存しない」にしたとき、1 行目だけ印が外れる
  - **保存の前後で `app._indices`・周回・戻す用の履歴が変わらない**（保存経路から状態を作り直す処理が無いことの固定。実装の変更は不要の見込み）
- `tests/test_child_save_rows.py`: 同じキーが 2 行のとき両方の行が別の識別子で出て、表示名に `（N 行目）` が付く / 1 行なら付かない

### 設計メモ / 制約

- 重複が無い構成では識別子・保存結果・ダイアログの表示が現行と完全に同じであること（既存テストが無修正で通るのが目安。`split_sequence_key` の要素数の追随は除く）
- 「何番目か」は保存計画を作る時点の一覧の並びで数える。並べ替えによるずれは task_06a の照合で防ぐ（本タスクでは扱わない）
- 保存ファイル名の重複回避は現行の `used_paths`（`split_payloads.py`）に任せる

## 読むファイル

- 暫定仕様 `instructions/history/30_list_reorder_range_copy.md` §5.4
- `keyseq/application/save_plan.py`（全体）
- 上記「対象範囲」の各ファイルの該当行の前後（編集箇所のみ。ファイル全体は読まない）
- `keyseq/application/config_service/split_payloads.py:300-400`
- 既存テスト: `tests/test_save_plan.py`・`tests/test_child_save_rows.py`・`tests/test_child_save_plan.py`・`tests/test_per_keymap_bulk_save.py`（書き方の手本・追随箇所の確認）

## 含まない

- 計画時の一覧と並びの固定・書き込み直前の照合・中止の理由表示（task_06a）
- トリガー一覧の複製 / 貼り付け（task_07）・キーマップ一覧（task_08）
- JSON 形式の変更（しない）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_save_plan tests.test_child_save_rows tests.test_child_save_plan tests.test_per_keymap_bulk_save` と新規テストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。task_06a と合わせて完了判定前に `deep-reviewer` + Codex レビュー（phase.md の方針）。
- 実機目視は task_06a でまとめて実施（同じキーの 2 行を保存 → 読込）。
