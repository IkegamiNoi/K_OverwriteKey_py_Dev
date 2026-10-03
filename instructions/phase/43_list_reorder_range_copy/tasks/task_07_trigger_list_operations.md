# task_07_trigger_list_operations

## 目的

フル表示のトリガー一覧に、範囲選択・ドラッグ移動・範囲削除・Ctrl+C / Ctrl+V（末尾へ貼り付け・ラベルの連番）を加える
（暫定 30 v0.7 §3.1〜3.5・§5.1〜5.3・§7・§8・§10-1/2/4/7/9a）。操作ごとに task_05a の「有効な行の交代」（進行中の実行があれば拒否・交代したキーの状態を消す）を
適用し、操作の後は現行の追加・削除と同じく、重なりの表の作り直し・フックの再登録・キーボード表示の再描画を行う（§5.2 末行）。
**presentation 限定（trigger_panel・full_view の trigger_box・list_clipboard）。application / domain 不変・スキーマ不変。**
複製ボタンは付けない（§3.4 は出力シーケンスのみ）。省略表示のトリガー一覧は単一選択のまま（§3.1 末行）。

## 対象範囲（presentation 限定）

### `keyseq/presentation/list_clipboard.py`

- 種類の定数 `CLIP_TRIGGERS = "trigger_rows"`（`"triggers"` は presentation の静的検査で禁止） を足す（`CLIP_ACTIONS` と並べる。値の文字列は保管庫の種類の区別だけに使う）

### `keyseq/presentation/controllers/trigger_panel/trigger_list_edit.py`（新規・処理の本体）

`action_edit.py` に倣い、トリガー一覧の範囲操作をここへ集める（`trigger_panel_controller.py`〔677 行〕へは委譲の数行だけを足す）。

- **対象の範囲**: フル表示の `trigger_list` の `listbox_range_drag.selected_range`。無ければ選択中のトリガー（`selected_trigger_index`）の 1 行
- **移動**（`move_trigger_range(start, end, target_start) -> bool`。`bind_listbox_range_drag` の `on_move`）:
  `after = move_block(triggers, start, end, target_start)` を作り、`apply_effective_row_transition(app, triggers, after, apply)`（`apply` = `triggers[:] = after`）。
  拒否なら `False`（部品が表示を戻す。理由は交代の口が一時メッセージに出す）。並びが変わらなければ何もしない（未保存にしない）。
  成功したら後処理（下記）・動かした範囲を選択・`True`
- **範囲削除**（`delete_trigger` の範囲版）: 範囲が 2 行以上なら「トリガー n 件を削除しますか？」で 1 回確認（1 行なら現行の文言のまま）。
  `after` = 範囲を除いた一覧で交代の口を通す。成功したら後処理。削除後の選択は現行の単一削除と同じ扱い（位置の補正）
- **Ctrl+C**（`copy_triggers`）: 範囲の行を `CLIP_TRIGGERS` で保管庫へ写す。`"break"` を返す
- **Ctrl+V**（`paste_triggers`）: 保管庫の `CLIP_TRIGGERS` の写しを末尾へ足す。各行は
  - 内部の値（キー名が `_` で始まるもの = 読込元のパス・参照元・未保存の印・取り込みの印など）を除く（§5.3。保存時に新しいファイルになる）
  - ラベルは `numbered_labels(貼るラベル, 貼り先の一覧の既存ラベル)`（§7。先に貼った行も含めて判定）
  - `after = triggers + 新しい行` で交代の口を通す（末尾に足すので既存キーの有効な行は変わらないが、口を通して扱いを揃える）
  - 成功したら後処理・各新しい行を `mark_sequence_dirty`（現行の追加と同じ）・貼った範囲を選択して見える位置へ。`"break"` を返す
  - 保管庫が空・種類違いなら何もしない。キーが停止 / トグル / 切替キーや置換元と重なっても受け入れる（§5.2。グレー表示は再描画で付く）
- **後処理**（移動・範囲削除・貼り付けで共通の 1 関数）: `refresh_triggers(select=範囲)` → `refresh_actions()` → `dirty_tracker.mark_trigger_set_dirty()` →
  フック稼働中なら `hook.start_hook()`（現行の `delete_trigger`〔`trigger_panel_controller.py:577-596`〕と同じ順）。
  実行中の状態はキー単位なので、交代・消えたキー以外は保つ（交代の口が消す）

### `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`

- `refresh_triggers(self, select: tuple[int, int] | None = None)`: 現行の処理の後、`select` があればフル表示の `trigger_list` に `select_range`（下線 = 範囲の末尾の行）を当て、
  `_selected_trigger_idx` をその下線の行にする（省略表示は単一選択のまま）。`select` が無ければ現行どおり（**トリガーの実行による選択〔`select_trigger_by_key`〕は単一選択に戻す** = §3.1）
