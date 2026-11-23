# task_06_integration

## 目的

phase 76（カウンター機能の拡張）の統合確認。標準検証 4 種を実測し、暫定 58 §7 の受け入れ条件 1〜8 と照合し、
phase 76 の全差分に二次レビュー（`deep-reviewer` + `codex-reviewer`）をかけて指摘を採否の判断ができる形に整理する。
**コードの変更は指摘の採否がユーザーで決まってから（本 task の後段）**。実機目視はユーザー。

## 対象範囲（検証・レビュー・整理のみ・コード不変）

### 標準検証（verifier・`.venv` の python）

- `python -m compileall -q keyseq tests tests_ui`
- `python -m unittest discover -s tests`（task_05 時点 2254 件・失敗 0 が基準）
- `python -m unittest discover -s tests_ui`（**全体を 1 本だけ**・他の verifier と同時に流さない・python.exe の一括 taskkill 禁止）
- `python -m tests.smoke_app`

### 受け入れ条件の照合（メイン）

暫定 58 §7 の 1〜8 ごとに「自動テストで担保 / 一部 / 実機目視に残る」に分類し、担保しているテストを `ファイル:テスト名` で示す。
§7.4（経路ごとに未使用の名前が開始値から動く）・§7.5（巻き戻し後の追従）は経路ごとに有無を確かめる。

### 二次レビュー

- 対象 = `git diff 4129c67b..HEAD`（phase 76 の全差分・task_01〜05）
- `deep-reviewer`: 5 観点 + phase.md「本フェーズ固有の観点」（実効値を通らない経路・保留の 2 要素の組の残り・依存方向 §4.1・既存データの互換 §7.1・ja / en の両方と ui_terms）
- `codex-reviewer`: 標準レビュー（`--base 4129c67b`）
- 指摘は事実主張を `ファイル:行` で裏取りしてから、表（# / 指摘 / 推奨）で本ファイル「結果」節へ記録する

### 実機目視の手順（ユーザーへ提示）

増やす量 / 開始値の欄・名前の変更で開始値が入れ替わる・一覧の `[count+3]` / `[count=10]` / `[counter_text] n (=5)`・
counter_text の入力・リセットで開始値へ戻る・保存 → 読込で開始値が保たれる・サンプル設定に戻すで開始値が消える・英語表示。

## 結果（2026-11-23・HEAD fa28a7a9）

- 実測: compileall clean / tests **2254 pass**（skip 7）/ tests_ui **1316 件・失敗 5・エラー 28** / smoke pass。
  tests_ui の内訳: `CallViewSummary` の `counter_starts` 欠落の TypeError 27（call_view_compact 10・call_view_frame 13・full_view_panes 3・full_view_scroll_areas 1 ほか）/
  key_hold_presentation 1（スタブに `counter_starts` 無し）/ config_io_characterization_keymap_set_startup 4（期待の辞書に `counter_starts: {}` が無い）/
  minimize_grab_custody 2（phase 76 は modal を触っていない・切り分け未了）。
- 受け入れ条件（暫定 58 §7・deep-reviewer の分類を採用）: 自動 = 1・2・3 / 一部 = 4・5（連続実行の巻き戻しは未テスト + R2）・6・7・8 / 実機目視に残る = 一覧・表示枠・ダイアログの見た目・ヘルプ。

## 指摘と推奨（ユーザー判断待ち）

| # | 指摘（裏取り） | 推奨 |
|---|---|---|
| R1 | tests_ui の 6 か所の `CallViewSummary(...)` とスタブ・特性テスト 4 件が `counter_starts` に追従していない（`call_view.py:22` 必須の項目・確認済） | **採用**（テスト側へ `counter_starts` を足す。コードに既定値は付けない＝作り手が渡し忘れない） |
| R2 | 連続実行で待機をまたぐと、待機前に初めて入った名前が巻き戻しで消えない（`run_to_end.py:205` が区間ごとに名前を取り直す・確認済） | **採用**（R3 と一緒に直す + 再現テスト） |
| R3 | 巻き戻しが `set(counters) - counter_names_before` で消すため、同じ間に他のトリガーが入れた名前も消し得る（`linked_call.py:20-21`・タイミング依存で未実測。codex P2 と同じ） | **採用**（その押下の文脈が初めて入れた名前〔差分 0 のリセットを含む〕だけを記録して消す。§4.1 の「押下の文脈で記録」に沿う） |
| R4 | 呼び出し先の不正な `amount` のエラーが呼び出しの行で通知される（codex P3・`call_context.py:275`） | **保留**（ループ回数・待機 ms の不正と同じ既存の扱い。§4.2 も「同じ扱い」） |
| R5 | `counters is None` のとき counter_text は `(=0)`（`sequence_control.py:194-197`） | 除外（file_line と同じ） |
| R6 | §5.3 の描き直しの通知は `refresh_actions` 経由で代用 / counter_text の送信失敗だけラベル付き | task_07 の正本反映で実装に合わせて記載 |
| R7 | 開始値を `CounterValues(dict)` の属性に持つ（dict へ写すと失う） | 保留（参考） |
| R8 | `test_minimize_grab_custody` 2 件 | 解決: 単体 29 pass（全体実行時のみの干渉・phase 76 と無関係） |

