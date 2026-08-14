# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-15T02:40:00
phase: `instructions/phase/09_per_keymap_set_presets`（**暫定仕様 08 を v0.8 へ改訂・ユーザー確定済**。**task_07c 完了 / task_07d・07e 未着手**。task_07 の実機目視はやり直し待ち）
last_commit_location: claude/preset-file-save-reference-903f03 ※現在地はセッション開始時の git 実測値が正

## current
focus: **task_07 の実機目視で見つかった 3 件（残置パス / トグル時の上書き / config 外パス）を仕様 v0.8 として確定し、是正タスク 07c・07d・07e へ分割。07c は完了（green + reviewer 完了可）で、次は 07d → 07e → 目視やり直し**。
mode: implementing

## last_action
ts: 2026-08-15T02:40:00
who: main
summary: |
  【**実機目視の 3 指摘 → 暫定仕様 v0.8 確定 → 是正タスク 3 本へ分割 → task_07c 完了**】
  - **ユーザーの実機目視（task_07 §3 の項目 2 / 7 / 10）で 3 件**。**いずれも実装バグではなく
    v0.7 の仕様どおりの挙動**だったが、実運用で破壊的なため**仕様側を改訂**した。
    - **項目 2**: 個別ファイルが `default.json` になる。**原因を実データで特定** =
      `config/user/keymap_sets/keymap_set1〜3.json`（phase 08 以前）に `hotkey_presets_individual`
      **キーが無く** `hotkey_presets_path` が**旧グローバル `user/hotkey_presets/default.json`** のまま
      残っており、v0.7 は**フラグだけ OFF に倒してパスは runtime へ載せていた**ため
      **初回 ON + OK の保存先が残置パス**になっていた（【M】の無警告共有が既定で発生・【O4】も素通り）。
    - **項目 7**: OFF → ON で**グローバルの内容が個別ファイルへ上書き**（【I 撤回】+【E】の帰結）。
    - **項目 10**: config 外パスは**読み出しでも無効**（【O2】v0.4）だったが、ユーザーの意図は
      「**読み出すが保存は管理下へ新規作成**」。
  - **ユーザー確定 = v0.8**: ①**フラグキーが無ければ残置パスも落とす**（false + キーありは保持＝【N】）
    ②**トグルで一覧を切替先から読み直す**（【I】再採用・**編集済みなら破棄確認**）+
    **【H2】撤回で OFF の OK もグローバルへ書く** ③**config 外は読み出しのみ許容**（書き込みは【O3】のまま）。
  - **`codex-adversarial-reviewer` = needs-attention（High 2 / Medium 3）**。**High 1 を採用**し、
    **「グローバルが読めなければ一覧を組込既定へ差し替える」**へ変更（v0.8 草案の「維持して書かない」は
    **閉じて開き直すと流出**するため却下記録 (D) へ）。**High 2 = 受入条件 15 の文言限定**（OFF 保存では
    置き換わらない）/ **M3 除外**（既知の制約）/ **M4 = 同期読み出しの制約を明記** /
    **M5 = 破棄確認モーダルの fail-fast ガードをタスク定義へ**。
  - **task_07c 完了**: `build_runtime_data_from_split` で **`hotkey_presets_individual` キーがある場合だけ
    `hotkey_presets_path` を runtime へ載せる**（1 行削除 + 4 行追加）。テスト 5 本追加。
    **`reviewer` = 完了可（必須修正なし）**。参考指摘 1 件（新規テストで `_load_keymap_set` ヘルパーを
    再利用できる・任意）。
result_files:
  - instructions/history/08_per_keymap_set_presets.md（**v0.8 へ改訂**）
  - .claude_data/state/decisions.md（仕様確定 v0.8 + 敵対的レビュー 5 件の採否）
  - instructions/phase/09_per_keymap_set_presets/phase.md（タスク 3 行追加 + v0.8 との矛盾解消）
  - instructions/phase/09_per_keymap_set_presets/tasks/task_07_integration_check.md（目視表を v0.8 へ・**項目 7b 追加**）
  - instructions/phase/09_per_keymap_set_presets/tasks/task_07c_residual_path_blocking.md（新規）
  - instructions/phase/09_per_keymap_set_presets/tasks/task_07d_external_path_read.md（新規）
  - instructions/phase/09_per_keymap_set_presets/tasks/task_07e_toggle_reload_and_off_write.md（新規）
  - keyseq/application/config_service/split_loading.py
  - tests/test_config_service.py / tests_ui/test_app_ui_flows.py
