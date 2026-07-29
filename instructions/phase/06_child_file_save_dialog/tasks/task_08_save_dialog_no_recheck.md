# task_08_save_dialog_no_recheck

## 目的

trigger_set を別名保存して子（sequence）の保存先が再計算されるたびに**一覧ダイアログが再表示され、
同じ選択をやり直させられる**冗長さを解消する（暫定仕様 05 **v0.3-A** / §3-3）。
併せて、緩和で生じる「未提示パスへの無断上書き」を **v0.3-A2**（行単位の上書き確認）で塞ぐ。

- レイヤ制約: **presentation 限定**（`config_io/keymap_set_io.py` / `config_io/child_save_dialog.py`）。
  **application / domain 不変・スキーマ不変**。`config_service` へ新しい問い合わせ API を足さない
  （既存の `resolve_child_save_targets` / `find_dependency_blocked_sequences` /
  `read_parent_refs` / `canonical_path` / `is_path_within` で足りる）。
- 判定は **task_07 の `canonical_path` / `is_path_within`** を使う（パス文字列の表記差で誤検出しない）。

## 対象範囲（presentation 限定）

### 1. `config_io/keymap_set_io.py` — `_collect_child_save_plan` の再表示廃止

**廃止するのは「保存先の再計算を理由とする自動再表示」だけ**。ユーザーが依存確認で
「選び直す」を明示的に選んだときの再表示は**残す**（唯一の戻り口のため）。

変更後の流れ:

1. `targets` / `rows` を解決し、**一覧ダイアログを 1 回表示**して `choices` を得る
2. `build_save_plan` で計画を作る
3. trigger_set の保存先が変わる場合（`_trigger_target_changed`）は、
   **`targets` を再解決して計画を組み直すだけ**にする（**一覧は再表示しない**）。
   再計算が起きた事実は 4 の確認と完了メッセージで扱う
4. **v0.3-A2 の上書き確認**（下記 2）を行う
5. 依存確認（trigger_set が `ACTION_SKIP` で保存先が変わる sequence がある場合）は**従来どおり**。
   「選び直す」が選ばれたときだけ 1 へ戻る（`rows` が空なら従来どおり保存中止）

- `show_recalculation_notice`（再表示時の注記ラベル）は**役目を失うため削除**する
  （`child_save_dialog.py` の属性・`_create_action_dialog` の分岐・`offset` 計算を含む）。
- **戻り値を `tuple[SavePlan | None, str]` に変える**（第 2 要素 = 再計算の事後通知文。
  再計算なしなら空文字）。呼び出しは `save_keymap_set_to` の 1 箇所のみ。
- `save_keymap_set_to` は、通知文が空でなければ **`flash_message` と保存完了ダイアログの本文へ追記**する
  （例: 「トリガー一覧の保存先が変わったため、出力シーケンス 2 件の保存先を再計算しました。」）。
  **確認は求めない**（v0.3-A）。

### 2. `config_io/child_save_dialog.py` — 再計算先の上書き確認（v0.3-A2）

`confirm_recalculated_overwrite(rows)` を追加する（`confirm_trigger_set_dependency` と同じ作法）。

- **対象行の条件（3 つすべてを満たす行のみ）**:
  1. **一覧で `ACTION_SAVE` を選んだ行**であること（`ACTION_SAVE_AS` はユーザーがパスを明示済み・
     `ACTION_SKIP` は書かないため対象外）
  2. 再計算後の保存先が、**一覧に提示した保存先と異なる**こと（`canonical_path` で比較）
  3. 再計算後の保存先に**既存ファイルがあり**、その共有状況が **`SHARE_SOLE` 以外**であること
     （判定は `child_save_rows.build_row` を再計算後のパスで作り直して得る）
- **一覧に出ていない子（非 dirty）は対象外**。非 dirty の子は保存先が既存なら `ACTION_SKIP`・
  未作成なら `ACTION_SAVE` になり、既存ファイルを上書きしないため。
- **対象行が 0 件ならダイアログを出さない**（別名保存先が新規領域なら通常 0 件）。
- 表示: 対象行ごとに **種別 / 対象名 / 新しい保存先 / 共有状況**を列挙し、
  `messagebox.askyesnocancel` で **「はい」= このまま上書き / 「いいえ」= 別名で保存 /
  「キャンセル」= 保存を中止**。**既定ボタンは `messagebox.NO`**（安全側。依存確認と同じ方針）。
