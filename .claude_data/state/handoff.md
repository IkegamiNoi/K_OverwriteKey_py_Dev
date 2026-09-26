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
2. `instructions/phase/current.md` を読む（**アクティブなフェーズ = なし**〔phase 34 は 2026-09-27 完了〕。
   次採番 = phase 35 / 暫定 26 / decisions 35 / 提案書 14。次フェーズはユーザー判断・着手時は `/phase_start`）
3. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
4. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。
   **凍結済の暫定仕様（`instructions/history/` の 04〜25）の条項を実装の根拠に引かない**（正本 `spec_detail/` が正）

## 現在の作業の 1 行サマリ
**phase 34 完了（トリガー一覧のキーマップ従属化・JSON スキーマ変更あり・暫定 25 v0.7 凍結・refactor_check = 提案書 13 → task_09 で実施済）。次フェーズは未定（ユーザー判断待ち）。**
直近コミット: phase 34 完了記録（本コミット）/ `9fc07a5`（task_09）/ `999cecd`（task_09 起票）/ `a1db856`（task_07e）。
**main は phase 18 task_05d まで取り込み済み**（phase 18 の残り・19〜34 はユーザーがマージする）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 34 完了時点 = 2026-09-27**）:
compile **clean** / tests **669 実行 OK**（skip 7）/ tests_ui **576 実行 OK**（skip 0）/ smoke **pass**。
**件数が減ったら退行を疑う**（tests: phase 33 完了 577 → phase 34 完了 669 / tests_ui: 537 → 576）。
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
- 次フェーズはユーザー判断（候補 = `current.md`「次フェーズ候補」の idea_23 /「別タスク化候補」の phase 34 残件）。着手時は `/phase_start`。
- **main へのマージはユーザーが行う**（ブランチ `claude/trigger-list-multi-keymap-19f4d7`・phase 18 残り・19〜34）。
- **`/template_pull` で取り込む**: `.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（ユーザー 2026-09-23）。

## 直前フェーズ（phase 34 = トリガー一覧のキーマップ従属化）の要点

**全レイヤ・JSON スキーマ変更あり**（暫定仕様先行モード・暫定 25 v0.7 凍結）。判断は `decisions_archive/34`、正本は `data_schema.md` §5.13 ほか / `key_input.md` §7.3 / `features.md` §4.1・§4.3・§4.5、
地図は `codebase_map.md`「キーマップとトリガー一覧（phase 34）」節。

- トリガー一覧（と従属するシーケンス）はキーマップに従属。keymap ファイルに `trigger_set_path`・keymap_set の `trigger_set_path` は常に `""`・単一 JSON は `keymaps[].triggers`。
- アクセスは `domain/keymap_triggers.py` の口だけ（presentation の `"triggers"` 直値は静的検査で禁止）。同じ trigger_set は実体を共有（代表 = 一覧順の先頭）。
- 入力の優先順位 = 停止 > トグル > 直接切替 > トリガー > 置換。重なりは `application/key_overlap.py` の読み取り専用の表。切替中は停止 / トグル以外を素通し。
- UI = `controllers/keymap_panel/`（追加フローは `keymap_add_flow.py`。テストはこちらの `messagebox` / `KeymapEditDialog` を patch）。
- 残件 = `config_service/__init__.py` 1133 行 / 80 行超の関数 5 つ / 統合レビュー保留 L-1・L-7 / 移行の境界値テスト（current.md「別タスク化候補」）。

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
  （直近 3 件: 33_grab_modal_static_check_discovery / 32_hook_resume_wait_in_ui_tests / 31_unknown_action_type_handling）。
- 着手中 idea: なし。未着手/保留 idea: **idea_23**（押す / 離すアクション）/
  idea_29〜idea_31 / idea_13 / idea_11 / idea_03 / idea_09（いずれも低）/ idea_04・idea_06（保留）。
  別タスク化候補に「同型スケルトンの共通化」（単純な `bind("<Escape>", destroy)` 等）/ M4（`_apply_initial_focus` の位置・保留）/
  `tests_ui/test_minimize_grab_custody.py`（603 行）の分割 / 「キーがあれば coerce_label」5 箇所（提案書 12 見送り）/
  `_run_to_end_step` の停止 2 行 3 箇所（phase 31・refactor_check 不要）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
