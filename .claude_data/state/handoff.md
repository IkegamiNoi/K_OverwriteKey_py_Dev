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
   （**v0.3**・ユーザー確定済 2026-07-29）。フェーズ中は正本 `spec_detail/` を直接改訂しない（**task_10** で昇格＋凍結）。
   タスク定義は `instructions/phase/06_child_file_save_dialog/tasks/`（**task_01〜09 は起票・完了済**）。
   受入条件の充足状況は `instructions/phase/06_child_file_save_dialog/integration_result.md` が正。
   番号対応: **α=phase05/暫定04〔完了〕 / β=phase06/暫定05〔進行中〕 / γ=phase07/暫定06 / プリセット=phase08/暫定07**。
5. session.md.next_action から作業を再開する

## 現在の作業の 1 行サマリ
**Phase β task_07〜09（実機目視フィードバックの実装）まで完了。残るは実機目視（ユーザー実施）→ task_10（正本反映）**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（task_09 完了時・verifier）: compile **clean** / tests **136** / tests_ui **116** / smoke **pass**。

## 次アクション（session.md.next_action より）
- **実機目視をユーザーへ依頼する**（残る唯一の未完了項目）。起動は worktree ルートで
  `../../../.venv/Scripts/python.exe main.py`。確認するのは **(a) 2026-07-29 フィードバック①③④⑤の解消**
  （②は仕様どおりで修正なし）+ **(b) task_06 定義「対象範囲 4」の 9 項目の退行が無いこと**。
  - **①** トリガー一覧を別名保存 → 一覧が再表示されない（再計算は保存完了メッセージで事後通知）。
    再計算先が既存ファイル（単独所有以外）のときだけ上書き確認が出る
  - **③** `config/user/keymap_sets/` へ保存して「デフォルト外」確認が出ない
  - **④** 未保存の出力シーケンスが `config/user/sequences/` へ保存される
  - **⑤** dirty な子 12 行以上・対象名 40 文字・パス 160 文字で、横にはみ出さない / 縦スクロール /
    ドラッグでリサイズ / 省略部にツールチップで全文
  - **③④は VS Code の ▶ 実行（小文字ドライブ）で発生していたため、目視も同じ起動方法で行う**
  - 結果は `integration_result.md` §3 へ記録する
- 目視 OK 後: **task_10（`finalize_records`）を `/task_new` で起票**。正本反映で**必ず明記**する項目は
  `SHARE_NEW` / 非 dirty 子の SKIP 規則 / SKIP した子の索引規則 / 依存確認ダイアログと既定ボタン /
  SKIP 子の dirty 保持 / `data_schema.md` §5.4 の「trigger_set は全セット共通」記述の更新 /
  §5.6 のフォールバック名の経路差（一括 = `default` / 個別 = `trigger_set.json`）/
  個別「トリガー一覧を保存」が全 sequence を書く点と §8 の関係 / `INTERNAL_TRIGGER_SET_SOURCE_PATH` /
  **v0.3 追加分**（A: 再表示しない / A2: 再計算先の上書き確認 / B: canonical identity / C: ダイアログ要件 /
  変更なし保存でも親・起動設定・未作成の子は書かれ完了ダイアログも出る）。
  併せて暫定仕様 05 の凍結・`decisions_archive/06` 作成・`current.md` 完了記載・
  `backlog/INDEX.md`（idea_05 クローズ・idea_06 / idea_07 の条件更新）・`/refactor_check`。

## 現フェーズ（Phase β）の要点 — 設計の正は暫定仕様 05（v0.3）
- keymap_set の「保存」を、**変更のある子ファイルごとに 保存 / 別名保存 / 保存しない を選べる確認ダイアログ**へ
  置き換える。**親 keymap_set.json は常に保存**（ラジオ対象外）。変更のある子が無ければダイアログを出さない
  （ただし親・起動設定・未作成の子は書かれ、保存完了ダイアログは出る）。
- **依存関係の扱い**: 親 keymap_set は**問わない**（「保存」操作自体が明示のため無確認保存）/
  **trigger_set は問う** → OK 押下時に確認ダイアログ（保存 / 別名保存 / 選び直す）。
  一覧のラジオは静的に無効化しない。`SavePlanError` は UI から到達しない内部不変条件の番人。
