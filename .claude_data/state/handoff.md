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
2. `instructions/phase/current.md` → [phase 08 の phase.md](../../instructions/phase/08_hotkey_presets_global/phase.md) を読む
3. 主入力の確定設計 = [history/07_hotkey_presets_global.md](../../instructions/history/07_hotkey_presets_global.md)
   （**v0.3**。**§4 検討事項 A だけが未確定**で task_03 で確定する）
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む
5. 過去の判断は `.claude_data/state/decisions.md`（**末尾に進行中の phase 08 の節がある**）+
   「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**phase 08（プリセットの config.json グローバル化）を起票済み・task_01 未着手**。前段の phase 07（Phase γ）と計画06 は完了済み。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（計画06 項目1 完了時・コミット `4fa12a6`）:
compile **clean** / tests **170** / tests_ui **178** / smoke **pass** / manual **G1〜G9 OK（2026-08-05）**。
**件数が減ったら退行を疑う**。実行後に worktree ルートへ `user/` が生成されていないことも確認する。

## 次アクション（session.md.next_action より）
- **phase 08 task_01 を `/task_new` で起票 → 実装委任**。内容 = config.json の `hotkey_presets_path` を
  スキーマへ追加し、**未設定時の既定補完**（`user/hotkey_presets/default.json`）付きの読み出し API を新設。
  **同型の先行実装 `split_loading.load_global_hook_keys` をそのまま参考にする**。
- **task_03（設計確定）の前に task_04 へ着手しない**。task_03 = 暫定仕様 07 §4 検討事項 A
  （runtime を新規化・置換する入口の一本化）をユーザー確定し **v0.4 へ改訂**するタスク。
  レビューは `codex-adversarial-reviewer`（縮退時 `deep-reviewer`）。
- 各タスクの流れ: タスク定義起票 → codex-implementer へ委任 → **verifier で実測** → reviewer → コミット。

## 直前フェーズ（phase 07 = Phase γ）の要点
**正本が正**: `spec_detail/data_schema.md` **§5.9** + `key_input.md` **§7.6** + `codebase_map.md`。
暫定仕様 06 は凍結済（経緯の参照用）。判断履歴は `decisions_archive/07_hook_keys_global_default.md`。

- `hook_stop_key` / `hook_toggle_key` の**全体デフォルトを `config/config.json`** に持たせ、
  keymap_set のフラグ `hook_keys_individual` で個別指定に切り替える（**後方互換必須・既存キー削除禁止**）。
- **解決の分岐点は 4 つ**（これ以外へ解決ロジックを置かない）:
  `split_loading.load_global_hook_keys`（読み出し・失敗時 `("","")`）/
  `split_loading.build_runtime_data_from_split`（**通常読込の選択**。移行判定を通す）/
  `ConfigService.apply_global_hook_key_defaults`（**新規化・置換経路の直接注入**。通常読込は経由しない。
  フラグ無しは OFF とみなす）/ `split_payloads.build_keymap_set_payload`（保存側・**OFF は常に `""`**）。
- **フック層（`input_router` / `hook_controller` / `keyboard_window` / `app.py` の供給部）は無変更**が設計の芯。
- **【計画06】キー名の定義元は `domain/config.py`**（`HOOK_STOP_KEY` / `HOOK_TOGGLE_KEY` /
  対のタプル `HOOK_KEY_FIELDS` / 対の正規化 `normalize_hook_key_pair`）。新規箇所はリテラルを書かない
  （**添字参照 `HOOK_KEY_FIELDS[0]` は禁止**）。**明示列挙のまま残す 3 箇所** = `DEFAULT_CONFIG` /
  `split_payloads` の保存 dict キー / `startup_io` の保存 dict キー
  （保存 JSON のキー順は `tests/test_save_plan.py::test_saved_keymap_set_json_keeps_stable_key_order` が固定）。
- **移行判定 `resolve_hook_keys_individual` は渡すデータで意味が変わる**（読込=生 keymap_set / 保存=runtime /
  互換化）。明示フラグの有無は **`in` で判定**し、冪等性が要件。
