# task_02_listbox_range_drag

## 目的

一覧の連続範囲選択とドラッグ移動を受け持つ presentation の共通部品を作り、まずプリセット編集ダイアログの一覧へ適用する
（暫定 30 §3.1・§3.2・§3.3・§3.5〔プリセット分〕・§6a・§8）。
**presentation 限定（新規モジュール + `dialogs/preset_manager.py`）。domain は task_01 の関数を使うだけ・application 不変・スキーマ不変。
フル表示の 3 つの一覧（キーマップ・トリガー・出力シーケンス）と省略表示には、このタスクでは適用しない。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/listbox_range_drag.py`（新規）

`bind_listbox_range_drag(listbox, *, on_move, on_commit=None, can_start_drag=None) -> ListboxRangeDrag` と、それが返す制御オブジェクト。

- 引数
  - `on_move(start: int, end: int, target_start: int) -> bool`: ドラッグを離したときに呼ぶ。呼び出し側がデータを並べ替えて再描画し、True を返す。拒否なら False（理由の表示は呼び出し側）
  - `on_commit(listbox) -> None`: マウスでの選択（クリック・Shift+クリック・Shift+ドラッグ）を離したとき、および Shift+↑↓ の後に `after_idle` で呼ぶ（phase 42 の `bind_listbox_click_selection_sync` の callback と同じ趣旨。ドラッグ移動・取り消しの後は呼ばない）
  - `can_start_drag() -> bool`: ドラッグ開始の可否（False なら移動しない。理由の表示は呼び出し側）。省略時は常に可
- 選択（§3.1）: Listbox 自体へのバインドで扱い、**`return "break"` で Tk のクラスバインドを通さない**。`selectmode` は変えない（browse のまま。範囲は `selection_set(a, b)` で付ける）
  - 押す（修飾なし・Ctrl 付きも同じ）: 押した行が選択範囲の外なら、その行の単一選択・アンカー・下線（`activate`）にする。範囲の中なら範囲を保つ（動かさずに離したらその行の単一選択にする）
  - Shift+押す / Shift+押したまま動かす: アンカーからポインタの行までを選択・下線はポインタの行
  - Shift+↑ / Shift+↓: 下線を 1 行動かし、アンカーから下線までを選択・`see`。端では動かさない
  - Shift なしの ↑↓ は Tk の既定（単一選択）に任せる（アンカーをその行へ更新する）
  - Ctrl+/・Ctrl+\・Shift+Ctrl+Home/End・Shift+Home/End は何もしない（`break`）
- ドラッグ移動（§3.2）
  - Shift なしで押したまま、ポインタが別の行に入ったらドラッグ開始（`can_start_drag` を確認）。動かす塊 = 押した行を含む選択範囲（押した時点で単一選択に切り替えた場合はその 1 行）
  - 開始時に各行の表示（文字列と `itemcget` で取れる `background` / `foreground` / `selectbackground` / `selectforeground`）を控え、ポインタが行をまたぐたびに `domain.list_editing.move_block` の並びで一覧の表示だけを描き直す（データは触らない）。塊の行を選択表示にする
  - ポインタが一覧の上端 / 下端の外にある間は、一定間隔（`after`）で 1 行ずつ自動スクロールし、移動先を更新する
  - 離したとき: 控えた表示へ戻してから、並びが変わっていれば `on_move(start, end, target_start)` を呼ぶ。False なら選択を元の範囲へ戻す。並びが変わらなければ何もしない
  - **Escape（ドラッグ中のみ）**: 控えた表示と元の選択へ戻してドラッグを取り消し、その後のボタンの解放では何もしない。`break` してダイアログ等の Escape へ伝えない。ドラッグ中でなければ Escape は素通し（`break` しない）
  - `<B1-Leave>` / `<B1-Enter>`（Tk の自動スキャン）は通さない
- 押下中の印: 押している間は `listbox_utils.listbox_mouse_button_is_down(listbox)` が True を返すこと（後続タスクで既存の一覧ハンドラが押下中の `<<ListboxSelect>>` を無視しているため）。
  `listbox_utils.py` に印を立てる / 下ろすための最小の公開関数を足すか、同じ属性を共有する（どちらでもよい。`bind_listbox_click_selection_sync` の振る舞いは変えない）
- 範囲の補助: `selected_range(listbox) -> tuple[int, int] | None`（選択の最小・最大）/ `select_range(listbox, start, end, *, active=None)`（選択・アンカー・下線・`see`）を公開する

### `keyseq/presentation/dialogs/preset_manager.py`（§6a）

- 一覧に `bind_listbox_range_drag` を付ける。`on_move` は `self._temp` を `move_block` で並べ替えて `_refresh` し、動かした行を選択範囲にして True
- 「上へ / 下へ」（`move`）: 選択範囲を `shift_block` でまとめて動かし、動かした範囲を選択する。選択なしの案内・端で何もしないは現行どおり
- 「削除」（`delete`）: 選択範囲をまとめて削除。確認文は 1 件なら現行の文言、複数なら件数を示す（例「選択した 3 件のプリセットを削除しますか？」）
- 「編集」（`edit`）・ダブルクリック: 対象は下線の行（範囲選択中でも 1 行）。範囲が無いときは現行どおり
- 作業用の一覧 `_temp` に反映し OK で確定・キャンセルで破棄（現行どおり）。複製・Ctrl+C / V は付けない
- ダイアログの Escape（閉じる）はドラッグ中でなければ現行どおり

### テスト（`tests_ui/`。追加・修正まで）

- `tests_ui/test_listbox_range_drag.py`（新規）: 素の `tk.Listbox` に部品を付け、`event_generate`（`tests_ui/test_listbox_click_selection_sync.py` の流儀）で
  - Shift+クリック・Shift+ドラッグ・Shift+↑↓ の範囲選択 / Ctrl+クリックで飛び飛びにならない / 範囲の中を押して動かさず離すと単一選択 / `on_commit` が離したとき・Shift+↑↓ の後に呼ばれ、ドラッグ移動の後は呼ばれない
  - 1 行・範囲のドラッグで `on_move` が正しい `(start, end, target_start)` で呼ばれる / 並びが変わらなければ呼ばれない / 途中の表示が並べ替わり、離す前にデータ（呼び出し側の list）は変わらない
  - Escape で取り消し（表示と選択が戻り、解放で `on_move` が呼ばれない・Escape がトップレベルのバインドへ伝わらない）/ ドラッグ中でない Escape は伝わる
  - `can_start_drag` が False ならドラッグしない / 押下中は `listbox_mouse_button_is_down` が True
- プリセット編集ダイアログ: 範囲のドラッグ・上へ / 下へのまとめて移動・範囲削除・OK で確定 / キャンセルで破棄・ドラッグ中の Escape でダイアログが閉じない
  （既存の PresetManagerDialog を作るテスト〔`tests_ui/test_app_ui_flows.py` 等〕の作り方に倣う。新規ファイル `tests_ui/test_preset_manager_range_drag.py` でよい）

### 設計メモ / 制約

- 新規モジュールは 300 行・関数 30 行の目安（`.claude/rules/implementation.md`）。超えるなら同じフォルダ内でクラスと補助関数に分ける
- 一覧の文字列や色は呼び出し側が再描画で付け直す前提（部品はドラッグ中の一時表示だけを扱い、確定後は `on_move` 側の再描画に任せる）
- `bind_all` を使わない（§8）。バインドは対象の Listbox だけ

## 読むファイル

- 暫定仕様 `instructions/history/30_list_reorder_range_copy.md` の §3.1〜§3.3・§3.5・§6a・§8
- `keyseq/presentation/listbox_utils.py`（全体）
- `keyseq/presentation/dialogs/preset_manager.py:63-370`（編集対象）
- `keyseq/domain/list_editing.py`（task_01 の `move_block` / `shift_block`）
- `tests_ui/test_listbox_click_selection_sync.py:1-100`（イベントの作り方）
- PresetManagerDialog を作る既存テストの 1 例（`grep -n PresetManagerDialog tests_ui/test_app_ui_flows.py` で該当箇所のみ）

## 含まない

- 出力シーケンスへの適用・`▶`・範囲削除のループ対（task_03）/ Ctrl+C / V・複製（task_04・task_07・task_08）
- トリガー一覧への適用（task_07）/ キーマップ一覧への適用と並べ替えの禁止条件（task_08）
- 省略表示のトリガー一覧（スコープ外・変えない）/ phase 42 の `bind_listbox_click_selection_sync` の変更

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_listbox_range_drag tests_ui.test_preset_manager_range_drag` が全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` が全 pass（tests 1059・tests_ui 645 から追加分だけ増える）・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: プリセット編集で Shift+クリック / Shift+ドラッグ / Shift+↑↓ の範囲選択・1 行と範囲のドラッグ移動（自動スクロール含む）・Escape の取り消し（ダイアログが閉じない）・上へ / 下へのまとめて移動・範囲削除。
