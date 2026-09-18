# handoff.md

過去の会話履歴は参照しないでください。
このファイルと `.claude_data/state/session.md` を起点に作業を再開してください。

## プロジェクト概要
- 言語/実行: Python（tkinter GUI）。オニオン構成（presentation / application / domain / infrastructure）。
- 対象アプリ: keyseq（キー割り当て/オーバーライドツール）。全体仕様は `instructions/common/`（`app_overview.md` / `codebase_map.md`）参照。
- **python 実行は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  依存 keyboard/pyautogui/pynput はこの `.venv` にのみ導入済み。**素の `python` / `python3` / `py` は使わない**
  （Windows ストア版スタブで**ハングする**。tests_ui/smoke も落ちる）。
- **Codex は python を一切実行できない**（サンドボックス制約・回避不能）。実装委任にテスト実行を含めず、
  実測は `verifier`（またはメイン）が行う（理由は `instructions/common/rules_detail/codex_operations.md` §0）。
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。

## 再開手順
1. `.claude_data/state/session.md` を読む（最重要・最新状態）
2. `instructions/phase/current.md` を読む（**アクティブ = phase 22 `22_mouse_drag_action`**・暫定仕様先行モード）
3. `instructions/history/19_mouse_drag_action.md`（**主入力・v0.5 確定済・未凍結**）と
   `instructions/phase/22_mouse_drag_action/tasks/task_03_integration_and_close.md` を読む（残りは実機目視 → 正本昇格 → 記録）
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。
   **凍結済の暫定仕様（`instructions/history/` の 04〜18）の条項を実装の根拠に引かない**（正本 `spec_detail/` が正）

## 現在の作業の 1 行サマリ
**phase 22 task_03 進行中（統合確認 pass・二次レビュー採否済・採用分を task_03b で反映済）。残り = ユーザーの実機目視 9 項目 → 正本昇格と記録。**
直近コミット: `88ee969`（task_03b）/ `9f22e3c`（task_02）/ `bae9cd8`（task_01）。
**main は phase 18 task_05d まで取り込み済み**（phase 18 の残り・19〜22 はユーザーがマージする）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 22 task_03b 時点 = 2026-09-19**）:
compile **clean** / tests **479 実行 OK**（skip 7）/ tests_ui **446 実行 OK** / smoke **pass**。
**件数が減ったら退行を疑う**（tests: phase 21 完了 461 → phase 22 task_03b 479 / tests_ui: 438 → 446）。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
実行後に **`config/config.json` の mtime が変わっていない**・worktree ルートへ **`user/` / `quarantine/` が生成されていない**ことを確認する。

**【重要】`tests_ui` の一括実行は負荷下で不定期に fail することがある**（idea_18 の Escape 配送 / 保存予約の実タイマー競合）。
**赤を見たらまず単独実行で再現するか確かめる**。

**既知の stderr ノイズ（退行ではない）**: `invalid command name "..._clear_flash_message"`（ステータスバーのタイマー）/
`ResourceWarning: unclosed file`（`tests/test_config_service.py`）。

## 次アクション（session.md.next_action より）
- **ユーザーの実機目視を待つ（9 項目）**: ①範囲選択（**短距離 50px / 長距離 500px の両方**）②ドラッグ&ドロップ
  ③速度を変えると速さが変わる（**100px 超で比較**。短いと下限に張り付く）④既存の単発クリックが従来どおり
  ⑤5 秒クランプのドラッグ後に停止キー・トグルが効く ⑥**離す点が画面の隅**でも完了し押しっぱなしにならない
  ⑦ドラッグ中に**物理マウスを隅へ動かしても中断しない**・終了後に離れている ⑧ドラッグ**以外**の (0,0) クリックは FailSafe のエラーになる
  ⑨ドラッグ ON/OFF で**ダイアログが伸縮**し速度欄と OK が隠れない。
