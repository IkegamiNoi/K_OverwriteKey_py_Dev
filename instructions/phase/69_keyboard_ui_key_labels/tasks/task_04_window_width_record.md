# task_04_window_width_record

## 目的

利用者が変えたキーボードUIの窓の幅をレイアウトごとに `config/config.json` の `keyboard_window_widths` へ記録し、
開くとき・レイアウトを切り替えたときにその幅で出す（記録が無ければ最小）（暫定 52 §2-8・§5「レイアウトの切替」・§8）。
**presentation に限定（キーボードUI・それを開くコントローラ・Tk 非依存の解釈）。config.json の任意キー `keyboard_window_widths` を追加（既存キーは不変）。書き込みは `StartupIo.write_startup` 1 本を通す。**

## 対象範囲（キーボードUI・layout_controller・大きさの純関数・tests 限定）

### `keyseq/presentation/keyboard_window_size.py`

- `KEYBOARD_WINDOW_WIDTHS_KEY = "keyboard_window_widths"`
- `parse_keyboard_window_widths(raw: object) -> dict[str, int]`: dict でなければ `{}` / 値ごとに判定し、bool を含む非 int・1 未満は捨てる / キーは文字列だけ採る（`compact_window_size.parse_compact_window_size` の `positive_int` と同じ判定）

### `keyseq/presentation/keyboard_window.py`

- コンストラクタに任意の引数を 2 つ足す（既定 None・None なら記録しない / 記録の幅なし）:
  - `get_saved_width: Callable[[str], int | None]`（layout_id → 記録の幅）
  - `on_width_settled: Callable[[str, int], None]`（layout_id・確定した幅）
  - キーボードUIは config.json を直接読まない・書かない
- **開くとき**: 今のレイアウトの記録の幅があれば `max(記録の幅, 最小の幅)` から比率で大きさを決める（記録の幅は書き換えない）。無ければ最小（task_03）。`minsize` は最小。キーが無いレイアウトは今どおり 510 × 210（記録を読まない）
- **レイアウトの切替**（task_03 の「目標の幅を決める 1 か所」）: 目標の幅 = 新しいレイアウトの記録の幅、無ければ最小の幅。`max(目標, 最小)` から比率で決める（`layout_id`・比率・最小のいずれかが変わったときだけ・task_03 の条件のまま）
- **書き込み**: `_settle_size` で、利用者の操作による大きさの変化の補正が確定したとき（補正を当てたならその目標の幅、当てなかったなら今の幅）、その幅が `get_saved_width(layout_id)` と違えば `on_width_settled(layout_id, 幅)` を呼ぶ。
  - 呼ばない場合: キーが無いレイアウト / 最大化中・最小化中（`_settle_size` が抜ける経路）/ 自分が当てた大きさ（開く・切替・比率の当て直し・`_apply_pending_ratio`・`_applied_size` で受け入れた Configure）/ 通常へ戻った後の基準の取り直し
  - コールバックの例外はキーボードUIの動作を止めない（既存の `is_mouse_button_down` の扱いにならう）

### `keyseq/presentation/controllers/layout_controller.py`（`KeyboardWindow(` の生成・`:60` 付近）

- `get_saved_width` = `parse_keyboard_window_widths(self._app._startup_settings.get(KEYBOARD_WINDOW_WIDTHS_KEY)).get(layout_id)`
- `on_width_settled(layout_id, width)` = 今の記録（`parse_keyboard_window_widths` で読んだ有効な値すべて・登録されていない id も残す）に `layout_id: width` を足し / 置き換えて `self._app.startup_io.write_startup({KEYBOARD_WINDOW_WIDTHS_KEY: 辞書})`
  （`write_startup` が `_startup_settings` を更新することを確認する。しないなら簡易表示の `compact_window_controller._save_size` と同じ扱いにそろえる）

### tests

- tests: `parse_keyboard_window_widths`（dict でない・bool・0・負・非 int・非文字列キーを捨てる・有効値を残す）
- tests_ui（既存のキーボードUIのテストの流儀・`write_startup` は差し替えて実 `config/` に書かない）:
  - 記録が無ければ最小で開く / 記録の幅で開く（最小未満の記録は最小で開き記録は変えない）
  - 利用者の大きさの変化の補正が確定すると `on_width_settled` が 1 回呼ばれ、`write_startup` に `{"keyboard_window_widths": {...}}` が渡る（他の id の値が残る）
  - 開く・レイアウトの切替・比率の当て直しでは呼ばれない / 最大化中は呼ばれない
  - 内蔵の US TKL と見本（`us_tkl_sample`）に別の幅を記録し、開いたまま切り替えるとそれぞれの幅になる（暫定 52 §9-6a）

### 設計メモ / 制約

- config.json の書き手を増やさない（`StartupIo.write_startup` 経由のみ・`handoff.md`「config.json の書き手は 2 本」）
- 縦横比の補正（phase 55）と task_03 の規則は変えない。記録の幅は「目標の幅」の入力として使うだけ
- 位置は記録しない（§2-8）

## 読むファイル

- `keyseq/presentation/keyboard_window.py`（編集対象・`:69-141`・`:228-356`）
- `keyseq/presentation/keyboard_window_size.py`（編集対象・全体）
- `keyseq/presentation/controllers/layout_controller.py:40-90`（編集対象）
- `keyseq/presentation/compact_window_size.py`・`controllers/compact_window_controller.py:70-130`（手本）
- `keyseq/presentation/controllers/config_io/startup_io.py:40-80`（`write_startup`）
- `tests_ui/test_app_ui_flows.py` のキーボードUIの大きさのテスト（task_03 で追加した箇所の周辺）
- `instructions/history/52_keyboard_ui_key_labels.md` §2・§5・§8

## 含まない

- 位置の記録
- 正本（`features.md` §4.6・`data_schema.md` §5.4）の更新（task_06）

## 確認

- compileall clean
- 追加した tests / tests_ui の単体 pass
- tests 全体 / tests_ui 全体（同時に 1 本だけ）/ smoke pass・件数が減らない
- 実行後に実 `config/config.json` が生成・変更されていない

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_06 でまとめて実施
