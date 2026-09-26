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
        config_io/             # 構成セット・個別JSONの保存/読込を7クラスへ分割（所有者フォルダ・計画04）
            keymap_set_io.py   # KeymapSetIo: 構成セット（keymap_set）+ 専用ヘルパ
            startup_io.py      # StartupIo: 起動設定（startup.json）read/write
            hotkey_presets_io.py  # HotkeyPresetsIo: hotkey プリセットの即時保存（グローバル / 個別。唯一の書き手）+ 拒否表示 / 上書き確認の 3 択モーダル
            io_dialogs.py      # IoDialogs: 共有ダイアログヘルパ（保存パス衝突 / ラベル連動）
            keymap_file_io.py  # KeymapFileIo: keymap 個別 JSON
            trigger_set_file_io.py  # TriggerSetFileIo: trigger_set 個別 JSON
            sequence_file_io.py     # SequenceFileIo: sequence 個別 JSON
            child_save_rows.py      # 子ファイルの共有状況判定と行モデル（判定名 / 表示文言 / 既定アクション）
            child_save_dialog.py    # ChildSaveDialog: 子一覧 / 依存確認 / 再計算先の上書き確認
            child_save_plan.py      # 行の選択・確定エントリ・既定規則から保存計画を組み立てる
            reference_cleanup_io.py # ReferenceCleanupIo: 参照元の掃除のフロー（保存確認→検査→確認→除去→通知）
            orphan_sweep_io.py      # OrphanSweepIo: 孤児ファイルの棚卸しのフロー（保存確認→走査→棚卸しダイアログ→確認→隔離→通知）+ 走査先設定の保存（→ StartupIo）
            quarantine_manage_io.py # QuarantineManageIo: 隔離の管理のフロー（一覧→単位選択→復元 / 削除の確認→実行→通知）
            keymap_set_history_io.py # KeymapSetHistoryIo: 読み込み履歴の記録の単一の口 record() + 履歴ダイアログの開閉と編集 6 メソッド（phase 27・`data_schema.md` §5.12）
        dirty_state.py
        button_width.py        # apply_fixed_button_width: TButton のフォントで文言を測り、ボタンの width を最大文言幅で固定（phase 19）
        hook_controller.py
        key_capture.py
        keymap_panel/          # キーマップ管理（所有者フォルダ・phase 34 task_09）
            __init__.py        # KeymapPanelController の再輸出
            keymap_panel_controller.py  # KeymapPanelController: 一覧・選択 = アクティブ化・編集・削除・グレー表示
            keymap_add_flow.py # KeymapAddFlow: キーマップの追加フロー（切替キー未設定の既存への設定 → 追加ダイアログ・読込分の追加）
        layout_controller.py
        pane_layout/           # フル表示の幅配分（所有者フォルダ・phase 18）
            __init__.py        # PaneLayoutController の再輸出
            pane_layout_controller.py  # PaneLayoutController: 境界線ドラッグ・最小幅・収まらない場合の適用・幅の保存と復元・最小の高さ（phase 20）
            pane_measure.py    # measure_min_widths: 各枠の最小幅 / measure_header_window_width: ヘッダの要求幅から求めたウィンドウ幅を実ウィジェットから測る / measure_window_min_height: 最小の高さ（ウィンドウの要求高さ・一時メッセージは 1 行分）
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
    dialogs/                   # ダイアログ群（計画07 項目2 で dialogs.py 1026 行から分割・1クラス1ファイル）
      __init__.py              # 公開面（明示列挙の再輸出のみ。tk / messagebox は持たない）
      action_dialog.py         # ActionDialog（+ キーキャプチャ）
      preset_manager.py        # PresetManagerDialog + format_preset_manager_source_labels（純関数）
      preset_dialog.py         # PresetDialog（プリセットの追加・編集）
      trigger_dialog.py        # TriggerDialog
      keymap_edit_dialog.py    # KeymapEditDialog（phase 34: 任意の検証コールバック `validate` を受け、False なら閉じない＝追加フローで使う）
      layout_delete_dialog.py  # LayoutDeleteDialog
      escape_close.py          # bind_escape_close（Esc に別用途がある 3 ダイアログの Escape 結線。印はクロージャに持つ・提案書 11 / phase 28 task_07）
      orphan_sweep_dialog.py   # OrphanSweepDialog（棚卸しの入口・走査先一覧の編集。保存は OrphanSweepIo → StartupIo）
      quarantine_manage_dialog.py  # QuarantineManageDialog（隔離の管理・実行単位のリスト選択 + 復元 / 削除ボタン）
      reference_cleanup_dialog.py  # ReferenceCleanupDialog（確認 1 枚・読み取り専用。header / run_label で文言とボタンを引数化し、掃除 / 隔離 / 復元 / 削除で再利用）
      keymap_set_history_dialog.py # KeymapSetHistoryDialog（読み込み履歴・**リポジトリ唯一の ttk.Treeview**〔2 列 / 名前列は stretch=False〕・操作のたびに永続化済みの履歴を読み直して再描画）+ CategoryChooserDialog（コピー先の分類選択・同ファイル内のネストした子）
    keyboard_layouts.py
    keyboard_window.py
    listbox_utils.py
    modal.py                   # grab_modal: モーダル化と破棄時の grab 復元（dialogs/ と controllers/config_io/ の両方から使う）/ 最小化中の grab 預かりと復元時のフォーカス復帰
    reference_cleanup_text.py  # 参照元の掃除の提示テキスト整形（純関数・tkinter 非依存）
    pane_width_rules.py        # フル表示の幅配分の純関数（保存値の検証・最小幅・可動範囲・収まらない場合の最終値〔ヘッダ幅込み〕・ドラッグ後の最小幅・既定幅と 780 基準・起動時の保存値更新の判定。tkinter 非依存）
    button_width_rules.py      # fixed_button_width_chars: 文言幅の最大 ÷ 「0」1 文字の幅（`font.measure("0")`）の切り上げ（ttk の文字数単位。純関数・phase 19）
    hook_button_texts.py       # フックの枠の切替ボタンの文言とキーボード選択のドロップダウン幅の定数（views / controllers の双方から参照する中立モジュール・import なし）
    orphan_sweep_text.py       # 孤児ファイルの棚卸しの提示テキスト整形（警告 / 候補一覧 / 隔離結果。純関数）
    quarantine_manage_text.py  # 隔離の管理の提示テキスト整形（単位一覧 / 復元・削除の計画と結果。純関数）
    keymap_set_history_text.py # 読み込み履歴の表示文言（ノード名・ボタン文言・確認文・失敗理由。純関数と定数のみ）
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
- View切替（`show_full_view` / `show_compact_view` と geometry の退避・復元）。`show_full_view` は表示内容の更新（選択同期・シーケンス一覧・ステータス）を済ませてから末尾で `pane_layout.on_full_view_shown()` を呼ぶ（最小の高さを 1 行のステータスで測るため・phase 20）
- 調整役メソッド（キャプチャ相互排他: `toggle_stop_key_capture` / `start_stop_key_capture` / `toggle_toggle_key_capture` / `start_toggle_key_capture`、ダーティ既定解決: `mark_keymap_dirty` / `mark_sequence_dirty`、フラッシュメッセージ、`_sync_control_vars_from_data`）
- hook キーの個別指定（`spec_detail/data_schema.md` §5.9）: `toggle_hook_keys_individual`（Var → data + dirty +
  ON→OFF で個別値を退避 / OFF→ON で復元・退避が無ければ両キーを `""`。フラグを data へ書いた**後**に
  `apply_global_hook_key_defaults` を呼ぶ）と `discard_retained_hook_keys`。
  退避先は **App の `_retained_hook_keys`**（`app.data` に持たないためスキーマ・保存経路に影響しない）。
  data → Var の同期は `_sync_control_vars_from_data` の 1 本（**ここに退避の破棄を入れない**）
