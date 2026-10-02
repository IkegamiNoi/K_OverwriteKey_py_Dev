# task_05a_trigger_effective_row_transition

## 目的

同じキーの有効な行（一番上の行）が別の既存の行へ入れ替わる「交代」を判定し、交代したキーの実行中の状態を削除と同じく消す。
そのキーに進行中の実行があれば交代させる操作を拒否する。あわせて、グレーの行を選んだときのシーケンス欄の扱いを入れる
（暫定 30 §5.1・§10-7・8・9a）。task_05 から分割（2026-10-02）。
**application（進行中の問い合わせ 1 つを新設）+ presentation（交代の判定と適用・削除 / キー変更・シーケンス欄）。スキーマ不変。**

## 前提（裏取り済み 2026-10-02）

- 連続実行は次の一歩ごとにキーでトリガーを引き直す（`sequence_runner.py:306`）。現行の削除はこの検索の失敗で止まるため、同じキーの行が残る交代では止まらず下の行を実行し続ける → 拒否が要る
- 呼び出しは開始時に呼び出し先のアクション列を写して使う（`call_context.py:53-65` の `collect_call_snapshot`）

## 対象範囲

### `keyseq/application/sequence_runner/`（`SequenceRunner` に問い合わせを 1 つ新設）

- `has_active_execution(key: str) -> bool`: アクティブなトリガー一覧で、`key`（正規化）について次のいずれかがあれば True
  - 連続実行（実行中・一時停止中）の実行元が `key`（`state.run_to_end_key`）
  - `state.pending_steps` に `(現在のトリガー一覧 id, key)` がある（単発の待ち・呼び出し・file_line。一時停止中の単発の呼び出しを含む）
  - 進行中の呼び出しの文脈（連続実行中の `_run_to_end_call`・単発の `PendingStep.call`）の呼び出し元・呼び出し先のフレームのキーに `key` がある
  - 連続実行の file_line の読込中で、その実行元が `key`
- 読み取り専用（状態を変えない）。置き場は runner 本体または既存の mixin のうち責務の合う所。テストは `tests/` へ

### `keyseq/domain/trigger_duplicates.py`（task_05 の新規モジュールへ追加）

- `effective_rows_by_key(triggers: Sequence[Any]) -> dict[str, int]`: キー → 有効な行の位置（id ではなく位置。呼び出し側が実体に写す）
- `replaced_effective_keys(before: Sequence[Any], after: Sequence[Any]) -> frozenset[str]`: 操作の前後で、両方にあるキーのうち有効な行の**実体**（`is`）が変わったキーの集合（後で無くなったキーは含めない＝交代ではない）

### presentation（`trigger_panel_controller.py`。処理が大きくなるなら同じフォルダに補助モジュールを作る）

- **交代の適用の手順**（task_07 の並べ替え・貼り付け・範囲削除でも使う共通処理として 1 か所に置く）:
  1. 操作の後の並びを作る（まだデータへ反映しない）→ `replaced_effective_keys(前, 後)` を求める
  2. 交代するキーのどれかで `sequence_runner.has_active_execution(key)` が True なら、反映せず理由を一時メッセージ（`App._set_flash_message`）に出して中止（例「f5 は実行中のため、有効なトリガーを入れ替えられません」）
  3. 反映し、交代した各キーの状態を**現行の削除と同じ後始末**（`_indices` / 周回 / `cancel_pending_wait` / `forget_trigger`）で消す。この後始末は 1 つの関数にまとめ、現行の `delete_trigger` からも使う
- **削除**（`delete_trigger`。範囲削除は task_07）:
  - グレーの行（有効でない行）の削除: キーの状態を**消さない**（状態は有効な行のもの。現行はキーで消してしまう）
  - 有効な行の削除で同じキーの下の行が残る: 交代 → 上の手順（進行中なら拒否）
  - 有効な行の削除で同じキーの行が無くなる: 現行どおり（交代ではない）
- **キー変更**（`rename_trigger`）: 有効な行のキーを変え、旧キーに下の行が残る場合は旧キーが交代 → 進行中なら拒否。拒否しなければ現行どおり状態を新キーへ移す（移した後の旧キーは状態なし＝後始末は不要だが、残っていれば消す）
- **グレーの行を選んだとき**（§5.1）:
  - シーケンス欄はその行のシーケンスを表示し `▶` を付けない
  - シーケンス欄のクリック・↑↓で次に実行を変えない（`on_action_list_select` 系の経路）
  - ステータスの次に実行の要約・省略表示の要約は、グレーの行では出さない（有効な行の状態を表示しない）
  - 判定は `is_effective_trigger(一覧, 選択中の行)`。キーで引いて有効な行の状態を表示している箇所（`select_next_action_row`・`update_status` 付近・`on_action_list_select`）を、選択中の行が有効な行のときだけ動くようにする

### テスト

- `tests/`: `has_active_execution`（連続実行の実行中・一時停止中・単発の待ち・単発の呼び出しの間隔待ち・呼び出し先のフレーム・file_line・何も無い）/
  `effective_rows_by_key`・`replaced_effective_keys`（削除・並べ替え・キー変更・キーが無くなる場合は含まない）
- `tests_ui/test_trigger_effective_row_transition.py`（新規）: グレーの行の削除で有効な行の位置・履歴が残る / 有効な行の削除で下の行へ交代し状態が消える /
  連続実行中（一時停止中）のキーの交代を伴う削除・キー変更が拒否され一時メッセージ / グレーの行を選ぶと `▶` が無くシーケンス欄のクリックで有効な行の位置が変わらない・要約が出ない

### 設計メモ / 制約

- presentation に `"triggers"` 直値を書かない。`trigger_panel_controller.py`（約 640 行）へ足す量を抑え、交代の手順は補助モジュール（例 `controllers/trigger_panel/effective_row_transition.py`）へ置く
- 関数 30 行の目安

## 読むファイル

- 暫定仕様 §5.1
- `keyseq/domain/trigger_duplicates.py`（task_05）
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:185-330`（`refresh_actions`・`select_next_action_row`・`update_status`）・`:465-560`（`rename_trigger`・`delete_trigger`）・`:580-620`（`on_action_list_select` 系）
- `keyseq/application/app_state.py:26-47`・`:105-125`（状態と `forget_trigger` / `rekey_trigger`）
- `keyseq/application/sequence_runner/sequence_runner.py:40-130`・`:236-320`（状態・`cancel_pending_wait`・連続実行の一歩）
- `keyseq/application/sequence_runner/call_wait.py:20-50`・`call_run_to_end.py:30-55`・`keyseq/application/call_context.py:20-40`（呼び出しの文脈とフレーム）

## 含まない

- 並べ替え・貼り付け・範囲削除への交代の手順の適用（task_07）/ 保存（task_06）/ 正本の更新（task_09）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストが全 pass・`-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。task_05 と合わせて完了判定前に **deep-reviewer + Codex レビュー**（phase.md レビュー方針）。
- 実機目視は task_07 でまとめて実施。
