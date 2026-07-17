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

## presentation のフォルダ構成

計画04で **種類別フォルダ**（`controllers/` / `views/`）へ再編し、View 専用 Widget は
`views/full_view/` / `views/compact_view/` の**所有者フォルダ**へ配置した。

```text
keyseq/presentation/
    app.py                     # Tk ルート・生成と配線（組み立て）・View切替・調整役・dialogs向け契約
    ui_vars.py                 # UiVars: View / コントローラ間で共有する Tk 変数ホルダー
    controllers/               # 種類別フォルダ
        config_io_controller.py
        dirty_state.py
        hook_controller.py
        key_capture.py
        keymap_panel_controller.py
        layout_controller.py
        trigger_panel_controller.py
    views/                     # 種類別フォルダ（__init__.py は空のパッケージマーカー）
        menu_bar.py            # build_menu_bar(app) / bind_menu_shortcuts(app)
        status_bar.py          # build_status_area(app, parent)
        full_view/             # 所有者フォルダ
            full_view.py       # FullView: Widget の生成と pack/grid 配置のみ
            hook_frame.py      # FullHookFrame（取得/クリアボタン付き）
            display_frame.py   # FullDisplayFrame
            file_frame.py      # FileFrame
            keymap_box.py      # KeymapBox
            trigger_box.py     # FullTriggerBox（編集ボタン・suppress 付き）
            sequence_box.py    # SequenceBox
        compact_view/
            compact_view.py    # CompactView
            hook_frame.py      # CompactHookFrame（表示のみ）
            display_frame.py   # CompactDisplayFrame
            trigger_box.py     # CompactTriggerBox（一覧のみ）
    config_paths.py            # 以下は presentation 直下（複数種から使われる共有モジュール）
    dialogs.py
    keyboard_layouts.py
    keyboard_window.py
    listbox_utils.py
    theme.py
    tk_keys.py
```

- **FullView と CompactView で Widget は共通化しない**（部品構成・配置が異なるため View ごとに専用 Widget を持つ）。
  クラス名は `Full` / `Compact` 接頭辞で衝突を避ける。
- 各 Widget は `ttk.LabelFrame` を継承し `__init__(self, parent, app)` で生成する。
  Widget からコントローラへの参照は `app.<コントローラ名>` 経由。

---

## 主な責務

### App

- Tk ルートウィンドウ管理（title / geometry / topmost / フォント適用 / 終了処理）
- 生成と配線（各サービス・コントローラの生成。コールバックはラムダで包み、実行時に `self.<コントローラ>.…` を解決）
- View切替（`show_full_view` / `show_compact_view` と geometry の退避・復元）
- 調整役メソッド（キャプチャ相互排他: `toggle_stop_key_capture` / `start_stop_key_capture` / `toggle_toggle_key_capture` / `start_toggle_key_capture`、ダーティ既定解決: `mark_keymap_dirty` / `mark_sequence_dirty`、フラッシュメッセージ、`_sync_control_vars_from_data`）
- dialogs 向け契約（`validate_hotkey` / `_dialog_result` / `_perform_action` / `open_preset_manager`）と、状態依存でパスを詰め替える薄メソッド（`suggest_keymap_set_dialog_path` / `suggest_keymap_set_dialog_dir` / `keymap_set_file_stem`）
- 配線用の薄いヘルパ（`_get_send_guard_count` / `_find_trigger_by_key` / `_find_keymap_target` / `_find_keymap_switch_target_id`）
- 分離JSONの現在の構成セットパス（keymap_set_path）・startup 設定を保持

### UiVars（ui_vars.py）

- View / コントローラ間で共有する **Tk 変数（StringVar / BooleanVar / IntVar 等）のホルダー**。
  App 生成直後に 1 度だけ作られ、差し替わらない（`app.ui_vars.<変数名>` で参照）。
- **`AppState`（application 層）とは別物**。UiVars は Tk に依存する presentation 層の部品であり、
  選択インデックス等のアプリ状態は引き続き `AppState` が持つ。混ぜない。
- Tk 変数はアプリ生存中に差し替わらないため、Widget・コントローラがコンストラクタで受け取って保持してよい。

### コントローラ（controllers/）

計画02で App の責務を以下のコントローラ／ヘルパへ分割し、計画03で **views / dialogs / keyboard_window は
App の委譲メソッドを介さず、コントローラを `app.<名前>`（`app.config_io` / `app.hook` / `app.layout` /
`app.keymap_panel` / `app.trigger_panel` / `app.dirty_tracker` / `app.stop_key_capture` /
`app.toggle_key_capture` / `app.paths`）経由で直接参照する**ようにした（App から委譲ボイラープレートを削除）:

- ConfigPaths（config_paths.py ※presentation 直下）: 設定ファイルの配置規約とパス解決
- DirtyStateTracker（controllers/dirty_state.py）: 未保存状態の一元管理
- SingleKeyCaptureController（controllers/key_capture.py）: 停止キー/トグルキーのキャプチャ
- ConfigIoController（controllers/config_io_controller.py）: 構成セット・個別JSONの保存/読込フロー
- LayoutController（controllers/layout_controller.py）: キーボードレイアウトと KeyboardWindow 管理
- KeymapPanelController（controllers/keymap_panel_controller.py）: キーマップ管理パネル
- TriggerPanelController（controllers/trigger_panel_controller.py）: トリガー/シーケンスパネルとステータス表示
- HookController（controllers/hook_controller.py）: フック開始/停止・サスペンド・入力イベント入口
- listbox_utils.py（presentation 直下）: Listbox 選択ヘルパ（モジュール関数）

### View → コントローラのウィジェット登録（計画04 W5）

View が App へウィジェット参照を生やす逆流（`app.hook_toggle_btn = ...`）は廃止した。現在は次の2方式:

1. **登録方式（複数 View に同種ウィジェットがあるもの）** — Widget が生成時に自分をコントローラへ登録し、
   同期メソッドは登録済みウィジェットを走査する（走査順は登録順 = full → compact）:
   - `HookController.register_hook_buttons(hook_btn, trigger_btn)` ← FullHookFrame / CompactHookFrame
   - `LayoutController.register_layout_combo(combo)` ← FullDisplayFrame / CompactDisplayFrame
   - `TriggerPanelController.register_trigger_list(listbox)` ← FullTriggerBox / CompactTriggerBox
   - `SingleKeyCaptureController.register_widgets(entry, capture_btn, clear_btn)` ← FullHookFrame（キャプチャUIは Full のみ）
2. **所有 Widget の属性（単一 View にしかないもの）** — コントローラからは
   `app.full_view.keymap_box.keymap_listbox` のように **App → View → Widget のパス**で辿る
   （`app.full_view.sequence_box.run_to_end_delay_entry` 等）。

### ConfigService

- 単一JSON互換の読込/書出
- split構成の読込/保存
- config配下は相対、外部は絶対のパス保存ルールを扱う
- trigger_set と sequence の分離保存・読込を扱う
- keymap / trigger_set / sequence の個別ファイル保存・読込を扱う

---

## UI構成

FullView / CompactView は **Widget の生成と pack/grid 配置のみ**を持つ組み立てクラス。
各 LabelFrame は View 専用の Widget クラスへ分割されている（計画04 W3 / W4）。

### FullView（views/full_view/）
- 編集機能 / トリガー管理 / シーケンス管理 / keymap・trigger_set・sequence の個別保存ボタン
- 構成 Widget:
  - FullHookFrame（hook_frame.py）: フック開始/停止・通常トリガー切替・停止/トグルキーの表示と**取得・クリア**
  - FullDisplayFrame（display_frame.py）: 常に手前・省略表示へ・キーボードUI・レイアウト選択
  - FileFrame（file_frame.py）: 保存 / 別名で保存 / 読込 / 新規作成
  - KeymapBox（keymap_box.py）: キーマップ一覧と管理ボタン（追加・変更・削除・選択・保存系）
  - FullTriggerBox（trigger_box.py）: トリガー一覧・編集ボタン・suppress チェック
  - SequenceBox（sequence_box.py）: 出力シーケンス一覧・アクション操作・連続実行と間隔(ms)

### CompactView（views/compact_view/）
- 簡易表示 / フック制御
- 構成 Widget:
  - CompactHookFrame（hook_frame.py）: フック開始/停止・通常トリガー切替・停止/トグルキーの**表示のみ**
  - CompactDisplayFrame（display_frame.py）: 常に手前・フルに戻す・キーボードUI・レイアウト選択
  - CompactTriggerBox（trigger_box.py）: トリガー一覧のみ

### メニュー / ステータス
- menu_bar.py: `build_menu_bar(app)`（ファイル / 設定メニュー）と `bind_menu_shortcuts(app)`（Ctrl 系アクセラレータ）。
  **build と bind は別関数**（フォントサイズ変更時はメニューのみ再構築し、バインドは再実行しない）。
- status_bar.py: `build_status_area(app, parent)`（「ステータス」欄 + 下部ステータスバー: ファイル状態 / 一時メッセージ）

---

## フック関連

- keyboard によるグローバルフック
- suppress=True 使用
- UI操作中は停止

---

## 注意

- UI更新は必ず UIスレッドで行う（after使用）
- フック処理はUIと分離される