- hotkey プリセット（`spec_detail/data_schema.md` §5.10）: `save_hotkey_presets(presets, *,
  individual=None, loaded_presets=None, on_overwrite_conflict=None) -> bool` が確定点。
  **書き込み前の判定はここに 1 本化されている**（順序は §5.10.3 のとおり
  **保存先算出〔`resolve_hotkey_presets_save_path`〕→ 拒否判定〔`individual_hotkey_presets_save_rejection_reason`〕
  → 上書き確認〔`describe_individual_hotkey_presets_overwrite`〕→ `hotkey_presets_io.write_presets`**）。
  **判定は application・モーダルは presentation**（`on_overwrite_conflict` は
  `"overwrite" / "adopt" / "cancel"` を返すコールバックで、**`overwrite` 以外は書かずに `False`**）。
  **成功したときだけ** `app.data` へ反映する（`PresetManagerDialog.on_ok` は戻り値が真のときだけ閉じる）。
  **プリセットの内容編集は keymap_set を dirty にしない**が、
  **`hotkey_presets_path` の値が変わったとき / 個別フラグを切り替えたときは dirty にする**（§5.10.3）
  - 切替 UI は `PresetManagerDialog`（`dialogs/preset_manager.py`）。
    「この構成セット専用にする」チェックと保存先表示を持ち、
    **トグルでの一覧の読み直し（`_reload_presets_for_individual_toggle`）・破棄確認・
    OFF で開いた時点の一覧確定・「既存を読み込む」での差し替え**は**すべてダイアログ内の表示**に閉じる。
    **runtime へ反映するのは OK のときだけ**（§5.8.8 の P1。プリセット単独の注入 API は作らない）。
    **破棄確認の比較基準（直近に読み込んだ一覧）も差し替え時に更新する**
    （更新し忘れると「既存を読み込む」の後の OK で確認が再発する）
- dialogs 向け契約（`validate_hotkey` / `_dialog_result` / `open_preset_manager`）・`_perform_action`（`SequenceRunner` へ注入。executor の戻り値を返す・phase 31）と、状態依存でパスを詰め替える薄メソッド（`suggest_keymap_set_dialog_path` / `suggest_keymap_set_dialog_dir` / `keymap_set_file_stem`）
  - `validate_hotkey` は**検証ロジックを持たず** `HotkeyService.validate`（application）への**薄い委譲**（実体は下記 HotkeyService / `domain/hotkey.py`）。dialogs 契約維持のため残す
- 配線用の薄いヘルパ（`_get_send_guard_count` / `_find_trigger_by_key` / `_find_keymap_target` / `_find_keymap_switch_target_id`）
- 起動時に設定ディレクトリ骨格
  （`config/user/{keymap_sets,keymaps,trigger_sets,hotkey_presets,hotkey_presets/global,sequences}`）を
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
- `hook_keys_individual_var`（BooleanVar）は **full / compact が同一インスタンスを共有**する
  （compact 側は `state="disabled"` の表示専用）。

### コントローラ（controllers/）

計画02で App の責務を以下のコントローラ／ヘルパへ分割し、計画03で **views / dialogs / keyboard_window は
App の委譲メソッドを介さず、コントローラを `app.<名前>`（`app.keymap_set_io` / `app.hook` / `app.layout` /
`app.keymap_panel` / `app.trigger_panel` / `app.dirty_tracker` / `app.stop_key_capture` /
`app.toggle_key_capture` / `app.paths`）経由で直接参照する**ようにした（App から委譲ボイラープレートを削除）:

- ConfigPaths（config_paths.py ※presentation 直下）: 設定ファイルの配置規約とパス解決
- DirtyStateTracker（controllers/dirty_state.py）: 未保存状態の一元管理（phase 34: trigger_set の状態はキーマップ要素の内部キーが正・実体を省略したらアクティブの実体。移行先キーマップの未保存化 `mark_migrated_keymap_dirty`）
- SingleKeyCaptureController（controllers/key_capture.py）: 停止キー/トグルキーのキャプチャ。
  **hook キーへの書き込みは `_apply_key` の 1 本のみ**（capture / clear の双方がここを通る）。
  個別指定 ON = `app.data` 更新 + Var 反映 + dirty / OFF = `startup_io.write_global_hook_keys` で
  config.json を更新し**成功時のみ** `app.data` と Var を確定する。OFF 経路は
  `dirty_tracker.capture_dirty_snapshot` / `restore_dirty_snapshot` を `try`/`finally` で使い、
  例外経路でも keymap_set を dirty にしない（仕様は `spec_detail/data_schema.md` §5.9.4）。
  取得ボタンは `register_widgets` 時と `apply_fixed_button_width()` で最大文言幅に固定する（phase 19）。
  App の `_apply_fixed_button_widths()` が HookController と 2 つのキャプチャの幅を当て直す（`_apply_font_delta` で `apply_global_theme` の後・`pane_layout.on_font_changed()` の前）
