# task_04_dialog_help_buttons

## 目的

暫定 53 §6.1 の表で「置く」のダイアログ 12 個に「?」ボタンを置き、押すとヘルプの窓を**そのダイアログの子の窓**として
飛び先を開いた状態で出す（§6.2・§6.3）。飛び先 id がデータにあることを検査テストで確かめる。
**presentation 限定（`help/` に「?」の部品と飛び先の定数・管理役に子の窓で開く入口・12 ダイアログへの「?」の追加）。
`grab_modal`・`install_minimize_grab_custody` は変えない。ダイアログの閉じ方（Escape・×・OK/キャンセル）は変えない。スキーマ不変。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/help/help_targets.py`（新規）

- 飛び先の定数（すべて guide タブ・大分類 id）: `SEQUENCE = "sequence"`・`KEYMAP = "keymap"`・`TRIGGER = "trigger"`・`PRESET = "preset"`・`KEYMAP_SET = "keymap_set"`・`CLEANUP = "cleanup"`・`KEYBOARD_UI = "keyboard_ui"`（§6.1 の表どおり）。
- `DIALOG_TARGETS: tuple[str, ...]`（上の全部。検査テスト用）。

### `keyseq/presentation/help/content/help_ja.json` と `tests/test_help_content.py`

- §6.1 の飛び先 id に骨組みの id を合わせる: `config_set` → `keymap_set`・`file_cleanup` → `cleanup`（題名・並びは変えない）。`tests/test_help_content.py` の期待する id の並びも合わせる。
- `tests/test_help_content.py` に検査を足す: `DIALOG_TARGETS` の各 id が同梱の `help_ja.json` の guide の大分類（または項目）の id に存在する。

### `keyseq/presentation/help/help_button.py`（新規）

- `add_help_button(row: tk.Misc, dialog: tk.Toplevel, target_id: str, *, tab: str = "guide") -> ttk.Button`:
  ボタン「?」（幅は最小。`width` を文字に合う最小値に）を `row` の**左端**に置く（`row` の既存の子より前。既存の子の pack の向きが left なら `before=` で先頭へ、right なら `side="left"` で置く等、列の左端に来ればよい）。
  ホバーで「ヘルプ」のツールチップ（`hover_tooltip.bind_hover_tooltip`）。キーの割り当てなし・Tab のフォーカス順には入る（`takefocus` 既定）。
  押すと `dialog.nametowidget(".")` の `help`（`HelpWindowController`）があれば `open_for_dialog(dialog, tab, target_id)` を呼ぶ。無ければ何もしない（テスト用の素の Tk ルートで例外にしない）。

### `keyseq/presentation/help/help_window_controller.py`

- `open_for_dialog(dialog: tk.Toplevel, tab: str, target_id: str) -> None`（§6.3）:
  - 既に同じダイアログの子として開いていれば再利用（前面化）。それ以外で窓があれば `close()` してから、`HelpWindow(dialog, ...)`（**master = dialog**）で作り直す（同時に 1 つ）。作り方・topmost・`<Destroy>` の扱い・フックの窓口の受け渡しは `open` と同じ（共通部分は小関数へ）。
  - 開いたら: 指定のタブへ切り替え、**フィルターを空にし**、飛び先の大分類を開き（項目 id ならその大分類と項目を開き）、先頭が見える位置へスクロールする。
  - 飛び先の id がデータに無い（読込失敗を含む）ときは、指定のタブで開くだけ（例外を出さない）。
  - 窓は grab を取らない。ダイアログを閉じると Tk の連鎖破棄で一緒に閉じる（追加の処理なし。`<Destroy>` で参照を捨てるのは既存どおり）。
- 窓・タブの表示（`help_window.py`・`help_tab_view.py`）に必要な最小の入口を足す（例: `HelpWindow.clear_filter()`・`HelpTabView.reveal(target_id) -> bool`）。

### 12 ダイアログ（§6.1 の「置く」）

各ダイアログの下端のボタン列（OK・キャンセル・閉じる 等の行）に `add_help_button(行, ダイアログ, 定数)` を 1 行足す（`grab_modal` の呼び出しより前・行の作成直後）:

| ファイル | 行の変数（目安） | 飛び先 |
|---|---|---|
| `dialogs/action_dialog.py`（`ActionDialog`） | `btns`（:93 付近） | `SEQUENCE` |
| `dialogs/keymap_edit_dialog.py` | `btns`（:92） | `KEYMAP` |
| `dialogs/trigger_dialog.py` | `btns`（:62） | `TRIGGER` |
| `dialogs/preset_manager.py` | `bottom`（:172） | `PRESET` |
| `dialogs/preset_dialog.py` | `btns`（:36） | `PRESET` |
| `dialogs/keymap_switch_batch_dialog.py` | `btns`（:158） | `KEYMAP` |
| `dialogs/keymap_set_history_dialog.py`（`KeymapSetHistoryDialog` のみ。`CategoryChooserDialog` には置かない） | `actions`（:73） | `KEYMAP_SET` |
| `dialogs/orphan_sweep_dialog.py` | `actions`（:49） | `CLEANUP` |
| `dialogs/quarantine_manage_dialog.py` | `actions`（:45） | `CLEANUP` |
| `dialogs/reference_cleanup_dialog.py` | `buttons`（:50） | `CLEANUP` |
| `dialogs/layout_delete_dialog.py` | `btns`（:46） | `KEYBOARD_UI` |
| `controllers/config_io/child_save_dialog.py`（`_create_action_dialog` のみ。`_create_dependency_dialog` には置かない） | `buttons`（:43） | `KEYMAP_SET` |

- 既存の初期フォーカス・ボタンの並び・Escape の束縛・既存のボタンの幅は変えない（「?」が加わるだけ）。

### tests_ui（新規 `tests_ui/test_dialog_help_buttons.py`）

- App を立てる作法は `tests_ui/test_help_window.py` にならう。本文は飛び先 id を含むテスト用の内容へ差し替える。
- 代表のダイアログ（少なくとも `TriggerDialog`・`OrphanSweepDialog`・子ファイルの保存の `_create_action_dialog`）で:
  - 下端の列の先頭（左端）に「?」がある
  - 「?」を押すとヘルプの窓が開き、`winfo_parent()` がダイアログ・grab はダイアログのまま（`grab_current()` がダイアログ）・選択タブ = 主要機能・飛び先の大分類が開いている・フィルターが空
  - メインから開いたヘルプ（フィルター入力あり）がある状態で「?」→ 前の窓が閉じ、新しい窓のフィルターは空（同時に 1 つ）
  - ダイアログを閉じる（キャンセル / Escape）とヘルプも破棄され `app.help.window is None`・ダイアログの grab の戻し先（メイン側）が既存どおり
  - 飛び先の id がデータに無いとき・読込失敗のときも例外なくタブだけ開く
- 12 ダイアログすべてについて、「?」が置かれていることを確かめる（作るのが重いダイアログは、`add_help_button` の呼び出しを grep で数える tests 側の静的テストでもよい。どちらにしたかを報告）。
- フックの入れ子（§4.4）: ダイアログの子のヘルプの入力欄に FocusIn → `get_hook_pause_count()` が 2 → FocusOut で 1 → ダイアログを閉じて 0。

### 設計メモ / 制約

- 「?」の追加はダイアログ側では 1 行（+ import）にとどめる。ヘルプの管理役の参照のしかたは `add_help_button` に閉じ込める。
- `grab_modal` / `install_minimize_grab_custody` / `modal.py` は変更しない（§6.3。正本への追記は task_08）。
- 既存の tests_ui（ダイアログの初期フォーカス・Escape・transient・teardown の各テスト）を壊さない。「?」がフォーカス順の先頭に来て初期フォーカスを奪わないこと（初期フォーカスは `grab_modal(focus=...)` のまま）。

## 読むファイル

- `instructions/history/53_help_window.md` §6（174-219 行）
- `keyseq/presentation/help/help_window_controller.py`・`help_window.py`・`help_tab_view.py`（編集対象）
- `keyseq/presentation/hover_tooltip.py` 105-122 行（`bind_hover_tooltip`）
- 12 ダイアログの各ファイルのボタン列の前後 15 行程度（上の表の行番号付近）
- 手本: `tests_ui/test_help_window.py` 1-110 行・ダイアログを開く既存 tests_ui（`grep -l "TriggerDialog\|OrphanSweepDialog" tests_ui` の該当部分）

## 含まない

- 確認・選択だけのダイアログ・画面の枠の編集の窓への「?」（§6.1 で置かない）
- バージョン情報・ライセンス（task_05）・本文の執筆と飛び先の項目 id への細分化（task_06）
- 正本「モーダルダイアログの作法」への追記（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` clean
- `tests.test_help_content`・`tests_ui.test_dialog_help_buttons`・`tests_ui.test_help_window` pass
- tests 全体 pass / tests_ui 全体（既知の負債 `test_compact_window` の 1 件を除き pass）/ smoke pass

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_08（実入力でダイアログとヘルプの両方を操作できること・最小化からの復帰）
