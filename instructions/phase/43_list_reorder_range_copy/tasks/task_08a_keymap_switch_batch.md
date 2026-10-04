# task_08a_keymap_switch_batch

## 目的

キーマップを増やす 3 つの流れ（追加・個別読込・貼り付け）で、切替キーが要るキーマップ（切替キー未設定の既存 + 増やすもの）を
**1 つのダイアログでまとめて設定**する（暫定 30 v0.9 §6.3・§6.4・§10-12）。現行の「未設定の既存を 1 つずつアクティブにして編集ダイアログ →
続いて追加 / 読込 / 貼り付けのダイアログ（貼り付けは 1 件ずつ）」を置き換える。
**application に検査の純関数 1 モジュール ＋ presentation（ダイアログ新設・keymap_add_flow・keymap_list_edit）。domain・スキーマ不変。**

## 対象範囲

### `keyseq/application/keymap_switch_batch.py`（新規・純関数）

- `validate_switch_batch(runtime: dict, stop_key: str, toggle_key: str, new_keymaps: list[dict], row_keys: list[str], row_keymap_ids: list[str]) -> tuple[int, str] | None`
  - 行 i の切替キー `row_keys[i]`（正規化前の値可）を、**完成予定の状態**（`runtime` の既存キーマップ + `new_keymaps` を足した写し。runtime は変えない）に対して検査し、
    最初のエラーの `(行番号, 理由の文言)` を返す。エラーが無ければ `None`
  - 検査（行の上から順・各行で下の順）: 空 → 停止キーとの重なり → 一時停止/再開キーとの重なり → **完成予定の全キーマップのトリガーキー** →
    **完成予定の全キーマップの置換元キー** → ダイアログ外のキーマップの切替キー（`keymap_switch_keys`。行の対象のキーマップ自身の値は除く）→ **上の行と同じキー**
  - トリガー・置換元キーの集合は `analyze_key_overlaps(完成予定の写し, stop, toggle)` の `all_trigger_keys` / `all_source_keys` を使う（集合の作り方を別に書かない）
  - 理由の文言は現行の `validate_keymap_switch_assignment`（`keymap_panel_controller.py:158-200`）と `_validate_addition_key` の文言に揃え、行の名前は呼び出し側で付ける
  - presentation に依存しない（tkinter / messagebox を使わない）

### `keyseq/presentation/dialogs/keymap_switch_batch_dialog.py`（新規）

- `KeymapSwitchBatchDialog(parent, title, rows, validate)`。`rows` = 行ごとの `(区別の表示, 名前, ラベルの初期値, 切替キーの初期値)`。
  `validate(values: list[dict]) -> tuple[int, str] | None`（`values[i] = {"key", "label"}`・キーは `normalize_key_name` 済み）
- 行ごとに「区別の表示（既存 / 新規 / 読込 / 貼り付け）・名前・ラベル入力・切替キー（読み取り専用の欄 + キー入力で取得 + クリア）」。
  キーの取得・クリア・Escape の扱いは `KeymapEditDialog`（`keymap_edit_dialog.py`）と同じ（取得中は Escape で取得だけを止める・取得中でなければ閉じる = キャンセル）
- **行が 1 つのときは区別の表示と見出しを出さず、現行の `KeymapEditDialog` に近い見た目**にする。高さは行数に合わせ、多いときは縦にスクロール（上限の高さを決めて Canvas + Scrollbar 等）
- OK: `validate` がエラーを返したら `messagebox.showerror("設定できません", 理由, parent=self)` を出し、その行の切替キー欄へフォーカスして**閉じない**。
  エラーが無ければ `self.result = values` で閉じる。キャンセル / Escape / 閉じるボタン: `self.result = None`
- フックの停止は `KeymapEditDialog` と同じく `parent.hook.suspend_hook_for_dialog(self)`・モーダルは `grab_modal`
- `dialogs/__init__.py` に公開を足す

### `keyseq/presentation/controllers/keymap_panel/keymap_add_flow.py`（置き換え）

