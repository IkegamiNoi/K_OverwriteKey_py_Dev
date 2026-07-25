# phase.md

## フェーズ名

ConfigIoController の責務分割（config_io_controller_split）

## フェーズの目的

`keyseq/presentation/controllers/config_io_controller.py`（**598 行・1 クラス・29 メソッド**）を
責務ごとに **6 モジュールへ分割**し、保守性と修正時の説明可能性を回復する。

- **対象レイヤ: presentation のみ**（`controllers/config_io/` を新設）。application / domain には触れない。
- **スキーマ変更: なし**。保存 JSON のバイト列を含め**挙動不変が絶対前提**。
- 起票元: ユーザー要望（2026-07-23）。`current.md`「別タスク化候補」に記録されていた
  「`config_io_controller.py` が 598 行で目安 600 行に接近」の着手。
- 主入力（暫定仕様）: [03_config_io_controller_split.md](../../history/03_config_io_controller_split.md)
  （**v0.4・ユーザー確定済**）
- モード: **暫定仕様先行モード**。番号対応: phase 04 / 暫定 03 / decisions 04。

## 確定（ユーザー 2026-07-23）

暫定仕様 03 §2 が正。要点のみ再掲する（**設計の正は暫定仕様。本ファイルで再定義しない**）:

- **挙動不変が絶対前提**。ダイアログ文言・表示順・flash メッセージ・保存 JSON のバイト列・
  例外時の分岐を一切変えない。
- **安全網（特性テスト）の追加を最初のタスクに置く**（§7-2 表）。分割はその後。
- **§4 = 案 B**: 外部呼び出し 30 箇所を本フェーズで差し替える（恒久ファサードを作らない）。
- **§5 = 案 1**: 同型ブロック D / E / F は分割のみ。共通化しない。
- **§1「既存の不整合」（E の source_path 分断）は直さずそのまま移設する**
  → [idea_05](../../backlog/idea_05_trigger_set_source_path_inconsistency.md)（phase 04 完了後に着手）。
- **`self._app.` reach-through（169 箇所）は本フェーズで扱わない**。

## スコープ

### 含む

- `controllers/config_io/` の新設と 6 モジュールへの分割（暫定仕様 §3 の対応表）。
- 特性テストの追加（暫定仕様 §7-2 の経路表）。
- 外部呼び出し 30 箇所・8 ファイルの差し替え（案 B）。
- `codebase_map.md` の反映・暫定仕様の凍結・記録類の更新。

### 含まない（後送り）

- E の source_path 不整合の修正 → [idea_05](../../backlog/idea_05_trigger_set_source_path_inconsistency.md)
- D / E / F の共通化 → [idea_06](../../backlog/idea_06_individual_json_io_unification.md)（保留）
- `self._app.` reach-through の解消 / `config_service`（application 層）の変更 /
  ダイアログ文言の修正（誤字を含む）/ `app.py` 起動シーケンスの整理

## このフェーズで読むファイル

1. `instructions/history/03_config_io_controller_split.md`（**主入力・設計の正**）
2. `keyseq/presentation/controllers/config_io_controller.py`（分割対象）
3. `keyseq/presentation/controllers/dirty_state.py`（E の source_path 周辺の確認用）
4. `tests_ui/test_startup_font_characterization.py`（**読む理由は 2 つ**: task_01 / task_02 では特性テストの
   monkeypatch 手法の先例として / task_05 では `config_io` を参照する 30 箇所の 1 つとして修正対象）
5. 呼び出し元 8 ファイル（task_05 で着手する時のみ。それまで読まない）:
   `views/menu_bar.py` / `app.py` / `views/full_view/{file_frame,trigger_box,sequence_box,keymap_box}.py` /
   `controllers/layout_controller.py`
6. `instructions/common/codebase_map.md`（最終タスクのみ）

※ `config_service`（application 層）は**読まない**（本フェーズで変更しないため）。

## タスク

