# 過去の「現在の参照先」の記録（past_areas.md・凍結）

> 2026-11-26 に `instructions/phase/current.md` から移した経緯記録。**凍結・追記しない**。
> 各フェーズの判断と残件の正は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`、
> 未着手の残件は `instructions/backlog/`（idea・`deferred_tasks.md`）。リンクは移す前の `instructions/phase/` 基準のまま。

## 完了フェーズの要約（phase 80・78〜40）

- その前の完了フェーズ = [phase 80](80_win_d_restore_blank_dialog/phase.md)（2026-11-25・Win+D から戻したときに入れ子のダイアログが白いまま = 原因は Tk 8.6.15（Windows）で transient 3 段以上の窓が最小化からの復元で中身の HWND を失うこと〔Win+D 固有でない〕・Windows では最小化の間だけ深さ 3 以上のモーダルの transient を外して隠し、復元で表示し直して grab を戻した 300ms 後に付け直す。直接改訂モード〔暫定なし・正本 `features.md` §4.6 に例外（Windows）〕・presentation + os_backend の窓の契約に 1 メソッド・JSON スキーマ不変・起票元 [idea_61](../backlog/idea_61_win_d_restore_blank_dialog.md)・判断は [decisions_archive/80](../../.claude_data/state/decisions_archive/80_win_d_restore_blank_dialog.md)・refactor_check 不要）。
- その前の完了フェーズ = [phase 78](78_action_hotkey_save_validation/phase.md)（2026-11-23・アクションの hotkey の保存時の検査と正規化。直接改訂モード〔暫定なし〕・JSON スキーマ不変・起票元 [idea_03](../backlog/idea_03_action_hotkey_save_normalization.md)・判断は [decisions_archive/78](../../.claude_data/state/decisions_archive/78_action_hotkey_save_validation.md)・refactor_check 不要）。
- その前の完了フェーズ = [phase 77](77_sample_in_user_folder/phase.md)（2026-11-23・サンプルを config/user/ へ書き出す。暫定仕様先行モード〔暫定 59 v0.2 凍結〕・JSON スキーマ不変・判断は [decisions_archive/77](../../.claude_data/state/decisions_archive/77_sample_in_user_folder.md)・refactor_check 不要）。
- その前の完了フェーズ = [phase 76](76_counter_expansion/phase.md)（2026-11-23・カウンター機能の拡張。判断は [decisions_archive/76](../../.claude_data/state/decisions_archive/76_counter_expansion.md)）。
- その前の完了フェーズ = [phase 75](75_mac_support/phase.md)（2026-11-22・macOS 対応。判断は [decisions_archive/75](../../.claude_data/state/decisions_archive/75_mac_support.md)）。
- その前の完了フェーズ = [phase 74](74_key_symbol_display/phase.md)（2026-11-09・記号キーのキー名の表示〔表 36 個・キーボードUIの枠 / トリガー一覧 / key_hold の一覧〕+ 置換先の Shift+¥ / Shift+ろ の保存と Shift の要る文字の送信。直接改訂モード・JSON スキーマ不変・判断は [decisions_archive/74](../../.claude_data/state/decisions_archive/74_key_symbol_display.md)・refactor_check 不要）。
- その前の完了フェーズ = [phase 73](73_welcome_first_launch/phase.md)（2026-11-09）。
- その前の完了フェーズ = [phase 72](72_multilingual_ui/phase.md)（2026-11-04・画面の文言の多言語対応〔日本語・英語・メニュー「設定」→「Language」で選び次回の起動から反映・「今すぐ再起動」可・文言は `keyseq/shared/i18n/locales/<code>.json`・ヘルプ本文は `help_<code>.json`・訳の無い文言は英語・言語の一覧は置いたファイルから・config.json の `ui_language`〔無いときは英語〕・全層の文言をキー化〔日本語は不変〕・英語の表記 E1〜E7・出力シーケンスの一覧の行頭の印は全言語共通の英語〕。暫定仕様先行モード〔暫定 55 v0.7 凍結〕・起票元 = ユーザー要望・3 言語目以降は [idea_56](../backlog/idea_56_more_ui_languages.md)・判断は [decisions_archive/72](../../.claude_data/state/decisions_archive/72_multilingual_ui.md)）。
- その前の完了フェーズ = [phase 71](71_taskbar_status_icon/phase.md)（2026-11-01・タスクバーのアイコンで状態を表示〔窓のアイコンの右上にステータス欄のフックの 3 状態と同じ印 = 緑の円 / 赤の正方形 / 黄の棒 2 本・白い正方形の上・土台はサンプル画像をユーザーが差し替え・子窓は既定のアイコンで追従・起動時に AppUserModelID〕。暫定仕様先行モード〔暫定 54 v0.4 凍結〕・JSON スキーマ不変・起票元 = [idea_55](../backlog/idea_55_taskbar_status_icon.md)・判断は [decisions_archive/71](../../.claude_data/state/decisions_archive/71_taskbar_status_icon.md)）。
  [phase 70](70_help_window/phase.md)（2026-10-29・ヘルプの作成〔メニュー「ヘルプ」・非モーダルで同時に 1 つのヘルプの窓〔タブ「主要機能」「QA」・2 段の開閉・絞り込み・入力欄のフォーカスでフック停止〕・ダイアログ 12 か所の「?」〔下端の左寄せ〕・バージョン情報〔`__version__` 0.1.0〕・同梱物 14 件のライセンス全文・「画面の枠」→ カーソルグリッド / マス〕。暫定仕様先行モード〔暫定 53 v0.7 凍結〕・JSON スキーマ不変・起票元 = ユーザー要望・判断は [decisions_archive/70](../../.claude_data/state/decisions_archive/70_help_window.md)・refactor_check 推奨 → [提案書 27](../modified_proposal/27_refactor_help_window.md)（保留））。
  [phase 69](69_keyboard_ui_key_labels/phase.md)（2026-10-26・キーボードUIのキー名の表示と最小サイズ〔キーの内側に収まるまで文字を縮め `\n` でだけ改行・レイアウトの JSON の `key_display_names` で送信先の表示名・最小 = 1u のキー 27px・変えた幅をレイアウトごとに `keyboard_window_widths` へ記録・見本 us_tkl.json〕。暫定仕様先行モード〔暫定 52 v0.4 凍結〕・**JSON スキーマ = 任意キーの追加**・起票元 = ユーザー要望・判断は [decisions_archive/69](../../.claude_data/state/decisions_archive/69_keyboard_ui_key_labels.md)・refactor_check 推奨 → [提案書 26](../modified_proposal/26_refactor_keyboard_ui_key_labels.md)（保留））。
  [phase 68](68_ui_terminology/phase.md)（2026-10-24・UI 文言の用語統一〔用語表 A1〜A21・個別の表現 C1〜C16・表記規則 D1〜D11・はい / いいえ の確認 3 か所をボタン名の共通ダイアログ `config_io/choice_dialog.py` へ〕。暫定仕様先行モード〔暫定 51 v0.8 凍結〕・JSON スキーマ不変・起票元 = ユーザー要望・正本 = 新規 `spec_detail/ui_terms.md` + 正本全体の用語・判断は [decisions_archive/68](../../.claude_data/state/decisions_archive/68_ui_terminology.md)）。
- その前の完了フェーズ = [phase 67](67_mouse_scroll_action/phase.md)（2026-10-21・出力シーケンスのマウススクロール〔新しい種類 `mouse_scroll`・上下左右・ノッチ数 / 生の値（120 = 1 ノッチ）・座標は任意・1 回の `SendInput` で WHEEL / HWHEEL・不正な行は止まる系〕。暫定仕様先行モード〔暫定 50 v0.4 凍結〕・**JSON スキーマ = 種類の追加**・起票元 = ユーザー要望・判断は [decisions_archive/67](../../.claude_data/state/decisions_archive/67_mouse_scroll_action.md)）。
  [phase 66](66_capture_jis_special_keys/phase.md)（2026-10-21・キーの取得で JIS の特殊キーを取る〔取得の間だけ suppress フックでレイアウトの行に当たるキーを抑止し、フックの実行時と同じ名前を 8 入口へ渡す・アプリの窓が前面のときだけ〕。暫定仕様先行モード〔暫定 49 v0.5 凍結〕・JSON スキーマ不変・起票元 idea_50・判断は [decisions_archive/66](../../.claude_data/state/decisions_archive/66_capture_jis_special_keys.md)）。
  [phase 65](65_layout_snapshot_for_hook/phase.md)（2026-10-21・受け取りと送信が同じレイアウトの写しを使う〔受け取り・送信・キーボードUI を `LayoutController` の写し 1 つへ・外部レイアウトの JSON の変更は選び直し〔同じレイアウトでも〕・読み直しのときだけ反映・押したままのキーは押したときの送り方で送る〕。暫定仕様先行モード〔暫定 48 v0.3 凍結〕・JSON スキーマ不変・起票元 idea_51・判断は [decisions_archive/65](../../.claude_data/state/decisions_archive/65_layout_snapshot_for_hook.md)）。
  [phase 64](64_external_layout_path_base/phase.md)（2026-10-21・外部キーレイアウトのパス基準の統一〔登録・読込・表示を正本 §5.7 どおりの `config` ルート基準の相対へそろえ、再起動のたびに登録が消える不具合を修正〕。直接改訂モード〔暫定なし〕・JSON スキーマ不変・起票元 idea_13。既存の壊れた値の移行・重複除去はしない〔利用者が JSON を手で直す〕・判断は [decisions_archive/64](../../.claude_data/state/decisions_archive/64_external_layout_path_base.md)）。
  [phase 63](63_make_only_keys/phase.md)（2026-10-20・押下だけが続けて届くキー〔無変換 241・変換 242 を「押した / 離した」に組み直す・リピートなし・離した直後 60 ms 以内の押下は押し続けの続き・直接置換の枠は灰色がかった緑・名前は `extra_scan_codes`〕。暫定仕様先行モード〔暫定 46 v0.5 凍結〕・**JSON スキーマ追加**〔レイアウトの任意キー `extra_scan_codes`〕・判断は [decisions_archive/63](../../.claude_data/state/decisions_archive/63_make_only_keys.md)）。
  [phase 62](62_special_keys_from_layout_only/phase.md)（2026-10-18・特殊キーの名前をレイアウトだけが決める。暫定仕様先行モード〔暫定 45 v0.5 凍結〕・判断は [decisions_archive/62](../../.claude_data/state/decisions_archive/62_special_keys_from_layout_only.md)）。
  [phase 61](61_keyboard_ui_vk_to_scan_code/phase.md)（2026-10-17・キーボードUI の取得で VK を走査コードへ変換する。直接改訂モード・判断は [decisions_archive/61](../../.claude_data/state/decisions_archive/61_keyboard_ui_vk_to_scan_code.md)）。
  [phase 60](60_ime_off_during_key_capture/phase.md)（2026-10-16・キーの取得中は IME を OFF にする〔取得の 8 入口で取得の間だけアプリ自身の IME を OFF・終了で復元 / `??` を全入口で記録せず取得を続ける〕。暫定仕様先行モード〔暫定 44 v0.4 凍結〕・JSON スキーマ不変・判断は [decisions_archive/60](../../.claude_data/state/decisions_archive/60_ime_off_during_key_capture.md)）。
  [phase 59](59_keyboard_ui_left_right_modifiers/phase.md)（2026-10-16・キーボードUI の左右の修飾キーの区別と割り当て禁止のキー〔左右の Shift・Ctrl・Alt・Win の枠を左右別のキー名で表示・編集 / Windows キー・Caps Lock・AltGr 配列の右 Alt〔標準の id `alt_gr`〕をキーマップの元キーと切替キーに割り当て禁止 / 切替キーの取得で判別できないキー〔`??`〕は案内 / jis.json・de.json の見本〕。暫定仕様先行モード〔暫定 43 v0.6 凍結〕・JSON スキーマ不変・判断は [decisions_archive/59](../../.claude_data/state/decisions_archive/59_keyboard_ui_left_right_modifiers.md)）。
  [phase 58](58_window_size_fit/phase.md)（2026-10-15・画面サイズの調整〔フル表示の 3 枠を枠ごとに縦スクロール・最小の高さ = 要求高さ − メイン領域 + ceil(H/2)〔+3 で 931 → 635px〕・各枠の最小幅にスクロールバーの幅 / 省略表示の「フック」「表示」を Expander で開閉・保存・見出しはキーでも開閉 / ステータス欄のフックを ON・OFF・一時停止の 3 状態に〕。暫定仕様先行モード〔暫定 42 v0.3 凍結〕・**JSON スキーマ変更あり**〔config.json の任意キー `compact_header_view`〕・判断は [decisions_archive/58](../../.claude_data/state/decisions_archive/58_window_size_fit.md)）。
  [phase 57](57_grid_crosshair_nudge/phase.md)（2026-10-14・画面の枠の十字マーク・矢印でクリック位置の微調整・操作キーの任意化〔選んだ枠のクリック点に十字・矢印で min(16px, 枠の 1/8)・Shift で 1px・操作キーは keymap ごとに各 1 つで付け替え可〔Esc = 戻る・num enter = クリックは固定〕・編集の窓のドラッグ中の十字・パネルの 2 列化とスクロール〕。暫定仕様先行モード〔暫定 41 v0.4 凍結〕・**JSON スキーマ変更あり**〔`grid` の任意キー `ops`〕・判断は [decisions_archive/57](../../.claude_data/state/decisions_archive/57_grid_crosshair_nudge.md)） /
  [phase 56](56_screen_grid_cursor/phase.md)（2026-10-13・画面の枠でカーソル移動・クリック〔枠 ON のキーマップがアクティブな間だけ枠を表示・キーで枠を選びカーソルを中心へ・Enter で左 / Shift+Enter で右クリック・Space で細分化・Tab で画面の切替・最上段は画面ごとに編集の窓でドラッグして記録・キーの表示位置〕。暫定仕様先行モード〔暫定 40 v0.7 凍結〕・**JSON スキーマ変更あり**〔keymap の任意キー `grid`〕・判断は [decisions_archive/56](../../.claude_data/state/decisions_archive/56_screen_grid_cursor.md)） /
  [phase 55](55_keyboard_ui_window/phase.md)（2026-10-12・キーボードUIのウィンドウ改善〔ステータス欄の削除とタイトル表示 / 「キーボードUIを常に手前」とダイアログ表示中の一時解除 / 縦横比固定〕。暫定仕様先行モード〔暫定 39 v0.6 凍結〕・判断は [decisions_archive/55](../../.claude_data/state/decisions_archive/55_keyboard_ui_window.md)） /
  [phase 54](54_numpad_key_distinction/phase.md)（2026-10-11・テンキーの区別。暫定 38 v0.5 凍結・判断は [decisions_archive/54](../../.claude_data/state/decisions_archive/54_numpad_key_distinction.md)） /
  [phase 53](53_repeat_stop_on_own_foreground/phase.md)（2026-10-11・アプリの窓が前面のときはキーリピートしない〔送り直しの発火ごとに前面の窓のプロセスを判定〕。暫定仕様先行モード〔暫定 37 v0.4 凍結〕・判断は [decisions_archive/53](../../.claude_data/state/decisions_archive/53_repeat_stop_on_own_foreground.md)） /
  [phase 52](52_key_hold_auto_repeat/phase.md)（2026-10-11・key_hold のキーリピート〔key_hold の任意キー `repeat`・**JSON スキーマ変更あり**〕。暫定仕様先行モード〔暫定 36 v0.4 凍結〕・判断は [decisions_archive/52](../../.claude_data/state/decisions_archive/52_key_hold_auto_repeat.md)） /
  [phase 51](51_key_press_release_actions/phase.md)（2026-10-11・キーの押下 / 解放アクション `key_hold` と自動で離す安全策。暫定仕様先行モード〔暫定 35 v0.9 凍結〕・判断は [decisions_archive/51](../../.claude_data/state/decisions_archive/51_key_press_release_actions.md)） /
  [phase 50](50_select_before_run/phase.md)（2026-10-09・確認して実行〔select_before_run〕と戻す・先頭への対象を一覧の選択へ。暫定仕様先行モード〔暫定 34 v0.6 凍結〕・判断は [decisions_archive/50](../../.claude_data/state/decisions_archive/50_select_before_run.md)）/
  [phase 49](49_status_truncation_tooltip/phase.md)（2026-10-07・ステータスの見切れのツールチップ。直接改訂モード・判断は [decisions_archive/49](../../.claude_data/state/decisions_archive/49_status_truncation_tooltip.md)）/
  [phase 48](48_compact_sequence_view/phase.md)（2026-10-07・省略表示の出力シーケンス欄。暫定仕様先行モード〔暫定 33 v0.6 凍結〕・判断は [decisions_archive/48](../../.claude_data/state/decisions_archive/48_compact_sequence_view.md)）/
  [phase 47](47_action_dialog_layout_cleanup/phase.md)（2026-10-06・アクションの追加・編集ダイアログの整理。直接改訂モード・判断は [decisions_archive/47](../../.claude_data/state/decisions_archive/47_action_dialog_layout_cleanup.md)）/
  [phase 46](46_back_rewind_target/phase.md)（2026-10-06・戻す・先頭への対象トリガー指定。暫定仕様先行モード・判断は [decisions_archive/46](../../.claude_data/state/decisions_archive/46_back_rewind_target.md)）/
  [phase 45](45_call_step_and_view/phase.md)（2026-10-05・呼び出しのステップ実行と呼び出し先の表示・
  判断は [decisions_archive/45](../../.claude_data/state/decisions_archive/45_call_step_and_view.md)）/
  [phase 44](44_child_save_dialog_layout/phase.md)（2026-10-04・子ファイル保存ダイアログの高さと列幅の調整・
  判断は [decisions_archive/44](../../.claude_data/state/decisions_archive/44_child_save_dialog_layout.md)）/
  [phase 43](43_list_reorder_range_copy/phase.md)（2026-10-04・一覧のドラッグ移動・範囲選択・複製・
  判断は [decisions_archive/43](../../.claude_data/state/decisions_archive/43_list_reorder_range_copy.md)）/
  [phase 42](42_listbox_click_selection_sync/phase.md)（2026-10-02・一覧のクリックで選択と下線がずれる不具合の修正・
  判断は [decisions_archive/42](../../.claude_data/state/decisions_archive/42_listbox_click_selection_sync.md)）/
  [phase 41](41_ime_off_while_typing/phase.md)（2026-10-02・文字の送信中は送り先の IME をオフにする・
  判断は [decisions_archive/41](../../.claude_data/state/decisions_archive/41_ime_off_while_typing.md)）/
  [phase 40](40_sequence_call/phase.md)（2026-10-01・制御アクション第 2 弾 後半 = 呼び出し・
  判断は [decisions_archive/40](../../.claude_data/state/decisions_archive/40_sequence_call.md)）。
  **それ以前の完了フェーズは `.claude_data/state/decisions.md`「アーカイブ索引」→
  `decisions_archive/<phase>.md` が正**（要約をここへ積まない）。

## 過去の「直近の領域」

- **直近のフェーズが扱った領域 = 画面の文言の多言語対応**（phase 72）。正本 = `features.md` §4.6「言語」「一覧の表示形式」「ヘルプの窓」/ `data_schema.md` §5.4 `ui_language` / `ui_terms.md` §1「多言語の扱い」・§2 英語の列・§3「英語の表記の規則」/ `architecture.md` §3.2（shared）/ 地図 = `codebase_map.md`「画面の文言の多言語対応」。**新しい文言は `ja.json` と `en.json` の両方にキーを足し、ソースに日本語を書かない**（静的テストが検出）。残件 = 3 言語目以降（idea_56）/ 保留 D5（実行時に組み立てるキーは照合の対象外）・D6（静的検査が全角記号・半角カナを拾わない）。次の予定 = Mac 対応
- その前の領域 = **ヘルプ・バージョン情報・ライセンスとカーソルグリッドの呼び名**（phase 70）。正本 = `features.md` §4.6（メニュー「ヘルプ」・ヘルプの窓・「?」・モーダルダイアログの作法の例外・バージョン情報・ライセンス）/ `key_input.md` §7.2 / `ui_terms.md` A22 / 本文 = `presentation/help/content/help_ja.json`（多言語化ではここを言語別に増やす）/ 地図 = `codebase_map.md` の `presentation/help/`。
- その前の領域 = **キーボードUIのキーの文字・最小の大きさ・幅の記録**（phase 69）。正本 = `features.md` §4.6「キーボード表示のウィンドウ」（最小の大きさ・幅の記録・キーの文字・レイアウトの JSON の `label` の改行と `key_display_names`）/ `data_schema.md` §5.4 `keyboard_window_widths` / 地図 = `codebase_map.md` の phase 69。保留 = `decisions_archive/69` の指摘 6・7・9。
  さらに前 = **UI 文言の用語と表記**（phase 68）。正本 = `spec_detail/ui_terms.md`（新しい文言はここに従う）/ 確認ダイアログ = `features.md` §4.6「保存先の確認ダイアログ」・地図 = `codebase_map.md` の `choice_dialog.py`。**残件** = 提案書 25 は 2026-10-25 実施済（表は `presentation/child_kind_labels.py` に 1 つ。多言語化ではこの表を辞書へ移す）/ アクションの種類の内部名の表示名化（多言語化で）/ 下記「別タスク化候補 > 保存・確認ダイアログ」。
- その前の領域 = **出力シーケンスのマウススクロール**（phase 67）。正本 = `data_schema.md` §5.11.1・§5.11.10 / `features.md` §4.2 冒頭・§4.2.12・§4.6（一覧の表示形式・出力シーケンスの編集）/ 地図 = `codebase_map.md`「アクションの実行」「マウス操作」の phase 67 の項。**残件** = decisions_archive/67 の保留（L6 = executor のテストの抜け・L7 = `amount` の文字列の受け入れの広さ）・暫定 50 §10 のスコープ外（間隔・速度・押したまま・画面の枠でのスクロール）。
- その前の領域 = **キーの名前（取得・フック・送信）と押下だけのキー**（phase 60〜63）。phase 63 = 押下だけが届くキーの組み直し（正本 `key_input.md` §7.1「押下だけが届くキー」・§7.3「押下だけのキーの組み直し」・`features.md` §4.6「レイアウトの JSON の `extra_scan_codes`」「押下だけのキーの直接置換の枠」/ 地図 = `codebase_map.md` の phase 63 の項）。**残件（phase 63）** = idea_53（送信の最中の物理の入力の素通り・直ればリピートを戻せる）/ idea_54（IME の切り替え・再発時）/ decisions_archive/63 の保留（L4〜L7）。計測用のデバッグ出力（`debug_jis_special_key_events`）は残している。phase 62 = フックの実行時と送信のキー名をレイアウトだけが決める（正本 `key_input.md` §7.1「フックの実行時のキー名の出どころ」・§7.7「キー名 → 走査コードの解決の順」・`features.md` §4.6「レイアウトの JSON の `scan_code`」/ 地図 = `codebase_map.md` の `keyboard_layouts.py`・`LayoutController`・キーの送信の節）。**残件（phase 62）** = idea_50 は phase 66 で完了（残件 = decisions_archive/66 の保留 deep 8・9）/ idea_51 は phase 65 で完了（残件 = decisions_archive/65 の保留 低 3・5・10）/ idea_52 は phase 63 で完了 / 下記「別タスク化候補 > キーの名前の解決と送信」。phase 61 = キーボードUI の編集のキーの名前（VK → 走査コード → レイアウトだけ・正本 `key_input.md` §7.4）。phase 60 = キーの取得中の IME と判別できないキー。正本 = `key_input.md` §7.4「取得の入口」「取得中の IME」「判別できないキー」/ 地図 = `codebase_map.md`（phase 60 の節）。**残件** = idea_48（取得中のフック再開）/ decisions_archive/60 の保留（L4〜L6）・入口の重なりは実機未確認（受容）。
- その前の領域 = **キーボードUI の左右の修飾キーと割り当て禁止のキー**（phase 59）。正本 = `features.md` §4.3「割り当て禁止のキー」・§4.6「キーボード表示のウィンドウ」/ `key_input.md` §7.1・§7.4 / 地図 = `codebase_map.md`（phase 59 の節）。**残件** = （idea_47 は phase 61 で対応済み）/ decisions_archive/59 の保留（低-1〜3）・JIS の Caps 単独のフック側の名前は未実測（受容）。
- その前の領域 = **画面サイズの調整**（phase 58）。正本 = `features.md` §4.5（ステータス欄のフックの 3 状態）・§4.6「フル表示の幅配分」「フル表示の 3 枠のスクロール」「省略表示の上部の開閉」「省略表示のウィンドウ」/ `data_schema.md` §5.4（`compact_header_view`）/ 地図 = `codebase_map.md`（`views/full_view/scroll_area.py`・`controllers/compact_header_controller.py`・`pane_measure`）。**残件** = decisions_archive/58 の保留（スクロールバーの出し入れで枠の要求幅が約 17px 増減・3 枠同時のスクロールバー / 一覧のスクロールバーの上のホイールの自動テストなし・開いた見出しと閉じた見出しの様式の違い）。
- その前の領域 = **カーソルグリッドでカーソル移動・クリック**（phase 56・57。phase 70 で「画面の枠」から改名）。正本 = `features.md` §4.7 / `data_schema.md` §5.6.1 / `key_input.md` §7.3・§7.4 / `nonfunctional.md`「カーソルグリッドの座標系」/ 地図 = `codebase_map.md`「カーソルグリッド（phase 56・57）」。**残件** = idea_44（枠の配色）/ idea_45（既存のキー取得の記号キー名）/ phase 56 task_07 の保留 L1・L5（decisions_archive/56）/ phase 57 の見送り（OK の拒否の理由に画面名・4 経路の ops の往復の結合テスト・decisions_archive/57）。その前の phase 55 の領域（キーボード表示のウィンドウ）の残件 = 下記「別タスク化候補」の keyboard_window の 1 行。
- **直近の一連の作業が扱っている領域 = 出力シーケンスの制御アクション**（phase 37〜40）。system 種別（ループ / カウンター / 待機 / 戻す / 先頭へ）と file_line（**JSON スキーマ変更あり**・phase 37）。
  phase 38 で file_line の読込をワーカー + UI 側 50 ms 確認タイマーへ移し、上限 5 秒・同じ読込キーの待ち合わせ・読込結果のキャッシュを加えた。構成セットの読込等で連続実行を常に停止する（既存挙動の変更）。
  正本 = `data_schema.md` §5.11.1・§5.11.5〜5.11.8・§5.13.1 / `features.md` §4.2.1〜4.2.10・§4.5・§4.6 / 地図 = `codebase_map.md`「出力シーケンスの制御アクション」節。
  phase 39 で system に停止（`op: stop`・連続実行の区切り）を加えた（`features.md` §4.2.8）。
  phase 40 で呼び出し（`op: call`・`target`・**JSON スキーマ変更あり**・§4.2.9）と入力の受け付け・一時停止（§4.2.10）を加え、待機を「送った後の待ち」に改めた（§4.2.5）。
  phase 45 で呼び出しの行ごとにステップ（既定）/ 一括（`all`・**JSON スキーマ変更あり**）を選べるようにし、写しをやめて参照中の印で呼び出し元と呼び出し先を連動させ、呼び出し先の表示枠（`call_view_heights`）を加えた（§4.2.6・§4.2.8・§4.2.9・§4.2.10・§4.6）。
  phase 46 で戻す・先頭への行に任意キー `target`（**JSON スキーマ変更あり**）を加え、指定があれば直前のトリガーに関係なく指定先を戻す / 先頭へ移す（§4.1・§4.2.6・§4.6）。
  phase 50 で確認して実行（§4.2.11・`select_before_run`・**JSON スキーマ変更あり**）を加え、`target` の無い戻す・先頭への対象を一覧の選択へ（使えなければ直前のトリガー・§4.2.6）・待機明けに選択が変わっていれば選び直さない（§4.2.5）とした。
  **残件** = カウンター条件分岐（idea_37）/ 直前のトリガーの廃止ほか（idea_39 の残り）/ 下記「別タスク化候補 > 出力シーケンスの制御アクション」。
  phase 41 で text / file_line の送信中は送り先の IME をオフにした（`key_input.md` §7.7・`infrastructure/ime_control.py`。IME オンでカタカナがひらがなの変換待ちになる不具合）。
  phase 42 で一覧のクリックで選択と下線がずれる不具合を直した（presentation の `listbox_utils.py`。押している間は帯だけ・離したときに反映）。
- その前の領域 = **トリガー一覧のキーマップ従属化**（phase 34）。
  トリガー一覧（と従属するシーケンス）はキーマップに従属し、キーマップ＝モードとして一括で切り替わる（**JSON スキーマ変更あり**）。
  正本 = `data_schema.md` §5.13（runtime の形・共有・移行・保存計画）+ §5.2/5.4/5.5/5.6/5.8.x / `key_input.md` §7.3
  （優先順位 **停止 > トグル > 直接切替 > トリガー > 置換**・重なりの表・切替中の受け付け停止）/ `features.md` §4.1・§4.3・§4.5。
  実装の地図 = `codebase_map.md`「キーマップとトリガーセット（phase 34）」節
  （口 = `domain/keymap_triggers.py`・重なり = `application/key_overlap.py`・UI = `controllers/keymap_panel/`）。
  phase 35 で旧形式の読込元が**存在しないファイル**なら移行しない（§5.13.3-8）と定め、移行の境界値をテストで固定した。
  phase 36 で保存・読込まわりを挙動不変で分割した（`config_service/__init__.py` 1135 → 840 行・80 行超の 5 関数を解消・`split_loading.py` 787 → 559 行。地図は `codebase_map.md` の ConfigService 節）。
  **残件** = 統合レビュー保留 L-1・L-7 / phase 36 のレビューで出た引数の多い補助関数・テストの無い経路（いずれも「別タスク化候補」）/
  共通トリガー層は [idea_36](../backlog/idea_36_common_trigger_layer.md)（未着手）。
  その前の領域（JSON の型不正とアクションの実行・phase 23〜31）は [decisions_archive/31](../../.claude_data/state/decisions_archive/31_unknown_action_type_handling.md) から辿る。

## 次採番の完了の行（phase 31〜81）

- **phase 31 は 2026-09-24 完了**（`31_unknown_action_type_handling` / 暫定 24〔v0.5・凍結〕/ decisions 31〔アーカイブ済〕）。
  **phase 32 は 2026-09-24 完了**（`32_hook_resume_wait_in_ui_tests` / 暫定なし〔直接改訂モード〕/ decisions 32〔アーカイブ済〕）。
  **phase 33 は 2026-09-24 完了**（`33_grab_modal_static_check_discovery` / 暫定なし〔直接改訂モード〕/ decisions 33〔アーカイブ済〕）。
  **phase 34 は 2026-09-27 完了**（`34_trigger_list_per_keymap` / 暫定 25〔v0.7・凍結〕/ decisions 34〔アーカイブ済〕）。
  **phase 35 は 2026-09-26 完了**（`35_legacy_trigger_set_missing_file` / 暫定なし〔直接改訂モード〕/ decisions 35〔アーカイブ済〕）。
  **phase 36 は 2026-09-27 完了**（`36_config_service_split` / 暫定なし〔直接改訂モード〕/ decisions 36〔アーカイブ済〕）。
  **phase 37 は 2026-09-27 完了**（`37_sequence_control_actions` / 暫定 26〔v0.6・凍結〕/ decisions 37〔アーカイブ済〕）。
  **phase 38 は 2026-09-27 完了**（`38_file_line_async_read` / 暫定 27〔v0.8・凍結〕/ decisions 38〔アーカイブ済〕）。
  **phase 39 は 2026-09-28 完了**（`39_sequence_stop` / 暫定 28〔v0.6・凍結〕/ decisions 39〔アーカイブ済〕）。
  **phase 40 は 2026-10-01 完了**（`40_sequence_call` / 暫定 29〔v0.9・凍結〕/ decisions 40〔アーカイブ済〕）。
  **phase 41 は 2026-10-02 完了**（`41_ime_off_while_typing` / 暫定なし〔直接改訂モード〕/ decisions 41〔アーカイブ済〕）。
  **phase 42 は 2026-10-02 完了**（`42_listbox_click_selection_sync` / 暫定なし〔直接改訂モード〕/ decisions 42〔アーカイブ済〕）。
  **phase 43 は 2026-10-04 完了**（`43_list_reorder_range_copy` / 暫定 30〔v0.11・凍結〕/ decisions 43〔アーカイブ済〕）。
  **phase 44 は 2026-10-04 完了**（`44_child_save_dialog_layout` / 暫定なし〔直接改訂モード〕/ decisions 44〔アーカイブ済〕）。
  **phase 45 は 2026-10-05 完了**（`45_call_step_and_view` / 暫定 31〔v0.6・凍結〕/ decisions 45〔アーカイブ済〕）。
  **phase 46 は 2026-10-06 完了**（`46_back_rewind_target` / 暫定 32〔v0.3・凍結〕/ decisions 46〔アーカイブ済〕）。
  **phase 47 は 2026-10-06 完了**（`47_action_dialog_layout_cleanup` / 暫定なし〔直接改訂モード〕/ decisions 47〔アーカイブ済〕）。
  **phase 48 は 2026-10-07 完了**（`48_compact_sequence_view` / 暫定 33〔v0.6・凍結〕/ decisions 48〔アーカイブ済〕）。
  **phase 49 は 2026-10-07 完了**（`49_status_truncation_tooltip` / 暫定なし〔直接改訂モード〕/ decisions 49〔アーカイブ済〕）。
  **phase 50 は 2026-10-09 完了**（`50_select_before_run` / 暫定 34〔v0.6・凍結〕/ decisions 50〔アーカイブ済〕）。
  **phase 51 は 2026-10-11 完了**（`51_key_press_release_actions` / 暫定 35〔v0.9・凍結〕/ decisions 51〔アーカイブ済〕）。
  **phase 52 は 2026-10-11 完了**（`52_key_hold_auto_repeat` / 暫定 36〔v0.4・凍結〕/ decisions 52〔アーカイブ済〕）。
  **phase 53 は 2026-10-11 完了**（`53_repeat_stop_on_own_foreground` / 暫定 37〔v0.4・凍結〕/ decisions 53〔アーカイブ済〕）。
  **phase 54 は 2026-10-11 完了**（`54_numpad_key_distinction` / 暫定 38〔v0.5・凍結〕/ decisions 54〔アーカイブ済〕）。
  **phase 55 は 2026-10-12 完了**（`55_keyboard_ui_window` / 暫定 39〔v0.6・凍結〕/ decisions 55〔アーカイブ済〕）。
  **phase 56 は 2026-10-13 完了**（`56_screen_grid_cursor` / 暫定 40〔v0.7・凍結〕/ decisions 56〔アーカイブ済〕）。
  **phase 57 は 2026-10-14 完了**（`57_grid_crosshair_nudge` / 暫定 41〔v0.4・凍結〕/ decisions 57〔アーカイブ済〕）。
  **phase 58 は 2026-10-15 完了**（`58_window_size_fit` / 暫定 42〔v0.3・凍結〕/ decisions 58〔アーカイブ済〕）。
  **phase 59 は 2026-10-16 完了**（`59_keyboard_ui_left_right_modifiers` / 暫定 43〔v0.6・凍結〕/ decisions 59〔アーカイブ済〕）。
  **phase 60 は 2026-10-16 完了**（`60_ime_off_during_key_capture` / 暫定 44〔v0.4・凍結〕/ decisions 60〔アーカイブ済〕）。
  **phase 61 は 2026-10-17 完了**（`61_keyboard_ui_vk_to_scan_code` / 暫定なし〔直接改訂モード〕/ decisions 61〔アーカイブ済〕）。
  **phase 62 は 2026-10-18 完了**（`62_special_keys_from_layout_only` / 暫定 45〔v0.5・凍結〕/ decisions 62〔アーカイブ済〕）。
  **phase 63 は 2026-10-20 完了**（`63_make_only_keys` / 暫定 46〔v0.5・凍結〕/ decisions 63〔アーカイブ済〕）。
  **phase 64 は 2026-10-21 完了**（`64_external_layout_path_base` / 暫定なし〔直接改訂モード〕/ decisions 64〔アーカイブ済〕）。
  **phase 65 は 2026-10-21 完了**（`65_layout_snapshot_for_hook` / 暫定 48〔v0.3・凍結〕/ decisions 65〔アーカイブ済〕）。
  **phase 66 は 2026-10-21 完了**（`66_capture_jis_special_keys` / 暫定 49〔v0.5・凍結〕/ decisions 66〔アーカイブ済〕）。
  **phase 67 は 2026-10-21 完了**（`67_mouse_scroll_action` / 暫定 50〔v0.4・凍結〕/ decisions 67〔アーカイブ済〕）。
  **phase 68 は 2026-10-24 完了**（`68_ui_terminology` / 暫定 51〔v0.8・凍結〕/ decisions 68〔アーカイブ済〕）。
  **phase 69 は 2026-10-26 完了**（`69_keyboard_ui_key_labels` / 暫定 52〔v0.4・凍結〕/ decisions 69〔アーカイブ済〕）。
  **phase 70 は 2026-10-29 完了**（`70_help_window` / 暫定 53〔v0.7・凍結〕/ decisions 70〔アーカイブ済〕）。
  **phase 71 は 2026-11-01 完了**（`71_taskbar_status_icon` / 暫定 54〔v0.4・凍結〕/ decisions 71〔アーカイブ済〕）。
  **phase 72 は 2026-11-04 完了**（`72_multilingual_ui` / 暫定 55〔v0.7・凍結〕/ decisions 72〔アーカイブ済〕）。
  **phase 75 は 2026-11-22 完了**（`75_mac_support` / 暫定 57〔v0.25・凍結〕/ decisions 75〔アーカイブ済〕）。
  **phase 76 は 2026-11-23 完了**（`76_counter_expansion` / 暫定 58〔v1.1・凍結〕/ decisions 76〔アーカイブ済〕）。**phase 77 は 2026-11-23 完了**（`77_sample_in_user_folder` / 暫定 59〔v0.2・凍結〕/ decisions 77〔アーカイブ済〕）。**phase 78 は 2026-11-23 完了**（`78_action_hotkey_save_validation` / 暫定なし〔直接改訂モード〕/ decisions 78〔アーカイブ済〕）。**phase 79 は 2026-11-24 完了**（`79_bundled_c_library_licenses` / 暫定 60〔v0.9・凍結〕/ decisions 79〔アーカイブ済〕）。**phase 80 は 2026-11-25 完了**（`80_win_d_restore_blank_dialog` / 暫定なし〔直接改訂モード〕/ decisions 80〔アーカイブ済〕）。**phase 81 は 2026-11-25 完了**（`81_uppercase_replacement_target` / 暫定 61〔v0.3・凍結〕/ decisions 81〔アーカイブ済〕）。**phase 82 は 2026-11-26 完了**（`82_scroll_direction_setting` / 暫定 62〔v0.4・凍結〕/ decisions 82〔アーカイブ済〕）。次の phase は `83_<topic>`。
  （phase 30 は 2026-09-23 完了 = `30_action_and_internal_key_type_coercion` / 暫定なし〔直接改訂モード〕/ decisions 30〔アーカイブ済〕）
  保存系リデザインの予定: **β=phase 06〔完了〕/ γ=phase 07〔完了〕/ プリセット=phase 08〔完了〕**。
  → **保存系リデザインは一巡完了**。その派生 = **phase 09〔完了〕**（idea_08）。