- config_io/（controllers/config_io/）: 構成セット・個別JSONの保存/読込フローを**7クラスへ分割**（計画04で `config_io_controller.py` を廃止）。App が各クラスを直接公開し、`app.<名前>.<method>` で参照する:
  - KeymapSetIo（keymap_set_io.py = `app.keymap_set_io`）: 構成セット（keymap_set）の new/save/save_as/load/import/export/restore + 起動構成セット指定・読込データのUI適用
    - 新規作成は `keymap_set_path` を空にし、`save_keymap_set` は空パスなら `save_as` へ委譲する（別名保存の初期名は `keymap_set.json`）。Import 成功時は**無条件で**空にする
    - **全体デフォルトの注入（`config_service.apply_global_defaults`）を呼ぶのは入口台帳の 5 経路**
      （E1 `App.__init__` / E2 `new_config` / E3 `restore_default` / E5 Import /
      E4 起動時の空データフォールバック〔StartupIo〕）。**hook キーとプリセットをこの 1 本で供給する**。
      **runtime を新規化・置換する入口を増やしたらここも足す**（漏れるとその経路だけ供給されない）。
      台帳と供給規則は `spec_detail/data_schema.md` **§5.8.8**（通常読込 L1〜L3 は経由しない /
      再正規化 N1 は供給不要 / **単独注入が残るのは ON→OFF だけ**）
    - **個別値の退避（`app._retained_hook_keys`）の破棄点は 4 箇所**: `save_keymap_set_to` の
      **保存実行の直前**（`save_runtime_data` 呼び出し前）/ `apply_loaded_data_to_ui` の先頭 /
      `new_config` / `restore_default`
    - 保存成功時は `config_service.save_runtime_data` が startup payload ごと `config/config.json` を書き直す（`write_startup` は経由しない）。`startup_entry_loaded`（キーワード専用・既定 False）を `save_runtime_data` → `build_split_save_payloads` → `build_startup_payload` へ渡し、application の `build_startup_payload` が既存の非空文字列かつ読込成功なら `keymap_set_path` を据え置き、それ以外は保存先へ更新する。他キーは従来どおり保存する
  - StartupIo（startup_io.py = `app.startup_io`）: 起動設定（`config/config.json`。旧 `settings/startup.json` は読込フォールバックのみ）の read/write
    - `entry_loaded`（初期 False）は起動エントリの読込成功の事実のみを保持し、更新要否は判定しない。起動読込成功 / 構成セット保存成功 / メニューでの起動対象指定成功の 3 契機で True にする（`write_startup` 自体では変更しない）
    - 起動時は stored `keymap_set_path` が実在すれば読み込み、無い / 読めない場合は**無言で空データ起動**し `keymap_set_path` を空にする
    - `write_startup(data) -> bool`（成功 True / 例外捕捉で False・`showerror` は従来どおり）と
      `write_global_hook_keys(*, stop_key, toggle_key) -> bool`（hook キーの全体デフォルト書き込み）。
      **全体デフォルトを書くのはこの 1 本のみ**。ConfigService 側に read-modify-write な保存 API を
      作らない（`_startup_settings` と config.json が乖離すると次の `write_startup` が hook キーを消す）
    - `write_startup` の保存失敗表示（`showerror`）は `hook.suspend_hook_for_dialog()` → `finally: resume_hook_after_dialog()` で囲む
      （表示中はフック停止。フォント変更・幅の保存など全呼び出し元に効く。phase 18）
  - HotkeyPresetsIo（hotkey_presets_io.py = `app.hotkey_presets_io`）: hotkey プリセットの即時保存。
    `write_presets(presets, *, stored_path) -> bool`（**空文字ならグローバル / 非空なら個別ファイル**。
    成功 True / 例外捕捉で `showerror` + False）。
    **プリセットファイルを書くのはこの 1 本のみ**（保存カスケードは書かない。
    仕様は `spec_detail/data_schema.md` §5.10.3）。
    保存先の**拒否理由の表示**（`show_save_path_rejection`。`reserved_dir` / `global_conflict` の 2 文言）と
    **上書き確認の 3 択モーダル**（`confirm_overwrite` → `"overwrite" / "adopt" / "cancel"`）も持つ。
    3 択は `messagebox` で表現できないため **`child_save_dialog.py` と同型の自作 Toplevel**。
    **保存先が読めない（破損）ときは「既存を読み込む」を出さず 2 択**にする
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
    - **カスケードが書くのは startup / keymap_set / trigger_set / sequence / keymap**。
      **hotkey プリセットは書かない**（§5.10.3。書き手は `HotkeyPresetsIo` の 1 本）
    - KeymapSetIo が上記を束ね、`config_service.save_runtime_data` へ計画を渡す。
      束ねる本体は `_collect_child_save_plan`（**保存計画が確定するまでのループ**）で、
      1 周は「行と保存先の収集 → 子一覧ダイアログ → 保存先が変わったなら再計算と上書き確認 →
      依存確認（トリガー一覧）」の並び。各ステップは private メソッドへ分割済み（計画05 項目 2）。
      **依存確認で「選び直す」が選ばれた場合はモジュール定数 `_RETRY` を返して一覧へ戻る**
      （戻り値がキャンセル / 再試行 / 確定の 3 系統あるため `None` と区別する）
  - **参照元の掃除（phase 10。仕様は `spec_detail/data_schema.md` §5.8.1）**:
    - ReferenceCleanupIo（reference_cleanup_io.py = `app.reference_cleanup_io`）: **フローだけ**を持つ。
      未保存なら保存確認 → **いいえ / 保存失敗なら検査もせず終了** → 検査 → **対象 0 件なら一覧を出さず通知** →
      確認ダイアログ → **キャンセルなら 1 件も書かない** → 除去 → 結果通知。**runtime・dirty は変えない**
    - 検査・除去は `config_service` へ委譲し、文言は `reference_cleanup_text` の純関数が組み立てる
      （**このクラス自身は検査・除去・文言のロジックを持たない**。0 件の分岐だけはフロー側にもある）
    - ReferenceCleanupDialog（dialogs/reference_cleanup_dialog.py）: 読み取り専用の一覧 + 実行 / キャンセル。
      `tk.Toplevel` 継承。**フックの停止はウィンドウを渡して行い、解除は破棄時に自動**
      （`layout_delete_dialog.py` と同型。`destroy()` override は持たない）。
      **`result` の既定は `False`**（× / Esc で実行しない）
    - reference_cleanup_text.py（presentation 直下）: 提示テキストの整形（**tkinter 非依存の純関数**。
      `dialogs/` に置くと `__init__` が tkinter / pynput を巻き込むため直下）
    - **メニュー配線は `views/menu_bar.py` の設定メニュー 1 行**
  - KeymapSetHistoryIo（keymap_set_history_io.py = `app.keymap_set_history_io`）: 構成セットの読み込み履歴
    （phase 27・仕様は `data_schema.md` §5.12）。**記録の単一の口 `record(path)`** と履歴ダイアログのフロー。
    - **記録の呼び出し点は 3 経路**: パス指定の共通読込入口 `KeymapSetIo.load_keymap_set_path` /
      起動時に読む構成セットの指定 / 構成セットの保存成功。**起動時の自動読込では呼ばない**（§5.12.3）。
      `record()` は**境界で例外を握って `(False, 理由)` へ変換する**（呼び出し点がいずれも既存の `try` の
      内側にあり、漏らすと「成功した保存を失敗と表示」「読込済みデータを捨てて空起動」になるため）
    - 編集 6 メソッド（分類の追加 / 名前変更 / 削除 / 分類へコピー / 直近の削除 / 分類内の削除）は
      **毎回ディスクから読み直し → `domain/keymap_set_history.py` の純関数 → 保存成功時のみ `(True, "")`**。
      比較キーは `ConfigService.canonical_path`（presentation で `normpath`/`normcase` を組まない）
    - `KeymapSetIo.load_keymap_set_path(path)`: **パス指定の共通読込入口**（メニュー読込と履歴ダイアログの
      双方が使う。成否を `KEYMAP_SET_LOAD_OK` / `..._FAILED` で返す）
    - **メニュー配線は `views/menu_bar.py` のファイルメニュー 1 行**（「読込（構成セット）…」の直後）
- LayoutController（controllers/layout_controller.py）: キーボードレイアウトと KeyboardWindow 管理
- PaneLayoutController（controllers/pane_layout/ = `app.pane_layout`）: フル表示の幅配分（仕様は `spec_detail/features.md` §4.6「フル表示の幅配分」・
  `data_schema.md` §5.4）。計算は `pane_width_rules.py` の純関数、最小幅の実測は `pane_measure.py`。
  - 初回適用（FullView の `PanedWindow` の最初の `<Configure>`）: 最小幅とヘッダ幅の実測 → 保存値の検証 or 既定幅（780 基準）→ 一括適用 →
    **有効な保存値（切り詰め前）が適用後のウィンドウ幅より狭ければ、適用後の幅を 1 回 `write_startup`**（`startup_window_width_to_save`・phase 19）
  - **ヘッダ幅** `header_window_width`: `header_area.winfo_reqwidth()` + 外側の余白。最小幅を測る 3 箇所（初回適用 / `on_font_changed` の非省略表示経路 / `on_full_view_shown` の再測定）で一緒に測り保持する。
    ボタン幅の固定（App が先に行う）→ `update_idletasks` → 測定の順
  - ドラッグ: サッシュ上の左ボタンだけを個別バインドで処理し `"break"`（可動範囲の制限・中ボタン無効）。移動は `after_idle` で間引き、
    離したときに接する側の希望幅を更新して `startup_io.write_startup` で `full_view_pane_widths` を保存
  - `apply_layout`: 収まらない場合の最終値を `resolve_layout(..., header_window_width=)` で計算して `wm minsize` / geometry / 両端の幅を 1 回で適用
    （ウィンドウ最小幅 = max(メイン, ヘッダ)・縮小目標 = max(画面幅, ヘッダ)）。ドラッグ後の最小幅は `window_min_width_after_drag`（縮小規則を通さない）。
    **最小の高さ** `window_min_height`: `apply_layout` の前半は保持している前回の値を `minsize` に使い、幅を変える geometry の高さを max(現在, 前回の最小) にする。
    末尾（両端の `paneconfigure` の後）で `measure_window_min_height` により測り直し、normal 状態で「現在の高さ < 新しい最小」または「新しい最小 < 前回の最小」なら
    `geometry(現在の幅x max(現在の高さ, 最小))` で Tk の記憶する高さを確定させてから（広げた高さ・最大化解除で広がった高さが後で縮まない）`minsize(最小幅, 最小の高さ)`。
    ドラッグ後の `minsize` も同じ高さを使う（phase 20）。
    `on_font_changed`（省略表示中は印だけ）/ `on_full_view_shown` / `release_window_min_size`（省略表示へ入る前）を App が呼ぶ
  - **自動決定幅** `_auto_window_width`: 初回適用後は常に、`apply_layout` で geometry を変えたときだけ記録。
    ユーザーが幅を変えたと判定したら無効化（`None`）する
  - **ウィンドウ幅の保存**: App の `<Configure>`（App 自身・幅の変化のみ）で 500ms 後に `_save_window_width` を予約し直す。
    **判定は予約の実行時**（`wm_state() != "normal"` / 省略表示中 / 初回適用前は何もせず自動決定幅も触らない →
    自動決定幅と同じなら書かない → 異なれば無効化 → 保存値と同じなら書かない）。
    予約は `on_close`（`cancel_window_width_save`）と App の `<Destroy>` で取り消す。**終了時には書かない**
