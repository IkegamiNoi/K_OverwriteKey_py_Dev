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
        config_io/             # 構成セット・個別JSONの保存/読込を6クラスへ分割（所有者フォルダ・計画04）
            keymap_set_io.py   # KeymapSetIo: 構成セット（keymap_set）+ 専用ヘルパ
            startup_io.py      # StartupIo: 起動設定（startup.json）read/write
            io_dialogs.py      # IoDialogs: 共有ダイアログヘルパ（保存パス衝突 / ラベル連動）
            keymap_file_io.py  # KeymapFileIo: keymap 個別 JSON
            trigger_set_file_io.py  # TriggerSetFileIo: trigger_set 個別 JSON
            sequence_file_io.py     # SequenceFileIo: sequence 個別 JSON
            child_save_rows.py      # 子ファイルの共有状況判定と行モデル（判定名 / 表示文言 / 既定アクション）
            child_save_dialog.py    # ChildSaveDialog: 子一覧 / 依存確認 / 再計算先の上書き確認
            child_save_plan.py      # 行の選択・確定エントリ・既定規則から保存計画を組み立てる
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
    startup_settings.py        # load_startup_settings: startup.json 読込+型ガード+正規化（config_service 直依存・未知キー全保持・UI通知は on_read_error 注入）
    theme.py                   # フォント/テーマ適用 + coerce_font_delta（フォント差分 -3..+3 正規化の唯一点）
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
  - `validate_hotkey` は**検証ロジックを持たず** `HotkeyService.validate`（application）への**薄い委譲**（実体は下記 HotkeyService / `domain/hotkey.py`）。dialogs 契約維持のため残す
- 配線用の薄いヘルパ（`_get_send_guard_count` / `_find_trigger_by_key` / `_find_keymap_target` / `_find_keymap_switch_target_id`）
- 起動時に設定ディレクトリ骨格（`config/user/{keymap_sets,keymaps,trigger_sets,hotkey_presets,sequences}`）を
  `config_service.ensure_split_config_dirs` で一括作成する。**`config/config.json` は起動時に書かない**
  （最初に設定が永続化された時点で作成。keymap_set 保存 / フォント変更 / 起動時読込先の指定）
- 分離JSONの現在の構成セットパス（keymap_set_path）・startup 設定を保持
  - `keymap_set_path` は「新規作成 / Import 成功 / 起動時に stored セットが読めない」の 3 経路で**空**になる
    （＝ファイルなし。次の保存が別名保存になる。仕様は `spec_detail/data_schema.md` §5.4）
  - 起動設定の**読込ロジックは持たず** `startup_settings.load_startup_settings`（presentation・`config_service` 直依存）へ委譲し、
    UI 通知（`messagebox`）だけを `on_read_error` ラムダで注入する（`__init__` 内）。フォント差分の正規化は `theme.coerce_font_delta`
- フォントサイズ設定（`_ui_font_delta_pt` を App 保持）: `_apply_font_delta`（状態更新・`apply_global_theme`・`startup_io.write_startup` 永続化）と
  `set_ui_font_delta`（メニュー再構築 `build_menu_bar` のみ + フラッシュ通知）に分割。差分なしは早期 return（`bind_menu_shortcuts` は呼ばない）

### UiVars（ui_vars.py）

- View / コントローラ間で共有する **Tk 変数（StringVar / BooleanVar / IntVar 等）のホルダー**。
  App 生成直後に 1 度だけ作られ、差し替わらない（`app.ui_vars.<変数名>` で参照）。
- **App private を直読みしない**: `ui_font_delta_var` の初期値は `__init__(self, master, ui_font_delta_pt: int)` の
  引数で受け取る（`master._ui_font_delta_pt` の直読みを廃止）。他の初期値は `master.data.get(...)` から取得。
- **`AppState`（application 層）とは別物**。UiVars は Tk に依存する presentation 層の部品であり、
  選択インデックス等のアプリ状態は引き続き `AppState` が持つ。混ぜない。
- Tk 変数はアプリ生存中に差し替わらないため、Widget・コントローラがコンストラクタで受け取って保持してよい。

### コントローラ（controllers/）

計画02で App の責務を以下のコントローラ／ヘルパへ分割し、計画03で **views / dialogs / keyboard_window は
App の委譲メソッドを介さず、コントローラを `app.<名前>`（`app.keymap_set_io` / `app.hook` / `app.layout` /
`app.keymap_panel` / `app.trigger_panel` / `app.dirty_tracker` / `app.stop_key_capture` /
`app.toggle_key_capture` / `app.paths`）経由で直接参照する**ようにした（App から委譲ボイラープレートを削除）:

