# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-09T01:13:00
phase: なし（アクティブなフェーズなし）。次採番 = phase 74 / 暫定 57 / decisions 74 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 73**（初回起動の Welcome とサンプルの作り直し・`decisions_archive/73_welcome_first_launch.md`）
last_commit_location: `claude/gracious-brahmagupta-2e05b1`（phase 73 の本体は `claude/welcome-popup-first-launch-2b70d9`）。main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: away（戻る予定 未定）
focus: **記号キーのキー名の表示（`bar` → `|`）の検討中・方針のユーザー判断待ち（暫定 57 は未起票）。** phase 73 は 2026-11-09 完了・アクティブなフェーズなし。
mode: blocked

## last_action
ts: 2026-11-09T01:13:00
who: main
summary: |
  記号キーのキー名の表示を調査し、記号の割り当て案を作成（コード・仕様書は未変更・暫定仕様は未起票）。/away（戻る予定 未定）のため判断待ちで引き継ぎ。テストの数値は phase 73 完了時のもの。
verified:
  compile: pass
  tests: pass（1940・skip 7）
  tests_ui: pass（1266）
  smoke: pass

## next_action
- **【ユーザー確認待ち】記号キーの表示の方針**: A（推奨）= 保存値は変えず表示だけ記号にする / B = 保存値も記号にする。A の根拠 = JSON の既存キーの意味変更の禁止（`.claude/rules/implementation.md`）・`+` は hotkey の区切りで `ctrl++` は検査でエラー（`keyseq/domain/hotkey.py:17`）。
  - 表示箇所: キーボードUIの置換の枠 `keyboard_window.py:462` / トリガー一覧 `domain/config.py:460` / 出力シーケンス一覧 `domain/config.py:511`・`domain/key_hold.py:129`。**未確認 = キーマップ編集のキー置換一覧・切替 / 停止 / トグルキーの欄**（起票前に調べる）
  - 割り当て案: backslash `\`・slash `/`・semicolon `;`・comma `,`・period `.`・equal `=`・grave / quoteleft `` ` ``・apostrophe / quoteright `'`・bracketleft `[`・bracketright `]`・at `@`・asciicircum `^`・bar `|`・underscore `_`・plus `+`・asterisk `*`・colon `:`・less `<`・greater `>`・question `?`・asciitilde `~`・exclam `!`・quotedbl `"`・numbersign `#`・dollar `$`・percent `%`・ampersand `&`・parenleft `(`・parenright `)`・braceleft `{`・braceright `}`
  - 併せて確認（推奨）: ①hotkey の中の `+` `,` は単語のまま（`ctrl+plus`）・単独キーなら `+` ②レイアウトの `key_display_names` を記号の表より優先（`keyboard_layouts.py:30`）③入力欄は保存値のまま・記号は一覧と枠だけ
  - 方針が決まったら: 未確認箇所を調べて `/spec_draft`（暫定 57）。別件 = 記録された `period` / `comma` 等がフックの `.` / `,` と一致しない問題（`key_input.md:143`・idea_45・発火の可否は未検証）は表示だけの方針では直らない
- ブランチ `claude/welcome-popup-first-launch-2b70d9` の main へのマージ（ユーザー）
- 次フェーズはユーザー判断で `/phase_start`（予定 = Mac 対応）

## blockers
- **【回避中】Codex の書き込み実行（2026-10-14 18:24 以降の不具合）**: `~/.codex/.sandbox/sandbox.2026-10-14.log` に `setup refresh had errors`（node_repl.exe の ACL 更新が失敗）。**2026-10-15 ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `unelevated` に変更 → 常駐の broker・app-server を止めて再実行で書き込み可**。Codex の更新で直ったら `elevated` に戻す（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **画面の文言（phase 72 以降）**: 新しい文言は `keyseq/shared/i18n/locales/ja.json` と `en.json` の両方にキーを足し、ソースに日本語を書かない（静的テスト）。`tr` はモジュール定数・import 時に評価しない。`App(` を作る / 文言を assert する新しいテストモジュールは import 直後に `fix_language("ja")`。英語は `ui_terms.md` §2・§3（E1〜E7）に従う。
- **phase 73**: 報告された不具合 2 件（プリセットが編集で開くまで表示されない / キー名の記号表記）は別セッションの提案カードに出してある（本フェーズ外）。tests_ui の窓の大きさのテスト（`test_compact_window.py:298`・`test_pane_window_width_persistence.py:236,275` の `pending`）が負荷で落ちることがある。**tests_ui の App() は worktree の `config/config.json`（ユーザーの手元の設定・gitignore）を読む**ので結果が手元の設定に左右される（task_05 の Welcome を出さない入口で考える）。Codex は python を実行できずテスト修正が手探りになる → 失敗はメインがトレースを読んで原因を絞ってから委任する。
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
