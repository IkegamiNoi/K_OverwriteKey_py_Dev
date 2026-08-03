# handoff.md

過去の会話履歴は参照しないでください。
このファイルと `.claude_data/state/session.md` を起点に作業を再開してください。

## プロジェクト概要
- 言語/実行: Python（tkinter GUI）。オニオン構成（presentation / application / domain / infrastructure）。
- 対象アプリ: keyseq（キー割り当て/オーバーライドツール）。全体仕様は `instructions/common/`（`app_overview.md` / `codebase_map.md`）参照。
- **python 実行は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  依存 keyboard/pyautogui/pynput はこの `.venv` にのみ導入済み。グローバル `py` は使わない（tests_ui/smoke が落ちる）。
- **Codex は python を一切実行できない**（サンドボックス制約・回避不能）。実装委任にテスト実行を含めず、
  実測は `verifier`（またはメイン）が行う（理由は `instructions/common/rules_detail/codex_operations.md` §0）。

## 再開手順
1. `.claude_data/state/session.md` を読む（最重要・最新状態）
2. `.claude_data/state/decisions.md` を読む（判断履歴。**末尾の「phase 07」節が現在の作業**。
   完了フェーズは「アーカイブ索引」→ `decisions_archive/<phase>.md`）
3. CLAUDE.md → `.claude/rules/` の順に必要分を読む
4. **現在のフェーズ = phase 07（保存系リデザイン Phase γ）**。
   規範 = [phase/07_hook_keys_global_default/phase.md](../../instructions/phase/07_hook_keys_global_default/phase.md)、
   主入力（確定設計）= [history/06_hook_keys_global_default.md](../../instructions/history/06_hook_keys_global_default.md)
   （v0.2・ユーザー確定済）。**暫定仕様先行モード**なのでフェーズ中は正本を直接改訂しない。
   番号対応: **phase 07 / 暫定 06 / decisions_archive 07**。
5. 着手するタスク定義（`instructions/phase/07_hook_keys_global_default/tasks/`）を読む →
   session.md.next_action から再開する（**task_03 から**）

## 現在の作業の 1 行サマリ
**phase 07（Phase γ = hook キーの全体デフォルト化）を実施中。task_01 / task_02 完了、次は task_03（保存時挙動）**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（task_02 完了時・コミット `8904c00`）: compile **clean** / tests **164** / tests_ui **159** / smoke **pass**。
**phase 07 はタスクごとにテストを追加するため tests の件数は増える**（減ったら退行を疑う）。
実行後に worktree ルートへ `user/` が生成されていないことも確認する。

## 次アクション（session.md.next_action より）
- **task_03（保存時挙動）を `/task_new` で起票 → codex-implementer へ委任**。
  内容 = `config_service/split_payloads.py` の keymap_set 保存で、ON なら個別値を保存 /
  **OFF なら個別値を空文字にクリアし `hook_keys_individual=false` を書き出す**
  （キー自体は残す = 既存キー削除禁止）。暫定仕様 06 §5 / 受入条件 3・5。
  **保存 JSON のバイト列比較テストが変化する初めてのタスク**になるため、
  差分が hook 関連キーのみであることを確認する。
- 以降: 04 全体デフォルト更新 API（成否付き）→ 05 チェック UI → 06 所有者切替 capture →
  07 統合確認（**実機目視はここでまとめて実施**）→ 08 正本反映。
- 各タスクの流れ: タスク定義起票 → codex-implementer へ委任 → **verifier で実測** → reviewer → コミット。

## phase 07（Phase γ）の要点
- **目的**: `hook_stop_key` / `hook_toggle_key` の全体デフォルトを `config/config.json` に持たせ、
  keymap_set 側のチェック（`hook_keys_individual`）で個別指定できるようにする。
  **挙動変更・スキーマ追加あり / 後方互換必須**（既存キーを削除しない）。
- **【設計の芯】キー解決点は 1 箇所**。`split_loading.load_global_hook_keys`（config.json の全体デフォルト
  読み出し・正規化・失敗時 `("", "")` へ縮退）と `ConfigService.apply_global_hook_key_defaults`
  （OFF のみ注入・その場更新・冪等）の 2 本のみ。
  **フック層（`input_router` / `hook_controller` / `keyboard_window` / `app.py`）は無変更を維持する**
  （常に解決済みの値を見る設計。触ったら設計違反）。
- **移行判定 `resolve_hook_keys_individual(source)`（domain）には生の `keymap_set` dict を渡す**。
  runtime を渡すと `new_default_data()` 由来でフラグが常に存在し移行が発火しない。
  明示フラグの有無は **`in` で判定**（`.get()` の真偽だと `false` とキー無しを区別できない）。
  **冪等性が要件**（フラグ True のまま両キーが空で False へ落とさない。落とすと
  「ON→OFF で個別値を内部保持」が壊れる）。
- **注入は読込時だけでは足りない**。新規 runtime を生成する presentation 3 箇所
  （`keymap_set_io.new_config` / `restore_default` / `startup_io` の空データフォールバック）からも
  注入 API を呼ぶ（受入条件 2「新規作成で再設定不要」）。`app.py` は直後に上書きされるため対象外。
- 未実装の確定事項（task_03 以降）: OFF 保存で個別値を空文字クリア + フラグ false /
  config.json 更新 API は**成否を返し成功時のみ UI を確定** / OFF 時のキー編集は config.json を編集し
  **keymap_set を dirty にしない**（OFF 前の dirty を記録して復元）/ 再 ON での個別値復活は
  **保存前の同一セッション内のみ**。

