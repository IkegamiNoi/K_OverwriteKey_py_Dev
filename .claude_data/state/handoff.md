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
2. `instructions/phase/current.md` → [phase 09 の phase.md](../../instructions/phase/09_per_keymap_set_presets/phase.md) を読む
3. 主入力の確定設計 = [history/08_per_keymap_set_presets.md](../../instructions/history/08_per_keymap_set_presets.md)
   （**v0.7・全条項が確定済**。**§2 が確定事項の集約**。§3-2 解決順序 / §3-3 保存 / §3-4 UI が実装の規範）
4. 実機目視の観点 = [tasks/task_07_integration_check.md](../../instructions/phase/09_per_keymap_set_presets/tasks/task_07_integration_check.md) **§3 の表**
5. CLAUDE.md → `.claude/rules/` の順に必要分を読む
6. 過去の判断は `.claude_data/state/decisions.md`（**末尾に進行中の phase 09 の節がある**）+
   「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**phase 09 は task_07 の 2 本立てレビューで見つかったグローバル上書き経路を task_07b で塞ぎ、自動確認は全て green。残るは task_07 の実機目視（16 項目・ユーザー実施）→ task_08 正本反映**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（phase 09 task_07b 完了時・コミット `3bf2e05`）:
compile **clean** / tests **229** / tests_ui **206** / smoke **pass** / manual **未実施（task_07 の目視が残っている）**。
**件数が減ったら退行を疑う**。実行後に worktree ルートへ `user/` が生成されていないことも確認する。

## 次アクション（session.md.next_action より）
- **【ユーザー作業・これが残り全部】task_07 の実機目視 16 項目**。観点は
  `tasks/task_07_integration_check.md` **§3 の表**が正（受入条件との対応付き）。
  **特に重要 = 項目 11**（無効な個別パスで既定パスへ寄る＝【O3】）と **項目 15**（**手動移行の 2 段**）。
  **task_07b のガードが入った状態**で行う（`global/` 配下や config.json と同一への保存が拒否される）。
  目視で不具合が出たら **task_07 内で是正**（最小差分 + `reviewer` 再実施）。
- 2 本立てレビュー（`deep-reviewer` + `codex-adversarial-reviewer`）は**実施済み**。
  **指摘の採否は決着済み**（`decisions.md` の「task_07 レビュー」節に一覧）。
- 次に **task_08 = 正本反映（最終）**: `data_schema.md` §5.10 改訂 + §5.5 / §5.4 / §5.8.8 / §5.1 +
  `codebase_map.md` / 暫定仕様 08 を凍結 / `decisions_archive/09_per_keymap_set_presets.md` 作成 /
  `current.md` 完了更新 / `backlog/INDEX.md` の idea_08 を `INDEX_done.md` へ移動 / `/refactor_check`。
  - **task_08 の着手前に直す（レビュー指摘 N8）**: **暫定仕様 §7 の反映対象記述**が v0.3 時点の
    「**プリセット単独の注入が入るため**」「**トグル時の単独注入**」のままで、**v0.4【I 撤回】および
    実装（単独注入 API なし）と矛盾**する。**直さないと正本に誤記が入る**。`phase.md:21` の
    「主入力（v0.4）」表記も v0.7 へ更新する。
  - **正本へ追加する（N9）**: 入口台帳 §5.8.8 へ **「OFF 復帰時のグローバル再読込」経路**を追加
    （E1〜E5 のどれでもない新しい供給点。hook キー単独注入と同型の例外として列挙）。
- 各タスクの流れ: タスク定義起票 → codex-implementer へ委任 → **verifier で実測** → reviewer → コミット。

## 現フェーズ（phase 09 = keymap_set ごとの個別プリセット）の要点

**確定設計は暫定仕様 08（v0.7）が正**。**実装は task_01〜07b まで完了**（残りは実機目視 → task_08）。

- **ファイル配置**: グローバル既定 = **`user/hotkey_presets/global/default.json`**（**移行は手動 2 段**＝
  ①ファイル移動 ②**config.json の明示値も書き換え**）/ 個別 = **`user/hotkey_presets/<stem>.json`**（直下）。
  **`global/` は予約ディレクトリ**（v0.7【G】）。
- **keymap_set のキー**: **`hotkey_presets_individual`（bool・既定 false）** + **`hotkey_presets_path`**。
  **【最重要】判定は値のみ**。**`resolve_hook_keys_individual`（フラグ無し + 非空なら ON）を流用しない**
  （流用すると phase 08 の**残置パスが個別指定として復活**する）。**OFF でもパスは空文字化しない**【N】。
- **解決順序**: **個別が有効なら個別 → `None` ならグローバル → それも `None` なら置き換えない**。
  **判定は `is None`**（`[]` は falsy。真偽で書くと「読めた空」がフォールバックする）。
- **有効判定は 1 関数**（`resolve_individual_hotkey_presets_path`）で、**読み出し / 保存先算出 / UI 表示の
  3 箇所が共有**する（分岐を二重化しない）。**比較専用 API**（`is_path_within` / `canonical_path`）を使い、
  **canonical 値を保存値・表示値へ混ぜない**。
