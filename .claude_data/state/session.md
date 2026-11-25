# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-25T15:00:00
phase: instructions/phase/81_uppercase_replacement_target（キー置換の置換先に英字の大文字・暫定 61 v0.3 ユーザー確定済）。次採番 = phase 82 / 暫定 62 / decisions 82 / 提案書 29 / idea 69
直前の完了フェーズ = **phase 80**（Win+D から戻したときに入れ子のダイアログが白いまま・`decisions_archive/80_win_d_restore_blank_dialog.md`）
last_commit_location: `claude/idea-62-048dd1`（worktree `idea-62-048dd1`・Windows・phase 81 task_01）。push / merge はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 81 task_01 完了（置換先の大文字の保存・判定・送信）。次は task_02（キーボードUI の記録と表示）。タスクの連続実行はユーザー許可済（2026-11-25）。**
mode: implementing

## last_action
ts: 2026-11-25T15:00:00
who: main
summary: |
  task_01: domain に `normalize_mapping_target`（ASCII の大文字 1 文字だけ保つ）・読込 / set_mapping / 置換先の取得 / input_router で使用。Windows は大文字を小文字の名前で解き press/release も小文字・needs_shift は大文字なら真。macOS は大文字を小文字の VK の mac_shift。契約に `sent_modifiers_down`（macOS = 送信済みの修飾・Windows = (False, False)）・send_mapped_key は送信済みの修飾でも Shift を足さない。
  実装 = codex-implementer（Luna high・3 回。2 回目まではテストを途中で止めた → 小分けの依頼で完了）+ メイン修正 2 点（test_input_router の差し込み位置・test_config_service の期待値 2 か所）。
  実測: 従来の `_needs_shift('A')` = False（暫定 61 §1 の前提どおり）。reviewer: 実装は採用・テスト不足 2 点は既存の契約の自動照合と Windows のみのモジュールで満たしていると確認。
result_files:
  - keyseq/domain/config.py・keyseq/application/（keymap_service.py・input_router.py）・keyseq/infrastructure/input_gateway.py・keyseq/infrastructure/os_backend/（contracts.py・windows/keyboard_backend.py・macos/keyboard_backend.py）
  - tests/（test_domain_config.py・test_config_service.py・test_keymap_service.py・test_input_router.py・test_input_gateway_send.py・test_macos_keyboard_backend.py）
  - instructions/phase/81_uppercase_replacement_target/tasks/task_01_uppercase_target_save_and_send.md
verified:
  compile: clean
  tests: pass 2292（skip 9・Windows）
  smoke: pass

## next_action
- `/task_new` で task_02（キーボードUI の記録と表示）を起票: `keyboard_window.py:629` で Shift + 英字 1 文字 → 大文字・`:231` の表示を `normalize_mapping_target` に・大文字は `key_display_names` を引かない・`keymap_panel_controller.py:633` の正規化・tests_ui → codex-implementer → verifier（tests_ui は 1 本だけ・taskkill 禁止）→ reviewer。
- ブランチ `claude/idea-62-048dd1`（phase 81）ほかの push / merge はユーザー。取り込み前の設定の件（main へ merge 後に新しいセッションで確認）も継続。保留中: R4・idea_37。

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