- KeymapPanelController（controllers/keymap_panel/keymap_panel_controller.py）: キーマップ管理パネル。追加フローは `KeymapAddFlow`（同フォルダ `keymap_add_flow.py`）へ委譲
- TriggerPanelController（controllers/trigger_panel_controller.py）: トリガー/シーケンスパネルとステータス表示
- HookController（controllers/hook_controller.py）: フック開始/停止・サスペンド・入力イベント入口
  - `register_hook_buttons(hook_btn, trigger_btn, *, fixed_width=False)`: `fixed_width=True`（FullHookFrame のみ）の組は登録時と `apply_fixed_button_widths()` で最大文言幅に固定する
  - **`suspend_hook_for_dialog(window)` はウィンドウを渡すと破棄時に自動で解除する**
    （渡さなければ呼び出し側が解除する＝try/finally 形）。
    `features.md` §4.6「モーダルダイアログの作法」/ `key_input.md` §7.2。
    破棄時の解除は `<Destroy>` から **`after(0)` で予約**される（即時ではない）。**テストで破棄後の解除を確かめるときは
    `tests_ui/hook_resume_wait.py` の `wait_for_hook_pause_count`**（`update()` を回して実時間の期限まで待つ。`update()` 1 回では負荷下で取りこぼす）。
    破棄直後の未解除・解除が起きないこと・同期解除の確認には使わない（phase 32）。
    `dialogs/` のトップレベルのダイアログが `suspend_hook_for_dialog(self)` を 1 回呼ぶこと・`dialogs/*.py` のどこも `resume` を呼ばないことは
    `tests_ui/test_dialog_teardown_flows.py` の静的検査（発見ベース・phase 33）が固定する。**常に親がフックを止めている間にだけ開かれ、
    自分では止めない子を足したら、同テストの `NESTED_CHILD_DIALOGS`（(ファイル名, クラス名) の組）へ追加する**
    （両方から開く `PresetManagerDialog` のような子は自分で止めるので含めない）。
  - **アプリ終了が確定したらフックを再開しない**（終了ガード。解除経路によらず効く）。
- listbox_utils.py（presentation 直下）: Listbox 選択ヘルパ（モジュール関数）
- modal.py（presentation 直下）: `grab_modal(window, parent=None, *, focus=None)` = モーダル化・
  **初期キーボードフォーカス**・**破棄時の grab 復元**・**最小化中の grab 預かりと復元時のフォーカス復帰**
  （`features.md` §4.6「モーダルダイアログの作法」）。**`dialogs/` と `controllers/config_io/` の
  すべてのモーダルがここを通す**（`grab_set` / `transient` を直呼びしない）。
  - **`focus` = 初期フォーカス先**（**省略時は窓自身**）。`grab_set()` の直後に `_apply_initial_focus` が
    `focus_set()` する（**`focus_force` / `lift` は呼ばない**・破棄中の `TclError` は握る）。
    **入力先を持つダイアログはここへ渡す**（`__init__` 内で別途 `focus_set` しない）。
    **二重呼び出し・預かり中の窓では要求を出し直さない**（早期 return）。
    **初期フォーカスでは**推測型（`focus_lastfor()` / `after_idle`）は**不採用**（未マップ時の `focus_set` が Tk 内で保留され
    明示指定を奪う。判断は `decisions_archive/28`。最小化からの復元は表示済みの窓の記録を読むので別物＝下の項）
  - **Escape の結線**（`grab_modal` の外・各ダイアログ側）: **× と同じ閉じ方へ結線する**
    （`io_dialogs.py` のみ `on_cancel`、他は `destroy`）。**Esc の別用途がある
    `ActionDialog` / `TriggerDialog` / `KeymapEditDialog` は `dialogs/escape_close.py` の
    `bind_escape_close(window, *, is_busy, stop)` で単一ハンドラ + 状態分岐**
    （記録中・取得中は停止して `"break"`。同一 widget では `<Escape>` が `<KeyPress>` より優先して
    単独発火するため、ハンドラを重ねると停止処理が死ぬ）。
    **判定順 = `is_busy()`（停止して印を立てる）→ 印（閉じない）→ 閉じる**。印は**クロージャに持つ**（ウィジェット属性を増やさない）。
    印は同関数が結線する `<KeyRelease-Escape>` で消す＝**押しっぱなしのリピートでは閉じない**
    （Windows の Tk はリピート中に KeyRelease を挟まない。判定順を逆にすると印が残ったまま再開した記録を Esc で止められない）。
    固定テスト = `tests_ui/test_modal_grab.py`（`focus_set` を 1 回・`focus_force` / `lift` を呼ばない）/
    `tests_ui/test_dialog_initial_focus.py`（初期フォーカス。**初期フォーカスの欠落を検出するのはここだけ**）/
    `tests_ui/test_dialog_escape_binding.py`（Escape の結線と実配送）。
    実配送のヘルパは `tests_ui/escape_delivery.py` の `send_escape`（フォーカスを期限つきで確保してから送り、
    破棄を待つ）。**ヘルパ自身もダイアログへ `focus_force` するため初期フォーカスの欠落は隠れる**
    （配送の検査であって初期フォーカスの検査ではない）
  - **第 2 引数 = 前面維持の相手**（`transient`）。**ネストして開く場合は呼び出し元のダイアログを渡す**
    （App を渡すと「App より前」としか指定されず、**呼び出し元を掴んで動かしたとき前に出る**）。
    **渡さなければ `transient` を設定しない**（既定 `None`。production の 15 箇所はすべて渡している）。
    **所有関係（`master`）は App のままで、この引数では変わらない**。
    渡す側は `PresetManagerDialog(..., transient_parent=...)`（**省略時は `parent` = App**）/
    `confirm_overwrite(..., transient_parent=...)`（キーワード必須）
  - **直前の grab 保持者を記録し `<Destroy>` イベントで戻す**（`destroy()` override ではないので
    × 閉じでも働く）。**記録はクロージャに持ちウィジェット属性を増やさない**
    （`object.__new__` で作られたインスタンスでも壊れない）
  - **`<Destroy>` は `add="+"` で結線する**（上書きすると他のハンドラを足したときに復元が無言で消える）
  - **呼び出しは初期化の最後の文に置く**（grab 取得後に失敗し得るコードを残さない）。
    **`tests_ui/test_nested_modal_grab.py` の静的検査がこの規約を固定している**ので、
    後ろに処理を足すとテストが落ちる。**落ちたらテストを緩めず、grab 取得後の失敗を
    どう回収するかをユーザーへ諮る**（phase 14 の確定運用）。
    検査対象は**発見ベース**（phase 33・発見は `tests_ui/dialog_discovery.py`）: `dialogs/` 直下の `Toplevel` 継承クラス +
    `controllers/config_io/` で `grab_modal` を呼ぶファイル（呼び出し場所はこの 2 か所だけ・式文以外の呼び出しも数える）。
    **新しいダイアログは列挙へ足さなくても検査される**。`dialogs/` に非モーダルの `Toplevel` を置くと落ちる /
    config_io に呼び出しを足したらテストの期待件数の辞書へ追加する。`Toplevel` の別名 import・多段継承は発見しない
  - **`install_minimize_grab_custody(app)` = 最小化中だけ grab を預かる**（`features.md` §4.6 の
    最小化の条項。`app.py` の `__init__` 末尾で 1 度だけ呼ぶ）。App の `<Unmap>` で**非表示になった保持者**
    から grab を外して預かり、`<Map>` で**記録窓 → 台帳の最内**の順に「生存かつ表示中」の窓へ張り直す。
    ガード = **App 自身のイベントのみ**（`pack_forget` でも `<Unmap>` が飛ぶ）/ **`grab_current()` が
    解決不能（stdlib ダイアログ）なら触らない** / **既に預かり中なら預かり直さない** /
    **破棄済み・表示中の保持者は預からない** / **別の窓が grab 中なら上書きしない**。
    **`deiconify` / `lift` を呼ばない**（`deiconify` は中間窓が消える・`lift` は WM が戻すので不要）。
    **復元時のフォーカス復帰**: `return_custody` は**どの経路でも最後に `app.after_idle(_restore_modal_focus, app)` を予約**する
    （**App の `<Map>` 全般で**予約する。grab の返却は `<Map>` 内で即時。**即時に `focus_set` しない**＝実 App の 3 段ネストで
    外側の窓が非表示のまま残る）。`_restore_modal_focus` は**予約の実行時点の** `grab_current()` が台帳に `is` で含まれ・
    最小化中に開いた窓でなく・生存かつ表示中なら、`focus_lastfor() or window` へ `focus_set`。さらに **`app.focus_get() is None`
    かつ `_is_app_foreground(app)`** のときだけ同じ先へ **`focus_force`**（タスクバー復元ではアクティブ化の時点で grab が預かり中のため
    Tk の振り向けが働かず、Tk がフォーカスを持たない）。`TclError` / `KeyError` は握り、最後に `_opened_while_minimized` を空にする。
    `_is_app_foreground` = 専用 `ctypes.WinDLL("user32")` の `GetForegroundWindow`（`argtypes=[]`・`restype=HWND`・`@cache` の
    `_foreground_window_fn`）と `int(app.wm_frame(), 16)` の比較。**presentation で `ctypes` を使うのはここだけ**・共有の
    `ctypes.windll.user32` は変えない・NULL / 例外は偽（判断は `decisions_archive/29`）
  - モジュール状態は 4 つ: `_active_modals`（アクティブなモーダルの台帳。**`grab_modal` を通った窓だけ**・
    末尾 = 最内）/ `_custody_window`（預かり中の窓）/ `_app_minimized`（最小化中フラグ）/
    `_opened_while_minimized`（最小化中に `grab_modal` した窓。復帰の対象外にする・**その回の復元の処理で空にする**・破棄時にも除く）。
    `grab_modal` 側は **預かり中に開いたモーダルなら預かり窓を直前の保持者にする** /
    **最小化中に復元できなかった直前の保持者は（預かりが空なら）預かりへ戻す**。
    固定テスト = `tests_ui/test_minimize_grab_custody.py`（テストは `setUp` でモジュール状態を patch して独立させ、
    `_is_app_foreground` を既定 `False` に差し替える）/ `tests_ui/test_modal_app_foreground.py`（前面判定と FFI の型設定）