- **選択中のトリガー = 下線の行**（シーケンス欄・トリガー変更・suppress 等はこの行を対象にする）。範囲は移動・削除・コピーの対象にだけ使う
- `delete_trigger` は範囲があるとき `trigger_list_edit` の範囲削除へ委譲。`copy_triggers` / `paste_triggers` / `on_trigger_list_move` の委譲を足す

### `keyseq/presentation/views/full_view/trigger_box.py`

- `trigger_list` を出力シーケンス欄（`sequence_box.py:19-30`）と同じく `bind_listbox_range_drag(on_move=on_trigger_list_move, on_commit=on_trigger_list_mouse_release)` で接続する
  （現行の `bind_listbox_click_selection_sync` は置き換え。押している間は帯だけ・離したときに反映〔phase 42〕は部品が担う）
- `<Control-c>` / `<Control-C>` / `<Control-v>` / `<Control-V>` を `trigger_list` にだけバインド（`bind_all` 不使用）
- 省略表示（`views/compact_view/trigger_box.py`）は変えない

### テスト（追加・修正まで）

- 新規 `tests_ui/test_trigger_list_operations.py`（`tests_ui/test_sequence_copy_paste.py`・`test_sequence_list_operations.py` の作り方に倣う）:
  - ドラッグ移動で並びが変わり、動かした範囲が選択・未保存・後処理（重なりの表の作り直し・フック再登録）が呼ばれる / 並びが変わらなければ未保存にしない
  - 同じキーの 2 行の並べ替えで有効な行が入れ替わると、そのキーの実行位置・周回が消える / 交代するキーに進行中の実行（`sequence_runner.has_active_execution` を True に）があれば移動しない・一時メッセージ
  - 範囲削除: 件数つきの確認 1 回・範囲全体が消える・交代の扱い（下の行が残るキーは状態が消える / 進行中なら削除しない）
  - Ctrl+C → Ctrl+V: 末尾へ写しが付き選択される・内部の値（`_` 始まり）が写らない・ラベルの連番（`a` → `a (2)`・`a (2)` → `a (3)`・空ラベルは空・先に貼った行を含めて判定）・
    新しい行が未保存・コピー後に元を編集しても貼る内容は変わらない・種類違い（`CLIP_ACTIONS` の保管庫）では何もしない・ハンドラが `"break"`
  - 貼ったトリガーのキーが既存のキーと同じとき、下の行がグレー（「上のトリガーと重複」）になる
  - 編集の再描画で範囲が保たれる / `select_trigger_by_key`（実行）では単一選択に戻る / 省略表示の一覧は単一選択のまま
- 既存の trigger_box のクリック同期を前提にしたテストがあれば、範囲ドラッグ部品の接続に追随させる

### 設計メモ / 制約

- 移動・削除の可否と状態の破棄は `apply_effective_row_transition` の 1 か所を通す（独自に判定しない）
- `trigger_list_edit.py` は 300 行・関数 30 行の目安
- 保存の識別子（task_06）は一覧の並びから数えるため、並べ替え後の保存に追加の対応は不要

## 読むファイル

- 暫定仕様 `instructions/history/30_list_reorder_range_copy.md` §3・§5.1〜5.3・§7
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:46-200`・`:577-600`・`:615-640`
- `keyseq/presentation/controllers/trigger_panel/action_edit.py:116-180`・`:290-345`（範囲・コピー / 貼り付け・移動の手本）
- `keyseq/presentation/controllers/trigger_panel/effective_row_transition.py`（全体）
- `keyseq/presentation/listbox_range_drag.py:1-90`（公開面）・`keyseq/presentation/list_clipboard.py`（全体）・`keyseq/domain/list_editing.py:1-80`
- `keyseq/presentation/views/full_view/trigger_box.py`・`views/full_view/sequence_box.py:15-35`
- 手本のテスト: `tests_ui/test_sequence_copy_paste.py`・`tests_ui/test_trigger_effective_row_transition.py`

## 含まない

- キーマップ一覧の操作（task_08）/ 正本反映（task_09）
- 省略表示のトリガー一覧の範囲選択・移動・複製（§11 対象外）/ トリガーの複製ボタン
- 貼り付け位置の指定（常に末尾）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests_ui.test_trigger_list_operations tests_ui.test_trigger_effective_row_transition tests_ui.test_sequence_copy_paste` が全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: トリガー一覧の Shift 範囲選択・ドラッグ移動（Escape で取り消し）・範囲削除・Ctrl+C → Ctrl+V（同じキーマップ / 別のキーマップ・ラベルの連番・下の行のグレー）・
  並べ替え後もキー入力で有効な行が動く・省略表示は従来どおり。
