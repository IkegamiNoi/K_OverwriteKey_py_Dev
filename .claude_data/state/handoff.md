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
2. `instructions/phase/current.md` を読む。**アクティブなフェーズは無い**（phase 09 完了）ため、
   **着手前にユーザーへ次フェーズの方針を確認する**
3. 方針が決まったら `/phase_start` で起票する（**フェーズ = `10_<topic>` / 暫定仕様 = `09_<topic>` /
   リファクタ提案書 = `08_<topic>`**）
4. 仕様は**正本 `instructions/common/spec_detail/` が正**（暫定仕様 04〜08 はすべて**凍結済**＝経緯の参照用。
   **凍結済の条項を実装の根拠に引かない**）
5. CLAUDE.md → `.claude/rules/` の順に必要分を読む
6. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`

## 現在の作業の 1 行サマリ
**phase 09（keymap_set ごとの個別プリセット）完了**。task_08 = 正本反映まで済み、暫定仕様 08 は凍結。
次は**次フェーズの方針決め**（候補 = 提案書 07 のリファクタ / idea_07 / idea_10 / idea_11）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（phase 09 完了時・コミット `7409237`）:
compile **clean** / tests **238** / tests_ui **223** / smoke **pass** /
manual **実機目視は全項目 OK**（v0.8 分 = 2026-08-15 / v0.9・v0.10 分 = 2026-08-16）。
**件数が減ったら退行を疑う**。実行後に worktree ルートへ `user/` が生成されていないことも確認する。

## 次アクション（session.md.next_action より）
- **次フェーズの方針をユーザーへ確認する**（`instructions/phase/current.md`「次フェーズ候補」）:
  - **提案書 [07_refactor_per_keymap_set_presets](../../instructions/modified_proposal/07_refactor_per_keymap_set_presets.md)**
    （**未承認**。`/refactor_check` = 推奨。①`PresetManagerDialog.__init__` 99 行の UI 構築抽出
    ②`dialogs.py` 1016 行の `dialogs/` パッケージ化 ③`__init__.py:435` の直値を定数由来へ）。
    承認する場合は **(a) 追加タスク / (b) 独立ミニ計画**のどちらかをユーザーに選んでもらう
  - **idea_07**（参照元の掃除・**着手可**）/ **idea_10**（ネストしたモーダルの grab 復元）/
    **idea_11**（別名保存の複製ロールバック・**優先度低**）
- 各タスクの流れ: タスク定義起票 → codex-implementer へ委任 → **verifier で実測** → reviewer → コミット。

## 直前フェーズ（phase 09 = keymap_set ごとの個別プリセット）の要点

**正本が正**: `spec_detail/data_schema.md` **§5.10**（全体ライブラリと個別指定）+ **§5.8.8**（入口台帳）+
§5.5 / §5.4 / §5.1 + `codebase_map.md`。暫定仕様 08 は**凍結済**。
判断履歴は `decisions_archive/09_per_keymap_set_presets.md`。

- **配置**: グローバル = **`user/hotkey_presets/global/default.json`**（`global/` は**予約ディレクトリ**・
  **移行は手動 2 段**＝ファイル移動 + config.json の明示値の書き換え）/
  個別 = **`user/hotkey_presets/<stem>.json`**（直下）。
- **keymap_set のキー**: `hotkey_presets_individual`（bool・既定 false）+ `hotkey_presets_path`（常に出力）。
  **フラグは値で判定**し、**フラグ*キー*が無ければ残置パスも runtime へ載せない**（判定は**キーの有無**）。
- **解決順序**: 個別が有効なら個別 → `None` ならグローバル → それも `None` なら**置き換えない**。
  **判定は `is None`**（`[]` は falsy。真偽で書くと「読めた空」がフォールバックする）。
- **パス解決は読み出し用と書き込み用の 2 本立て**（混線させない）:
  読み出し `resolve_individual_hotkey_presets_read_path` = **config 外もそのまま** /
  書き込み `resolve_individual_hotkey_presets_path` = **config 外は空文字**。
- **書き込み前の判定は 3 段**: ①**未設定 / 空 / 非文字列 / config 外なら既定パスへ寄せる**
  → ②**`global/` 配下・グローバルと同一なら拒否** → ③**上書き確認**（**保存先の実体 vs
  ダイアログが読み込んだ一覧**の**内容比較**。出どころパスの比較にしない）→ 書き込み。
  確認は **3 択**（上書きする / 既存を読み込む / キャンセル。**破損時は 2 択**）。
  **adopt / cancel はどちらも書かず閉じない**（`data`・dirty・ファイル不変）。
- **マネージャのトグルは一覧も切り替える**（ON = 個別 / OFF = グローバル、読めなければ**組込既定**）。
  **OFF での OK もグローバルへ書く**（書かれるのは組込既定なので個別の内容は流出しない）。
  **OFF で開いた時点も表示元へ確定**（ON では確定しない）。**読み直しは表示のみ**で runtime 反映は OK のとき。
- **dirty**: フラグ変化時 + **`hotkey_presets_path` の値の変化時**だけ。**内容編集では立てない**。
- **書き手はマネージャ 1 本**。**保存カスケードは書かない**。**プリセット単独の注入 API を作らない**。
  **E1〜E4 は常にグローバル / E5（Import）は強制 OFF**。別名保存の追随は**ファイル複製のみ**。
- **既知の制約**: 同一 stem の無警告共有 / フラグキーを持つ keymap_set の手編集パスはそのまま使う /
  壊れたグローバルは退避されず上書きされる / **別名保存の複製が部分成功し得る（idea_11）**。

## 注意事項・blockers
- **blockers: なし**（phase 09 は完了。次フェーズ未確定なので方針確認から）。
- **【既知・触らない】ネストしたモーダルを閉じると親の grab が復元されない**
  （**既存の「追加」「編集」も同じ**）。**idea_10 として分離済**で、
  **新しいダイアログにも復元処理を書かない**（挙動を揃えるため）。
- **【既知・idea_11】別名保存で個別プリセットの複製に成功した後、keymap_set の保存が失敗すると
  巻き戻らない**（孤児の複製 + メモリ上だけ新パス・dirty も立たない）。**正本 §5.10.4 に明記済**。
  この状態で再編集しても**内容が一致するため上書き確認は出ない**。
- **【Codex 運用・最重要】フォワーダが 2 分で切れても Codex ワーカーは生き続ける**（node ラッパだけが死に、
  companion status は `running` のまま停滞する）。**ハングと即断しない**。
  判別は**作業ツリーの更新時刻**。**書き換え途中で `verifier` / `reviewer` を回すと偽の結果を掴む**。
  ワーカー終了後は state が自己更新されないため `codex_operations.md` §4 で手修復する。
- **【Codex 運用】詰まったジョブに `taskkill /T` を使わない**（PID 再利用で**無関係なプロセスを巻き込む**。
  実害あり）。**§4 の state 手修復**に倒す。
- **【Codex 運用】**フォワーダが最終出力を返さず完了通知だけ来る / 差分 0 件で返ることがある
  → `SendMessage` で同じフォワーダを再開して回収する。**Codex 申告のテスト結果は信用せず必ず実測**。
- **【config_service の配置制約】`config_service` はパッケージ**で **ConfigService 本体は `__init__.py`**。
  テストが `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため、
  この配置を崩すと壊れる。同じ理由で**パス基盤メソッドを兄弟モジュールへ移さない**。
  兄弟 = `save_plan_execution.py` / `split_payloads.py` / `save_path_resolution.py` / `split_loading.py`。
  抽出関数は **`service` を第 1 引数に取る**。**兄弟から `__init__` を import しない**（循環回避）。
  **presentation から兄弟モジュールを直接 import しない**（公開面は `ConfigService` の委譲メソッド）。
