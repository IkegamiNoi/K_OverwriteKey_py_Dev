# 別タスク化候補（deferred_tasks.md）

継続保留の、ソース変更を伴う細かい負債の置き場。`/refactor_check` の追記先・照合先もここ。
idea・フェーズへ昇格したものはここから消す（昇格先の idea / phase がその後の正）。
> このファイルは 2026-11-26 に `instructions/phase/current.md` から分けた。以後の追記・削除はこのファイルで行う。


（継続保留、ソース変更を伴う細かい負債。`/refactor_check` からの追記先もここ。
**領域別に並べ、由来フェーズは各項の末尾に括弧で示す**。
idea へ昇格したものはここに残さない〔2026-09-22 に idea_27〜32 を昇格〕）

### ヘルプの付け替え（phase 83 由来）

- phase 83 の /refactor_check の境界: `keyseq/presentation/help/help_window_controller.py`（296 行）に責務のまとまりが 4 つ（持ち主への付け替え・状態の控え・最小化からの復帰・Tk 9.1 の deiconify の対策）。300 行を超える変更が入ったら、控え（`_save_state` / `_schedule_save` / `_run_scheduled_save`）か Tk の対策を help/ 内の別モジュールへ分けるのを検討（判断 = decisions_archive/83）

### スクロールの向きの反転（phase 82 由来）

- phase 82 の /refactor_check の境界: M4 = `ScrollInvert(` の全フィールドの組み立てが新しい型のため 0 → 3 か所（`domain/mouse_scroll.py` の `coerce_scroll_invert`・`presentation/app.py` の `set_scroll_invert`・`NO_SCROLL_INVERT`）と `scroll_invert_to_json` の全キーの列挙。フィールド 2 つのため不要と判定。フィールドを足すときは 4 か所をそろえて直す。M3 の参考 = `set_scroll_invert` と `set_ui_language` の「保存済みと同じなら書かない・失敗で変数を戻す」が同型 2 か所（3 か所目が出たら共通化を検討）

### 多言語対応（phase 72 由来）

- phase 72 の /refactor_check の境界の候補: `controllers/config_io/keymap_set_io.py` の `save_keymap_set_to` が 80 → 約 90 行（文言を `tr` の複数行の呼び出しへ置き換えた分の増加・処理は不変）/ `dialogs/action_dialog.py` は 597 → 643 行（+105 / −59・純増 46）。次に処理を足すときに再判定する

### タスクバーのアイコン（phase 71 由来）

- `presentation/status_icon/status_icon.py` の `_STATES` は `HookDisplayState` の値の再列挙（`typing.get_args` で導ける）・対応する大きさの直値 `(16, 32, 48)` / `[16, 32]` が同ファイルに 3 か所。状態を足すフェーズが来たら定数へ寄せる（refactor_check M4・M6 の境界事例・phase 71）
- 保留（ユーザー判断 2026-11-01）: `update_status` が文言の組み立て中に例外で終わるとアイコンだけ先に変わる（反映を文言の後へ移すなら暫定 54 §3.2 の位置の変更）/ 土台が 1 つの大きさだけのとき足りない大きさを印だけで補うか（phase 71）

### 保存・確認ダイアログ（phase 68 由来）

- `features.md` §4.6「未使用ファイルの整理…」の①が「保存する / 中止する」の 2 択と書かれているが、実装は askyesno「整理の前に保存が必要です。保存しますか？」（`orphan_sweep_io.py`。phase 68 より前からのずれ・phase 68 完了判定前レビューで発見）
- `/refactor_check` の参考: `config_io/choice_dialog.py`（ボタン名で選ぶ確認）と `config_io/hotkey_presets_io.py` の `confirm_overwrite` が同じ形（2 か所）。3 か所目が出たら共通化（phase 68）

### カーソルグリッド（phase 56 由来・旧称「画面の枠」）