verified:
  compile: clean
  tests: pass **233**（基準線 229 → +4）
  tests_ui: pass **207**（基準線 206 → +1）
  smoke: pass
  review: `reviewer` = **完了可（必須修正なし）**。判定がキーの有無 / false + キーありでパス保持（【N】）/
    落とす場所が `build_runtime_data_from_split` の 1 箇所（domain・Import 経路へ波及なし）/
    他キーの引き継ぎ不変 / 後続タスク（07d・07e・08）の先取りなし を確認。**参考指摘 2 件**
    （`split_payloads` の二重評価 / `show_save_path_rejection` が理由 2 値以外を一律 global_conflict 扱い）

## next_action
- **task_07d を `codex-implementer` へ委任**（タスク定義 =
  `instructions/phase/09_per_keymap_set_presets/tasks/task_07d_external_path_read.md`）。
  要点 = **読み出し用のパス解決を新設**（config 外も許容）し `build_runtime_data_from_split` から使う /
  **書き込み用 `resolve_individual_hotkey_presets_path` は現状のまま**（【O3】【O4】・複製が依存）/
  `describe_hotkey_presets_source` の `invalid` の意味変更 + `format_preset_manager_source_labels` の文言 /
  **`tests_ui` の既存文言テスト 2 ケースの更新も実装範囲**。
- 続けて **task_07e**（`tasks/task_07e_toggle_reload_and_off_write.md`）。**07d の後**に着手する。
  要点 = トグルで一覧を読み直す（ON = 個別 / OFF = グローバル・**読めなければ組込既定**）+
  **破棄確認モーダル**（`tests_ui` 4 ファイルの fail-fast ガードへ `askyesno` を追加）+
  `App.save_hotkey_presets` の **ON→OFF 特別分岐（`app.py:420-428`）を削除**して OFF もグローバルへ書く。
- 3 タスク完了後 **【ユーザー作業】task_07 の実機目視をやり直す**
  （`tasks/task_07_integration_check.md` §3 の表。**項目 2 / 5 / 6 / 7 / 7b / 10 / 11 が v0.8 の期待値**。
  特に重要 = **7b**〔グローバル削除状態で ON→OFF〕/ **11**〔【O3】〕/ **15**〔手動移行の 2 段〕）。
- その後 **task_08 = 正本反映（最終）**: `data_schema.md` §5.10 改訂 + §5.5 / §5.4 / §5.8.8 / §5.1 +
  `codebase_map.md` / 暫定仕様 08 を凍結 / `decisions_archive/09_per_keymap_set_presets.md` 作成 /
  `current.md` 完了更新 / `backlog/INDEX.md` の idea_08 を `INDEX_done.md` へ移動 / `/refactor_check`。
  - **正本へ追加する項目（N9）**: 入口台帳 §5.8.8 へ **「OFF 復帰時のグローバル再読込」経路**を
    追加する（E1〜E5 のどれでもない新しい供給点）。**プリセット単独の注入 API は増やさない**ことも明記。
  - **v0.5→v0.6 の反転（【O3】）/ v0.7 の【O4】/ v0.8 の 3 改訂 / dirty 規則 /
    task_05b が task_05c で置き換わった経緯**を decisions_archive へ集約すること。
- 各タスク共通の流れ: 実装委任（**テスト追加まで含める / 実行は依頼しない**）→ `verifier` で実測 →
  `reviewer` → `/save_state` + `/task_commit`。

## blockers
- **task_07 の完了に実機目視（ユーザー作業）が必要**。それまでフェーズ完了判定は出せない。
  **07c / 07d / 07e が揃うまで目視はやり直さない**（途中で見ても期待値が変わる）。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **【暫定仕様 08 は v0.8 が正】**版が多いので**古い版の条項を引かない**。v0.8 で変わったのは 3 点 =
  ①**フラグキーが無ければ残置 `hotkey_presets_path` も落とす**（判定はキーの**有無**。false + キーありは
  【N】で保持）②**【I】再採用**（トグルで一覧を読み直す・**【H2】撤回で OFF の OK もグローバルへ書く**・
  **グローバルが読めなければ組込既定へ差し替える**）③**【O2】config 外は読み出しのみ許容**
  （**書き込みは【O3】のまま管理下へ寄せる**＝読み書きで非対称なのは意図どおり）。
