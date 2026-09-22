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
2. `instructions/phase/current.md` を読む（**アクティブなフェーズは無い**。次採番 = phase 28 / 暫定 22 / decisions 28）
3. **次フェーズの方針をユーザーへ確認してから** `/phase_start` で起票する。
   候補の確認先は `instructions/backlog/INDEX.md`
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。
   **凍結済の暫定仕様（`instructions/history/` の 04〜21）の条項を実装の根拠に引かない**（正本 `spec_detail/` が正）

## 現在の作業の 1 行サマリ
**phase 27（構成セットの読み込み履歴管理）完了。task_01〜task_06・正本昇格（`data_schema.md` §5.12 新設）・暫定仕様 21 の凍結・実機目視 OK・refactor_check〔不要〕まで完了。次フェーズ未確定。**
直近コミット: `f0275b8`（task_06 = 編集失敗時の再描画）/ `c27b63e`（task_05 = 正本昇格と凍結）/ `8c9e693`（idea_26 起票）。
**main は phase 18 task_05d まで取り込み済み**（phase 18 の残り・19〜27 はユーザーがマージする）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 27 完了時点 = 2026-09-22**）:
compile **clean** / tests **556 実行 OK**（skip 7）/ tests_ui **484 実行 OK** / smoke **pass**。
**件数が減ったら退行を疑う**（tests: phase 26 完了 518 → phase 27 完了 556 / tests_ui: 449 → 484）。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
実行後に **`config/config.json` の mtime が変わっていない**・worktree ルートへ **`user/` / `quarantine/` /
`keymap_set_history*.json` が生成されていない**ことを確認する。

**【重要】`tests_ui` の一括実行は負荷下で不定期に fail することがある**（idea_18 の Escape 配送 / 保存予約の実タイマー競合）。
**赤を見たらまず単独実行で再現するか確かめる**。症状は `get_hook_pause_count()` が `1 != 0`。
**phase 27 完了時にも 3 回中 1 回・毎回別テストで再現**（コード差分ゼロの時点で発生＝フェーズ由来ではない）。

**既知の stderr ノイズ（退行ではない）**: `invalid command name "..._clear_flash_message"`（ステータスバーのタイマー）/
`ResourceWarning: unclosed file`（`tests/test_config_service.py`）。

## 次アクション（session.md.next_action より）
- **次フェーズはユーザーに方針確認してから起票する**（`/phase_start`。次採番 = **phase 28 / 暫定 22 / decisions 28**）。
- **有力候補 = [idea_26](../../instructions/backlog/idea_26_dialog_keyboard_focus.md)**（ダイアログがキーボードフォーカスを
  取らず Escape が効かない。`orphan_sweep` / `quarantine_manage` / `reference_cleanup` の横断修正 +
  テストの検出力強化）。案 A（個別に `focus_set`・1 タスク規模）/ 案 B（`grab_modal` へ集約 +
  正本 `features.md` §4.6 へ追記・小フェーズ規模）の選択が着手時の判断ポイント。
  **phase 27 で実測済みの材料（フォーカスが App ルートのままである実測）がある**うちが着手しやすい。
- その他の候補は `instructions/backlog/INDEX.md` と `current.md`「別タスク化候補」の
  **Phase 27 項**（履歴ファイル名の語幹が 2 箇所に直値）/ **Phase 26 項** / **Phase 25 項**。
- **main へのマージはユーザーが行う**。
- **運用**: `verifier` に変異検査を頼むときは「**`git checkout --` / `git restore` / `git stash` を使わない**（未コミットの実装ごと巻き戻る）。
  ファイルのコピーで退避・復元する」を明示する。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。

## 直前フェーズ（phase 27 = 構成セットの読み込み履歴管理）の要点

**正本が正**: `spec_detail/data_schema.md` **§5.12**（新設・5.12.1〜5.12.8）+ §5.4 /
`features.md` §4.6「メニュー・個別保存」/ `codebase_map.md`。
**暫定仕様 21 は凍結済で条項の根拠に引かない**。判断は `decisions_archive/27_keymap_set_load_history.md`。

- **新規 JSON = `config/keymap_set_history.json`（固定パス）**。config.json にキーを増やさない。**遅延作成**
  （起動時のディレクトリ骨格作成に含めない）。`version` キーを持たず、**未知キーは保持しない**。
- **記録契機 = 読込または保存が成功し、空でないパスが確定したとき、その実保存先**。
  除外 = 初期代入 / 新規作成 / Import / 例の復元 / **起動時の自動読込**
  （起動しただけで履歴ファイルを作らないため。v0.5 で改訂。`tests_ui` が実 `config/` を汚した実測が理由）。
