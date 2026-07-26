# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-27T12:00:00
phase: **フェーズ間（phase 04 完了・phase 05 未起票）**。保存系リデザインの暫定仕様 04〜07 をユーザー確定済（未実装）
last_commit_location: claude/task-06-proceed-eb9f1b ※現在地はセッション開始時の git 実測値が正

## current
focus: **保存系リデザインの暫定仕様 4 本（04=α/05=β/06=γ/07=プリセット）を敵対的レビュー反映・ユーザー確定まで完了（コミット dfa8f95）。次は Phase α（暫定04）を `/phase_start` で phase 05 として起票し実装着手**。
mode: completed

## last_action
ts: 2026-07-27T12:00:00
who: main
summary: |
  【保存系リデザインの暫定仕様 04〜07 を起票・敵対的レビュー・ユーザー確定（コミット dfa8f95）】
  - ユーザー要望（保存系統の改善・点1〜5）を 4 フェーズへ分割し設計討議 → 暫定仕様先行モードで起票:
    04 α（新規=空パス/保存先ディレクトリ化/prompt_if_missing 撤去・v0.3）/ 05 β（子ファイル保存の確認ダイアログ+
    参照元記録・idea_05 内包・v0.2）/ 06 γ（停止/トグルキーの config.json 既定化+個別指定・v0.2）/
    07（プリセットの config.json グローバル化・v0.2）。
  - 各仕様に codex-adversarial-reviewer を実施（04=指摘4 / 05=critical1+high3 / 06=6 / 07=4）→ 全指摘を精査し
    ユーザー確定のうえ v0.2/v0.3 へ反映。idea_07（参照元の掃除機能）/ idea_08（keymap_set 個別プリセット）を起票。
  - フェーズ番号対応（予定）: **Phase α=phase05/暫定04 / β=phase06/暫定05 / γ=phase07/暫定06 / プリセット=phase08/暫定07**。
  【（前タスク: phase 04 task_06 正本反映・完了。詳細は decisions_archive/04）】
  - config_io_controller.py（598行）を config_io/ 6クラスへ分割完了・codebase_map 反映・refactor_check 不要。
  - `codebase_map.md`: presentation ツリー図に `controllers/config_io/`（6ファイル）追記 / コントローラ節の
    ConfigIoController 行を6クラス（KeymapSetIo/StartupIo/IoDialogs/KeymapFileIo/TriggerSetFileIo/SequenceFileIo）
    + App 公開名へ差し替え / `config_io.write_startup`→`startup_io.write_startup` / `app.config_io`例→`app.keymap_set_io`。
  - spec_detail 昇格要否: `config_io` 言及0件（再grep）→ **昇格不要**（担当層は codebase_map.md が正・architecture §3.5）。
  - 暫定仕様 03 を**凍結**（ヘッダ「凍結・正本反映済」）。`decisions_archive/04_config_io_controller_split.md` 新規作成し
    decisions.md の phase 04 詳細を集約・索引化（詳細セクション削除）。
  - `current.md`: アクティブ=なし（04完了）/ 次採番 phase 05・暫定 04 明記 / idea_05 を有力候補・idea_06 の条件充足更新。
  - task_06 定義起票。**/refactor_check 判定=不要**（M3 の同型3ブロックは既存重複の移設で idea_06〔保留〕がカバー済＝既知。他は非該当）。
  - **検証**: verifier=全緑（compile clean / tests 86 / tests_ui 74 / smoke pass / 旧ファサード参照0件）。
    **レビュー**: reviewer=完了可（採用・指摘なし・文書と実構成が完全一致）。
result_files:
  - instructions/history/04_keymap_set_new_and_default_dir.md（新規・v0.3 確定）
  - instructions/history/05_child_file_save_dialog.md（新規・v0.2 確定）
  - instructions/history/06_hook_keys_global_default.md（新規・v0.2 確定）
  - instructions/history/07_hotkey_presets_global.md（新規・v0.2 確定）
  - instructions/backlog/idea_07_reference_link_cleanup.md / idea_08_per_keymap_set_preset_ownership.md（新規）
  - instructions/backlog/INDEX.md（idea_07/08 追加）
