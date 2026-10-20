# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-20T12:30:00
phase: instructions/phase/64_external_layout_path_base（進行中・直接改訂モード・暫定なし / decisions 64）。次採番 = phase 65 / 暫定 47 / decisions 65 / 提案書 25 / idea 55
直前の完了フェーズ = **phase 63**（`decisions_archive/63_make_only_keys.md`）
last_commit_location: `claude/external-key-layout-persistence-a9eaa2`（phase 64 task_01）。main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 64 進行中（外部キーレイアウトのパス基準の統一・idea_13）。task_01 実装・検証・reviewer 採用済み → ユーザーの実機目視待ち。**
mode: pending_review
presence: present

## last_action
ts: 2026-10-20T12:30:00
who: main
summary: |
  phase 64 起票（ユーザー判断: 移行・重複除去はしない〔JSON は手で直す〕/ 孤児検出の superset は残す）。起票の整合チェック reviewer 軽微 3 件を反映。
  task_01（codex-implementer）: split_loading.normalize_external_keyboard_layouts を config ルート基準の相対へ（冪等）・layout_controller の登録 / 表示の基準を paths.config_root へ・ConfigPaths.to_rel_if_possible 削除・テスト更新と新規 tests/test_layout_controller_registration.py。application + presentation に跨る（スキーマ不変）。
  reviewer: 完了可（指摘なし）。ユーザーから phase 内タスクの連続実行の許可あり（2026-10-20）。
result_files:
  - keyseq/application/config_service/split_loading.py
  - keyseq/presentation/controllers/layout_controller.py
  - keyseq/presentation/config_paths.py
  - tests/test_config_service.py
  - tests/test_layout_controller_scan_code.py
  - tests/test_layout_controller_registration.py
  - instructions/phase/64_external_layout_path_base/
verified:
  compile: clean
  tests: pass 1761（skipped 7）
  tests_ui: pass 1122
  smoke: pass

## next_action
- ユーザーの実機目視（task_01 完了条件）: 既存 JSON の外部レイアウト要素を手で直すか削除 → 外部レイアウトを登録 → 再起動して一覧に残る → 再度再起動しても構成セットの JSON が `user/keylayout/jis.json` のまま
- 目視 OK 後 task_02 を `/task_new` で起票し実施（正本 `data_schema/5_08_09_orphan_sweep.md:38-42` の理由の記述・codebase_map・decisions_archive/64・decisions.md 索引・current.md 完了・idea_13 を INDEX_done へ・/refactor_check・完了判定前レビュー〔deep-reviewer + codex-adversarial-reviewer〕）

## blockers
- **【回避中】Codex の書き込み実行（2026-10-14 18:24 以降の不具合）**: Codex の更新（0.162.x・cua_node runtime a9ba…・17:22〜18:25）以降、`~/.codex/.sandbox/sandbox.2026-10-14.log` に `setup refresh had errors`（node_repl.exe の ACL 更新が「別のプロセスが使用中」で失敗）。読み取り専用（レビュー・調査）は通る。再起動では直らない。**2026-10-15 ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `unelevated` に変更 → 常駐の broker・app-server を止めて再実行で書き込み可**。Codex の更新で直ったら `elevated` に戻す（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **素の `python` を Bash で呼ばない**（必ず `..\..\..\.venv\Scripts\python.exe`）。Bash の heredoc の前に `cat > file` を単独で書かない（stdin 待ちでハングする）。
- **Codex は互換の工夫・テストの期待値の推測を足すことがある**。差分を直読みしてから verifier / reviewer へ。Codex は LF を混ぜることがある（コミットは git が正規化）。
- 画面の枠（phase 56・57）の地図 = `codebase_map.md`「画面の枠（phase 56・57）」。振り分けは `suppress_keys` 1 本（`screen_grid_session._publish_snapshot`）/ 操作キーは `domain/screen_grid/ops.py`。
- **【罠・phase 57 で実証】Windows の Tk で位置の反映の保留中に `wm_attributes("-topmost", True)` を呼ぶと窓が `0,0` へ戻る**（`geometry` の直後に `update_idletasks()`）。**Tk の測り直しは after_idle だと配置の計算より先に走ることがある**（測る前に `update_idletasks()`）・`<Configure>` で configure し返すと無限ループになり得る（値が変わったときだけ・結び付けは 1 つ）。
- **プロセスは pyautogui の import でシステム DPI 対応**（`.venv/Lib/site-packages/pyautogui/_pyautogui_win.py:17`）。検証は本番の起動経路で
- `tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・current.md「テスト負債」）。
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜41）の条項を実装の根拠に引かない。
- **【Codex のプロセス・2026-10-14 実測】** companion は作業フォルダ（cwd）ごとに `app-server-broker.mjs serve` を常駐させ、その下の `codex app-server`（+ sandbox の runner・node）は**呼び出し後も残る（再利用のための設計）**。
  worktree ごとに 1 組ずつ増えるため、worktree を多く使うと codex.exe が溜まる。Codex デスクトップアプリ（ChatGPT.exe）配下の codex.exe は別物。2026-10-14 の不調はプロセスの溜まりではなく Codex の更新が原因（blockers 参照・再起動では直らない）
- **【罠・phase 58 task_02 で実測】ttk.LabelFrame の `labelwidget` に既定の ttk.Label を使うと枠の要求高さが 4px 増える**（vista・58 → 62px。矢印の字形とは無関係）。`style="TLabelframe.Label"` なら元と同じ 58px・同じ見た目
