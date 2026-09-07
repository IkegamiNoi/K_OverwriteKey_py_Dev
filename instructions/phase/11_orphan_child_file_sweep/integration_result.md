# phase 11 統合確認の結果（task_07）

> 対象 = task_01〜06b の全差分（基点 `e01712d` 〜 `223301e`）。コードは変更していない。

## 1. 実測（`verifier`・`.venv` python）

| 項目 | 結果 |
|---|---|
| `compileall -q keyseq main.py tests tests_ui` | clean |
| `unittest discover -s tests` | **399** pass（skip 5） |
| `unittest discover -s tests_ui` | **287** pass（skip 0） |
| `tests.smoke_app` | pass（`SMOKE OK`） |
| worktree ルートへの `user/` `quarantine/` 生成 | **なし**（実行前後とも） |

**skip 5 件はすべて Windows の symlink 作成権限不足（`WinError 1314`）**。
`test_symlink_replacement_is_rejected_after_rescan` /
`test_collect_paths_counts_symlink_once_without_following_it` /
`test_delete_child_symlink_does_not_delete_external_files` /
`test_delete_root_link_is_rejected_even_with_override` / `test_real_symlink_unit_is_not_followed`。
**同じ観点はジャンクション版のテストが実行されている**ため観点の抜けではない。これ以外の skip はない。

**phase 11 で追加されたテストの内訳**（`tests` 132 件 / `tests_ui` 58 件）:

| モジュール | 件数 |
|---|---|
| `tests/test_quarantine_manage.py` | 35 |
| `tests/test_orphan_scan.py` | 31 |
| `tests/test_quarantine.py` | 24 |
| `tests/test_orphan_sweep_text.py` | 20 |
| `tests/test_reference_scan.py` | 12 |
| `tests/test_quarantine_manage_text.py` | 10 |
| `tests_ui/test_orphan_sweep_flow.py` | 30 |
| `tests_ui/test_quarantine_manage_flow.py` | 19 |
| `tests_ui/test_reference_cleanup_flow.py` | 9（既存。引数化で壊れていない） |

---

## 2. 受け入れ条件 1〜22 の突合（暫定仕様 10 §5）

**22 条件すべてに自動テストの担保がある**。未担保は条件 16 の**件数の値のみ**（下記）。

