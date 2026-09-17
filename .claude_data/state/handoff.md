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
2. `instructions/phase/current.md` を読む（**アクティブ = phase 21 `21_extended_key_send`**・直接改訂モード）
3. `instructions/phase/21_extended_key_send/phase.md` と `tasks/task_02_integration_and_close.md` を読む（残りは実機目視 → 記録 → 完了処理）
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。
   **凍結済の暫定仕様（`instructions/history/` の 04〜18）の条項を実装の根拠に引かない**（正本 `spec_detail/` が正）

## 現在の作業の 1 行サマリ
**phase 21 task_02 進行中（統合確認 pass・二次レビュー採否済・採用分を task_02b で反映済）。残り = ユーザーの実機目視 → 記録とフェーズ完了処理。**
直近コミット: `fc3d1c4`（task_02b）/ `3e43aea`（task_01）/ `9428fea`（phase 21 起票）。**main は phase 18 task_05d まで取り込み済み**
（phase 18 の残り・phase 19・phase 20・phase 21 はユーザーがマージする）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 21 task_02b 時点 = 2026-09-19**）:
compile **clean** / tests **460 実行 OK**（skip 7）/ tests_ui **438 実行 OK**（task_02b 前・infrastructure のみの変更）/ smoke **pass**。
**件数が減ったら退行を疑う**（tests: phase 20 完了 451 → phase 21 task_02b 460）。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
実行後に **`config/config.json` の mtime が変わっていない**・worktree ルートへ **`user/` / `quarantine/` が生成されていない**ことを確認する。

**【重要】`tests_ui` の一括実行は負荷下で不定期に fail することがある**（idea_18 の Escape 配送 / 保存予約の実タイマー競合）。
**赤を見たらまず単独実行で再現するか確かめる**。

**既知の stderr ノイズ（退行ではない）**: `invalid command name "..._clear_flash_message"`（ステータスバーのタイマー）/
`ResourceWarning: unclosed file`（`tests/test_config_service.py`）。

## 次アクション（session.md.next_action より）
- **ユーザーの実機目視を待つ**（task_02 定義の 5 項目 + 追加 2 項目）:
  ①hotkey `shift+right` ×数回 → 範囲選択 → `ctrl+c` ②`ctrl+shift+end` / `ctrl+shift+home` ③キーマップで `right` / `end` に割り当て、**物理 Shift** と併用
  ④通常キーの hotkey・text・マウスが従来どおり ⑤フックの停止 / トグル・通常トリガーの抑止が従来どおり
  ⑥**拡張キーを自分のトリガー / キーマップ元 / 停止・トグルキーに割り当てて同じキーを送る**（自己起動・自己停止しないか。今回の変更の新リスク）
  ⑦`windows` / `menu` / 右 Alt / `num lock` / `print screen` を 1 回ずつ。
- 目視 OK なら: `instructions/phase/21_extended_key_send/integration_result.md` を記録 → `decisions_archive/21_extended_key_send.md` + `decisions.md` 索引（本体の phase 21 節を移動）→
  `current.md` 完了記載（次採番 **phase 22 / 暫定 19 / decisions 22**）→ **`/refactor_check`**（PHASE_BASE = `9428fea`）→ 完了判定前レビュー（`deep-reviewer` + `codex-adversarial-reviewer`）→ 採否 → コミット。
- **運用**: `verifier` に変異検査を頼むときは「**`git checkout --` / `git restore` / `git stash` を使わない**（未コミットの実装ごと巻き戻る。実際に 1 度発生し、差分の再適用で復旧）。ファイルのコピーで退避・復元する」を明示する。
  タスク定義で「直さず報告」とした失敗は、メインが修正する前にユーザーへ報告する。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。

## 進行中フェーズ（phase 21 = 拡張キーを拡張キーとして送る）の要点

- **正本**: `spec_detail/key_input.md` **§7.7「キーの送信」**（新設・文言はユーザー確定済）+ `codebase_map.md`「キーの送信」節。直接改訂モード（暫定仕様なし）。
- **原因（実機で確定）**: `keyboard` は `keybd_event` に KEYEVENTF_EXTENDEDKEY を付けない（`_winkeyboard.py` の `_send_event`）。`right` は scan 77 = テンキー 6 と同じ →
  Shift 併用で範囲選択にならない。**押す / 離すアクションを足しても直らない**（同じ送信経路）。
- **実装**: `infrastructure/input_gateway.py` に拡張キー表 18 件（名前 → vk / scan）+ `_resolve_extended_key`（`keyboard.normalize_name` で別名解決）+ `_send_extended_event`（`ctypes.windll.user32.keybd_event`）。
  `press_key` / `release_key` は表に載る名前だけ拡張送信。`send_hotkey` は**拡張キーを含まなければ従来どおり `keyboard.send`**、含む場合は記述順に押し逆順に離す（例外時も押したキーを逆順に離す）。
- **新しい前提（重要）**: raw `keybd_event` は `keyboard` の `is_replaying` を通らないため、**自分が送った拡張キーがアプリのフックに届く**（防護は send guard 1 枚。挙動は不変の想定・実機⑥で確認）。
- **テスト**: `tests/test_input_gateway_send.py`（9 本。送信をモックし順序 / vk / scan / 押す・離すを検証。1 本は `ctypes` ごと差し替えてフラグ合成を検証）。
- **保留（記録のみ）**: 途中失敗で先行キーが実際に出る / `,` 区切りの多段 hotkey（現状アプリの検証で到達不能）/ 離す側の例外が残らない / `requirements.txt` の `keyboard` が非固定。
- **関連 idea**: [idea_23](../../instructions/backlog/idea_23_key_press_release_actions.md)（押す / 離すアクション・未着手・優先度低）。

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
  採用前に `ファイルパス:行` / 状態を確認する**（phase 20・21 とも、指摘の再現をメインがスクリプトで実測してから採否を聞いた）。
- **【傾向・実証済み】reviewer が「採用」でも敵対的 / 上位レビューで指摘が出る**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**。
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
- **【罠】App に View の部品を属性で生やさない**（phase 01 で解消済）。
- **【罠】worktree と main は別コピー**。main 側の絶対パスを編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。長い heredoc は壊れやすい（その場合は Write ツール）。**sed の区切りに `#` を使うとパターン中の `##` で壊れる**。
  複数行のコミットメッセージは `git commit -F -` + 短い heredoc。**`git grep` は追跡済みのみ検索**。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: 20_full_view_min_height / 19_full_view_header_width / 18_full_view_resizable_panes）。
- 未着手/保留 idea: **idea_23**（押す / 離すアクション）/ **idea_18**（Escape 配送依存テストの不安定）/ idea_13 / idea_11 / idea_03 / idea_09（いずれも低）/ idea_04・idea_06（保留）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