- **【最重要・2 度踏んだ罠】パス表記の混在事故**: runtime の `source_path` 3 種と
  `hotkey_presets_path` は **config 配下なら相対**で保持される（config 外は絶対・区切りは `/` 正規化）。
  **相対値を `os.path.abspath` / `dirname` / `exists` / `join` へ解決なしで渡すと cwd 基準で解決される**。
  症状 = **リポジトリルートに `user/` が生成される** / 「別名で保存」が前回の場所に開かない。
  解決は `ConfigService.resolve_config_path(path, config_root)`。
  `to_config_relative_or_absolute` は**入口で解決するので相対を渡してよい**。
- **不変条件（壊しやすい）**: ① `dirty_tracker.trigger_set_source_path` と
  `data[INTERNAL_TRIGGER_SET_SOURCE_PATH]` は**常に一致** / ② 子の `_parent_refs` は
  **保存先ファイルの集合 + 現在の上位** / ③ **canonical identity は比較専用**
  （`normcase` 済み文字列を保存値・戻り値・表示へ混入させない）/
  ④ **共有状況は判定名で分岐する**（`SHARE_SOLE` / `SHARE_NEW`。表示文言で分岐しない）。
- **【hook キー】キー名の定義元は `domain/config.py`**（`HOOK_STOP_KEY` / `HOOK_TOGGLE_KEY` /
  対のタプル `HOOK_KEY_FIELDS` / `normalize_hook_key_pair`）。新規箇所はリテラルを書かない
  （**添字参照 `HOOK_KEY_FIELDS[0]` は禁止**）。**明示列挙のまま残す 3 箇所** = `DEFAULT_CONFIG` /
  `split_payloads` の保存 dict キー / `startup_io` の保存 dict キー。
  **保存 JSON のキー順は `tests/test_save_plan.py::test_saved_keymap_set_json_keeps_stable_key_order` が固定**。
  config.json への書き込みは `StartupIo.write_startup`（`-> bool`）に集約する。
