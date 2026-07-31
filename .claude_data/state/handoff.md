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
   （**v0.4**・ユーザー確定済 2026-07-30）。フェーズ中は正本 `spec_detail/` を直接改訂しない（**task_10** で昇格＋凍結）。
   タスク定義は `instructions/phase/06_child_file_save_dialog/tasks/`
   （**task_01〜09・11〜13 は完了。残るは task_10 = 正本反映のみ**）。
   受入条件の充足状況は `instructions/phase/06_child_file_save_dialog/integration_result.md` が正。
   番号対応: **α=phase05/暫定04〔完了〕 / β=phase06/暫定05〔進行中〕 / γ=phase07/暫定06 / プリセット=phase08/暫定07**。
5. session.md.next_action から作業を再開する（**実機目視の結果待ち**。目視の確認項目は session.md が正）

## 現在の作業の 1 行サマリ
**Phase β は task_13 まで完了（実装は全て完了）。残りは実機目視（ユーザー実施）→ task_10（正本反映）**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（task_13 完了時・verifier）: compile **clean** / tests **138** / tests_ui **136（完走）** / smoke **pass**。

## 次アクション（session.md.next_action より）
- **実機目視をユーザーへ依頼する**（Phase β で残る唯一の未完了項目。実装タスクは task_01〜09・11〜13 で全て完了）。
  起動は `../../../.venv/Scripts/python.exe main.py`。**③④の確認は VS Code の ▶ 実行〔小文字ドライブ〕で**。
  結果は `instructions/phase/06_child_file_save_dialog/integration_result.md` §3 へ記録する。
- 目視 OK 後 → **task_10（`finalize_records` = 正本反映）**。
  目視の確認項目と task_10 の必須記載は **session.md.next_action が正**。

## 現フェーズ（Phase β）の要点 — 設計の正は暫定仕様 05（v0.4）
- keymap_set の「保存」を、**変更のある子ファイルごとに 保存 / 別名保存 / 保存しない を選べる確認ダイアログ**へ
  置き換える。**親 keymap_set.json は常に保存**（ラジオ対象外）。変更のある子が無ければダイアログを出さない
  （ただし親・起動設定・未作成の子は書かれ、保存完了ダイアログは出る）。
- **依存関係の扱い（v0.4-D/E）**: 子のパスが変わると上位（trigger_set）の保存が必須。
  **上位の共有状況が「単独」「新規作成」なら確認を出さず自動保存**（完了メッセージで事後通知）。
  それ以外は **4 択**（保存 / 別名保存 / **保存しない** / キャンセル・**既定ボタン=別名保存**）。
  「保存しない」= **deferred index**（索引は旧パス維持・上位を**強制 dirty 化**して次回保存で追随。
  application の必須依存チェックは `SavePlan.allow_deferred_index` が True のときだけ通す）。