- 3 つの入口（`add_keymap` / `add_imported_keymap(keymap)` / 貼り付け用の入口 `paste_keymaps(sources: list[dict]) -> tuple[int, int] | None`）が、
  共通の 1 経路（例: `_run_batch(kind, new_keymaps) -> bool`）を通る:
  1. 既存のキーマップが 0 個なら現行どおりダイアログなし（追加 = `create_keymap`・読込 = そのまま追加・切替キー不要。貼り付けは保管庫が空でない限り既存は 1 個以上ある）
  2. 行を組み立てる: 切替キー未設定の既存キーマップ（一覧順）→ 増やすキーマップ。**増やすキーマップは確定前にすべて作っておく**
     （追加 = `{"id", "label": "", "mappings": {}}` 相当 / 読込 = 読み込んだ dict / 貼り付け = `duplicate_keymap(元, id, 連番ラベル)`）。
     id は `next_keymap_id` を**候補を足した写しに対して**順に呼んで重ならないように採番する（runtime には足さない）。
     貼り付けのラベルは `numbered_labels`（既存ラベル + 先の候補を含む・現行 `keymap_list_edit.py:141-146` と同じ）
  3. `KeymapSwitchBatchDialog` を開く。`validate` は `validate_switch_batch` を呼び、行の名前を付けた文言を返す
  4. キャンセル → **何も変えない**（runtime・切替キーの表・未保存の印・アクティブ）で `False`
  5. OK → **アクティブ化・確認ダイアログ・イベントループを挟まずに一度で確定**: 既存の行のラベル・切替キーを設定 → 増やすキーマップを末尾へ追加 → 切替キーを登録 →
     未保存の印（現行と同じ: 変更した既存と追加したキーマップは `mark_keymap_dirty`・貼り付けは加えてトリガー一覧〔`mark_trigger_set_dirty`〕と各シーケンス〔`mark_sequence_dirty`〕・
     追加は現行の `add_keymap` と同じ）→ 後処理（`_refresh_after_keymap_change`〔重なりの表の作り直しを含む〕）
- **アクティブは変えない**（`activate_keymap_by_id` を流れの中で呼ばない）。`apply_keymap_edit` と `_collect_missing_switch_edits` / `_apply_pending_switch_edits` / `prepare_keymap_paste` / `paste_keymap` は使わなくなるので削除する
  （`apply_keymap_edit` はダブルクリックの編集で使い続けるので残す）
- 個別読込の後処理（`keymap_file_io.py:249-253` の `joins_existing_set` の印と `_refresh_after_load`）は呼び出し側のまま変えない
- 完了の一時メッセージは現行の文言（「キーマップを追加しました: <id>」等）を維持

### `keyseq/presentation/controllers/keymap_panel/keymap_list_edit.py`

- `paste_keymaps`: 保管庫の全キーマップを `keymap_add_flow` の貼り付けの入口へ 1 回で渡し、返った範囲（貼った行）を `_finish(select=...)` で選択する。キャンセルなら何もしない
  （現行の 1 件ずつのループと `prepare_keymap_paste` の呼び出しをやめる）

### テスト（追加・修正まで）

- 新規 `tests/test_keymap_switch_batch.py`（`validate_switch_batch`）: 空 / 停止 / トグル / 既存キーマップのトリガー / **増やすキーマップ自身のトリガー** /
  **別の増やす行のトリガー** / 置換元キー（既存・増やす側）/ ダイアログ外の切替キー / 行どうしの重複 で正しい行番号と理由・エラーなしで `None`・runtime が変わらない
