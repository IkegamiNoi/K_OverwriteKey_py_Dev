# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-01T19:13:00
phase: instructions/phase/72_multilingual_ui（**アクティブ** = 画面の文言の多言語対応・暫定 55 v0.3 ユーザー確定済・decisions 72）。次採番 = phase 73 / 暫定 56 / decisions 73 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 71**（タスクバーのアイコン・`decisions_archive/71_taskbar_status_icon.md`）
last_commit_location: `claude/multilingual-support-ff44eb`（phase 72）。phase 71 一式は `claude/taskbar-app-status-indicator-f73d28` にもあり、main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 72 進行中（task_01〜10 完了・task_11 の統合確認は済み・二次レビューの指摘の採否と task_12〔実機目視・正本反映〕はユーザー判断待ち）。** 日英の切り替え・全層の文言のキー化・en.json（915 キー）・help_en.json・日本語リテラルの静的検査まで入った。
mode: blocked
presence: away（戻る予定 未定）

## last_action
ts: 2026-11-01T19:13:00
who: main
summary: |
  task_07 確定（暫定 55 v0.4・E1 に「/ で並べた語はそれぞれ大文字」）→ task_08（en.json 915 キー・種類とマウスのボタンの表示名・test_i18n を全キーの検査へ・メインで英訳 5 か所と簡易表示の要約のボタン名を修正）→ task_09（help_en.json・65 項目）→ task_10（日本語リテラルの静的テスト・許可 34 件・メインで f-string の断片とネストの除外を修正）。いずれも reviewer 採用でコミット済み。
  task_11: 統合実測 = tests 1900 / tests_ui 1233 / smoke OK / 英語で起動（File / Settings / Help）。二次レビュー = codex-reviewer P2 1 件・deep-reviewer 修正して完了可（中 2・低 6）。指摘と推奨は `instructions/phase/72_multilingual_ui/tasks/task_11_integration.md` に整理（コードは未変更）。
result_files:
  - keyseq/shared/i18n/locales/{ja,en}.json / keyseq/presentation/dialogs/action_dialog.py / controllers/action_list_rendering.py / keyseq/domain/config.py
  - keyseq/presentation/help/content/help_en.json / tests/test_no_japanese_ui_literals.py / tests/test_i18n.py / tests/test_help_content.py / tests_ui/test_action_dialog_labels.py ほか
  - instructions/history/55_multilingual_ui.md（v0.4）/ instructions/phase/72_multilingual_ui/tasks/task_07〜11
verified:
  compile: pass
  tests: pass（1900・skip 7）
  tests_ui: pass（1233）
  smoke: pass

## next_action
- **【ユーザー確認待ち 1】二次レビューの指摘の採否**（`instructions/phase/72_multilingual_ui/tasks/task_11_integration.md` の表・各推奨つき）:
  - C1（Codex P2）言語の知らせを開く間にフックを止めていない（`app.py:523`）→ 推奨 = 採用（try / finally で suspend / resume・3 行）
  - D1 App の言語の決定のテストが無い → 推奨 = 採用（patch でキー無し / 不正 → en・ja → ja・警告が決定の後）
  - D2 smoke は言語を固定しない → 推奨 = 意図的な例外として暫定 55 §9 に明記
  - D7 キーマップの追加の行の種類を表示名とコードの同じ列で比べている → 推奨 = 採用（小）
  - D3・D4 は正本の文面で扱う / D5・D6・D8 は保留・不要
- **【ユーザー確認待ち 2】英語のヘルプで JIS の特殊キー名（無変換・変換・半角 / 全角）に日本語を併記するか**（画面のキー名は日本語のまま〔暫定 55 §6.2〕なので、英語のヘルプの Muhenkan 等だけでは画面のキーを探しにくい。推奨 = 初出に `Muhenkan (無変換)` の形で併記し、help_en の「日本語なし」テストの許可に入れる）
- 採否が決まったら: 採用分を task_11a として実装（codex-implementer）→ verifier → reviewer → その後 task_12
- **【ユーザー作業】task_12 の実機目視**: 「設定」→「Language / 言語」で English を選んで再起動 → メニュー・主画面・主なダイアログ・ステータス欄・エラー文・ヘルプが英語か / ボタン・ラベルが切れないか（暫定 55 §7・§9-1・§9-12）/ 日本語に戻して今と同じか。結果を受けて正本反映（暫定 55 §11 + task_11_integration.md の追加項目）・暫定 55 凍結・decisions_archive/72・current.md 完了記載・/refactor_check
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
