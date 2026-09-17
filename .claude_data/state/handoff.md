# handoff.md

過去の会話履歴は参照しないでください。
このファイルと `.claude_data/state/session.md` を起点に作業を再開してください。

## プロジェクト概要
- 言語/実行: Python（tkinter GUI）。オニオン構成（presentation / application / domain / infrastructure）。
- 対象アプリ: keyseq（キー割り当て/オーバーライドツール）。全体仕様は `instructions/common/`（`app_overview.md` / `codebase_map.md`）参照。
- **python 実行は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  依存 keyboard/pyautogui/pynput はこの `.venv` にのみ導入済み。**素の `python` / `python3` / `py` は使わない**
  （Windows ストア版スタブで**ハングする**。tests_ui/smoke も落ちる）。
- **Codex は python を一切実行できない**（サンドボックス制約・回避不能）。実装委任にテスト実行を含めず、
  実測は `verifier`（またはメイン）が行う（理由は `instructions/common/rules_detail/codex_operations.md` §0）。
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。

## 再開手順
1. `.claude_data/state/session.md` を読む（最重要・最新状態）
2. `instructions/phase/current.md` を読む（**アクティブなフェーズなし**。phase 20 は完了・次フェーズは未起票）
3. 次フェーズが決まったら、暫定仕様先行なら `/spec_draft`（**暫定 19**）→ `/phase_start`（**phase 21**）。
   **凍結済の暫定仕様（`instructions/history/` の 04〜18）の条項を実装の根拠に引かない**（正本 `spec_detail/` が正）
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**phase 20 完了（正本反映・暫定仕様 18 凍結・refactor_check 不要・完了判定前レビューの採否反映〔task_04b〕）。次フェーズは未起票。**
直近コミット: `699fa14`（task_04 = phase 20 完了）/ `ba31614`（task_04b）。**main は phase 18 task_05d まで取り込み済み**
（phase 18 の残り・phase 19・phase 20〔`f39ad74`〜`699fa14`〕はユーザーがマージする）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 20 完了時点 = 2026-09-18**）:
compile **clean** / tests **451 実行 OK**（skip 7）/ tests_ui **438 実行 OK** / smoke **pass**。
**件数が減ったら退行を疑う**（tests_ui: phase 19 完了 427 → phase 20 完了 438）。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
実行後に **`config/config.json` の mtime が変わっていない**・worktree ルートへ **`user/` / `quarantine/` が生成されていない**ことを確認する。

**【重要】`tests_ui` の一括実行は負荷下で不定期に fail することがある**（idea_18 の Escape 配送 / 保存予約の実タイマー競合）。
**赤を見たらまず単独実行で再現するか確かめる**。

**既知の stderr ノイズ（退行ではない）**: `invalid command name "..._clear_flash_message"`（ステータスバーのタイマー）/
`ResourceWarning: unclosed file`（`tests/test_config_service.py`）。

## 次アクション（session.md.next_action より）
- **ユーザーに次の方針を確認**: ①phase 18 残り・19・20 のコミットを main へマージ（ユーザーが実施）②次フェーズの候補（backlog / 別タスク化候補）。
  決まったら `/spec_draft`（暫定 19）→ `/phase_start`（phase 21）。
- **運用**: タスク定義で「直さず報告」とした失敗は、メインが修正する前にユーザーへ報告する。
  修正・リファクタの検出力は**変異検査**（一時的に壊して落ちるか確認 → 必ず戻して差分一致）で確かめる（phase 19・20 で実施）。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。

## 直前フェーズ（phase 20 = フル表示ウィンドウの縦方向の最小サイズ・完了）の要点

- **正本が正**: `features.md` §4.6「フル表示の幅配分」の「最小の高さ」項 / `codebase_map.md`（PaneLayoutController 節・FullView 節・App の View 切替）。暫定仕様 18 は凍結。
- **一覧の `height` = 6 / 6 / 9 が最小の高さの基準**（既定の半分。表示行数は伸びた分で決まる）。**最小の高さ = フル表示中のウィンドウの要求高さ**（一時メッセージは 1 行分）。
  実測: −3 / 標準 / ＋3 = 654 / 729 / 844（全フォントで出力シーケンスのボタン列が支配）。
- **測る順序**: 両端の `paneconfigure` の後（`tk.PanedWindow` の要求高さは paneconfigure まで古い）。`show_full_view` は表示内容の更新後に末尾で `on_full_view_shown`。
- **【Tk の罠・実測】** `minsize` の引き上げで Tk が広げた高さは geometry の記憶に残らず、最小が下がると元の高さ（820 等）へ縮む →
  `apply_layout` は normal 状態で「最小未満」または「最小が下がる」とき `geometry(現在の幅x高さ)` で確定させる（最大化の解除で広がった高さも同じ）。