- ConfigPaths（config_paths.py ※presentation 直下）: 設定ファイルの配置規約とパス解決
- DirtyStateTracker（controllers/dirty_state.py）: 未保存状態の一元管理
- SingleKeyCaptureController（controllers/key_capture.py）: 停止キー/トグルキーのキャプチャ
- config_io/（controllers/config_io/）: 構成セット・個別JSONの保存/読込フローを**6クラスへ分割**（計画04で `config_io_controller.py` を廃止）。App が各クラスを直接公開し、`app.<名前>.<method>` で参照する:
  - KeymapSetIo（keymap_set_io.py = `app.keymap_set_io`）: 構成セット（keymap_set）の new/save/save_as/load/import/export/restore + 起動構成セット指定・読込データのUI適用
    - 新規作成は `keymap_set_path` を空にし、`save_keymap_set` は空パスなら `save_as` へ委譲する（別名保存の初期名は `keymap_set.json`）。Import 成功時は**無条件で**空にする
    - 保存成功時は `config_service.save_runtime_data` が startup payload ごと `config/config.json` を書き直し、`keymap_set_path` が保存先へ更新される（`write_startup` は経由しない。「起動時に読むJSONを設定」メニュー側とは**別経路で同じキーを書く**点に注意）
  - StartupIo（startup_io.py = `app.startup_io`）: 起動設定（`config/config.json`。旧 `settings/startup.json` は読込フォールバックのみ）の read/write
    - 起動時は stored `keymap_set_path` が実在すれば読み込み、無い / 読めない場合は**無言で空データ起動**し `keymap_set_path` を空にする
  - IoDialogs（io_dialogs.py = `app.io_dialogs`）: 共有ダイアログヘルパ（保存パス衝突解決 / ラベル連動ファイル名）
  - KeymapFileIo（keymap_file_io.py = `app.keymap_io`）: keymap 個別 JSON の保存/読込
  - TriggerSetFileIo（trigger_set_file_io.py = `app.trigger_set_io`）: trigger_set 個別 JSON の保存/読込
  - SequenceFileIo（sequence_file_io.py = `app.sequence_io`）: sequence 個別 JSON の保存/読込
  - **子ファイル保存（Phase β。仕様は `spec_detail/data_schema.md` §5.8）**: 保存計画は
    **presentation が決定し application が実行する**（application に tkinter 依存を持ち込まない）
    - child_save_rows.py: 保存先の `_parent_refs` と現在の上位から**共有状況を判定**し、行モデル
      （判定名 / 表示文言 / 既定アクション）を組み立てる。**分岐は判定名で行い、表示文言では分岐しない**
    - ChildSaveDialog（child_save_dialog.py = `app.child_save_dialog`）: 子一覧ダイアログ・
      依存確認（4 択）・再計算先の上書き確認
    - child_save_plan.py: 一覧の選択 > 確定エントリ > 既定規則（保存先に実体があれば保存しない /
      無ければ保存）の優先順位で `SavePlan` を組み立てる
    - KeymapSetIo が上記を束ね、`config_service.save_runtime_data` へ計画を渡す
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
- **子ファイルの保存計画（`application/save_plan.py` の `SavePlan`）を実行する**
  （仕様は `spec_detail/data_schema.md` §5.8）:
  - 保存対象の解決（`resolve_child_save_targets`）・依存関係の検出・計画の事前検証・
    **書き込み順序による best-effort 保証**（子 → 上位 → keymap_set → 起動設定。
    上位の索引を新パスへ進める前に子の成功を確認する。トランザクション / ロールバックは持たない）
  - `_parent_refs` の読み書き（best-effort マージ）とパス同一性判定（`canonical_path` /
    `is_path_within` の 2 本のみを使う。正規化文字列は比較専用）
  - **計画を決めるのは presentation 側**（`config_io/child_save_*`）。ConfigService は
    渡された計画を実行するだけで、ダイアログを持たない

### HotkeyService（application/hotkey_service.py）/ domain/hotkey.py

hotkey 文字列の検証（文法検査 + キー名検証 + 正規化）を担う。フェーズ 02_hotkey_validation で
App から層移設した（挙動不変）。公開契約は `(エラーメッセージ, 正規化hotkey)`。

- **`domain/hotkey.py::validate_hotkey_syntax(hotkey)`** — 純粋な**文法検査**（空 / `+` 前後空 / 重複）と
  正規化（trim + 小文字化 + `+` 連結）。標準ライブラリのみ・注入なし・クラスなし。
  `(error, normalized, parts)` を返す（`parts` は application がキー名検証に使う内部インターフェース）。
- **`HotkeyService.validate(hotkey)`** — domain の文法検査を呼び、エラーが無ければ各キーに
  キー名検証を適用する**合成**役。キー名検証は `validate_key_name: Callable` を DI で受け取る
  （`App` が `input_gateway.validate_key_name` を注入）。文法エラー優先の順序を保つ。
- 呼び出し側: `App.validate_hotkey`（dialogs 経由・薄い委譲）と `ActionExecutor`（実行時・注入経由）。
  **`ActionExecutor` は `App.validate_hotkey` ではなく `HotkeyService.validate` を注入で受け取る**
  （application → presentation の層の逆転を解消済み）。

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