| # | 条件（要約） | 担保 |
|---|---|---|
| 1 | 参照集合の構築・2 段辿り・旧形式 `keymaps[]` | `test_reference_scan`: `test_collects_all_first_level_keymap_set_paths` / `test_collects_legacy_string_keymap_entries` / `test_collects_sequence_paths_from_trigger_set`、`test_orphan_scan.test_multiple_sets_reference_children_and_second_level_sequences` |
| 2 | `hotkey_presets_individual` が false でも参照扱い | `test_reference_scan.test_collects_hotkey_presets_when_individual_is_false`、`test_orphan_scan.test_individual_presets_are_referenced_even_when_disabled` |
| 3 | 現在開いているセットが config 外でも走査される | `test_orphan_scan.test_current_set_outside_config_is_scanned_without_startup_config` |
| 4 | 候補側は 4 種の直下のみ・`global/` 除外 | `test_orphan_scan.test_candidates_are_only_direct_json_files_in_four_directories` |
| 5 | 現在のセットが参照する子は config 外でも孤児にならない | `test_orphan_scan.test_protection_accepts_missing_and_external_paths_without_references` / `test_external_scan_directory_still_references_config_child` |
| 6 | 未保存時は「保存する / 中止する」の 2 択 | `tests_ui/test_orphan_sweep_flow`: `test_unsaved_no_stops_before_save_collection_and_scan` / `test_unsaved_yes_saves_existing_set_before_collection_and_scan` / `test_save_failure_or_save_as_cancel_stops_collection_and_scan` |
| 7 | 見つからない指定ディレクトリはスキップ + パス付き表示 | `test_orphan_scan.test_missing_scan_dirs_keep_input_spelling_and_other_scans_continue`、`test_orphan_sweep_text.test_missing_directories_are_counted_and_listed_without_warning`、`tests_ui.test_missing_scan_dirs_are_retained_and_reported_without_writes` |
| 8 | 読めなかった参照側・対象外 JSON の件数が出る | `test_orphan_sweep_text`: `test_unreadable_warning_is_first_in_warnings_and_plan` / `test_excluded_entries_show_only_count` |
| 9 | 相対構造を保って移動 + `manifest.json` | `test_quarantine`: `test_move_keeps_relative_structure_and_leaves_no_original` / `test_manifest_is_written_in_unit_dir_with_stored_paths`（+ 目視 **M1**） |
| 10 | 再判定で新たに孤児になった候補は隔離しない | `test_quarantine.test_candidate_that_became_orphan_after_presentation_is_not_moved` / `test_candidate_referenced_after_presentation_is_dropped` |
| 11 | 復元・同名スキップ・`original_path` ガード | `test_quarantine_manage`: `test_restore_all_four_directories_creates_parents_and_cleans_unit` / `test_existing_destination_is_not_overwritten_and_manifest_is_unchanged` / `test_outside_reserved_and_candidate_directory_itself_are_rejected`（+ 目視 **M4**） |
| 12 | 削除は隔離ルート配下でなければ拒否 | `test_quarantine_manage`: `test_delete_root_link_is_rejected_even_with_override` / `test_delete_root_junction_is_rejected_even_with_override` / `test_delete_external_junction_is_rejected_even_with_override` |
| 13 | 候補 0 件ならダイアログを出さず通知のみ | `tests_ui.test_zero_candidates_only_notifies_without_opening_dialog`、`test_orphan_sweep_text.test_empty_notice_includes_all_scan_diagnostics`（+ 目視 **M8**） |
| 14 | 設定が起動設定経路で保存され、別操作後も残る | `tests_ui/test_orphan_sweep_flow`: `test_scan_dirs_and_existing_settings_survive_real_keymap_set_save` / `test_settings_save_only_uses_startup_io`（+ 目視 **M3**） |
| 15 | 検出そのものによる書き込みが 0 件 | `test_reference_scan.test_scan_is_read_only_and_creates_no_files_or_directories`、`test_orphan_scan.test_scan_never_writes_or_creates_missing_directories`、`tests_ui.test_real_sweep_does_not_write_files_or_change_runtime` |
| 16 | 件数を減らさず pass / smoke pass / `user/` を作らない | **条件の数値が古い**（`tests` 267 / `tests_ui` 238）。**実測 399 / 287 へ読み替える**。隔離未実行環境に隔離ルートを作らないことは `test_quarantine.test_scan_alone_does_not_create_quarantine_root`。**数値の改訂は task_08** |
| 17 | 警告が一覧先頭・「実行 / キャンセル」の 2 択 | `test_orphan_sweep_text.test_unreadable_warning_is_first_in_warnings_and_plan`、`tests_ui`: `test_candidates_are_presented_with_warning_first_in_confirmation_dialog` / `test_unreadable_sources_do_not_block_quarantine`（+ 目視 **M7**） |
| 18 | 形状検証で必須キーを欠く JSON を除外 | `test_orphan_scan.test_all_kinds_exclude_missing_keys_wrong_types_lists_and_broken_json` |
| 19 | 復元 / 削除が実行単位ごと | `test_quarantine_manage.test_delete_other_unit_keeps_listing_and_restore_working`、`tests_ui/test_quarantine_manage_flow` のリスト選択系 |
| 20 | マニフェスト先行・書けなければ 1 件も動かない | `test_quarantine`: `test_manifest_is_written_before_any_move_with_planned_states` / `test_unwritable_manifest_moves_nothing_and_leaves_no_directory`（+ 目視 **M2**） |
| 21 | 削除 API が不正値を拒否・ゴミ箱へ送らない | `test_quarantine_manage`: `test_delete_invalid_ids_preserve_root_and_other_units_even_with_override` / `test_delete_invalid_manifests_require_explicit_override` ほか。**条件の文言が v0.5 と不整合**（下記 F-1） |
| 22 | 外部レイアウトが両基準で保護される | `test_reference_scan.test_collects_external_layout_paths_from_both_bases`、`test_orphan_scan.test_external_layout_references_resolve_against_both_bases` |

