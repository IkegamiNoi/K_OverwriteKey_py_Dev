# idea_55_taskbar_status_icon.md

## 概要

**タスクバーのアイコンだけでアプリの状態（ON / OFF / 一時停止）が分かるようにする**。
メイン窓のアイコンを状態ごとに差し替え、**右上に色＋形の印**（ON=緑● / OFF=赤■ / 一時停止=黄‖）を付ける。
**新規依存なし**（tkinter の `iconphoto` のみ）。

## 起票経緯（2026-10-31）

ユーザー要望。「IME の横（通知領域）に出す」案と「アイコン右上にカラーの印」案を比較し、後者を採用方向とした。
通知領域案は、Windows 11 で新しいアイコンが既定で「^」の中に隠れること・新規依存（`pystray` 等）か
ctypes の API 直呼びが要ること・常駐化（窓を閉じても裏で動く）の予定がないことから見送り。
Windows 標準のオーバーレイアイコン（`ITaskbarList3::SetOverlayIcon`）は印が右下固定のため不採用。

## 現状

- 窓のアイコンは未設定（`iconphoto` / `iconbitmap` の使用 0 件・アイコン素材なし）。Tk 既定の羽アイコン。
- メイン窓は通常の窓でタスクバーにボタンが出る（`overrideredirect` は補助窓のみ:
  `keyseq/presentation/dialogs/grid_editor_window.py:52` ・ `hover_tooltip.py:45` ・ `screen_grid/grid_overlay_window.py:32`）。
- 状態の出所: `keyseq/presentation/controllers/hook_controller.py:87-109`
  （`hook_active` = フック ON/OFF / `custom_input_enabled` = キーマップ有効・一時停止）。
  文言は `keyseq/presentation/hook_button_texts.py`（「開始（フックON）」「停止（フックOFF）」「キーマップ一時停止」「キーマップ再開」）。
- 正本の関連節: `instructions/common/spec_detail/features.md` / `key_input.md` / `ui_terms.md`（フック・キーマップ一時停止の用語）。

## 提案（方向性・要設計）

- 状態の対応（案）: フック OFF → 赤■ / フック ON かつキーマップ有効 → 緑● / フック ON かつキーマップ一時停止 → 黄‖。
- アイコン画像: 基本アイコン＋右上の印を 3 種用意（16px でも判別できる大きさ〔アイコンの約 1/3〕・白フチ）。
  素材ファイルを置くか、起動時に `PhotoImage` で描くかは要設計（後者なら素材管理が不要）。
- 差し替えの契機: `sync_hook_toggle_buttons` / `sync_trigger_toggle_buttons` と同じタイミングで反映（UI スレッド）。
- 要検討:
  - UI 編集中のフック停止（`hook_suspend_count`）中に何を表示するか（OFF 扱い / 直前の状態のまま）。
  - 実行の一時停止（`run_to_end_paused` 等・シーケンス側）は今回の「一時停止」に含めない想定でよいか。
  - 基本アイコンのデザイン（現状は Tk 既定。アプリ独自のアイコンも同時に作るか）。
  - ダイアログ等の子窓のアイコンも揃えるか（`iconphoto(True, …)` で既定にするか）。

## 想定スコープ

- 含む: メイン窓（と必要なら子窓）のアイコン差し替え・状態との結線・tests_ui での最小確認。
- 含まない: 通知領域（トレイ）アイコン・常駐化・右クリックメニュー。
- 影響レイヤ: presentation のみ（application / domain は無変更の見込み）。
- 仕様変更: あり（features.md に表示仕様を追加）。局所的なら直接改訂、表示状態の定義を詰めるなら暫定仕様先行。