- 目視 OK なら **task_03 の残り**: ①`integration_result.md` を記録
  ②**正本昇格** = `spec_detail/data_schema.md` に **§5.11「アクション要素」を新設**（§5.2 / §5.6 から参照。**§5.6 の下にぶら下げない**）+
  マウスも例外時に必ず離すこと・**ドラッグ中は FailSafe を無効化する**こと（理由と失うもの）・**マウスは send guard 対象外**を明文化 +
  `codebase_map.md` へマウス操作の節を追加 ③**暫定仕様 19 を凍結** ④`decisions_archive/22_mouse_drag_action.md` + `decisions.md` 索引
  ⑤`current.md` 完了記載（次採番 **phase 23 / 暫定 20 / decisions 23**）+ 別タスク化候補へ 1 行
  ⑥`/refactor_check` の判定記載（**不要** = メトリクス収集済・M1〜M6 該当なし）⑦完了判定前レビュー
  （`deep-reviewer` + `codex-adversarial-reviewer`）→ 採否 → コミット。
- **運用**: `verifier` に変異検査を頼むときは「**`git checkout --` / `git restore` / `git stash` を使わない**（未コミットの実装ごと巻き戻る）。
  ファイルのコピーで退避・復元する」を明示する。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。

## 進行中フェーズ（phase 22 = マウスのドラッグ操作）の要点

- **主入力 = 暫定仕様 [19](../../instructions/history/19_mouse_drag_action.md)（v0.5・ユーザー確定済・未凍結）**。正本はフェーズ末に新設する（現時点で `spec_detail/` に `mouse_click` の記述は 0 件）。
- **データ**: `mouse_click` に `drag` / `to_x` / `to_y` / `drag_speed`（px/秒・既定 **1000**）を追加。
  **新種別は作らない**・種別ドロップダウンは 3 種のまま。**drag OFF では新キーを出力しない**（生成停止。ON→OFF 保存で 4 キーは消えるが既存キーは残る）。
- **実行**（`input_gateway.drag_mouse`）: **`FAILSAFE` を退避 → False → 外側 `finally` で復元**、
  `moveTo → mouseDown → moveTo(duration) → mouseUp`（**解放は内側 `finally`**）。**`dragTo` と `ctypes` は使わない**
  （`mouseUp` は解放前に `failSafeCheck` を通すため、FailSafe 有効のままだと**画面の四隅**で解放が遮られる。
  pyautogui は OS 別実装を内部で選ぶので**分岐を増やさない** = 将来の macOS 対応を見据えた判断）。
- **所要時間**（application 側で算出）: 距離 ÷ 速度を **0.15〜5.0 秒へクランプ**
  （`duration > 0.1` のときだけ補間が入る＝下限が無いとワープする / アクションは `app.after(0, ...)` = **UI スレッド**で走るので上限が要る）。
  **5.0 秒は `moveTo` へ渡す引数の上限**で実時間の厳密な上限ではない。`drag_speed` は不正値・**NaN** も既定 1000 へ倒す（`not (speed > 0)`）。
- **UI**: マウス設定内のチェックで離す位置・速度欄が出る / **回数欄は無効化し `clicks` は 1 固定** / X・Y ラベルは「掴む位置」へ /
  **座標取得は掴む用と離す用で排他**。表示切替は `grid()` / `grid_remove()`。
- **テスト**: `tests/test_input_gateway_drag.py`（7）/ `tests/test_action_executor_drag.py`（7）/ `tests_ui/test_action_dialog_drag.py`（8）/
  `tests/test_domain_config.py`（表示 + 永続化）。**変異検査で検出力を確認済み**（FAILSAFE 復元・クランプ下限・生成停止・結線・NaN）。
- **記録のみ / 保留**: `click_mouse` 側の FAILSAFE 検出力 / 速度欄が `int()` 判定（`"1500.5"` は黙って 1000）/
  `instate` ガード / **座標取得リスナーはダイアログ破棄後の `after(0, ...)` で TclError になりうる**（既存挙動・別タスク化候補へ）。

## 運用インフラ

- **モード切替は `.claude_data/modes/`**。エージェント構成は 3 モード（`codex`〔現構成〕/ `codex_medium` / `claude_only`）。
  **`.claude/` 配下または `CLAUDE.md` を編集する前に `.claude_data/modes/README.md` を読む**。
