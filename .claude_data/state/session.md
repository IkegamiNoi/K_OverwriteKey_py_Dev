# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-04T02:00:00
phase: instructions/phase/72_multilingual_ui（**アクティブ** = 画面の文言の多言語対応・暫定 55 v0.7 ユーザー確定済・decisions 72）。次採番 = phase 73 / 暫定 56 / decisions 73 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 71**（タスクバーのアイコン・`decisions_archive/71_taskbar_status_icon.md`）
last_commit_location: `claude/ui-text-length-english-style-f5ba4e`（phase 72 task_11b〜11d）。それ以前の phase 72 は `claude/multilingual-support-ff44eb`。phase 71 一式は `claude/taskbar-app-status-indicator-f73d28` にもあり、main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: away（戻る予定 未定）
focus: **phase 72 進行中（task_01〜11・11a〜11d 完了・task_12・11c の実機目視 OK。残り = task_11d の実機目視 → task_12 の正本反映）。** 日英の切り替え・全層の文言のキー化・en.json・help_en.json・静的検査・二次レビューの採用分・英語の文言の見直し（機能名の大文字・記録ボタンの短縮・JIS の特殊キーを例へ）・メニューの項目名「Language」と切り替え後の「今すぐ再起動」・一覧の行頭の印の統一（`[click]` 等）まで入った。
mode: blocked

## last_action
ts: 2026-11-04T02:00:00
who: main
summary: |
  ユーザー報告（2026-11-04）: task_11c の実機目視は問題なし。追加の判断 = 出力シーケンスの一覧の行頭の印を全言語共通の英語の短い名前に統一（メイン推奨は言語ごとの表示名だったがユーザーは英語を選択）→ 暫定 55 v0.7（§8 Q6）。
  task_11d: codex-implementer（2 回 + テスト追加 1 回）。mouse_click → `[click]`・mouse_scroll → `[scroll]`・key_hold → `[press]` / `[release]`（domain/config.py の ACTION_LIST_TAGS・key_hold.py・mouse_scroll.py・省略表示 action_list_rendering.py）・言語ファイルから印を外し、未使用の domain.key_hold.display.down / up を削除。
  reviewer 修正して採用 → 英語でも印が共通のテストを追加（lambda の引数名の衝突 1 行はメインで修正）。ユーザーは不在モード（2026-11-04 00:53〜・戻り未定）。
result_files:
  - keyseq/domain/config.py / keyseq/domain/key_hold.py / keyseq/domain/mouse_scroll.py / keyseq/presentation/controllers/action_list_rendering.py / ja.json / en.json
  - tests/test_domain_config.py / tests/test_key_hold.py / tests/test_mouse_scroll.py / tests_ui/test_action_dialog_labels.py / tests_ui/test_action_list_rendering.py / tests_ui/test_key_hold_presentation.py
  - instructions/history/55_multilingual_ui.md / instructions/phase/72_multilingual_ui/phase.md / tasks/task_11d_action_list_tags.md / .claude_data/state/decisions.md
verified:
  compile: pass
  tests: pass（1909・skip 7・テスト追加後に再実行）
  tests_ui: pass（1238・テスト追加前の実装で実行。その後の変更は tests/ の 2 ファイルのみ）
  smoke: pass

## next_action
- **【ユーザー確認・不在中に到達】task_11d の実機目視**: 出力シーケンスの一覧（詳細表示・省略表示の両方）で、マウスのクリックが `[click]`・スクロールが `[scroll]`・押下 / 解放が `[press]` / `[release]` になり、日本語と英語で同じ印か / 印の後ろ（向き・（生）・（リピート）・ボタン名）は言語ごとの文言のままか / 他の印（`[hotkey]`・`[text]`・`[loop]` 等）は変わっていないか。結果をメインへ報告
- 目視 OK を受けて task_12 の正本反映: 暫定 55 §11 + `tasks/task_11_integration.md` の「正本反映で足す項目」+ D2・D3・D4 + v0.5（E1・E7）・v0.6（項目名・再起動）・v0.7（一覧の印。features.md §4.2・§4.6 の `[スクロール]`・`[押す]` 等の記述も直す）→ 暫定 55 凍結・decisions_archive/72・current.md 完了記載・/refactor_check
- main へのマージはユーザー（PR は作らない）