## 採用分の修正（ユーザー 2026-11-23: R1〜R3 採用・R4〜R8 は推奨どおり）

### R1（tests_ui のみ・コード不変）

- `tests_ui/test_call_view_compact.py:120` / `test_call_view_frame.py:106,123,427` / `test_full_view_panes.py:186` / `test_full_view_scroll_areas.py:237` の `CallViewSummary(...)` に `counter_starts={}`（または検証内容に合う値）を足す
- `tests_ui/test_key_hold_presentation.py:23` の `SimpleNamespace` スタブに `counter_starts={}`
- `tests_ui/test_config_io_characterization_keymap_set_startup.py` の 4 件（`test_import_config_success` / `test_load_startup_and_config_empty_when_stored_path_missing` /
  `test_load_startup_and_config_swallows_load_exception_and_falls_back` / `test_restore_default_yes`）の期待の辞書に `counter_starts: {}` を足す（新しい仕様 §3.3 の既定）
- `CallViewSummary` に既定値は付けない

### R2 + R3（application・巻き戻しで消す名前）

- 暫定 58 §4.1: 巻き戻しは「**その押下で初めて `counters` に入った名前のキーを消す**（押下の文脈で記録・差分 0 のリセットを含む）」。
  今の「押下の前の名前の集合との差（`set(counters) - counter_names_before`）」をやめ、**この押下の流れが counters へ書いた時に新しく入った名前だけ**を押下の文脈に積み、巻き戻しでそれだけを消す
  （書き込みは lock の中なので、書く直前と直後の差がその押下の追加分）。他のトリガーが同じ間に入れた名前は消さない。
- 連続実行（`run_to_end.py`）では、待機をまたいでも**押下の最初の区間からの追加分**を持ち回る（区間ごとに取り直さない・今の `run_to_end.py:205` の問題）。
  `_run_to_end_snapshot` と同じ寿命で持つ。単発（`sequence_runner.py:412`）・`linked_call.py:145`（確定後の取り直し = 空に戻す）も同じ形へ。
- 対象: `call_context.py`（`counter_names_before` の置き換え）・`linked_call.py`・`call_run_to_end.py`・`call_wait.py`・`run_to_end.py`・`sequence_runner.py`。他の挙動は変えない
- テスト（`tests/`）: ① 連続実行で `[counter_inc m, wait, call 使用中の呼び出し先]` 相当 → 無視の巻き戻しで m が未使用に戻り、続けて開始値を変えると追従
  ② 押下の間に別のトリガーが入れた名前は巻き戻しで消えない ③ 既存の `test_ignored_call_rolls_back_new_counter_keys_for_increment_and_zero_reset`（`tests/test_sequence_runner_call.py:2482` 付近）が通る形を保つ

## 読むファイル

- `instructions/history/58_counter_expansion.md` §3〜§5・§7（照合の基準）
- `instructions/phase/76_counter_expansion/phase.md`「レビュー方針」
- 照合時は tests 配下の task_01〜05 で足したテスト（`git diff --stat 4129c67b..HEAD -- tests tests_ui`）のみ

## 含まない

- 指摘の修正（採否確定後に本 task の後段で実装エージェントへ委任）
- 正本への昇格・暫定 58 の凍結・decisions_archive・codebase_map・current.md 完了記載・`/refactor_check`（task_07）
- 暫定 58 §8 のスコープ外項目

## 確認