- **壊しやすい不変条件**（レビューで実際に破れていた箇所。変更時は必ず確認する）:
  ① 未知・別の上位に属す → **別名保存が既定**（一覧の既定 + 依存確認の**既定ボタン**の両方で担保）
  ② 共有判定は **`target_path`（上書きする相手のファイル）の refs** を読む（runtime の refs ではない）
  ③ 一覧の再表示はしない（v0.3-A）。安全弁は **v0.3-A2**（再計算で実体パスが変わった「保存」行のうち、
  新パスに既存ファイルがあり `SHARE_SOLE` 以外の行だけ行単位で上書き確認）＝ **v0.4-F で維持**。
  **一覧へ戻る経路は依存確認の「キャンセル」だけ**
  ④ `dirty_tracker.trigger_set_source_path` と `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致**
  （入口は `dirty_state` の `set_trigger_set_source_path` / `sync_trigger_set_source_path_from_data` /
  **`reset_trigger_set_state`（task_13 で追加。`data` 置換時のリセット専用）**の 3 本のみ。直接代入を復活させない。
  リセット後は `data` からキーを pop して `new_default_data()` と同じ「キー無し」の形にする）
  ⑤ 子の `_parent_refs` は**保存先ファイルの集合 + 現在の上位**（保存元 in-memory の旧参照元は足さない）
  ⑥ アクションの優先順位は `child_save_plan.build_save_plan` の 1 箇所（一覧の選択 > confirmed > 非 dirty 既定）
  ⑦ 保存計画の**決定は presentation・実行は application** / **行ごとの粒度**（選んだ子だけ書く）。
  `allow_deferred_index` も presentation が立て、application は検証の緩和にのみ使う
  ⑧ パスの同一性判定は **`ConfigService.canonical_path` / `is_path_within` を必ず使う**（task_07）。
  `commonpath` の素の文字列一致・`startswith` の前方一致を復活させない。
  **canonical identity は比較専用**で、保存値（`_parent_refs` / 索引 / 起動設定）・戻り値・表示へ混入させない
- **主要モジュール**: `keyseq/application/save_plan.py`（`SavePlan`〔`allow_deferred_index`〕/ `ChildSaveEntry` /
  `SavePlanError`）/ `config_service`（`save_runtime_data(..., save_plan=...)`・`resolve_child_save_targets`・
  `find_dependency_blocked_sequences`・`read_parent_refs`・`canonical_path` / `is_path_within`）/
  `config_io/child_save_rows.py`（行モデル・共有状況）/ `child_save_plan.py`（選択 → 計画の純変換）/
  `child_save_dialog.py`（一覧 UI〔可変列・px 省略・ツールチップ〕+ 4 択の依存確認 + A2）/
  `keymap_set_io._collect_child_save_plan`（提示条件の判定と deferred index の配線）。

## 注意事項・blockers
- **blockers: なし**。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  テスト内の `AssertionError` も `save_keymap_set_to` の広い `except Exception` に捕まるため、
  **失敗が「ハング」に化けて原因が見えなくなる**（2026-07-30 に 3 回発生）。対策として tests_ui の 3 ファイル
  （`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup`）の `setUp` に **fail-fast ガード**を入れてある:
  `messagebox.showerror` / `confirm_recalculated_overwrite`(A2) / `confirm_trigger_set_dependency` を
  「呼ばれたら `AssertionError`」に patch。**期待するテストは個別 patch で上書きし内容をアサーションする**。
  新しいモーダルを増やすときは同じガードを足すこと。
- **【教訓】ハングしたら `messagebox` / `filedialog` を全遮断して単独実行する**と真因が一発で出る
  （`python -c` で差し替えて `unittest.main(module=..., argv=[...])`。2026-07-30 実測で 0.6 秒）。
- **【Codex 運用】フォワーダが最終出力を返さないまま完了通知だけ来る / タイムアウトしてジョブだけ走り続ける**
  ことがある。**差分 0 件で返ることもある**（ジョブ未起動 or 早期リターン）→ その場合は `SendMessage` で
  同じフォワーダを再開し、ジョブ状態の確認と最終出力の回収を依頼する（2026-07-29・30 とも回収できた）。
  差分が入っている場合は worktree のファイル mtime が停滞するまで待ってから verifier を回す。
  **Codex 申告のテスト結果は信用せず必ず verifier で実測**。詳細は
  `instructions/common/rules_detail/codex_operations.md`。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。編集は必ず worktree ルート配下で。
- **【罠】Bash ツールは Git Bash**。PowerShell の here-string（`@'...'@`）はコミットメッセージに `@` が混入する。
  複数行は heredoc（`git commit -F - <<'EOF'`）を使う。
- **【罠】`git grep` は追跡済みのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。行数計測は `wc -l`。
- **【傾向】reviewer が「完了可」でも実測で落ちることがある**（task_12 で実際に発生）。
  **判定はテストの実測が優先**。fail が出たら**まず production か test かを切り分ける**
  （既知の期待値誤り: `slugify_file_stem` は大文字小文字を変換しない / `source_path` は config_root 相対 /
  `_parent_refs` の差し込み先は妥当な JSON でないと `load_json` が落ちる）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。出力の作法は
  `.claude/rules/output_style.md`。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近: 05_keymap_set_new_and_default_dir / 04_config_io_controller_split / 03_startup_font_settings_cleanup）。
- 未着手/保留 idea: idea_03（hotkey 保存正規化・低）/ idea_04（FontSettingsController・保留）/ idea_07（参照元掃除・β後）/
  idea_08（個別プリセット・07後）/ idea_09（レガシー保存パス・α の積み残し）。
  idea_05→β が内包（**実装完了。task_10 で INDEX_done へ移す**）/ idea_06→β 達成見込み。
- **β で保留にしたレビュー指摘**（task_10 or 別 idea で扱う）: sequence の共有判定の「現在の上位」が
  計画後の trigger_set 保存先である点 / 事前検証で `os.makedirs` の副作用がある点 /
  `_ask_save_as_path` が `choose_save_path_with_collision` を使っていない点。
- **`/refactor_check` へ申し送り**: `config_service.py` 1644 行 / `child_save_dialog.py` 324 行 /
  `keymap_set_io._collect_child_save_plan` が長く再計算処理が 2 箇所に重複 /
  `_add_text_cell` の戻り値が素の dict（型注釈なし）/ deferred index のテストが keymap_set・起動設定を
  存在確認レベルでしか見ていない。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