### 本タスクで見つかった仕様側の齟齬

- **F-1: 受け入れ条件 21 の文言が v0.5 の改訂に追随していない。**
  条件 21 は「**マニフェストの無い単位**を渡すと拒否される」と書いているが、**v0.5 以降は
  `allow_invalid_manifest=True` を明示すれば削除できる**（§3-8）。**既定では拒否**なので実装は正しく、
  **条件文の方が古い**。→ **task_08 で「既定では拒否される」と限定する**。
- **F-2: 受け入れ条件 16 の件数が古い**（267 / 238 → 実測 399 / 287）。→ **task_08 で改訂**。

---

## 3. 二次レビュー

接合部（manifest のキー / `manifest_valid` → `allow_invalid_manifest` / 判定名での分岐）に
ずれは見つからなかった。以下は**メインセッションで `ファイルパス:行` を裏取り済み**のもの。

### 3-1. `deep-reviewer`（Claude・複数タスクを跨ぐ差分）= **修正要**（18 件）

### 3-2. `codex-reviewer`（Codex・標準レビュー）= 3 件

### 3-3. 統合した採否一覧

**R = deep-reviewer / C = codex-reviewer**。採否はユーザー判断。

#### A. 修正候補 → **全 7 件を修正して採用**（ユーザー確定 2026-09-07・**task_07b `b8c9cc4` で反映済み**）

