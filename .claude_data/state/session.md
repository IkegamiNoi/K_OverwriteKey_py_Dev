# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-13T12:00:00
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.6・ユーザー確定済）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/task-06-progression-a047bd`（Mac の worktree `task-06-progression-a047bd`）。push はユーザー。main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 75 段階 ③ 着手。暫定 57 v0.7（§5.1.1 ディスパッチャの契約・敵対的レビュー 3 回）を確定し、task_08 を分割して task_08（ディスパッチャ・OS 非依存）を起票済み。次は task_08 の実装（Windows で可）。**
mode: implementing

## last_action
ts: 2026-11-13T12:00:00
who: main
summary: |
  2026-11-13: task_08 起票前に暫定 57 を v0.7 へ改訂（§5.1.1 ディスパッチャの契約）。Codex 敵対的レビュー 3 回の指摘をすべて推奨どおり反映して確定。phase.md で task_08 を 08（ディスパッチャ）/ 08b（CGEventTap）に分割し、task_08 を起票。
  2026-11-13（Windows）: 段階 ② の区切り M1 = Windows の標準検証 4 種（compile clean・tests 1997 / 0 / 0 / skip 7・tests_ui 1271 / 0 / 0・smoke OK・verifier）と目視 6 項目（既定の高さ 820・プリセットとサンプル・ツールチップとフォント・ペインの初期幅・一覧の Control+/ と Control+Shift+Home の封じ・右クリック）すべて OK（ユーザー）。
  2026-11-11〜12 のコミット: task_05c・06（3878868）/ task_07c（9c4c098・Mac でペインの初期幅が適用されない）/ task_07（3598823・Mac のテストの基準線 `instructions/phase/75_mac_support/mac_test_baseline.md`）/ fa60f50（§7 の skip の範囲・task_07d 起票）/ task_07b（d26fac0・OS ごとの既定プリセット）。
  task_07d（コミット済み・目視 OK）: アプリ = ①コンパクト表示の trigger_panes に <Map> でも schedule_layout ②ツールチップは表示後に -topmost を再設定 ③起動時の既定の高さ = max(820, 3 枠が収まる高さ)・画面の高さ（wm_maxsize）で頭打ち ④aqua ではキーの文字を Helvetica。テスト = 窓の幅・既定のペイン幅・省略表示を Windows のフォント非依存に。codex-delegating-implementer・verifier（compile clean / tests 1939・失敗 6・エラー 10・skip 28 = 基準線どおり / smoke OK / 対象 tests_ui 7 モジュール 失敗 0）・reviewer 修正して採用（R1 = 上限を画面の高さに文書統一・R2 = test_full_view_panes の独立検証を復元 → 単独で OK）。
result_files:
  - instructions/phase/75_mac_support/tasks/task_07d_tk9_aqua_metrics.md・mac_test_baseline.md
  - keyseq/presentation/（compact_pane_layout・hover_tooltip・pane_measure・pane_layout_controller・tk_platform・keyboard_window）・tests/・tests_ui/
verified:
  mac_tests: 1939 件・失敗 6・エラー 10・skip 28（基準線どおり）
  mac_tests_ui: task_07d の対象 7 モジュール 失敗 0・pane / compact / keyboard 系は基準線どおり
  mac_visual: task_07d ①〜④ OK（ユーザー・④ はダイアログの「?」のツールチップ）

- 次: task_08 の実装（`instructions/phase/75_mac_support/tasks/task_08_hook_dispatcher.md`・codex 実装 → verifier → reviewer → Windows 目視）→ task_08b（CGEventTap・Mac。未起票。起票時に受信側の vk の表〔§5.3 受信・§5.3.1〕を 08b に含めるか task_09 のままかを決める）
- 次: 段階 ③ task_08（CGEventTap のフック・修飾キー・配送の滞留 §5.1・KeyCaptureHook の after をディスパッチャへ〔区切り M1〕・ディスパッチャの型改訂〔M2〕・§4.1 の未実測の実測〔L2〕）。task_08 は未起票 → `/task_new` から。実装・実測は Mac（M1 の Windows 検証は 2026-11-13 に完了）
- `test_keymap_list_operations` の合成マウスイベントの 2 件は要調査（task_09 で）
- task_09 でキーボードUIの右クリックによる割り当てのクリアを目視（task_05c の残り）
- JIS の実測（§5.3.1 の文書値の確定）は JIS キーボードを用意できたとき
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
