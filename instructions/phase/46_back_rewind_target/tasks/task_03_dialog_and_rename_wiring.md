# task_03_dialog_and_rename_wiring

## 目的

戻す・先頭への編集ダイアログに「対象のトリガーを指定する」チェックと対象のドロップダウン（呼び出し先のドロップダウンの流用）を加え、
OK 時の検査（task_01 の `edit_control_target_violation`）とキー変更の書き換え（task_01 の `rename_control_targets`）を配線する（暫定 32 §2・§5）。
表示（一覧・省略表示の要約・呼び出し先の表示枠）は既に全経路で `resolve_call` を渡しているため、domain（task_01）の変更で反映済み — 本タスクは UI テストで確認だけする。
**presentation 限定。domain / application は変えない・スキーマ不変。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/dialogs/action_control_fields.py`

- `__init__` にキーワード引数 `control_target_check: Callable[[str], str | None] | None = None` を足す（保持のみ）
- `_build_system_fields`（呼び出し先のドロップダウンを作る箇所 :114-137）に以下を足す:
  - `self.control_target_var = tk.BooleanVar(value=False)` と `ttk.Checkbutton(text="対象のトリガーを指定する", variable=..., command=self.sync_system)`。
    置き場は呼び出し先の行（row=4）の**上**の行に差し込まず、既存の行番号を崩さない位置（例: row=7・columnspan=3）でよい。ただし表示上ドロップダウンと近い位置が望ましいので、
    既存の row 番号を変えずに置けるなら row=3〜4 の間の別行でもよい（既存 UI テストの grid 位置の assert を壊さないことを優先）
- `sync_system`:
  - 戻す / 先頭へのとき: チェックを表示・`call_target_label` と `call_target_combo` を表示・見出しの文字を「対象のトリガー」・
    ドロップダウンの `state` はチェック ON で `"readonly"`・OFF で `"disabled"`
  - 呼び出しのとき: 現行どおり（見出し「呼び出し先」・`state="readonly"`・チェックは隠す）
  - それ以外: チェック・ドロップダウンとも隠す（現行どおり）
  - 呼び出しの注記・「一括」チェックは呼び出しのときだけ（現行どおり）
  - 選択値（`call_target_var`）・`_missing_call_target`・チェックの値は操作の切替で**消さない**
- `load`: `op` が back / rewind のとき、`"target" in action` ならチェック ON・`_select_call_target(normalize_key_name(str(action.get("target", ""))))`（空なら未選択）・無ければチェック OFF。
  `sync_system()` の後に選択する（呼び出しと同じ順）
- `_build_system_result`: `op in (OP_BACK, OP_REWIND)` でチェック ON なら `_build_control_target_result(label, result)` を呼ぶ。チェック OFF なら現行どおり `label` だけ（`target` を書かない）
- `_build_control_target_result`（新規・`_build_call_result` と同じ形）:
  - 候補に無い表示で `（参照先なし）` のまま → `control_target_check(missing)` の文言（無ければ `f"対象のトリガーがありません（{missing}）"`）でエラー
  - 未選択 → `"対象のトリガーを選んでください"`
  - 選択あり → `control_target_check(target)` が文言を返せばエラー（閉じない）
  - 通れば `result.update({"target": target, "label": label})`
  - エラー表示は既存と同じ `messagebox.showerror("入力エラー", ...)`

### `keyseq/presentation/dialogs/action_dialog.py`

- `__init__` に `control_target_check` を足し、`ActionControlFields(...)`（:123 付近）へそのまま渡す

### `keyseq/presentation/controllers/trigger_panel/action_edit.py`

- `_call_dialog_options`（:362-385）の戻り値を `(candidates, call_check, control_target_check)` の 3 要素にし、
  `control_target_check = lambda target: edit_control_target_violation(owner_key, target, find_trigger)`（同じ `find_trigger` を使う）
- 呼び出し元 2 か所（:71・:214 付近）で受け取り、`ActionDialog(..., control_target_check=...)` へ渡す

### `keyseq/presentation/controllers/trigger_panel/trigger_row_edit.py`

- キー変更の書き換え（:135-143）で、`rename_call_targets` の結果（無ければ元の `actions`）に続けて `rename_control_targets` を適用する。
  どちらかで変わったら `trigger["actions"]` を差し替え、`mark_sequence_dirty(trigger)` を 1 回呼ぶ（条件 `old != new and was_effective` は現行どおり）

### テスト（tests_ui）

- `tests_ui/test_action_dialog_control.py`（既存へ追加・既存の呼び出しのテストの形を流用）:
  - 戻す / 先頭へでチェックとドロップダウンが出る・OFF でドロップダウンが `disabled`・ON で `readonly`・見出しが「対象のトリガー」・注記と「一括」は出ない
  - OFF で OK → `target` 無し / ON で選んで OK → `target` が正規化キー
  - ON で未選択 → 「対象のトリガーを選んでください」で閉じない / `control_target_check` の文言で閉じない / 参照先なしのまま OK → 文言で閉じない
  - 既存の `target` 付きの行を開くとチェック ON で選ばれている・候補に無ければ `f5（参照先なし）`・`target` 無しの行は OFF
  - 呼び出し ⇔ 戻すの切替で選択とチェックが保たれる・呼び出しへ戻すとドロップダウンが `readonly`・見出しが「呼び出し先」
- キー変更の書き換え: `tests_ui/test_trigger_effective_row.py` の `test_effective_key_change_keeps_existing_state_transfer_and_call_rewrite`（:106）の形を流用して、
  戻す / 先頭への `target` も新しいキーへ書き換わり・未保存扱いになり・書き換えたトリガーの位置 / 周回 / 履歴が消えないことを追加（同じファイルか `test_sequence_control_review_fixes.py` のどちらか近い方）
- 表示: `tests_ui/test_action_list_rendering.py` に、`target` 付きの戻すの行が一覧で `[back] → f5` / 参照先なしで `[back] → f5（参照先なし）` と出ることを 1 件追加（既存のテストの形を流用）

### 設計メモ / 制約

- ドロップダウンと候補・`（参照先なし）` の表示は呼び出しのものを**共有**する（別のウィジェットを作らない）
- 単独登録の制限（`standalone_violation`）は変えない（`target` の有無に関係ない）
- `edit_call_violation` は呼び出しのときだけ・`edit_control_target_violation` は戻す / 先頭へのときだけ使う

## 読むファイル

- `instructions/history/32_back_rewind_target.md` §2・§5・§6
- `keyseq/presentation/dialogs/action_control_fields.py`（全体・341 行・編集対象）
- `keyseq/presentation/dialogs/action_dialog.py:15-140`
- `keyseq/presentation/controllers/trigger_panel/action_edit.py:60-90`・`:205-230`・`:355-386`
- `keyseq/presentation/controllers/trigger_panel/trigger_row_edit.py:115-145`
- `keyseq/domain/control_target.py`（task_01・全体）
- `tests_ui/test_action_dialog_control.py:1-50`・`:128-282`（手本）・`tests_ui/test_trigger_effective_row.py:80-130`・`tests_ui/test_action_list_rendering.py` の呼び出しの表示のテスト付近

## 含まない

- domain / application の変更（task_01・task_02 で完了）
- 案 B（後送り）
- 正本 `spec_detail/`・`codebase_map.md` の更新（task_04）

## 確認

- 追加した UI テストが pass: `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_action_dialog_control tests_ui.test_trigger_effective_row tests_ui.test_action_list_rendering`（該当ファイルへ追加した場合は `tests_ui.test_sequence_control_review_fixes` も）
- 既存テスト全 pass: `-m compileall -q keyseq tests tests_ui` / `-m unittest discover -s tests` / `-m unittest discover -s tests_ui` / `-m tests.smoke_app`（verifier が実行）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **本タスクの完了後にユーザーの実機目視**（ダイアログのチェック・グレー・拒否の文言 / 一覧の表示 / 指定ありの戻す・先頭へが直前のトリガーに関係なく指定先に効くこと / キー変更の追従）。
