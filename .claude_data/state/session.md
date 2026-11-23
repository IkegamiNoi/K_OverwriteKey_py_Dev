# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-23T17:00:00
phase: phase 79 = 同梱の C ライブラリのライセンス（2026-11-24 起票・暫定 60 v0.6 確定済・起票元 idea_65）。次採番 = phase 80 / 暫定 61 / decisions 80 / 提案書 29 / idea 67
直前の完了フェーズ = **phase 78**（アクションの hotkey の保存時の検査と正規化・`decisions_archive/78_action_hotkey_save_validation.md`）
last_commit_location: `claude/idea-03-ec8eea`（worktree `idea-03-ec8eea`・phase 78 完了）。push / merge はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 79 起票（2026-11-24）。** 配布物に入る C ライブラリを第三者ライセンスの表に OS ごとの行で載せる。次 = task_01（Windows の行）の起票。
mode: idle

## last_action
ts: 2026-11-23T17:00:00
who: main
summary: |
  phase 78 完了。実機目視 OK（ユーザー・Windows）。task_03: decisions_archive/78 作成・decisions.md 索引・current.md 完了記載（次採番 phase 79 / decisions 79）・idea_03 を INDEX → INDEX_done・refactor_check 不要（action_dialog.py 670 行 +5・M2〜M6 該当なし）。
  完了判定前レビューの採否（ユーザー）: ラベルだけの編集も検査 = A（正本 1 文）・Codex 1（Mac の option+comma）は除外し idea_45 へ・deep 2・3・4 テスト補強 = task_03a・deep 7（features.md）保留。
result_files:
  - .claude_data/state/decisions_archive/78_action_hotkey_save_validation.md
  - .claude_data/state/decisions.md
  - instructions/phase/current.md
  - instructions/backlog/INDEX.md
  - instructions/backlog/INDEX_done.md
  - instructions/phase/78_action_hotkey_save_validation/phase.md
verified:
  compile: clean
  tests: pass 2278（skip 9）
  tests_ui: pass 1319（統合）/ 35（task_03a 後の action_dialog_key_hold + labels）
  smoke: pass
  visual: OK（ユーザー実機確認・2026-11-23）

## next_action
- phase 78 は完了。ブランチ `claude/idea-03-ec8eea` の push / merge はユーザー。次フェーズはユーザー判断（`/phase_start`）。
- **idea_65（同梱の C ライブラリのライセンス）に着手（2026-11-23・ブランチ `claude/template-import-idea-65-7e55e5`）**: ユーザー判断 = 案 A（ライブラリごとに third_party.json の行と全文の txt・OS 列で出し分け）・暫定仕様先行（暫定 60 → phase 79）。範囲 = 静的に取り込まれた物〔bzip2・xz・zstd・mpdecimal・expat〕も含める（ユーザー確定）。暫定 60 v0.1 を起票（`instructions/history/60_bundled_c_library_licenses.md`・未コミット・Windows の同梱 DLL と版の実測を §1 に記録・§6 Q1〜Q4 は未確定）・INDEX の idea_65 を「着手」へ。deep-reviewer「修正して採用」1〜13 を実測で裏取りして v0.2 に反映（python.txt に OpenSSL の Apache-2.0 全文あり・zlib-ng は python314.dll に組込・zlib1.dll は tcl86t.dll 用・python314.dll に mimalloc / HACL*）。§6 Q1〜Q5 はユーザー確定（提案どおり・v0.3）。Codex 敵対的レビュー = needs-attention 4 件（high: Q5 の全文で HACL* の表示が漏れる・最終配布物の棚卸しが条件に無い / medium: 版テストは配布物の版違いを検出できない〔mpdecimal は _decimal で〕・VC++ の再頒布条件の記録）。主張は実測で裏取り済。採否案（1・2・4 採用・3 一部採用・次の手順の「— の制約を外す」は除外）をユーザー承認 → v0.4 に反映（§4.1 配布物の棚卸し・Q5 の全文に license.rst に無い組み込みコード〔HACL* 必須〕・mpdecimal は _decimal・VC++ の入手元と条件の記録・§7 に 8〜10）。Codex 再レビュー = needs-attention 3 件（拡張モジュール内の HACL*・版の根拠を配布物に結びつける・VC++ の条件を満たす根拠）→ 全件採用で v0.5（ユーザー 2026-11-24）。暫定 60 v0.6 ユーザー確定（2026-11-24）→ phase 79 起票（`instructions/phase/79_bundled_c_library_licenses/phase.md`・current.md / INDEX 更新）。phase.md の整合チェック = reviewer 修正して採用（task_01 に VC++ の条件を満たす根拠と出荷停止・一覧の期待値を追記）。task_01 起票（`tasks/task_01_windows_rows.md`・棚卸しの記録・全文 10 ファイルをメインが配置〔未コミット〕・VC++ は未解決 = Windows 版は出荷停止でユーザー判断待ち）→ codex-implementer（Luna high）で json / tests / packaging README を実装 → verifier pass（tests 2279 / test_help_window 25 / smoke / test_third_party 8）→ reviewer 採用。残り = ライセンスの窓の実機目視（25 行）と VC++ の判断（ユーザー）。task_02 は Mac で実施。task の連続実行はユーザー許可済（2026-11-24） → `/phase_start`（phase 79）。実測: Windows の python.txt に VC++ ランタイムの条件・bzip2・libffi・Zstandard の節はあるが OpenSSL・zlib・xz・mpdecimal・expat は無い / python_macos.txt に第三者の節は無い。- 別件: ブランチ `claude/sample-folder-save-path-d3cd34`・`claude/click-timing-issue-79de93` の push / merge はユーザー。保留中: R4・idea_37。
- **template の取り込み（完了・2026-11-23）**: template 7791fa7..1a99527 を取込済（skills 移行・save_mode の model コマンド・full_hooks 登録解除・フック修正 ほか・last_pulled = 1a99527）。template 側は 1a99527・5c41b38・6086db4 とも main にマージ済み（84a48a4）。Operation_check でファイル面の確認済（skills 15 個・5 つに disable-model-invocation・settings.json = auto_save_and_use_task_file・フックのコマンドを手で実行して出力 OK）。**残りの確認（取り込み後のブランチで開いた新しいセッションで）**: `disable-model-invocation` の 5 つが Claude の Skill 一覧から消えていること・UserPromptSubmit の状態注入が会話に出ること・worktree のセッションで SessionStart の branch が worktree 側になること（取り込み前のセッションでは main の handoff が注入された）。2026-11-24: 取り込み前に起動したセッションで、旧 UserPromptSubmit（task_NN に反応する prompt 型）が task_01 の指示をブロック。原因 = 起動時に読んだ旧設定、かつメインのリポジトリ（main・704c6a16）の settings.json も旧のまま。取り込みを main へ merge してから新しいセッションで確認する（push / merge はユーザー）。

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
