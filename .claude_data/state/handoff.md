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
2. `instructions/phase/current.md` を読む（**アクティブなフェーズなし**。次採番 = phase 29 / 暫定 23 / decisions 29 / 提案書 12）
3. 次フェーズを始めるなら `current.md`「次フェーズ候補」→ `instructions/backlog/INDEX.md` の該当 idea を読み、
   ユーザーが選んだら `/phase_start`
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。
   **凍結済の暫定仕様（`instructions/history/` の 04〜22）の条項を実装の根拠に引かない**（正本 `spec_detail/` が正）

## 現在の作業の 1 行サマリ
**phase 28 完了（task_01〜07 + 05b〜05e）。次は backlog の idea から次フェーズを選んで `/phase_start`。**
直近コミット: `8728a81`（task_07 = `bind_escape_close` へ集約・phase 28 完了）/ `ad79e84`（task_06 = 正本反映・暫定 22 を v0.7 で凍結）/
`5d83e49`（task_05e = 押しっぱなし Esc で閉じない）。
**main は phase 18 task_05d まで取り込み済み**（phase 18 の残り・19〜28 はユーザーがマージする）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 28 task_07 完了時点 = 2026-09-23**）:
compile **clean** / tests **556 実行 OK**（skip 7）/ tests_ui **509 実行 OK**（skip 0）/ smoke **pass**。
**件数が減ったら退行を疑う**（tests: 556 で不変 / tests_ui: phase 27 完了 484 → phase 28 完了 509）。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
実行後に **`config/config.json` の mtime が変わっていない**・worktree ルートへ **`user/` / `quarantine/` /
`keymap_set_history*.json` が生成されていない**ことを確認する。

**【既知の flaky】`tests_ui` 一括でまれに `get_hook_pause_count()` が `1 != 0`**（例: `test_quarantine_manage_flow` の
`test_escape_and_window_close_keep_action_empty`。単体では pass）= [idea_33](../../instructions/backlog/idea_33_hook_resume_after_idle_flaky_test.md)
（`<Destroy>` → `after(0)` のフック再開の取りこぼし。**Escape 配送ではない**＝`send_escape` の診断は出ない）。
**task_01 のフォーカス変更は原因候補に残る**。赤くなっても**まず再実行・交互実行で切り分ける**（1 回で退行と決めない）。

**既知の stderr ノイズ（退行ではない）**: `invalid command name "..._clear_flash_message"`（ステータスバーのタイマー）/
`ResourceWarning: unclosed file`（`tests/test_config_service.py`）。

## 次アクション（session.md.next_action より）
- **次フェーズの選定**: `current.md`「次フェーズ候補」= **idea_34**（最小化復帰後にフォーカスが最内のモーダルへ戻らない・
  **仕様変更あり**〔`features.md` §4.6〕）/ **idea_33**（フック再開 flaky・テストのみ）/ **idea_23**（キーを押す / 離すアクション）。
  ユーザーが選んだら `/phase_start`。
- **main へのマージはユーザーが行う**。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。

## 直前フェーズ（phase 28 = ダイアログの初期キーボードフォーカス）の要点

**正本が正** = `features.md` §4.6「モーダルダイアログの作法」+ `codebase_map.md` の `modal.py` 節。
判断は `decisions_archive/28_dialog_keyboard_focus.md`（暫定仕様 22 は v0.7 で凍結）。

- **初期フォーカスは `grab_modal(window, parent=None, *, focus=None)` の責務**（明示引数・省略時は窓自身・`grab_set()` の直後に
  `focus_set`・`focus_force` / `lift` は呼ばない）。**入力先を持つダイアログは `focus=` で渡す**（`__init__` で別途 `focus_set` しない）。
  推測型（`focus_lastfor()` / `after_idle`）は未マップ時の保留で**明示指定を奪う**と実測で反証。