verified:
  spec_review: codex-adversarial-reviewer 実施済（全4本）・指摘反映・ユーザー確定
  commit: dfa8f95
  production_scope: 文書のみ（実装は未着手）

## next_action
- **保存系リデザインの暫定仕様 4 本は確定・コミット済（dfa8f95）**。次は **Phase α（暫定 04）を `/phase_start` で
  phase 05 として起票し、実装に着手**する（順序: α→β→γ→プリセット。α は独立・小さいので先行）。
  - Phase α のタスク: new_config の空パス化 / save_keymap_set の空パス→別名分岐 / import_config の無条件クリア /
    起動時ディレクトリ骨格作成 / 別名保存 initialfile=`keymap_set.json` / prompt_if_missing 撤去（新規出力停止・残置許容）。
  - **α は挙動変更フェーズ**（挙動不変ではない）。特性テストで新挙動を固定する（暫定 04 §8）。
- 実装は `.claude/rules/agent_selection.md` の既定（codex-implementer）へ委任。各タスクで reviewer 必須。
- β/γ/プリセットは α 完了後に順次 `/phase_start`（暫定 05/06/07 が設計の正）。
- idea 位置づけ更新（β 起票時）: idea_05→β 内包・idea_06→β 達成見込みを INDEX へ反映。

## blockers
- なし。次は Phase α の `/phase_start`（ユーザー着手指示待ち）。

## resume_hints
- **python は必ず `..\..\..\.venv\Scripts\python.exe`（worktree相対）を使う。グローバル `py` は依存欠落で tests_ui/smoke が落ちる。**
- **保存系リデザインの設計の正は暫定仕様 04〜07（すべてユーザー確定・v0.2/v0.3）**。番号対応は
  Phase α=phase05/暫定04 / β=phase06/暫定05 / γ=phase07/暫定06 / プリセット=phase08/暫定07。
  討議の全経緯（点1〜5・敵対レビュー4本の指摘と対応）は各暫定仕様の版履歴と §確定事項に集約済。
  依存: α→β の順（β は α のディレクトリ化前提・idea_05 内包）。γ は独立。プリセット07 は β とカスケード除外で協調。
- phase 04 は完了・アーカイブ済（判断は `decisions_archive/04_config_io_controller_split.md` が正）。config_io は
  `controllers/config_io/` の6クラスへ分割済（App が `app.keymap_set_io` 等で直接公開・`config_io` 名は消滅）。
- **次候補 idea_05（E=trigger_set の source_path 不整合修正）は挙動変更を伴う**。着手時は spec_change_workflow の
  仕様変更フロー（暫定仕様先行モード）で。既存不整合の詳細は暫定仕様 03 §1「既存の不整合」/ idea_05 に記載。
- **【Codex 運用の手順書】ジョブが詰まった / cancel が効かない / ハング検知 / state 手修復は
  `instructions/common/rules_detail/codex_operations.md` を読む**（`.claude/rules/agent_selection.md` 冒頭にポインタ）。
  **Codex 申告のテスト結果は信用せず必ず verifier で `.venv` 再実行**（今回 19件全 ERROR を検出）。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**。
  main リポジトリ側の絶対パスを編集すると commit から漏れる（phase 02・03 で再発）。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規（未追跡）ファイルの確認には**直接 `grep`** を使う。
- 行数計測は `wc -l`（PowerShell `Measure-Object -Line` は空行を数えず誤解の元）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引あり）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 02_hotkey_validation / 03_startup_font_settings_cleanup / 04_config_io_controller_split。
- 未着手 idea: idea_05（trigger_set source_path・**着手条件充足＝有力候補**）/ idea_03（hotkey 保存時正規化・優先度低）。
  保留 idea: idea_04（FontSettingsController）/ idea_06（D/E/F 共通化）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