- 「いいえ」を選んだ場合は**対象行ごとに `_ask_save_as_path` を開く**。1 つでもキャンセルされたら
  **保存を中止**（既存の `_resolve_action_targets` と同じ扱い）。選ばれたパスは `choices` を
  `ACTION_SAVE_AS` へ更新して計画を組み直す。
- 「キャンセル」は `_collect_child_save_plan` から `None` を返す（＝保存中止・1 件も書かない）。

### 3. テスト

| ファイル | 内容 |
|---|---|
| `tests_ui/test_child_save_dialog.py` | **既存 `test_trigger_set_save_as_recalculates_sequence_targets_before_saving` の期待値を更新**。再表示が無くなるため `ask.call_count` は **1**。再計算後の保存先へ保存されること・既存の `other.json` が変わらないこと（非 dirty の SKIP）は維持 |
| `tests_ui/test_child_save_dialog.py` | **新規: A2 が発火するケース**。`ACTION_SAVE` を選んだ dirty な sequence の再計算後の保存先に、**別の上位に属す既存ファイル**を置き、①上書き確認が出る ②「はい」で上書きされる ③「いいえ」＋別名パス指定でそちらへ書かれ既存ファイルが変わらない ④「キャンセル」で 1 件も書かれない |
| `tests_ui/test_child_save_dialog.py` | **新規: A2 が発火しないケース**。再計算後の保存先が未作成のときは確認が出ない（`confirm_recalculated_overwrite` が呼ばれない） |
| `tests_ui/test_child_save_dialog.py` | 依存確認の「選び直す」で**一覧が再表示される**こと（`ask.call_count == 2`）が維持されているか（既存 `test_dependency_reselect_*` の確認） |

### 設計メモ / 制約

- **再計算後の `targets` で計画を組み直すこと**が肝。`build_save_plan` の非 dirty 子の既定
  （`ACTION_SKIP if os.path.exists(targets[child_id]) else ACTION_SAVE`）は `targets` に依存するため、
  再解決前の `targets` で作った計画をそのまま使うと索引切れ・誤 SKIP を招く。
- 既存の不変条件を壊さないこと: **②未知・別の上位に属す保存先を明示操作なしに上書きしない**
  （一覧の既定 + 依存確認の既定ボタン + 今回の A2 既定ボタン）/ **⑤アクションの優先順位は
  `child_save_plan.build_save_plan` の 1 箇所**（一覧の選択 > confirmed > 非 dirty 既定）。
- `pending` / `confirmed`（`SavePlan`）の受け渡しの形は変えなくてよい。再表示が減るだけで
  優先順位の規則は同じ。
- 無限ループを作らないこと。「選び直す」以外で 1 へ戻る経路を残さない。

## 含まない

- **一覧ダイアログのレイアウト（固定サイズ・縦スクロール・省略表示＋ツールチップ）— task_09**。
  本タスクでは `_add_rows` / `_add_headers` のレイアウトに手を入れない
  （`show_recalculation_notice` の削除に伴う `offset` の整理は本タスクの範囲）。
- **正本 `spec_detail/` への反映 — task_10**。
- 依存確認ダイアログ（`confirm_trigger_set_dependency`）の廃止・文面変更。**従来どおり出す**。
- `config_service` 側の API 追加・保存計画の型（`SavePlan` / `ChildSaveEntry`）の変更。
- 個別保存ボタンの統合（暫定仕様 §11）/ 参照元の掃除（idea_07）。

## 確認

`.venv` の python で実行する（worktree ルートから `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests_ui` が clean
2. `-m unittest discover -s tests` が全 pass（現行 136 件）
3. `-m unittest discover -s tests_ui` が全 pass（現行 107 件 + 追加分）
4. `-m tests.smoke_app` が pass
5. **受入条件 12**: trigger_set の別名保存で保存先が再計算されても**一覧が再表示されない**
   （`ask_child_save_actions` の呼び出しが 1 回）
6. **受入条件 12b**: 再計算先が既存ファイル（`SHARE_SOLE` 以外）の「保存」行があるときだけ
   上書き確認が出て、承認なしに上書きされない。0 件なら確認も出ない
7. 既存の特性テスト（保存 JSON のバイト列比較）を**緩めずに** pass すること
8. `grep` で `show_recalculation_notice` が `keyseq/` と `tests_ui/` に残っていないこと

## 完了条件

- 上記確認 1〜8 が pass・**reviewer 採用**。
- 実機目視は**本タスクでは行わない**（task_09 完了後に task_10 の前でまとめて実施する）。
