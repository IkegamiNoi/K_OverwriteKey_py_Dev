# task_05c_tk9_right_click

## 目的

task_06 の probe（2026-11-11・Mac・Tk 9.1.0 aqua）で、右クリックが `<Button-3>` で届くことを実測した（3 回とも。Tk 8.6 までの aqua は `<Button-2>`）。
task_05 で入れた `tk_platform.right_click_sequence` は aqua で `<Button-2>` を返すため、Mac ではキーボードUIとヘルプの右クリックメニューが出ず、`<Button-2>` は中クリックに当たる。
Mac の Tk は Tk 9.1（decisions 2026-11-10・暫定 57 §8 Q1 を task_06 で改訂）なので、右クリックはどの OS でも `<Button-3>` になる。`right_click_sequence` をやめ、呼び出し 2 か所を task_05 以前の `"<Button-3>"` に戻す。

**レイヤ制約**: presentation のみ。domain / application / infrastructure 不変・JSON スキーマ不変。Windows は従来も `<Button-3>` のため**動作不変**。

## 対象範囲（presentation 限定）

### `keyseq/presentation/tk_platform.py`

- `right_click_sequence` を削除する（他の関数は変えない）。

### `keyseq/presentation/keyboard_window.py`

- `:144` の `self.canvas.bind(right_click_sequence(self.canvas), ...)` を `self.canvas.bind("<Button-3>", ...)` に戻す。
- `:38` の `right_click_sequence` の import を削除する。

### `keyseq/presentation/help/help_tab_view.py`

- `:97` の `self.text.bind(right_click_sequence(self), ...)` を `self.text.bind("<Button-3>", ...)` に戻す。
- `:10` の import から `right_click_sequence` を外す（`primary_modifier` は残す）。

### `tests/test_tk_platform.py`

- import から `right_click_sequence` を外し、`test_windows_results` / `test_aqua_results` の `right_click_sequence` の assert 2 行を削除する（他の assert は残す）。

## 読むファイル

- `keyseq/presentation/tk_platform.py`・`tests/test_tk_platform.py`
- `keyseq/presentation/keyboard_window.py:30-45,138-150`
- `keyseq/presentation/help/help_tab_view.py:1-15,90-100`

## 含まない

- 中ボタン（`<Button-2>`）の既存バインド（`call_view_controller.py` 等）は変えない（Tk 9 の aqua でも中クリック = 2 のため正しい）
- 暫定 57 §4 の「右クリックは aqua では `<Button-2>`」の記述の改訂（task_06）
- Control+クリックを右クリック扱いにすること（要件なし）

## 確認

**Mac**（`../../../.venv/bin/python`）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_tk_platform` が失敗 0
- `grep -rn right_click_sequence keyseq tests tests_ui` が 0 件
- `-m tests.smoke_app` が pass
- `-m unittest discover -s tests` の失敗・エラーが task_05 時点（失敗 89・エラー 15）から増えない
- `main.py` を起動し、キーボードUIのキーの右クリックが届くこと（編集中なら編集がキャンセルされる）と、ヘルプの本文の右クリックで「コピー」が出てコピーできること（ユーザー目視）
  - 2026-11-11 実施: 両方 OK。キーボードUIの右クリックによる**割り当てのクリア**は、Mac ではスタブのキー検証で割り当てを作れないため目視できず、**task_09 で確認する**（ユーザー判断）

**Windows**: 動作不変のため、次に Windows で標準検証 4 種を行う機会にまとめて実施する。
- 2026-11-13 実施（M1）: compile clean・tests 1997 件 失敗 0 / エラー 0 / skip 7・tests_ui 1271 件 失敗 0 / エラー 0・smoke OK（verifier）。目視 OK（ユーザー）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視: Mac の右クリックメニューは本タスクで実施（ユーザー）。
