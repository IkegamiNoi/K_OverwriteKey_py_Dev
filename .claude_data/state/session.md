# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-10T00:00:00
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.5・ユーザー確定済）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/mac-support-4f08b3`（Mac の worktree `mac-support-4f08b3`。push はユーザー）。main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 75（macOS 対応）起票済・実装未着手。次は Windows で段階 ①（task_01〜04）。**
mode: implementing

## last_action
ts: 2026-11-10T00:00:00
who: main
summary: |
  実施: phase 75 と暫定 57 を起票（文書のみ・コードは無変更・コミット 0daa767）。
  ユーザー判断: §8 Q0〜Q8 はすべて提案どおり。Codex 敵対的レビューの 4 件はすべて反映。段階 ① は実装も検証も Windows で行う。
  レビュー: deep-reviewer「修正して採用」→ v0.2 反映 / codex-adversarial-reviewer 2 回 → v0.4・v0.5 反映（v0.5 の修正は再レビューなし）/ phase.md の整合チェック reviewer「修正して採用」→ 反映。
result_files:
  - instructions/history/57_mac_support.md
  - instructions/phase/75_mac_support/phase.md
  - instructions/phase/current.md
verified:
  compile: not_run（文書のみの変更）
  tests: not_run（基準線 = Windows 1951 pass・skip 7）
  tests_ui: not_run（基準線 = Windows 1270 pass）
  smoke: not_run

## next_action
- ユーザーが Mac でブランチ `claude/mac-support-4f08b3` を push し、Windows で取得する
- Windows で `instructions/phase/75_mac_support/phase.md` の task_01 を `/task_new` で起票する（暫定 57 §3・段階 ①）。`keyseq/infrastructure/os_backend/` の骨格・契約・import 境界の AST テスト・公開シンボルと Protocol の一致テスト・IME の移動
- task_01〜04 を実装エージェントへ委任し、タスクごとに verifier で Windows の標準検証 4 種（compile / tests / tests_ui / smoke）をゲートにする。件数を減らさない
- 段階 ① の完了後、state を更新して push し、Mac に戻って task_05 から再開する
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