- config.json への書き込みは `StartupIo.write_startup`（`-> bool`）→ `write_global_hook_keys` の**1 本のみ**。
  **別経路で read-modify-write しない**（`_startup_settings` と乖離すると次の書き出しで hook キーが消える）。
- 個別値の退避は `App._retained_hook_keys`（`app.data` に持たない）。**破棄は保存の実行 + runtime の
  置換・新規化**（読込 / 新規作成 / 例を復元）。**`_sync_control_vars_from_data` に破棄を入れない**。

## 注意事項・blockers
- **blockers: なし**。
- **【config_service の配置制約】`config_service` はパッケージ**（`keyseq/application/config_service/`）で
  **ConfigService 本体は `__init__.py`**。テスト 4 箇所が
  `patch("keyseq.application.config_service.os.path", ntpath)` で**モジュール名前空間の `os.path` を差し替える**
  ため、この配置を崩すと壊れる。同じ理由で**パス基盤メソッド**（`canonical_path` / `is_path_within` /
  `to_config_relative_or_absolute` 等）**を兄弟モジュールへ移さない**。
  兄弟 = `save_plan_execution.py` / `split_payloads.py` / `save_path_resolution.py` / `split_loading.py`。
  抽出関数は **`service` を第 1 引数に取る**。**兄弟から `__init__` を import しない**（循環回避）。
- **【最重要・2 度踏んだ罠】パス表記の混在事故**: runtime の `source_path` 3 種は **config 配下なら相対**で
  保持される（config 外は絶対・区切りは `/` 正規化）。**相対値を `os.path.abspath` / `dirname` / `exists` /
  `join` へ解決なしで渡すと cwd 基準で解決される**。症状 = **リポジトリルートに `user/` が生成される** /
  「別名で保存」が前回の場所に開かない。解決は `ConfigService.resolve_config_path(path, config_root)`。
  `to_config_relative_or_absolute` は**入口で解決するので相対を渡してよい**。
- **不変条件（壊しやすい）**: ① `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致**（入口は `dirty_state` のメソッドのみ・内部キー直代入禁止）/
  ② 子の `_parent_refs` は**保存先ファイルの集合 + 現在の上位**（in-memory の旧 refs を持ち込まない）/
  ③ **canonical identity は比較専用**（`normcase` 済み文字列を保存値・戻り値・表示へ混入させない）/
  ④ **共有状況は判定名で分岐する**（`SHARE_SOLE` / `SHARE_NEW`。表示文言 `share_text_for` で分岐しない）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  テスト内の `AssertionError` も広い `except Exception` に捕まり、**失敗が「ハング」に化ける**。
  tests_ui の 3 ファイル（`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup`）の `setUp` に **fail-fast ガード**がある。
  期待するテストは個別 patch で上書きする。新しいモーダルを増やすときは同じガードを足す
  （`askyesnocancel` はガードへ入れない）。**ハングしたら `messagebox` / `filedialog` を全遮断して単独実行**する。
- **【tests_ui の罠】`_prepare_loaded_keymap_set` は `save_plan=None` で `save_runtime_data` を呼ぶため
  runtime に source_path が入らない**。source_path 前提のテストは保存後に
  `load_runtime_data_from_keymap_set_path` → `apply_loaded_data_to_ui` で読み直すこと。
- **【tests_ui の罠】特性テストは `config_service` の生成系をスタブ dict で差し替える**
  （`new_empty_data` → `{"empty": True}` 等）。runtime へキーを増やす変更を入れると
  `assertEqual(self.app.data, {...})` が落ちる。**実装ではなくテスト側の追従で正しい**。
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
  fail が出たら**まず production か test かを切り分ける**。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。出力の作法は
  `.claude/rules/output_style.md`。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **07_hook_keys_global_default** / 06_child_file_save_dialog / 05_keymap_set_new_and_default_dir）。
  提案書「計画05」（`config_service` / `keymap_set_io` の分割）と「計画06」（hook キー対の列挙の集約）は
  いずれも完了済みで、**どちらもフェーズ番号を消費していない**。
- 未着手/保留 idea: idea_07（参照元の掃除・**着手可**）/ idea_03（hotkey 保存正規化・低）/
  idea_08（個別プリセット）/ idea_09（レガシー保存パス）/ idea_04・idea_06（保留）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
