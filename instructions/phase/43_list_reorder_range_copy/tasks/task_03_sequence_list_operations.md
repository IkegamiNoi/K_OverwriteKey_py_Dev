# task_03_sequence_list_operations

## 目的

出力シーケンス欄に、次に実行の印 `▶`（選択と分離）・範囲選択・ドラッグ移動・上へ / 下へのまとめて移動・範囲削除を加える
（暫定 30 §3.1・§3.2・§3.3・§3.5・§4.1・§4.2）。
**presentation 限定（task_01 の domain 関数と task_02 の部品を使う）。domain / application 不変・スキーマ不変。トリガー一覧・キーマップ一覧・省略表示は変えない。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/listbox_range_drag.py`（小変更）

- 直近の `on_commit` が範囲を伸ばす操作（Shift+クリック / Shift+ドラッグ / Shift+↑↓）によるものかを、呼び出し側が判別できるようにする
  （例: 読み取り専用の属性 `last_commit_extended: bool`。Shift なしのクリック・範囲の中を押して離した単一選択では False）。他の振る舞いは変えない

### `keyseq/presentation/views/full_view/sequence_box.py`

- `action_list` の `bind_listbox_click_selection_sync(...)` を `bind_listbox_range_drag(..., on_move=..., on_commit=...)` に置き換える（ハンドラは trigger_panel 側）。
  `<<ListboxSelect>>`・`<KeyRelease>`・`<Double-Button-1>` のバインドは残す
- ボタンの並びは変えない（複製ボタンは task_04）

### `keyseq/presentation/controllers/trigger_panel/`（`trigger_panel_controller.py`・`action_edit.py`）

- **`▶`（§4.1）**: `refresh_actions` で各行の先頭に、次に実行の行なら `"▶ "`、それ以外は同じくらいの幅の空白を付ける（例 `"　 "`）。`build_action_rows` の戻り値（文字列・背景色）は変えず、前置きは refresh 側で付ける
  （連続実行の終端 = 次回は先頭、の場合は現行の `select_next_action_row` と同じく先頭の行に `▶`）
- **選択と次に実行の分離**:
  - `refresh_actions` に、再描画後の選択範囲を指定できる引数を足す（例 `select: tuple[int, int] | None = None`）。指定があればその範囲を選択（下線は範囲の末尾）、無ければ現行どおり次に実行の 1 行を選択する
    （トリガーの実行・トリガーの切替などの既存の呼び出しは引数なし = 現行どおり）
  - 次に実行を変えるのは **Shift なしのクリック**（部品の `on_commit` で `last_commit_extended` が False のとき → 現行の `on_action_list_select(prefer_selection=True)`）と
    **Shift なしの ↑↓**（Tk 既定の `<<ListboxSelect>>` → 現行どおり）だけ。`last_commit_extended` が True の commit では次に実行を変えない
  - `<KeyRelease>`（`on_action_list_focus_index_change`）は、Shift を押していない ↑ / ↓ / PageUp / PageDown / Home / End のときだけ現行の同期を行い、それ以外（Shift 付き・Shift キー自体の解放など）では何もしない（範囲を 1 行に潰さないため）
- **ドラッグ移動（§3.2・§4.2）**: `on_move(start, end, target_start)` で
  `can_move_block` が False なら移動せず、ステータスバーの一時メッセージ（`App._set_flash_message`）に「ループの始まりと終わりの組が変わるため移動できません」を出して False。
  可なら `move_block` で並べ替えた結果を `actions` へ反映（list の中身を差し替える）、次に実行を `index_after_reorder` で同じアクションへ付け直し、現行の移動と同じく `reset_loop_frames`・未保存化、
  `refresh_actions(select=動かした範囲)` で True
- **上へ / 下へ（§3.3）**: `move_action(delta)` を、選択範囲（選択が 1 行・範囲なしなら現行どおりの対象行）を `shift_block` でまとめて動かす形にする。判定・反映はドラッグと同じ（`can_move` の代わりに `can_move_block`）。
  **次に実行は動かした行へ移さない**（現行は移動先へ移していた。§4.1 で「同じアクションを指す」に変わる）
- **範囲削除（§3.5）**: `delete_action` で、範囲選択中は範囲の各行に `delete_indices`（ループの対）を適用した和集合を削除する。確認は 1 回:
  1 行（対を含まない）・ループ 1 組だけは現行の文言、それ以外は件数を示す（例「選択した 3 行を削除しますか？」、範囲外の対を巻き込む場合は「ループの始まりと終わりは対で削除します（中の行は残ります）。」を添える）。
  削除後、次に実行の行が残っていれば `index_after_reorder` 相当で同じアクションへ付け直し、消えた場合は現行どおり（位置の数値のまま補正）
- **編集**（`edit_action`）: 対象は現行どおり `selected_action_index`（フォーカスがあれば下線の行）。編集後の選択はその 1 行

### テスト（`tests_ui/`。追加・修正まで）

- 新規 `tests_ui/test_sequence_list_operations.py`: `▶` が次に実行の行に付く / 範囲選択・ドラッグ・上へ / 下へ・範囲削除で次に実行が同じアクションを指したまま /
  Shift なしのクリック・↑↓ で次に実行が変わり、Shift+クリック・Shift+↑↓ では変わらない（範囲も潰れない）/ ループの組が変わるドラッグ・上へ / 下へは移動せず一時メッセージ /
  ループを丸ごと別のループへ動かせる / 範囲削除の確認文（1 行・対・複数）と未保存化
- 既存テストの追随（意図は変えない）: `▶` の前置きで行の文字列を比べているもの（`tests_ui/test_action_list_rendering.py` 等）、
  シーケンス欄のクリック同期（`tests_ui/test_listbox_click_selection_sync.py` のシーケンス一覧の分）、上へ / 下へで次に実行が移動先へ移ることを前提にしたもの（`tests_ui/test_trigger_panel_controller_action_edit.py` 等）。
  **追随で期待値を変えたテストは、変えた理由（§4.1 等）を完了報告に列挙する**

### 設計メモ / 制約

- `trigger_panel_controller.py` が大きいため、新しい処理は `action_edit.py`（`ActionEditFlow`）側へ置き、controller は委譲だけにする
- 関数 30 行の目安。表示文言は presentation に置く（domain の理由定数は task_04 で使う）

## 読むファイル

- 暫定仕様 §3.1〜§3.3・§3.5・§4.1・§4.2
- `keyseq/presentation/listbox_range_drag.py`（全体）・`keyseq/domain/list_editing.py`・`keyseq/domain/sequence_editing.py:100-175`
- `keyseq/presentation/views/full_view/sequence_box.py`（全体）
- `keyseq/presentation/controllers/trigger_panel/action_edit.py`（全体）
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:185-265`（`refresh_actions` / `select_next_action_row`）・`:556-605`（move の委譲・`on_action_list_*`）
- 既存テストは追随が必要なものだけ（`grep -n "action_list\|move_action" tests_ui/*.py` で該当箇所）

## 含まない

- 複製ボタン・Ctrl+C / V（task_04）/ グレーのトリガーで `▶` を出さない・シーケンス欄のクリックで次に実行を変えない（task_05）
- トリガー一覧（task_07）・キーマップ一覧（task_08）・省略表示（スコープ外）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_sequence_list_operations` が全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: `▶` の表示 / Shift+クリック・Shift+↑↓ で範囲選択しても `▶` が動かない / ドラッグ・上へ / 下へのまとめて移動 / ループの組が変わる移動の拒否 / 範囲削除。
