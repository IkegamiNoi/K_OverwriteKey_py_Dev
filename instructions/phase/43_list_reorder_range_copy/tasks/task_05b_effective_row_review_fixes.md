# task_05b_effective_row_review_fixes

## 目的

task_05 + task_05a の完了判定前レビュー（deep-reviewer「修正要」・Codex 標準レビュー P2）で採用した修正（暫定 30 §2・§5.1・§5.2・§10-8）。
**presentation 限定。domain / application 不変・スキーマ不変。**

## 対象範囲（presentation 限定）

### 1. グレーの行のシーケンス編集で有効な行の状態を変えない（deep 指摘 1・4・高）

- `keyseq/presentation/controllers/trigger_panel/action_edit.py` の、キーで実行中の状態を触る全経路
  （追加 `:101-104`・複製 / 貼り付け `_append_actions` `:155-159`・編集 `:222`・削除 `:244-249`・移動 `:292-295`。行番号は 2026-10-02 時点）で、
  **編集しているトリガーが有効な行のときだけ** `_indices[key]` の調整と `sequence_runner.reset_loop_frames(key)` を行う。
  グレーの行ではシーケンス（アクション列）の変更と未保存化・再描画だけを行う
- 判定は「編集しているトリガーの実体」が一覧で有効な行か（`keyseq/domain/trigger_duplicates.py` の関数と、実体の同一性 `is` で位置を求める）。判定を 1 つの補助関数にまとめて各経路から使う

### 2. キー変更でキーを変えないときは重なりの検査をしない（deep 指摘 2・中）

- `trigger_panel_controller.py` の `rename_trigger` で、停止 / トグル / 直接切替 / 置換元キーとの重なりの検査（`:520-532` 付近）も `key_exists` と同じく**キーが変わるときだけ**行う
  （正本 `key_input.md` §7.3「グレー表示の行も編集はできる」・暫定 §5.2「キーを変えない編集では重複検査をしない」）

### 3. キー変更の後にシーケンス欄を再描画（Codex P2）

- `rename_trigger` の反映後、`refresh_triggers()` に加えて `refresh_actions()` を呼ぶ（グレーの行が新しいキーで有効になったとき `▶` が出る）

### 4. 交代の共通手順でキーが消える場合も後始末する（deep 指摘 3・中・task_07 の範囲削除の前提）

- `controllers/trigger_panel/effective_row_transition.py` の共通手順で、交代したキーに加えて**操作前にあり操作後に無いキー**も、反映後に同じ後始末（状態の消去）をする（消えるキーは拒否の対象にしない＝現行の削除と同じ）
- `delete_trigger` の「有効な行の削除でキーが無くなる場合」の個別の後始末をこの共通手順へ寄せ、分岐を減らす（振る舞いは変えない）

### テスト（追加・修正まで）

- `tests_ui/test_trigger_effective_row_transition.py`（または新規ファイル）: グレーの行で 追加・複製・貼り付け・編集・削除・移動 をしても、有効な行の `_indices`・周回・履歴が変わらず `reset_loop_frames` が呼ばれない /
  有効な行では現行どおり / 停止キーと重なった行のラベル変更ができる（キーを変える場合は現行どおり拒否）/ グレーの行のキーを未使用のキーへ変えると `▶` が出る /
  共通手順でキーが消える場合に状態が消える（`delete_trigger` の既存の振る舞いが変わらない）

## 読むファイル

- 暫定仕様 §5.1・§5.2
- `keyseq/presentation/controllers/trigger_panel/action_edit.py`（全体）
- `keyseq/presentation/controllers/trigger_panel/effective_row_transition.py`（全体）
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:490-600`（`rename_trigger`・`_apply_trigger_rename`・`delete_trigger`）
- `keyseq/domain/trigger_duplicates.py`
- `tests_ui/test_trigger_effective_row_transition.py`（流儀）

## 含まない

- domain の走査の共通化・`has_active_execution` の置き場と条件の揃え・rename の事前確定（deep 指摘 7・8・9・10 = 保留）
- 呼び出し先の「入っているフレーム」の意味の明確化（deep 指摘 5 = task_09 の正本反映でユーザー確認）
- 並べ替え・貼り付け・範囲削除の UI（task_07）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストが全 pass・`-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（task_05・05a・05b の完了判定）。
- 実機目視は task_07 でまとめて実施。
