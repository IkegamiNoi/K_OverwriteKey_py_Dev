# instructions/backlog/

実装予定（または検討中）の改善ネタを蓄積する場所。

このフォルダのファイルは **正式なフェーズ／タスクではない**。
着手時は `instructions/phase/<phase>/tasks/` へ正式タスクとして起票し直すこと。
起票手順は `/idea`（`.claude/commands/idea.md`）。

---

## 運用ルール

- 1 ネタ 1 ファイル
- ファイル名: `idea_<連番>_<topic_snake_case>.md`
- 各ファイルは「概要 / 起票経緯 / 現状 / 提案 / 想定スコープ」を含む
- 着手時は状態列を「**着手**（→ 暫定仕様 / phase へのリンク）」へ更新し、行は本 INDEX に残す
- 完了・クローズ（対応不要 / 除外）が確定したものは、判定理由と対応フェーズへのリンクを
  状態列に残した上で、行を [INDEX_done.md](INDEX_done.md) へ移動する
  （フェーズ完了時の更新は `.claude/rules/task_execution.md`「フェーズ完了時」に従う）
- 「保留」は判定理由を状態列に残して本 INDEX に残す
- 仕様変更を伴うネタは `.claude/rules/spec_change_workflow.md` に従う
- 採番はフォルダ実体（`idea_*.md` の最大番号 + 1）が正。本表を基準にしない

---

## ネタ一覧

