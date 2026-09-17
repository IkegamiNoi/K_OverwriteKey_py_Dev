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
2. `instructions/phase/current.md` を読む（**アクティブなフェーズなし**。phase 19 は完了・次フェーズは未起票）
3. 次フェーズが決まったら、暫定仕様先行なら `/spec_draft`（**暫定 18**）→ `/phase_start`（**phase 20**）。
   **凍結済の暫定仕様（`instructions/history/` の 04〜17）の条項を実装の根拠に引かない**（正本 `spec_detail/` が正）
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**phase 19 完了（正本反映・暫定仕様 17 凍結・refactor_check 推奨 → task_07 で実施・完了判定前レビューの採否反映）。次フェーズは未起票。**
直近コミット: `aced07e`（task_06 = phase 19 完了）/ `7a96eef`（task_07 リファクタ）。**main は phase 18 task_05d まで取り込み済み**
（phase 18 の残り 3 コミットと phase 19 の 10 コミットはユーザーがマージする）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 19 完了時点 = 2026-09-17**）:
compile **clean** / tests **451 実行 OK**（skip 7）/ tests_ui **427 実行 OK** / smoke **pass**。
**件数が減ったら退行を疑う**（tests_ui: phase 18 完了 413 → phase 19 完了 427）。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
実行後に **`config/config.json` の mtime が変わっていない**・worktree ルートへ **`user/` / `quarantine/` が生成されていない**ことを確認する。

**【重要】`tests_ui` の一括実行は負荷下で不定期に fail することがある**（idea_18 の Escape 配送 / 保存予約の実タイマー競合）。
**赤を見たらまず単独実行で再現するか確かめる**。

**既知の stderr ノイズ（退行ではない）**: `invalid command name "..._clear_flash_message"`（ステータスバーのタイマー）/
`ResourceWarning: unclosed file`（`tests/test_config_service.py`）。

## 次アクション（session.md.next_action より）
- **ユーザーに次の方針を確認**: ①phase 19 のコミットを main へマージ（ユーザーが実施）②次フェーズの候補（**idea_22** 縦方向の最小サイズ / その他 backlog）。
  決まったら `/spec_draft`（暫定 18）→ `/phase_start`（phase 20）。
- **運用**: タスク定義で「直さず報告」とした失敗は、メインが修正する前にユーザーへ報告する。
  リファクタの安全網は、既存テストがあれば**変異検査**（一時的に壊して落ちるか確認 → 必ず戻して md5 一致）で検出力を確かめる（phase 19 で承認）。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。

## 直前フェーズ（phase 19 = フル表示ヘッダの幅をウィンドウ最小幅に含める・完了）の要点

- **正本が正**: `features.md` §4.6「フル表示の幅配分」/ `data_schema.md` §5.4 / `codebase_map.md`（PaneLayoutController 節）。暫定仕様 16・17 は凍結。
- **用語**: 「ヘッダの要求幅」= `header_area.winfo_reqwidth()` + ウィンドウ端までの余白（**ウィンドウ幅換算**。標準フォントで約 799）。
- **ウィンドウ最小幅 = max(メインの必要幅, ヘッダの要求幅)** / 画面超過の縮小目標 = max(画面幅, ヘッダ) / **ドラッグ後の最小幅は縮小規則を通さず実表示幅から**。
- **起動時**: ヘッダに合わせて 780 より広く開く（保存しない）。**有効な保存値（切り詰め前）が適用後の幅より狭ければ、広げた幅を 1 回保存**。
- **ボタン幅**: フル表示ヘッダの切替ボタン 4 つを最大文言幅で固定（`HookController.register_hook_buttons(..., fixed_width=True)` / `SingleKeyCaptureController`）。
  フォント変更時は `App._apply_fixed_button_widths()` → `pane_layout.on_font_changed()` の順。**省略表示のボタンは固定しない**。文言は `hook_button_texts.py`（中立モジュール）。
- **tests_ui の型**: 既定幅の期待値は `max(780, pane_layout.header_window_width)`。App を作るテストは**クラス単位で `write_startup` / `save_startup` / `load_startup` を patch**し、
  破棄前に `pane_layout.cancel_window_width_save()`。書き込み回数を見るテストは保存予約の遅延定数を patch で延ばす（`WindowWidthPersistenceTest` が手本）。
- **【Tk の罠・実測】** 同じ座標でも、トリガー一覧が要求幅より広い状態で `sash_place` するとサッシュがずれる（433 → 492）/
  `header_area` の要求幅はボタンの `configure` 直後ではなく **idle 処理の後**に変わる。

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
  採用前に `ファイルパス:行` / 状態を確認する**（phase 19 起票時、メインの実測表が取得中の状態で測られていた）。
- **【傾向・実証済み】reviewer が「完了可」でも敵対的レビューで指摘が出る**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**（phase 18・19 とも正本の文言の食い違いが出た）。
  `codex-reviewer`（標準 review）は focus text を受け付けないので、観点を渡すなら `codex-adversarial-reviewer`。
- **【Codex 運用】フォワーダが切れても Codex ワーカーは生き続ける**（判別は作業ツリーの更新時刻）。
  **書き換え途中で `verifier` / `reviewer` を回さない**。`taskkill /T` を使わない。**Codex 申告のテスト結果は信用せず実測**。
- **【運用・重要】委任の実行中はメイン側でコードを編集しない**（範囲外の差分として巻き戻された実績）。
- **【config.json の書き手は 2 本】** `StartupIo.write_startup`（現在値へマージ・成功時のみ `_startup_settings` 置換・**失敗表示中はフック停止**）と
  keymap_set 保存（`save_runtime_data` が `_startup_settings` をディープコピー）。**直接 `config.json` を read-modify-write しない**。
- **【config_service の配置制約】** ConfigService 本体は `application/config_service/__init__.py`（828 行・新規ロジックを置かない）。
  **presentation から兄弟モジュールを直接 import しない**（公開面は `ConfigService` の公開 API と `contracts.py` のみ・テストが落とす）。
- **【最重要・2 度踏んだ罠】パス表記の混在**: runtime の `source_path` 3 種と `hotkey_presets_path` は config 配下なら相対。
  解決なしで `os.path` 系へ渡すと cwd 基準になり **リポジトリルートに `user/` が生成される**。
  解決は `ConfigService.resolve_config_path(path, config_root)`（`config_root` に空文字を渡さない）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**
  （失敗が「ハング」に化ける）。tests_ui の各ファイルの `setUp` に fail-fast ガードがある。
- **【tests_ui の罠】`setUpClass` で App を共有する**: dirty・フック停止カウンタ・ウィンドウ最小幅 / geometry / pane 幅 / font delta / 保存予約
  を他テストから持ち越す。**前後の変化で assert し、`addCleanup` で必ず元へ戻す**。新規テストは `patch.object` を優先。
- **【罠】worktree と main は別コピー**。main 側の絶対パスを編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。長い heredoc は壊れやすい（その場合は Write ツール）。複数行のコミットメッセージは
  `git commit -F -` + 短い heredoc。**`git grep` は追跡済みのみ検索**。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **19_full_view_header_width** / 18_full_view_resizable_panes / 17_minimize_grab_custody）。
- 未着手/保留 idea: **idea_22**（縦方向の最小サイズ）/ **idea_18**（Escape 配送依存テストの不安定）/ idea_13 / idea_11 / idea_03 / idea_09（いずれも低）/
  idea_04・idea_06（保留）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