- **【config.json のキーは増えない】`build_startup_payload` は既存キーを引き継ぐだけ**なので、
  `hotkey_presets_path` の**明示値が存在するのはユーザーが手で書いたときだけ**。ただし
  **一度書かれると保存の round-trip で永久に保持される**（保存先ガードの背景）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**。
  テスト内の `AssertionError` も広い `except Exception` に捕まり、**失敗が「ハング」に化ける**。
  tests_ui の 4 ファイル（`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup` / `test_app_ui_flows`）の `setUp` に
  **fail-fast ガード**がある（`showerror` + **`askyesno`**）。新しいモーダルを増やすときは
  **4 ファイル全部のガードを更新する**。**ハングしたら `messagebox` / `filedialog` を全遮断して単独実行**する。
- **【tests_ui の罠】`AppUiFlowsTest` は `setUpClass` で App を 1 つ共有する**。
  `has_unsaved_changes()` は個別 dirty も OR するため、**絶対値で assert せず前後の変化で見る**。
- **【tests_ui の罠】`_prepare_loaded_keymap_set` は `save_plan=None` で `save_runtime_data` を呼ぶため
  runtime に source_path が入らない**。source_path 前提のテストは保存後に読み直すこと。
- **【tests_ui の罠】特性テストは `config_service` の生成系をスタブ dict で差し替える**。
  runtime へキーを増やすと `assertEqual(self.app.data, {...})` が落ちる。**テスト側の追従が正しい**。
- **【tests_ui のノイズ】`invalid command name "..._clear_flash_message"`** は破棄後の `after` 発火で、
  結果が `OK` なら無害。`ResourceWarning: unclosed file` も同様。
- **【教訓・UI】tkinter の「初期表示だけ崩れる」系は one-shot の再計算では直らない**。
  **対象ウィジェット自身の `<Configure>` で自己修復させる**（同幅早期 return を必ず併設）。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。PowerShell の here-string（`@'...'@`）は**コミットメッセージに `@` が混入する**。
  複数行メッセージは **heredoc** が確実。
- **【罠】`git grep` は追跡済みのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。行数計測は `wc -l`。
- **【傾向】reviewer が「完了可」でも実測・別レビューで問題が出る**。**判定はテストの実測が優先**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**
  （phase 08・09 とも**両者が独立に同じ穴を検出**した）。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  Codex レビュー系との併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: **09_per_keymap_set_presets** / 08_hotkey_presets_global / 07_hook_keys_global_default）。
  提案書「計画05」「計画06」は完了済みで、**どちらもフェーズ番号を消費していない**。
- 未着手/保留 idea: idea_07（参照元の掃除・着手可）/ **idea_10**（ネストしたモーダルの grab 復元）/
  **idea_11**（別名保存の複製ロールバック・低）/ idea_03（hotkey 保存正規化・低）/
  idea_09（レガシー保存パス・低）/ idea_04・idea_06（保留）。**idea_08 は phase 09 で完了**。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
