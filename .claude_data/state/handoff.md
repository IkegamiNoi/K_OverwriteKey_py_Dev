# handoff.md

過去の会話履歴は参照しないでください。
このファイルと `.claude_data/state/session.md` を起点に作業を再開してください。

## プロジェクト概要
- 言語/実行: Python（tkinter GUI）。オニオン構成（presentation / application / domain / infrastructure）。
- 対象アプリ: keyseq（キー割り当て/オーバーライドツール）。全体仕様は `instructions/common/`（`app_overview.md` / `codebase_map.md`）参照。
- **python 実行は必ずリポジトリルートの `.venv` を使う**（worktree相対 `..\..\..\.venv\Scripts\python.exe`）。
  依存 keyboard/pyautogui/pynput はこの `.venv` にのみ導入済み。グローバル `py` は使わない（tests_ui/smoke が落ちる）。

## 再開手順
1. `.claude_data/state/session.md` を読む（最重要・最新状態）
2. `.claude_data/state/decisions.md` を読む（判断履歴。phase 04 セクション + 完了フェーズは「アーカイブ索引」→ `decisions_archive/<phase>.md`）
3. CLAUDE.md → `instructions/phase/current.md`（**アクティブ: phase 04**）→ `.claude/rules/` の順に必要分を読む
4. **設計の正は暫定仕様 [03_config_io_controller_split.md](../../instructions/history/03_config_io_controller_split.md)（v0.4・ユーザー確定済）**。
   番号対応: phase 04 / 暫定 03 / decisions 04
5. session.md.next_action から作業を再開する

## 現在の作業の 1 行サマリ
**phase 04 task_05（ConfigIo ファサード削除 + 呼び出し元30箇所を6分割オブジェクトへ差し替え・案B）完了。分割は全完了（config_io 名消滅・全緑）。残るは task_06（正本反映）のみで、その前に実機目視のユーザー必須ゲート待ち**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ず .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests_ui
../../../.venv/Scripts/python.exe -m unittest tests_ui.test_config_io_characterization
../../../.venv/Scripts/python.exe -m unittest tests_ui.test_config_io_characterization_keymap_set_startup
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
session.md.verified（compile clean / char① 19 pass / char② 35 pass / tests 86 / tests_ui 74 / smoke pass）と一致することを確認する。
`grep -rn "config_io\." keyseq main.py tests tests_ui --include=*.py` が `config_io/` パッケージ import 以外に残らないこと。

## 次アクション（session.md.next_action より）
- **【最優先・ユーザー必須ゲート】実機目視を依頼する**。task_05 完了で分割は全完了。**task_06（正本反映）に進む前に
  ユーザーが実機でアプリを動かして確認**する: 保存 / 読込 / 別名で保存 / Import / Export / 起動時に読む構成セット指定 /
  keymap・トリガー一覧・出力シーケンスの個別 保存・読込。**目視 OK を得るまで task_06 に着手しない**。
- **実機目視 OK 後に task_06（正本反映）を起票・着手**（実装はメイン=文書作業）:
  - `codebase_map.md` の「コントローラ（controllers/）」節を更新（ConfigIoController 削除 / config_io パッケージ6クラス
    〔KeymapSetIo/StartupIo/IoDialogs/KeymapFileIo/TriggerSetFileIo/SequenceFileIo〕を `app.<名>.<method>` で参照する構成へ / ツリー図 :44）。
  - **暫定仕様 03 を凍結**（ヘッダを「凍結・正本反映済」へ）。**spec_detail 昇格の要否を判定**（§8: grep で config_io の担当層記述が
    spec_detail にあるか。無ければ昇格不要＝担当層は codebase_map.md が正）。
  - `decisions_archive/04_config_io_controller_split.md` を作成し decisions.md phase 04 セクションを集約・索引化。
  - `current.md` 完了記載・次採番（phase 05 / 暫定 04）。起票元は current.md 別タスク化候補（idea 由来でないため INDEX 移動不要）。
  - **`/refactor_check` 実行**（変更ファイル対象・M1〜M6。挙動不変フェーズだが判定は出す）。
- タスクが緑＋reviewer 採用なら確認なしで `/save_state`→`/task_commit`（standing 許可）。

## 現フェーズの要点（04_config_io_controller_split・task_05 まで完了）
- 目的: `config_io_controller.py`（598 行・1クラス）を `controllers/config_io/` 配下の **6 モジュール**へ分割し、
  ファサードを削除（案B）。**挙動不変が絶対前提**・presentation 限定・スキーマ不変。
- 完了状況: task_01/02=特性テスト（安全網 19+35件）/ task_03=D/E/F 分割 / task_04=A/B/C 分割 / task_05=ファサード削除+呼び出し元差し替え。
  **config_io 名は消滅**し、App が6オブジェクト（keymap_set_io / startup_io / io_dialogs / keymap_io / trigger_set_io / sequence_io）を公開。
- **【最重要】既存バグを「直していない」**: E(trigger_set) の source_path は読み手 `app._trigger_set_source_path`（未定義・常に ""）と
  書き手 `dirty_tracker.trigger_set_source_path`（read されない）で分断し、到達不能な askyesno が残る。**そのまま移設済**（修正は idea_05・phase 04 完了後）。
- 特性テストの設計: 内部メソッド mock は分割で外れる。**task_03=境界 mock / task_04・05=アクセサ切替**で調整（判断は decisions 04・
  タスクごとに最適手段を選択・アサーション非緩和）。テストアクセサは分割オブジェクト（`app.keymap_io` 等）を返す。

## 注意事項・blockers
- **blockers: task_05 完了。次は実機目視のユーザー必須ゲート**（ここで停止）。目視 OK 後に task_06（正本反映）。
- **【Codex 運用の手順書】ジョブが詰まった / cancel が効かない / ハング検知 / state 手修復は
  `instructions/common/rules_detail/codex_operations.md` を読む**（要点は `.claude/rules/agent_selection.md` 冒頭）。
  **Codex 申告のテスト結果は信用せず必ず verifier で `.venv` 再実行**。Codex 投入時はジョブログ停滞の Monitor をセットで
  （task_03〜05 は正常完了・ハングなし・Monitor 有効）。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/` だけでなく **`instructions/` や code も**、
  main リポジトリ側の絶対パス（パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。編集は必ず worktree ルート配下で。
- **【罠】`git grep` は追跡済みファイルのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。
- 行数計測は `wc -l`（PowerShell `Measure-Object -Line` は空行を数えず誤解の元）。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: 03_startup_font_settings_cleanup / 02_hotkey_validation / 01_view_ref_cleanup）。
- 未着手 idea: idea_03（hotkey 保存時正規化・優先度低）/ idea_05（E の不整合・**phase 04 完了後**）。
  保留 idea: idea_04（FontSettingsController）/ idea_06（D/E/F 共通化）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
