# task_01_choice_dialog

## 目的

はい / いいえ に本文で意味を割り当てている確認 3 か所を、**ボタンに操作名を書いたアプリ側のモーダルダイアログ**へ替える（暫定 51 §3.5・C15）。
各選択の後の処理（呼び出し元から見た分岐）は現状と同じにする。× / Esc の扱いと、開いている間のフック停止は §3.5 の表と規定に従う。
**presentation 限定（`controllers/config_io/`）・application / domain 不変・JSON スキーマ不変。**

## 対象範囲（presentation・config_io 限定）

### 新規 `keyseq/presentation/controllers/config_io/choice_dialog.py`

- `ask_choice(app, *, title: str, message: str, choices: list[tuple[str, str]], default: str, cancel: str) -> str`
  - `choices` = `(選択肢 id, ボタンの文字)` の並び（**見た目の左 → 右**）。戻り値は押したボタンの id。× / Esc は `cancel` の id を返す。
  - 親 = `app.grab_current()`（例外・None なら `app`）。`tk.Toplevel(親)`・`resizable(False, False)`・本文は `ttk.Label`（`justify="left"`・`wraplength=560`）・ボタンは右寄せ。
  - `app.hook.suspend_hook_for_dialog(dialog)` を呼ぶ（破棄で自動解除・ネスト対応。`key_input.md` §7.2）。
  - `grab_modal(dialog, 親, focus=既定ボタン)` で開く。Enter = フォーカス中のボタンを押す（`<Return>` で `focus_get()` が `ttk.Button` なら `invoke()`）。Tab でボタン間を移動（ttk の既定）。
    Esc と × (`WM_DELETE_WINDOW`) は `cancel` の id で閉じる。`dialog.wait_window()` で待つ。
  - **呼び出し側はモジュール経由で呼ぶ**（`from keyseq.presentation.controllers.config_io import choice_dialog` → `choice_dialog.ask_choice(...)`）。テストは `choice_dialog.ask_choice` を差し替えて分岐を検査する。

### `io_dialogs.py` `choose_save_path_with_collision`

- `messagebox.askyesnocancel` → `ask_choice(title="保存先の確認", message=f"同名ファイルがすでにあります。\n\n{path}\n\n上書きしますか？", choices=[("overwrite","上書き"),("save_as","別名保存"),("cancel","キャンセル")], default="overwrite", cancel="cancel")`。
  `overwrite` = そのまま `path` / `save_as` = 現状どおり `asksaveasfilename` / `cancel` = `""`。

### `child_save_dialog.py` `confirm_recalculated_overwrite`

- `messagebox.askyesnocancel(..., default=NO)` → `ask_choice(title="再計算後の保存先を確認", message=<末尾の「「はい」= …」の行を除いた本文>, choices=[("overwrite","上書き"),("save_as","別名保存"),("abort","保存を中止")], default="save_as", cancel="abort")`。
  `overwrite` = `{}` / `save_as` = 現状の行ごとの別名保存の処理 / `abort` = `None`。外側の `suspend_hook_for_dialog()` / `resume_hook_after_dialog()` の try/finally は**そのまま残す**。
  本文のそれ以外の行（種別・対象名・保存先・共有状況）は変えない（task_02 の担当）。

### `keymap_set_io.py` `choose_split_base_dir_for_keymap_set`

- `messagebox.askyesno` → `ask_choice(title="保存先の確認", message="構成セットが既定の保存先の外に保存されます。\nキーマップ・トリガーセット・出力シーケンスも構成セットと同じフォルダ(keymaps / trigger_sets / sequences)に保存しますか？", choices=[("nearby","構成セットと同じフォルダに保存"),("default","既定の保存先に保存")], default="nearby", cancel="default")`。
  `nearby` = 現状の「はい」（構成セットのフォルダ）/ `default` = `""`。括弧は中身が英数字・記号だけなので半角（暫定 51 §3.6 D1）。

### テスト

- 新規 `tests_ui/test_choice_dialog.py`: 実ダイアログで (1) 既定ボタンに初期フォーカス・Enter で既定の id (2) Tab で次のボタンへ移って Enter でその id (3) Esc / × で `cancel` の id (4) 開いている間 `hook_suspend_count` が 1 増え、閉じた後に元へ戻る（閉じ方 3 通り）(5) 親が grab 中の窓のとき、その窓を親（transient）にする。
- 既存テストの追従: 上の 3 関数について `messagebox.askyesno` / `askyesnocancel` を差し替えている箇所（`tests_ui/test_config_io_characterization.py:431-483`・`tests_ui/test_config_io_characterization_keymap_set_startup.py`・`tests_ui/test_child_save_dialog.py`・`tests_ui/test_keymap_set_history_flow.py` ほか。`grep` で網羅確認）を `choice_dialog.ask_choice` の差し替えへ置き換える。
  **期待する分岐・呼び出し回数・本文の検査は保ち**、引数（題・本文・choices・default・cancel）を検査する。同じファイルの**他の確認**（未保存確認など）の askyesno の差し替えは変えない。

### 設計メモ / 制約

- 手本: `hotkey_presets_io.py:45-90` の `confirm_overwrite`（Toplevel・ボタン・Esc / ×・`grab_modal`）。ただし同ファイルは本タスクで変えない（共通化しない）。
- 戻り値の分岐は現状と同じ。選択肢を増やさない。
- `keymap_set_io.py` のこの関数以外・`child_save_dialog.py` の他の文言・`io_dialogs.py` の `ask_link_label_to_filename` は触らない。

## 読むファイル

1. `instructions/history/51_ui_terminology.md` の §3.5 と §3.6 の D1・D6・A19 の行
2. `keyseq/presentation/controllers/config_io/io_dialogs.py`（全体）
3. `keyseq/presentation/controllers/config_io/child_save_dialog.py:240-290`
4. `keyseq/presentation/controllers/config_io/keymap_set_io.py:115-125`・`:728-742`
5. `keyseq/presentation/controllers/config_io/hotkey_presets_io.py:45-90`（手本）
6. `keyseq/presentation/modal.py:113-175`（`grab_modal`）・`keyseq/presentation/controllers/hook_controller.py:48-80`（停止 / 解除）
7. `instructions/common/spec_detail/features.md:978-1043`（モーダルダイアログの作法）
8. `tests_ui/test_config_io_characterization.py:425-490`（既存テストの形）

## 含まない

- 3 か所以外の文言（種別名「トリガー一覧」・共有状況・未保存確認・`_kind_label` 等）の置換（task_02）
- `hotkey_presets_io.py` の専用ダイアログの共通化（暫定 51 §3.5 で本フェーズ外）
- 「…」の付与 / 除去（task_06）・正本反映（task_08）・実機目視（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 新規 `tests_ui/test_choice_dialog.py` の (1)〜(5) が pass
- 追従した既存テストが pass（3 関数の全分岐: io 3 通り・child_save 3 通り・keymap_set_io 2 通り + × / Esc）
- `-m unittest discover -s tests` / `-s tests_ui` 全 pass・`-m tests.smoke_app` OK

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_08 でまとめて実施（3 ダイアログの見た目・Enter / Tab / Esc）。
