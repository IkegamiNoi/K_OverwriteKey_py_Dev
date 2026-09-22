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
2. `instructions/phase/current.md` を読む（**アクティブ = phase 28**。次採番 = phase 29 / 暫定 23 / decisions 29）
3. `instructions/phase/28_dialog_keyboard_focus/phase.md` と、
   **主入力の暫定仕様 `instructions/history/22_dialog_keyboard_focus.md`（v0.4・ユーザー確定済・未凍結）**を読む。
   着手するタスク定義は `instructions/phase/28_dialog_keyboard_focus/tasks/` 配下
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。
   **凍結済の暫定仕様（`instructions/history/` の 04〜21）の条項を実装の根拠に引かない**（正本 `spec_detail/` が正）。
   **22 だけは未凍結で、phase 28 の確定設計として有効**

## 現在の作業の 1 行サマリ
**phase 28 task_04 まで完了（idea_18 解消 = 一括 3/3 green）。次は task_05（統合確認 + 実機目視）。実装は全て完了済みで、残りは検証と正本反映。**
直近コミット: `35c280e`（task_04 = Escape 配送の flaky 解消）/ `bd0a1bc`（task_03 = 群 C へ Escape 結線）/
`28ab399`（task_02 = 実 Tk の初期フォーカス検査）/ `08ace46`（task_01 = grab_modal へフォーカス集約）。
**main は phase 18 task_05d まで取り込み済み**（phase 18 の残り・19〜28 はユーザーがマージする）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 28 task_04 完了時点 = 2026-09-23**）:
compile **clean** / tests **556 実行 OK**（skip 7）/ tests_ui **502 実行 OK**（skip 0）/ smoke **pass**。
**件数が減ったら退行を疑う**（tests: phase 27 完了 556 → 変化なし / tests_ui: 484 → 502）。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
実行後に **`config/config.json` の mtime が変わっていない**・worktree ルートへ **`user/` / `quarantine/` /
`keymap_set_history*.json` が生成されていない**ことを確認する。

**【解消済み】`tests_ui` 一括の Escape 依存 flaky（idea_18）は phase 28 task_04 で解消した**
（一括連続 3 回とも 502 OK・skipped 0。直前は 3 回中 1 回しか緑にならなかった）。
**新しく Escape でダイアログを閉じるテストを書くときは、`focus_force` + `event_generate` を直書きせず
`tests_ui/escape_delivery.py` の `send_escape(test_case, app, dialog)` を使う**
（フォーカス確保を確認してから送り、破棄を上限つきで待ち、失敗時は診断情報を添えて fail する）。

**既知の stderr ノイズ（退行ではない）**: `invalid command name "..._clear_flash_message"`（ステータスバーのタイマー）/
`ResourceWarning: unclosed file`（`tests/test_config_service.py`）。

## 次アクション（session.md.next_action より）
- **task_05 のタスク定義を `/task_new` で起票する**（統合確認 + 実機目視）。
  ①`deep-reviewer` + `codex-reviewer` の統合レビュー（task_01〜04 を跨ぐ差分）
  ②**負荷下の再現確認**（暫定仕様 §8-7。busy loop 4 本の負荷下で対象クラスを 6 回）+ 一括連続 3 回 green
  ③**実機目視の依頼**（§8-8）: 群 B の 3 ダイアログを**アクティブな App から開き、ダイアログ内を
  クリックせずに直ちに Escape** で閉じること / 群 C の 5 経路も Escape で閉じること /
  **フォーカス復帰の再現確認**（内側ダイアログを閉じた後・最小化復帰後に外側で Escape が効くか）
  ④skip 件数の報告（現状 0 件）
- 以降: **task_06（正本反映）** = `features.md` へフォーカス + Escape の **2 条項** /
  `codebase_map.md` の `grab_modal` 署名更新と**「13 箇所」→「15 箇所」訂正** / 暫定仕様 22 の凍結 /
  `decisions_archive/28` 作成 / `current.md` 更新 / **idea_26・idea_18 を `backlog/INDEX_done.md` へ移動** /
  `/refactor_check`。
- **main へのマージはユーザーが行う**。
- **運用**: `verifier` に変異検査を頼むときは「**`git checkout --` / `git restore` / `git stash` を使わない**（未コミットの実装ごと巻き戻る）。
  ファイルのコピーで退避・復元する」を明示する。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。

## 現在のフェーズ（phase 28 = ダイアログの初期キーボードフォーカス）の要点

**設計は暫定仕様 22 が正**（`instructions/history/22_dialog_keyboard_focus.md`・v0.4・**未凍結**）。
フェーズ中は正本 `spec_detail/` を直接改訂しない（昇格は task_06）。