- task_07 統合レビューの保留: L1（`ScreenGridController.sync` のたびに枠を描き直す）/ L5（`cell_label.py` の中央の文字のフォントを描くたびに作る）/ L6（`keymap_panel_controller.py` 671 行に枠の編集の文脈とキー名の解決がある → idea_45 と一緒に移す）。色の直値の重複（`#202028` が `dialogs/grid_editor_window.py` と `screen_grid/grid_overlay_window.py`）→ idea_44 の配色の見直しで定数化（phase 56）

### キーの名前の解決と送信（phase 62 由来）

- phase 66 の /refactor_check の境界: `presentation/screen_grid/grid_editor_panel.py` の「記録先の選択が変わったら `editor._capture_target_changed()`」が 5 か所（`op_selected` 2・`sub_selected` 3）。選択の変更を 1 か所に集める余地（増えたら共通化）。直値 200 ms / 100 ms / 5 秒は `key_capture_hook.py` に名前なし（意味は既存定数と別）
- phase 65 の /refactor_check M3（ユーザー判断で保留）: `application/held_inputs.py` の `resolve_send` → `identity_of` → `("key", scan, extended)` の 3 行組が 3 か所（`_key_identity`・`press_key`・`release_key`）。`(identity, send)` を返す内部関数 1 つにまとめられる。4 か所目が出たら実施
- `/refactor_check` M6 の参考: 走査コードの範囲 1〜255 の直値が `infrastructure/input_gateway._resolve_key` と `presentation/keyboard_layouts.resolve_layout_scan_code_from_key_name` の 2 か所（既存の定数と同値ではなく非該当・増えたら定数化）/ `LayoutController.should_debug_special_key_event` の未使用の引数 `resolved_key`（phase 62）

### キーボード表示（phase 55・59 由来）

- `presentation/keyboard_window.py`（523 行）の「マウスのボタンが押されていれば置き直す」が `_settle_size` / `_apply_pending_ratio` で同型 2 個・表示欄 2 つの「キーボードUIを常に手前」Checkbutton が同一 2 個（3 個目が出たら共通化。Win32 問い合わせの同型 4 個は提案書 21）（phase 55）
- phase 59 の /refactor_check の境界の候補: 切替キーの 2 つのダイアログで取得の無視の分岐（修飾キー単独・禁止のキー）が同形 / エラー文言「Windows キー・Caps Lock・AltGr は切替キーにできません」が application（`keymap_switch_batch.py:35`）と presentation（`keymap_panel_controller.py:181`）に重複。3 か所目が増えたら共通化（元からの修飾キー単独の判定 `("ctrl", "shift", "alt", "windows")` は 6 か所〔`key_capture.py`・`action_dialog.py`・`trigger_dialog.py`・`keyboard_window.py`・上の 2 つ〕）（phase 59）。
  phase 60 で再評価: 取得の入口は共通化しない（decisions_archive/60 の設計判断 #3）。`??` の判定は `tk_keys.is_unresolved_capture_key` に集約済み（案内の分岐は 4 入口だが文言は定数 1 つ）。残る同形の分岐は修飾キー単独・禁止のキーで、上の条件のまま

### ダイアログ・モーダル

- **同型スケルトンの共通化**。`suspend_hook_for_dialog` が **9 ファイル**、
  `bind("<Escape>")` + `protocol("WM_DELETE_WINDOW")` が **4 クラスで完全同型**
  （`keymap_set_history` / `orphan_sweep` / `quarantine_manage` / `reference_cleanup`。2026-09-22 実測）。
  phase 14 で `transient` + `grab_set` は `grab_modal` へ集約済、phase 15 で `destroy()` override は解消済で、
  **残るのはこの 2 種**。**phase 28（idea_26 の案 B）へは合流させないとユーザーが判断済**
  （2026-09-22。フォーカス集約とは別の責務でスコープが倍近くなるため）。
  なお phase 28 で**群 C の 5 経路・群 A の 4 経路へ Escape を追加した**ため、
  `bind("<Escape>")` の同型箇所は**増えた**
  （着手判断は再評価が要る）（phase 11 / 14 / 28 由来）