### View → コントローラのウィジェット登録（計画04 W5）

View が App へウィジェット参照を生やす逆流（`app.hook_toggle_btn = ...`）は廃止した。現在は次の2方式:

1. **登録方式（複数 View に同種ウィジェットがあるもの）** — Widget が生成時に自分をコントローラへ登録し、
   同期メソッドは登録済みウィジェットを走査する（走査順は登録順 = full → compact）:
   - `HookController.register_hook_buttons(hook_btn, trigger_btn, *, fixed_width=False)` ← FullHookFrame（`fixed_width=True`）/ CompactHookFrame
   - `LayoutController.register_layout_combo(combo)` ← FullDisplayFrame / CompactDisplayFrame
   - `TriggerPanelController.register_trigger_list(listbox)` ← FullTriggerBox / CompactTriggerBox
   - `SingleKeyCaptureController.register_widgets(entry, capture_btn, clear_btn)` ← FullHookFrame（キャプチャUIは Full のみ）
2. **所有 Widget の属性（単一 View にしかないもの）** — コントローラからは
   `app.full_view.keymap_box.keymap_listbox` のように **App → View → Widget のパス**で辿る
   （`app.full_view.sequence_box.run_to_end_delay_entry` 等）。

### ConfigService（`application/config_service/` パッケージ）

**単一ファイルではなくパッケージ**（計画05 項目 1 で分割・挙動不変）。責務ごとに 14 ファイル:

| ファイル | 責務 |
|---|---|
| `__init__.py` | **`ConfigService` 本体**。公開面 / パス基盤（`canonical_path` / `is_path_within` / `to_config_relative_or_absolute`）/ 個別ファイル IO / `_parent_refs` 操作 |
| `contracts.py` | **公開面**（phase 12 で新設）。**判定名・理由コード・結果型（dataclass）の唯一の定義**（定数 34 / 型 9）。**`config_service` 内の他モジュールを import しない**（依存は実装モジュール → `contracts` の一方向）。**presentation はこのモジュールと `ConfigService` の委譲メソッドだけを見る**（`spec_detail/architecture.md` §3.2）。実装モジュール側は `from . import contracts` + `contracts.NAME` で参照する（`from .contracts import NAME` は名前が再束縛され逆戻り防止テストが書けないため不可）。**内部表現（`QUARANTINE_DIR_NAME` / `UNIT_ID_PATTERN` / `ENTRY_*` / `CANDIDATE_DIRS`）はここへ置かない** |
| `save_plan_execution.py` | 保存計画の実行（事前検証 / 保存後パスの適用 / 依存判定） |
| `split_payloads.py` | 保存 payload の構築（keymap / trigger_set / sequence） |
| `save_path_resolution.py` | 保存先の解決と既定命名（`slugify_file_stem` の実体・一意パス採番） |
| `split_loading.py` | split 構成の読込（keymap_set → keymap / trigger_set / sequence の再構成） |
| `parent_refs_cleanup.py` | **参照元の掃除**（phase 10）。検査（子の列挙 / 実在判定 / 保護対象の分離 / 判定名 / 重複排除）と `prune_parent_refs`（除去） |
| `reference_scan.py` | **参照集合の構築**（phase 11）。keymap_set の列挙と **3 段辿り**（keymap_set → keymap → trigger_set → sequence・phase 34。旧形式の keymap_set `trigger_set_path` も参照に数える・`mappings` を持つ JSON は keymap_set と判定しない）。読めなかった参照側を理由コード付きで返す |
| `orphan_scan.py` | **走査と孤児判定**（phase 11）。候補側の列挙と形状検証 / 保護対象の適用 / 判定名 4 種 / `normalize_scan_dirs` |
| `quarantine.py` | **隔離**（phase 11）。隔離ルートの遅延作成・**マニフェストの原子書込み（移動より先）**・1 件ずつの移動 |
| `quarantine_manage.py` | **隔離の管理**（phase 11）。実行単位の一覧 / 復元 / **削除**（実行単位 ID + 4 検証・不可逆） |
| `candidate_dirs.py` | **候補側ディレクトリの唯一の定義**（`CANDIDATE_DIRS` / `RESERVED_DIR`。計画08 で新設）。**孤児判定の対象範囲**（`orphan_scan`）と**復元先ガードの許可範囲**（`quarantine_manage`）が同じ定義を見る。片方だけ変えると「隔離はできるが復元できない」ズレが出るため。**添字で結び付けない**（`zip(strict=True)` を使う） |
| `keymap_set_history.py` | **構成セットの読み込み履歴**（phase 27・仕様は `data_schema.md` §5.12）。読込（不在と破損の区別 / `*.broken*.json` への退避 = 連番 5 で打ち止め）・原子的書込み・**記録**（保存表記への正規化と `canonical_path` による先頭一致 no-op）。規則そのものは `domain/keymap_set_history.py` の純関数が持つ。`ConfigService` からは `load_keymap_set_history` / `save_keymap_set_history` / `record_keymap_set_history` の 3 つを 1 行委譲 |
| `path_boundary.py` | **`is_real_path_within` の唯一の定義**（実体〔realpath〕基準の境界判定。ジャンクションを解決する）。**リダイレクト判定 `_is_redirected` は `quarantine.py` / `quarantine_manage.py` が各自持ち、`ConfigService.is_path_within` は別物**（比較専用の表記判定で**同一パスも配下と判定する**）。`orphan_scan` / `quarantine` / `quarantine_manage` が import する。**再定義しない**（`quarantine.py` → `orphan_scan` の import があるため逆向きは循環になる） |

- **`ConfigService` 本体を `config_service.py` へ移してはならない**。テストが
  `patch("keyseq.application.config_service.os.path", ntpath)` でモジュール名前空間の `os.path` を
  差し替えており、パス同一性まわり（`canonical_path` / `_merge_parent_ref` 等）は
  この名前空間に居ることが前提（4 テスト）。同じ理由で**パス基盤メソッドを兄弟モジュールへ移さない**。
- 兄弟モジュールの関数は **`service` を第 1 引数に取るモジュール関数**（`service.X` で本体を参照）。
  兄弟から `__init__` を import しない（循環回避）。private ヘルパの互換ラッパは置かない。

責務の内訳:

- 単一JSON互換の読込/書出
- split構成の読込/保存
- config配下は相対、外部は絶対のパス保存ルールを扱う
  - `normalize_scan_dirs` は `orphan_scan.py` へ委譲し、走査先設定の読み出し・保存で
    非文字列・空文字・同一パスの重複を除く。実在確認はせず、保存表記を返す。
- **孤児ファイルの棚卸しのファサードを持つ**（実体は上表の 4 モジュール。仕様は
  `spec_detail/data_schema.md` §5.8.9）。いずれも**1 行委譲**で、`__init__.py` に実ロジックを置かない:
  `collect_reference_paths` / `scan_orphans` / `collect_protected_paths` / `normalize_scan_dirs` /
  `quarantine_orphans` / `list_quarantine_units` / `restore_quarantine_unit` /
  `collect_unit_paths` / `delete_quarantine_unit`
