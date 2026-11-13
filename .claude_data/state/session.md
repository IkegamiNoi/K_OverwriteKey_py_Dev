# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-14T13:00:00
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.7・ユーザー確定済）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/continue-a0cc59`（Windows の worktree・task_09 / 09a 起票まで）。Mac の worktree `claude/continue-0b2dfa` へ取り込んでから task_09 を実装する。push はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 75 段階 ③。task_09（送信）・task_09a（Tk の取得・表示・入力ソース）を起票（reviewer 修正して採用・反映済み）。次は task_09 の実装（Mac で行う。Quartz の実物の検証が要るため）。**
mode: implementing

## last_action
ts: 2026-11-14T10:00:00
who: main
summary: |
  実施: task_08b = `macos/key_table.py`・`modifier_state.py`・`event_tap.py`（新規）・`macos/backend.py` のフック 3 メソッドと合成（infrastructure の `macos/` 限定）。codex-delegating-implementer（Sol + Luna サブエージェント使用・自己申告）。既存の `test_macos_stub_contracts_and_factory`（旧スタブの OSError 前提。権限ありの Mac で実 tap が作られ失敗）を偽の EventTap で開始・停止を確かめる形へメインが修正。
  reviewer: 修正して採用。中 = 表に無い vk を抑止できない → ユーザー判断「仕様どおり直す」（素通しは CapsLock 57・fn 63 だけ）。低 = `_pressed_keys` 削除・未知の flagsChanged は素通し・テストの reload 廃止 → codex-implementer で修正。
  probe（2026-11-14）: 自動リピート = 初回 0・以降 1 / 右 Command 54 `0x10` 等を再確認 / 右 Option・右 Control は内蔵キーボードにキーが無く未実測（文書値のまま）/ CapsLock 2 回押下で FlagsChanged が 1 件も届かず（原因未確定・素通しなので影響なし）→ 暫定 57 §4.1 に追記。
  codebase_map の os_backend 節（macos 4 ファイル）を追従（メイン）。
result_files:
  - keyseq/infrastructure/os_backend/macos/backend.py・event_tap.py・key_table.py・modifier_state.py
  - tests/test_macos_key_table.py・test_macos_modifier_state.py・test_macos_keyboard_backend.py（新規）・test_os_backend_contracts.py
  - instructions/phase/75_mac_support/diagnostics/probe_tap_08b.py（新規）
  - instructions/history/57_mac_support.md（§4.1）・instructions/common/codebase_map.md
verified:
  compile: clean（Mac）
  tests_mac: 2008 件・失敗 6・エラー 10・skip 28（基準線どおり・既知のみ）
  smoke_mac: pass
  tests_windows: 2065 件・失敗 0・エラー 0・skip 7（2026-11-14 verifier）/ compile clean / smoke OK
  visual_mac: ①②⑥ OK（ユーザー）・③④は修飾キーを登録できず未確認 → task_09 へ移した（phase.md の task_09 行に追記）・⑤未報告

## next_action
- （済）Mac 向けのレイアウト = 暫定 57 v0.8 §5.3.2・task_09b（task_09 の後）
- task_09 の実装（codex-delegating-implementer の想定。Mac で実装・検証・目視）→ task_09a → task_09b
- task_08 のキュー版の実機確認（reviewer 参考 2 = 排出中のモーダル）は task_09 の目視でまとめて
- `test_keymap_list_operations` の合成マウスイベントの 2 件は要調査（task_09 で）
- task_09 でキーボードUIの右クリックによる割り当てのクリアを目視（task_05c の残り）
- 右 Option・右 Control の実測は外付けキーボード、JIS の実測（§5.3.1）は JIS キーボードを用意できたとき
- Mac で tests_ui を流すときは `mac_test_baseline.md` の手順（モジュールごと・4 モジュール除外）

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
