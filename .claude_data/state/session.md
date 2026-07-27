# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-27T22:45:00
phase: instructions/phase/05_keymap_set_new_and_default_dir（**Phase α・起票完了・task_01 未起票**）
last_commit_location: claude/opus5-prompt-tuning-f6076e ※現在地はセッション開始時の git 実測値が正

## current
focus: **Phase α（phase 05_keymap_set_new_and_default_dir）を起票完了（reviewer 整合チェック=完了可・未コミット）。次は task_01（startup_dir_skeleton）を `/task_new` で起票し codex-implementer へ実装委任**。
mode: implementing

## last_action
ts: 2026-07-27T22:45:00
who: main
summary: |
  【Opus5 向け指示文の改修（コミット 43c1094 / 0c73758・ユーザーがコミット）】
  - `.claude/rules/output_style.md` を新設（応答の簡潔性 / 進捗報告のカデンス / 文書成果物の分量 /
    自己訂正の言及制限 / 委任量の抑制 / 検証の重ね過ぎ禁止）。CLAUDE.md に参照 + 末尾 `<tone_preference>`。
  - **レビュアーを 2 本立てに分離**: `reviewer`（sonnet・単一タスクの実装差分）/ **`deep-reviewer`（opus・新設。
    設計文書 / 複数タスクを跨ぐ差分 / フェーズ完了判定。5観点 + 前提・未定義挙動・矛盾・実装可能性・正本整合・代替案）**。
    agent_selection.md のレビュー表を Claude 側 / Codex 側の 2 列へ再構成。spec_draft の起票時レビューは deep-reviewer へ。
  - `/phase_start` の phase.md レビューを**整合チェック限定**に縮小（設計の再レビューはしない = 三重レビューの解消）。
  - **不具合修正**: `switch_files/codex/` 側の agent_selection.md が live 版から乖離しており、モード切替で
    Codex 運用ノート等が巻き戻る状態だった → live を正として同期。deep-reviewer は switch_files 管理外＝両モードで残る。
  【Phase α（phase 05）起票（未コミット）】
  - `instructions/phase/05_keymap_set_new_and_default_dir/phase.md` を新規作成（主入力=暫定 04 v0.3）。
    タスク 6 本: 01 起動時ディレクトリ骨格 / 02 新規=空パス+保存の空パス→別名分岐+initialfile / 03 Import 後クリア+
    空起動 path 空+default.json 用途整理 / 04 prompt_if_missing 撤去 / 05 統合退行 / 06 正本反映。
  - `current.md`: アクティブを phase 05 へ差し替え / 次採番 06（β=06・γ=07・プリセット=08）/ 暫定次採番 08 /
    idea_05 は「Phase β が内包」へ更新（単独フェーズ化しない）。
  - **レビュー**: reviewer（整合チェック限定）=**完了可**。軽微指摘 1 件（task_05 に受入 7・8 のタグ明記）を反映済。
  - 起票元はユーザー要望であり idea 由来ではないため backlog/INDEX.md の更新対象なし。
result_files:
  - instructions/phase/05_keymap_set_new_and_default_dir/phase.md（新規・未コミット）
  - instructions/phase/current.md（アクティブ / 次採番 / 次フェーズ候補・未コミット）
  - .claude/rules/output_style.md・.claude/agents/deep-reviewer.md（新規・コミット済）
  - CLAUDE.md / .claude/rules/agent_selection.md / .claude/agents/reviewer.md /
    .claude/commands/{phase_start,spec_draft}.md / switch_files 両モードの agent_selection.md（コミット済）
verified:
  review: reviewer 整合チェック=完了可（主入力との齟齬なし / 受入 1〜8 と §10 の割当漏れなし / リンク・番号対応・
    「読むファイル」9 パスの実在をすべて確認）
  commit: 43c1094 + 0c73758（指示文改修のみ）。phase 05 起票分は**未コミット**
  production_scope: 文書のみ（keyseq/ の実装は未着手）