- **`recent` の先頭が同一パスなら書き込まない**（判定は**永続化済みの内容**。メモリ先行更新しない）。上限 20（不在も 1 枠）。
- **破損時は `*.broken*.json` へ退避してから作り直す**（`broken`〜`broken5` の**最大 5 個**。
  すべて埋まっていたら退避も書き込みもしない）。**判定は都度**でセッション内に保持しない。
- **永続化に成功してから UI を確定**し、**読込・編集のたびに永続化済みの内容を読み直して再描画**する
  （失敗時も再描画してから理由を出す）。履歴の失敗で構成セットの読込・保存を巻き戻さない。
- 実装 = `domain/keymap_set_history.py`（純関数・比較キーは `key_of` で受け取る）/
  `application/config_service/keymap_set_history.py`（読み書き・退避・記録）/
  `presentation/controllers/config_io/keymap_set_history_io.py`（**記録の単一の口 `record()`**・
  **境界で例外を `(False, 理由)` へ変換**）/ `dialogs/keymap_set_history_dialog.py`（**リポジトリ唯一の `ttk.Treeview`**）/
  `keymap_set_history_text.py` / `keymap_set_io.load_keymap_set_path`（**パス指定の共通読込入口**）。
- **受容した既知の制約** = 多重起動時の退避先 TOCTOU / 削除時の index 陳腐化（単一インスタンスでは成立しない。
  phase 11 の TOCTOU 受容と同じ扱い）。
- phase 26 以前の要点は `decisions_archive/<phase>.md` を参照する。
  **使い分け = パスは `coerce_label`（trim のみ）/ キー名・id は `coerce_key_name`（trim + 小文字化）**だけは
  触る頻度が高いので覚えておく（パスを小文字化すると壊れる。§5.7 の `normcase` は比較専用）。
  **起動エントリ（`config.json` の `keymap_set_path`）は保存で上書きしない**（phase 26・§5.4）。

## 運用インフラ

- **モード切替は `.claude_data/modes/`**。エージェント構成は 3 モード（`codex`〔現構成〕/ `codex_medium` / `claude_only`）。
  **`.claude/` 配下または `CLAUDE.md` を編集する前に `.claude_data/modes/README.md` を読む**。
- **template からの取り込みは `/template_pull`**（マーカー = `.claude/template_pull_state.md`）。
- **`.gitignore` は追跡ファイルだけを根拠にしない**。確認は `git check-ignore -v`。

## 注意事項・blockers
- **blockers: なし**（Codex 利用可。Codex 不可時の実装代替はユーザー許可が必須）。
- **【罠】Bash ツールで `python3` / `python` を呼ばない**（Windows ストア版スタブが stdin 待ちでハングし、同じコマンド内の後続も実行されない）。
  スクリプトを直接走らせるときは `PYTHONPATH=.` を付ける。
- **【裏取り】レビュー・調査・サブエージェントの「コードがこうなっている」という主張は、採用前に `ファイルパス:行` を実測確認する**。
  **phase 27 では reviewer が見逃した欠陥 2 件（例外ガードの欠落 / 公開単一点 `canonical_path` の再実装）をメインの直読みで検出した**。
  **設計規則の単一点（公開 API）がある箇所は、実装がそれを呼んでいるかを必ず確認する**。
- **【傾向・実証済み】reviewer が「採用」でも敵対的 / 上位レビューで指摘が出る**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**。
  `codex-reviewer`（標準 review）は focus text を受け付けないので、観点を渡すなら `codex-adversarial-reviewer`。
- **【傾向・phase 22 / 27 で実証】正本へ昇格した文章は `deep-reviewer` にかけると矛盾が出る**
  （既存節との衝突・手順の書き落とし・実装より強い断定）。**昇格差分も必ずレビュー対象に含める**。
  **phase 27 では「UI の規範条項がコードにしか無い」昇格漏れを指摘されて追加した**。
- **【罠・phase 27 で実証】テストに `focus_force()` のような「通してしまう前処理」があると、実使用の不具合を隠す**
  （履歴ダイアログの Escape が実機で効かなかったのに全テスト緑だった）。
  **新規ダイアログは「生成直後にフォーカスがダイアログ内にあるか」を `focus_force` 無しで検証する**。
