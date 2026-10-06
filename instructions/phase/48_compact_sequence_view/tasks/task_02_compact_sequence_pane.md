# task_02_compact_sequence_pane

## 目的

暫定 33 §3・§4・§8（と §2-1・§2-4・§2-7）の実装: 省略表示のトリガー一覧と呼び出し先の枠の間に出力シーケンス欄を置き、フル表示と同じ内容を描き、
クリック・キー操作で次に実行を変えられるようにする。**presentation 限定・domain / application 不変・スキーマ不変。**
開閉は**メモリ上だけ・既定は閉じる**（保存・初回は開く・高さの制御は task_03）。

## 対象範囲（presentation 限定）

### 新規 `keyseq/presentation/views/compact_view/sequence_frame.py` — `CompactSequenceFrame`

- 呼び出し先の枠（`views/full_view/call_view_frame.py` の `CallViewFrame`）と同じ作り: 見出し `ttk.Label`（cursor hand2・クリックで `on_heading_click`）/ `body`（PanedWindow に入れる枠）/ 一覧 `tk.Listbox` + 縦スクロールバー
  - 見出しの文言: 閉 `▸ シーケンス` / 開 `▾ シーケンス`（`set_heading(is_open)`）
  - 一覧: `exportselection=False`・単一選択（`selectmode="browse"`）・**選択の帯は通常の色で出す**（呼び出し先の枠のように選択色を消さない）・`takefocus` は既定のまま
  - 見出しの置き場所の切替: `show_heading_in_body()`（開・本体の上端）/ `show_heading_at(parent)`（閉・トリガー一覧のペインの下端）。`CallViewFrame` の同名の作法に合わせる
  - 最小の高さを返す `minimum_body_height()`（`call_view_frame.list_minimum_height` を使う）
- 一覧のイベントの受け口はコンストラクタ引数のコールバックで受け取り、ここでは判断しない

### 新規 `keyseq/presentation/controllers/compact_sequence_controller.py` — `CompactSequenceController`

- `App` が 1 つ持つ（`app.compact_sequence`。`app.py` の `CallViewController` の生成 :208 付近と同じ場所で作る）
- **描画** `render(rows: list[tuple[str, str | None]], next_index: int | None) -> None`: 一覧を作り直し（行頭 `▶ ` / `　 `・背景色）、`next_index` があればその行を選択の帯にして `see` する。
  描画中は自分のイベント処理を抑止する（自前のフラグ）。描くたびに**描画の世代**を 1 つ進める
- **開閉**（メモリ上・既定 False）: 見出しのクリックで切り替える。
  - 開く: `trigger_panes.add(body, …)` を**呼び出し先の枠の本体より前**に入れる（呼び出し先が開いていれば `before=`）・見出しを本体へ。開いたら今の選択で描く
  - 閉じる: `trigger_panes.forget(body)`・見出しをトリガー一覧のペイン（`CompactTriggerBox.trigger_frame`）の下端へ
  - 呼び出し先の枠の開閉・既定の高さ・境界の位置の扱いは**このタスクでは変えない**（両方開いたときの高さの配分の崩れは task_03 で直す・受容）
- **クリック**（§4・§2-7）:
  - `<Button-1>`: フォーカスを一覧へ移し、押した行（`nearest(y)`・行が無ければ None）・押した時点の構成セット ID（`app._active_trigger_set_id()`）・選択中のトリガーのキー・描画の世代を覚える。**`"break"` を返して押した時点で選択を動かさない**
  - `<B1-Motion>`: `"break"`（選択を動かさない）
  - `<ButtonRelease-1>`: 離した行が押した行と同じで、構成セット ID・トリガーのキー・描画の世代がいずれも押した時点と同じなら `trigger_panel.set_next_action_index(row, refuse_running_callee=True)`。違えば何もしない。覚えた値は捨てる
  - 欄を閉じたら覚えた値を捨てる
- **キー操作**（§2-4・§4）: `Up` / `Down` / `Prior` / `Next` / `Home` / `End`（Shift 付きは何もしない・`"break"`）で、今の次に実行の行から移動先を決めて
  `set_next_action_index(row, refuse_running_callee=True)`。Prior / Next は一覧に見えている行数ぶん。端で止める。Listbox 既定の移動は `"break"` で止める
- **何もしない**: `<Double-Button-1>`・`<Control-c>` / `<Control-C>` / `<Control-v>` / `<Control-V>`・`<Delete>`（`"break"`）

