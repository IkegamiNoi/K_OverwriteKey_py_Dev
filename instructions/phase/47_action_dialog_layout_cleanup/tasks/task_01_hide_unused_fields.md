# task_01_hide_unused_fields

## 目的

出力シーケンスの追加・編集ダイアログ（`ActionDialog`）で、選んだ種別で使わない項目をグレーにせず非表示にし、「末尾に追加」を種別の行の右端へ移す。
開いたときのフォーカスを、値欄が無い種別では種別のドロップダウン（ループの行の編集ではループ回数の欄）へ入れる（phase.md「確定」1〜4）。
**presentation 限定（`keyseq/presentation/dialogs/action_dialog.py`）・domain / application 不変・JSON スキーマ不変。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/dialogs/action_dialog.py`

- **非表示の切替**（`_sync_capture_ui`）: 今の `configure(state="disabled")` / `"normal"` による切替をやめ、`grid()` / `grid_remove()` で表示を切り替える
  - 「値」のラベルと `value_entry`: hotkey / text だけ表示（mouse_click・system・file_line では非表示）。値のラベルは今 `ttk.Label(...)` を変数に持っていないので、属性に持たせる（例 `self.value_label`）
  - `capture_btn` と `capture_hint`: hotkey だけ表示。非表示にするとき記録は止める（今の `_stop_recording()` を維持）。
    text 用の説明文の差し替え（`"※text は通常の文字入力です…"`）は不要になるので削除してよい
  - `presets_frame` と `preset_edit_btn`: hotkey だけ表示
  - 既存のマウス設定・system / file_line の欄の表示切替はそのまま
  - 表示に戻すときは `state` を `normal` に戻す（今グレーになっている状態を引きずらない）
- **「末尾に追加」**（`mode == "add"` のときだけ）: 今の `row=7, column=0` から、種別のドロップダウンと同じ `row=0` の右端（`column=3`・`sticky="e"`）へ移す。既定 ON・`append_to_end_var` の扱い・OK 時の挙動は不変
- **初期フォーカス**（`grab_modal(self, parent, focus=...)`）: `_sync_capture_ui()` の後の種別で決める
  - hotkey / text → `value_entry`（現行どおり）
  - mouse_click・system・file_line → `type_combo`
  - `mode == "edit_loop"`（種別・操作が disabled）→ `control_fields.loop_count_entry`。「無限」にチェックがあり回数の欄が disabled なら `control_fields.loop_infinite_check`
  - 決める処理は小さな関数に分ける（例 `_initial_focus_widget()`）
- **種別の切替で非表示にした欄にフォーカスがあった場合**は `type_combo` へ移す（非表示の欄にキー入力が入り続けないように）

### テスト（`tests_ui/`）

- `tests_ui/test_dialog_initial_focus.py:94-105`: mouse_click の subTest の期待を `type_combo` に改める（hotkey / text は `value_entry` のまま）。system・file_line（`mode="add"` で種別を変えて開く or `initial` を渡す）と edit_loop の初期フォーカスのテストを足す
- 新規または既存の UI テストに次を足す（置き場は `tests_ui/test_action_dialog_control.py` の流儀に合わせる）:
  - 種別ごとに値・記録・プリセット枠・プリセット編集が表示 / 非表示になる（`winfo_ismapped()` 等）。hotkey → system → hotkey の往復で元に戻り、`state` が normal
  - 「末尾に追加」が `mode="add"` のとき種別と同じ行（`grid_info()["row"] == 0`）にあり、他のモードでは作られない
  - 非表示の欄にフォーカスがある状態で種別を変えるとフォーカスが `type_combo` へ移る
  - 最小化から復元したとき非表示の欄へフォーカスを戻さない（`tests_ui/test_minimize_grab_custody.py:63-66,326-353` の流儀。難しければ「最後にフォーカスがあった欄が `type_combo` なら `type_combo` へ戻る」で可）

## 読むファイル

- `keyseq/presentation/dialogs/action_dialog.py`（全体）
- `keyseq/presentation/dialogs/action_control_fields.py:85-100,184-225`（ループの欄の名前・`_show` の表示切替の流儀）
- `keyseq/presentation/modal.py:35-50,122-160`（`grab_modal` の初期フォーカスと復元の `focus_lastfor`）
- `tests_ui/test_dialog_initial_focus.py`（全体）・`tests_ui/test_action_dialog_control.py`（先頭の setUp と表示確認の 1〜2 例）・`tests_ui/test_minimize_grab_custody.py:40-80,326-360`

## 含まない

- 高さ・幅の固定 / 項目の並び順の見直し / system・file_line・マウス設定の欄の中身の変更
- プリセット編集など他のダイアログ
- 正本の改訂（task_02）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui`
- `-m unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` が全 pass（verifier が実行）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- **本タスクの完了後にユーザーの実機目視**（各種別の表示・「末尾に追加」の位置・開いたときのフォーカス・切替での高さの伸び縮み）