- **書込先の分岐**: 有効な個別パス → そのパス / **未設定 “または” config 外（無効）→ 既定パスへ寄せて
  新規作成**【O3・v0.6 で拒否から反転】/ OFF → グローバル。
  **その後【O4・v0.7】の最終関門**で、保存先が **`global/` 配下** または **グローバルの読み先と同一**なら
  **拒否**（理由 2 種・文言は `hotkey_presets_io` に集約）。**ON→OFF の確定と OFF のままの保存は対象外**。
- **dirty**: **フラグ変化時** + **`hotkey_presets_path` の値の変化時**だけ。**内容編集では立てない**。
- **書き手はプリセットマネージャ 1 本**。**保存カスケードは書かない**。
  別名保存の追随は **`shutil.copyfile` によるファイル複製のみ**（runtime の内容を書き出さない）で、
  **保存先そのものが変わったとき（`save_path != keymap_set_path`）だけ**走る。
- **E1〜E4 は常にグローバル**（`apply_global_defaults` は無変更）。**E5（Import）は強制 OFF**
  （`load_legacy_runtime_data` 直後・`apply_global_defaults` 直前の 1 箇所）。
- **既知の制約（v0.7 で明記・挙動は変えない）**: 残置パスの初回 ON で旧ファイルを上書き /
  複製失敗は本体保存ごと中止 / OFF 復帰時にグローバルが読めないと個別内容が維持され次の保存で書かれる。

## 直前フェーズ（phase 08 = プリセットの config.json グローバル化）の要点

**正本が正**: `spec_detail/data_schema.md` **§5.10** + **§5.8.8**（入口台帳）+ §5.1 の例外 + `codebase_map.md`。
暫定仕様 07 は**凍結済**。判断履歴は `decisions_archive/08_hotkey_presets_global.md`。

- **全体デフォルトの注入は `ConfigService.apply_global_defaults` の 1 本**（**入口台帳 E1〜E5**）。
  **L1〜L3（通常読込）は経由しない**が供給規則は共通。**N1 は供給不要**。
- **プリセットの読み出しは `list | None`**（読めた＝空も採用 / 読めない＝置き換えない）。
  戻り値は**正規化済み**（trim / 小文字化 / **非 dict 要素と非文字列 `label`・`value` の要素を除去**）。
  **「読めたか」の判定は正規化の前**。**正規化は読み出し側 1 箇所**（緩めると起動不能が再発する）。
- **§5.1 の例外**: 役目を終えたキーは**生成停止**で自然消滅させる（**能動削除しない**）。
  ※ phase 09 で `hotkey_presets_path` は**個別パスとして復活**するため、
  **正本 §5.5 / §5.1 / §5.4 / §5.8.8 の改訂が phase 09 task_08 に入っている**。

## 注意事項・blockers
- **blockers: task_07 の完了に実機目視（ユーザー作業）が必要**。それまでフェーズ完了判定は出せない。
- **【運用】サブエージェントがセッション上限で失敗することがある**。その場合 `verifier` の実測は
  **メインが直接実行してよい**（`grep -v ResourceWarning | tail` で出力を絞る）。
  **必須レビュー（`reviewer` / `deep-reviewer`）は代替不可**。
- **【Codex 運用・重要】詰まったジョブに `taskkill /T` を使わない**（PID 再利用で**無関係な
  プロセスを巻き込む**。phase 09 task_04 で `node_repl` 約 22 個を巻き込んだ実害あり）。
  **`codex_operations.md` §4 の state 手修復**（backup → `cancelled` へ書換・`.log` は保全）に倒す。
- **【Codex 運用】**フォワーダが最終出力を返さず完了通知だけ来る / 差分 0 件で返ることがある
  → `SendMessage` で同じフォワーダを再開して回収する。**Codex 申告のテスト結果は信用せず必ず実測**。
  **報告が「実装物なし」でも鵜呑みにせず `git status` / `git log` で自分で確かめる**。
  フォワーダは**メインが入れた `instructions/` の差分を「未申告の scope creep」として報告してくる**ことがある。