- `presentation/modal.py`（**187 行**・phase 29 で +54）で `grab_current()` の try/except と
  `winfo_exists()` / `winfo_viewable()` の try/except が**それぞれ 3 箇所**（M3 の境界）。
  **意図的に意味が違う**ため共通化しない（`grab_modal` は解決不能を「保持者なし」と扱い、
  預かり側は**解決不能と `None` を区別する**〔暫定仕様 15 §3-2(5)〕/ `<Unmap>` は「非表示」、
  他 2 箇所は「生存かつ表示中」）。**4 箇所目が同じ意味で増えたら**判定ヘルパ抽出を再判定（phase 17 由来）。
  phase 29 の `_restore_modal_focus` も `grab_current()` の解決不能を握り「生存かつ表示中」を判定する＝**4 箇所目相当**。
  ただし台帳・最小化中の記録の判定と 1 つの try に同居しており、**再判定の結果、据え置き**（phase 29 由来）
- `modal.py` の `_transient_depth`（phase 80）と `_belongs_to_app` が transient の連鎖を辿る同型の処理（2 か所・`_belongs_to_app` は `_transient_depth(...) is not None` にまとめられる・phase 80 の refactor_check で M3 非該当・deep-reviewer 10 で保留）。
- `tests_ui/test_minimize_grab_custody.py` が **603 行**（phase 29 で +282。a1〜a13 / b1〜b6・b8〜b11 / c10〜c13〔c13 は 2 件〕。phase 80 で 9 件追加し745 行）。
  テストは `/refactor_check` の判定対象外だが、組み立て（`_action` / `_manager` / `_minimize` / `_with_confirmation`）と
  a / b / c 系の分割を次に増えたら検討（phase 29 由来）
- `dialogs/action_dialog.py` が **418 行**で実装目安 300 行を超過（M1 の 600 行には未達）。
  `ActionDialog.__init__` も **113 行**（既存の巨大関数）。次に増えたら再判定（phase 22 由来）
- `controllers/config_io/child_save_dialog.py` が **369 行**（M1 非該当だが実装目安超過）+
  `_add_text_cell` の戻り値が素の dict（Phase β 由来）

### application / config_service

- `keyseq/application/config_service/__init__.py` は **840 行**（phase 36 で 1135 → 840。2026-09-27 実測）。残る実ロジックは起動時ロード・個別キーマップの読込と計画なし保存・
  シーケンスの正規化・パス基盤・`relocate_individual_hotkey_presets`。**パス基盤は動かしてよい**（`config_service.os.path` の patch は `os.path` をプロセス全体で
  差し替えるため名前空間の位置に依存しない。制約は「`__init__.py` が `os` を import」「`from os.path import` で事前束縛しない」だけ・phase 36 で判明）。
  次に増えたら、パス基盤（`__init__.py` の 1017-1121 行付近だった約 105 行）の切り出しを検討（phase 09〜11 / 36 由来）
- 個別 JSON IO の共通化は [idea_06](idea_06_individual_json_io_unification.md) が保持
  （**残る着手条件は「共通化の実需」1 つ**）。以下は**その近接領域**としてここで追跡する:
  - `config_io/` の `try/except Exception → messagebox.showerror → return False` が
    **6 ファイル・14 箇所**規模（2026-09-22 実測）。各箇所はメッセージ・保存対象が独立のため M3 非該当に
    倒しているが、さらに増えるなら共通化の再検討対象（phase 08 由来）
  - `controllers/config_io/` の IO クラス骨格（`__init__` + `run_*` → `config_service` 呼び出し →
    `format_*` → `messagebox`）と `presentation/*_text.py` の整形関数が **3 系統目**に達した（phase 11 由来）

