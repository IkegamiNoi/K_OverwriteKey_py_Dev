# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-27T23:30:00
phase: instructions/phase/05_keymap_set_new_and_default_dir（**Phase α・task_01 完了 / 全 6 タスク中 1 完了**）
last_commit_location: claude/opus5-prompt-tuning-f6076e ※現在地はセッション開始時の git 実測値が正

## current
focus: **Phase α の task_01（起動時ディレクトリ骨格作成）完了（verifier 全緑・reviewer 完了可・指摘なし）。次は task_02（new_config_empty_path）を `/task_new` で起票し codex-implementer へ委任**。
mode: implementing

## last_action
ts: 2026-07-27T23:30:00
who: main
summary: |
  【task_01（startup_dir_skeleton）完了 = Phase α 最初の実装タスク】
  - 起票: `tasks/task_01_startup_dir_skeleton.md`。コード実読で暫定仕様に無い判断 2 点をタスク定義で先に確定させた:
    ① `_ensure_split_config_dirs` は private のため presentation から直呼びできない → **公開名へリネーム**
    （新メソッド追加ではなくリネーム。互換エイリアス禁止）② 既存 tests_ui が `app_module.os.makedirs` を
    patch して実ディレクトリ作成を止めており、作成処理が config_service 側へ移ると patch をすり抜けて
    リポジトリ配下に実ディレクトリが作られる → **patch 対象を `ConfigService.ensure_split_config_dirs` へ差し替え**。
  - 実装（codex-implementer）: config_service のリネーム + 内部呼び出し追従 / `app.py:56` の
    `os.makedirs(user_root)` を `ensure_split_config_dirs(config_root)` へ**置換** / 新規テスト 3 本。
  - **Codex は sandbox 制約で python 検証 1〜4 を実行できず未実行申告** → 運用ルールどおり verifier で `.venv` 再実行。
  - **検証**（verifier・全緑）: compile clean / tests **87**（+1）/ tests_ui **76**（+2）/ smoke pass /
    `_ensure_split_config_dirs` 残存 0 件 / `config/` 配下に未追跡ディレクトリなし。
  - **レビュー**: reviewer=**完了可・必須指摘なし**（リネーム完全・置換であり追加でない・既存テストを緩めていない・
    task_02〜04 の先取りなし）。参考指摘 1 件: 新規 tests_ui の `save_json` 未呼び出しアサーションは
    「config.json 非書込」より広い保証（現状は意図どおりで修正不要）。
result_files:
  - keyseq/application/config_service.py（`ensure_split_config_dirs` へリネーム + 内部呼び出し追従）
  - keyseq/presentation/app.py（起動時の makedirs を置換）
  - tests/test_config_service.py（+1・7 ディレクトリ作成の単体テスト）
  - tests_ui/test_startup_font_characterization.py（patch 対象の差し替えのみ）
  - tests_ui/test_startup_dir_skeleton.py（新規・+2・起動時呼び出し / config.json 非書込）
  - instructions/phase/05_keymap_set_new_and_default_dir/tasks/task_01_startup_dir_skeleton.md（新規）
verified:
  compile: clean
  tests: pass 87（ベースライン 86 → +1）
  tests_ui: pass 76（ベースライン 74 → +2）
  smoke: pass
  review: reviewer=完了可（指摘なし）
  実機目視: 未実施（task_05 でまとめて依頼する方針）

## next_action
- **task_02（`new_config_empty_path`）を `/task_new` で
  `instructions/phase/05_keymap_set_new_and_default_dir/tasks/task_02_new_config_empty_path.md` へ起票**し、
  `codex-implementer` へ実装委任する（暫定 04 §3・§4・§7-1 / **受入条件 1** が根拠）。
  - 内容: `keymap_set_io.py` の `new_config`（:33）で `keymap_set_path` を **空文字**にする /
    `save_keymap_set`（:44-49）の先頭で空パスなら `save_as(...)` へ委譲 /
    `save_as`（:51-66）の `initialfile` を固定 `default.json` ではなく **`keymap_set.json`**（一般名）にする。
  - `confirm_save_if_dirty`（:9-24）は既存の空パス分岐で正しいため**変更しない**（二重に save_as へ回さない）。
  - `save_keymap_set_to` のロジック（正規化・分割保存・ダイアログ）は**変更しない**。
- 以降 task_03〜06 は phase.md「タスク」表の順で進める（各タスクで reviewer 必須・
  task_05 統合と完了判定前は Codex レビュー + `deep-reviewer` を併用）。
- **α は挙動変更フェーズ**（挙動不変ではない）。β/γ/プリセットは α 完了後に順次 `/phase_start`。

## blockers
- なし。

## resume_hints
- **python は必ず作業ツリー直下の `.\.venv\Scripts\python.exe` を使う**（2026-07-27 に方式変更。
  worktree ごとに `.venv` を持つ。ツリー外の `..\..\..\.venv` は Codex のサンドボックスが実行を拒否するため使わない）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。**新しい worktree では最初に `.venv` を作成する**
  （手順は `.claude/rules/python_rules.md`。`.venv` は .gitignore 済み）。
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
  **Codex 申告のテスト結果は信用せず必ず verifier で再実行**（phase 04 で 19件全 ERROR を検出）。
  Codex のサンドボックスは**作業ツリー配下しか実行できない**ため venv を worktree 内に置く方式へ変更した
  （2026-07-27・phase 05 task_01 で発覚。詳細と却下案〔--cwd 拡大〕は codex_operations.md §0）。
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
