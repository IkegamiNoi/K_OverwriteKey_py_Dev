# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-24T08:45:00
phase: phase 79 = 同梱の C ライブラリのライセンス（2026-11-24 起票・暫定 60 v0.7 ユーザー確定済・起票元 idea_65）。次採番 = phase 80 / 暫定 61 / decisions 80 / 提案書 29 / idea 67
直前の完了フェーズ = **phase 78**（アクションの hotkey の保存時の検査と正規化・`decisions_archive/78_action_hotkey_save_validation.md`）
last_commit_location: `claude/windows-handoff-task-8a4d59`（worktree `windows-handoff-task-8a4d59`・Mac・task_02 完了 bdcf4cb6 + task_03 の下書き）。push / merge はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 79 task_02 完了・task_03 は完了判定前レビュー（deep 修正要・Codex needs-attention）の採否待ちで停止（2026-11-24）。**
mode: blocked
presence: away（戻る予定 未定）

## last_action
ts: 2026-11-24T08:45:00
who: main
summary: |
  task_02（Mac の行）完了（実機目視 OK・21 行・bdcf4cb6）。ユーザー判断: PSL（Tcl の cookiejar の Public Suffix List・MPL 2.0）は Tcl の行で扱う（task_01 の記録に追記）。
  task_03 を起票し、正本 features.md「バージョン情報・ライセンス」と codebase_map.md（件数 32 個 / 35 行）へ昇格の下書き（コミット済み・未レビュー確定）。
  完了判定前レビュー: deep-reviewer 修正要（条件 8 = Tcl/Tk の行の全文に libtommath・PSL・NanoSVG の表示が無い・Mac の Tk に NanoSVG・手順書に Tcl/Tk の静的コード無し ほか）/ codex-adversarial needs-attention（xxHash の表示漏れ・VC++ の停止解除の根拠・otool -t の手順・Zstandard の照合が黙って外れる）。主張はメインが実測で確認。採否の一覧 = phase 79 の task03_review_decisions.md。
result_files:
  - instructions/phase/79_bundled_c_library_licenses/task03_review_decisions.md（採否の一覧）
  - instructions/common/spec_detail/features.md・instructions/common/codebase_map.md（昇格の下書き）
  - instructions/phase/79_bundled_c_library_licenses/tasks/task_03_integration_and_promotion.md・task_01_windows_rows.md（PSL の追記）
verified:
  compile: clean
  tests: pass 2217（Mac・task_02 後）
  tests_ui: pass 25（test_help_window のみ）
  smoke: pass
  visual: OK（Mac 21 行）

## next_action
- **【ユーザー判断待ち】`instructions/phase/79_bundled_c_library_licenses/task03_review_decisions.md` の A-1〜A-3 の採否と B の了承**（推奨 = A-1(a) Tcl/Tk の全文を OS ごとに分けて表示を足す・A-2(a) VC++ は今の扱いを維持して残存リスクを記録・A-3 記録の置き場所を手順書に書く・B 4〜9 は採用）。
- 推奨どおりなら task_02a（Mac: tcl_macos.txt / tk_macos.txt・NanoSVG の記録・手順書の otool -tX と Tcl/Tk の静的コード）と task_01a（Windows: zstandard.txt に xxHash・Zstandard の照合を必須に・libtommath の表示・PSL の有無・テストの流し直しと目視）を起票 → task_03 を再開（暫定 60 v0.8・凍結・decisions_archive/79・current.md・idea_65 を INDEX_done へ・refactor_check = 不要の見込み〔phase 79 の Python の変更は tests/test_third_party.py の +42 行だけ〕）。
- task の連続実行はユーザー許可済（2026-11-24・phase 79）。
- **取り込み前の設定の件**: このブランチを起動したセッションは取り込み前の旧フックで動いていた（旧 UserPromptSubmit が task_NN の指示をブロック・旧 Stop が旧パスで /save_state を繰り返し要求）。メインのリポジトリ（main・704c6a16）の settings.json も旧のまま。**取り込みを main へ merge してから新しいセッションで確認する**: `disable-model-invocation` の 5 スキルが Skill 一覧に出ないこと・UserPromptSubmit が状態の注入になること・worktree のセッションで SessionStart の branch が worktree 側になること（push / merge はユーザー）。
- ブランチ `claude/template-import-idea-65-7e55e5`（template 取り込み + phase 79）・`claude/idea-03-ec8eea`（phase 78）・`claude/sample-folder-save-path-d3cd34`・`claude/click-timing-issue-79de93` の push / merge はユーザー。保留中: R4・idea_37。

