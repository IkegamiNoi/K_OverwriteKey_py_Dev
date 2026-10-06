# task_04_compact_window

## 目的

暫定 33 §2-9〜§2-11・§7.2・§7.3 の実装: 省略表示のウィンドウの幅・高さを `config.json` の `compact_window_size` に記録して省略表示へ入るたびに当て、
省略表示中はウィンドウに最小の高さを設け、ステータス欄を 2 行・ステータスバーを 1 行に固定する。
**presentation 限定・domain / application 不変。`config.json` にキー `compact_window_size` を追加（後方互換）。フル表示の幅の保存・最小サイズは不変。**

## 対象範囲（presentation 限定）

### 新規 `keyseq/presentation/compact_window_size.py`（tkinter 非依存の純関数）

- `COMPACT_WINDOW_SIZE_KEY = "compact_window_size"`
- `parse_compact_window_size(raw) -> tuple[int | None, int | None]`: §7.2。dict でなければ (None, None)。`width` / `height` は値ごとに bool を除く int・1 以上のときだけ採用
- `compact_geometry(saved_w, saved_h, current_h, minimum_h, screen_w, screen_h) -> tuple[int, int]`: 省略表示へ入るときの大きさ。
  幅 = 保存値（無ければ 270）を主モニタの幅で切り詰め / 高さ = 保存値（無ければ max(360, current_h)）を主モニタの高さで切り詰め、**最後に最小の高さへ引き上げる（最小を優先・はみ出しは受容）**
- 単体テスト（新規 `tests/test_compact_window_size.py`）: parse の正常・不正の組み合わせ / geometry の保存値あり・なし・画面より大きい・最小が画面より大きい

### 新規 `keyseq/presentation/controllers/compact_window_controller.py` — `CompactWindowController`

- `App` が持つ（`app.compact_window`）。省略表示のウィンドウの大きさ・最小の高さの唯一の受け持ち
- **適用**（`show_compact_view` から）: 最小の高さを測り（§7.3）、`compact_geometry` の大きさで `geometry` を当て、`minsize(1, 最小の高さ)` を設定する。当てた大きさは「アプリが決めた大きさ」として覚える（保存しない）
  - 今の `app._apply_compact_geometry`（幅 270・高さ max(360, 今の高さ)）はこれに置き換える。`release_window_min_size()` の後に呼ぶ順は保つ
- **最小の高さ**（§2-10・§7.3）: 上部（`compact_view.header_area`）・ステータス欄・ステータスバー・トリガー欄の枠の余白と見出し・トリガー一覧の最小 3 行・シーケンス欄と呼び出し先の枠の見出しが入る高さ。
  **開閉で変えない**。測る契機 = 省略表示へ入ったとき / 省略表示中のフォント変更（`app.py:346` 付近の `on_font_changed` の並びに加える）。そのとき窓が最小より低ければ最小まで伸ばす（アプリが決めた大きさ・保存しない）
- **保存**（§7.2）: 省略表示中に `<Configure>`（`event.widget is app`）で幅または高さが変わったら 500ms の予約をし直し、予約時に次をすべて満たせば今の幅・高さを `write_startup({"compact_window_size": {"width":…, "height":…}})`:
  省略表示中 / `wm_state() == "normal"` / アプリが決めた大きさと違う / 保存済みと違う。手本 = `controllers/pane_layout/pane_layout_controller.py:228-260`（`_on_window_configure`・`_save_window_width`・`cancel_window_width_save`）
  - フル表示へ戻るとき・破棄時は予約を取り消す
  - フル表示の幅の保存（`_save_window_width` は省略表示中は書かない）は変えない
- フル表示へ戻るときの最小サイズは今の `pane_layout.on_full_view_shown()` に任せる（変えない）

### ステータスの行数の固定（§2-11）

- 省略表示中は、ステータス欄の文言（`trigger_panel_controller.update_status` の省略表示の分岐 :410-416）の**各部分の改行を空白へ置き換えて**常に 2 行にする（1 行目 = フック / キーマップ、2 行目 = 選択 / 次）
- ステータスバー（`ui_vars.file_status_var`・`flash_message_var`）は省略表示中は改行を空白へ置き換えて 1 行で出す。フル表示へ戻ったら元の文言（改行あり）で出す。
  実装は表示用の文言を省略表示のときだけ整える形にし、メッセージの元の文言は保つ（`app._set_flash_message`・`_update_file_status` の周辺。表示切替時にも当て直す）
- フル表示の表示は変えない

### 配線

- `app.py`: `CompactWindowController` の生成・`show_compact_view` / `show_full_view` / フォント変更からの呼び出し・`<Configure>` の束縛（`add="+"`）

### テスト（新規 `tests_ui/test_compact_window.py`・実 `config/` を汚さない手法は既存の `tests_ui/test_compact_sequence_view.py` に合わせる）

1. 保存値なしで省略表示へ入ると幅 270・高さは今の高さ（最低 360）。保存値ありならその大きさで入る（フル ⇔ 省略を往復しても）
2. 省略表示中に大きさを変えて 500ms 後に `compact_window_size` が 1 回書かれる。最大化中・フル表示中・入った直後の自動の大きさ・同じ値では書かれない
3. 省略表示の `minsize` の高さが最小の高さで、最小まで縮めた状態で上部・ステータス欄・ステータスバー・2 つの見出しが見えている（`winfo_ismapped` と y 座標がウィンドウ内）。欄の開閉で `minsize` が変わらない
4. フル表示へ戻ると今の最小サイズ（フル表示の規則）に戻る
5. 改行を含む値の行を次に実行にしたとき・改行を含むフラッシュメッセージを出したとき、省略表示中のステータス欄は 2 行・ステータスバーは 1 行。フル表示では元の改行のまま

## 読むファイル

- `instructions/history/33_compact_sequence_view.md` §2-9〜11・§7.2・§7.3
- `keyseq/presentation/app.py:100-120, 200-250, 295-350, 400-460`
- `keyseq/presentation/controllers/pane_layout/pane_layout_controller.py:130-160, 225-262`
- `keyseq/presentation/views/status_bar.py`（全体）・`views/compact_view/compact_view.py`（全体）
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:400-445`
- `keyseq/presentation/controllers/compact_pane_layout.py`（見出しの高さ・最小の取り方）
- `tests_ui/test_compact_sequence_view.py`（冒頭の App の作り方・config の隔離）

## 含まない

- 省略表示の幅の最小・既定の幅 270 の変更・フル表示の高さ / 位置の保存（暫定 33 §11）
- 3 段の高さの規則（task_03）/ 正本反映（task_06）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` clean
- `tests/test_compact_window_size.py`・`tests_ui/test_compact_window.py` pass
- tests・tests_ui 全体・`-m tests.smoke_app` pass。実 `config/` を汚さない

## 完了条件

- 上記確認 pass・**reviewer 採用**（重点: フル表示の幅の保存・最小サイズが不変か・自動の大きさを保存しないか・予約の取り消し）
- 実機目視: なし（task_05 でまとめて実施）
