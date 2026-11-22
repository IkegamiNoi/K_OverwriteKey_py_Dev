# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-22T23:00:00
phase: なし（phase 75 は 2026-11-22 完了）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 29 / idea 67
直前の完了フェーズ = **phase 75**（macOS 対応・`decisions_archive/75_mac_support.md`）
last_commit_location: `claude/task-15-360298`（Mac の worktree・phase 75 の完了コミットまで）。push / merge はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **フェーズなし。phase 75（macOS 対応）は 2026-11-22 完了（task_15 の Mac の確認 3 = 自動テスト pass・実機目視 OK）。次は新フェーズの起票待ち（ユーザー判断）。**
mode: completed

## last_action
ts: 2026-11-22T22:30:00
who: main
summary: |
  実施（Mac の worktree `claude/task-15-360298`）: 次タスク = task_15 の確認 3 と current.md・task_15_refactor.md で確認 → verifier で Mac の確認 3 の自動テストを実行 → 4 項目 pass（基準線 mac_test_baseline.md:37 と一致を実測）。
  ユーザー判断: 確認 3 の実行を承認・Mac の実機目視 OK → task_15 完了・phase 75 を閉じた（phase.md・current.md・decisions.md の索引・decisions_archive/75 を更新）。
result_files:
  - .claude_data/state/（session.md・decisions.md・decisions_archive/75_mac_support.md）・instructions/phase/（current.md・75_mac_support/phase.md）（コード変更なし）
verified:
  tests_mac: compile clean / tests 2157 失敗 0 エラー 0 skip 32 / tests_ui 3 モジュール（minimize_grab_custody・modal_grab・nested_modal_grab）81 OK / smoke OK（task_15 後）
  tests_windows: compile clean / tests 2219 失敗 0 skip 7 / tests_ui 1300 OK / smoke OK（task_15 後）
  visual_windows: task_15 OK
  visual_mac: task_15 OK（ユーザー）

## next_action
- 新フェーズの起票（`/phase_start`）はユーザーの指示待ち。候補 = 検討段階の idea（idea_45・59〜66）・保留の提案書 26 / 27。
- このブランチ `claude/task-15-360298` の push / merge はユーザー。
- 保留中: 2 枚目のモニタの目視・中クリック（ユーザー判断）。

## blockers
- なし。注記: **Mac で tests_ui を通しで走らせない**（モーダルで止まるモジュールがある・モジュール指定で流す。verifier にも明記）。Mac の python は `../../../.venv/bin/python`
- **【解消・2026-11-22】Codex の書き込み実行（2026-10-14 以降の不具合）**: ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `elevated` に戻し、Codex 0.171.0 で書き込みのテスト OK（`setup refresh ... errors=[]`）。再発したら `unelevated` に変えて回避（ユーザー操作・常駐の broker〔`app-server-broker.mjs`〕と app-server を止めないと効かない）

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
