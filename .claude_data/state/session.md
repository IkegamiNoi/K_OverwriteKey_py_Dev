# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-17T17:00:00
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.20・ユーザー確定済）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 62
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/modifier-key-registration-issue-faa33a`（Mac の worktree・task_11d のコミットまで）。push はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 75 段階 ③ の Mac 側が完了（task_09〜11f を Mac で実装・目視 OK・コミット済み。最後 = task_11d 割り当て禁止の文言・暫定 57 v0.20）。次 = task_09〜11f の Windows 検証（ユーザーが push）→ 段階 ④（task_12 起票）。保留 = 2 枚目のモニタの目視・中クリック（未確認）。idea_59・idea_60 は検討段階。**
mode: implementing

## last_action
ts: 2026-11-17T15:00:00
who: main
summary: |
  task_11d を起票（ユーザー判断: 両 OS 共通の文言・ヒントは ctrl+c）→ reviewer 修正して採用（ヘルプの本文も含める・ユーザー判断）→ v0.20 承認 → codex-implementer で実装 → verifier pass・reviewer 採用 → Mac 目視 3・4 OK（1・2 は画面から出せずテストで代える・ユーザー判断）→ コミット。目視の際の新しい発見（ダイアログから開いたヘルプに入力できない）を idea_60 に起票。
result_files:
  - keyseq/shared/i18n/locales/ja.json・en.json・keyseq/presentation/help/content/help_ja.json・help_en.json・tests/test_keymap_switch_batch.py・tests_ui/test_prohibited_assign_keys_ui.py
  - instructions/history/57_mac_support.md（v0.20）・task_11d 定義（新規）・current.md・decisions.md・backlog/idea_60（新規）・INDEX.md
verified:
  compile: clean（Mac）
  tests_mac: 2131 件・失敗 1（test_third_party）・エラー 0・skip 32
  smoke_mac: pass
  tests_ui_mac: test_prohibited_assign_keys_ui・test_preset_manager_i18n・test_task06_keymap_management_ui・test_help_window 失敗 0
  tests_windows: compile clean / tests 2193・失敗 0（テスト側の取りこぼし 3 件を修正後）/ smoke OK / tests_ui 79 本 1 本ずつ・失敗 0（修正後）
  visual_mac: task_11d OK（3・4）
  visual_windows: task_09〜11f OK（Win+D で入れ子のプリセット追加が白くなる件は phase 75 前の main でも起きる既存の問題 → idea_61。task_09d は記号キーの記録で確認・ドイツ語入力は省略〔ユーザー判断〕）

## next_action
- **task_09〜11f の Windows 自動検証は完了（2026-11-17・テスト側の取りこぼし 3 件を修正・reviewer 採用・コミット済み）。Windows の目視も完了（既存の問題 1 件を idea_61 へ）**
- その後、段階 ④ の task_12（`app_data_root` への統一と同梱物のパス・再起動）を起票。

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
