# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-14T15:40:00
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.10・ユーザー確定済）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 58
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/continue-f5ebb7`（Mac の worktree・task_09c 実装 f8a976a1 まで）。push はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: away（戻る予定 未定）
focus: **phase 75 段階 ③。task_09（Mac 目視 OK）・09a（Mac 再目視 OK・3 は idea_57 と task_09c へ分離）・09c（修飾キーの表示名の適用範囲・暫定 57 v0.10 §5.3.3・reviewer 採用）を Mac で実装済み。残り = 09c の Mac 実機目視・09 / 09a / 09c の Windows 検証・Caps Lock の未決。**
mode: pending_review

## last_action
ts: 2026-11-14T15:40:00
who: main
summary: |
  実施: task_09a の目視後の修正（暫定 57 v0.9 §5.1 = 送るフラグは物理側 + 送信側・一覧の hotkey 表示・aqua の Command+Option+P・7a56770e）→ 再目視で 3 以外 OK → 置換先の修飾キーは当初からの仕様で idea_57 へ分離 → 暫定 57 v0.10 §5.3.3（表示名の適用範囲・Codex 敵対的レビュー 1 件反映で確定）・task_09c 起票（b58d22cb）→ task_09c 実装（f8a976a1）。
  実装: codex-delegating-implementer（サブエージェント 2 名・自己申告）。application の文言の判定候補は keyboard_layouts / save_plan_execution を対象外、他を対象。メイン修正 1 件（新規 tests_ui のテストデータに km1）。
  reviewer: 採用。低 3 件は任意のため保留（decisions.md 参照）。
  ユーザー: /away（戻る予定 未定）→ 目視待ちで終了処理。
result_files:
  - keyseq/presentation/ui_vars.py・views/full_view/hook_frame.py・views/compact_view/hook_frame.py
  - keyseq/presentation/dialogs/keymap_edit_dialog.py・keymap_switch_batch_dialog.py・action_control_fields.py・keyboard_window.py
  - keyseq/presentation/controllers/（key_capture・hook_controller・keymap_panel/keymap_panel_controller・keymap_add_flow・trigger_panel/trigger_row_edit・trigger_list_edit・effective_row_transition）
  - keyseq/application/（call_context・hotkey_service・keymap_switch_batch・sequence_steps・sequence_runner/input_acceptance）
  - tests_ui/test_modifier_display_scope.py・instructions/common/codebase_map.md
verified:
  compile: clean（Mac）
  tests_mac: 2057 件・失敗 6・エラー 10・skip 28（既知のみ）
  smoke_mac: pass
  tests_ui_mac: 15 本 1 本ずつ 失敗 0（test_modifier_display_scope はテストデータ修正後 7 件 OK）
  tests_windows: not_run
  visual_mac: task_09c 未実施

## next_action
- **【確認事項・ユーザー】(1) task_09c の Mac 実機目視**: キーマップ一覧の切替キー・停止 / トグルキーの欄（幅 8 文字で `left Command` が欠けて読めなくならないか）・キーマップ編集 / まとめて設定の切替キーの欄・キーボードUIのタイトル（編集中のキー名）・切替キーの重複のエラーで `Command` / `Option` と出るか。保存した設定（`config/config.json`）のキー名は `windows` / `alt` のままか。
- **【確認事項・ユーザー】(2) Caps Lock の未決**: Mac のキー表に `caps lock` が無い（常に素通し・暫定 57 §5.1）ため、既存の Caps Lock の切替キーが変わっていなくても「不明なキー名」で再検証を通らない（`tests_ui/test_prohibited_assign_keys_ui.py:166` が落ちる・正本 `features.md` §4.6「既存データは拒否しない・消さない」と食い違い）。案 A = Mac のキー表に `caps lock` を vk 57 の検証・送信だけの名前として足す / 案 B = Mac の仕様差として暫定 57 に記録しテストを Mac で skip。メインがコードを確かめて推奨を付けてからユーザーへ出す（未提示）。
- **(3) task_09・09a・09c の Windows 検証**: ユーザーが push → Windows 側で verifier（`.venv\Scripts\python.exe`・compile・`tests` 失敗 0・`tests_ui` 1 本ずつ失敗 0・smoke）→ 完了判定。
- 続き: task_09b（Mac 用のレイアウトの見本 us_mac / jis_mac）→ task_10 → task_11。実測（右 Option の keysym・テンキーの keycode）は測れたら暫定 57 §4.1 へ。

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
