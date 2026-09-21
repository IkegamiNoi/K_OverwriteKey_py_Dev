# task_03_record_and_close

## 目的

phase 26 の**記録と完了**（フェーズ最終タスク）。正本改訂は task_01、実装は task_02 で完了し、
**実機目視も OK**（ユーザー確認 2026-09-21）。本タスクは判断履歴の集約・ルーティング更新・
リファクタ判定までを行い、フェーズを完了扱いにする。

レイヤ制約: **文書作業のみ**。コード変更なし。正本 `data_schema.md` の再改訂もしない
（task_01 で確定済み）。

## 対象範囲（文書のみ）

### .claude_data/state/decisions_archive/26_startup_entry_preservation.md（新規）

1. phase 26 の判断履歴を集約する（`decisions_archive/25_...md` の書式に倣う）。
   記載する判断: ①仕様変更と判定した理由（正本 §5.4 が「保存で更新する」と規定していた）
   ②直接改訂モードを選んだ理由 ③論点 1 = 案 A（起動時の実読込結果）採用 / 案 B（`os.path.exists`）除外
   ④論点 2 = 別名保存でも据え置き ⑤論点 3 = 可視化 UI / 解除手段は除外
   ⑥実装上の判断（判定は application 1 箇所 / `entry_loaded` の更新契機 3 経路 /
   **`write_startup` には入れない**理由 / 既定引数 False）⑦現状監査の結果
   ⑧残件（`.strip()` 非対称の参考指摘・phase 25 残件①との関係）。

### .claude_data/state/decisions.md

2. 「アーカイブ索引」へ phase 26 の行を追加し、**本文の phase 26 節は削除**する
   （完了フェーズの判断は archive が正・本ファイルは索引のみ）。

### instructions/phase/current.md

3. 「現在の参照先」の phase 26 項を**完了記載（リンクのみ）**へ更新する。
4. 「直近の一連の作業が扱っている領域」を **phase 26 の内容**（起動エントリの書き込み契機）へ差し替え、
   phase 25 以前の領域記述を 1 段ずつ繰り下げる。
5. 「直前の完了フェーズ」リンクを 26 / 25 / 24 へ更新する。
6. 「別タスク化候補」へ Phase 26 項を追加する（`.strip()` 非対称の参考指摘・到達不能のため据え置き）。
7. 「次採番」節の phase 26 行を**完了記載**へ更新する（次採番 27 は task_01 で設定済み・**再変更しない**）。

### instructions/phase/26_.../phase.md

8. 「タスク」一覧へ task_03 の完了を反映する。

### instructions/backlog/

9. **更新不要**（起票元はユーザー要望であり idea なし）。対応不要であることを完了報告に書く。

## 読むファイル

- `.claude_data/state/decisions.md`「アーカイブ索引」節 + phase 26 節（`:546-` 以降）
- `.claude_data/state/decisions_archive/25_path_field_type_normalization.md`（書式の手本）
- `instructions/phase/current.md`「現在の参照先」「次採番」「別タスク化候補」「フェーズ完了時の指示」
- `instructions/phase/26_startup_entry_preservation/phase.md`

## 含まない

- コード・テストの変更（task_02 で完了）
- 正本 `data_schema.md` / `5_08_09_orphan_sweep.md` の再改訂（task_01 で完了）
- `codebase_map.md` の更新（task_02 で実施済み）
- reviewer 参考指摘（`.strip()` 非対称）の修正 — **到達不能のため候補送り**
- phase 25 残件①（`startup_io.py` の `keymap_set_path` の**型正規化**）— 別件・未着手のまま
- main へのマージ（ユーザーが行う）

## 確認

1. `decisions.md` の索引リンクが実在ファイルを指し、**本文に phase 26 節が残っていない**こと。
2. `current.md` の完了記載に**要約を書いていない**こと（リンクのみ。要約は archive が正）。
3. `/refactor_check` を実行し、判定結果（要否・根拠 M1〜M6）を完了報告に含めること。
4. 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui`

## 完了条件

- 上記確認 1〜4 が pass・**reviewer 採用**（観点: 記録の漏れ・既存記述との矛盾・不要変更の有無）。
- 実機目視: **完了済み**（2026-09-21・ユーザー OK）。
- 本タスク完了をもって phase 26 を完了とする。