| # | 出所 | 内容 | 裏取り | 推奨 |
|---|---|---|---|---|
| A-1 | R1（高） | **参照側の symlink が無警告で参照集合から落ちる**。`orphan_scan.py:150` の skip は候補側では安全側だが、**参照側では「その親が参照していた子」が警告なしに孤児候補になる**。`unreadable_sources` にも `non_keymap_set_sources` にも記録されない。**§3-5「握りつぶさない」と §4-A の受容前提（警告は必ず出る）が同時に崩れる** | `orphan_scan.py:138`（参照側）と `:171`（候補側）が同じ `_list_json_files` を呼ぶことを確認 | **修正して採用** |
| A-2 | C P1 | **隔離ルートがリダイレクトされていると、隔離は成功と報告されるのに管理から見えない**。書き込み側 `quarantine.py:222` の `os.makedirs` はジャンクションを辿るが、読み出し側 `quarantine_manage.py:122` は `_is_redirected(root)` で空を返す。**復元も削除もできない隔離物**ができる = §4-A が避けたかった状況 | 両行を確認 | **修正して採用**（隔離側でも拒否して対称化） |
| A-3 | C P2 | **`os.listdir` の `PermissionError` が素通りする**。`orphan_scan.py:146` に例外処理がなく、Tk コールバックのトレースバックになり結果が出ない。走査ディレクトリは config 外を指してよい仕様（§3-2）なので現実的 | 同行に try/except が無いことを確認 | **修正して採用** |
| A-4 | R5（中） | **既定ディレクトリ `user/keymap_sets/` の不在が「見つからなかった指定ディレクトリ」として警告に出る**。§3-5-1 はユーザー指定ディレクトリの規定で既定ディレクトリは対象外。表記も `\` 区切りの絶対パスで §5.7 から外れる | `orphan_scan.py:118` が既定ディレクトリを `_scan_source_directory` へ通し `:136` で `missing_dirs` へ積むことを確認 | **修正して採用**（1 行） |
| A-5 | R10（低） | **管理ダイアログのヘッダが「復元する実行単位を選択してください。」のまま**。task_06b で削除ボタンが増えたのに追随していない | `quarantine_manage_dialog.py:30` を確認 | **修正して採用**（1 行） |
| A-6 | R7（低） | **`manifest.json.tmp` の残骸で実行単位が永久に片付かない**。移動中のマニフェスト更新失敗で `.tmp` が残ると `_empty_directories` が常に `None` を返し、§3-7 の MUST「全件復元した単位は削除する」が満たされない | 未確認（`quarantine.py:274` / `quarantine_manage.py:176-192`。task_07b で確認する） | **修正して採用** |
| A-7 | R13（低） | **`_is_real_path_within` が 2 箇所に同一実装**。片方だけ直すと境界判定が割れる | `orphan_scan.py:206` と `quarantine.py:284` を確認 | **修正して採用**（片方へ寄せる） |

**task_07b の実測**: compileall clean / tests **413**（399 → +14・skip 7）/
tests_ui **288**（287 → +1）/ smoke pass。skip の +2 は新規テストの symlink 権限不足（WinError 1314）。
**`reviewer` = 採用（指摘なし）**。

**Codex の実装に入った劣化 2 件をメインが検出し是正させた**（詳細はコミットメッセージ）:
①**A-1 の skip 条件を広げすぎ**（親ディレクトリがジャンクションなら配下の全 keymap_set が
参照集合から落ちる。**追加テストがその挙動を固定していた**）→ skip 集合を元に戻し**回帰テストを追加**。
②**A-7 の循環 import 回避で定数をリテラルへ、呼び出しをファサード経由へ置換**
→ **`path_boundary.py` を新設**して解消。

#### B. 仕様判断が要る（**task_08**。§5 へ転記済み）

| # | 出所 | 内容 |
|---|---|---|
| B-1 | R3（中） | **§3-8「部分失敗を許容し件数 + 理由を出す」が削除では未実装**。`quarantine_manage.py:282-289` は単一 `try` で最初の失敗で中止し `DELETE_FAILED` 1 件を返すだけ。**隔離と復元は条項どおり 1 件ずつ継続しており、削除だけが非対称**。実装を条項に合わせるか、条項を「中止 + 一部削除の可能性を通知」へ改めるか（**条項変更はユーザー承認必須**） |
| B-2 | R2（中） | **§3-11「presentation から内部モジュールを直参照しない」に違反**。`orphan_sweep_io.py:3` / `orphan_sweep_text.py:1-17` / `quarantine_manage_text.py:3-17`。既存 `reference_cleanup_text.py` と同形。実装を直すか、条項を撤回するか |
| B-3 | R4・R8・R9 | **§3-12 への追記候補**: ①一覧に出ない残骸（名前不一致 / リダイレクト / ルート直下のファイル）はアプリから復元も削除もできない ②削除経路だけ `_is_redirected(unit_dir)` を課していない（ルート内に限定） ③空になった隔離ルートの後始末が削除と復元で非対称 |
| B-4 | R6・R16 | `codebase_map.md` が部分反映のみ（`OrphanSweepDialog` 1 行 + 注記だけ）/ `phase.md:22,65` の主入力表記が **v0.4** のまま |

#### C. 保留・除外（対応しない）

| # | 出所 | 内容 | 理由 |
|---|---|---|---|
| C-1 | C P2 | 走査・隔離が UI スレッドをブロックする | 事実だが**phase 11 固有ではない**（保存系など既存フローも同期 I/O）。直すとフェーズの範囲を大きく超える |
| C-2 | R11 | `_is_keymap_set` の判定キーに `external_keyboard_layouts` が無い | 判定基準は §3-2 が「4 キー」と明記。変えるなら仕様判断。到達には手編集が要る |
| C-3 | R12 | 警告一覧のパスが絶対パス + `\` 区切り | 直しに行く用途では絶対パスの方が親切という反論があり得る |
| C-4 | R14・R15・R17・R18 | 全件拒否時に空の実行単位が残る / `_save_before_sweep` の分岐重複 / Python の最低バージョン床が未宣言 / `OrphanSweepDialog.destroy` の二重呼び出し | いずれも動作影響がないか、現行フローで到達しない |

---

## 4. 実機目視

観点リスト = [manual_check.md](manual_check.md)（**M1〜M8 + M2b**）。**ユーザーが 2026-09-08 に実施**。

- **M1〜M5・M2b・M7・M8 = 期待どおり**（M2b = task_07b のジャンクション中止の修正確認を含む）。
- **M6 = 期待どおり**（`manifest.json` を `{}` のみ / `{` のみに壊したケース）。
  あわせて `{"created_at": …, "entries": [{}]}`（**well-formed でエントリだけ空**）でも試され、
  「マニフェスト不正」表示と削除の追加 2 行が出ないことが分かった。
  application + text 層を `.venv` で実測した結果は次のとおり（**実装は §3-7 の条文どおり**）:

  | マニフェスト | 一覧 | 復元 | 削除確認 |
  |---|---|---|---|
  | `{"entries": [{}]}` | `残り 0/1 件`（不正表示なし） | 中止せず「復元 0 件 / スキップ 1 件」 | 追加 2 行なし |
  | `{}` のみ | `マニフェスト不正（復元できません）` | 「復元を中止しました: マニフェストが読めません」 | 追加 2 行あり |

  判定は `quarantine_manage.py:81` の 1 箇所だけで、**dict であり `entries` が list か**しか見ない。
  **エントリ単位の妥当性は §3-7 に未定義だった**ため仕様変更フラグ（B. 仕様書の不備）を上げ、
  **ユーザー確定 = A 案（現状維持・実装変更なし。定義を明記して手順へ注記）**。
  暫定仕様を **v0.7** へ改訂（§3-7 に「読めない」の定義 / §3-12-8 に残存リスク）、
  `manual_check.md` M6 の手順へ注記を追加した。**残骸は残らない**（削除確認は実体を全件列挙する）ため
  §4-A は満たしており、この形はアプリの原子書込みでは発生せず**手編集でのみ到達する**。

---

## 5. task_08（正本反映）への申し送り

フェーズ中に積み上がった「仕様書側の判断が要る」項目。**11〜14 は task_07b で増えた分**。

1. **§3-6 に「移動中の進捗書込み失敗時の扱い」が無い**（実装は `state` を信用せず実体で判定して吸収済み）。
2. **§3-6 に「実行単位ディレクトリ作成失敗」の規定が無い**（実装は中止扱い・task_05b）。
3. **§3-11 と実装が矛盾**（§3-11 は「presentation は `ConfigService` の委譲メソッド経由」だが、
   実装は判定名・理由コードの定数を兄弟モジュールから直 import している。既存パターンとして許容中）。
4. **マニフェストの `state` キーが §3-6 の例に無い**（実装は `planned` / `moved` / `failed` を書く）。
5. **§3-8 の v0.5 改訂**（検証④のみ `allow_invalid_manifest` で上書き可）を正本へ反映する。
6. **§3-12-6 / §3-12-7（v0.6 の残存リスク 2 件）**を正本へ反映する。
7. **F-1: 受け入れ条件 21 の文言を「既定では拒否」へ限定する**（本タスクで検出）。
8. **F-2: 受け入れ条件 16 の件数を 399 / 287 へ改訂する**（本タスクで検出）。
9. **`codebase_map.md` へ phase 11 の成果を反映する**
   （`reference_scan` / `orphan_scan` / `quarantine` / `quarantine_manage` の各モジュール、
   `QuarantineDeleteResult` / `collect_unit_paths` / `delete_quarantine_unit`、
   設定メニューの 2 項目と管理ダイアログの削除ボタン）。
10. `reference_cleanup_text.py` の警告文言の見直し（phase.md タスク 8）。
11. **新モジュール `keyseq/application/config_service/path_boundary.py`** を `codebase_map.md` へ記載する
    （境界判定 `is_real_path_within` の唯一の定義。task_07b で統合）。
12. **追加した理由コード 3 つ**を正本へ反映する:
    `SOURCE_REDIRECTED` / `SOURCE_DIRECTORY_UNREADABLE`（`reference_scan.py`）/
    `QUARANTINE_ROOT_REDIRECTED`（`quarantine.py`）。
13. **§3-5 に「読めなかった走査ディレクトリ」のカテゴリが無い**。task_07b は §3-5 の
    「握りつぶさない」原則に沿って `unreadable_sources` へ寄せたが、**条文の追記要否は要判断**。
14. **§3-5-1 の適用範囲**に「**既定ディレクトリは含めない**」ことを明示する（A-4 の根拠）。
15. **§3-7 の「マニフェストが読めない」の定義（v0.7）と §3-12-8** を正本へ反映する
    （実機目視 M6 で検出。**エントリ単位の妥当性は検査しない**旨まで含めて昇格する）。
