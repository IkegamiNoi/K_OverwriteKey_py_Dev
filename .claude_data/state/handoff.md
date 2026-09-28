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
2. `instructions/phase/current.md` を読む（**アクティブなフェーズ = phase 40**〔呼び出し・`instructions/phase/40_sequence_call/phase.md`・主入力 = 暫定 29〕。
   次採番 = phase 41 / 暫定 30 / decisions 41 / 提案書 17）
3. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
4. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。
   **凍結済の暫定仕様（`instructions/history/` の 04〜28。**28 の §9 と、未凍結の 29 は例外**）の条項を実装の根拠に引かない**（正本 `spec_detail/` が正）

## 現在の作業の 1 行サマリ
**phase 40 進行中（暫定 29 v0.7）。task_09e（ダイアログ廃止・ステータスバーの通知・戻す / 先頭への 2 回押し・待機中に止めたら次の送る行へ）まで完了。ユーザーの実機目視待ち。**
直近コミット: `2c8f1cc`（task_09e）/ `6df8eda`（暫定 29 v0.7）/ `a4de795`（task_09d）/ `d0bf813`（task_09c）。ブランチ `claude/trigger-input-during-call-d13202`。
**main は phase 37 まで取り込み済み**（phase 38〜40 はユーザーがマージする）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 40 task_09e 時点 = 2026-09-29**）:
compile **clean** / tests **995 実行 OK**（skip 7）/ tests_ui **634 実行 OK** / smoke **pass**。
**件数が減ったら退行を疑う**（tests: phase 39 完了 906 → 995 / tests_ui: 616 → 634。tests_ui は task_09e でダイアログのテストを削除して 635 → 634）。
**`tests_ui` と smoke を並行実行しない**（フックの取り合いで 13 件落ちる。逐次で実行する）。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
実行後に **`config/config.json` の mtime が変わっていない**・worktree ルートへ **`user/` / `quarantine/` /
`keymap_set_history*.json` が生成されていない**ことを確認する。

**【flaky は phase 32 で対処済】** `get_hook_pause_count()` が `1 != 0` / `resume_hook_after_dialog` が 0 回の赤（idea_33）は、
破棄後の確認を `wait_for_hook_pause_count` へ置き換えて解消（負荷下で 9 モジュール × 6 回 + tests_ui 全体 × 1 回とも赤 0 件）。
**再び出たら**、`update()` を伴わないテスト冒頭のカウント確認（`decisions_archive/32`「残るリスク」）を疑い、その冒頭にヘルパ（0）を入れる。
それでも**赤くなったら まず再実行・単体実行で切り分ける**（1 回で退行と決めない）。

**既知の stderr ノイズ（退行ではない）**: `invalid command name "..._clear_flash_message"`（ステータスバーのタイマー）/
`ResourceWarning: unclosed file`（`tests/test_config_service.py`）。

## 次アクション（session.md.next_action より）
- **ユーザーの実機目視（task_09e）**: ①待機中に一時停止 / フック停止 → 位置が次の送る行・再開でそこから（単発の待機中に他の連続実行・フック停止でも同じ）
  ②一時停止中に他の連続実行を開始 → ダイアログなしで捨てて通知 ③キーマップの切替 / 削除でも捨てて通知（削除は既存の確認だけ・完了の通知が破棄の通知で置き換わる点も確認）
  ④戻す / 先頭へで対象が一時停止中 → 1 回目は通知だけ・続けてもう一度で実行・間に他の押下で 1 回目に戻る。
- 目視 OK → task_10（正本反映〔暫定 29 §11 + v0.6/v0.7 の §4.7・待機中の停止の規定改訂〕・暫定 29 凍結・decisions_archive/40・current.md・`/refactor_check`〔call_wait / call_run_to_end の重複・runner 548 行〕）。
- 申し送り（任意）: `call_run_to_end.py` `_run_to_end_call_matches` のトークン照合は一時停止 1 回分のずれのみ吸収。
- **main へのマージはユーザーが行う**（ブランチ `claude/trigger-input-during-call-d13202`・phase 38〜40）。

## 直前フェーズ（phase 39 = 停止）の要点

**JSON スキーマ変更あり（op `stop`）**（暫定仕様先行・暫定 28 v0.6 凍結・§9 は phase 40 の起票元）。判断は `decisions_archive/39`、正本は `features.md` §4.2.8 ほか。

- 連続実行は停止の行で間隔なしに終える（保留をその場で反映・停止の後も先行処理）/ 単発は読み飛ばす / その連続実行でまだ送っていない間の停止は読み飛ばす（印 `_run_to_end_sent`）。
- phase 40 の呼び出しは、単発 = `PendingStep.call`（`CallWaitMixin`）/ 連続 = `_run_to_end_call`（`CallRunToEndMixin`）/ 文脈の進め方 = `application/call_context.py`（送信しない純粋な処理）。

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
- **【最重要・phase 28・29 で実証】Tk の挙動は推測せず probe で実測する**（`.venv` python の小スクリプトで数分）:
  ①未マップ時の `focus_set` は外から検出できない ②Escape はフォーカス窓へ再配送される
  ③同一 widget では `<Escape>` が `<KeyPress>` より優先して単独発火する（`add="+"` は登録順に両方発火）
  ④Windows Tk はキーリピート中に KeyRelease を挟まない（`PostMessageW` で WM_KEYDOWN の repeat ビットを送って確認）。
  **レビューだけでは前提の誤りは見つからない**。**ただし素の Tk の probe で成立しても実 App で崩れることがある**（phase 29:
  即時 `focus_set` は素の 3 段 transient 連鎖では無害だったが、実 App の 3 段ネストで外側の窓を戻さなかった）。**実 App で probe するか、既存の統合テストで確かめる**。**フォーカス・前面化は実操作でしか再現しないことがある**（phase 29 の測定 4）。
