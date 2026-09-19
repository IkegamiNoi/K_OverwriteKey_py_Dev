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
2. `instructions/phase/current.md` を読む（**アクティブなフェーズは無い**。次採番 = phase 26 / 暫定 21 / decisions 26）
3. **次フェーズの方針をユーザーへ確認してから** `/phase_start` で起票する。
   候補の確認先は `instructions/backlog/INDEX.md`（未着手はいずれも優先度低）
4. CLAUDE.md → `.claude/rules/` の順に必要分を読む。
   **`.claude/` 配下または `CLAUDE.md` を編集するなら、先に `.claude_data/modes/README.md` を読む**
5. 過去の判断は `.claude_data/state/decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。
   **凍結済の暫定仕様（`instructions/history/` の 04〜20）の条項を実装の根拠に引かない**（正本 `spec_detail/` が正）

## 現在の作業の 1 行サマリ
**phase 25（パス系フィールドの型正規化）完了。実装 3 ファイル・正本 §5.5 / §5.7 への追記・記録・refactor_check〔不要〕まで完了。次フェーズ未確定。**
直近コミット: `56ef53b`（task_02 = 正本反映と記録）/ `ad0a7d0`（task_01b）/ `b8636bb`（task_01）。
**main は phase 18 task_05d まで取り込み済み**（phase 18 の残り・19〜25 はユーザーがマージする）。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ずリポジトリルートの .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近の実測（**phase 25 task_01b 時点 = 2026-09-19**。task_02 はコード変更なし）:
compile **clean** / tests **514 実行 OK**（skip 7）/ tests_ui **446 実行 OK** / smoke **pass**。
**件数が減ったら退行を疑う**（tests: phase 24 完了 505 → phase 25 完了 514 / tests_ui: 446 で不変）。
skip 7 件は**シンボリックリンク作成の特権不足**（`WinError 1314`）で環境依存。
実行後に **`config/config.json` の mtime が変わっていない**・worktree ルートへ **`user/` / `quarantine/` が生成されていない**ことを確認する。

**【重要】`tests_ui` の一括実行は負荷下で不定期に fail することがある**（idea_18 の Escape 配送 / 保存予約の実タイマー競合）。
**赤を見たらまず単独実行で再現するか確かめる**。

**既知の stderr ノイズ（退行ではない）**: `invalid command name "..._clear_flash_message"`（ステータスバーのタイマー）/
`ResourceWarning: unclosed file`（`tests/test_config_service.py`）。

## 次アクション（session.md.next_action より）
- **次フェーズはユーザーに方針確認してから起票する**（`/phase_start`。次採番 = **phase 26 / 暫定 21 / decisions 26**）。
  候補は `instructions/backlog/INDEX.md`（**idea_23** = キーの押す / 離すアクション。優先度低）と、
  `current.md`「別タスク化候補」の **Phase 25 項**（`startup_io.py` の `keymap_set_path` /
  **runtime 内部キーの型未追従**〔正本 §5.7 に【実装未追従】として明記済〕）。
- **main へのマージはユーザーが行う**。
- **運用**: `verifier` に変異検査を頼むときは「**`git checkout --` / `git restore` / `git stash` を使わない**（未コミットの実装ごと巻き戻る）。
  ファイルのコピーで退避・復元する」を明示する。
- **前セッションからの未処理 2 件**: ①`codex_medium` を実運用へ入れる前に `Explore` の可用性確認
  ②`.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）。

## 直前フェーズ（phase 25 = パス系フィールドの型正規化）の要点

**正本が正**: `spec_detail/data_schema.md` **§5.5 / §5.7**（phase 24 で新設した §5.1「型不正の共通規則」を参照する形）、
`codebase_map.md`。暫定仕様なし（直接改訂モード）。判断は `decisions_archive/25_path_field_type_normalization.md`。

- **使い分け = パスは `coerce_label`（trim のみ）/ キー名・id は `coerce_key_name`（trim + 小文字化）**。
  **パスに `coerce_key_name` を使うと小文字化で壊れる**（§5.7 の `normcase` は**比較専用**で、記録表記は大小文字を保持）。
- **参照突合経路（`reference_scan.py`）は生 JSON を直接読む別実装**で `ensure_config_compatibility` を通らない。
  同種の修正をするときは**この経路も個別に確認する**（task_01 では取りこぼし、完了後レビューで検出した）。
- **keymap_set の `keymaps[]`（参照エントリ）は旧記法の文字列を受ける**。§5.1 の
  「`keymaps[]` の非 dict 要素は除去」は**単一 JSON / runtime の内容 keymaps**（§5.2）を指す**別物**。
  混同すると旧記法の互換を壊す。
- **例外（`AttributeError`）になる箇所はゼロ**だった（すべて `str()` でラップ済み）。本フェーズは repr 混入の解消。
- **未対応の残件**（`current.md`「別タスク化候補」の Phase 25 項）= ①`startup_io.py` の `keymap_set_path`
  （presentation 層）②**runtime 専用の内部キー**（`_keymap_source_path` 等）が §5.1 に未追従。
  生値のまま素通しし `save_path_resolution.py:127` 経由で**保存先パス候補に repr が混入し得る**
  （正本 §5.7 に**【実装未追従】**として明記済）。
- phase 24（内容フィールドの型正規化）以前の要点は `decisions_archive/<phase>.md` を参照する。

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
  （phase 22 では pyautogui の補間条件・FailSafe の四隅・NaN の素通り・`_normalize_sequence_payload` の未追従をメインが実測して採否を決めた）。
- **【傾向・実証済み】reviewer が「採用」でも敵対的 / 上位レビューで指摘が出る**。
  **フェーズ完了時は Claude 側 × Codex 側の 2 本立てを省略しない**。
  `codex-reviewer`（標準 review）は focus text を受け付けないので、観点を渡すなら `codex-adversarial-reviewer`。
- **【傾向・phase 22 で実証】正本へ昇格した文章は `deep-reviewer` にかけると矛盾が出る**
  （既存節との衝突・手順の書き落とし・実装より強い断定）。**昇格差分も必ずレビュー対象に含める**。
- **【傾向】テストの「検出力」は変異検査で確かめる**（その仕様を壊すと**追加テストだけ**落ちるか）。phase 21・22 とも有効だった。
- **【Codex 運用】フォワーダが切れても Codex ワーカーは生き続ける**（判別は作業ツリーの更新時刻）。
  **書き換え途中で `verifier` / `reviewer` を回さない**。`taskkill /T` を使わない。**Codex 申告のテスト結果は信用せず実測**。
  30 行目安を超えた実装は**同じ Codex へ差し戻して分割**させると早い（phase 22 task_01 で実施）。
- **【運用・重要】委任の実行中はメイン側でコードを編集しない**（文書のみ・対象ファイルが重ならない場合は可）。
- **【config.json の書き手は 2 本】** `StartupIo.write_startup`（現在値へマージ・成功時のみ `_startup_settings` 置換・**失敗表示中はフック停止**）と
  keymap_set 保存（`save_runtime_data` が `_startup_settings` をディープコピー）。**直接 `config.json` を read-modify-write しない**。
- **【config_service の配置制約】** ConfigService 本体は `application/config_service/__init__.py`（827 行・新規ロジックを置かない）。
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
  （直近 3 件: 25_path_field_type_normalization / 24_json_type_normalization / 23_sequence_payload_action_normalization）。
- 未着手/保留 idea: **idea_23**（押す / 離すアクション）/
  **idea_18**（Escape 配送依存テストの不安定）/ idea_13 / idea_11 / idea_03 / idea_09（いずれも低）/ idea_04・idea_06（保留）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
