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
- **ユーザーへの提示（応答・報告・文書）は日本語で行う**（2026-09-16 指示・2026-10-05 再確認）。

## 再開手順
1. `.claude_data/state/session.md` を読む（最重要・最新状態）
2. `instructions/phase/current.md` を読む（**アクティブなフェーズ = phase 47**〔`47_action_dialog_layout_cleanup`・直接改訂モード〕）。
   次採番 = phase 48 / 暫定 33 / decisions 48 / 提案書 20。
3. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
4. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。
   **凍結済の暫定仕様（`instructions/history/` の 04〜32）の条項を実装の根拠に引かない**（正本 `spec_detail/` が正）

## 現在の作業の 1 行サマリ
**phase 47 task_01 実装完了（presentation）。ユーザーの実機目視待ち → OK なら task_02（正本反映）。**
ブランチ `claude/physical-device-verification-d3c460`（phase 46 task_03 の目視以降・phase 47 も同じ）。task_03 までは `claude/back-sequence-trigger-limit-49fff0`（**main への取り込み状況は git で確認**・マージはユーザー）。
ユーザーはフェーズ内のタスクの連続実行を許可済み（スペックフラグ・フォールバック・実機目視では止まる）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 47 task_01 = 2026-10-06**）:
compile **clean** / tests **1308 実行 OK**（skip 7）/ tests_ui **837 実行**（全体で 836 OK・残り 1 件はテスト修正後に該当 41 件 OK） / smoke **pass**。
**件数が減ったら退行を疑う**（tests: phase 45 完了 1292 → 1308 / tests_ui: 824 → 837）。
**`tests_ui` と smoke を並行実行しない・tests_ui を同時に 2 本走らせない**（複数の verifier・reviewer の UI テストを含む。フックの取り合いで止まる）。
**verifier に `taskkill` で python.exe を一括終了させない**（2026-10-04 に全 python が落ちた）。tests_ui は 260〜730 秒・タイムアウト 1800 秒・出力はファイルへ。
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
- ユーザーの実機目視（task_01）の結果を受ける → OK なら task_02（`/task_new` で起票・正本 §4.6 へ追記・codebase_map・完了判定前レビュー 2 種・decisions_archive/47・current.md・/refactor_check）。
- その後の次フェーズ候補: **idea_39** 表示中のトリガーを戻す・先頭への対象にする / idea_37 カウンター条件分岐 / idea_23 押す / 離すアクション。
- **main へのマージはユーザーが行う**。

## 直前フェーズ（phase 46 = 戻す・先頭への対象トリガー指定）の要点

正本 = `features.md` §4.1・§4.2.6・§4.2.10・§4.6 / `data_schema.md` §5.11.6。判断は `decisions_archive/46`。
- `back` / `rewind` の任意キー `target`: あればそのトリガー・無ければ直前のトリガー。判定は `domain/sequence_control.control_target`（None / "" / 正規化キー）の 1 か所。
  実行時は `sequence_history.apply_control(..., target_key=)`・OK 時の検査は `domain/control_target.edit_control_target_violation`（呼び出しの検査とは別）・キー変更は `rename_control_targets`。
- 2 回押しの破棄で確定していなかった段が確定すると直前のトリガーが指定先になる（受容・§4.2.6）。「表示中のトリガーを対象にする」案は idea_39（ユーザー提案）。
- その前の phase 45 の要点（連動・参照中の印・押下の番号つき履歴）は `decisions_archive/45` と正本 §4.2.6・§4.2.9。

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
- **【設計・phase 40 v0.8】待機は「直前に送った行の後の待ち」**: `settle_after_normal` の `wait_mode`（stop = in_call・従来 / wait = 送った後の先行処理で待つ / skip = 止めた後・停止の行の後）。
  `advance` は in_call 外では送る前の待機を読み飛ばす。待機をまたぐ控えのカウンター操作は `StepResume.deferred_counters`。
- **【罠・phase 42 で実証】Tk の標準の挙動は `bind <Class> <Event>` と `info body ::tk::...` で実測してから直す**（Listbox は押下で選択・離しで下線・ドラッグで選択だけ動く）。テストは `event_generate` でクラスバインドを通す。
- **【罠・phase 41 で実証】Win32 の定番の前提も probe で確かめる**（前面の窓への IME 問い合わせは Windows 11 のメモ帳で常に 0。SendInput の文字は後から処理されるので、直後の状態変更は文字より先に効く）。
- **【罠・phase 40 で実証】verifier の失敗報告の「実際の値」は文字化けの書き写しで誤ることがある**（`呼び出し先` → `呼び出し元`）。期待値を直す前に `PYTHONIOENCODING=utf-8` で単体実行して原文を見る。
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
  （直近 3 件: 46_back_rewind_target / 45_call_step_and_view / 44_child_save_dialog_layout）。
- 着手中 idea: なし。モデル ID の更新は `/model_update`（系統ごとに版が独立・稼働側とモード変種を揃える）。未着手/保留 idea: **idea_39**（表示中のトリガーを戻す・先頭への対象に）/ **idea_37**（カウンター条件分岐）/ idea_36（共通トリガー層・現時点で不要）/ **idea_23**（押す / 離すアクション）/
  idea_29〜idea_31 / idea_13 / idea_11 / idea_03 / idea_09（いずれも低）/ idea_04・idea_06（保留）。
  別タスク化候補に「同型スケルトンの共通化」（単純な `bind("<Escape>", destroy)` 等）/ M4（`_apply_initial_focus` の位置・保留）/
  `tests_ui/test_minimize_grab_custody.py`（603 行）の分割 / 「キーがあれば coerce_label」5 箇所（提案書 12 見送り）/
  `_run_to_end_step` の停止 2 行 3 箇所（phase 31・refactor_check 不要）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