- **【config_service の配置制約】`config_service` はパッケージ**（`keyseq/application/config_service/`）で
  **ConfigService 本体は `__init__.py`**。テストが
  `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため、
  この配置を崩すと壊れる。同じ理由で**パス基盤メソッドを兄弟モジュールへ移さない**。
  兄弟 = `save_plan_execution.py` / `split_payloads.py` / `save_path_resolution.py` / `split_loading.py`。
  抽出関数は **`service` を第 1 引数に取る**。**兄弟から `__init__` を import しない**（循環回避）。
- **【最重要・2 度踏んだ罠】パス表記の混在事故**: runtime の `source_path` 3 種と
  `hotkey_presets_path` は **config 配下なら相対**で保持される（config 外は絶対・区切りは `/` 正規化）。
  **相対値を `os.path.abspath` / `dirname` / `exists` / `join` へ解決なしで渡すと cwd 基準で解決される**。
  症状 = **リポジトリルートに `user/` が生成される** / 「別名で保存」が前回の場所に開かない。
  解決は `ConfigService.resolve_config_path(path, config_root)`。
  `to_config_relative_or_absolute` は**入口で解決するので相対を渡してよい**。
- **不変条件（壊しやすい）**: ① `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致**（入口は `dirty_state` のメソッドのみ）/
  ② 子の `_parent_refs` は**保存先ファイルの集合 + 現在の上位**（in-memory の旧 refs を持ち込まない）/
  ③ **canonical identity は比較専用**（`normcase` 済み文字列を保存値・戻り値・表示へ混入させない）/
  ④ **共有状況は判定名で分岐する**（`SHARE_SOLE` / `SHARE_NEW`。表示文言で分岐しない）。
- **【hook キー（phase γ）】キー名の定義元は `domain/config.py`**（`HOOK_STOP_KEY` / `HOOK_TOGGLE_KEY` /
  対のタプル `HOOK_KEY_FIELDS` / `normalize_hook_key_pair`）。新規箇所はリテラルを書かない
  （**添字参照 `HOOK_KEY_FIELDS[0]` は禁止**）。**明示列挙のまま残す 3 箇所** = `DEFAULT_CONFIG` /
  `split_payloads` の保存 dict キー / `startup_io` の保存 dict キー。
  **保存 JSON のキー順は `tests/test_save_plan.py::test_saved_keymap_set_json_keeps_stable_key_order` が固定**。
  config.json への書き込みは `StartupIo.write_startup`（`-> bool`）に集約する
  （**別経路で read-modify-write しない**）。仕様は `data_schema.md` §5.9 + `key_input.md` §7.6。
- **【config.json のキーは増えない】`build_startup_payload` は既存キーを引き継ぐだけ**なので、
  `hotkey_presets_path` の**明示値が存在するのはユーザーが手で書いたときだけ**。ただし
  **一度書かれると保存の round-trip で永久に保持される**（【O4】ガードの背景）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  テスト内の `AssertionError` も広い `except Exception` に捕まり、**失敗が「ハング」に化ける**。
  tests_ui の 4 ファイル（`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup` / `test_app_ui_flows`）の `setUp` に
  **fail-fast ガード**がある。期待するテストは個別 patch で上書きする。新しいモーダルを増やすときは
  **ガードが見ているファイル（`hotkey_presets_io` 等）へモーダルを集約する**のが安全。
  **ハングしたら `messagebox` / `filedialog` を全遮断して単独実行**する。
- **【tests_ui の罠】`AppUiFlowsTest` は `setUpClass` で App を 1 つ共有する**。
  `dirty_tracker.has_unsaved_changes()` は個別 dirty も OR するため、
  **絶対値で assert せず前後の変化・`set_dirty` の呼出有無で見る**。
- **【tests_ui の罠】`_prepare_loaded_keymap_set` は `save_plan=None` で `save_runtime_data` を呼ぶため
  runtime に source_path が入らない**。source_path 前提のテストは保存後に
  `load_runtime_data_from_keymap_set_path` → `apply_loaded_data_to_ui` で読み直すこと。
- **【tests_ui の罠】特性テストは `config_service` の生成系をスタブ dict で差し替える**。
  runtime へキーを増やす変更を入れると `assertEqual(self.app.data, {...})` が落ちる。
  **実装ではなくテスト側の追従で正しい**。
- **【tests_ui のノイズ】`invalid command name "..._clear_flash_message"`** は破棄後の `after` 発火で、
  結果が `OK` なら無害。`ResourceWarning: unclosed file` も同様。
- **【教訓・UI】tkinter の「初期表示だけ崩れる」系は one-shot の再計算では直らない**。
  **対象ウィジェット自身の `<Configure>` で自己修復させる**（同幅早期 return を必ず併設）。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。PowerShell の here-string（`@'...'@`）は**コミットメッセージに `@` が混入する**。
  複数行メッセージは**スクラッチパッドへファイルを書いて `git commit -F <file>`** が確実。
- **【罠】`git grep` は追跡済みのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。行数計測は `wc -l`。
- **【傾向】reviewer が「完了可」でも実測・別レビューで問題が出る**。**判定はテストの実測が優先**。
  fail が出たら**まず production か test かを切り分ける**。**フェーズ完了時は Claude 側 × Codex 側の
  2 本立てを省略しない**（phase 08・09 とも**両者が独立に同じ穴を検出**した）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **08_hotkey_presets_global** / 07_hook_keys_global_default / 06_child_file_save_dialog）。
  提案書「計画05」「計画06」は完了済みで、**どちらもフェーズ番号を消費していない**。
- 未着手/保留 idea: idea_07（参照元の掃除・着手可）/ idea_03（hotkey 保存正規化・低）/
  idea_09（レガシー保存パス・低）/ idea_04・idea_06（保留）。**idea_08 は phase 09 で着手中**。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
