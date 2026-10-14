# task_06a_fixed_op_key_overlap_check

## 目的

task_06 の統合レビュー（deep-reviewer 中・codex-reviewer P2・ユーザー採用 2026-10-14）の修正。編集の窓の OK の検査で、**固定の操作キー（esc / num enter）と枠のキーの重なり**を、未編集の今つながる画面を含めて拒否する（暫定 41 §8「枠のキーと操作キー（固定の esc / num enter を含む）の重なり」）。
あわせて §5「何もしない場合はクリック点も変えない」のテストの抜け 2 件を足す。
**domain の `validate_ops` のみ + テスト**。presentation / application は変えない（`grid_editor_window.py` は既に `frame_keys` を集めて `validate_ops` へ渡している）。

## 対象範囲

### `keyseq/domain/screen_grid/ops.py` の `validate_ops`

* 8 操作の検査の後に、`FIXED_OP_KEYS ∩ frame_names` の各キーについて（`FIXED_BACK_KEY` → `FIXED_CLICK_KEY` の順で）理由を足す:
  「操作キー（戻る・固定）: 枠のキー 'esc' と重なっています」/「操作キー（クリック・固定）: 枠のキー 'num enter' と重なっています」
* 既存の 8 操作の検査・文言・順序は変えない

### テスト

* `tests/test_screen_grid_ops.py`: `validate_ops(DEFAULT_OPS, set(), {"esc"})` / `{"num enter"}` / 両方 が上の理由を返す・既定の枠のキーでは空のまま（既存の `test_default_ops_do_not_overlap_default_frame_keys` が通ること）
* `tests_ui/test_grid_editor_window.py` の `test_accept_saves_custom_operations_and_rejects_conflicts` の `cases` に追加: **未編集の今つながる画面（`secondary`）の記録に枠のキー `esc`**（`ops` は既定のまま・その画面へ切り替えない）で OK が拒否され窓が閉じない。`num enter` も同様
* `tests/test_screen_grid_session.py`（暫定 41 §5）:
  * 選択ありでクリック点をずらした後、Space で細分化できない（細分化した 1 枠が 4px 未満になる）とき、クリック点・選択が変わらない
  * 最上段で選択ありでクリック点をずらした後、BackSpace（付け替え可の back）を押してもクリック点・選択が変わらない

## 読むファイル

* `instructions/history/41_grid_crosshair_nudge.md`（§5・§8）
* `keyseq/domain/screen_grid/ops.py`（全体・編集対象）
* `tests/test_screen_grid_ops.py`・`tests/test_screen_grid_session.py`（全体・編集対象）
* `tests_ui/test_grid_editor_window.py`（:560-610 と組み立て部分 :1-60）

## 含まない

* 拒否のメッセージに画面名を出すこと（見送り・ユーザー判断 2026-10-14）
* presentation / application の変更・正本反映（task_07）

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_screen_grid_ops tests.test_screen_grid_session tests_ui.test_grid_editor_window` が全 pass
* `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `discover -s tests_ui` が全 pass・`-m tests.smoke_app` OK

## 完了条件

* 上記確認 pass・**reviewer 採用**
* 実機目視なし（手編集データのときだけの検査）