### `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`

- `set_next_action_index(self, idx, *, refuse_running_callee: bool = False)`: True のときは先頭で `_refuse_running_chain_callee_edit()` を通し、拒否なら False（既定 False のときの挙動は task_01 のまま）
- `refresh_actions`: フル表示の一覧へ描いたのと同じ `rows`・次に実行の行（有効でなければ None）で `app.compact_sequence.render(...)` を呼ぶ。トリガーが無い / 選択が無い早期 return の経路では空で描く。
  省略表示の一覧には範囲の選択（`select`）を当てない
- §8 の描き直し: `set_selected_trigger_index` の省略表示の分岐でも `refresh_actions()` を呼ぶ（`call_view.on_selection_changed()` は残す）
- **ファイルは 633 行（M1 超）**。加える行は最小にし、描画の詳細は `CompactSequenceController` 側に置く

### `keyseq/presentation/controllers/hook_controller.py:206-207`・`keyseq/presentation/app.py` `show_compact_view`

- `hook_controller.py`: 省略表示中でも `refresh_actions()` を呼ぶ（`_compact_mode` の条件を外す）
- `show_compact_view`: 省略表示へ切り替えた後に `trigger_panel.refresh_actions()` を呼ぶ（今の選択で描く）

### `keyseq/presentation/views/compact_view/trigger_box.py`

- `CompactSequenceFrame` を作り、閉じた見出しをトリガー一覧のペインの下端に置く（一覧の下）。部品の参照を `app.compact_sequence` へ渡す

### テスト（新規 `tests_ui/test_compact_sequence_view.py`）

既存の `tests_ui/test_call_view_compact.py` の App の作り方・config の隔離（`tests_ui/test_keymap_set_history_flow.py:17-34` の ExitStack 手法）に合わせる。
1. 既定は閉じていて見出し `▸ シーケンス` がトリガー一覧の下にある。見出しのクリックで開き、`▾ シーケンス` と一覧が PanedWindow のトリガー一覧の次に入る。もう一度で閉じる
2. 開いた一覧の行の文字列・`▶` の位置がフル表示の一覧と同じ。トリガーを選び替える（省略表示中の `set_selected_trigger_index`）と追従する。選択の帯が次に実行の行にある
3. 押した行で離すと次に実行が変わる。別の行で離すと変わらない。押してから離すまでにトリガーの選び替え・描き直しがあると変わらない
4. ↓ / ↑ / Home / End で次に実行が動く。有効でないトリガーでは動かない。呼び出し先の実行中（`sequence_runner.is_running_chain_callee` を差し替え）はクリックでもキーでも変わらない
5. ダブルクリック・Ctrl+C では何も起きない（編集ダイアログが開かない・クリップボードへ写さない）
6. 省略表示へ切り替えた直後に今の選択で描かれている。フックの状態の変化（`hook_controller` の該当経路）で描き直される

## 読むファイル

- `instructions/history/33_compact_sequence_view.md` §2・§3・§4・§8
- `keyseq/presentation/views/full_view/call_view_frame.py`（全体・手本）・`views/compact_view/trigger_box.py`（全体）
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:60-150, 264-370, 580-627`
- `keyseq/presentation/controllers/call_view_controller.py:40-130`（ホストの登録・開閉の作法）
- `keyseq/presentation/app.py:200-245, 398-422`・`controllers/hook_controller.py:195-210`
- `tests_ui/test_call_view_compact.py`（冒頭〜最初の数テスト）・`tests_ui/test_keymap_set_history_flow.py:17-34`

## 含まない

- 開閉と高さの保存・初回は開く・3 段の高さの配置 / ドラッグ / 優先順・フォント変更での最小の測り直し（task_03）
- 省略表示のウィンドウの大きさ・最小の高さ・ステータスの行数（task_04）
- フル表示の一覧の操作・フル表示のキー操作の拒否の抜け（暫定 33 §11）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests_ui` clean
- `tests_ui/test_compact_sequence_view.py` 全件 pass・`tests_ui/test_call_view_compact.py`・`test_sequence_list_operations.py` pass
- tests・tests_ui 全体・`-m tests.smoke_app` pass。実行後に `config/config.json` の mtime が変わっていない

## 完了条件

- 上記確認 pass・**reviewer 採用**（重点: フル表示の一覧の挙動不変・2 つの一覧の選択の干渉なし・押している間の取り消し）
- 実機目視: なし（task_05 でまとめて実施）