- **モーダル全 15 経路が Escape で閉じる**（× と同じ結果。`io_dialogs.py` のみ `on_cancel`）。
  **Esc に別用途がある 3 ダイアログ**（Action = 記録 / Trigger・KeymapEdit = 取得）は `dialogs/escape_close.py` の
  **`bind_escape_close(window, *, is_busy, stop)`**: 判定順 = 記録・取得中（停止して印）→ 印（閉じない）→ 閉じる。
  印は `<KeyRelease-Escape>` で消す＝**押しっぱなしのリピートでは閉じない**（Windows Tk はリピート中に KeyRelease を挟まない）。
- **新しいダイアログを足すとき**: `grab_modal(..., focus=入力先)` を `__init__` の最後の文に / Escape は × と同じ閉じ方へ結線 /
  Esc に別用途があるなら `bind_escape_close`。
- **テストで Escape を送るときは `tests_ui/escape_delivery.py` の `send_escape`**（閉じることの検査）/
  **`acquire_focus`**（閉じないことの検査）。`focus_force()` + `event_generate` の直書きは使わない。
  **初期フォーカスの欠落を検出するのは `test_dialog_initial_focus.py` だけ**（ヘルパ自身が `focus_force` するため）。
- **フォーカスの戻り先（閉じた後・最小化復帰後）は規定しない**。最小化復帰後はメイン窓に残る＝idea_34。

## 運用インフラ

- **モード切替は `.claude_data/modes/`**。エージェント構成は 3 モード（`codex`〔現構成〕/ `codex_medium` / `claude_only`）。
  **`.claude/` 配下または `CLAUDE.md` を編集する前に `.claude_data/modes/README.md` を読む**。
- **template からの取り込みは `/template_pull`**（マーカー = `.claude/template_pull_state.md`）。
- **`.gitignore` は追跡ファイルだけを根拠にしない**。確認は `git check-ignore -v`。

## 注意事項・blockers
- **blockers: なし**（Codex 利用可。Codex 不可時の実装代替はユーザー許可が必須）。
- **【罠】Bash ツールで `python3` / `python` を呼ばない**（Windows ストア版スタブが stdin 待ちでハングし、同じコマンド内の後続も実行されない）。
  スクリプトを直接走らせるときは `PYTHONPATH=.` を付ける。
- **【裏取り】レビュー・調査・サブエージェントの「コードがこうなっている」という主張は、採用前に `ファイルパス:行` を実測確認する**。
- **【最重要・phase 28 で 4 度実証】Tk の挙動は推測せず probe で実測する**（`.venv` python の小スクリプトで数分）:
  ①未マップ時の `focus_set` は外から検出できない ②Escape はフォーカス窓へ再配送される
  ③同一 widget では `<Escape>` が `<KeyPress>` より優先して単独発火する（`add="+"` は登録順に両方発火）
  ④Windows Tk はキーリピート中に KeyRelease を挟まない（`PostMessageW` で WM_KEYDOWN の repeat ビットを送って確認）。
  **レビューだけでは前提の誤りは見つからない**。
- **【傾向・phase 28 で実証】正本へ昇格する文言は既存条項と突き合わせる**（「保存せずに閉じる」が既存の
  「閉じても一覧は保存される」と矛盾した）。**条項の主語（すべての〜）は対象集合を `grep` で数えてから昇格する**。
- **【傾向・phase 28 で実証】新しい状態分岐を足したら「押しっぱなし」「状態が残ったままの再開」を実機で見る**
  （自動テスト・レビュー・実機目視 A2 の単発押しでは退行 L3 が見えず、ユーザーの押しっぱなしで判明した）。
- **【罠・phase 28 task_05d で実証】「上限つきで N 回再試行」は実時間の待ちが無いと意味がない**。
  再試行は実時間の期限（deadline）で切り、待機中も `app.update()` を回す。
- **【傾向・実証済み】reviewer が「採用」でも敵対的 / 上位レビューで指摘が出る**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**。暫定仕様の改訂も `codex-adversarial-reviewer` を通す。
  `codex-reviewer`（標準 review）は focus text を受け付けないので、観点を渡すなら `codex-adversarial-reviewer`。