- trigger_set と sequence の分離保存・読込を扱う
- keymap / trigger_set / sequence の個別ファイル保存・読込を扱う
- **hook キーの解決点を持つ**（仕様は `spec_detail/data_schema.md` §5.9）。分岐点は次の 4 つで、
  **これ以外へ解決ロジックを置かない**（フック層・UI 層へ分散させない）:
  - `split_loading.load_global_hook_keys(service, *, config_root)` — config.json の全体デフォルトの
    **読み出し**（正規化・失敗時は `("", "")` へ縮退）。それ自体は選択をしない
  - `split_loading.build_runtime_data_from_split` — **通常の keymap_set 読込での選択**。
    `resolve_hook_keys_individual(keymap_set)` の結果を runtime へ確定させ、
    OFF のときだけ `load_global_hook_keys` の値を注入する
  - `ConfigService.apply_global_hook_key_defaults(runtime, *, config_root)` — **hook キー単独の注入**。
    冪等で、先頭で `hook_keys_individual` の既定（`False`）を補う。**通常読込はこの API を経由しない**。
    **直接の呼び出しは `App.toggle_hook_keys_individual` の ON→OFF だけ**
    （runtime の新規化・置換時は下記 `apply_global_defaults` が内部で呼ぶ）
  - `split_payloads.build_keymap_set_payload` — **保存側**。OFF のとき書くのは**常に `""`**
    （runtime の解決済み値を書くと全体デフォルトが keymap_set へ焼き付く）
- **全体デフォルトの注入口を 1 本に束ねる**（仕様は `spec_detail/data_schema.md` §5.8.8 の入口台帳）:
  - `ConfigService.apply_global_defaults(runtime, *, config_root)` — **runtime を新規化・置換した直後**に
    呼ぶ唯一の注入 API。`apply_global_hook_key_defaults` を呼んだ上で**グローバルプリセットを供給**する。
    **冪等・例外を投げない**（読めなければ縮退）。呼ぶのは**入口台帳 E1〜E5**
  - **通常読込（L1〜L3）はこの API を経由しない**が、プリセットの**供給規則は共通**
- **hotkey プリセットの解決点を持つ**（仕様は `spec_detail/data_schema.md` §5.10）。
  **グローバルと個別の分岐・保存先の算出・拒否 / 上書きの判定はすべて application 側**に置き、
  presentation へ二重化しない。分岐点:
  - `split_loading.load_global_hotkey_presets_path(service, *, config_root)` — config.json の
    `hotkey_presets_path` の**読み出し**（未設定・空・非文字列・読込失敗は既定へ縮退。
    既定は **`user/hotkey_presets/global/default.json`**）。
    返すのは**保存表記のまま**なので、書き込み・存在確認では `resolve_config_path` を通す
  - `split_loading.load_hotkey_presets_file(service, stored_path, *, config_root) -> list | None` —
    **1 ファイルの読み出し**（グローバル / 個別で共通）。`load_global_hotkey_presets` はこれの薄い包み。
    **読めた＝`list`（空を含む）/ 読めない＝`None`**。戻り値は
    `domain/config.py::normalize_hotkey_presets` を通した**正規化済み**（**「読めたか」の判定は正規化の前**）。
    **正規化はここ 1 箇所**に置く（注入 API 側・保存側には置かない）
  - `split_loading.build_runtime_data_from_split` — **通常読込での選択**（個別 → 読めなければ
    グローバル → どちらも読めなければ置き換えない）。**`hotkey_presets_individual` キーを持たない
    keymap_set は `hotkey_presets_path` も runtime へ載せない**（§5.10.1 の移行規則。
    フラグ自体は**値**で、残置パスの遮断は**キーの有無**で判定する）
  - **読み出し用と書き込み用でパス解決が分かれる**（意図的な非対称。§5.10.2 / §5.10.3）:
    `resolve_individual_hotkey_presets_read_path(runtime)` = **config 外も許容**（読み出し用）/
    `resolve_individual_hotkey_presets_path(service, runtime, *, config_root)` = **config 配下のみ**（書き込み用）
  - `split_loading.resolve_hotkey_presets_save_path(..., keymap_set_path, individual=None)` —
    **保存先の算出**。個別かつ有効パスが無ければ
    `save_path_resolution.default_individual_hotkey_presets_path`（`user/hotkey_presets/<stem>.json`）へ
    寄せる。**グローバル宛は空文字**を返す
  - `split_loading.individual_hotkey_presets_save_rejection_reason(...)` — **保存先ガード**。
    `"reserved_dir"`（`global/` 配下）/ `"global_conflict"`（グローバルと同一ファイル。
    判定は `canonical_path`）/ `""`（問題なし）
  - `split_loading.describe_individual_hotkey_presets_overwrite(...)` — **上書き確認の要否**。
    **`{"conflict": bool, "existing": list | None}` を同時に返す**（`existing` は「既存を読み込む」
    が使う。破損時は `None` で、UI 側が 2 択へ縮退する）。比較は正規化済みどうし
  - `ConfigService.load_individual_hotkey_presets(...)` — **個別ファイルの読み出し入口**
    （マネージャのトグルでの読み直しが使う唯一の経路。表示用であり runtime へは反映しない）
  - `split_loading.describe_hotkey_presets_source(...)` — **UI の状態表示**
    （`individual_state` = `off` / `active` / `missing` / `external` / `external_missing`、
    `displayed_source` = `individual` / `global` / `builtin`）
  - `ConfigService.save_hotkey_presets(presets, *, config_root, stored_path)` — **書き込み**
    （`save_global_hotkey_presets` はグローバル宛の入口）。
    **例外は握り潰さず送出**し、成否への変換は presentation（`HotkeyPresetsIo`）が行う
  - `ConfigService.clear_individual_hotkey_presets(runtime)` — **Import での強制 OFF**（E5）/
    `relocate_individual_hotkey_presets(...)` — **別名保存での個別ファイル複製と追随**
    （コピー先に実体があれば複製しない / コピー元が無ければ複製しない）
- 移行判定の純関数は `domain/config.py::resolve_hook_keys_individual`。呼び出しは 3 系統で、
  **渡すデータが違う**: 読込＝**生の keymap_set dict**（`split_loading`）/ 保存＝**runtime**
  （`split_payloads`。`.get()` の真偽で見ずに必ずこの純関数を通す＝フラグ無しの旧 runtime を
  従来どおり個別値保存にするため）/ 互換化＝`ensure_config_compatibility` 内（hook キー正規化の直後）
- **hook キー名の定義元も `domain/config.py`**（`HOOK_STOP_KEY` / `HOOK_TOGGLE_KEY` /
  対のタプル `HOOK_KEY_FIELDS` / 対の正規化 `normalize_hook_key_pair`）。application / presentation は
  リテラルを書かずこれを参照する。**例外はキーの並び自体が契約になる 3 箇所**
  （`DEFAULT_CONFIG` の既定値表 / `split_payloads` の保存 payload の dict キー / `startup_io` の保存 dict キー）で、
  ここは**明示列挙のまま**にする（保存 JSON のキー順が変わらないことの担保）
