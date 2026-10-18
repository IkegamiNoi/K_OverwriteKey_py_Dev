# task_01_receive_from_layout_only

## 目的

フックの実行時と画面の枠の編集の窓で、走査コードからキー名を引くとき、既知の特殊キーの表へ落とすのをやめる。
選んでいるレイアウトの `scan_code` だけで名前を引く（暫定 45 §3）。
デバッグ出力（`debug_jis_special_key_events`）の対象の判定も、既知の名前ではなくレイアウトの `scan_code` で決める。
**presentation 限定**（`keyboard_layouts.py`・`layout_controller.py`）。domain・application・infrastructure は不変（既知の表そのものの削除と送信側は task_02）。JSON スキーマ不変。

## 対象範囲（presentation 限定）

### `keyseq/presentation/keyboard_layouts.py`

- `resolve_key_id_from_scan_code` を**削除**する（既知の表への落とし込みをやめる。中間の関数は残さない）。
- `resolve_known_key_name_from_scan_code` の import を削除する。
- `resolve_layout_key_id_from_scan_code` は変えない。

### `keyseq/presentation/controllers/layout_controller.py`

- `resolve_key_name_from_scan_code`: `resolve_layout_key_id_from_scan_code(self.get_current_keyboard_layout(), scan_code)` を `normalize_key_name` して返す。
- `should_debug_special_key_event`: 次の 2 つをやめる。
  - `is_special_key_name(raw_name)` / `is_special_key_name(resolved_key)` の判定
  - レイアウトの行を `SPECIAL_KEY_NAMES` で絞る処理

  代わりに、設定が真で押下（`down`）のとき、**イベントの走査コードが選んでいるレイアウトの `scan_code` を持つ行に当たるなら真**とする（行の `id` は問わない）。
  走査コードが整数にできなければ偽。
- import を整理する: `SPECIAL_KEY_NAMES` / `is_special_key_name` / `resolve_key_id_from_scan_code` を外し、`resolve_layout_key_id_from_scan_code` を加える。

### テスト

- `tests/test_keyboard_layout_files.py`:
  - `test_scan_code_lookup_keeps_known_key_fallback` と `resolve_key_id_from_scan_code` の import を削除する。
  - 代わりに「US TKL（`resolve_keyboard_layout()`）で走査コード 41 を引くと空」は既存の `test_layout_scan_code_lookup_does_not_use_known_key_fallback` が確かめている。足りなければそこへ寄せる。
- `LayoutController` の 2 メソッドの単体テストを新規に追加する（`tests/test_layout_controller_scan_code.py`）。`LayoutController` は `app` を受け取るので、`get_current_keyboard_layout` を差し替えるか、最小のスタブの `app` で作る。
  - US TKL 相当（`scan_code` なし）のとき: `resolve_key_name_from_scan_code(41)` が `""`、123 / 121 / 112 も `""`
  - jis.json のとき: 41 / 123 / 121 / 112 → `zenkaku_hankaku` / `muhenkan` / `henkan` / `kana`
  - 自作レイアウト（`KeySpec` の `id="My_Key"`・`scan_code=50`）のとき: 50 → `my_key`（正規化される）
  - `should_debug_special_key_event`:
    - 設定が偽なら偽
    - `up` なら偽
    - jis.json で走査コード 123 の `down` なら真
    - jis.json で走査コード 30 なら偽
    - US TKL で 123 なら偽
    - 走査コードが `None` / 文字列なら偽

### 設計メモ / 制約

- **途中の状態（仕様どおり）**: 本タスクの後も、送信側（`infrastructure/input_gateway.py`）と `domain/key_identifiers.py` には既知の表が残る。task_02 で消す。本タスクでは触らない。
- `get_current_keyboard_layout` の読み直しの挙動は変えない（暫定 45 §3 末尾）。
- `KeyStateManager` / `input_router` は `resolve_scan_code` の関数を受け取るだけなので変更不要。

## 読むファイル

1. `instructions/history/45_special_keys_from_layout_only.md` §3
2. `keyseq/presentation/keyboard_layouts.py:1-30`（import・`KeySpec`）/ :320-352
3. `keyseq/presentation/controllers/layout_controller.py`（編集対象。:1-20 / :170-200 / :355-395 を中心に読む）
4. `tests/test_keyboard_layout_files.py`
5. 手本（テストの差し替え方）: `tests_ui/test_keyboard_window_scan_code.py`

## 含まない

- 既知の表（`domain/key_identifiers.py`）とその他の参照元の削除（task_02）
- 送信・検査・同じキーの判定（task_02）
- レイアウトが変わる前の離し（task_03）
- 正本反映（task_04）
- キーボードUI の取得（phase 61 で済み・`keyboard_window.py` は変えない）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_keyboard_layout_files tests.test_layout_controller_scan_code` が全 pass
- `grep -rn "resolve_key_id_from_scan_code\|is_special_key_name\|SPECIAL_KEY_NAMES" keyseq/presentation` の結果が 0 件
- 既存テストが全 pass: `unittest discover -s tests` / `unittest discover -s tests_ui` / `-m tests.smoke_app`

## 完了条件

- 上記の確認が pass し、**reviewer が採用**していること。
- 実機目視は task_03 でまとめて行う。
