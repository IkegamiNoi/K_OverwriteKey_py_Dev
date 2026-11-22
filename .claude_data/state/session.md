# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-22T21:00:00
phase: instructions/phase/75_mac_support（暫定 57 v0.25 は凍結・正本反映済み）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 29 / idea 67。phase 75 の判断の記録は `decisions_archive/75_mac_support.md` に追記する（decisions.md から移し済み）
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/windows-support-continuation-f235f4`（Windows の worktree・Mac の task_13b まで取り込み済み + task_13c〜15）。push はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 75。task_14（正本反映）完了（2026-11-22）= 暫定 57 凍結・正本昇格・deep-reviewer 指摘反映・Codex 敵対的の 5 件は idea_66・ヘルプ 2 文を両 OS に。task_15（提案書 28 のリファクタ）は Windows で実装・検証 pass・reviewer 採用。Windows 目視 OK（Win+D の白い窓は idea_61 の既存の症状）。残り = Mac の作業時に Mac の確認（task_15 の確認 3）で phase 75 を閉じる（その後 current.md を完了に・decisions.md の索引の行を完了に）。**
mode: completed

## last_action
ts: 2026-11-22T21:30:00
who: main
summary: |
  実施（Windows の worktree）: Windows 検証 pass（tests 2219・tests_ui 1300・smoke・requirements-build の版一致）→ task_13c（Windows の .spec の sources を Mac と同じに・codex-implementer・reviewer 採用）→ C ライブラリを idea_65 → テンキーのサンプルの Windows 実機 OK → task_14（正本反映・暫定 57 v0.25 凍結・architecture §3.6 / key_input §7.9 / features §4.8 を新設・decisions_archive/75）→ refactor_check 推奨 = 提案書 28 → deep-reviewer 修正要→反映 / Codex 敵対的 needs-attention → task_15（提案書 28 のリファクタ・codex-delegating-implementer・reviewer 採用）→ Windows 目視 OK。
  ユーザー判断: ヘルプの 2 文を両 OS に（カーソルグリッドの素通し・左右の修飾キー）/ Codex の 5 件は idea_66 / 提案書 28 は phase 75 の追加タスク task_15。
result_files:
  - instructions/common/spec_detail/（architecture・key_input・features・data_schema・ui_terms・nonfunctional）・codebase_map・app_overview・README・.claude/rules/python_rules.md
  - instructions/history/57_mac_support.md（凍結）・instructions/phase/75_mac_support/tasks/（task_13c・14・15）・instructions/modified_proposal/28_refactor_mac_support.md・instructions/backlog/（idea_65・66）
  - keyseq/infrastructure/os_backend/macos/（backend.py を分割 → keyboard_backend・mouse_backend・window_backend・tk_key_translator・ime_backend・app_identity）・keyseq/presentation/modal.py・packaging/windows/keyseq.spec
verified:
  tests_windows: compile clean / tests 2219 失敗 0 skip 7 / tests_ui 1300 OK / smoke OK（task_15 後）
  tests_mac: not_run（task_15 の分割後は未実行）
  visual_windows: task_15 OK（Win+D の白い窓は idea_61 の既存の症状）

## next_action
- **Mac で task_15 の確認 3**（Mac の worktree へこのブランチ `claude/windows-support-continuation-f235f4` を取り込むのはユーザー〔push / merge はユーザー〕）: `../../../.venv/bin/python` で compileall / `tests` 全件 / `tests_ui` の `test_minimize_grab_custody`・`test_modal_grab`・`test_nested_modal_grab`（モジュール指定・通しで走らせない）/ smoke。実機目視 = フック開始・置換・メニュー・ダイアログを開いたままの最小化と戻し（ユーザー）。
- pass したら phase 75 を閉じる: `instructions/phase/current.md` の「アクティブなフェーズ」を「なし」・直前の完了フェーズ = phase 75・次採番節に「phase 75 は完了」の行 / `decisions.md` の索引の 75 の行を完了に / phase.md の task_15 を完了に / `decisions_archive/75` に追記 / コミット。
- 保留中: 2 枚目のモニタの目視・中クリック（ユーザー判断）。idea_45・59〜66 は検討段階。

## blockers
- **Mac で tests_ui を通しで走らせない**（モーダルで止まるモジュールがある・モジュール指定で流す。verifier にも明記）。Mac の python は `../../../.venv/bin/python`
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
