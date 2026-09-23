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
2. `instructions/phase/current.md` を読む（**アクティブ = phase 29**。次採番 = phase 30 / 暫定 24 / decisions 30 / 提案書 12）
3. `instructions/phase/29_focus_restore_after_minimize/phase.md` と、
   **主入力の暫定仕様 `instructions/history/23_focus_restore_after_minimize.md`（v0.4・ユーザー確定済・未凍結）**を読む。
   タスク定義は `instructions/phase/29_focus_restore_after_minimize/tasks/` 配下
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`
   （phase 29 の判断は `decisions.md` 本体の末尾節）。
   **凍結済の暫定仕様（`instructions/history/` の 04〜22）の条項を実装の根拠に引かない**（正本 `spec_detail/` が正）。
   **23 だけは未凍結で、phase 29 の確定設計として有効**

## 現在の作業の 1 行サマリ
**phase 29 は task_01 完了（最小化復元時に `after_idle` で最内モーダルの最後のフォーカス先へ `focus_set`）。次は task_02（統合確認 + 実機目視 §6-6 ①〜⑦）。**
直近コミット: `0b3e6c5`（phase 29 task_01）/ `d8a250f`（phase 29 起票）/ `8728a81`（phase 28 完了）。
**main は phase 18 task_05d まで取り込み済み**（phase 18 の残り・19〜29 はユーザーがマージする）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 29 task_01 完了時点 = 2026-09-23**）:
compile **clean** / tests **556 実行 OK**（skip 7）/ tests_ui **519 実行 OK**（skip 0・3 回連続）/ smoke **pass**。
**件数が減ったら退行を疑う**（tests: 556 で不変 / tests_ui: phase 28 完了 509 → phase 29 task_01 519）。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
実行後に **`config/config.json` の mtime が変わっていない**・worktree ルートへ **`user/` / `quarantine/` /
`keymap_set_history*.json` が生成されていない**ことを確認する。

**【既知の flaky】`tests_ui` 一括でまれに落ちる**: ①`get_hook_pause_count()` が `1 != 0`（例: `test_quarantine_manage_flow`。
= [idea_33](../../instructions/backlog/idea_33_hook_resume_after_idle_flaky_test.md)・Escape 配送ではない）
②`test_dialog_escape_binding` がまとめて落ちる回が 1 度あった（phase 29 task_01 中・以後の一括 3 回で再発せず）。
**赤くなっても まず再実行・単体実行で切り分ける**（1 回で退行と決めない）。

**既知の stderr ノイズ（退行ではない）**: `invalid command name "..._clear_flash_message"`（ステータスバーのタイマー）/
`ResourceWarning: unclosed file`（`tests/test_config_service.py`）。

## 次アクション（session.md.next_action より）
- **task_02 を `/task_new` で起票**: 統合確認（`verifier`〔標準検証 + 実 Tk の到達検査の要否判断〕+ `deep-reviewer` + `codex-reviewer`）+
  **実機目視（ユーザー）= 暫定仕様 23 §6-6 ①〜⑦**。起動 = `..\..\..\.venv\Scripts\python.exe -m keyseq`
  ①Win+D → タスクバー復元 → クリックせず Escape で閉じる ②3 段ネスト（アクション編集 → プリセットマネージャ → 追加・編集）で
  3 窓とも表示・Escape で 1 つずつ閉じる ③Win+D 2 回目 ④Alt+Tab で最小化中の窓を選ぶ ⑤他アプリ入力中に Win+D 2 回 →
  他アプリの入力が奪われない ⑥最小化せず Alt+Tab で戻る → 記録のみ ⑦ラベル欄で入力中に最小化 → 復元後の文字がラベル欄へ。
- その後 task_03（正本反映 = `features.md` §4.6 の最小化の条項を API 単位へ言い換え + フォーカス復帰の条項 + 「閉じた後は規定しない」への分割 /
  `codebase_map.md` の `modal.py` 節〔`:312-313` の「推測型は不採用」を初期フォーカスに限定〕・暫定仕様 23 の凍結・`decisions_archive/29`・
  `current.md`・idea_34 を INDEX_done へ・`/refactor_check`）。
- **main へのマージはユーザーが行う**。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。

## 現在のフェーズ（phase 29 = 最小化から復元した後のキーボードフォーカス）の要点

**設計は暫定仕様 23 が正**（v0.4・未凍結）。フェーズ中は正本 `spec_detail/` を直接改訂しない（昇格は task_03）。

- 実装 = `keyseq/presentation/modal.py`: `return_custody`（App の `<Map>`）は **grab の返却を即時**に行い、`finally` で
  **`app.after_idle(_restore_modal_focus, app)`** を予約する。`_restore_modal_focus` は**予約実行時に**
  「`app.grab_current()` が台帳 `_active_modals` に同一性で含まれ・生存・表示中」の窓の `focus_lastfor() or window` へ `focus_set`。
  `deiconify` / `lift` / `focus_force` は呼ばない。
- **`<Map>` 内で即時に `focus_set` してはならない**: 実 App の 3 段ネストで**一番外側の窓が非表示のまま戻らない**（既存 a2・a3 が検出。
  素の Tk の probe では再現しなかった）。
- **最小化中に `grab_modal` した窓**は `_opened_while_minimized` に記録し、**その回の復元では戻さない**（初期フォーカス要求を優先）。
  記録は復帰処理の最後で空にする（次の復元からは通常どおり）。
- 固定テスト = `tests_ui/test_minimize_grab_custody.py`（a1〜a13 = 既存の grab 預かり / b1〜b6・b8〜b11 = フォーカス復帰）。
  **期待値はダイアログごとの具体 widget**（`ActionDialog.value_entry` / `action_label_entry`）。
  **テストで未マップの widget へ `focus_set` すると、OS フォーカスの無い環境では保留のまま残り `focus_lastfor()` が窓自身を返す**
  （b11 で踏んだ。先に `update()` でマップしてから要求する）。
- 確定事項: 閉じた後のフォーカスは規定しない / 最小化を伴わない再アクティブ化（Alt+Tab で最小化していない窓へ戻る）は対象外。
- 直前の完了フェーズ = phase 28（ダイアログの初期キーボードフォーカス。正本 `features.md` §4.6「モーダルダイアログの作法」+
  `codebase_map.md` の `modal.py` 節・判断は `decisions_archive/28`）。要点 = 初期フォーカスは `grab_modal(..., focus=)` /
  モーダル全 15 経路が Escape で閉じる / Esc の別用途がある 3 ダイアログは `dialogs/escape_close.py` の `bind_escape_close` /
  テストで Escape を送るときは `tests_ui/escape_delivery.py` の `send_escape` / `acquire_focus`。

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
  **レビューだけでは前提の誤りは見つからない**。**ただし素の Tk の probe で成立しても実 App で崩れることがある**（phase 29:
  即時 `focus_set` は素の 3 段 transient 連鎖では無害だったが、実 App の 3 段ネストで外側の窓を戻さなかった）。**実 App で probe するか、既存の統合テストで確かめる**。
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
  （直近 3 件: 28_dialog_keyboard_focus / 27_keymap_set_load_history / 26_startup_entry_preservation。phase 29 の判断は進行中につき `decisions.md` 本体）。
- 着手中 idea: **idea_34**（phase 29）。未着手/保留 idea: **idea_33**（フック再開 flaky）/ **idea_23**（押す / 離すアクション）/
  idea_31・idea_32 / idea_13 / idea_11 / idea_03 / idea_09（いずれも低）/ idea_04・idea_06（保留）。
  別タスク化候補に「同型スケルトンの共通化」（単純な `bind("<Escape>", destroy)` 等）と M4（`_apply_initial_focus` の位置・保留）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