- トリガー / シーケンスの属性（`run_to_end`・`select_before_run`）の読み書きの列挙が `domain/config.py`・`config_service/__init__.py`・`split_loading.py`・`split_payloads.py` の 4 モジュールに分かれている。
  phase 50 は既存の列挙箇所に 1 属性を並べただけで箇所数は不変（M4 非該当）。属性がさらに増えるなら属性の表から読み書きする形を検討（phase 50 由来）
- `split_payloads.py` の既存の 80 行超の関数 2 つ: `build_keymap_payloads`（100 行）/ `build_trigger_set_payloads`（106 行）。phase 36 では未変更（phase 36 由来）
- 引数の多い位置指定の補助関数（phase 36 の分割で生じた）: `split_payloads.py::_append_split_trigger_set_payloads` / `_build_split_trigger_set_entry`（13〜15 個）/
  `child_save_rows.py::_append_trigger_set_row`（13 個・同型の str を位置で並べる）/ `domain/config.py` の内部キー 4 要素タプル。
  次に触るときに keyword-only 化または文脈用の dataclass を検討（phase 36 由来）
- **phase 34 統合レビューの保留**: L-1 移行先キーマップと一覧を共有する別キーマップを個別保存すると移行先も一緒に書かれる（「移行先は必ず保存」の副作用・害なし）/
  L-7 「保存しない」共有メンバーの予想パスが一括保存の親参照に入る（安全側・掃除で除去）（phase 34 由来）
- `infrastructure/input_gateway.py` が 408 行に増え、送信（keyboard・拡張キー・テンキーの `SendInput`）・OS のリピート設定の取得・前面判定・名前の検査の責務が 1 ファイルに並ぶ。`_send_extended_event` と `_send_numpad_event` の `is_replaying` の退避が同型（2 個目）。次に送信系を足すときに送信の補助を別モジュールへ分けるかを再判定（phase 54 の /refactor_check・境界事例として不要に倒した）

### 定数・直値の重複（M6 の境界）

- `domain/config.py` の「キーがあれば `coerce_label`」2 行が **5 箇所**（`normalize_actions` の `type` / `button`、
  `ensure_config_compatibility` の内部キー 3 種）。内部キー名の文字列直値も同ファイル内で各 3 回（`_trigger_set_*` は phase 34 task_09 で定数化済・`_keymap_source_path` / `_sequence_source_path` は直値のまま）。
  提案書 [12](../modified_proposal/12_refactor_action_and_internal_key_type_coercion.md) は**見送り**（効果小・同一ファイル内で近接）。
  **同型がさらに増えたら** `_coerce_label_if_present(dst, src, key)` への集約を再判定（phase 30 由来）

- 履歴ファイル名の語幹が 2 箇所に直値（`config_service/__init__.py:27` の
  `KEYMAP_SET_HISTORY_RELATIVE_PATH = "keymap_set_history.json"` と
  `config_service/keymap_set_history.py:23` の `f"keymap_set_history.broken{suffix}.json"`）。
  **同値ではないため M6 非該当**だが、相対パス定数を変えると退避先の命名だけ黙ってずれる。
  語幹を定数化するか退避先を相対パス定数から導出する（挙動不変の小修正・数行）（phase 27 由来）
- `pane_width_rules.DEFAULT_LIST_CHARS = 26` が**未使用**で、`views/full_view/keymap_box.py:19` /
  `views/full_view/trigger_box.py:20` / `views/compact_view/trigger_box.py:18` が
  `width=26` の直値のまま（**compact 側も同値**。2026-09-22 実測）（phase 18 由来）
- 子カテゴリ列挙（`CHILD_KEYMAP` / `CHILD_TRIGGER_SET` / `CHILD_SEQUENCE`）が 8 ファイルに散在し、
  うち phase 10 の 2 ファイル（`config_service/parent_refs_cleanup.py` /
  `presentation/reference_cleanup_text.py`）は **`save_plan.CHILD_*` を import せず同値の文字列直値**。
  子の種類は仕様上 3 種で固定のため**優先度低**。まとめて触るときはここも対象にする（Phase β / phase 10 由来）
