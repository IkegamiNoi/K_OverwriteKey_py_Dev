# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-22T13:00:00
phase: instructions/phase/75_mac_support（主入力 = 暫定 57 v0.25・v0.25 は Codex 敵対的レビュー needs-attention で確定待ち）。次採番 = phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 64
直前の完了フェーズ = **phase 74**（記号キーのキー名の表示・`decisions_archive/74_key_symbol_display.md`）
last_commit_location: `claude/task-13b-72ac5c`（Mac の worktree・state のコミットまで。task_13b / 11g の作業ファイルは未コミット）。push はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: away（戻る予定 未定）
focus: **phase 75 段階 ④。task_13b（Mac のビルド）実装・検証 pass・reviewer 修正して採用→反映・`.app` ビルド済み。実機確認で見つかった「メニューからのモーダルが戻らない」は task_11g（暫定 57 v0.25）で解決・完了。残り = task_13b の実機確認のやり直し（1・2・3・5）と、保存パネルが `.app` で固まる件の調査。**
mode: implementing

## last_action
ts: 2026-11-22T04:30:00
who: main
summary: |
  実施: task_13b を起票（reviewer 修正して採用）→ ユーザー許可で PyInstaller 6.22.3 と sdist を Mac の .venv / packaging/sources へ → codex-implementer で実装 + メインの補い → verifier（tests 2141・test_third_party 7 pass・smoke OK・ビルド成功〔Tk 9.1 同梱可〕・codesign OK・pynput 差し替え OK）→ reviewer 修正して採用（README の pynput のパス）→ 反映・再ビルド。task_12 で書かれた test_app_data_roots（Mac でエラー）を OS 別に分割（ユーザー承認）。
  ユーザー判断: 識別子 io.github.ikegaminoi.keyseq・未公証の開き方を README に（暫定 57 v0.24）・C ライブラリ（OpenSSL 等）は Mac の一覧を記録し Windows 作業時に両 OS 分を 1 本で起票・メニューの処理を after(0) で遅らせる案で起票。
  実機確認: 4 OK。3（再起動）はメニューの処理の中の wait_window が戻らず止まる（開発実行でも起きる・faulthandler で特定・after(0) で直ることを probe で確認）→ 暫定 57 v0.25（§5.4「メニューの処理」）+ task_11g 起票（reviewer 修正して採用→反映）。保存パネルの件は .app でだけ起き、未調査。
  Codex 敵対的レビュー（v0.25）: needs-attention・中 3（終了と予約の競合／チェック項目の遅延で別の構成セットに作用／tests_ui の漏れ〔反映済み〕）。
result_files:
  - packaging/requirements-build.txt・packaging/README.md・packaging/macos/（keyseq.spec・README_dist.txt）
  - keyseq/presentation/help/content/third_party/（third_party.json・pyobjc.txt・rubicon_objc.txt・python_macos.txt）・tests/test_third_party.py・tests/test_os_backend_contracts.py
  - instructions/history/57_mac_support.md（v0.24・v0.25）・instructions/phase/75_mac_support/（phase.md・tasks/task_13b_packaging_macos_build.md・tasks/task_11g_menu_command_deferral.md）・.claude_data/state/decisions.md
verified:
  tests_mac: compile clean / tests 2141・エラー 1（test_app_data_roots → 分割後のモジュール 24 件 OK・全体の再実行は未）/ smoke OK / tests_ui test_help_window OK / ビルド成功
  tests_windows: not_run（表・テスト・requirements の変更は次の Windows 作業で）
  visual_mac: task_13b 4 OK・3 NG（→ task_11g）・保存パネル NG（.app のみ）・1・2・5 未報告

## next_action
- **task_11g 完了（2026-11-22・Mac 目視 1〜7 OK・コミット済み）**。idea_64（Mac の保存パネルを広げた形で）を起票。次 = **task_13b の実機確認のやり直し**: `.app` は task_11g を入れて作り直し済み（2026-11-22・ビルド成功・codesign OK）→ **実機確認 1〜4 OK**（再許可は `tccutil reset Accessibility io.github.ikegaminoi.keyseq` で消して許可し直すと動いた → 手順書と README_dist を具体化済み・`.app` は未反映）。**5 はテンキーのサンプルの A・R・F（→ `plus`・`9`・`6`・`sample/keymaps/numpad.json`）でエラー・ほか OK → 原因特定**: Mac の backend（`macos/backend.py:196-218`）が `key_symbols.py` の記号キーの名前 34 個（`plus`・`asterisk`・`slash`・`minus` 等・`yen`・`ro` 以外）を拒否する（開発実行でも起きる既存の不具合・暫定 57 §8 Q7 案 A との乖離）。ユーザー提案（2026-11-22）= 記号キーのキー名は**文字を正**にする（互換は気にしない・良いコードを優先）。実測 = レイアウトの JSON は文字・Tk の記録は名前（`tk_keys.py:73,76-105`）・サンプルは名前（`config.py:108-110`）・Windows は keyboard ライブラリが両方受け付ける。ユーザー了承で暫定 57 §5.3.5（v0.26 案・未確定）を下書き済み（文字を正・例外 = `plus`〔ホットキーの区切り `hotkey.py:17`〕と JIS の `yen` / `ro`・記録は文字で返す〔idea_45 も解消〕・表示の表は例外だけに・Windows の Shift の要る文字の送信は Windows で実測・**論点 = 単語の名前の入力は案 1〔読み替えも拒否もしない・推奨〕/ 案 2〔両 OS で拒否〕**）。Codex 敵対的レビュー = needs-attention（high 2: `,` も壊れる〔`action_executor.py:249` の区切り・`key_hold.py:86-87` が拒否〕・Shift 付きの文字は入力側の物理キー名〔`input_router.py:186-200`〕と一致しない／medium 3: 出力の Shift の契約は置換先だけ・テンキーのサンプルは OS で別の物理キー・旧名の扱い。メインが裏付け済み）。本質 = キー名に入力用〔物理キー〕と出力用〔出す文字〕が混ざっている。**【ユーザー判断待ち】推奨 = 分ける: ①今はサンプルのテンキーを `num add` / `num multiply` / `num divide` に直すだけ（§5.3.5 の下書きは取り下げ）②キー名の入力用 / 出力用の整理は idea にして idea_45 と統合（互換不要の方針も記す）**。その後、保存パネルが `.app` で固まる件の調査。
- task_11g の完了後: task_13b の実機確認をやり直す（1 初回起動〔先に `~/Library/Application Support/keyseq` を別名に〕・2 保存と再読込・3 言語の再起動〔`open -n` の要否〕・5 置換・シーケンス・キー取得）。
- 保存パネルの件（`.app` でだけ・別名保存で既存名 → 置き換えの確認で Cancel → パネルの Save / Cancel が効かない）を調べる（task_13b の範囲）。
- Mac の tests 全体を verifier で流し直す（test_app_data_roots の分割の後）。
- 残課題（次の Windows 作業）: test_third_party・test_os_backend_contracts・requirements-build.txt・task_11g の Windows 検証。C ライブラリ（Mac = libssl・libcrypto・liblzma・libmpdec・libtommath）と Windows 側の洗い出し → 両 OS 分を 1 本で起票。

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
