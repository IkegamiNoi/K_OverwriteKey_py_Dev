# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-15T22:00:00
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.11・ユーザー確定済）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 58
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/modifier-key-registration-issue-faa33a`（Mac の worktree・task_09d のコミットまで）。push はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: 在席
focus: **phase 75 段階 ③。暫定 57 v0.11（§5.3.4 = Mac の修飾キーのキー名 `command` / `option`・§5.3.3 の表示名の差し替えを廃止・両 OS で他方の名前を拒否）を確定し task_09d / 09e / 09f を起票。task_09d（Option の文字・Mac 目視 OK）・task_09e（Mac のキー名・表示名の差し替えの撤去）・task_09f（他方の OS の名前の拒否と入口・修飾キー単独の読み飛ばし）を Mac で実装・目視 OK。次 = task_09b。残り = 09〜09f の Windows 検証・Caps Lock の未決。**
mode: implementing

## last_action
ts: 2026-11-15T22:00:00
who: main
summary: |
  task_09f 実装（暫定 57 v0.11 §5.3.4）: codex-delegating-implementer（Sol medium + Luna high 3 体）・23 ファイル。backend の `accepts_key_name`・各入口・修飾キー単独の読み飛ばしを `is_modifier_key` へ。メインがテストの前提の誤り 2 件を修正。
  reviewer: 採用（低 3 は任意・未対応）。Mac 目視 OK（09e と合わせて）。
  ユーザー: hotkey の保存時の検査もホワイトリストにしたい → idea_03 に追記（phase 75 の範囲外）。「コミット」。
result_files:
  - keyseq/infrastructure/（input_gateway・os_backend/contracts・macos/backend・windows/keyboard_backend）
  - keyseq/presentation/（keyboard_window・dialogs/action_dialog・trigger_dialog・keymap_edit_dialog・keymap_switch_batch_dialog・controllers/key_capture・keymap_panel/keymap_panel_controller・trigger_panel/trigger_row_edit）
  - tests / tests_ui（拒否・保持・読み飛ばしのテスト 10 ファイル）・codebase_map.md・instructions/backlog/idea_03・INDEX.md
verified:
  compile: clean（Mac）
  tests_mac: 2070 件・失敗 6・エラー 10・skip 29（基準線どおり）
  smoke_mac: pass
  tests_ui_mac: 10 本 1 本ずつ・失敗は既知の Caps Lock 1 件のみ
  tests_windows: not_run（test_input_gateway_send の Windows の拒否は Mac で skip）
  visual_mac: task_09e・09f OK

## next_action
- **task_09b を実装**: `instructions/phase/75_mac_support/tasks/task_09b_*`（未起票なら `/task_new` で起票。暫定 57 §5.3.2 v0.11 = `config/user/keylayout/us_mac.json` / `jis_mac.json`・修飾キーの id は `command_l` / `command_r` / `option_l` / `option_r`・fn は置かない・CapsLock と Command は禁止の色・`jis_mac` は `yen` / `ro` を置く）→ 実装エージェントへ → verifier → reviewer → Mac 目視（§9 の 13・キーボードUIで Option の枠をクリックしたタイトル）。
- **【確認事項・ユーザー】Caps Lock の未決**: Mac のキー表に `caps lock` が無く、既存の Caps Lock の切替キーが再検証を通らない（`tests_ui/test_prohibited_assign_keys_ui.py` の `test_switch_validation_rejects_new_caps_but_allows_unchanged_caps`・`features.md` §4.6「既存データは拒否しない」と食い違い）。案 A = Mac のキー表に vk 57 の検証・送信だけの名前を足す / 案 B = Mac の仕様差として記録・テストを Mac で skip。メインが推奨を付けて提示（未提示）。
- **task_09〜09f の Windows 検証**: ユーザーが push → Windows で verifier（compile・tests 失敗 0〔test_input_gateway_send の拒否を含む〕・tests_ui 1 本ずつ・smoke）。目視 = task_09d はドイツ語入力で hotkey に ä の位置のキーと AltGr+e を記録 → 実行して ä / € が出るか・AltGr が hotkey の記録で黙って無視されないか（09f reviewer 低 3）・Windows で `command+c` を hotkey に書くと保存で拒否されること。

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