- `KEYBOARD_LAYOUT_COMBO_WIDTH` がボタン文言のモジュール `hook_button_texts.py` に同居
  （使う側は full_view / compact_view の 2 箇所）（phase 19 由来）
- `controllers/hook_controller.py` の `register_hook_buttons` と `apply_fixed_button_widths` の
  幅適用 2 行が同型（軽微）（phase 19 由来）
- `infrastructure/input_gateway.py` の `press_key` / `release_key` の「拡張キー判定 → 分岐」が同型
  （**2 箇所**。M3 の 3 箇所目が出たらヘルパ抽出を再判定する）（phase 21 由来）
- `application/sequence_runner.py` の `_run_to_end_step` で `stop_run_to_end()` → `_select_trigger(key)` → `return` が **3 箇所**
  （phase 31 で 1 箇所追加）。うち 2 箇所は直前に index を 0 へ戻し、phase 31 の 1 箇所は**意図して戻さない**（不正な行に残す）。
  共通部は既存メソッド 2 つの呼び出しのみのため `/refactor_check` は**不要**と判定。停止時の後処理が増えたら集約を再判定（phase 31 由来）

### デッドコード・据え置き（実害なし）

- `InputGateway.register_key_hook` の未使用は
  [idea_31](idea_31_input_gateway_dead_register_key_hook.md)
- `dirty_tracker.trigger_set_imported` が**読み手不在の残置状態**
  （production は書き込み 3 箇所のみで読むのはテストだけ。2026-09-22 実測）（Phase β 由来）
- `views/full_view/full_view.py:57` の `action_list` alias（`self.action_list = self.sequence_box.action_list`）は
  **据え置き**。`trigger_list` と違い production（`controllers/trigger_panel_controller.py` が
  `app.full_view.action_list` を 13 箇所で使用）の**生きた参照経路**であり、計画04 §1.3-2 の
  「App → View → Widget のパス」を満たす。所有 Widget 経由（`full_view.sequence_box.action_list`）へ
  統一したくなった場合のみ単独タスク化する
  （判断根拠は [decisions_archive/01](../../.claude_data/state/decisions_archive/01_view_ref_cleanup.md)）（phase 01 由来）
- `presentation/app.py:77` の `self.keymap_set_path = self.paths.resolve_keymap_set_path()` と、
  `config_paths.resolve_keymap_set_path()` の**引数なし分岐が実質デッド**
  （起動時に `startup_io` が必ず上書きするため）。`DEFAULT_KEYMAP_SET_FILENAME` を ConfigPaths 側へ
  寄せる代替案も挙動同値のため据え置き。まとめて触りたくなった時のみ単独タスク化する
  （判断根拠は [decisions_archive/05](../../.claude_data/state/decisions_archive/05_keymap_set_new_and_default_dir.md)）（phase 05 由来）
- `controllers/config_io/startup_io.py:19` の `keymap_set_path`（`str(startup.get(...) or "").strip()`）は
  config.json の生値を読むが**presentation 層**のため phase 25 のスコープ外。実害は
  「存在しないパスとして無視される」のみ。あわせて**「空」の定義が字面上非対称**
  （`split_payloads.py:363` の据え置き条件は `.strip()` しない）だが、
  **`entry_loaded=True` かつ値が空白のみ**という組み合わせは 3 経路のいずれからも生成されず**到達不能**
  （config.json を手編集した場合のみ）。触るなら `.strip()` 側へ揃える 1 行修正（phase 25 / 26 由来）
- `to_x` 欠落時に一覧表示が `(100, 200)→(, )` になる（実行はエラーになる）（phase 22 由来）

### 出力シーケンスの制御アクション（phase 37 由来）

