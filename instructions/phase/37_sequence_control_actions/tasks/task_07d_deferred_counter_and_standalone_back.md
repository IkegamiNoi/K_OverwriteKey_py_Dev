# task_07d_deferred_counter_and_standalone_back

## 目的

実機目視を受けた暫定仕様 26 v0.5 の §2-25・§2-26 を実装する。
- **§2-25 カウンターの保留**: 先行処理（task_07c）でカウンターの行（+1 / 0 に）に達したら、**値を変えずに位置だけ進め、操作をトリガーごとの「保留」に控える**。
  保留は、そのトリガーの次のステップの開始時（system の処理より前）に順に反映し、そのステップの差分（戻す履歴）として記録する。
  一覧の `(=値)` と file_line の参照値が「直前に実行した通常アクションの時点の値」になる。ループの周回は変えない（v0.4 のまま）。
  - 保留は位置と同じ単位（trigger_set_id, key）で持ち、§4.4 の契機（reset_indices / forget / rekey / トリガー削除・キー変更）・位置変更と編集（`reset_loop_frames`）・先頭へ（rewind）で消す。
  - 戻す: ステップ開始時の保留も控え、位置・周回と一緒に復元する（反映した差分は従来どおり打ち消す）。
- **§2-26 戻す・先頭へ の単独登録**:
  - 編集: 空でないシーケンスへ戻す・先頭へを追加しない / 戻す・先頭へのあるシーケンスに他の行を追加しない / 既存の行を戻す・先頭へに変える編集は、シーケンスがその 1 行だけのときに限る。
    いずれも OK 後に `messagebox.showinfo` で理由を示して反映しない（ダイアログの選択肢は変えない）。
  - 実行: 戻す・先頭へ の行に達したとき、シーケンスに他の行があれば実行時エラー（「戻す・先頭へは単独で登録してください」）で止まる（§8.5）。

**application + domain（編集規則の純関数）+ presentation（controller の判定呼び出し）**。

## 対象範囲

### `keyseq/application/sequence_steps.py`

- 先行処理（`settle_after_normal`）でカウンターの行に達したら、値と差分を変えずに保留の列（例: `[(op, 名前)]`）へ追加して次の行へ進める。
  カウンター名が空の行は従来どおり「処理せず止まる」。
- `advance` に保留の列を受け取る引数を追加し、ステップの開始時（周回の整合検査の後・system の処理の前）に順に反映して差分へ記録する
  （待機の続き〔`resume`〕では再反映しない）。
- `back` / `rewind` の行: `len(actions) > 1` なら実行時エラー（位置はその行）。先行処理では従来どおり止まるだけ。

### `keyseq/application/app_state.py`

- 保留の列を `loop_frames` と同じ持ち方で追加し、`reset_indices` / `forget_trigger_set` / `rekey_trigger_set` / トリガー単位の消去・付け替え（`forget_trigger` / `rekey_trigger`）で同様に扱う。

### `keyseq/application/sequence_history.py` / `sequence_runner.py`

- ステップ開始時の控え（`StepSnapshot`）に保留を含め、`back` で復元する。`rewind` と `reset_loop_frames` で保留を消す。
- runner はステップ開始時に保留を `advance` へ渡し、ステップ後に新しい保留を保存する（単発・待機の続き・連続実行とも）。「状態が変わったか」の判定に保留の変化も含める。
- `sequence_runner.py` は 360 行未満（増えるなら保留の出し入れを `sequence_history.py` 側の関数へ寄せる）。

### `keyseq/domain/sequence_editing.py`

- `standalone_violation(actions, item, *, replace_index: int | None = None) -> bool`（名前は任意）: 追加（`replace_index=None`）または置換の結果が §2-26 に反するか。
  戻す・先頭へ の判定は `sequence_control` の定数を使う。

### `keyseq/presentation/controllers/trigger_panel_controller.py`

- `add_action` / `edit_action`: ダイアログの結果（ループは対にする前の始まり 1 行で判定してよい）について `standalone_violation` が真なら、
  `messagebox.showinfo("追加" / "編集", "戻す・先頭へは、出力シーケンスにそれ 1 つだけで登録してください。")` を出して反映しない。

### テスト

- `tests/test_sequence_steps.py`（追記）: 先行処理でカウンターが保留になる（値・差分は不変・位置は進む）/ 次のステップの開始で反映され差分に記録 / 待機の続きで再反映しない /
  back・rewind の混在で実行時エラー・単独なら従来どおり。
- `tests/test_sequence_runner.py`（追記・既存の期待値は v0.5 に合わせて直す）: `[counter+1, A]` の単発で、各押下後の n と一覧用の値が実行回数と一致（1 回目後 n=1・2 回目後 n=2）/
  ループ内 `[loop×2, counter+1, A, loop_end]` でも同様 / 戻すで位置・周回・保留が戻り n も戻る / 先頭へ・位置変更・編集で保留が消える /
  他トリガーの file_line が現在値を参照する / 連続実行でも保留は次のステップで反映。
- `tests/test_sequence_editing.py`（追記）: 単独登録の判定（空への追加・混在への追加・置換で 1 行だけ / 2 行以上）。
- `tests_ui/`（追記）: controller が違反時に案内を出して反映しないこと（既存 `test_trigger_panel_controller_action_edit.py` に倣う）。
- AppState の保留の生存期間（reset / forget / rekey / forget_trigger / rekey_trigger）。

## 読むファイル

- `instructions/history/26_sequence_control_actions.md` §2-25・§2-26・§4.1・§4.4・§8.2・§8.3・§8.5・§11.2（仕様）
- `keyseq/application/{sequence_steps,sequence_runner,sequence_history,app_state}.py`（編集対象・全体）
- `keyseq/domain/sequence_editing.py`（編集対象）/ `keyseq/domain/sequence_control.py`（定数のみ）
- `keyseq/presentation/controllers/trigger_panel_controller.py` の `add_action` / `edit_action`（`rg -n` で位置を特定し範囲指定）
- 既存テスト: `tests/test_sequence_steps.py` / `tests/test_sequence_runner.py` / `tests/test_sequence_editing.py` / `tests_ui/test_trigger_panel_controller_action_edit.py`

## 含まない

- ループの周回表示の変更（v0.4 のまま）/ ダイアログの選択肢の変更 / 正本・codebase_map（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` がエラー無し。
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`・`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass、`..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass。
- `wc -l keyseq/application/sequence_runner.py` が 360 未満。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（ユーザー）**: カウンターの表示が現在値になること・file_line の行がずれないこと・戻す / 先頭への単独登録の案内。task_07b の H1 と task_07c の選択表示も合わせて確認。
