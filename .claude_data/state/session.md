# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-08-15T09:40:00
phase: `instructions/phase/09_per_keymap_set_presets`（**暫定仕様 08 を v0.9 へ改訂・ユーザー確定済**。**task_07f まで完了＝v0.9 の実装も入った**。次は実機目視の追加 4 項目〔ユーザー作業〕）
last_commit_location: claude/jikki-mokushi-ok-9c0a52 ※現在地はセッション開始時の git 実測値が正

## current
focus: **v0.8 の実機目視は OK。フェーズ完了判定前レビューで出た 2 件を仕様 v0.9（【S】上書き確認 /【I2】OFF 開時の一覧確定）として確定し、task_07f で実装完了。残るは追加 4 項目の実機目視〔ユーザー作業〕→ task_08 正本反映**。
mode: blocked

## last_action
ts: 2026-08-15T09:40:00
who: main
summary: |
  【**v0.8 の実機目視 OK → フェーズ完了判定前レビュー → 仕様 v0.9 確定 → task_07f 完了**】
  - **ユーザーが実機目視 OK を報告**（v0.8 の期待値・16 項目）。task_07 §2 の 2 本立てを
    **v0.8 分の差分 `b6ca866..HEAD`** に対して実施（前回は task_01〜07b が対象だったため）。
    - `codex-adversarial-reviewer` = **symlink 1 件のみ**（2026-08-10 と同一指摘）→ **前回どおり除外**。
    - `deep-reviewer` = **修正要（中 2 件）**。根因は共通で、**v0.8 の「切替先を読んでから書く」保証が
      トグル経路にしかない**こと。
  - **【仕様 v0.9・ユーザー確定】** ①**【S】個別へ書く直前の上書き確認**（保存先の実体があり、
    **その内容がダイアログの読み込んだ一覧と異なる / 読めない**ときだけ）②**【I2】OFF で開いた時点の
    一覧確定**（ON は【E】維持のため対象外）。受入条件 **19 / 20** を追加。
    - **敵対的レビュー High で当初案を修正**: ③を「読み出し元パスとの比較」で書いていたが、
      **別名保存【L】でコピー先の実体を採用すると素通りする**ため **内容比較**へ変更した。
    - 残り 2 件 = **原子性（確認中の競合）除外** / **正本 §5.10.4 との優先関係は task_08 で明記**。
  - **task_07f 実装完了**（Codex 委任）。application に判定 API
    （`individual_hotkey_presets_overwrite_conflict`）+ `ConfigService` 委譲、`app.py` は
    **【O3】→【O4】→【S】→ 書込**の順、モーダルは `hotkey_presets_io` へ集約、
    `dialogs.py` は **OFF のときだけ**開始時に一覧を確定し `on_ok` は `_loaded_temp` を渡す。
  - **`reviewer` = 完了可**（差し戻し無し・参考指摘 1 件のみ）。**追加テスト 1 本**（config 外からの
    寄せ先で確認が出る）は v0.9【S】の範囲内として**採用**。
result_files:
  - instructions/history/08_per_keymap_set_presets.md（**v0.9**）
  - instructions/phase/09_per_keymap_set_presets/tasks/task_07f_overwrite_confirm_and_off_open_sync.md（新規）
  - instructions/phase/09_per_keymap_set_presets/phase.md / tasks/task_07_integration_check.md（目視 項目 17〜19）
  - keyseq/application/config_service/split_loading.py / __init__.py（判定 API + 委譲）
  - keyseq/presentation/app.py / controllers/config_io/hotkey_presets_io.py / dialogs.py
  - tests/test_config_service.py（+5）/ tests_ui/test_app_ui_flows.py（+7）
verified:
  compile: clean
  tests: pass **242**（基準線 237 → +5）
  tests_ui: pass **220**（基準線 213 → +7・ハングなし）
  smoke: pass
  review: `reviewer` = **完了可**。受入条件 19 の発火/非発火の表・「いいえ」で data/dirty/ファイル不変・
    判定=application / モーダル=presentation・【O3】【O4】の順序と挙動不変・**【I2】が ON へ波及していない**・
    トグル（07e）契約の維持・fail-fast ガード（他 3 ファイルは `tkinter.messagebox` 直パッチで捕捉済み）を確認
  note: `tests/test_config_service.py` に `ResourceWarning: unclosed file` が数件（**今回の追加分に `open(` は無く既存由来**・pass）