| # | タスク | 概要 |
|---|---|---|
| task_01 | `characterization_tests_individual_json` | 特性テスト①: C（共有ダイアログ）+ D / E / F（個別 JSON IO）。**分割前のコードで pass すること**が完了条件 |
| task_02 | `characterization_tests_keymap_set_startup` | 特性テスト②: A（構成セット）+ B（起動設定）。**A/B は config_service へ委譲するため、バイト列比較ではなくコントローラの変換ロジック（渡す引数）を固定**。同上 |
| task_03 | `split_individual_json_io` | D / E / F を `config_io/{keymap,trigger_set,sequence}_file_io.py` へ分割（共通化しない） |
| task_04 | `split_keymap_set_and_startup` | A + A' / B / C を `config_io/{keymap_set_io,startup_io,io_dialogs}.py` へ分割 |
| task_05 | `replace_call_sites` | 外部 30 箇所の差し替え（対応表 → 機械的置換 → `grep -rn "config_io\."` 残存 0 件） |
| task_06 | `finalize_records` | 正本反映（`codebase_map.md`）・暫定仕様 03 の凍結・`decisions_archive/04` 作成・`current.md` 更新・`/refactor_check` |

**特性テストを 2 タスクに分けた理由**（2026-07-23・task_01 起票時に見積り）: 暫定仕様 §7-2 の経路表は
全体で **約 55〜60 ケース / テストメソッド 25 本前後**になり、1 タスクとしては大きすぎるため
（暫定仕様 §7-2 末尾「この表が過大なら分割の前にユーザーへ相談する」に基づく判断）。
分割の対象単位（task_03 = D/E/F、task_04 = A/B/C）と対応させ、**守る対象と安全網を対にする**。
C は task_04 で分割されるが、D/E/F から呼ばれるため特性テストは task_01 側に置く。

- task_03 と task_04 の順序は「依存の少ない D/E/F を先」とする。D/E/F が持つクラスタ外依存は
  **2 系統**あり、いずれも task_04 まで元の場所に残るため、task_03 では**参照経路のみ調整**する:
  - **C（共有ダイアログヘルパ）** — `choose_save_path_with_collision`（D:363 / E:445 / F:528）と
    `ask_link_label_to_filename`（D:389 / F:555。**E は呼ばない**）
  - **A（構成セット）** — `confirm_save_if_dirty`。**E の `load_trigger_set_file`（:487）のみ**が呼ぶ
    （D / F にはこの呼び出しがない）
- タスク定義ファイルは着手するタスクから順に `/task_new` で起票する（全部を先に作らない）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

1. **挙動不変の検証**（最重要）。移設の過程で条件式・呼び出し順・例外処理が変わっていないか。
   特に暫定仕様 §7-2 に挙げた分岐（`confirm_save_if_dirty` の 3 分岐 /
   `set_startup_keymap_set` の保存失敗後の続行 / `load_startup_and_config` の握りつぶし）。
2. **「既存の不整合」を直していないか**。E の source_path 分断（読み `app._trigger_set_source_path` /
   書き `dirty_tracker.trigger_set_source_path`）と、`:440` の到達不能な askyesno が
   **そのまま維持されている**こと。善意の修正が最も混入しやすい箇所。
3. **共通化の先取りをしていないか**（§5 = 案 1）。D / E / F に共通基底や共有ヘルパを
   新設していないか。
4. **スコープ外への波及がないか**。`self._app.` の書き換え・`config_service` の変更・
   ダイアログ文言の変更が入っていないか。
5. task_05 は**対応表どおりの機械的置換**になっているか（ついでの整理が混入していないか）。

- タスク単位の必須レビューは `reviewer`。**task_05 完了時（統合）とフェーズ完了判定前は
  Codex レビューを併用する**（`.claude/rules/agent_selection.md`）。
- 実機目視はユーザー。最低限「保存 / 読込 / 別名保存 / Import / Export / 起動設定変更 /
  keymap・トリガー一覧・シーケンスの個別保存読込」を確認してもらう。