- 統合レビュー Low（詳細は decisions_archive/37）: L3 `rekey_trigger_set` で移動先側の既存の保留を破棄 / L4 範囲外の位置の丸め方が旧実装（`% len`）と違う /
  L6 ループの対を削除しても「次に実行」を補正しない / L8 対応崩れが別の場所にあると張り直さず正しい終わりもエラー / L9 既に深さ超過があるとどこにも追加できない /
  L11 file_line は `_write_text` の例外も捕捉（text は外へ抜ける）/ L13 削除確認ダイアログの表示中はフックが止まらず待機の続きが発火しうる / L14 待機の続きの id 不一致時に記録しない（上流で取り消すので実害なし）
- `application/sequence_runner.py` 359 行で先行処理の呼び出しが単発・連続に重複（完了判定前レビュー L-8）。次に触るなら `sequence_steps` / `sequence_history` へ寄せる
- phase 38 由来（詳細は decisions_archive/38）: 通常アクション（hotkey 等）のエラー通知ダイアログ中の停止・別の連続実行の開始の後に続く処理を再照合していない（file_line だけ task_07a で対処）/
  統合 L2 `execute()` に file_line を渡したときの防御文言に内部名 `begin_file_line / poll_file_line` が出る（本番で到達しない・保留）
- phase 40 由来（詳細は decisions_archive/40）: file_line の開始・poll が「単発 / 連続実行 × 通常 / 呼び出し」の 4 組で並行構造（`file_line_wait.py` / `call_wait.py` / `call_run_to_end.py`。
  照合が経路ごとに違い統合のリスクが高いため提案書 17 から除外）/ 完了判定前レビュー L8 キーマップの切替・削除が失敗しても一時停止中のものは捨て済み（受容）/
  `StepOutcome.wait_ms` / `resume_position` / `resume` は in_call 専用（コメント追加は任意）
- phase 42 由来: `presentation/controllers/trigger_panel/trigger_panel_controller.py` が 606 行（M1 の基準 600 を超過・phase 42 の増分は +25 で非該当）。次に触るフェーズで分割を再判定
- phase 43 由来（完了判定前の deep-reviewer）: `domain/sequence_editing.py` の `can_move` が未使用（`can_move_block` へ置き換え済み）/ `KeymapEditDialog` の `validate` 引数が未使用（追加フローがまとめて設定へ移ったため）/ `KeymapSwitchBatchDialog` の Escape 処理が `bind_escape_close` を使わず同じ判定順を自前で持つ
- phase 46 由来（`/refactor_check` の M4 境界）: `(OP_BACK, OP_REWIND)` の所属判定が 3 → 8 か所（`action_control_fields.py` 4・`sequence_steps.py` 3・`sequence_control.py` 1）。戻す・先頭へのまとまりを表す定数か判定関数を `sequence_control` に置くか次に触るフェーズで再判定
- phase 43 由来（完了判定前の Codex 敵対的レビュー）: シーケンスの個別保存（`sequence_file_io.py:54-86`）はパスのダイアログ中にアクティブが変わると、保持した A の行を保存しつつ参照元・未保存の印を現在のアクティブ B へ付ける（phase 43 より前からの挙動・キーマップの個別保存の固定なし〔decisions 43 の task_06b 保留 L1〕と同類）

### テスト負債
- tests_ui で 1 回だけ `write_startup` が呼ばれた失敗（`compact_window_size` の保存・テスト名は未取得）。同じ実行を繰り返すと再現せず（phase 52 task_01 の検証で 2026-10-11 に発生・task_01 の変更とは無関係）。再発したらテスト名を取って切り分ける。**2026-10-14 再発（phase 57 task_02 の検証・tests_ui 全体の実行時のみ）: `tests_ui.test_compact_window.CompactWindowTest.test_automatic_full_view_and_maximized_sizes_are_not_saved`**（単独・モジュール単独では pass・実行順依存）
- `tests_ui/test_action_dialog_control.py` の 2 件（`test_focus_moves_to_type_combo_when_*_is_hidden`）は、Tk のルートを作るモジュール（`test_modal_grab`・`test_action_dialog_key_hold` 等）の**後に同じプロセスで走らせると**フォーカスが取れず落ちる（実行順への依存。名前順の一括実行では先に走るので落ちない。phase 51 task_05 で判明・既存）