## blockers
- なし。注記: **Mac で tests_ui を通しで走らせない**（モーダルで止まるモジュールがある・モジュール指定で流す。verifier にも明記）。Mac の python は `../../../.venv/bin/python`
- **【解消・2026-11-22】Codex の書き込み実行（2026-10-14 以降の不具合）**: ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `elevated` に戻し、Codex 0.171.0 で書き込みのテスト OK（`setup refresh ... errors=[]`）。再発したら `unelevated` に変えて回避（ユーザー操作・常駐の broker〔`app-server-broker.mjs`〕と app-server を止めないと効かない）

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **phase 78 の要点**: hotkey のアクションの OK は `action_dialog.py` の `on_ok` で `accepts_key_name`（他方 OS の修飾キー・phase 75 の文言）→ `self.parent.validate_hotkey`（`App.validate_hotkey` → `HotkeyService.validate`）→ 正規化値を保存。tests_ui の fake root で ActionDialog の hotkey の OK を呼ぶなら `root.validate_hotkey` を設定する（`test_action_dialog_key_hold.py` / `labels.py` の setUp）。
- **phase 77 の要点**: 初回のサンプルは `config/user/`（`sample_install.SAMPLE_DIR = "user"`）。構成セットが無いときは `_find_conflicting_children` が `save_plan_execution.preview_child_payloads` と既存の子を照合（lexists・sort_keys の json 文字列比較）。旧 `config/sample/` は書かない・孤児の掃除の経路 5 で参照だけ残す。symlink のテストは Windows の特権不足で skip（Mac で一度流すと確証）。
- **phase 76 の要点**: 実効値（値が入った名前は値・それ以外は開始値・それも無ければ 0）は `keyseq/application/counter_values.py`（`CounterValues(dict)`・`counter_value`・`counter_start`・`counter_display_values`・`counter_starts_of`）に 1 か所。保留は `(op, name, amount)`。開始値は構成セットの `counter_starts`（`domain/sequence_control.normalize_counter_starts`）→ `App._sync_control_vars_from_data` で `AppState.set_counter_starts`。ダイアログは開始値を `_dialog_counter_start` で返し、`action_edit._apply_counter_start_result` が行の追加・置換の成立後に書く。新しい種類 `counter_text` は `ActionExecutor.execute` の 1 分岐。
- **Codex の傾向（phase 76 で実測）**: テストを書き漏らす（task_01・04 は 2 回目の依頼で追加）・既存テストの途中に新しいテストを差し込む（task_01）・タスク定義の一部（通知のラベル）を落とす（task_03）。依頼文に「既存テストの途中に差し込まない」を書き、差分を直読みしてから verifier へ。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **画面の文言（phase 72 以降）**: 新しい文言は `keyseq/shared/i18n/locales/ja.json` と `en.json` の両方にキーを足し、ソースに日本語を書かない（静的テスト）。`tr` はモジュール定数・import 時に評価しない。`App(` を作る / 文言を assert する新しいテストモジュールは import 直後に `fix_language("ja")`。英語は `ui_terms.md` §2・§3（E1〜E7）に従う。
- tests_ui の窓の大きさのテスト（`test_compact_window.py:298`・`test_pane_window_width_persistence.py:236,275` の `pending`）が負荷で落ちることがある。**tests_ui の App() は worktree の `config/config.json`（ユーザーの手元の設定・gitignore）を読む**ので結果が手元の設定に左右される。Codex は python を実行できずテスト修正が手探りになる → 失敗はメインがトレースを読んで原因を絞ってから委任する。
- **`__version__`** はユーザーが直接またはユーザーの指示でだけ変更する（Claude が独断で上げない）。
- **Codex は Python で既存ファイルを編集しようとして失敗することがある** → 依頼文に「apply_patch で編集・Python を使わない」と書く（phase 71）。
- **素の `python` を Bash で呼ばない**（必ず `..\..\..\.venv\Scripts\python.exe`）。Bash の heredoc の前に `cat > file` を単独で書かない（stdin 待ちでハングする）。
- **Codex は互換の工夫・テストの期待値の推測を足すことがある**。差分を直読みしてから verifier / reviewer へ。Codex は LF を混ぜることがある（コミットは git が正規化）。
- `tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・current.md「テスト負債」）。
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜46・48〜59）の条項を実装の根拠に引かない（正本 `spec_detail/` が正）。
- **【Codex のプロセス】** companion は作業フォルダごとに `app-server-broker.mjs serve` を常駐させ、`codex app-server` は呼び出し後も残る。worktree を多く使うと codex.exe が溜まる。`codex-delegating-implementer` は 180 秒を超えるとバックグラウンドへ移る → 出力ファイルの更新時刻で進み具合を見る。
- **【罠・phase 58】ttk.LabelFrame の `labelwidget` に既定の ttk.Label を使うと枠の要求高さが 4px 増える**（`style="TLabelframe.Label"` なら同じ）