## 直前の完了作業（計画05・フェーズ番号を消費しない）
- `config_service` / `keymap_set_io` の分割リファクタ（**挙動不変**）。項目 0 / 1 / 2 完了（`c7a8bf4` / `c22e49b`）。
- **`config_service` はパッケージ**（`keyseq/application/config_service/`）で
  **ConfigService 本体は `__init__.py`**（`config_service.py` ではない）。
  理由: テスト 4 箇所が `patch("keyseq.application.config_service.os.path", ntpath)` で
  **モジュール名前空間の `os.path` を差し替えている**ため、この配置を崩すと壊れる。
  同じ理由で**パス基盤メソッド**（`canonical_path` / `is_path_within` /
  `to_config_relative_or_absolute` / `_merge_parent_ref` 等）**を兄弟モジュールへ移さない**。
- 兄弟モジュール: `save_plan_execution.py`（保存計画の実行）/ `split_payloads.py`（payload 構築）/
  `save_path_resolution.py`（保存先解決・命名）/ `split_loading.py`（split 読込）。
  抽出関数は **`service` を第 1 引数に取る**。**兄弟から `__init__` を import しない**（循環回避）。
  構成の正本は `codebase_map.md` の ConfigService 節。
- `keymap_set_io._collect_child_save_plan` は手順の並びのみ。**ループ再入は `_RETRY` センチネル**
  （戻り値がキャンセル / 再試行 / 確定の 3 系統あるため `None` と区別）。

## 注意事項・blockers
- **blockers: なし**。
- **【最重要・2 度踏んだ罠】パス表記の混在事故**: runtime の `source_path` 3 種は **config 配下なら相対**で
  保持される（config 外は絶対・区切りは `/` 正規化）。**相対値を `os.path.abspath` / `dirname` / `exists` /
  `join` へ解決なしで渡すと cwd 基準で解決される**。症状 = **リポジトリルートに `user/` が生成される** /
  「別名で保存」が前回の場所に開かない。解決は `ConfigService.resolve_config_path(path, config_root)`。
  `to_config_relative_or_absolute` は**入口で解決するので相対を渡してよい**。
- **不変条件（壊しやすい）**: ① `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致**（入口は `dirty_state` のメソッドのみ・内部キー直代入禁止）/
  ② 子の `_parent_refs` は**保存先ファイルの集合 + 現在の上位**（in-memory の旧 refs を持ち込まない）/
  ③ **canonical identity は比較専用**（`canonical_path` / `is_path_within` を使い、`normcase` 済み文字列を
  保存値・戻り値・表示へ混入させない）/ ④ **共有状況は判定名で分岐する**（`SHARE_SOLE` / `SHARE_NEW`。
  表示文言 `share_text_for` で分岐しない）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  テスト内の `AssertionError` も広い `except Exception` に捕まり、**失敗が「ハング」に化ける**。
  tests_ui の 3 ファイル（`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup`）の `setUp` に **fail-fast ガード**がある。
  期待するテストは個別 patch で上書きする。新しいモーダルを増やすときは同じガードを足す
  （`askyesnocancel` はガードへ入れない）。**ハングしたら `messagebox` / `filedialog` を全遮断して単独実行**すると
  真因が一発で出る（実測 1 秒以下）。
- **【tests_ui の罠】`_prepare_loaded_keymap_set` は `save_plan=None` で `save_runtime_data` を呼ぶため
  runtime に source_path が入らない**。source_path 前提のテストは保存後に
  `load_runtime_data_from_keymap_set_path` → `apply_loaded_data_to_ui` で読み直すこと。
  怠ると個別保存が「保存先を選ぶ」分岐へ落ち、**実リポジトリの `config/` にモーダルを開いてハングする**。
- **【tests_ui の罠・phase 07 で遭遇】特性テストは `config_service` の生成系をスタブ dict で差し替える**
  （`new_empty_data` → `{"empty": True}` 等）。runtime へキーを増やす変更を入れると
  `assertEqual(self.app.data, {...})` が落ちる。**実装ではなくテスト側の追従で正しい**が、
  実 runtime と混同しないこと。
- **【教訓・UI】tkinter の「初期表示だけ崩れる」系は one-shot の再計算（`after_idle` 1 回）では直らない**。
  **対象ウィジェット自身の `<Configure>` で自己修復させる**（同幅早期 return を必ず併設）。
- **【Codex 運用】フォワーダが最終出力を返さないまま完了通知だけ来る / 差分 0 件で返る**ことがある
  → `SendMessage` で同じフォワーダを再開して回収する。**Codex 申告のテスト結果は信用せず必ず verifier で再実測**。
  手順書は `instructions/common/rules_detail/codex_operations.md`。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。編集は必ず worktree ルート配下で。
- **【罠】Bash ツールは Git Bash**。PowerShell の here-string（`@'...'@`）はコミットメッセージに `@` が混入する。
  複数行は heredoc（`git commit -F - <<'EOF'`）を使う。
- **【罠】`git grep` は追跡済みのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。行数計測は `wc -l`。
- **【傾向】reviewer が「完了可」でも実測で落ちることがある**。**判定はテストの実測が優先**。
  fail が出たら**まず production か test かを切り分ける**（既知の期待値誤り: `slugify_file_stem` は
  大文字小文字を変換しない / `source_path` は config_root 相対）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。出力の作法は
  `.claude/rules/output_style.md`。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **06_child_file_save_dialog** / 05_keymap_set_new_and_default_dir / 04_config_io_controller_split）。
- 未着手/保留 idea: idea_07（参照元の掃除・**β 完了で着手可**）/ idea_03（hotkey 保存正規化・低）/
  idea_08（個別プリセット）/ idea_09（レガシー保存パス）/ idea_04・idea_06（保留）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
