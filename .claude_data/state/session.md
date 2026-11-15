# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-16T02:30:00
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.15・ユーザー確定済）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 59
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/modifier-key-registration-issue-faa33a`（Mac の worktree・task_11a のコミットまで）。push はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: away（戻る予定 未定）
focus: **phase 75 段階 ③。暫定 57 v0.11（§5.3.4 = Mac の修飾キーのキー名 `command` / `option`・§5.3.3 の表示名の差し替えを廃止・両 OS で他方の名前を拒否）を確定し task_09d / 09e / 09f を起票。task_09d（Option の文字・Mac 目視 OK）・task_09e（Mac のキー名・表示名の差し替えの撤去）・task_09f（他方の OS の名前の拒否と入口・修飾キー単独の読み飛ばし）・task_09b（Mac 用のレイアウトの見本・v0.12 = fn を禁止のキーとして置く）を Mac で実装・目視 OK。Caps Lock の未決は案 B で解決。task_10（権限の案内）・task_11（前面の判定・リピート間隔・v0.13）を Mac で実装・目視 OK。task_11 は 11〜11d に分割。task_11a（マウス・v0.14 = Quartz のクリック / ドラッグ / 保持中の移動の書き換え）を Mac で実装・目視 OK（中クリックは未確認）。task_11b（窓と画面・v0.15 = NSWindow を `Tk_MacOSXGetNSWindowForDrawable` で引く）を Mac で実装・reviewer 採用（未コミット）。残り = tests_ui 4 本と Mac 実機目視 1〜4。残り = 09〜09f の Windows 検証・Caps Lock の未決。**
mode: pending_review

## last_action
ts: 2026-11-16T02:30:00
who: main
summary: |
  task_11a をコミット（ae6095fa）→ task_11b を起票（起票前にメインが実測: Tk_MacOSXGetNSWindowForDrawable で NSWindow を一意に引ける・-transparent / systemTransparent・NSScreen は下原点・未表示の窓の windowNumber は -1）→ reviewer 修正して採用 → ユーザー承認で暫定 57 v0.15・phase.md:83 を改訂 → codex-implementer（3 回の継続）で実装 → メインが segfault するテスト（実物の C 関数を偽の drawable で呼んでいた）と参考の指摘 2 点を修正 → reviewer 採用。ユーザーは不在（/away・戻る予定 未定）。
result_files:
  - keyseq/infrastructure/os_backend/contracts.py・windows/backend.py・macos/backend.py・macos/ns_window.py（新規）
  - keyseq/presentation/screen_grid/grid_overlay_window.py・presentation/controllers/layout_controller.py
  - tests/test_macos_window_backend.py（新規）・tests/test_os_backend_contracts.py・tests_ui/test_screen_grid_overlay.py・tests_ui/test_app_ui_flows.py
  - instructions/history/57_mac_support.md（v0.15）・phase.md・task_11b 定義（新規）・codebase_map.md
verified:
  compile: clean（Mac）
  tests_mac: 2114 件・失敗 1（test_third_party）・エラー 0・skip 30
  smoke_mac: pass
  tests_ui_mac: test_modal_app_foreground pass。test_screen_grid_overlay・test_help_window・test_modal_grab・test_app_ui_flows は未実行（画面のロック中で tkinter.Tk() が返らない）
  tests_windows: not_run
  visual_mac: task_11b 未実施

## next_action
- **【ユーザーの戻り待ち】task_11b の残り（画面のロックを解いた状態で）**:
  1. verifier で tests_ui を 1 本ずつ: test_screen_grid_overlay（基準線 失敗 4・エラー 9 → 減る見込み）・test_help_window・test_modal_grab（基準線 失敗 4・変化を報告）・test_app_ui_flows（基準線 失敗 3・新規 test_keyboard_topmost_watch_ignores_foreground_when_handle_unknown の成否）。増えた失敗はメインがトレースを読んで切り分ける。
  2. ユーザーに Mac 実機目視 1〜4 を依頼（task_11b 定義の完了条件: カーソルグリッドが透けてクリックが通る / モニタの位置 / 最前面のキーボードUIがダイアログの下へ回る / モーダルにフォーカスが戻る）。
  3. OK なら mac_test_baseline.md の test_screen_grid_overlay の行を追従・current.md / decisions.md に記録 → コミットの確認。NG なら報告して止める（動かない機能があれば、無効化の UI の起票を提案）。
- **task_09〜11b の Windows 検証**: ユーザーが push → Windows で verifier（compile・tests 失敗 0〔test_os_backend_contracts の Windows の委譲・呼び出し順を含む〕・tests_ui 1 本ずつ・smoke）。目視 = カーソルグリッドが今どおり透けてクリックが通る・マウスのアクション・task_09d のドイツ語入力の hotkey 等。

## blockers
- **Mac で tests_ui を通しで走らせない**（task_08・09 まではスタブがキー検証できずモーダルで止まる。verifier にも明記）。Mac の python は `../../../.venv/bin/python`
- **【回避中】Codex の書き込み実行（2026-10-14 18:24 以降の不具合）**: `~/.codex/.sandbox/sandbox.2026-10-14.log` に `setup refresh had errors`（node_repl.exe の ACL 更新が失敗）。**2026-10-15 ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `unelevated` に変更 → 常駐の broker・app-server を止めて再実行で書き込み可**。Codex の更新で直ったら `elevated` に戻す（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **画面の文言（phase 72 以降）**: 新しい文言は `keyseq/shared/i18n/locales/ja.json` と `en.json` の両方にキーを足し、ソースに日本語を書かない（静的テスト）。`tr` はモジュール定数・import 時に評価しない。`App(` を作る / 文言を assert する新しいテストモジュールは import 直後に `fix_language("ja")`。英語は `ui_terms.md` §2・§3（E1〜E7）に従う。
- **phase 73**: 報告された不具合のうち、キー名の記号表記は別セッションの提案カードに出してある（本フェーズ外）。tests_ui の窓の大きさのテスト（`test_compact_window.py:298`・`test_pane_window_width_persistence.py:236,275` の `pending`）が負荷で落ちることがある。**tests_ui の App() は worktree の `config/config.json`（ユーザーの手元の設定・gitignore）を読む**ので結果が手元の設定に左右される（task_05 の Welcome を出さない入口で考える）。Codex は python を実行できずテスト修正が手探りになる → 失敗はメインがトレースを読んで原因を絞ってから委任する。
- **phase 71**: タスクバーのアイコンは AppUserModelID（`main.py`）が無いと出ない。`App()` を直接作る tests_ui / smoke では設定されない。
- **`__version__`** はユーザーが直接またはユーザーの指示でだけ変更する（Claude が独断で上げない）。
- **Codex は Python で既存ファイルを編集しようとして失敗することがある** → 依頼文に「apply_patch で編集・Python を使わない」と書く（phase 71）。
- **素の `python` を Bash で呼ばない**（必ず `..\..\..\.venv\Scripts\python.exe`）。Bash の heredoc の前に `cat > file` を単独で書かない（stdin 待ちでハングする）。
- **Codex は互換の工夫・テストの期待値の推測を足すことがある**。差分を直読みしてから verifier / reviewer へ。Codex は LF を混ぜることがある（コミットは git が正規化）。
- カーソルグリッドの地図 = `codebase_map.md`「カーソルグリッド（phase 56・57）」。
- **【罠・phase 57】Windows の Tk で位置の反映の保留中に `wm_attributes("-topmost", True)` を呼ぶと窓が `0,0` へ戻る**（`geometry` の直後に `update_idletasks()`）。Tk の測り直しは after_idle だと配置の計算より先に走ることがある・`<Configure>` で configure し返すと無限ループになり得る。
- **プロセスは pyautogui の import でシステム DPI 対応**。検証は本番の起動経路で
- `tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・current.md「テスト負債」）。
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜46・48〜55）の条項を実装の根拠に引かない。
- **【Codex のプロセス】** companion は作業フォルダごとに `app-server-broker.mjs serve` を常駐させ、`codex app-server` は呼び出し後も残る。worktree を多く使うと codex.exe が溜まる。
- **【罠・phase 58】ttk.LabelFrame の `labelwidget` に既定の ttk.Label を使うと枠の要求高さが 4px 増える**（`style="TLabelframe.Label"` なら同じ）