- compileall clean / tests 全件 pass（失敗 0）/ tests_ui 全件 pass / smoke pass
- 受け入れ条件 1〜8 の分類表が本ファイルにある
- deep-reviewer・codex-reviewer の指摘が裏取り済みで表にある

## 完了条件

- 上記確認 pass・指摘の採否をユーザーが確定し、採用分の修正が検証 + **reviewer 採用**を通過
- 実機目視は本タスクでユーザーが実施し、結果を受領

## 修正後の結果（2026-11-23）

- 実装: codex-delegating-implementer（Sol medium・Luna high サブエージェント使用〔自己申告〕）。R1 = tests_ui 6 ファイル / R2+R3 = `CallContext.added_counter_names` と `track_counter_additions`（書く前後の差を lock 内で記録）・連続実行は `_run_to_end_added_counter_names` で待機をまたいで持ち回り・
  settle 系（`call_wait` / `call_run_to_end` / `call_context` / `send_wait._settle_after_stopped_sequence`）も記録。`linked_call._propagate_linked_completion` は確定後のため対象外。`codebase_map.md` に 1 行。
- reviewer: 1 回目 = 修正要（settle 系の記録漏れ）→ 差し戻し → 2 回目 = **採用**（指摘なし）。
- 実測: compileall clean / tests **2257 pass**（skip 7）/ tests_ui **1316 pass**（全体 1 本）/ smoke pass。
- 残り: 実機目視（ユーザー）。

## 実機目視の結果と追加の修正 R9（2026-11-23）

- 目視: 下記 R9 以外は問題なし（ユーザー）。保存 → 読込・サンプル設定に戻すの目視は自動テスト（`CounterStartsSyncTest` 等）で代える（ユーザー合意）。
- **R9（ユーザー判断 A・暫定 58 v1.1 §5.3「保留の反映」）**: 一覧・次のアクションの要約・呼び出し先の表示枠の `(=値)` を、実効値に**そのトリガーの保留中のカウンター操作を控えた順に反映した値**にする（表示用の写し・AppState 不変・実行の挙動不変）。
  - application: `sequence_steps.py` に表示用の関数（例 `preview_counter_values(counters, deferred) -> dict[str, int]`）= `counters` の写し（`CounterValues` なら開始値も写す）へ `apply_deferred_counters` と同じ規則で保留を反映し、`counter_display_values` と同じ形の dict を返す。元の `counters` は変えない
  - `call_view.py` の `build_call_view_summary` に `deferred` を受ける引数（既定 `()`）を足し、`counters` の写しをこの関数で作る。`call_view_notice.py` は最上段の保留を渡す（進行中の文脈の段〔`ctx.changed_frames` の `frame.deferred`〕があればそれ、無ければ `state.deferred_counters_for(trigger_set_id).get(top, [])`）
  - presentation: `trigger_panel_controller.py:299`（一覧）・`:506`（次のアクションの要約）は、選択中のトリガーが有効な行なら `state.deferred_counters_for(trigger_set_id).get(key, [])` を渡した表示用の値を使う（有効でない行は従来どおり）
  - テスト（tests/）: ① `[count+3] n, counter_text n` で 1 回目の後（保留あり）に表示用の値が 実効値+3 になり、実行で入力される値と一致 ② 保留のリセットは開始値 ③ 元の counters が変わらない ④ 呼び出し先の表示枠の summary が最上段の保留を反映
- R9 の結果: codex-implementer（Luna high）が `preview_counter_values`（`sequence_steps.py`）・`build_call_view_summary(deferred=)`・`call_view_notice`（進行中の段の保留を優先）・一覧 / 次のアクションの要約を実装 + tests 4 件。
  reviewer 1 回目 = 修正して採用（import 整理・変数化・changed_frames 分岐のテスト・tests_ui スタブに `deferred_counters_for`）→ 2 回目 = **完了可**。
  tests_ui 全体の 2 件: `test_trigger_effective_row_transition` は固定データが古い保留の形（2 要素）→ メインで 1 行修正 / `test_compact_window` は単体で pass（全体実行時のみの揺れ・phase 76 と無関係）。
  実測: compileall clean / tests **2262 pass** / tests_ui 全体 1316 件（上記 2 件を除き pass・2 件は単体で 10 / 8 pass）/ smoke pass。残り = R9 の再目視（ユーザー・描き直しの契機を含む）。