- **子ファイルの保存計画（`application/save_plan.py` の `SavePlan`）を実行する**
  （仕様は `spec_detail/data_schema.md` §5.8）:
  - 保存対象の解決（`resolve_child_save_targets`）・依存関係の検出・計画の事前検証・
    **書き込み順序による best-effort 保証**（子 → 上位 → keymap_set → 起動設定。
    上位の索引を新パスへ進める前に子の成功を確認する。トランザクション / ロールバックは持たない）
  - `_parent_refs` の読み書き（best-effort マージ）とパス同一性判定（`canonical_path` /
    `is_path_within` の 2 本のみを使う。正規化文字列は比較専用）
  - **計画を決めるのは presentation 側**（`config_io/child_save_*`）。ConfigService は
    渡された計画を実行するだけで、ダイアログを持たない
  - **参照元の掃除**（`parent_refs_cleanup.py`。公開面は `ConfigService` の**委譲 2 本**）。
    設計の芯は 3 つ:
    - **子の列挙は runtime の source_path 3 種のみ**。**`resolve_child_save_targets` を使わない**
      （「次に保存するとしたらどこへ書くか」であり、未実体化の子へ既定パスが割り当てられて
      **無関係な既存ファイルを書き換える**）
    - **保護対象**（現在の keymap_set / keymap / trigger_set への参照）は**実在しなくても除去しない**。
      検査の時点で分離し、提示・件数・0 件警告から外す
    - **除去直前に JSON 全体を読み直して再判定する**（検査時のスナップショットを書き戻さない）。
      除去 0 件なら書かず（冪等）、全件除去は `[]`。1 件の失敗で中止せず記録して継続する

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
- メイン領域は `tk.PanedWindow`（横・`view.panes`）に KeymapBox | FullTriggerBox | SequenceBox を入れる。
  両端 `stretch="never"`・トリガー一覧 `stretch="always"`・境界線 12px（phase 18）。幅の制御は PaneLayoutController が持ち、FullView は生成と配置のみ
  一覧の行数指定（KeymapBox・FullTriggerBox = 6 / SequenceBox = 9）は**フル表示の最小の高さの基準**（既定の半分。表示行数は伸びた分で決まる・phase 20）
- 構成 Widget:
  - FullHookFrame（hook_frame.py）: フック開始/停止・キーマップ一時停止 / 再開・停止/一時停止・再開キーの表示と**取得・クリア**・
    「このキーマップセットで個別指定する」チェック（操作可能なのは full のみ）
  - FullDisplayFrame（display_frame.py）: 常に手前・省略表示へ・キーボードUI・レイアウト選択
  - FileFrame（file_frame.py）: 保存 / 別名で保存 / 読込 / 新規作成
  - KeymapBox（keymap_box.py）: キーマップ一覧と管理ボタン（追加・変更・削除・保存系。phase 34 で「選択」ボタンを削除し一覧の選択 = アクティブ化）
  - FullTriggerBox（trigger_box.py）: トリガー一覧・編集ボタン・suppress チェック
  - SequenceBox（sequence_box.py）: 出力シーケンス一覧・アクション操作・連続実行と間隔(ms)

### CompactView（views/compact_view/）
- 簡易表示 / フック制御
- 構成 Widget:
  - CompactHookFrame（hook_frame.py）: フック開始/停止・キーマップ一時停止 / 再開・停止/一時停止・再開キーの**表示のみ**
    （個別指定チェックも `state="disabled"` の状態表示のみ）
  - CompactDisplayFrame（display_frame.py）: 常に手前・フルに戻す・キーボードUI・レイアウト選択
  - CompactTriggerBox（trigger_box.py）: トリガー一覧のみ

### メニュー / ステータス
- menu_bar.py: `build_menu_bar(app)`（ファイル / 設定メニュー）と `bind_menu_shortcuts(app)`（Ctrl 系アクセラレータ）。
  設定メニューは「参照元を掃除…」「**孤児ファイルの棚卸し…**」「**隔離の管理…**」を持つ
  （`features.md` §4.6）。ファイルメニューは「読込（構成セット）…」の直後に
  「**履歴から読み込む…**」を持つ（phase 27・`data_schema.md` §5.12）。**テストはメニュー項目をインデックスで固定しない**
  （top-level menubar には tearoff があり位置がずれる。カスケードとラベルで探す）。
  **build と bind は別関数**（フォントサイズ変更時はメニューのみ再構築し、バインドは再実行しない）。
- status_bar.py: `build_status_area(app, parent)`（「ステータス」欄 + 下部ステータスバー: ファイル状態 / 一時メッセージ）

---

## フック関連

- keyboard によるグローバルフック
- suppress=True 使用
- UI操作中は停止
- **停止/トグルキーは解決済みの 1 値のみをフック層が直読みする**（`app.data` の
  `hook_stop_key` / `hook_toggle_key`）。全体デフォルトと個別指定の切替は application 層で解決済みのため、
  `hook_controller` / `input_router` / `keyboard_window` / App のフック供給部は供給源を意識しない
  （仕様は `spec_detail/key_input.md` §7.6 / `spec_detail/data_schema.md` §5.9）

### アクションの実行（application/action_executor.py / sequence_runner.py・phase 31）

- `ActionExecutor.execute(action) -> bool`: `type`（非文字列は空扱い）が `hotkey` / `text` / `mouse_click` なら送って `True`
  （内部の hotkey 検証エラー・`x` / `y`〔`to_x` / `to_y`〕不正・mouse_click の送信失敗も通知して `True`。**hotkey / text の送信例外は従来どおり `execute` の外へ抜ける**）。**それ以外は送らず** `on_action_error` へ
  `type` を文字列化した浅いコピーと理由を渡して `False`（`App` が `HookController.show_action_error` を注入）。
- `SequenceRunner` は `perform_action`（= `App._perform_action` → `execute`）の戻り値が **`is False`** のときだけ止める:
  run_to_end は `stop_run_to_end`、単発は index を進めない。注入される `perform_action` の実装が `None` を返す場合は従来どおり進む。
- 仕様は `spec_detail/data_schema.md` §5.11.1 / §5.11.5。テスト = `tests/test_action_executor_type.py` / `tests/test_sequence_runner.py`。

### キーの送信（infrastructure/input_gateway.py の InputGateway・phase 21）

- 呼び出し元は `ActionExecutor` だけ（hotkey アクション = `send_hotkey(normalized)` / キーマップの送信先 = `press_key` → `release_key`。send guard は呼び出し元が張る）。
- **Windows の拡張キー**（矢印・Home・End・PageUp/PageDown・Insert・Delete・右 Ctrl / 右 Alt・Windows・menu・PrintScreen・NumLock）は、
  ファイル内の表（正規化後のキー名 → 仮想キー / スキャンコード）で解決し、`user32.keybd_event` に KEYEVENTF_EXTENDEDKEY を付けて送る
  （`keyboard` ライブラリは拡張フラグを付けないため、`shift+right` 等がテンキー扱いになり範囲選択にならない。仕様は `spec_detail/key_input.md` §7.7）。
  名前の正規化は公開 API の `keyboard.normalize_name`（別名 `pgup` / `del` / `apps` / `win` 等）。
- `send_hotkey`: 要素に拡張キーが無ければ従来どおり `keyboard.send(hotkey)`。含む場合は要素を記述順に押して逆順に離し、途中の例外でも押したキーを逆順に離してから再送出する。
- text（`keyboard.write`）・マウス（`pyautogui`）は対象外（マウスは下記「マウス操作」節）。

### マウス操作（infrastructure/input_gateway.py の InputGateway・phase 22）

- 呼び出し元は `ActionExecutor._execute_mouse_click` だけ（`mouse_click` アクション）。**send guard には入らない**
  （フックはキーボードのみで自己受信しないため。仕様は `spec_detail/data_schema.md` §5.11.2）。
- `click_mouse`（`pyautogui.click`）= 従来の単発クリック。**FailSafe は従来どおり有効**（触らない）。
- `drag_mouse` = `moveTo → mouseDown → moveTo(duration) → mouseUp`。`mouseUp` は `finally` に置き、
  途中で例外が出てもボタンを離す。**実行中だけ `pyautogui.FAILSAFE` を退避して False にし、`finally` で復元する**
  （離す点が画面の隅だと解放自体が FailSafe に遮られるため。仕様は `data_schema.md` §5.11.4）。
  `dragTo` は使わない（try/finally が無い）。`ctypes` も使わない（pyautogui が OS 別実装を内部で選ぶため）。
- **所要時間の算出は application 層**（`action_executor._execute_mouse_drag` が距離 ÷ `drag_speed` を
  0.15〜5.0 秒へクランプして秒数を渡す）。infrastructure は受け取った秒数で動かすだけ。
- ドラッグの入力 UI は `dialogs/action_dialog.py`（「ドラッグ」チェックで離す位置 X/Y・取得ボタン・速度欄を
  `grid_remove` で出し入れし、X/Y ラベルを「掴む位置」へ、回数欄を `disabled` にして保存値を 1 に固定。
  座標取得は掴む用 / 離す用で排他）。一覧表示の整形は `domain/config.py` の `format_action_list_item`。
