# task_05_call_view_full

## 目的

フル表示に**呼び出し先の表示枠**を作り、task_04 の要約を表示する。枠と出力シーケンスの一覧の間の境界線の位置を `config/config.json` に保存する（暫定 31 v0.5 §5.1〜§5.3・§6・§10-7〜§10-10）。
**presentation 限定（新規の枠・コントローラ・高さの規則 + `sequence_box.py`・`app.py` の配線）。application・JSON の構成セットは変えない。省略表示の枠は task_06。**

## 対象範囲

### 新規 `keyseq/presentation/call_view_heights.py`（純関数・tkinter 非依存）

- `CALL_VIEW_HEIGHTS_KEY = "call_view_heights"`
- `parse_call_view_heights(raw) -> dict[str, int]`: `{"full": int, "compact": int}` の**値ごと**に判定（bool を含む非 int・0 以下は捨てる。片方が不正でももう片方は使う。dict でなければ空）。`pane_width_rules.parse_saved_pane_widths` の書き方に倣う
- 既定の高さ・表示の高さの決め方（希望の高さを保ち、最小を割るなら表示だけ引き上げる）の純関数

### 新規 `keyseq/presentation/views/full_view/call_view_frame.py`（フル表示の枠・Widget のみ）

- 見出しのラベル（経路 `f1 › f5 › f7`）+ 読み取り専用の Listbox + 縦スクロールバー
- 読み取り専用: 選択・クリック・ダブルクリック・ドラッグ・Ctrl+C / V・キー操作で何もしない（`<Button-1>` 等を `"break"` で潰す・`exportselection=False`・選択色を出さない）。マウスホイールのスクロールはできる

### `keyseq/presentation/views/full_view/sequence_box.py`

- 一覧（`action_list` + スクロールバー）を、**上下に分ける境界線**（`tk.PanedWindow(orient="vertical")` 等・`minsize` が使えるもの）の上の枠に入れ、下の枠に `CallViewFrame` を入れる。**右のボタン列は今のまま一覧の右**（ボタン列の高さ = ウィンドウの最小の高さを変えない）
- 枠が閉じているときは下の枠を外す（境界線も出さない・上の一覧が全体を使う）。開くときは保存した高さで足す
- 一覧の最小 = 3 行・枠の最小 = 見出し + 3 行（`minsize`）

### 新規 `keyseq/presentation/controllers/call_view_controller.py`

- `CallViewController(app)`: runner から `CallViewSummary | None` を受けて、開閉と中身の描画を行う（**UI スレッドで呼ばれる前提**。runner の処理は UI スレッド）
  - None → 枠を閉じる / 要約 → 開いていなければ開いて、中身を描く
  - 中身: `action_list_rendering.build_action_rows(summary.actions, loop_iterations=…（summary.loop_frames から）, counters=summary.counters, resolve_call=…)` で行と背景色を作り、**`summary.position` の行に `▶`**（出力シーケンスの印と同じ書き方・他の行は同じ幅の空白）。`▶` の行が見えるようにスクロール
  - 見出し: `" › ".join(summary.path)`
  - 最後に受けた要約を持つ（task_06 の表示の切替で使う）
- 境界線のドラッグを離したとき、枠の希望の高さが変わっていれば `app.startup_io.write_startup({CALL_VIEW_HEIGHTS_KEY: {"full": 新, "compact": 今の compact の希望値}})`（片方だけ動かしても両方書く・§6）。起動時に `config.json` から読む（幅の配分の読込と同じ経路 = `pane_layout_controller.py:86` の手本）

### `keyseq/presentation/app.py`

- `CallViewController` を作り、`SequenceRunner(..., notify_call_view=self.call_view.on_summary)` で配線する（既存の `update_status` と同じ並び）

### キーマップの並べ替え・削除での表示の残り（task_04 の reviewer 指摘 2）

- `AppState.forget_trigger_set` / `rekey_trigger_set` が runner を通らずに保留中のステップを消す経路（キーマップの削除・並べ替え）で、枠に古い文脈が残らないことを確かめる。残るなら、その操作の後に runner の再通知（task_04 の `_publish_call_view` を公開の口として呼ぶ）を足す

### テスト（追加・修正まで）

- 新規 `tests/test_call_view_heights.py`: 値ごとの判定（bool・0 以下・非 int・片方だけ不正・dict でない）・既定・最小の引き上げ
- 新規 `tests_ui/test_call_view_frame.py`:
  - 要約を渡すと枠が開き、見出しが `f1 › f5`・`▶` が位置の行・行の表示名とループの色が出力シーケンスと同じ
  - None で閉じる（下の枠が外れる）・開いていないときに None を受けても何もしない
  - 読み取り専用: クリック・ダブルクリック・Ctrl+C で実行位置・保管庫・選択が変わらない
  - 境界線を動かして離すと `config.json` へ `{"full": …, "compact": …}` が書かれる / 再び開くと保存した高さ / 不正な保存値なら既定
  - **フル表示のウィンドウの最小の高さと、横の 3 枠の幅の配分が変わらない**（枠を開く前後で `minsize` と各枠の幅が同じ）
- 既存の出力シーケンス欄のテスト（`grep -rln "action_list" tests_ui`）が通る

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §5・§6
- `keyseq/presentation/views/full_view/sequence_box.py`（全体）
- `keyseq/application/call_view.py`（`CallViewSummary`）
- `keyseq/presentation/controllers/action_list_rendering.py`（全体）・出力シーケンスの `▶` の付け方（`trigger_panel_controller.py` の `refresh_actions`）
- `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py:80-100`・`:215-235`・`keyseq/presentation/pane_width_rules.py`（保存の手本）
- `keyseq/presentation/app.py:200-230`
- `keyseq/application/app_state.py:115-145`（forget / rekey）

## 含まない

- 省略表示の枠（task_06）/ 正本反映（task_07）/ 経路のクリック・手動の開閉・横スクロール

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass（tests_ui は verifier 1 つで）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: ①ステップの呼び出しを単発で押すと出力シーケンスの一覧の下に枠が開き、写し・`▶`・経路が出て、押すたびに `▶` が進み、終わると閉じる ②連続実行で呼び出し先の停止の行で一時停止すると開き、再開すると処理中も `▶` が追従する ③境界線を動かすと、次に開いたとき・再起動後もその高さ ④枠をクリックしても何も起きない ⑤一括の呼び出しが流れるだけでは開かない。
