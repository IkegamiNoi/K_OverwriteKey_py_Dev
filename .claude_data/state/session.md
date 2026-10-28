# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-29T18:00:00
phase: **アクティブなフェーズ = なし**（phase 70 = ヘルプの作成は 2026-10-29 完了・暫定 53 v0.8 凍結・`decisions_archive/70_help_window.md`）。次採番 = phase 71 / 暫定 54 / decisions 71 / 提案書 28 / idea 55
直前の完了フェーズ = **phase 70**（ヘルプの作成）。予定 = 多言語対応 → Mac 対応（次フェーズはユーザー判断で `/phase_start`）
last_commit_location: `claude/ui-wording-improvement-4eaa76`（phase 70 の task_06 以降〜完了）。main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 70 完了（2026-10-29）。** 実機目視 15 項目 → 2 件を task_08a（「?」を下端の左寄せ・「用語」の注記）で修正 → 正本反映・凍結 → 完了判定前レビュー（Codex 敵対的 1・deep 修正して完了可 10）→ task_08b（「?」とプリセット編集…で記録を止める）・文書の指摘を反映。refactor_check = 推奨（M3）→ 提案書 27 = 保留（ユーザー判断）。
mode: idle
presence: present

## last_action
ts: 2026-10-29T18:00:00
who: main
summary: |
  task_08a = 500c3e7 / task_08 正本反映 WIP = 9eaaaff / 完了判定前レビューの反映と task_08b = 最終コミット。
  ユーザー判断（2026-10-29・推奨どおり）: A = 08b で修正 / B = 正本をライセンスの窓は Ctrl+C のみに（確定設計どおり）/ 文書の指摘を反映 / 提案書 27 保留。
verified:
  compile: pass
  tests: pass（1856・skip 7）
  tests_ui: pass（1202）
  smoke: pass

## next_action
- 次フェーズはユーザー判断（予定 = 多言語対応 → Mac 対応）。`/phase_start`
- main へのマージはユーザー（PR は作らない）
- 実機目視（任意）: JIS 配列でトリガーの追加・編集の記録中に「?」→ 絞り込み欄で半角/全角が効く

## blockers
- **【回避中】Codex の書き込み実行（2026-10-14 18:24 以降の不具合）**: Codex の更新（0.162.x・cua_node runtime a9ba…・17:22〜18:25）以降、`~/.codex/.sandbox/sandbox.2026-10-14.log` に `setup refresh had errors`（node_repl.exe の ACL 更新が「別のプロセスが使用中」で失敗）。読み取り専用（レビュー・調査）は通る。再起動では直らない。**2026-10-15 ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `unelevated` に変更 → 常駐の broker・app-server を止めて再実行で書き込み可**。Codex の更新で直ったら `elevated` に戻す（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **phase 70 の実測（2026-10-27）**: `dialog.grab_set()` の下で `Toplevel(dialog)` は実入力（SetCursorPos + mouse_event / keybd_event）のクリック・キーを受け、`Toplevel(root)` は受けない（probe の写しは暫定 53 §6.3）。実 App（`grab_modal`・最小化の預かり）での確認は task_04 の tests_ui / 実機目視で行う。
- **phase 70 の版**: `__version__` はユーザーが直接またはユーザーの指示でだけ変更する（Claude が独断で上げない）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
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
