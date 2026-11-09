# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-10T01:29:42
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.5・ユーザー確定済）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/mac-support-4f08b3`（Mac の worktree `mac-support-4f08b3`。push はユーザー）。main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 75（macOS 対応）段階 ① を実装中。task_01〜04 完了（段階 ① の実装完了）。段階の区切りレビューと実機目視の待ち。**
mode: implementing
presence: away（戻る予定 未定）

## last_action
ts: 2026-11-10T01:29:42
who: main
summary: |
  実施: 段階 ①（task_01〜04）完了・各コミット済み（2f25838e / 6dda07b5 / e582b8dd / 146f1fe0）。OS 依存はすべて `infrastructure/os_backend/windows/` の裏へ移動し、AST の許可リストは空。`KeyCaptureHook` の `after` はディスパッチャ未対応（確認事項 2）。
  ユーザー判断: タスクの連続実行を許可（2026-11-10）。不在モード。
  レビュー: 各タスク reviewer 採用 / 段階の区切り = Codex 敵対的 approve（指摘なし）・deep-reviewer「修正して採用」（M1〜M5 は next_action の確認事項）。想定外の先行実装なし。
result_files:
  - keyseq/infrastructure/os_backend/
  - keyseq/infrastructure/input_gateway.py
  - instructions/phase/75_mac_support/tasks/
verified:
  compile: clean
  tests: pass 1971（skip 7）
  tests_ui: pass 1270（最終コミット 146f1fe0 で全件）
  smoke: pass

## next_action
- **【ユーザー確認 1】段階 ① の実機目視（Windows）**: `git` のブランチ `claude/phase-75-progress-d68f10` で起動し、IME オンの文字送信 / キーの取得 / キー置換とシーケンス / マウス操作とクリック位置の取得 / キーボードUIの常に手前 / カーソルグリッド / 言語の「今すぐ再起動」を確認する
- **【ユーザー確認 2】deep-reviewer の指摘の採否**（推奨つき）:
  - M1 フックスレッドの `after` が残る（`presentation/key_capture_hook.py:148→168`・実測済）→ 推奨 = task_08 の対象に明記（Windows の動作は変わらず、macOS のディスパッチャの実体と一緒に直す）
  - M2 ディスパッチャの型では §5.1 の「捨てるときの復元」を渡せない（`hook_controller.py:26-34`）→ 推奨 = task_08 で暫定 57 と併せて改訂
  - M3 フックの契約が Protocol に未記載（`os_backend/contracts.py:21-27`。イベントの必須属性・戻り値 False = 抑止等）→ 推奨 = 段階 ② の前に docstring を追記（小修正）
  - M4 pyautogui / pynput / 再起動の実装が `windows/` にしかない（`windows/mouse_backend.py`・`windows/app_relaunch.py`）→ 推奨 = task_11・task_12 で OS 共通の置き場を決める
  - M5 契約テストが module 先頭で `windows.backend` を import し macOS では収集時に落ちる（`tests/test_os_backend_contracts.py:13-17` ほか）→ 推奨 = task_05 で分離（§7）
- 確認後: 採用分を反映し、state を更新して push（ユーザー）、Mac で task_05 から再開する（Mac の `.venv` は python.org 版 3.13 に作り直す）
- 別件: ブランチ `claude/gracious-brahmagupta-2e05b1` と `claude/welcome-popup-first-launch-2b70d9` の main へのマージ（ユーザー）

## blockers
- **Mac の `.venv` は Python 3.15 で Tk が使えない**。task_05 で python.org 版の 3.13 に作り直す（段階 ① には影響しない）
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
