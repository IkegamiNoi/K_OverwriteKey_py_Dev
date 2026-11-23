# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-24T12:00:00
phase: phase 79 = 同梱の C ライブラリのライセンス（2026-11-24 起票・暫定 60 v0.7 ユーザー確定済・起票元 idea_65）。次採番 = phase 80 / 暫定 61 / decisions 80 / 提案書 29 / idea 67
直前の完了フェーズ = **phase 78**（アクションの hotkey の保存時の検査と正規化・`decisions_archive/78_action_hotkey_save_validation.md`）
last_commit_location: `claude/template-import-idea-65-7e55e5`（worktree `template-import-idea-65-7e55e5`・Operation_check 733ac0f9 から早送り・template 取り込み + phase 79 task_01 完了まで）。push / merge はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 79 task_01 完了（2026-11-24）。** Windows の C ライブラリ 10 行を第三者ライセンスの表に追加。次 = task_02（Mac の行）を **Mac のセッション**で起票・実施。
mode: idle

## last_action
ts: 2026-11-24T12:00:00
who: main
summary: |
  task_01（Windows の行）完了。third_party.json に 10 行（bzip2・CPython incorporated software〔license.rst の節 + HACL*〕・expat・libffi・mpdecimal・OpenSSL・xz・zlib・zlib-ng・Zstandard・すべて platforms win32）と全文 10 ファイル（上流の各版のライセンスファイルの写し・メインが配置）・tests/test_third_party.py（C ライブラリの版の照合 = OpenSSL / Zstandard / _decimal / expat・PyPI 照合から除外・windows_names）・packaging/README.md の棚卸しの手順（codex-implementer〔Luna high〕・reviewer 採用）。
  棚卸しの記録は task_01 のタスク定義の末尾（DLL・pyd 26 個が CPython のインストールとハッシュ一致・版の根拠 = CPython v3.14.6 の PCbuild/get_externals.bat / pythoncore.vcxproj）。VC++ ランタイムはユーザー判断で packaging/README_dist.txt（日英）に一文を追記（暫定 60 v0.7）。
result_files:
  - keyseq/presentation/help/content/third_party/third_party.json（+ 全文 10 ファイル）
  - tests/test_third_party.py
  - packaging/README.md・packaging/README_dist.txt
  - instructions/history/60_bundled_c_library_licenses.md（v0.7）
  - instructions/phase/79_bundled_c_library_licenses/phase.md・tasks/task_01_windows_rows.md
verified:
  compile: clean
  tests: pass 2279（skip 9）
  tests_ui: pass 25（test_help_window のみ）
  smoke: pass
  visual: OK（ライセンスの窓 25 行・ユーザー実機確認・2026-11-24）

## next_action
- **phase 79 task_02（Mac の行）を Mac で起票・実施**: 暫定 60 §4.1 の棚卸しを Mac のビルド（`keyseq.app`）で行う。確かめること = 同梱の dylib（OpenSSL・liblzma・libmpdec・libtommath ほか）と静的に入る物・各版（配布物から読んだ値かビルドの入力で・`.venv` の値だけを根拠にしない）・拡張モジュール（`_sha2` 等）の中の HACL* の有無（あれば表示必須）・libtommath の出所（Homebrew の tcl-tk の依存か）・tcllib 等の Tcl の拡張。Mac の行（platforms darwin・Mac の Python の行の直後に大文字小文字を無視した ABC 順）・全文・`mac_names`・`_NON_PYPI_NAMES` への Mac の名前の追加・`packaging/README.md` の macOS 節。手本 = Windows の task_01（`tasks/task_01_windows_rows.md` の棚卸しの記録）。→ task_03（統合確認・正本 features.md への昇格・暫定 60 の凍結・decisions_archive/79・current.md・idea_65 を INDEX_done へ・refactor_check）。
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