- **pack の罠（実測）**: 足りないときは後から pack した部品から削られ、`expand=True` の部品は要求高さより縮まない。
- **tests_ui の型**: `tests_ui/test_full_view_min_height.py`（11 本）。`window_min_height` も退避・復元し、`_restore` で最大化を解除する。
  「切れていない」は `winfo_y()+winfo_height()` と `winfo_height() >= winfo_reqheight()` の実測で判定（`wm_minsize` の値比較だけにしない）。

## 運用インフラ

- **モード切替は `.claude_data/modes/`**。エージェント構成は 3 モード（`codex`〔現構成〕/ `codex_medium` / `claude_only`）。
  **`.claude/` 配下または `CLAUDE.md` を編集する前に `.claude_data/modes/README.md` を読む**。
- **template からの取り込みは `/template_pull`**（マーカー = `.claude/template_pull_state.md`）。
- **`.gitignore` は追跡ファイルだけを根拠にしない**。確認は `git check-ignore -v`。

## 注意事項・blockers
- **blockers: なし**（Codex 利用可。Codex 不可時の実装代替はユーザー許可が必須）。
- **【罠】Bash ツールで `python3` / `python` を呼ばない**（Windows ストア版スタブが stdin 待ちでハングし、同じコマンド内の後続も実行されない）。
  スクリプトを直接走らせるときは `PYTHONPATH=.` を付ける。
- **【裏取り】レビュー・調査・サブエージェントの「コードがこうなっている」という主張、および自分の実測は、
  採用前に `ファイルパス:行` / 状態を確認する**（phase 20 ではレビュー指摘の再現をメインがスクリプトで実測してから採否を聞いた）。
- **【傾向・実証済み】reviewer が「採用」でも敵対的レビューで指摘が出る**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**（phase 18・19 は正本の文言、phase 20 は最大化解除の経路が出た）。
  `codex-reviewer`（標準 review）は focus text を受け付けないので、観点を渡すなら `codex-adversarial-reviewer`。
- **【Codex 運用】フォワーダが切れても Codex ワーカーは生き続ける**（判別は作業ツリーの更新時刻）。
  **書き換え途中で `verifier` / `reviewer` を回さない**。`taskkill /T` を使わない。**Codex 申告のテスト結果は信用せず実測**。
- **【運用・重要】委任の実行中はメイン側でコードを編集しない**（文書のみ・対象ファイルが重ならない場合は可）。
- **【config.json の書き手は 2 本】** `StartupIo.write_startup`（現在値へマージ・成功時のみ `_startup_settings` 置換・**失敗表示中はフック停止**）と
  keymap_set 保存（`save_runtime_data` が `_startup_settings` をディープコピー）。**直接 `config.json` を read-modify-write しない**。
- **【config_service の配置制約】** ConfigService 本体は `application/config_service/__init__.py`（828 行・新規ロジックを置かない）。
  **presentation から兄弟モジュールを直接 import しない**（公開面は `ConfigService` の公開 API と `contracts.py` のみ・テストが落とす）。
- **【最重要・2 度踏んだ罠】パス表記の混在**: runtime の `source_path` 3 種と `hotkey_presets_path` は config 配下なら相対。
  解決なしで `os.path` 系へ渡すと cwd 基準になり **リポジトリルートに `user/` が生成される**。
  解決は `ConfigService.resolve_config_path(path, config_root)`（`config_root` に空文字を渡さない）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**
  （失敗が「ハング」に化ける）。tests_ui の各ファイルの `setUp` に fail-fast ガードがある。
- **【tests_ui の罠】`setUpClass` で App を共有する**: dirty・フック停止カウンタ・ウィンドウ最小サイズ / geometry / 最大化状態 / pane 幅 / font delta / 保存予約
  を他テストから持ち越す。**前後の変化で assert し、`addCleanup` で必ず元へ戻す**。新規テストは `patch.object` を優先。
- **【罠】App に View の部品を属性で生やさない**（phase 01 で解消済。phase 20 でも一時メッセージのラベルは測定側で textvariable から探した）。
- **【罠】worktree と main は別コピー**。main 側の絶対パスを編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。長い heredoc は壊れやすい（その場合は Write ツール）。**sed の区切りに `#` を使うとパターン中の `##` で壊れる**。
  複数行のコミットメッセージは `git commit -F -` + 短い heredoc。**`git grep` は追跡済みのみ検索**。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **20_full_view_min_height** / 19_full_view_header_width / 18_full_view_resizable_panes）。
- 未着手/保留 idea: **idea_18**（Escape 配送依存テストの不安定）/ idea_13 / idea_11 / idea_03 / idea_09（いずれも低）/ idea_04・idea_06（保留）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
