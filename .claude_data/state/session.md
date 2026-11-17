# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-17T23:55:00
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.21・ユーザー確定済）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 62
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/continue-c6c37b`（Windows の worktree・task_12 のコミットまで）。push はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: away（戻る予定 未定）
focus: **phase 75 段階 ④。task_12（app_data_root・同梱物のパス・見本のコピー・再起動の共通化・暫定 57 v0.21）完了（2026-11-18・Windows 目視 OK）。次 = task_13（packaging とビルド・各 OS の実機確認）の起票。保留 = 2 枚目のモニタの目視・中クリック（未確認）。idea_59〜61 は検討段階。**
mode: implementing

## last_action
ts: 2026-11-17T23:55:00
who: main
summary: |
  task_09〜11f の Windows 検証（テスト側の取りこぼし 3 件を修正・目視 OK・Win+D の白い窓は既存の問題で idea_61）→ task_12 を起票（見本のコピーは keylayout が無いときだけ・Mac は Application Support/keyseq/config・v0.21 ユーザー確定・起票レビュー修正して採用）→ codex-implementer（3 回に分けて実行。止まった分 = git mv・import の抜け 3 か所・Mac の relaunch の import をメインが補った。Codex のパッチが CRLF のテストに当たらない → 対象を LF に揃えて再依頼）→ verifier pass → reviewer 完了可（codebase_map に app_data_root を一言追記）→ コミット。不在モード中（戻り未定）のため目視待ちで止めた。
result_files:
  - keyseq/infrastructure/os_backend/app_relaunch.py（windows/ から移動）・contracts.py・windows/backend.py・macos/backend.py・keyseq/infrastructure/bundled_layouts.py（新規）・keyseq/presentation/bundled_paths.py・app.py
  - tests/test_app_relaunch.py・test_os_backend_contracts.py・test_bundled_layouts.py（新規）・test_bundled_paths.py（新規）・instructions/common/codebase_map.md
  - instructions/history/57_mac_support.md（v0.21）・task_12 定義（新規）・decisions.md
verified:
  tests_windows: compile clean / tests 2202・失敗 0・skip 7 / smoke OK / tests_ui（first_launch_flow・app_ui_flows・help_window・ui_language）失敗 0。テスト実行で config/ に keylayout.tmp 等は出来ていない
  tests_mac: not_run（task_13 でまとめて）
  visual_windows: task_09〜11f OK。task_12 OK（開発実行での言語切り替え＝再起動・2026-11-18）

## next_action
- **task_12 完了（Windows 目視 OK・2026-11-18）。次 = task_13 を起票**（`packaging/`・`.spec`・datas の相対配置・ビルドと各 OS の実機確認・`.app` の `open -n`・同梱する見本の選別・`test_third_party`）。
- Mac 側の task_12 の確認（tests・smoke）は task_13 でまとめて行う。

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
