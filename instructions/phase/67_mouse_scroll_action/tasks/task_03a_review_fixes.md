# task_03a_review_fixes

## 目的

task_03 の完了判定前レビュー（ユーザー確定 2026-10-21・推奨どおり）のうちコードの修正分。
暫定 50 §3（`amount` の欠落はエラー）・§5（不正な値は直させる）に合わせ、ダイアログが量の欠けた行を既定値で埋めないようにする。あわせて `/refactor_check` M6（domain の定数と同じ直値）と deep-reviewer L4・L5。
**presentation 限定（`action_mouse_scroll_fields.py` と tests_ui）・domain / application / infrastructure は不変・スキーマ不変。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/dialogs/action_mouse_scroll_fields.py`

1. **量の欠けた既存行（Codex 指摘）**: `load(action)` で `amount` のキーが無いときは、**選んだ単位の欄を空文字にする**（単位が未選択なら両方の欄を空）。選ばなかった方の欄は既定値のまま。これで OK は `parse_mouse_scroll` の「量は整数で…」で拒否される（`action_dialog.py` の OK の流れは変えない）
2. **M6**: 直値を `keyseq.domain.mouse_scroll` の定数へ置き換える — `"notch"` / `"delta"` → `UNIT_NOTCH` / `UNIT_DELTA`・`"mouse_scroll"` → `ACTION_TYPE_MOUSE_SCROLL`・既定の `"1"` → `str(DEFAULT_NOTCHES)`・既定の `"120"` → `str(WHEEL_DELTA)`・ラジオの文言の 120 も `WHEEL_DELTA` から組み立てる・向きの対応表は `DIRECTIONS` の順と一致させる（表示名の対応は残してよい）
3. **L4**: `_parsed_amount` の末尾の同じ値を返す分岐を 1 つにまとめる

### テスト（`tests_ui/test_action_dialog_mouse_scroll.py` に追加）

- 量の欠けた行（notch / delta / 単位なし / 不正な単位）を開くと対象の欄が空・ラベルだけ変えて OK すると拒否され `_dialog_result` が設定されない（messagebox は既存テストと同じ方法で差し替え）
- L5: ①mouse_click の取得ボタンから取得を始めると（`_set_mouse_capture_state("disabled")`）mouse_scroll の取得ボタンも disabled ②取得中に種類を mouse_scroll へ切り替えても disabled のまま ③取得中に「座標を指定する」を OFF → ON にしても disabled のまま ④取得の終了（`_set_mouse_capture_state("normal")`）でチェック ON なら normal
- state の比較は `str(widget.cget("state"))`（Tcl の index オブジェクトのため）

## 読むファイル

1. `keyseq/presentation/dialogs/action_mouse_scroll_fields.py`（全体）
2. `keyseq/domain/mouse_scroll.py:1-25`（定数）
3. `keyseq/presentation/dialogs/action_dialog.py:330-345`（`_set_mouse_capture_state`）・`:455-470`（`_sync_capture_ui`）
4. `tests_ui/test_action_dialog_mouse_scroll.py`（全体）

## 含まない

- 正本の文言（メインが直接・task_03）/ L6・L7（保留）/ 他の種類の欄

## 確認

- `compileall` clean / `unittest discover -s tests` 全 pass / `unittest discover -s tests_ui` 全 pass / smoke pass

## 完了条件

- 上記確認 pass・**reviewer 採用**・実機目視は不要（task_03 で OK 済み・挙動の変更は量の欠けた行のダイアログだけ）