- 新規 `tests_ui/test_keymap_switch_batch_dialog.py`: 1 行のとき区別の表示と見出しが無い / 複数行で各行の取得・クリア / エラーで閉じずその行へフォーカス / キャンセル・Escape で `result is None` / 取得中の Escape は取得だけを止める
- `tests_ui/test_task06_keymap_management_ui.py` の追加・個別読込の項（`:225-420` の追加・未設定の既存・リトライ・キャンセル・個別読込）を新しいダイアログに追随させ、次を確かめる:
  未設定の既存と新規が 1 つのダイアログに並ぶ / キャンセルで runtime・切替キー・未保存の印・アクティブが変わらない / OK で全部が一度に反映 / **流れの途中でアクティブが変わらない**（`activate_keymap_by_id` が呼ばれない）
- `tests_ui/test_keymap_list_operations.py` の貼り付けの項（`:281-380`）を追随: 複数貼り付けでダイアログが 1 回 / キャンセルで何も貼らない / 連番ラベルが初期値 / トリガー一覧の独立・未保存の印・アクティブ不変 /
  **貼るキーマップ自身のトリガーと同じ切替キーはエラーで閉じない**
- `KeymapEditDialog` を差し替えていた既存テストの patch 先を新しいダイアログへ変える（ダブルクリック編集のテストは `KeymapEditDialog` のまま）

### 設計メモ / 制約

- 検査を 2 か所に持たない: 行が 1 つでも同じダイアログ・同じ `validate_switch_batch` を通す（§6.4。現行の追加 / 読込 / 貼り付け用の `KeymapEditDialog` 呼び出しは残さない）
- 確定の途中で失敗しうる処理（ダイアログ・アクティブ化・検証のやり直し）を確定の中に置かない。確定の前にすべて揃える
- ダイアログを開いたことでフックが止まる（実行中の状態の扱い）は全ダイアログ共通のまま変えない（§6.4「実行中の状態」）
- `keymap_add_flow.py` は 300 行・関数 30 行の目安。ダイアログは 300 行目安

## 読むファイル

- 暫定仕様 `instructions/history/30_list_reorder_range_copy.md` §6.3・§6.4・§7・§10-12
- `keyseq/presentation/controllers/keymap_panel/keymap_add_flow.py`（全体・置き換え対象）
- `keyseq/presentation/controllers/keymap_panel/keymap_list_edit.py:124-160`（貼り付け）
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:158-230`（切替キーの検証の文言・入口の委譲）
- `keyseq/presentation/dialogs/keymap_edit_dialog.py`（全体・ダイアログの手本）
- `keyseq/application/key_overlap.py:24-80`（`KeyOverlapAnalysis`・`analyze_key_overlaps`）
- `keyseq/application/keymap_service.py:85-180`（採番・作成・切替キー）
- `keyseq/domain/keymap_triggers.py` の `duplicate_keymap`
- `keyseq/presentation/controllers/config_io/keymap_file_io.py:240-255`（個別読込の呼び出し側）
- 手本のテスト: `tests_ui/test_task06_keymap_management_ui.py:225-420`・`tests_ui/test_keymap_list_operations.py:281-380`

## 含まない

- 正本反映（task_09）
- ダブルクリックでの通常の編集（`KeymapEditDialog`・`apply_keymap_edit`）の変更
- キーマップの切替キーの重複保持（§11）/ ダイアログ表示中のフック停止に伴う実行状態の扱いの変更（§6.4）
- 個別保存（`5_08_07`）の「キーマップの追加として扱う」箇所の挙動変更（追加の流れを通るので自動で追随する範囲だけ）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加・修正した tests / tests_ui のテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass
- `grep -n "activate_keymap_by_id\|KeymapEditDialog" keyseq/presentation/controllers/keymap_panel/keymap_add_flow.py` が 0 件

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: ①キーマップ 1 つ（切替キーなし）から追加 → 既存と新規の 2 行のダイアログ ②切替キーのある状態で追加 → 1 行で現行に近い見た目
  ③2 つ以上を Ctrl+C → Ctrl+V → 1 つのダイアログ・連番ラベル・キャンセルで何も貼らない ④貼るキーマップのトリガーと同じ切替キーはエラーで閉じない ⑤個別読込も同じダイアログ ⑥流れの中でアクティブが変わらない。