- **フォーカスの責務は `grab_modal` に集約**。署名 = `grab_modal(window, parent=None, *, focus=None)`。
  **省略時は窓自身**へ、指定時はその widget へ `focus_set`。適用は `grab_set()` の直後
  （`_apply_initial_focus`）。**早期 return 経路〔二重呼び出し・最小化中の預かり〕では触らない**。
  例外は **`TclError` のみ**握る。
- **推測型は実測で反証済み**: 未マップの Toplevel への `focus_set` は Tk 内で保留され、
  **`focus_lastfor()` / `focus_get()` から検出できない**。だから「既存指定の有無を grab_modal 側で判定する」
  方式（`focus_lastfor` 既定 / `after_idle`）は**既存の初期フォーカスを奪う**。**明示引数が唯一の形**。
- **群分け（`grab_modal` の呼び出しは production 15 箇所）**: A=6（`__init__` 内で明示）/
  A'=1（`child_save_dialog` のビルダ内で明示）/ B=3（欠落していた `orphan_sweep` / `quarantine_manage` /
  `reference_cleanup`）/ C=5（Escape 未結線だった `layout_delete` / `preset_manager` / `io_dialogs` /
  `hotkey_presets_io` / `child_save_dialog` の「子ファイルの保存」）。
- **Escape は「閉じる（×）」と同じ経路へ結ぐ**（新しい閉じ方を作らない）。
  群 C は `io_dialogs` のみ **`on_cancel`**、他 4 件は `destroy`。
  **`bind` は `grab_modal` より前**に置く（静的検査「`__init__` の最後は `grab_modal`」を壊さないため）。
- **Escape 配送の機序（idea_18 の根本原因・task_04 で確定）**: Tk はキーイベントを**フォーカス窓へ再配送**する。
  `tests_ui` はテストクラスごとに `App`（`tk.Tk`）を作る = **同一プロセスに複数の Tk アプリ**があり、
  **別アプリが OS フォーカスを持つと Escape は破棄される**。**「配送が遅い」のではなく「配送先が違う」**ため
  待つだけでは直らない。対処は**フォーカス確保を確認してから送る**（`escape_delivery.send_escape`）。
- **テストの役割分担**: `test_modal_grab.py`＝決定論的な単体検査（`focus_set` の呼び出しを patch で記録）/
  `test_dialog_initial_focus.py`＝実 Tk の初期フォーカス検査（**App の前面化は試みるがダイアログの
  `focus_force` はしない**。取れなければ skip）/ `test_dialog_escape_binding.py`＝結線と後始末の固定。
- **ユーザー確定事項**: 群 C にフォーカスが入る挙動変化は**受容** / 正本へ **Escape 条項も追加**する /
  **フォーカスの復帰（閉じた後・最小化復帰後）はスコープ外**（実機目視で再現確認のみ）/
  同型スケルトンの共通化は**合流させない** / **案 A（ハンドラ直呼び）は併用しない**（実配送の検証を残す）。
- 直前の完了フェーズ = phase 27（構成セットの読み込み履歴）。要点と判断は
  `decisions_archive/27_keymap_set_load_history.md` を参照（正本は `data_schema.md` §5.12）。
  **使い分け = パスは `coerce_label`（trim のみ）/ キー名・id は `coerce_key_name`（trim + 小文字化）**だけは
  触る頻度が高いので覚えておく。**起動エントリ（`config.json` の `keymap_set_path`）は保存で上書きしない**（phase 26）。

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
  **phase 28 では idea_26 の「正本 §4.6 に Escape 規定あり」が実在せず、`codebase_map.md:308` の
  「13 箇所」も実測 15 箇所だった**（後者は task_06 で訂正する）。
- **【最重要・phase 28 で実証】Tk の挙動は推測せず probe で実測する**。
  `.venv` python で小さなスクリプトを書けば数分で確定でき、**設計の前提を 2 度ひっくり返した**
  （①未マップ時の `focus_set` は外から検出できない ②Escape はフォーカス窓へ再配送される）。
  **レビューだけでは前提の誤りは見つからない**（`deep-reviewer` は「Tk の前提は妥当」と判定したが実測で反証された）。
- **【傾向・実証済み】reviewer が「採用」でも敵対的 / 上位レビューで指摘が出る**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**。
  `codex-reviewer`（標準 review）は focus text を受け付けないので、観点を渡すなら `codex-adversarial-reviewer`。
- **【傾向・phase 22 / 27 で実証】正本へ昇格した文章は `deep-reviewer` にかけると矛盾が出る**
  （既存節との衝突・手順の書き落とし・実装より強い断定）。**昇格差分も必ずレビュー対象に含める**。
