# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-19T23:45:00
phase: instructions/phase/03_startup_font_settings_cleanup/phase.md（主入力＝暫定仕様 instructions/history/02_startup_font_settings_cleanup.md v1.0）
last_commit_location: claude/phase-03-task-01-a60716（worktree: priceless-fermat-2a15c1）※現在地はセッション開始時の git 実測値が正

## current
focus: **フェーズ 03 task_02（coerce → theme.py 移設）完了・全緑・reviewer 採用。次は task_03（startup_settings.py 切り出し）**。
mode: pending_review              # task_02 完了・コミット済。task_03 実装着手待ち。

## last_action
ts: 2026-07-19T23:45:00
who: main
summary: |
  【phase 03 task_02_theme_coerce_font_delta 完了】
  負債②（逆参照）解消。`theme.py` にモジュール純関数 `coerce_font_delta` を新規追加（現行
  App._coerce_font_delta のロジックを 1:1 不変移設）→ 呼び出し元4箇所差し替え（app.py 58/228/390・
  config_io_controller.py:278 の `self._app._coerce_font_delta` 逆参照除去）→ App._coerce_font_delta 削除。
  - 安全網維持: tests_ui の特性テスト coerce 呼び出しを theme.coerce_font_delta へ付け替え（アサーション不変）。
  - 前進ユニット: tk 不要の coerce 単体テスト tests/test_theme_coerce.py 新規（5 ケース）。
  - 実装 codex-implementer → verifier 全緑 → reviewer 5観点「採用（完了可）・指摘なし」。
  - 受け入れ条件: `git grep "_coerce_font_delta" -- keyseq/` 0件・コードの `_app._coerce_font_delta` 0件（残りは docs/state の経緯記述のみ）。
result_files:
  - keyseq/presentation/theme.py（coerce_font_delta 追加）
  - keyseq/presentation/app.py（import・呼び出し3箇所・メソッド削除）
  - keyseq/presentation/controllers/config_io_controller.py（import・逆参照除去）
  - tests_ui/test_startup_font_characterization.py（coerce 呼び出し先付け替え）
  - tests/test_theme_coerce.py（新規）
  - instructions/phase/03_startup_font_settings_cleanup/tasks/task_02_theme_coerce_font_delta.md（新規・起票）
verified:
  compile: clean
  test(tests): pass 82            # 基準77 + coerce 5
  test(tests_ui): pass 20
  smoke: pass

## next_action
- **task_03_startup_settings_loader を起票（/task_new）→ codex-implementer へ実装委任**:
  新規 `keyseq/presentation/startup_settings.py` に `load_startup_settings(config_service, startup_path, *, on_read_error) -> dict`
  を作成（I/O は `config_service.load_startup` 直依存・**未知キー全保持**・`ui_font_delta_pt`=`theme.coerce_font_delta` /
  `prompt_if_missing`=bool 正規化・**真理値表どおり例外時のみ on_read_error(exc)**）→ `App._load_startup_settings` 削除・
  `app.py:57` を新ローダ呼び出しに差し替え（on_read_error に `messagebox.showwarning("startup.json 読込失敗", ...)` を注入）。
  tk 不要のローダ単体テスト（真理値表4分岐 + 未知キー保持 + on_read_error 呼出/文言）を tests/ に追加。暫定仕様 §5。
- **注意**: 初期化順序を壊さない（config_service〔app.py:43〕のみ依存・config_io〔:127〕に非依存・:57 実行位置保持）。
  安全網 test_load_startup_settings_* は App._load_startup_settings 削除で破綻するため、呼び出し先を新ローダへ付け替える
  （アサーション不変。§8 の真理値表/未知キー契約を維持）。
- 検証は verifier（.venv 全緑 + 受け入れ条件 §8-3/§8-4）、レビューは reviewer。緑＋採用なら /save_state → /task_commit（standing 許可済）。
- 以降 task_04（font apply/uivars・二次レビュー codex-reviewer 併用・**実機目視=ユーザー**）→ task_05（正本反映・記録）。

## blockers
- なし（task_02 完了・git クリーン・標準検証全緑）。

## resume_hints
- **python は必ず `..\..\..\.venv\Scripts\python.exe`（worktree相対）を使う。グローバル `py` は依存欠落で tests_ui/smoke が落ちる。**
- **設計の正は暫定仕様 `instructions/history/02_startup_font_settings_cleanup.md`（v1.0）**。phase.md は設計を再定義していない（参照のみ）。
  番号対応: phase 03 / 暫定 02 / decisions `decisions_archive/03_startup_font_settings_cleanup.md`（暫定仕様は独立採番）。
- **【罠】state ファイル（`.claude_data/`）は worktree のパスで編集する**。main リポジトリ側の絶対パスへ編集すると
  worktree の追跡ファイルに反映されず commit から漏れる（phase 02 で複数回遭遇）。
- 実装は codex-implementer が既定（agent_selection.md）。Codex は sandbox から `.venv` python を起動できないため、
  標準検証はメイン側/verifier が `.venv` で実行する分担。**Codex 申告のテスト結果は信用せず必ず verifier で実行する**。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規（未追跡）ファイルの確認には**直接 `grep`** を使う。
- **app.py の行数計測は `wc -l`**（現 466 行）。PowerShell `Measure-Object -Line` は空行を数えず誤解の元。
- phase 03 の要注意点（暫定仕様 02）: ①未知キー全保持（keymap_set_path 消失防止・最優先の後方互換）
  ②エラー通知の真理値表を保つ（欠損=無警告/例外=警告1回/非dict=無警告・文言1文字一致）
  ③初期化順序（起動設定ローダは config_service〔:43〕のみ依存・config_io〔:127〕に依存しない）
  ④メニュー再構築は build_menu_bar のみ（bind_menu_shortcuts を呼ばない副作用を保持）⑤案B は実装しない。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引あり）+ `decisions_archive/<phase>.md`。
  完了済: 計画04 / 01_view_ref_cleanup（2026-07-17）/ 02_hotkey_validation（2026-07-18）。
- 未着手 idea: [idea_03](../../instructions/backlog/idea_03_action_hotkey_save_normalization.md)（アクション hotkey の保存時正規化・優先度低）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
