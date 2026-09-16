# handoff.md

過去の会話履歴は参照しないでください。
このファイルと `.claude_data/state/session.md` を起点に作業を再開してください。

## プロジェクト概要
- 言語/実行: Python（tkinter GUI）。オニオン構成（presentation / application / domain / infrastructure）。
- 対象アプリ: keyseq（キー割り当て/オーバーライドツール）。全体仕様は `instructions/common/`（`app_overview.md` / `codebase_map.md`）参照。
- **python 実行は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  依存 keyboard/pyautogui/pynput はこの `.venv` にのみ導入済み。**素の `python` / `py` は使わない**
  （`python` は Windows ストア版スタブで**ハングする**。tests_ui/smoke も落ちる）。
- **Codex は python を一切実行できない**（サンドボックス制約・回避不能）。実装委任にテスト実行を含めず、
  実測は `verifier`（またはメイン）が行う（理由は `instructions/common/rules_detail/codex_operations.md` §0）。
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。

## 再開手順
1. `.claude_data/state/session.md` を読む（最重要・最新状態）
2. `instructions/phase/current.md` を読む（**アクティブ = phase 18**）
3. `instructions/phase/18_full_view_resizable_panes/phase.md` と
   **主入力の暫定仕様 `instructions/history/16_full_view_resizable_panes.md`（v0.3・ユーザー確定済）** を読む。
   完了タスクの記録は同フォルダ `tasks/task_01〜03_*.md`（**task_03 末尾の「完了記録」に既知の残存あり**）。
   **凍結済の暫定仕様（`instructions/history/` の 04〜15）の条項を実装の根拠に引かない**
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`
   （**phase 18 進行中の判断は `decisions.md` 末尾の phase 18 節**）

## 現在の作業の 1 行サマリ
**phase 18 task_03 完了（ドラッグの可動範囲制限・中ボタン無効・希望幅と表示幅・wm minsize・フォント / 省略表示との結線）。次は task_04（保存と復元）。**
直近コミット: `458ed4a`（task_03）。**phase 17 までは main へマージ済**（phase 18 は未マージ）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 18 task_03 完了時点 = 2026-09-17**）:
compile **clean** / tests **441 実行 OK**（skip 7）/ tests_ui **368 実行 OK** / smoke **pass**。
**tests_ui は 351（phase 17）→ 357（task_02）→ 368（task_03）**。**件数が減ったら退行を疑う**。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
実行後に **`git status --short config` が空**・worktree ルートへ **`user/` / `quarantine/` が生成されていない**ことを確認する。

**【重要】`tests_ui` の一括実行は負荷下で不定期に 5 件 fail することがある**（**退行ではない**・idea_18）。
Escape 配送の取りこぼしでフック停止カウンタが 1 残り後続が連鎖する。**赤を見たらまず単独実行で再現するか確かめる**。

**既知の stderr ノイズ（退行ではない）**: `invalid command name "..._clear_flash_message"`（ステータスバーのタイマー）/
`ResourceWarning: unclosed file`（既存テスト 2 ファイル）。

## 次アクション（session.md.next_action より）
- **`/task_new` で task_04 を起票**（暫定仕様 16 §3-5・§3-6）: 起動時に `_startup_settings` の `full_view_pane_widths` を
  `parse_saved_pane_widths` で検証し、正常なら `desired` に（不正は既定幅）→ `apply_layout()`。
  `PaneLayoutController._on_desired_changed` で **`write_startup({"full_view_pane_widths": {...}})`**
  （希望幅が変わった時だけ・失敗しても desired はメモリ上で更新済み）。
  **keymap_set 保存（`save_runtime_data`）でも値が残る**テスト。**テストは実際の config を書かない**。
  → 実装は Codex が使えれば `codex-implementer`、**使えなければユーザーに `implementer` 代替の許可を取る**
  （task_02・03 はユーザー許可のうえ `implementer` で実施）→ `verifier` → `reviewer`。
- 残タスク: task_05（統合確認 + `deep-reviewer` + `codex-reviewer` + 実機目視）/ task_06（正本反映・凍結・完了処理・`/refactor_check`）。
- **【ユーザー指示】フェーズ完了判定前の `codex-adversarial-reviewer` は Codex 回復後に必ず実施**（Claude 側へ縮退して完了判定しない）。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。

## 現フェーズ（phase 18 = フル表示メイン領域の幅配分と境界線ドラッグ）の要点

**暫定仕様先行モード**（番号対応: phase 18 / 暫定 16 / decisions 18）。
**presentation + 純関数。`config.json` にキー `full_view_pane_widths` を追加（後方互換）**。

- **確定（ユーザー）**: ウィンドウ幅の変更はトリガー一覧だけが受ける / 境界線 2 本のドラッグの差分もトリガー一覧が吸収
  （**反対側の枠を押し縮めない**・中ボタン無効）/ 一覧も横に広がる・最小幅 = 中身が切れない幅（一覧 10 文字）/
  **ウィンドウ最小幅 = 両端の表示幅 + トリガー一覧の最小幅** / **ドラッグを離したとき `write_startup` で保存・
  希望幅と表示幅を分ける（表示幅が実際に変わった側だけ）** / 既定幅は現状と同じ見た目 /
  収まらない場合は最終値を計算してから一括適用。
- **構成**: 計算 = `presentation/pane_width_rules.py`（tkinter 非依存・`SASH_WIDTH=12` もここ）/
  測定・適用・イベント = `controllers/pane_layout_controller.py`（`_plan()` が `resolve_layout` を呼ぶ唯一の経路）/
  `views/full_view/full_view.py` は `self.panes = tk.PanedWindow`（生成と配置のみ）。
- **【Tk の罠・実測済】** ①`PanedWindow` 標準のサッシュドラッグは隣が最小幅に達すると**反対側まで押し縮める** →
  インスタンスバインドで `"break"` ②**表示前の `sash_place` は反対側をずらす** → 幅は `paneconfigure(width=)`、読むのは `winfo_width()`
  （`panecget("width")` はドラッグで更新されない）③**`pack` は先に詰めた部品へ要求幅を優先**する → スクロールバー・ボタン列を
  `side="right"` で一覧より先に詰める ④**Windows の Tk は `minsize(1,1)` 後も `wm_minsize()` = `(120,1)`** を返す。
- **既知の残存**: 画面幅超過で表示幅が縮んだ状態でドラッグすると、ウィンドウ最小幅が表示幅合計と一致しない場合がある
  （task_03 完了記録。task_05 の二次レビュー・実機目視で扱う）。

## 直前フェーズ（phase 17 = 最小化中の grab 預かり・完了）の要点

- ダイアログを開いたまま最小化すると復元できない欠陥を、**App の `<Unmap>` / `<Map>` で最小化の間だけ grab を預かる**形で是正
  （`presentation/modal.py` の `install_minimize_grab_custody`）。**正本 `features.md` §4.6 + `codebase_map.md` の `modal.py` 節が正**。
- **モーダルの窓口は 2 つだけ**: `modal.py` の **`grab_modal`**（**`__init__` の最後の文**・静的検査が固定）と
  `HookController.suspend_hook_for_dialog(window)`。`grab_set` / `transient` の直呼びは 0 件。
- tests_ui で `modal.py` の状態 3 つ（`_active_modals` / `_custody_window` / `_app_minimized`）は **`setUp` で patch** して独立させる。

## 運用インフラ

- **モード切替は `.claude_data/modes/`**。エージェント構成は 3 モード（`codex`〔現構成〕/ `codex_medium` / `claude_only`）。
  **`.claude/` 配下または `CLAUDE.md` を編集する前に `.claude_data/modes/README.md` を読む**。
- **template からの取り込みは `/template_pull`**（マーカー = `.claude/template_pull_state.md`）。
- **`.gitignore` は追跡ファイルだけを根拠にしない**。確認は `git check-ignore -v`。

## 注意事項・blockers
- **blockers: なし**（**Codex は利用上限中**。実装の代替はユーザー許可が必須）。
- **【裏取り】レビュー・調査・サブエージェントの「コードがこうなっている」という主張は、
  採用前に `ファイルパス:行` を実測確認する**（自分が書く文書も同じ）。
- **【傾向・実証済み】reviewer が「完了可」でも敵対的レビューで指摘が出る**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**（phase 18 はユーザー指示で Codex 回復待ち）。
  `codex-reviewer`（標準 review）は focus text を受け付けないので、観点を渡すなら `codex-adversarial-reviewer`。
- **【Codex 運用】フォワーダが切れても Codex ワーカーは生き続ける**（判別は作業ツリーの更新時刻）。
  **書き換え途中で `verifier` / `reviewer` を回さない**。`taskkill /T` を使わない。**Codex 申告のテスト結果は信用せず実測**。
- **【運用・重要】委任の実行中はメイン側でコードを編集しない**（範囲外の差分として巻き戻された実績）。
- **【config.json の書き手は 2 本】** `StartupIo.write_startup`（現在値へマージ・成功時のみ `_startup_settings` 置換）と
  keymap_set 保存（`save_runtime_data` が `_startup_settings` をディープコピー）。**どちらもメモリ上の `_startup_settings` が土台**。
  **直接 `config.json` を read-modify-write しない**（次の保存で無言消滅する）。
- **【config_service の配置制約】** ConfigService 本体は `application/config_service/__init__.py`（828 行・新規ロジックを置かない）。
  **presentation から兄弟モジュールを直接 import しない**（公開面は `ConfigService` の公開 API と `contracts.py` のみ・テストが落とす）。
- **【最重要・2 度踏んだ罠】パス表記の混在**: runtime の `source_path` 3 種と `hotkey_presets_path` は config 配下なら相対。
  解決なしで `os.path` 系へ渡すと cwd 基準になり **リポジトリルートに `user/` が生成される**。
  解決は `ConfigService.resolve_config_path(path, config_root)`（`config_root` に空文字を渡さない）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**
  （失敗が「ハング」に化ける）。tests_ui の各ファイルの `setUp` に fail-fast ガードがある。
- **【tests_ui の罠】`setUpClass` で App を共有する**: dirty・フック停止カウンタ・**ウィンドウ最小幅 / geometry / pane 幅 / font delta**
  を他テストから持ち越す。**前後の変化で assert し、`addCleanup` で必ず元へ戻す**。**`write_startup` は patch して config を書かない**。
  App を破棄する前に `update()` を回す。新規テストは `patch.object` を優先。
- **【罠】`event_generate("<Escape>")` は非表示ウィンドウでは配送されない**（`deiconify` + `focus_force` を先に。負荷下では取りこぼす）。
- **【罠】worktree と main は別コピー**。main 側の絶対パスを編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。長い heredoc は壊れやすい（その場合は Write ツール）。複数行のコミットメッセージは
  `git commit -F -` + 短い heredoc。**`git grep` は追跡済みのみ検索**。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **17_minimize_grab_custody** / 16_dialog_transient_parent / 15_dialog_teardown_on_close）。
- 未着手/保留 idea: **idea_18**（Escape 配送依存テストの不安定）/ idea_13 / idea_11 / idea_03 / idea_09（いずれも低）/
  idea_04・idea_06（保留）。**idea_20 は phase 18 で着手中**。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