- **【傾向・phase 28 で実証】正本へ昇格する文言は既存条項と突き合わせる**（「保存せずに閉じる」が既存の
  「閉じても一覧は保存される」と矛盾した）。**条項の主語（すべての〜）は対象集合を `grep` で数えてから昇格する**。
- **【傾向・phase 28 で実証】新しい状態分岐を足したら「押しっぱなし」「状態が残ったままの再開」を実機で見る**
  （自動テスト・レビュー・実機目視 A2 の単発押しでは退行 L3 が見えず、ユーザーの押しっぱなしで判明した）。
- **【罠・phase 28 task_05d で実証】「上限つきで N 回再試行」は実時間の待ちが無いと意味がない**。
  再試行は実時間の期限（deadline）で切り、待機中も `app.update()` を回す。
- **【傾向・実証済み】reviewer が「採用」でも敵対的 / 上位レビューで指摘が出る**（phase 30 でも reviewer 2 回「指摘なし」→ Codex が high）。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**。暫定仕様の改訂も `codex-adversarial-reviewer` を通す。
  `codex-reviewer`（標準 review）は focus text を受け付けないので、観点を渡すなら `codex-adversarial-reviewer`。
- **【罠・phase 40 で実証】Codex は仕様書の例示の値（`f5` 等）を文字どおり埋め込むことがある**。タスク定義に「例示」と明記し、`grep` で埋め込みを確かめる。
- **【罠・phase 40 で実証】Codex はテストの期待値を仕様と逆に書くことがある**（単発で呼び出しが終わると呼び出し元の次の行まで送る前提 = 誤り。呼び出しは押下を消費する・`tests/test_sequence_runner_call.py` の test_01）。
  連続実行の待機中の停止では停止の行の規則（`stop_ends_run`）を、file_line・呼び出しの途中には待機の規則を当てない。**実測で差し戻す**。
- **【運用・phase 40】ダイアログは操作中のアプリからフォーカスを奪うため、実行中の知らせはステータスバー（`notify_message`）にする**（暫定 29 v0.7）。
- **【罠・phase 40】呼び出しの最初のステップは `after(0)` の予約**。テストでは `run_one` が要る。未使用のカウンターは辞書にキーが無い（`counters.get(name, 0)`）。
- **【罠・phase 38 で 4 回実証】「戻す履歴が 1 段」をテストするときは状態が変わるシーケンスにする**（file_line 1 行だけでは位置もカウンターも変わらず
  `commit_step` が積まない＝仕様どおり）。**subTest でループ前に `self.runner.method` を束縛しない**（`setUp()` で作り直した runner に届かない）。
- **【傾向・phase 28 で実証】テストの「検出力」は変異検査で確かめる**（その仕様を壊すと**追加テストだけ**落ちるか）。
  `verifier` に頼むときは「**`git checkout --` / `git restore` / `git stash` を使わない**（未コミットの実装ごと巻き戻る）」を明示する。
- **【罠・phase 27 で実証】テストに `focus_force()` のような「通してしまう前処理」があると、実使用の不具合を隠す**。
- **【罠】フック再開は `<Destroy>` から `after(0)` で予約される**（`presentation/controllers/hook_controller.py:57`）。
  **`destroy()` の直後に `get_hook_pause_count()` を数えると 1 のまま**。**`app.update()` 1 回では負荷下で取りこぼす**ため、
  破棄後の解除は `tests_ui/hook_resume_wait.py` の `wait_for_hook_pause_count` で待ってから確かめる（phase 32）。
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
- **【ダイアログ追加時・phase 33】静的検査は発見ベースで列挙不要**。ただし ①config_io に `grab_modal` を足したら
  `test_nested_modal_grab.py` の期待件数の辞書へ ②常に親の停止中にだけ開く子は `NESTED_CHILD_DIALOGS`（(ファイル名, クラス名)）へ
  ③T2（destroy override を残す）なら `T2_DIALOG_FILES` へ追加する（いずれも `tests_ui/test_dialog_teardown_flows.py` 等）。
- **【罠】worktree と main は別コピー**。main 側の絶対パスを編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。長い heredoc・`sed` の複数行追記（`a\`）は壊れやすい（**壊れたら Write / Edit ツールを使う**）。
  **sed の区切り文字が置換文字列に含まれると壊れる**（`/` を含むなら `|` を使う）。複数行のコミットメッセージは `git commit -F -`。
  **heredoc で書いた行は LF になる**（CRLF のファイルへ差し込んだら `sed -i 's/\r$//; s/$/\r/'` で揃える）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: 39_sequence_stop / 38_file_line_async_read / 37_sequence_control_actions）。
- 着手中 idea: なし（phase 40 は暫定 26 §13 由来）。未着手/保留 idea: **idea_37**（カウンター条件分岐）/ idea_36（共通トリガー層・現時点で不要）/ **idea_23**（押す / 離すアクション）/
  idea_29〜idea_31 / idea_13 / idea_11 / idea_03 / idea_09（いずれも低）/ idea_04・idea_06（保留）。
  別タスク化候補に「同型スケルトンの共通化」（単純な `bind("<Escape>", destroy)` 等）/ M4（`_apply_initial_focus` の位置・保留）/
  `tests_ui/test_minimize_grab_custody.py`（603 行）の分割 / 「キーがあれば coerce_label」5 箇所（提案書 12 見送り）/
  `_run_to_end_step` の停止 2 行 3 箇所（phase 31・refactor_check 不要）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
