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
2. `instructions/phase/current.md` を読む（**アクティブなフェーズ = phase 75 = macOS 対応**）。続けて `instructions/phase/75_mac_support/phase.md` と主入力 `instructions/history/57_mac_support.md`（v0.18。冒頭の版の履歴で v0.11〜v0.18 の改訂を確認する）を読む。
   次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 62（暫定 47 は idea_53 で保留中の番号）
3. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
4. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。
   **画面の文言を書くときは `instructions/common/spec_detail/ui_terms.md`（UI 用語と表記・英語の列と表記規則 E1〜E7）に従い、`ja.json` と `en.json` の両方にキーを足す**。
   **凍結済の暫定仕様（`instructions/history/` の 04〜46・48〜56）の条項を実装の根拠に引かない**（正本 `spec_detail/` が正。暫定 47 は保留・未確定）

## 現在の作業の 1 行サマリ
**phase 75 段階 ④。task_12 完了（2026-11-18）。暫定 57 v0.22（§6.3 配布物の中身とライセンスの表示）確定。task_13a（第三者ライセンスの表の OS 列）を実装・Windows 検証 pass・reviewer 完了可・コミット済み。task_13a は Windows 目視 OK で完了。task_13 起票済み（2026-11-18・reviewer 修正して採用）。次 = PyInstaller の導入の許可（ユーザー）→ task_13 実装 → task_13b（Mac）。**
**presence: away（戻る予定 未定）**。再開したら session.md の presence 行は消してよい。
Windows の worktree = `claude/continue-c6c37b`（未 push）。Mac の worktree = `claude/modifier-key-registration-issue-faa33a`。push と main へのマージはユーザー（PR は作らない）。
直近の実測（Windows・task_13 後・2026-11-18）: compile clean / tests 2203・失敗 0・skip 7 / smoke pass / PyInstaller 6.22.3 のビルド成功。
Mac のテストの基準線 = `instructions/phase/75_mac_support/mac_test_baseline.md`（task_11d 後 2131 件・失敗 1〔test_third_party〕→ task_13a で Python / Tcl / Tk の照合は skip に）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
Mac では `../../../.venv/bin/python` に読み替え、**tests_ui は通しで走らせない**（`mac_test_baseline.md` の手順でモジュールごと）。
直近の実測（**Windows = task_08b 完了時・2026-11-14**）:
compile **clean** / tests **2065 pass**（skip 7）/ tests_ui **1271 pass**（task_08 時）/ smoke **pass**（verifier）。tests_ui の `invalid command name "...apply_if_already_sized"` は破棄後の after のノイズで失敗ではない。
**Mac（task_11e 後・2026-11-17・`../../../.venv/bin/python`・Homebrew 3.13.18 + Tk 9.1.0）**: compile clean / tests 2124 件・失敗 1（test_third_party）・エラー 0・skip 31 / smoke pass / tests_ui 8 本 失敗 0。**Mac の窓の不具合は実際の App で本物のクリック（Quartz の CGEventPost）を送る probe で実測する**（プログラムからの呼び出しでは再現しないことが多い・scratchpad の probe は消える）。**画面のロック中は `tkinter.Tk()` が返らず tests_ui が止まる**（ロックを解いてから流す）。
**件数が減ったら退行を疑う**（tests: 1951〔phase 74〕→ 1977〔task_05〕→ 1997〔M1〕→ 2022〔task_08〕→ 2065〔task_08b〕 / tests_ui: 1270 → 1271）。
`tests_ui.test_compact_window`（サイズ保存のタイミング系 3 件）が全体実行時だけ落ちることがある（単独 pass・current.md「テスト負債」）。`tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・名前順の一括実行では落ちない・current.md「テスト負債」。例: `test_dialog_help_buttons` の後に続けて走らせると落ちる）。
`tests_ui/test_dialog_teardown_flows.py` の t4a / t4b / t5 が全体実行で `1 != 0`（setUp のフック一時停止の数）で落ちることがある（2026-10-18 にも 1 回。単独 2 回・全体再実行 1 回で再現せず）。再発が続くなら下記の flaky 対処を当てて idea 化を検討。
**`tests_ui` と smoke を並行実行しない・tests_ui を同時に 2 本走らせない**（複数の verifier・reviewer の UI テストを含む。フックの取り合いで止まる）。
**verifier に `taskkill` で python.exe を一括終了させない**（2026-10-04 に全 python が落ちた）。tests_ui は 260〜730 秒・タイムアウト 1800 秒・出力はファイルへ。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
実行後に **`config/config.json` の mtime が変わっていない**・worktree ルートへ **`user/` / `quarantine/` /
`keymap_set_history*.json` が生成されていない**ことを確認する。

**tests_ui の flaky**（`get_hook_pause_count()` が `1 != 0` 等）が出たら、まず再実行・単体実行で切り分け、`decisions_archive/32` の対処（`wait_for_hook_pause_count`）を当てる。

**既知の stderr ノイズ（退行ではない）**: `invalid command name "..._clear_flash_message"`（ステータスバーのタイマー）/
`ResourceWarning: unclosed file`（`tests/test_config_service.py`）。

## 次アクション（session.md.next_action より）
- **【ユーザーの確認待ち】task_13 の実機確認（Windows・ビルド済みの `dist/keyseq/keyseq.exe`）**: ①初回起動で exe の隣に `config/` ができ `config/user/keylayout` に見本 5 本 ②設定を保存→再起動で読み込まれる ③言語の切り替えの再起動で exe が 1 つだけ起き直る ④ヘルプ→ライセンスの窓に 15 行（最後が PyInstaller）・ja / en で切り替わる ⑤置換・シーケンス（キーとマウス）が開発実行と同じに動く。OK なら task_13 完了。dist/ は worktree の直下（`C:\Users\ikega\Documents\GitHub\python_dev\K_OverwriteKey_py_Dev\.claude\worktrees\continue-c6c37b\dist\keyseq\keyseq.exe`）。作り直すときは `packaging/README.md` の手順。exe の名前 `keyseq`・タグ `v0.1.0`（版を上げるかはユーザー判断）・タグと push はユーザー。
- その後 task_13b（Mac のビルド・Mac の行〔pyobjc・Python / Tcl / Tk〕・`open -n`・Mac での task_12 / 13a / 13 の確認・Mac の `.spec`）。
- **Codex の注意**: CRLF のファイルには apply_patch が当たらず止まる → 依頼前に対象を LF に揃える（`sed -i 's/\r$//'`・git が正規化）。`git mv` は Codex では失敗する → メインで。Codex は 1 回で全部終わらないことが多い（本体 → テストの 2 回に分けると通る）。

## 運用インフラ

- **モード切替は `.claude_data/modes/`**。エージェント構成は 3 モード（`codex`〔現構成〕/ `codex_medium` / `claude_only`）。
  **`.claude/` 配下または `CLAUDE.md` を編集する前に `.claude_data/modes/README.md` を読む**。
- **template からの取り込みは `/template_pull`**（マーカー = `.claude/template_pull_state.md`）。
- **`.gitignore` は追跡ファイルだけを根拠にしない**。確認は `git check-ignore -v`。

## 注意事項・blockers
- 文言カタログ = `keyseq/shared/i18n/`（`tr(key, /, **params)`・`tr_in`・選んだ言語 → en → ja → キー）・`locales/ja.json`（正）/ `en.json`
- **`tr` をモジュール定数・クラス属性・既定引数に書かない**（import 時に ja で固まる）。表は値をキーにして表示の時点で `tr`
- **App を作る / 文言を assert する新しいテストモジュールは import 直後に `fix_language("ja")`**（`tests/test_i18n_test_language_fixed.py` が検出）。ソースの日本語は `tests/test_no_japanese_ui_literals.py` が検出
- **【罠・phase 72】Codex は表示用の部品・文字列を取り違えることがある / 新テストが messagebox（modal）で tests_ui を止めることがある**（単独実行 + `timeout` で特定し patch）
- **【phase 75】`.venv` のパスは OS で違う**（本書の `Scripts/python.exe` は Windows。Mac は `bin/python`）。Mac の `.venv` は Homebrew の 3.13 + `python-tk@3.13`（**Tk 9.1**・Q1 から変更・decisions.md）。**Tk 9 は長さの `cget` を単位つき（`10c`・`2.25p`）で返す → `tk_platform.screen_distance` を使う**。Tk の差の判定は `presentation/tk_platform.py` の 1 か所。
- **【解消・2026-11-22】Codex の書き込み実行の不具合**（2026-10-14 の Codex 更新〔0.162.x〕以降の `setup refresh had errors`）。`~/.codex/config.toml` の `[windows] sandbox` を `elevated` に戻し、Codex 0.171.0 で書き込み OK。
  再発したら `unelevated` に変えて回避（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない。
  companion は作業フォルダごとに broker + app-server を常駐させる（呼び出し後も残る設計・worktree ごとに増える）。Codex 不可時の実装代替はユーザー許可が必須。
- **【罠・phase 58 task_02 で実測】ttk.LabelFrame の `labelwidget` に既定の ttk.Label を使うと枠が 4px 高くなる**（vista・58 → 62px）。`style="TLabelframe.Label"` なら元と同じ
- **【罠・phase 54 で実証】合成入力の probe で NumLock を切り替えるなら VK（`keybd_event(0x90, ..., EXTENDEDKEY)`）**。スキャンコード入力（69）では切り替わらない。probe の後は元の状態へ戻す。**Codex の新規テストの Mock の戻り値・期待値の誤り**が 1 フェーズで 2 件出た（実装は正しい）＝失敗時はまずテストを疑い、実装の仕様と照合する
- **【罠・phase 51 で実証】keyboard ライブラリの `write` は送信前後に押下中のキーを離して修飾キーを押し直す**（拡張キーの right ctrl が left ctrl に化けて残った・probe）。合成の入力の扱いは `.venv` の小スクリプトで probe してから決める。**新しい tests_ui でテストごとに `tk.Tk()` を作り直すと後のモジュールのフォーカスが取れなくなる**（クラスで共有する）。Esc 等のキーの event_generate は `tests_ui/escape_delivery.acquire_focus` でフォーカスを取ってから
- **Codex は互換の工夫（`inspect` での引数判定・`getattr` の逃げ道）を足す・テストの期待値を推測で書くことがある**（task_04d で 2 つ目の待機が次の押下まで始まらないのを見落とした）＝差分の直読みと実測で外す。
- **【罠・phase 49 で実証】共有 App の tests_ui で `<Enter>` を送ったら後始末で `<Leave>` も送る**（乗せた状態が次のテストに漏れてツールチップが重複する）。**実機目視の手順はカーソル・窓の位置まで考えて書く**。
- **【罠・phase 48 で実証】遅延保存（after 500ms）を持つ部品は、書き込み回数を数えるテストに時間依存で混ざる**。テストでは先に `app.compact_window.cancel_save()`。
- **【罠・phase 48 で実証】Tk の PanedWindow は欄の高さを明示しないと子の要求の高さへ戻し、明示直後の `sash_place` は古い大きさで押さえ込まれる**
  （`compact_pane_layout._place_heights` は paneconfigure height → update_idletasks → sash_place）。**pack は先に入れた子が高さを先に取る**（ステータス類・閉じた見出しは side=bottom で先に pack）。
  **0 に縮んだ欄の子の `winfo_height` は古い値のまま**・見えていない行の `bbox` は None（テストで頼らない）。
- **【罠】Bash ツールで `python3` / `python` を呼ばない**（Windows ストア版スタブが stdin 待ちでハングし、同じコマンド内の後続も実行されない）。
  スクリプトを直接走らせるときは `PYTHONPATH=.` を付ける。
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
- **【罠・phase 42 で実証】Tk の標準の挙動は `bind <Class> <Event>` と `info body ::tk::...` で実測してから直す**（Listbox は押下で選択・離しで下線・ドラッグで選択だけ動く）。テストは `event_generate` でクラスバインドを通す。
- **【罠・phase 41 で実証】Win32 の定番の前提も probe で確かめる**（前面の窓への IME 問い合わせは Windows 11 のメモ帳で常に 0。SendInput の文字は後から処理されるので、直後の状態変更は文字より先に効く）。
- **【罠・phase 40 で実証】verifier の失敗報告の「実際の値」は文字化けの書き写しで誤ることがある**（`呼び出し先` → `呼び出し元`）。期待値を直す前に `PYTHONIOENCODING=utf-8` で単体実行して原文を見る。
- **【運用・phase 40】ダイアログは操作中のアプリからフォーカスを奪うため、実行中の知らせはステータスバー（`notify_message`）にする**（暫定 29 v0.7）。
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
  **Codex は改行コードを混在させることがある**（LF のファイルを CRLF で書き戻す・CRLF のファイルへ LF の行を入れる。phase 48 でも発生）。コミット前に `git diff --stat` の行数と改行コードを確かめる。
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
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: 74_key_symbol_display / 73_welcome_first_launch / 72_multilingual_ui）。
- 未着手・保留の idea は `instructions/backlog/INDEX.md` を見る。モデル ID の更新は `/model_update`（系統ごとに版が独立・稼働側とモード変種を揃える）。
- 別タスク化候補: 「同型スケルトンの共通化」（単純な `bind("<Escape>", destroy)` 等）/ M4（`_apply_initial_focus` の位置・保留）/
  `tests_ui/test_minimize_grab_custody.py`（603 行）の分割 / 「キーがあれば coerce_label」5 箇所（提案書 12 見送り）/
  `_run_to_end_step` の停止 2 行 3 箇所（phase 31・refactor_check 不要）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