| ID | ファイル | 概要 | 状態 |
|---|---|---|---|
| idea_03 | [idea_03_action_hotkey_save_normalization.md](idea_03_action_hotkey_save_normalization.md) | アクション hotkey の保存経路がプリセットと非対称で生値のまま保存される点を統一。実行時は正規化されるため実害はないが JSON に生値が残る。保存/読込どちらで正規化するか等は要設計。 | 未着手（検討段階・phase 02 task_04 の実機目視から分離）|
| idea_04 | [idea_04_font_settings_controller.md](idea_04_font_settings_controller.md) | フォント設定（状態/正規化/適用/UI反映/永続化）が App に散在する点を `FontSettingsController` へ集約。phase 03 で案 B として比較検討し、初期化順序が未解決のため見送られたもの。 | **保留（着手条件付き）**: 対象が実質 int 1 個で controller 新設が過剰なため。フォント設定項目の追加・設定ダイアログ化等の**着手トリガー**（ファイル内に 5 件明記）が発生するまで着手しない。着手時は初期化順序設計の暫定仕様が先に必要（1 フェーズ規模）。phase 03 §6 案 B から分離 |
| idea_06 | [idea_06_individual_json_io_unification.md](idea_06_individual_json_io_unification.md) | 個別 JSON（keymap / trigger_set / sequence）の save/save_as/to_path/load 4点セットが同じ骨格で3回反復している点を共通テンプレートへ集約。 | **保留（前提条件付き）**: 骨格は同型だが細部が9点食い違い、うち2点は既存の不整合。①phase 04 完了（**充足・2026-07-26**）②[idea_05](idea_05_trigger_set_source_path_inconsistency.md) の解消（**充足・2026-08-02 / Phase β**）③共通化の実需（4種目の追加等）の**3条件すべて**を満たすまで着手しない。**残るは③のみ**（Phase β で個別保存 3 経路のパス解決・上位 dirty 化を揃えたため、共通化の対象は着手当時より整理されている）。暫定仕様 03 §5 案2 から分離 |
| idea_09 | [idea_09_legacy_settings_save_path_fallback.md](idea_09_legacy_settings_save_path_fallback.md) | 別名保存でレガシー `settings/` 配下を選ぶと選択パスが捨てられ無言で `default.json` へ保存される残存経路（`config_paths.normalize_keymap_set_save_path:72-73`）。Phase α の「`default.json` フォールバック廃止」の取りこぼし。 | 未着手（検討段階・優先度低・phase 05 task_05 の deep-reviewer 指摘2 から分離。**正本 `data_schema.md` §5.4 に「実装未追従」として明記済 → 実装修正が既定**。判断が要るのは案 A〜C の選択のみ）|
| idea_11 | [idea_11_save_as_preset_copy_rollback.md](idea_11_save_as_preset_copy_rollback.md) | 別名保存で個別プリセットの複製に成功した後、keymap_set 本体の保存が失敗しても巻き戻らない。孤児の複製とメモリ上だけ新パスを指す `hotkey_presets_path` が残り dirty も立たない。補償削除・参照復元、または最低限 dirty を立てる。 | 未着手（検討段階・**優先度低**・phase 09 task_08 の敵対的レビュー High 3 から分離。**現状は正本 `data_schema.md` §5.10.4 に既知の制約として明記済**。例外系が前提でデータは失われないため後送りとユーザー判断）|
| idea_29 | [idea_29_action_dialog_listener_after_destroy.md](idea_29_action_dialog_listener_after_destroy.md) | `ActionDialog` の座標取得リスナー（`pynput` のデーモンスレッド）が、ダイアログ破棄後に `after(0, ...)` を呼ぶと `TclError` になり得る（`action_dialog.py:247-251`）。 | 未着手（検討段階・**優先度低**・phase 22 task_02 の `reviewer` 参考指摘から分離〔task_02 以前からの既存挙動〕。2026-09-22 に current.md「別タスク化候補」から昇格。**未再現・理屈上の経路**）|
| idea_30 | [idea_30_keymap_set_slug_collision.md](idea_30_keymap_set_slug_collision.md) | `slugify_file_stem` で別々の keymap_set 名が同一 stem へ丸まり、子ファイルの既定保存先が重なり得る。同一保存計画内の連番回避は効くが、別の keymap_set 由来の衝突は互いを知らない。 | 未着手（検討段階・**優先度低**・Phase β の `/refactor_check` 候補送りから分離〔受入条件 8 の範囲外〕。2026-09-22 に current.md「別タスク化候補」から昇格。**着手時はまず共有判定・確認ダイアログでどこまで防げているかの実測が先**〔防げていればクローズ〕）|
| idea_31 | [idea_31_input_gateway_dead_register_key_hook.md](idea_31_input_gateway_dead_register_key_hook.md) | `InputGateway.register_key_hook`（`input_gateway.py:58-75`）に呼び出し元が無い。フック登録の実経路は `register_global_hook` のみで、押下だけ上位へ渡す包み（18 行）が残っている。 | 未着手（検討段階・**優先度低**・phase 21 完了判定前の `deep-reviewer` 指摘 8 から分離〔当時は「phase 21 の差分外」として据え置き・ユーザー判断 2026-09-19〕。2026-09-22 に current.md「別タスク化候補」から昇格。**挙動不変**・削除前に `_wrapped` の挙動が他所で再実装されていないかの確認が要る）|
| idea_36 | [idea_36_common_trigger_layer.md](idea_36_common_trigger_layer.md) | トリガー一覧のキーマップ従属化（phase 34 予定）の後、全キーマップで有効な共通トリガー層を追加する（共通 + キーマップ別の 2 層）。 | 未着手（検討段階・2026-09-24 設計議論から分離・現時点では不要とユーザー判断）|
| idea_37 | [idea_37_counter_conditional_branch.md](idea_37_counter_conditional_branch.md) | 出力シーケンスの system 種別にカウンター値による条件分岐（N 以上でループを抜ける / 停止 等）を加える。file_line の終端で止める用途。 | 未着手（検討段階・2026-09-26 暫定 26 の設計対話から分離・第 2 弾の完了後に要否判断）|
| idea_39 | [idea_39_back_rewind_visible_trigger.md](idea_39_back_rewind_visible_trigger.md) | 対象を指定しない戻す・先頭への対象を「直前のトリガー」から「押した時点で一覧に表示されているトリガー」へ変える。 | 一部取り込み（phase 50 暫定 34 v0.6 §3a）・残り = 直前のトリガーの廃止ほか（2026-10-09 追記）|
| idea_44 | [idea_44_screen_grid_colors.md](idea_44_screen_grid_colors.md) | 画面の枠（phase 56）の線・文字・選択の強調・左上の文字の下地の色の組み合わせを、明るい / 暗い画面の上で見分けやすく見直す。 | 未着手（検討段階・2026-10-13 phase 56 task_06b の実機目視）|
| idea_45 | [idea_45_tk_key_capture_symbol_names.md](idea_45_tk_key_capture_symbol_names.md) | 既存のキー取得で記号キーが `period` 等の Tk の名前になり、フックの名前（`.` 等）と一致しない可能性を調べて直す（phase 56 では編集の窓だけ対応）。 | 未着手（検討段階・2026-10-13 phase 56 task_06 の実機目視から分離）|
| idea_48 | [idea_48_hook_resume_during_key_capture.md](idea_48_hook_resume_during_key_capture.md) | キーの取得中（停止 / トグルキーの取得・キーボードUI の編集）にフック開始ボタンでフックを再開できてしまい、取得の打鍵がフックに流れ得るのを防ぐ。 | 未着手（検討段階・2026-10-16 暫定 44 の Codex 敵対的レビューから分離）|
| idea_50 | [idea_50_capture_jis_special_keys.md](idea_50_capture_jis_special_keys.md) | キーの取得（キーボードUI の編集・切替キー 等）で JIS の特殊キー（無変換・変換・半角/全角・かな）を取れるようにする（今は IME に横取りされ `??` で届き判別できない・Tk のイベントは物理の走査コードを持たない）。 | 未着手（検討段階・2026-10-17 phase 61 の実機目視から分離・実測あり）|
| idea_51 | [idea_51_layout_snapshot_for_hook.md](idea_51_layout_snapshot_for_hook.md) | フックの実行時に外部レイアウトの JSON を打鍵ごとに読み直すのをやめ、受け取りと送信が同じレイアウトの写し（UI スレッドでだけ更新）を使うようにする。 | 未着手（検討段階・2026-10-18 暫定 45 の Codex 敵対的レビューから分離）|
| idea_53 | [idea_53_send_without_dropping_physical_input.md](idea_53_send_without_dropping_physical_input.md) | アプリの送信の最中に届いた物理の入力が、フックに届かず OS へ素通りする（keyboard の `is_replaying`・送信ガードの素通し）のを直し、自分の送信だけを見分けて除く。直れば押下だけのキーのリピートを戻せる。 | 未着手（検討段階・2026-10-20 phase 63 task_03 の実機目視の NG の計測から分離）|
| idea_54 | [idea_54_ime_switch_on_make_only_keys.md](idea_54_ime_switch_on_make_only_keys.md) | 押下だけのキー（無変換・変換）を直接置換で使っている最中に IME が切り替わった件（計測では 241 / 242 は全て抑止・原因未特定）を、再発時に切り分けて直す。 | 未着手（検討段階・2026-10-20 phase 63 task_03d・03e の実機目視から分離・task_03f の後は再発せず）|