## next_action
- **【ユーザー作業・ブロッカー】追加 4 項目の実機目視**（`tasks/task_07_integration_check.md` §3 の表。
  **v0.8 分〔項目 1〜16〕は 2026-08-15 に OK 済**なので、やり直すのは
  **13**〔別名保存の複製・17 の前提操作〕/ **17**〔別名保存で既存名へ上書き → ON + OK で**上書き確認が出て、
  いいえ なら何も変わらない**〕/ **18**〔通常 ON 編集・初回 ON・OFF の OK で**確認が出ない**〕/
  **19**〔グローバル削除 + 個別 ON セットの Import → OFF のままマネージャを開くと**組込既定に揃い、
  OK で組込既定が書かれる**〕の 4 つ）。結果をメインセッションへ報告してもらう。
  - 目視で不具合が出たら **task_07 内で是正**（最小差分 + `reviewer` 再実施）。仕様変更を伴うなら
    **枝番タスクへ切り出す**（07b〜07f と同じ流儀）。
- その後 **task_08 = 正本反映（最終）**: `data_schema.md` §5.10 改訂 + **§5.10.4（v0.9）** + §5.5 / §5.4 / §5.8.8 / §5.1 +
  `codebase_map.md` / 暫定仕様 08 を凍結 / `decisions_archive/09_per_keymap_set_presets.md` 作成 /
  `current.md` 完了更新 / `backlog/INDEX.md` の idea_08 を `INDEX_done.md` へ移動 / `/refactor_check`。
  - **正本へ追加する項目（N9）**: 入口台帳 §5.8.8 へ **「OFF 復帰時のグローバル再読込」経路**を
    追加する（E1〜E5 のどれでもない新しい供給点）。**プリセット単独の注入 API は増やさない**ことも明記。
  - **§5.10.4（v0.9）**: 「読めないときは入口経路ごとの内容で確定する（Import ならインライン値）」は
    **OFF でマネージャを開いた場合には当てはまらない**（【I2】で表示元へ確定する）ことと、
    **【S】の上書き確認**を追記する。**【I2】は runtime 注入ではなく表示用再読込**である旨も併記。
  - **v0.5→v0.6 の反転（【O3】）/ v0.7 の【O4】/ v0.8 の 3 改訂 / v0.9 の【S】【I2】/ dirty 規則 /
    task_05b が task_05c で置き換わった経緯**を decisions_archive へ集約すること。
- 各タスク共通の流れ: 実装委任（**テスト追加まで含める / 実行は依頼しない**）→ `verifier` で実測 →
  `reviewer` → `/save_state` + `/task_commit`。

## blockers
- **task_07 の完了に実機目視（ユーザー作業）が必要**。それまでフェーズ完了判定は出せない。
  **v0.8 分は 2026-08-15 に OK 済**。**v0.9 の実装（task_07f）も入った**ので、
  残るは**追加 4 項目（13 / 17 / 18 / 19）**のみ。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **【暫定仕様 08 は v0.9 が正】**版が多いので**古い版の条項を引かない**。
  v0.8 の 3 点 = ①**フラグキーが無ければ残置 `hotkey_presets_path` も落とす**（判定はキーの**有無**。
  false + キーありは【N】で保持）②**【I】再採用**（トグルで一覧を読み直す・**【H2】撤回で OFF の OK も
  グローバルへ書く**・**グローバルが読めなければ組込既定へ差し替える**）③**【O2】config 外は読み出しのみ許容**
  （**書き込みは【O3】のまま管理下へ寄せる**＝読み書きで非対称なのは意図どおり）。
  v0.9 の 2 点 = ④**【S】個別へ書く直前の上書き確認**（**保存先の実体の内容 vs ダイアログが読み込んだ一覧**で
  判定。**出どころパスの比較にしない**＝別名保存でコピー先を共有すると素通りするため）
  ⑤**【I2】OFF で開いた時点の一覧確定**（**ON は対象外**＝【E】の引き継ぎを維持）。
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
- **【Codex 運用・重要】フォワーダが 2 分で切れても Codex ワーカーは生き続ける**（node ラッパだけが死に、
  ログパイプが切れて companion status は `running` のまま停滞する）。**ハングと即断しない**。
  判別は**作業ツリーの更新時刻**（対象ファイルが数十秒以内に更新され続けていれば作業中）。
  **書き換え途中で `verifier` / `reviewer` を回すと偽の結果を掴む**（phase 09 task_07e で実際に踏んだ）。
  ワーカー終了後は state が自己更新されないため `codex_operations.md` §4 で手修復する。
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
