# task_02_keyboard_ui_record_and_display

## 目的

キーボードUI で、Shift を押しながら英字を記録すると置換先を大文字で保存し、枠に大文字のまま表示する（暫定 61 §5）。
task_01 の `normalize_mapping_target`（`keyseq/domain/config.py`）を presentation の置換先の 2 か所で使う。
**presentation のみ（`keyboard_window.py`・`keymap_panel_controller.py`）・domain / application / infrastructure 不変・JSON スキーマ不変**。

## 対象範囲（presentation 限定）

### `keyseq/presentation/keyboard_window.py`

- `_record_key`（`:618` 付近）: 既存の `yen` / `ro` の変換（`:629`）と同じ位置で、**Shift を押していて（`get_backend().window.is_shift_down()`）、記録した名前が ASCII の英字 1 文字（`a`〜`z`）なら大文字にする**。Shift を押していなければ小文字のまま。`yen` / `ro` の変換は今のまま。
  - `_record_key` は置換先の記録だけの入口（Tk の経路と記録用のフックの経路が合流する）。置換元・トリガー・key_hold・切替 / 停止 / トグルキーの記録は別の経路なので触らない。
- 表示の組み立て（`:231`）: 置換先を `normalize_key_name` ではなく `normalize_mapping_target` で正規化する（置換元の `:230` は `normalize_key_name` のまま）。
- 描画（`:469-470` 付近 `display = self._layout.key_display_name(display) or display_key_name(display)`）: **置換先が ASCII の英字 1 文字の大文字なら `key_display_name` を引かず、そのまま出す**（表示名は `A` と `a` を同じ名前で引くため）。それ以外は今のまま。

### `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`

- `assign_keymap_from_keyboard_ui`（`:631`）: `target = normalize_key_name(target_key)`（`:633`）を `normalize_mapping_target(target_key)` に替える。置換元（`:632`）と、その後の検査（`"+" in target`・`validate_key_name(target)` 等）は変えない。

### テスト（`tests_ui/`）

**既存テストの途中に新しいテストを差し込まない（各クラスの最後へ足す）。apply_patch で編集し、Python で書き換えない。**

- `tests_ui/test_keyboard_window_scan_code.py`:
  - 既存の `test_shift_does_not_change_other_key_names`（`a` + Shift → `a` を期待）は本タスクで意味が変わる。英字以外の名前（例: `f1`）で Shift を押しても変わらないことを確かめる形に直す（テスト名はそのまま）。
  - 追加（クラスの最後・`self._record` を使う）: `a` + Shift → `"A"` / `z` + Shift → `"Z"` / `a` + Shift なし → `"a"`。
- 表示（`tests_ui/test_keyboard_key_text.py` の `test_key_display_name_takes_priority_over_common_symbol` と同じ作り方・クラスの最後）:
  - `mappings` が `{"1": "A", "2": "a"}` のとき、キー `1` の枠の文字に `"A"`、キー `2` に `"a"` が出る。
  - `key_display_name` を `"x-name"`（`a` に対して）を返すよう patch しても、置換先 `"A"` の枠は `"A"` のまま（小文字の `"a"` の枠は従来どおり `"x-name"`）。
- 割り当て（`assign_keymap_from_keyboard_ui`）: 既存のテストでこの関数を呼んでいるもの（`grep -rn "assign_keymap_from_keyboard_ui" tests tests_ui`）と同じ作り方で、クラスの最後に: `a` の置換先を `"a"` にした後 `"A"` を割り当てると、保存値が `"A"`・キーマップに変更の印（`mark_keymap_dirty` が呼ばれる / dirty になる、既存テストの確かめ方に合わせる）。

## 読むファイル

- [暫定 61](../../../history/61_uppercase_replacement_target.md) §5
- `keyseq/presentation/keyboard_window.py:60-70`・`:215-240`・`:455-480`・`:610-640`
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:625-680`
- `keyseq/domain/config.py:132-145`（task_01 の `normalize_mapping_target`）
- 手本のテスト: `tests_ui/test_keyboard_window_scan_code.py:25-60`・`:125-145` / `tests_ui/test_keyboard_key_text.py:80-125`

## 含まない

- 統合確認・Windows / macOS の実機目視（task_03）
- 正本・`codebase_map.md` の更新（task_04）
- 置換元・トリガー・key_hold・切替 / 停止 / トグルキーの記録の変更・Caps Lock を見る処理・文言の追加

## 確認

- verifier（Windows・`.venv`・tests_ui は同時に 1 本だけ・`taskkill` 禁止）:
  - `compileall keyseq tests tests_ui` clean
  - `unittest -v tests_ui.test_keyboard_window_scan_code tests_ui.test_keyboard_key_text` と、割り当てのテストを足したモジュールが pass（追加 / 変更したテスト名が実行されていること）
  - `unittest discover -s tests` 全 pass・`unittest discover -s tests_ui` 全 pass（件数を記録）・`-m tests.smoke_app` pass
- 差分の直読み（メイン）: 置換元・他の記録経路を変えていないこと・既存テストの途中への差し込みが無いこと

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_03 でまとめて実施。