- **【傾向・phase 28 で実証】テストの「検出力」は変異検査で確かめる**（その仕様を壊すと**追加テストだけ**落ちるか）。
  `verifier` に頼むときは「**`git checkout --` / `git restore` / `git stash` を使わない**（未コミットの実装ごと巻き戻る）」を明示する。
- **【罠・phase 27 で実証】テストに `focus_force()` のような「通してしまう前処理」があると、実使用の不具合を隠す**。
- **【罠】フック再開は `<Destroy>` から `after(0)` で予約される**（`presentation/controllers/hook_controller.py:57`）。
  **`destroy()` の直後に `get_hook_pause_count()` を数えると 1 のまま**。数える前に `app.update()` を挟む（→ idea_33）。
- **【罠・phase 27 で実証】`tests_ui` は実 `config/` を汚し得る**（`App()` を作るだけで起動時処理が走る）。
  **App を作る新規テストは `tests_ui/test_keymap_set_history_flow.py:17-34` の ExitStack 手法を踏襲する**。
- **【Codex 運用】フォワーダが切れても Codex ワーカーは生き続ける**（判別は作業ツリーの更新時刻）。
  **書き換え途中で `verifier` / `reviewer` を回さない**。`taskkill /T` を使わない。**Codex 申告のテスト結果は信用せず実測**。
  **Codex が書いた行は LF で入ることがある**（CRLF のファイルへ混在）。
- **【運用・重要】委任の実行中はメイン側でコードを編集しない**（文書のみ・対象ファイルが重ならない場合は可）。
- **【config.json の書き手は 2 本】** `StartupIo.write_startup`（現在値へマージ）と keymap_set 保存。
  **直接 `config.json` を read-modify-write しない**。**`keymap_set_path` だけは保存で据え置く**（phase 26）。
- **【config_service の配置制約】** ConfigService 本体は `application/config_service/__init__.py`（新規ロジックを置かない）。
  **presentation から兄弟モジュールを直接 import しない**。モジュールを増やしたら
  `tests/test_config_service_contracts.py` の `INTERNAL_MODULE_NAMES` を更新する。
- **【最重要・2 度踏んだ罠】パス表記の混在**: 解決は `ConfigService.resolve_config_path(path, config_root)`、
  比較は `ConfigService.canonical_path`。**パスは `coerce_label`（trim のみ）/ キー名・id は `coerce_key_name`**。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
- **【tests_ui の罠】`setUpClass` で App を共有する**。前後の変化で assert し、`addCleanup` で必ず元へ戻す。
- **【罠】ダイアログを増やしたら 3 つの列挙を更新する**: `DIALOG_FILES` / `T2_DIALOG_FILES`
  （`tests_ui/test_dialog_teardown_flows.py`）と **`dialog_classes`（`tests_ui/test_nested_modal_grab.py:262`）**。
- **【罠】worktree と main は別コピー**。main 側の絶対パスを編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。長い heredoc・`sed` の複数行追記（`a\`）は壊れやすい（**壊れたら Write / Edit ツールを使う**）。
  **sed の区切り文字が置換文字列に含まれると壊れる**（`/` を含むなら `|` を使う）。複数行のコミットメッセージは `git commit -F -`。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: 28_dialog_keyboard_focus / 27_keymap_set_load_history / 26_startup_entry_preservation）。
- 未着手/保留 idea: **idea_34**（最小化復帰後のフォーカス）/ **idea_33**（フック再開 flaky）/ **idea_23**（押す / 離すアクション）/
  idea_31・idea_32 / idea_13 / idea_11 / idea_03 / idea_09（いずれも低）/ idea_04・idea_06（保留）。
  別タスク化候補に「同型スケルトンの共通化」（単純な `bind("<Escape>", destroy)` 等）と M4（`_apply_initial_focus` の位置・保留）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
