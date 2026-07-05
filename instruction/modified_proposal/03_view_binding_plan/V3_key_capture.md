# V3: キーキャプチャ系の付け替えと委譲削除

- 実施日: 2026-07-06

## 付け替えた参照元

- **views.py**: `command=app.clear_stop_key`→`command=app.stop_key_capture.clear`、`command=app.clear_toggle_key`→`command=app.toggle_key_capture.clear`。
- **app.py 本体**（`show_compact_view` / `_is_menu_shortcut_enabled` の 2 箇所）: `getattr(self, "_capturing_stop_key", False) or getattr(self, "_capturing_toggle_key", False)`→`self.stop_key_capture.capturing or self.toggle_key_capture.capturing`。
  - `getattr(..., False)` の防御は、コントローラが `__init__` で必ず生成され `capturing` 属性を初期化するため不要（挙動同一）。計画 §V3 の指示どおり直接参照へ。
- **views.py のキャプチャ開始ボタン** `command=app.toggle_stop_key_capture` / `toggle_toggle_key_capture` は V1 で公開名化済み。App 調整役のため本項目では変更なし。

## 削除した App 委譲・プロパティ（計 6）

`_capturing_stop_key`（prop） / `_capturing_toggle_key`（prop） / `_stop_stop_key_capture` / `_stop_toggle_key_capture` / `clear_stop_key` / `clear_toggle_key`。

- `_stop_stop_key_capture` / `_stop_toggle_key_capture` は tests_ui が V1 で `app.stop_key_capture.stop(...)` へ移行済みのため外部呼び出しなし。削除。
- キャプチャ系のキープレスハンドラ（`_on_stop_key_capture_keypress` 等）は App に存在せず（SingleKeyCaptureController が内部保持）、削除対象なし。

## App に残した調整役（削除禁止・§1.4）

`toggle_stop_key_capture` / `start_stop_key_capture` / `toggle_toggle_key_capture` / `start_toggle_key_capture`（片方を止めてから他方を開始する相互排他ロジック）。

## 検証結果

- 削除対象の残存参照: 0 件
- compile OK / tests 59 OK / tests_ui 9 OK / SMOKE OK
- **手動確認（計画02 S5 の 5 項目: 取得→F9確定 / Escキャンセル / トグル側取得 / 重複エラー / クリア）**: GUI 操作のため自動環境で実施不可。標準検証で代替、実機確認は要ユーザー。