- **【phase 08 の成果は正本が正】** `spec_detail/data_schema.md` **§5.10**（プリセットの全体ライブラリ）
  + **§5.8.8**（**全体デフォルトの入口台帳 E1〜E5 / L1〜L3 / N1**）+ §5.1 の例外 + `codebase_map.md`。
  暫定仕様 07 は**凍結済**。要点だけ再掲 = ①runtime を新規化・置換したら
  **`apply_global_defaults` を呼ぶ**（通常読込は経由しないが供給規則は共通 /
  **ON→OFF の hook キー単独注入だけ `apply_global_hook_key_defaults` を直呼び**）
  ②プリセットの読み出しは **`list | None`**（読めたら空でも採用 / `None` は置き換えない）で
  **読み出し側で正規化**（**非文字列 `label`/`value` の要素は除去**。ここを緩めると起動不能が再発する）
  ③**書き手は `PresetManagerDialog.on_ok` → `App.save_hotkey_presets` →
  `HotkeyPresetsIo` → `ConfigService.save_global_hotkey_presets` の 1 本のみ**
  （カスケードは書かない / 失敗時は確定せずダイアログを閉じない / dirty を汚さない）。
- **【tests_ui の罠・追加】`AppUiFlowsTest` は `setUpClass` で App を 1 つ共有する**ため、
  `has_unsaved_changes()` は他テストが残した個別 dirty も拾う。**絶対値で assert せず、
  前後の変化 / `set_dirty` の呼出有無で見る**こと（task_06 で 1 度踏んだ）。
- **hook キー（Phase γ の成果）は正本が正**: `spec_detail/data_schema.md` **§5.9** +
  `key_input.md` **§7.6** + `codebase_map.md`。暫定仕様 06 は**凍結済**（経緯の参照用）。
  要点だけ再掲 = **解決の分岐点は 4 つ**（`load_global_hook_keys` 読み出し /
  `build_runtime_data_from_split` 通常読込の選択 / `apply_global_hook_key_defaults` 新規化・置換経路
  〔**通常読込は経由しない**〕/ `build_keymap_set_payload` 保存側）。**フック層は無変更**が設計の芯。
- **【計画06 で変わった構造】hook キー名の定義元は `keyseq/domain/config.py` の `HOOK_STOP_KEY` /
  `HOOK_TOGGLE_KEY` / `HOOK_KEY_FIELDS`（対のタプル）+ `normalize_hook_key_pair()`**。新たに触る箇所は
  リテラルを書かずこれを使う（**添字参照 `HOOK_KEY_FIELDS[0]` は禁止**。反復・zip でのみタプルを使う）。
  意図的にリテラルのまま残した 3 箇所 = `DEFAULT_CONFIG` の既定値表 / `split_payloads` の返却 dict キー /
  `startup_io` の保存 dict キー。**保存 JSON のキー順は
  `tests/test_save_plan.py::test_saved_keymap_set_json_keeps_stable_key_order` が固定している**。
  `ensure_config_compatibility` と `build_keymap_set_payload` が `normalize_key_name` 直呼びのままなのは
  **非文字列時の例外を握り潰さないため**（`normalize_hook_key_pair` は `str()` を挟む）。
- **Phase β の成果も正本が正**: `data_schema.md` **§5.8**（子ファイルの保存計画と参照元記録）+
  §5.4 / §5.6 / §5.7、`features.md` §4.6、`codebase_map.md`。暫定仕様 05 は凍結済。
- **【最重要・2 度踏んだ罠】パス表記の混在事故**: runtime の `source_path` 3 種は **config 配下なら相対**で
  保持される（config 外は絶対・区切りは `/` 正規化）。**相対値を `os.path.abspath` / `dirname` / `exists` /
  `join` へ解決なしで渡すと cwd 基準で解決される**。症状 = **リポジトリルートに `user/` が生成される** /
  「別名で保存」が前回の場所に開かない。解決は `ConfigService.resolve_config_path(path, config_root)`。
  `to_config_relative_or_absolute` は**入口で解決するので相対を渡してよい**。