- **【罠・phase 27 で実証】テストに `focus_force()` のような「通してしまう前処理」があると、実使用の不具合を隠す**。
  **ダイアログ自身への `focus_force` は初期フォーカス検査で使わない**（App の前面化は可。役割が違う）。
- **【罠・phase 28 で実証】フック再開は `<Destroy>` から `after(0)` で予約される**
  （`presentation/controllers/hook_controller.py:57`）。**`destroy()` の直後に
  `get_hook_pause_count()` を数えると 1 のまま**。数える前に `app.update()` を挟む。
- **【罠・phase 27 で実証】`tests_ui` は実 `config/` を汚し得る**（`App()` を作るだけで起動時処理が走る。
  `.gitignore` の `config/` 除外で `git status` に出ない）。**App を作る新規テストは
  `tests_ui/test_keymap_set_history_flow.py:17-34` の ExitStack 手法を踏襲する**。
- **【傾向】テストの「検出力」は変異検査で確かめる**（その仕様を壊すと**追加テストだけ**落ちるか）。
- **【Codex 運用】フォワーダが切れても Codex ワーカーは生き続ける**（判別は作業ツリーの更新時刻）。
  **書き換え途中で `verifier` / `reviewer` を回さない**。`taskkill /T` を使わない。**Codex 申告のテスト結果は信用せず実測**。
  30 行目安を超えた実装は**同じ Codex へ差し戻して分割**させると早い。
  **Codex が書いた行は LF で入ることがある**（CRLF のファイルへ混在）。受領後に改行コードを揃える。
- **【運用・重要】委任の実行中はメイン側でコードを編集しない**（文書のみ・対象ファイルが重ならない場合は可）。
- **【config.json の書き手は 2 本】** `StartupIo.write_startup`（現在値へマージ・成功時のみ `_startup_settings` 置換・**失敗表示中はフック停止**）と
  keymap_set 保存（`save_runtime_data` が `_startup_settings` をディープコピー）。**直接 `config.json` を read-modify-write しない**。
  **`keymap_set_path` だけは保存で据え置く**（phase 26）。
- **【config_service の配置制約】** ConfigService 本体は `application/config_service/__init__.py`（841 行・新規ロジックを置かない）。
  **presentation から兄弟モジュールを直接 import しない**（公開面は `ConfigService` の公開 API と `contracts.py` のみ・テストが落とす）。
  モジュールを増やしたら `tests/test_config_service_contracts.py` の `INTERNAL_MODULE_NAMES` を更新する（**実ファイル集合と完全一致**）。
- **【最重要・2 度踏んだ罠】パス表記の混在**: runtime の `source_path` 3 種と `hotkey_presets_path` は config 配下なら相対。
  解決なしで `os.path` 系へ渡すと cwd 基準になり **リポジトリルートに `user/` が生成される**。
  解決は `ConfigService.resolve_config_path(path, config_root)`（`config_root` に空文字を渡さない）。
  **比較専用の正規形は `ConfigService.canonical_path`**（自前で `normpath`/`normcase` を組まない）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**
  （失敗が「ハング」に化ける）。tests_ui の各ファイルの `setUp` に fail-fast ガードがある。
- **【tests_ui の罠】`setUpClass` で App を共有する**: dirty・フック停止カウンタ・ウィンドウ最小サイズ / geometry / 最大化状態 / pane 幅 / font delta / 保存予約
  を他テストから持ち越す。**前後の変化で assert し、`addCleanup` で必ず元へ戻す**。新規テストは `patch.object` を優先。
- **【罠】ダイアログを増やしたら 3 つの列挙を更新する**: `DIALOG_FILES` / `T2_DIALOG_FILES`
  （`tests_ui/test_dialog_teardown_flows.py`）と **`dialog_classes`（`tests_ui/test_nested_modal_grab.py:262`）**。
- **【罠】worktree と main は別コピー**。main 側の絶対パスを編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。長い heredoc は壊れやすい（**壊れたら Write ツールを使う**）。
  **PowerShell の here-string（`@'...'@`）を Bash へ渡さない**（メッセージ先頭 / 末尾に `@` が混入する）。
  **sed の区切りに `#` を使うとパターン中の `##` で壊れる**。複数行のコミットメッセージは `git commit -F <file>`。
  **`git grep` は追跡済みのみ検索**。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: 27_keymap_set_load_history / 26_startup_entry_preservation / 25_path_field_type_normalization）。
- 未着手/保留 idea: **idea_23**（押す / 離すアクション）/ idea_13 / idea_11 / idea_03 / idea_09（いずれも低）/
  idea_31・idea_32（phase 28 の周辺で起票済）/ idea_04・idea_06（保留）。
  **idea_26・idea_18 は phase 28 で着手中**（task_06 で `INDEX_done.md` へ移す）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