- **【罠・phase 27 で実証】`tests_ui` は実 `config/` を汚し得る**（`App()` を作るだけで起動時処理が走る。
  `.gitignore` の `config/` 除外で `git status` に出ない）。**新規の永続化を足したら、テストの patch と
  実行後のファイル生成有無を必ず実測する**。
- **【傾向】テストの「検出力」は変異検査で確かめる**（その仕様を壊すと**追加テストだけ**落ちるか）。
- **【Codex 運用】フォワーダが切れても Codex ワーカーは生き続ける**（判別は作業ツリーの更新時刻）。
  **書き換え途中で `verifier` / `reviewer` を回さない**。`taskkill /T` を使わない。**Codex 申告のテスト結果は信用せず実測**。
  30 行目安を超えた実装は**同じ Codex へ差し戻して分割**させると早い。
  **Codex が書いた行は LF で入ることがある**（CRLF のファイルへ混在）。受領後に改行コードを揃える。
- **【運用・重要】委任の実行中はメイン側でコードを編集しない**（文書のみ・対象ファイルが重ならない場合は可）。
- **【config.json の書き手は 2 本】** `StartupIo.write_startup`（現在値へマージ・成功時のみ `_startup_settings` 置換・**失敗表示中はフック停止**）と
  keymap_set 保存（`save_runtime_data` が `_startup_settings` をディープコピー）。**直接 `config.json` を read-modify-write しない**。
  **`keymap_set_path` だけは保存で据え置く**（phase 26）。
- **【config_service の配置制約】** ConfigService 本体は `application/config_service/__init__.py`（841 行・新規ロジックを置かない）。
  **presentation から兄弟モジュールを直接 import しない**（公開面は `ConfigService` の公開 API と `contracts.py` のみ・テストが落とす）。
  モジュールを増やしたら `tests/test_config_service_contracts.py` の `INTERNAL_MODULE_NAMES` を更新する（**実ファイル集合と完全一致**）。
- **【最重要・2 度踏んだ罠】パス表記の混在**: runtime の `source_path` 3 種と `hotkey_presets_path` は config 配下なら相対。
  解決なしで `os.path` 系へ渡すと cwd 基準になり **リポジトリルートに `user/` が生成される**。
  解決は `ConfigService.resolve_config_path(path, config_root)`（`config_root` に空文字を渡さない）。
  **比較専用の正規形は `ConfigService.canonical_path`**（自前で `normpath`/`normcase` を組まない）。
- **【罠・重要】保存経路の例外は `messagebox.showerror` になり、テストではモーダルで永久ブロックする**
  （失敗が「ハング」に化ける）。tests_ui の各ファイルの `setUp` に fail-fast ガードがある。
- **【tests_ui の罠】`setUpClass` で App を共有する**: dirty・フック停止カウンタ・ウィンドウ最小サイズ / geometry / 最大化状態 / pane 幅 / font delta / 保存予約
  を他テストから持ち越す。**前後の変化で assert し、`addCleanup` で必ず元へ戻す**。新規テストは `patch.object` を優先。
- **【罠】ダイアログを増やしたら 3 つの列挙を更新する**: `DIALOG_FILES` / `T2_DIALOG_FILES`
  （`tests_ui/test_dialog_teardown_flows.py`）と **`dialog_classes`（`tests_ui/test_nested_modal_grab.py:262`）**。
- **【罠】worktree と main は別コピー**。main 側の絶対パスを編集すると commit から漏れる。
- **【罠】Bash ツールは Git Bash**。長い heredoc は壊れやすい（**壊れたら Write ツールを使う**）。
  **PowerShell の here-string（`@'...'@`）を Bash へ渡さない**（メッセージ先頭 / 末尾に `@` が混入する）。
  **sed の区切りに `#` を使うとパターン中の `##` で壊れる**。複数行のコミットメッセージは `git commit -F <file>`。
  **`git grep` は追跡済みのみ検索**。
- レビュアーは 2 本立て: `reviewer`（sonnet・単一タスクの差分）/ `deep-reviewer`（opus・設計文書/統合/完了判定）。
  併用は `.claude/rules/agent_selection.md` のレビュー表が正。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: 27_keymap_set_load_history / 26_startup_entry_preservation / 25_path_field_type_normalization）。
- 未着手/保留 idea: **idea_26**（ダイアログのフォーカスと Escape・**次フェーズ有力候補**）/ **idea_23**（押す / 離すアクション）/
  **idea_18**（Escape 配送依存テストの不安定）/ idea_13 / idea_11 / idea_03 / idea_09（いずれも低）/ idea_04・idea_06（保留）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
