# コード構造

## エントリーポイント

main.py

- App を起動する

---

## アーキテクチャ

オニオンアーキテクチャ構成

presentation
- UI（tkinter）
- イベント処理

application
- ユースケース
- 実行制御

domain
- トリガー
- アクション
- ロジック

infrastructure
- keyboard フック
- JSON入出力

---

## 主な責務

### App

- Tk ルートウィンドウ・View切替（Full / Compact）・メニュー
- 各コントローラの生成と配線（コールバックはラムダで包み、実行時に `self.<コントローラ>.…` を解決）
- 調整役メソッド（キャプチャ相互排他: `toggle_stop_key_capture` / `start_stop_key_capture` / `toggle_toggle_key_capture` / `start_toggle_key_capture`、ダーティ既定解決: `mark_keymap_dirty` / `mark_sequence_dirty`）
- dialogs 向け契約（`validate_hotkey` / `_dialog_result`）と、状態依存でパスを詰め替える薄メソッド（`suggest_keymap_set_dialog_path` / `suggest_keymap_set_dialog_dir` / `keymap_set_file_stem`）
- 分離JSONの現在の構成セットパス（keymap_set_path）・startup 設定を保持

計画02で App の責務を以下のコントローラ／ヘルパへ分割し、計画03で **views / dialogs / keyboard_window は
App の委譲メソッドを介さず、コントローラを `app.<名前>`（`app.config_io` / `app.hook` / `app.layout` /
`app.keymap_panel` / `app.trigger_panel` / `app.dirty_tracker` / `app.stop_key_capture` /
`app.toggle_key_capture` / `app.paths`）経由で直接参照する**ようにした（App から委譲ボイラープレートを削除）:

- ConfigPaths（config_paths.py）: 設定ファイルの配置規約とパス解決
- DirtyStateTracker（dirty_state.py）: 未保存状態の一元管理
- SingleKeyCaptureController（key_capture.py）: 停止キー/トグルキーのキャプチャ
- ConfigIoController（config_io_controller.py）: 構成セット・個別JSONの保存/読込フロー
- LayoutController（layout_controller.py）: キーボードレイアウトと KeyboardWindow 管理
- KeymapPanelController（keymap_panel_controller.py）: キーマップ管理パネル
- TriggerPanelController（trigger_panel_controller.py）: トリガー/シーケンスパネルとステータス表示
- HookController（hook_controller.py）: フック開始/停止・サスペンド・入力イベント入口
- listbox_utils.py: Listbox 選択ヘルパ（モジュール関数）

### ConfigService

- 単一JSON互換の読込/書出
- split構成の読込/保存
- config配下は相対、外部は絶対のパス保存ルールを扱う
- trigger_set と sequence の分離保存・読込を扱う
- keymap / trigger_set / sequence の個別ファイル保存・読込を扱う

---

## UI構成

### FullView
- 編集機能
- トリガー管理
- シーケンス管理
- keymap / trigger_set / sequence の個別保存ボタン

### CompactView
- 簡易表示
- フック制御

---

## フック関連

- keyboard によるグローバルフック
- suppress=True 使用
- UI操作中は停止

---

## 注意

- UI更新は必ず UIスレッドで行う（after使用）
- フック処理はUIと分離される