- **`actions[]` の読込時正規化は `domain/config.py::normalize_actions` に一本化**（dict 以外の要素を除去し
  `label` を整形、`type` / `button` は**キーがある場合のみ** `coerce_label` する純関数・冪等。phase 30）。呼び出しは 2 系統 = `ensure_config_compatibility` 内（split 読込・単一 JSON）と
  `application/config_service::_normalize_sequence_payload`（個別 sequence JSON の単体読込 / 保存後の戻り値）。
  **application 側は整形規則を持たず domain の関数を呼ぶだけ**（規定は `data_schema.md` §5.11）。
- **JSON 読込時の型正規化は `domain/config.py` の `coerce_key_name` / `coerce_label` に一本化**（phase 24）。
  どちらも**非 str なら `""`** を返す純関数で、`coerce_key_name` は str のとき `normalize_key_name`
  （trim + 小文字化）を通す。適用先は**読込経路すべて**（`ensure_config_compatibility` の
  `triggers[].key` / `triggers[].label` / `keymaps[].id` / `keymaps[].label` / `mappings` の target、
  `normalize_actions` の `label`、`config_service` の `_generate_keymap_id` / `load_keymap_file` /
  `_normalize_sequence_payload`、`split_loading` の `load_triggers_from_trigger_set` / `load_keymap_entry`）。
  **`normalize_key_name(value: str)` のシグネチャは変えない**（呼び出しが 158 箇所あり、Any 受けにすると
  全経路の意味が変わるため）。規定は `data_schema.md` §5.1「型不正の共通規則」。
- **パス系・キー名系にも同じ関数を適用する**（phase 25）。**使い分けは
  「パス = `coerce_label`（trim のみ）/ キー名・id = `coerce_key_name`（trim + 小文字化）」**。
  パスに `coerce_key_name` を使うと小文字化でパスが壊れる（規定は `data_schema.md` §5.5 / §5.7）。
  適用先は `split_loading` の `trigger_set_path` / `active_keymap_path` / `keymaps[].path` /
  `keymaps[].switch_key` / 外部レイアウト登録、`domain/config` の `external_keyboard_layouts` /
  `keymap_switch_keys`、および**参照突合経路**（`reference_scan.py::_source_path`。
  孤児棚卸し・参照元の掃除はディスクから生 JSON を直接読む別実装で、
  `ensure_config_compatibility` を通らないため個別に適用が要る）。
  **未対応の残件** = `presentation/controllers/config_io/startup_io.py` の `keymap_set_path`
  （config.json の生値。presentation 層のため phase 25 のスコープ外）。
- **runtime 内部キーのパス値 3 種**（`_keymap_source_path` / `_sequence_source_path` / `_trigger_set_source_path`）も
  `ensure_config_compatibility` で**キーがある場合のみ** `coerce_label` する（phase 30・`data_schema.md` §5.7）。
  domain は内部キー名を文字列直値で持つ（application の `ConfigService.INTERNAL_*` を import しない）。
  **読み手（`save_path_resolution` / `split_payloads` / presentation の `config_io/*` 等）は正規化済みの値を前提に無修正**。
- **読み込み履歴の規則は `domain/keymap_set_history.py`**（phase 27・`data_schema.md` §5.12）。
  型不正の正規化 / 重複統合 / 上限 20 / 分類の追加・名前変更・削除・コピー / 名前順の整列を
  **I/O に依存しない純関数**として持ち、**比較キーは呼び出し側から `key_of` で受け取る**
  （`config_root` を知らないため）。`domain/config.py`（353 行）へは足さない。
  拒否（空名・同名・不存在・重複・範囲外）は **`None` を返す**で表現し、呼び出し側が理由を付ける。

---

## キーマップとトリガー一覧（phase 34）

仕様は `spec_detail/data_schema.md` §5.13（データ・読込移行・保存）/ `key_input.md` §7.3（優先順位・重複）/ `features.md` §4.1・§4.3・§4.5（UI）。

- **口 `domain/keymap_triggers.py`**: アクティブキーマップのトリガー一覧の取得・確保・代入（`get_active_triggers` / `ensure_active_triggers` /
  `set_active_triggers`）と、共有実体の列挙（`iter_trigger_sets` = 同一 list を共有するキーマップ群を一覧順の代表でまとめる / `trigger_set_members` /
  `trigger_set_owner`）、キーマップ 1 つ以上の保証（`ensure_at_least_one_keymap`）、単一 JSON の移行（`migrate_single_json_triggers`）。
  **presentation は runtime の `"triggers"` を直接書かない**（`tests/test_keymap_triggers.py` の静的テストで固定）。
- **runtime の形**: 各 `keymaps[]` 要素が `triggers` と trigger_set の内部キー（`_trigger_set_source_path` / `_parent_refs` / `_dirty` / `_imported`）を持つ。
  トップレベル `triggers` は `[]`。移行状態はトップレベル `_legacy_trigger_set`（状態・旧値・移行先 keymap id・`auto_created`）。
  `DEFAULT_CONFIG` は新形式（`keymaps[0].triggers` に例）。`KeymapService.ensure_active_keymap` は `keymap_1` / label 空へ統一。
- **読込** `config_service/split_loading.py`: keymap ファイルの `trigger_set_path` を `attach_trigger_set`（同じ解決先は同一 list を共有）で読む。
  旧形式の移行（項目の無いキーマップのみ・同ファイル参照なら same・移行できなければ「旧トリガー一覧（<stem>）」を自動作成）もここ。
  キーマップの個別読込（`config_service.load_keymap_file` / `keymap_file_io`）も同じ `attach_trigger_set` を使う。
- **保存** `config_service/split_payloads.py` / `save_plan_execution.py` / `save_plan.py`: trigger_set の実体ごとの payload と行（識別子 = 代表キーマップ id）、
  sequence の合成キー（`save_plan.compose_sequence_key` / `split_sequence_key`・区切り `\x1f`）、計画全体の衝突回避、依存 3 段
  （`find_dependency_blocked_parents`）、§5.13.4 の決定表、移行した trigger_set の `_parent_refs` の後処理。
  キーマップの個別保存計画は `config_service/__init__.py` の `_save_keymap_with_plan` 以下（**1100 行超の肥大は `/refactor_check` の候補**）。
  個別キーマップ保存は runtime の list 同一性を保つため意図的に `ensure_config_compatibility` を通さない（入口で正規化済み）。
- **重なり判定 `application/key_overlap.py`**: `analyze_key_overlaps` が停止 / トグル / 切替 / 置換 / トリガーの重なりを判定し、
  読み取り専用の索引（`MappingProxyType`）を持つ `KeyOverlapAnalysis` を返す。**App が表を保持し差し替える**（`_key_overlap_report` /
  `_refresh_key_overlap_report`）。作り直しの契機はトリガー一覧・キーマップ一覧の再描画・停止 / トグルキーの変更（trace）・読込
  （`KeymapSetIo.apply_loaded_data_to_ui`）。グレー表示・§7.3 の案内・編集時拒否・開始検証が同じ表を使い、`InputRouter` は表を引くだけ。
- **入力判定** `application/input_router.py`: 停止 > トグル > 直接切替 > トリガー > 置換。案内用の `InputRoute.shadowed` を付け、
  `ActionExecutor.on_shadowed_action` → `HookController` がステータスバーの一時メッセージ（`App._set_flash_message`）に出す（停止時は併記）。
- **切替と実行位置** `application/app_state.py`: 実行位置・選択行はトリガー一覧の実体（代表キーマップ id）ごと（`indices_for` / `keymap_indices` /
  `selected_trigger_indices`・代表削除で `rekey_trigger_set`）。連続実行中の切替可否は `AppState.can_switch_keymap` の 1 箇所で、
  一覧の選択・直接切替キー（`ActionExecutor`）・アクティブの削除が共有する。
- **キーマップ管理** `controllers/keymap_panel/`（`keymap_panel_controller.py` + 追加フロー `keymap_add_flow.py`）: 一覧の選択 = アクティブ化（未保存にしない）・追加フロー（切替キー未設定の既存への設定 →
  追加ダイアログ。`KeymapEditDialog(validate=...)` で入力エラー時に閉じない）・編集（2 つ以上で切替キー空不可）・削除（1 つなら不可・移行先なら移行記録を消す）・
  グレー表示。個別読込の二重読込拒否は `keymap_file_io`。

---

## 注意

- UI更新は必ず UIスレッドで行う（after使用）
- フック処理はUIと分離される
