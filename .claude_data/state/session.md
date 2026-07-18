# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-18T03:00:00
phase: instructions/phase/03_startup_font_settings_cleanup/phase.md（主入力＝暫定仕様 instructions/history/02_startup_font_settings_cleanup.md v1.0）
last_commit_location: claude/task-04-progression-dc2eeb（worktree: worktree-state-tracking-da2833）※現在地はセッション開始時の git 実測値が正

## current
focus: **フェーズ 03_startup_font_settings_cleanup 起票済・実装未着手**。起動設定/フォント 3 メソッドを整理（presentation 内再編・挙動不変）。暫定仕様 02 は v1.0 でユーザー確定済。次は task_01（安全網の特性テスト）の起票・実装から。
mode: ready                      # phase 03 起票完了。task_01 から着手。

## last_action
ts: 2026-07-18T03:00:00
who: main
summary: |
  【フェーズ 03_startup_font_settings_cleanup 起票（暫定仕様 02 v1.0 確定）】
  idea_02 に着手。暫定仕様先行モードで暫定仕様 02 を起票 → reviewer「完了可・事実誤認0」＋
  codex-adversarial-reviewer の指摘3件を反映（v0.2）→ ユーザー確定5件（v1.0・実装着手可）:
    1. coerce_font_delta → theme.py の純関数（逆参照解消）
    2. 起動設定ローダ → 新規 presentation/startup_settings.py（config_service 直依存で初期化順序を壊さない）
    3. フォント設定の責務分離 = 案A（最小抽出）確定・案B（FontSettingsController）は今フェーズ見送り（初期化順序未解決）
    4. エラー通知 → on_read_error(exc) コールバック注入（真理値表: 欠損=無警告/例外=警告1回/非dict=無警告。文言不変）
    5. 未知キー全保持の契約（keymap_set_path 等を保持・既知2キーのみ正規化。後方互換の要・実コードで裏取り）
  phase 03 phase.md 起票（task_01〜05・依存順）→ reviewer「完了可」。current.md を phase03 参照へ・
  INDEX の idea_02 を着手に更新。すべてコミット済（624753e ほか）。**実装コードは未変更**。
verified:
  compile: clean                 # 起票のみ・コード無変更
  test(tests): pass 77           # 基準（未変更）
  test(tests_ui): pass 16        # 基準（未変更）
  smoke: pass

## next_action
- **task_01_characterization_test（安全網）に着手**: `/task_new` で起票 → 現行 3 メソッドの特性テストを新規追加
  （coerce 純関数 / startup ローダの真理値表〔欠損・例外・非dict・正常〕+ on_read_error 呼出/文言 /
   **未知キー保持** / フォント変更フロー〔差分なし早期 return・build_menu_bar のみ〕）。**実装は変更しない**。
  移設後も無変更で pass することが挙動不変の証明になる。
- 以降 task_02（theme.coerce_font_delta）→ task_03（startup_settings.py）→ task_04（font apply/uivars・二次レビュー併用）→
  task_05（正本反映・記録: 昇格判断・凍結・codebase_map・decisions_archive/03・idea_02 の INDEX_done 移動・refactor_check）。
- 実装は codex-implementer 既定・標準検証は verifier・コミットはメイン（agent_selection.md）。

## blockers
- なし（phase 03 起票完了・暫定仕様 v1.0 確定・git クリーン・標準検証全緑）。

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