## next_action
- **phase 05 の起票分（phase.md + current.md）を `/task_commit` でコミット**する（未コミット）。
- 次に **task_01（`startup_dir_skeleton`）を `/task_new` で
  `instructions/phase/05_keymap_set_new_and_default_dir/tasks/task_01_startup_dir_skeleton.md` へ起票**し、
  `codex-implementer` へ実装委任する（暫定 04 §5「起動時ディレクトリ作成」・受入 2 が根拠）。
  - 内容: `keyseq/presentation/app.py` の起動時に `config/user/{keymap_sets,keymaps,trigger_sets,hotkey_presets,sequences}`
    を一括作成（`config_service._ensure_split_config_dirs` 相当を再利用）。**config.json は起動時に書かない**。
  - 完了条件に「reviewer 採用」を必ず含める。新挙動は特性テストで固定（暫定 04 §8）。
- 以降 task_02〜06 は phase.md「タスク」表の順で進める（各タスクで reviewer 必須・
  task_05 統合と完了判定前は Codex レビュー + `deep-reviewer` を併用）。
- **α は挙動変更フェーズ**（挙動不変ではない）。β/γ/プリセットは α 完了後に順次 `/phase_start`。

## blockers
- なし。

## resume_hints
- **python は必ず `..\..\..\.venv\Scripts\python.exe`（worktree相対）を使う。グローバル `py` は依存欠落で tests_ui/smoke が落ちる。**
- **保存系リデザインの設計の正は暫定仕様 04〜07（すべてユーザー確定・v0.2/v0.3）**。番号対応は
  Phase α=phase05/暫定04 / β=phase06/暫定05 / γ=phase07/暫定06 / プリセット=phase08/暫定07。
  討議の全経緯（点1〜5・敵対レビュー4本の指摘と対応）は各暫定仕様の版履歴と §確定事項に集約済。
  依存: α→β の順（β は α のディレクトリ化前提・idea_05 内包）。γ は独立。プリセット07 は β とカスケード除外で協調。
- phase 04 は完了・アーカイブ済（判断は `decisions_archive/04_config_io_controller_split.md` が正）。config_io は
  `controllers/config_io/` の6クラスへ分割済（App が `app.keymap_set_io` 等で直接公開・`config_io` 名は消滅）。
- **レビュアーは 2 本立て**（2026-07-27〜）: `reviewer`（sonnet・単一タスクの実装差分）/ `deep-reviewer`（opus・
  設計文書 / 複数タスクを跨ぐ差分 / フェーズ完了判定）。使い分けは `.claude/rules/agent_selection.md` のレビュー表が正。
  出力の作法（応答・進捗報告・文書分量・委任量）は `.claude/rules/output_style.md`。
- idea_05（trigger_set の source_path 不整合）は **Phase β が内包**する（単独フェーズ化しない）。
  既存不整合の詳細は暫定仕様 03 §1「既存の不整合」/ idea_05 に記載。
- **【Codex 運用の手順書】ジョブが詰まった / cancel が効かない / ハング検知 / state 手修復は
  `instructions/common/rules_detail/codex_operations.md` を読む**（`.claude/rules/agent_selection.md` 冒頭にポインタ）。
  **Codex 申告のテスト結果は信用せず必ず verifier で `.venv` 再実行**（今回 19件全 ERROR を検出）。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**。
  main リポジトリ側の絶対パスを編集すると commit から漏れる（phase 02・03 で再発）。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規（未追跡）ファイルの確認には**直接 `grep`** を使う。
- 行数計測は `wc -l`（PowerShell `Measure-Object -Line` は空行を数えず誤解の元）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引あり）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 02_hotkey_validation / 03_startup_font_settings_cleanup / 04_config_io_controller_split。
- 未着手 idea: idea_05（trigger_set source_path・**Phase β で内包**）/ idea_03（hotkey 保存時正規化・優先度低）/
  idea_07（参照元の掃除・β 完了後）/ idea_08（keymap_set 個別プリセット・プリセット案2 完了後）。
  保留 idea: idea_04（FontSettingsController）/ idea_06（D/E/F 共通化）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