- **template からの取り込みは `/template_pull`**（マーカー = `.claude/template_pull_state.md`）。
- **`.gitignore` は追跡ファイルだけを根拠にしない**。確認は `git check-ignore -v`。

## 注意事項・blockers
- **blockers: なし**（Codex 利用可。Codex 不可時の実装代替はユーザー許可が必須）。
- **【罠】Bash ツールで `python3` / `python` を呼ばない**（Windows ストア版スタブが stdin 待ちでハングし、同じコマンド内の後続も実行されない）。
  スクリプトを直接走らせるときは `PYTHONPATH=.` を付ける。
- **【裏取り】レビュー・調査・サブエージェントの「コードがこうなっている」という主張は、採用前に `ファイルパス:行` を実測確認する**
  （phase 22 では pyautogui の補間条件・FailSafe の四隅・NaN の素通りをメインが実測して採否を決めた）。
- **【傾向・実証済み】reviewer が「採用」でも敵対的 / 上位レビューで指摘が出る**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**。
  `codex-reviewer`（標準 review）は focus text を受け付けないので、観点を渡すなら `codex-adversarial-reviewer`。
- **【傾向】テストの「検出力」は変異検査で確かめる**（その仕様を壊すと**追加テストだけ**落ちるか）。phase 21・22 とも有効だった。
- **【Codex 運用】フォワーダが切れても Codex ワーカーは生き続ける**（判別は作業ツリーの更新時刻）。
  **書き換え途中で `verifier` / `reviewer` を回さない**。`taskkill /T` を使わない。**Codex 申告のテスト結果は信用せず実測**。
  30 行目安を超えた実装は**同じ Codex へ差し戻して分割**させると早い（phase 22 task_01 で実施）。
- **【運用・重要】委任の実行中はメイン側でコードを編集しない**（文書のみ・対象ファイルが重ならない場合は可）。
- **【config.json の書き手は 2 本】** `StartupIo.write_startup`（現在値へマージ・成功時のみ `_startup_settings` 置換・**失敗表示中はフック停止**）と
  keymap_set 保存（`save_runtime_data` が `_startup_settings` をディープコピー）。**直接 `config.json` を read-modify-write しない**。
- **【config_service の配置制約】** ConfigService 本体は `application/config_service/__init__.py`（828 行・新規ロジックを置かない）。
  **presentation から兄弟モジュールを直接 import しない**（公開面は `ConfigService` の公開 API と `contracts.py` のみ・テストが落とす）。
- **【最重要・2 度踏んだ罠】パス表記の混在**: runtime の `source_path` 3 種と `hotkey_presets_path` は config 配下なら相対。
  解決なしで `os.path` 系へ渡すと cwd 基準になり **リポジトリルートに `user/` が生成される**。
  解決は `ConfigService.resolve_config_path(path, config_root)`（`config_root` に空文字を渡さない）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**
  （失敗が「ハング」に化ける）。tests_ui の各ファイルの `setUp` に fail-fast ガードがある。
- **【tests_ui の罠】`setUpClass` で App を共有する**: dirty・フック停止カウンタ・ウィンドウ最小サイズ / geometry / 最大化状態 / pane 幅 / font delta / 保存予約
  を他テストから持ち越す。**前後の変化で assert し、`addCleanup` で必ず元へ戻す**。新規テストは `patch.object` を優先。
- **【罠】App に View の部品を属性で生やさない**（phase 01 で解消済）。
- **【罠】worktree と main は別コピー**。main 側の絶対パスを編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。長い heredoc は壊れやすい（**壊れたら Write ツールを使う**）。
  **sed の区切りに `#` を使うとパターン中の `##` で壊れる**。複数行のコミットメッセージは `git commit -F -` + 短い heredoc。
  **`git grep` は追跡済みのみ検索**。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: 21_extended_key_send / 20_full_view_min_height / 19_full_view_header_width）。
- 未着手/保留 idea: **idea_23**（押す / 離すアクション）/ **idea_18**（Escape 配送依存テストの不安定）/ idea_13 / idea_11 / idea_03 / idea_09（いずれも低）/ idea_04・idea_06（保留）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
