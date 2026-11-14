# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-14T10:50:00
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.7・ユーザー確定済）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/continue-f5ebb7`（Mac の worktree・task_09 実装まで）。push はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 75 段階 ③。task_09a（Tk のキー取得・入力ソースの切替〔ctypes の TIS〕・Command / Option の表示）を Mac で実装・reviewer 修正して採用・修正反映済み。残り = Mac 実機目視 1〜5・Windows 検証（task_09 と合わせて）。未決 = Mac で既存の Caps Lock の切替キーが「不明なキー名」で再検証を通らない（tests_ui 1 件・仕様の判断待ち）。**
mode: implementing

## last_action
ts: 2026-11-14T10:50:00
who: main
summary: |
  実施: task_09 = `MacKeyboardBackend` の送信系（resolve_send の 4 段・印・自分の修飾の記録によるフラグ・物理 Shift の例外・identity_of・write_text・send_native_hotkey=False）・JIS の受信名（set_layout_key_ids・is_jis_layout）・テンキー 16 個・送信だけの別名・Shift の要る文字の表・MacWindowBackend.is_shift_down / is_ctrl_alt_win_down・layout_controller から id の集合を渡す 1 か所。codex-delegating-implementer（Sol + Luna 2 体・自己申告）。
  reviewer: 修正して採用。中 = write_text の分割単位（UTF-16 の 20 単位へ）・低 = 物理フラグ失敗ログを 1 回に → ユーザー判断「推奨どおり直す」→ codex-implementer。Codex の新テストの期待値誤り 1 件をメインが修正。codebase_map の os_backend 節を追従（メイン）。
result_files:
  - keyseq/infrastructure/os_backend/contracts.py・windows/keyboard_backend.py・macos/backend.py・event_tap.py・key_table.py
  - keyseq/presentation/controllers/layout_controller.py
  - tests/test_macos_key_table.py・test_macos_keyboard_backend.py・test_os_backend_contracts.py・test_layout_controller_scan_code.py
  - instructions/common/codebase_map.md
verified:
  compile: clean（Mac）
  tests_mac: 2031 件・失敗 6・エラー 10・skip 28（既知のみ・修正後の macOS 2 モジュール 53 件 OK はメインで再実行）
  smoke_mac: pass
  tests_ui_mac: test_app_ui_flows / test_task05_overlap_ui / test_keymap_list_operations が失敗 3 / 2 / 3 → 0（修正前に計測）
  tests_windows: 未実施
  visual_mac: 1〜6 すべて OK（2026-11-14・ユーザー）。テンキーの有無は報告どおり OK 扱い

## next_action
- （済）Mac 向けのレイアウト = 暫定 57 v0.8 §5.3.2・task_09b（task_09 の後）
- task_09 の残り: Windows 検証（verifier・tests・tests_ui を 1 本・smoke）→ 完了判定 → task_09a → task_09b
- task_08 のキュー版の実機確認（reviewer 参考 2 = 排出中のモーダル）は task_09 の目視でまとめて
- `test_keymap_list_operations` は task_09 の実装後に Mac で失敗 0（合成マウスイベントの 2 件も解消・原因はキー検証側だったと見られる）
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