- phase 36 の完了判定前レビューで判明したテストの無い経路: `save_runtime_data` の `keep_legacy_copy=True`（本番の呼び出し元 `keymap_set_io.py:136` は常に False・実質未使用の引数）/  `post_save_warnings=None` のときの `warnings.warn`（`assertWarns` の検査なし）/ `build_runtime_data_from_split` のアクティブキーマップ補完（一覧に無い `active_keymap_path` を読む分岐・専用テスト未確認）（phase 36 由来）
- `tests/test_input_gateway_drag.py::test_initial_move_failure_restores` が `mouseUp` の
  **非呼び出し**を固定していない / ドラッグ 4 キーの**ファイル層での永続化往復**テストが無い（phase 22 由来）
- `tests_ui/test_full_view_header_width.py` / `test_header_button_widths.py` は保存予約の遅延を
  延ばしていない（現状は予約取消で実害なし・揺れたら phase 19 task_03 と同じ対処）（phase 19 由来）

### レビュー保留（判断待ち・判断は decisions_archive が正）

- phase 72 統合レビューの D5（実行時に組み立てる文言キー 93 か所は完全性テストの照合の対象外。足りないと画面にキーがそのまま出るので実機目視で気づける）/ D6（日本語リテラルの静的検査の正規表現が全角記号・半角カナを拾わない。今残るのは全角空白 5 か所だけ）。判断は [decisions_archive/72](../../.claude_data/state/decisions_archive/72_multilingual_ui.md)
- phase 28 統合レビューの M4（`modal.py` の `_apply_initial_focus` が `grab_set()` と `<Destroy>` 登録の間にあり、
  ここで例外が抜けると復元ハンドラ未登録の窓が残る。現実的な失敗は `TclError` で握っており実害は低い）。
  判断は [decisions_archive/28](../../.claude_data/state/decisions_archive/28_dialog_keyboard_focus.md)
- phase 18 完了判定前レビューの保留 3 件（ドラッグで元の希望幅へ戻したとき最小幅が更新されない場合 /
  `pane_measure.py` の SequenceBox 構造依存 / phase 18 以前の tests_ui が実 config を読む）。
  判断は [decisions_archive/18](../../.claude_data/state/decisions_archive/18_full_view_resizable_panes.md)
- 一時メッセージのラベルを App 属性で直接参照する案（phase 01 の「生やし」解消と衝突）。
  判断は [decisions_archive/20](../../.claude_data/state/decisions_archive/20_full_view_min_height.md)
- `controllers/pane_layout/pane_layout_controller.py` は **281 行**でドラッグ・レイアウト適用・
  ウィンドウ幅の保存の 3 まとまりを持つ。phase 20 で「高さの処理は独立したまとまりではない」として
  **分割不要と再判定済**。次にまとまりが増えたら再判定する（phase 18 / 20 由来）

- `application/action_executor.py` の counter_text 分岐（phase 76）: `counter_text_error` だけが `_labeled` のキーを f-string で組み立てる（他の分岐は明示キー）・`"counter_text"` は定数 `ACTION_TYPE_COUNTER_TEXT` があるのに他の種別と同じく直値で並ぶ。種別の直値を定数へ寄せるときに一緒に直す（phase 76 の refactor_check は不要判定）
- `application/config_service/save_plan_execution.py` の `preview_child_payloads` と `_write_runtime_payloads`: 子の並び（sequences → trigger_sets → keymaps）とキーマップのパスの解決が 2 か所に書かれている（片方だけ変えるとサンプルの衝突判定がずれる）。次に保存の書き出し順を触るとき、子を `(path, payload)` で並べる処理を 1 つにして書き込み側もそれを使う（phase 77 task_02 の deep-reviewer 指摘①・保留）