## blockers
- **【回避中】Codex の書き込み実行（2026-10-14 18:24 以降の不具合）**: Codex の更新（0.162.x・cua_node runtime a9ba…・17:22〜18:25）以降、`~/.codex/.sandbox/sandbox.2026-10-14.log` に `setup refresh had errors`（node_repl.exe の ACL 更新が「別のプロセスが使用中」で失敗）。読み取り専用（レビュー・調査）は通る。再起動では直らない。**2026-10-15 ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `unelevated` に変更 → 常駐の broker・app-server を止めて再実行で書き込み可**。Codex の更新で直ったら `elevated` に戻す（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **phase 72**: `App(` を作る / 画面の文言を assert する新しいテストモジュールは import 直後に `fix_language("ja")` を書く（無いと `ui_language` 未設定の環境で英語になり落ちる・静的テストが検出）。`tr` はモジュール定数・import 時に評価しない。
- **phase 71**: タスクバーのアイコンは AppUserModelID（`main.py`）が無いと出ない。`App()` を直接作る tests_ui / smoke では設定されない。保留 2 件は current.md「別タスク化候補」。
- **`__version__`** はユーザーが直接またはユーザーの指示でだけ変更する（Claude が独断で上げない）。
- **Codex は Python で既存ファイルを編集しようとして失敗することがある** → 依頼文に「apply_patch で編集・Python を使わない」と書く（phase 71）。
- **素の `python` を Bash で呼ばない**（必ず `..\..\..\.venv\Scripts\python.exe`）。Bash の heredoc の前に `cat > file` を単独で書かない（stdin 待ちでハングする）。
- **Codex は互換の工夫・テストの期待値の推測を足すことがある**。差分を直読みしてから verifier / reviewer へ。Codex は LF を混ぜることがある（コミットは git が正規化）。
- カーソルグリッド（旧称「画面の枠」・phase 56・57）の地図 = `codebase_map.md`「カーソルグリッド（phase 56・57）」。振り分けは `suppress_keys` 1 本（`screen_grid_session._publish_snapshot`）/ 操作キーは `domain/screen_grid/ops.py`。
- **【罠・phase 57 で実証】Windows の Tk で位置の反映の保留中に `wm_attributes("-topmost", True)` を呼ぶと窓が `0,0` へ戻る**（`geometry` の直後に `update_idletasks()`）。**Tk の測り直しは after_idle だと配置の計算より先に走ることがある**（測る前に `update_idletasks()`）・`<Configure>` で configure し返すと無限ループになり得る（値が変わったときだけ・結び付けは 1 つ）。
- **プロセスは pyautogui の import でシステム DPI 対応**（`.venv/Lib/site-packages/pyautogui/_pyautogui_win.py:17`）。検証は本番の起動経路で
- `tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・current.md「テスト負債」）。
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜41）の条項を実装の根拠に引かない。
- **【Codex のプロセス・2026-10-14 実測】** companion は作業フォルダ（cwd）ごとに `app-server-broker.mjs serve` を常駐させ、その下の `codex app-server`（+ sandbox の runner・node）は**呼び出し後も残る（再利用のための設計）**。
  worktree ごとに 1 組ずつ増えるため、worktree を多く使うと codex.exe が溜まる。Codex デスクトップアプリ（ChatGPT.exe）配下の codex.exe は別物。2026-10-14 の不調はプロセスの溜まりではなく Codex の更新が原因（blockers 参照・再起動では直らない）
- **【罠・phase 58 task_02 で実測】ttk.LabelFrame の `labelwidget` に既定の ttk.Label を使うと枠の要求高さが 4px 増える**（vista・58 → 62px。矢印の字形とは無関係）。`style="TLabelframe.Label"` なら元と同じ 58px・同じ見た目
