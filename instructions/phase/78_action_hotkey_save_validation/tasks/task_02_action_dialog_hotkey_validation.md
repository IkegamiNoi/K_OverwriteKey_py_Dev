# task_02_action_dialog_hotkey_validation

## 目的

正本 `key_input.md` §7.7（phase 78 で改訂）・§7.9「他方の OS のキー名」の hotkey の入口を実装する。出力シーケンスの hotkey アクションを、OK の時点で `validate_hotkey` に通す。通らなければ保存せず、通れば正規化した値を保存する。
**presentation（`ActionDialog.on_ok` の hotkey 分岐）限定。domain / application / infrastructure・JSON スキーマ・言語ファイルは変更しない。**

## 対象範囲（`ActionDialog.on_ok` の hotkey 分岐とそのテストのみ）

### `keyseq/presentation/dialogs/action_dialog.py`

`on_ok` の `if t == "hotkey":` の部分（現在 L257-264）を次の順の処理にする。

1. 既存の `accepts_key_name` のループ（他方の OS の修飾キーの拒否）は**そのまま残す**。順序・メッセージ（`capture.error.unknown_key`）も変えない。
2. 続けて `err_msg, normalized = self.parent.validate_hotkey(v)` を呼ぶ。
3. `err_msg` があれば `messagebox.showerror(tr("action_dialog.error.input_title"), err_msg)` を出して `return` する。`_dialog_result` は設定せず、窓も閉じない。
4. 通った場合は `self.parent._dialog_result = {"type": t, "value": normalized, "label": label}` とする。text の場合は今のまま `v` を保存する。

### 設計メモ / 制約

- `validate_hotkey` は `App.validate_hotkey`（→ `HotkeyService.validate`）を指す。プリセット編集（`preset_manager.py:318`）と同じ呼び出し口を使い、ダイアログ内で `HotkeyService` を作らない。
- エラー文は `validate_hotkey` が返す翻訳済みの文をそのまま出す。新しい言語キーは足さない。
- 空チェック（`value_required`）は今の位置・文言のまま残す。
- 実行時の正規化（`action_executor`）・読み込みの経路は変えない。

### テスト（`tests_ui/test_action_dialog_key_hold.py`）

- `setUp` で `self.root.validate_hotkey` に `HotkeyService(validate_key_name=self.root.input_gateway.validate_key_name).validate` を設定する（`keyseq.application.hotkey_service` から import）。
- 既存の `test_hotkey_rejects_other_os_modifier_but_keeps_unknown_normal_name` を新しい仕様に合わせて書き換える。テスト名も内容に合わせて変える。
  - `left command+a` は今どおり拒否され、窓が残り、メッセージに「不明なキー名」が含まれる。
  - `invalid_names` に入れた通常のキー名（例 `unknown-normal-name`）を含む hotkey も拒否され、窓が残る。`_dialog_result` は `None` のまま。
- 新規テストを追加する。**既存テストの途中に差し込まず、クラスの末尾に足す。**
  - `"Ctrl+ A"` を OK すると、`_dialog_result["value"] == "ctrl+a"` になる（正規化）。
  - 文法エラー（`ctrl++a`・`ctrl+ctrl+a`）は拒否され、窓が残り、`_dialog_result` は `None` のまま。
  - text の値（例 `"Ctrl+ A"`）は正規化されず、入力のまま保存される。

### 追加（reviewer 指摘・2026-11-23）

- `tests_ui/test_action_dialog_labels.py` の `setUp` にも同じ `validate_hotkey` を設定する（素の Tk の親で hotkey の OK を呼ぶ subTest があるため）。

## 読むファイル

- `instructions/common/spec_detail/key_input.md` の L232・L346
- `keyseq/presentation/dialogs/action_dialog.py`（編集対象。`on_ok` は L230-270 付近）
- `keyseq/presentation/dialogs/preset_manager.py:312-325`（手本の呼び出し）
- `keyseq/application/hotkey_service.py`
- `tests_ui/test_action_dialog_key_hold.py`（編集対象。L14-60 と L300-335）

## 含まない

- `codebase_map.md` の更新・統合確認・実機目視（task_03）
- 既存ファイルの移行・読み込み時の正規化・プリセット編集・実行時の経路の変更
- hotkey 以外の種類の保存処理

## 確認（verifier が実行）

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui`
- `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_action_dialog_key_hold tests_ui.test_action_dialog_labels tests_ui.test_action_dialog_mouse_scroll tests_ui.test_action_dialog_drag` が pass
- `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_action_dialog_control` が単独で pass（実行順依存の既存の 2 件があるため単独で流す）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_03 でまとめて実施する。
