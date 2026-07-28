# handoff.md

過去の会話履歴は参照しないでください。
このファイルと `.claude_data/state/session.md` を起点に作業を再開してください。

## プロジェクト概要
- 言語/実行: Python（tkinter GUI）。オニオン構成（presentation / application / domain / infrastructure）。
- 対象アプリ: keyseq（キー割り当て/オーバーライドツール）。全体仕様は `instructions/common/`（`app_overview.md` / `codebase_map.md`）参照。
- **python 実行は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  依存 keyboard/pyautogui/pynput はこの `.venv` にのみ導入済み。グローバル `py` は使わない（tests_ui/smoke が落ちる）。
- **Codex は python を一切実行できない**（サンドボックス制約・回避不能）。実装委任にテスト実行を含めず、
  実測は `verifier` が行う（理由は `instructions/common/rules_detail/codex_operations.md` §0）。

## 再開手順
1. `.claude_data/state/session.md` を読む（最重要・最新状態）
2. `.claude_data/state/decisions.md` を読む（判断履歴。完了フェーズは「アーカイブ索引」→ `decisions_archive/<phase>.md`）
3. CLAUDE.md → `instructions/phase/current.md`（**現在: `instructions/phase/06_child_file_save_dialog/phase.md` = Phase β**）→
   `.claude/rules/` の順に必要分を読む
4. **このフェーズの設計の正は暫定仕様 [05_child_file_save_dialog.md](../../instructions/history/05_child_file_save_dialog.md)**
   （v0.2・ユーザー確定済）。フェーズ中は正本 `spec_detail/` を直接改訂しない（task_07 で昇格＋凍結）。
   タスク定義は `instructions/phase/06_child_file_save_dialog/tasks/`（task_01〜04 は起票・完了済）。
   番号対応: **α=phase05/暫定04〔完了〕 / β=phase06/暫定05〔進行中〕 / γ=phase07/暫定06 / プリセット=phase08/暫定07**。
5. session.md.next_action から作業を再開する

## 現在の作業の 1 行サマリ
**Phase β task_04（dirty な子の収集・保存先解決・共有状況判定・既定アクション）完了。次は task_05（保存確認ダイアログ UI と保存経路への挟み込み）の `/task_new` 起票**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（task_04 完了時・verifier）: compile **clean** / tests **119** / tests_ui **86** / smoke **pass**。

## 次アクション（session.md.next_action より）
- **task_05（`save_dialog_ui`）を `/task_new` で起票**（暫定仕様 05 §3）。
  ① 保存確認ダイアログ（列 = 種別 / 対象名 / 保存先パス / 共有状況 / **ラジオ 3 択**。既定は task_04 の
  `default_action`）② 別名保存行の保存先を `asksaveasfilename` で決める ③ 選択を **`SavePlan` へ変換**して
  `save_runtime_data` へ渡す ④ `keymap_set_io.save_keymap_set_to` への挟み込み（**dirty な子が無ければ出さない**）。
- **ユーザー確認待ちの設計判断が 1 件**: 依存関係違反（パスが変わる子があるのに親を「保存しない」）を
  **UI で選べなくする**（起票時の既定案）か、`SavePlanError` をユーザー向けメッセージへ変換して差し戻すか。
- 起票後: `codex-implementer` へ委任（テスト実行は依頼しない）→ **書き込み停止を確認してから** `verifier` 実測 →
  `reviewer` → `/save_state` + `/task_commit`。

## 現フェーズ（Phase β）の要点 — 設計の正は暫定仕様 05
- keymap_set の「保存」を、**変更のある子ファイルごとに 保存 / 別名保存 / 保存しない を選べる確認ダイアログ**へ
  置き換える。**親 keymap_set.json は常に保存**（ラジオ対象外）。変更のある子が無ければダイアログを出さない。
- **task_01〜04 で入った土台**（task_05 はこれを組み合わせるだけ）:
  - `_parent_refs`（子JSON の参照元）。**未知 = `None` / 既知ゼロ = `[]` の区別を維持**
  - trigger_set の source_path 接続（idea_05 解消）+ 既定命名の **keymap_set stem 基準化**
  - `keyseq/application/save_plan.py`（`SavePlan` / `ChildSaveEntry` / `SavePlanError`）と
    `save_runtime_data(..., save_plan=...)`。**事前検証 → 子 → 親 → startup** の順で実行（失敗時は旧索引維持）
  - `config_io/child_save_rows.py` の `collect_child_save_rows(...)` が行モデル `ChildSaveRow` を返す
    （kind / key / display_name / target_path / share_state / share_text / default_action）
- **実装で後退しやすい点**: ① 未知・別の上位に属す → **別名保存が既定**（安全側）/ ② 判定は
  **`target_path`（上書きする相手のファイル）の refs** を読む（runtime の refs ではない）/
  ③ 保存計画の**決定は presentation・実行は application**（application に判断を持ち込まない）/
  ④ **行ごとの粒度**（選んだ子だけ書く）。
- **暫定仕様に対して足した判断（task_07 で正本へ明記する）**: `SHARE_NEW`（保存先ファイルが存在しない →
  既定は保存）/ skip の索引規則（既存ありは旧パス維持・既存なしは索引に載せない）/
  `INTERNAL_TRIGGER_SET_SOURCE_PATH`（runtime 内部キー）。

## 注意事項・blockers
- **blockers: なし**。
- **【Codex 運用】フォワーダが最終出力を返さないまま完了通知だけ来ることがある**。その場合は worktree の
  ファイル mtime が停滞するまで待ってから `verifier` を回す（早すぎると**実装途中の fail** を掴む。2026-07-28 実測）。
  ジョブが詰まった / ハング検知 / state 手修復は `instructions/common/rules_detail/codex_operations.md`。
  **Codex 申告のテスト結果は信用せず必ず verifier で実測**。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。編集は必ず worktree ルート配下で。
- **【罠】`git grep` は追跡済みのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。行数計測は `wc -l`。
- **【傾向】既存の特性テストが旧挙動を固定している**。β は挙動変更フェーズのため、各タスク起票時に
  対象を固定しているテストを先に grep で洗い出し、更新対象としてタスク定義に明記する。
  また**モック署名が実装の引数追加に追随していないと tests_ui がモーダルでハングする**（task_01 で実測）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  出力の作法は `.claude/rules/output_style.md`。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近: 05_keymap_set_new_and_default_dir / 04_config_io_controller_split / 03_startup_font_settings_cleanup）。
- 未着手/保留 idea: idea_03（hotkey 保存正規化・低）/ idea_04（FontSettingsController・保留）/ idea_07（参照元掃除・β後）/
  idea_08（個別プリセット・07後）/ idea_09（レガシー保存パス・α の積み残し）。idea_05→β 内包（着手中）/ idea_06→β 達成見込み。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