- **壊しやすい不変条件**（レビューで実際に破れていた箇所。変更時は必ず確認する）:
  ① 未知・別の上位に属す → **別名保存が既定**（一覧の既定 + 依存確認の**既定ボタン**の両方で担保）
  ② 共有判定は **`target_path`（上書きする相手のファイル）の refs** を読む（runtime の refs ではない）
  ③ ~~提示した保存先と実際に書く先を一致させる（再解決のたび一覧再表示）~~ → **v0.3-A で緩和・task_08 で廃止**。
  代わりに **v0.3-A2**（再計算で実体パスが変わった「保存」行のうち、新パスに既存ファイルがあり
  `SHARE_SOLE` 以外の行だけ、行単位の小ダイアログで上書き確認）が安全弁。
  **一覧へ戻る経路は依存確認の「選び直す」だけ**（自動再表示を復活させない）
  ④ `dirty_tracker.trigger_set_source_path` と `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致**
  （入口は `dirty_state` の `set_trigger_set_source_path` / `sync_trigger_set_source_path_from_data` の 2 本のみ。
  直接代入を復活させない）
  ⑤ 子の `_parent_refs` は**保存先ファイルの集合 + 現在の上位**（保存元 in-memory の旧参照元は足さない）
  ⑥ アクションの優先順位は `child_save_plan.build_save_plan` の 1 箇所（一覧の選択 > confirmed > 非 dirty 既定）
  ⑦ 保存計画の**決定は presentation・実行は application** / **行ごとの粒度**（選んだ子だけ書く）
  ⑧ パスの同一性判定は **`ConfigService.canonical_path` / `is_path_within` を必ず使う**（task_07）。
  `commonpath` の素の文字列一致・`startswith` の前方一致を復活させない。
  **canonical identity は比較専用**で、保存値（`_parent_refs` / 索引 / 起動設定）・戻り値・表示へ混入させない
  （保存表記は config_root 内=相対 / 外=絶対のまま）
- **主要モジュール**: `keyseq/application/save_plan.py`（`SavePlan` / `ChildSaveEntry` / `SavePlanError`）/
  `config_service`（`save_runtime_data(..., save_plan=...)`・`resolve_child_save_targets` ・
  `find_dependency_blocked_sequences` ・ `read_parent_refs` ・ `canonical_path` / `is_path_within`）/
  `config_io/child_save_rows.py`（行モデル）/ `child_save_plan.py`（選択 → 計画の純変換）/
  `child_save_dialog.py`（UI・スクロール/省略/ツールチップ・`confirm_recalculated_overwrite`）/
  `keymap_set_io._collect_child_save_plan`（戻り値は `tuple[SavePlan | None, str]`）。

## 注意事項・blockers
- **blockers: なし**。
- **【Codex 運用】フォワーダが最終出力を返さないまま完了通知だけ来る / タイムアウトしてジョブだけ走り続ける**
  ことがある。**差分 0 件で返ることもある**（ジョブ未起動 or 早期リターン）→ その場合は `SendMessage` で
  同じフォワーダを再開し、ジョブ状態の確認と最終出力の回収を依頼する。差分が入っている場合は
  worktree のファイル mtime が停滞するまで待ってから verifier を回す。
  **Codex 申告のテスト結果は信用せず必ず verifier で実測**。詳細は
  `instructions/common/rules_detail/codex_operations.md`。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。編集は必ず worktree ルート配下で。
- **【罠】Bash ツールは Git Bash**。PowerShell の here-string（`@'...'@`）はコミットメッセージに `@` が混入する。
  複数行は heredoc（`git commit -F - <<'EOF'`）を使う。
- **【罠】`git grep` は追跡済みのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。行数計測は `wc -l`。
- **【傾向】テストの期待値誤りが混ざる**（Codex 実装物で実測済み: `slugify_file_stem` は大文字小文字を変換しない /
  `source_path` は config_root 相対なので読み出し時に root と結合が要る / `_parent_refs` を差し込む相手は
  妥当な JSON でないと `load_json` が落ちる）。fail が出たら**まず production か test かを切り分ける**。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。出力の作法は
  `.claude/rules/output_style.md`。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近: 05_keymap_set_new_and_default_dir / 04_config_io_controller_split / 03_startup_font_settings_cleanup）。
- 未着手/保留 idea: idea_03（hotkey 保存正規化・低）/ idea_04（FontSettingsController・保留）/ idea_07（参照元掃除・β後）/
  idea_08（個別プリセット・07後）/ idea_09（レガシー保存パス・α の積み残し）。idea_05→β 内包（着手中）/ idea_06→β 達成見込み。
- **β で保留にしたレビュー指摘**（task_10 or 別 idea で扱う）: sequence の共有判定の「現在の上位」が
  計画後の trigger_set 保存先である点 / 事前検証で `os.makedirs` の副作用がある点 /
  `_ask_save_as_path` が `choose_save_path_with_collision` を使っていない点。
- **`/refactor_check` へ申し送り**: `config_service.py` 1644 行 / `keymap_set_io._collect_child_save_plan` 約 116 行で
  再計算処理が 2 箇所に重複 / `_ellipsize*` は limit が極端に小さいと破綻し得る（実利用は 24・56 固定）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
