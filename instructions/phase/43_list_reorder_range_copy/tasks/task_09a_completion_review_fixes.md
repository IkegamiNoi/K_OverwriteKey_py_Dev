# task_09a_completion_review_fixes

## 目的

phase 43 の完了判定前レビューで見つかった実装と仕様のずれを直す（decisions 43「完了判定前レビュー」・ユーザー判断 2026-10-04）。

- キーマップの単一対象の操作（編集・改名・削除・個別保存 / 読込）は、正本どおり**常にアクティブなキーマップ**を対象にする（`features.md` §4.3）
- プリセット一覧の Escape は**ダイアログにつき 1 つのハンドラ**にし、ドラッグを取り消した Esc を押し続けても閉じない（`features.md` §4.6「モーダルダイアログの作法」・暫定 30 §6a）

**presentation 限定・domain / application 不変・スキーマ不変。**

## 対象範囲

### `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`

- `selected_keymap_list_index()`（`:57-63`）を、一覧の選択（`focused_listbox_index`）ではなく **`active_keymap_id` に一致するキーマップの一覧上の位置**を返すように変える（無ければ `None`）。
  docstring も合わせる。呼び出し元は次のとおりで、どれも「対象 = アクティブ」が正本の規定:
  ボタンの有効化 `:67` / `rename_keymap_label` `:233` / `delete_keymap` の単一削除 `:276` / `edit_selected_keymap` `:364` /
  `keymap_list_edit.py:30`（範囲が無いときの 1 行）/ `config_io/keymap_file_io.py:31`（個別保存・読込の対象）
- 一覧のクリック・キー操作によるアクティブ化の経路（範囲確定時に下線の行をアクティブにする処理）は変えない

### `keyseq/presentation/listbox_range_drag.py`

- `ListboxRangeDrag` に、ドラッグ中かを返す `is_dragging() -> bool` と、外から取り消す `cancel_drag() -> None`（現行の `_escape` のドラッグ中の処理と同じ）を足す
- `bind_listbox_range_drag(..., bind_escape: bool = True)` を足し、`False` のときは一覧に `<Escape>` をバインドしない（既定は現行どおり。フル表示の 3 一覧は変えない）

### `keyseq/presentation/dialogs/preset_manager.py`

- 一覧の部品は `bind_escape=False` で作る
- `:83` の `self.bind("<Escape>", lambda _event: self.destroy())` を、`dialogs/escape_close.py` の
  `bind_escape_close(self, is_busy=self._range_drag.is_dragging, stop=self._range_drag.cancel_drag)` に置き換える
  （判定順 = ドラッグ中なら取り消して印を立てる → 印がある間は閉じない → 閉じる。Esc を離すと印を下ろす）
- `bind_escape_close` を使うダイアログが 4 つになるので、`instructions/common/codebase_map.md` の「Escape の結線」の記述（`PresetManagerDialog` は一覧側で取り消す、の部分）を「`bind_escape_close` で単一ハンドラ」へ直す

### テスト（追加・修正まで）

- `tests_ui/test_keymap_list_operations.py`: km1〜km3 を範囲選択して km3 がアクティブになった後、一覧からフォーカスを外した状態で
  `edit_selected_keymap` / `rename_keymap_label` / 単一の `delete_keymap` / `keymap_file_io.selected_keymap_for_io` の対象が km3（アクティブ）になる
- `tests_ui/test_preset_manager_range_drag.py`: ドラッグ中の Escape で取り消され、ダイアログが残る / **同じ Esc の押し続け（KeyRelease 無しの 2 回目の Escape）でも閉じない** /
  Esc を離した後の Escape で閉じる / ドラッグ中でなければ Escape で閉じる
- `tests_ui/test_listbox_range_drag.py`: `is_dragging` / `cancel_drag` / `bind_escape=False` で一覧に Escape がバインドされない
- `tests_ui/test_dialog_escape_binding.py` に `PresetManagerDialog` の項があれば追随（無ければ足さない）

### 設計メモ / 制約

- 正本の「Escape のハンドラはダイアログにつき 1 つにまとめ、状態で分岐する」に従い、一覧とダイアログに Escape を重ねない
- `selected_keymap_list_index` の名前は変えない（呼び出し元の修正を最小にする）

## 読むファイル

- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:50-75`・`:225-290`・`:355-375`
- `keyseq/presentation/controllers/keymap_panel/keymap_list_edit.py:20-35`
- `keyseq/presentation/controllers/config_io/keymap_file_io.py:25-40`
- `keyseq/presentation/listbox_range_drag.py`（全体）
- `keyseq/presentation/dialogs/preset_manager.py:70-90`・`:165-180`
- `keyseq/presentation/dialogs/escape_close.py`（全体）
- 手本のテスト: `tests_ui/test_keymap_list_operations.py`・`tests_ui/test_preset_manager_range_drag.py`・`tests_ui/test_dialog_escape_binding.py`

## 含まない

- 提案書 18 のリファクタ（task_10）/ 暫定 30 の凍結・decisions_archive・current.md の完了記載（task_09 の残り）
- シーケンス・キーマップの個別保存の対象の固定（別タスク化候補）
- `KeymapSwitchBatchDialog` の Escape の `bind_escape_close` への置き換え（別タスク化候補）
- 次に実行のキー移動（Home/End・PageUp/PageDown）と挿入位置は仕様を実装に合わせた（v0.10）ためコード変更なし

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加・修正したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: ①キーマップを範囲選択 → 一覧の外をクリック → 編集ボタンで下線（アクティブ）のキーマップが開く ②プリセット編集でドラッグ中に Esc を押し続けてもダイアログが閉じず、離してもう一度押すと閉じる。