- **不変条件（壊しやすい）**: ① `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致**（入口は `dirty_state` のメソッドのみ）/
  ② 子の `_parent_refs` は**保存先ファイルの集合 + 現在の上位**（in-memory の旧 refs を持ち込まない）/
  ③ **canonical identity は比較専用**（`canonical_path` / `is_path_within` の 2 本。
  `normcase` 済み文字列を保存値・戻り値・表示へ混入させない）。
- **【共有状況の判定名と表示文言は別物】** 仕様書・タスク定義の「共有状況が単独 / 新規作成なら〜」は
  **判定名**（`SHARE_SOLE` / `SHARE_NEW`）を指す。**分岐は判定名で書き、文言で分岐しない**。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  tests_ui の 4 ファイル（`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup` / `test_app_ui_flows`）の
  `setUp` に **fail-fast ガード**がある。
  新しいモーダルを増やすときは同じガードを足す。**ハングしたら `messagebox` / `filedialog` を全遮断して
  単独実行**すると真因が一発で出る。
- **【tests_ui の罠】`_prepare_loaded_keymap_set` は `save_plan=None` で `save_runtime_data` を呼ぶため
  runtime に source_path が入らない**。source_path 前提のテストは保存後に
  `load_runtime_data_from_keymap_set_path` で読み直すこと。
- **【Codex 運用・重要】詰まったジョブに `taskkill /T` を使わない**（PID 再利用で**無関係な
  プロセスを巻き込む**。phase 09 task_04 で `node_repl` 約 22 個を巻き込んだ実害あり）。
  **`codex_operations.md` §4 の state 手修復**（backup してから `cancelled` へ書換・`.log` は保全）に倒す。
- **【Codex 運用】**フォワーダが最終出力を返さず完了通知だけ来ることがある（`SendMessage` で再開して回収）。
  **Codex 申告のテスト結果は信用せず必ず verifier で再実行**。**Codex は python をまったく実行できない**
  → 委任にテスト実行を含めない。手順書は `instructions/common/rules_detail/codex_operations.md`。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**（main 側を編集すると
  commit から漏れる）。`git grep` は追跡済みファイルのみ。行数計測は `wc -l`。
- **レビュアーは 2 本立て**: `reviewer`（sonnet・単一タスクの実装差分）/ `deep-reviewer`（opus・設計文書 /
  複数タスクを跨ぐ差分 / フェーズ完了判定）。使い分けは `.claude/rules/agent_selection.md` が正。
- **保存系リデザインの番号対応**: α=phase05/暫定04〔完了〕 / β=phase06/暫定05〔完了〕 /
  γ=phase07/暫定06〔完了〕 / プリセット=phase08/暫定07〔**完了**・decisions_archive 08〕 /
  **個別プリセット=phase09/暫定08〔着手中〕**。
  **計画05・計画06 はフェーズ番号を消費していない**（規範 = `modified_proposal/05_*.md` / `06_*.md`）。
- **【計画05 で変わった構造】`config_service` は単一ファイルではなく*パッケージ***
  （`keyseq/application/config_service/`）。**ConfigService 本体は `__init__.py`**
  （テストが `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため、
  この配置を崩すと 4 テストが壊れる。同じ理由で**パス基盤メソッドを兄弟へ移さない**）。
  兄弟 = `save_plan_execution.py` / `split_payloads.py` / `save_path_resolution.py` / `split_loading.py`。
  抽出関数は **`service` を第 1 引数に取る**。兄弟から `__init__` を import しない（循環回避）。
- config_io は `controllers/config_io/` へ分割済（App が `app.keymap_set_io` 等で直接公開）。
- 未着手 idea: idea_07（参照元の掃除・**着手可**）/ idea_03（hotkey 保存時正規化・優先度低）/
  idea_09（レガシー settings/ フォールバック・優先度低）。**idea_08 は phase 09 で着手中**。
  保留 idea: idea_04 / idea_06（**残る着手条件は「共通化の実需」1 つのみ**）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 06_child_file_save_dialog / 07_hook_keys_global_default /
  **08_hotkey_presets_global**。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
