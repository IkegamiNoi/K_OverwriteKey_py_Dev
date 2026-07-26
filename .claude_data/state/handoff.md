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
2. `.claude_data/state/decisions.md` を読む（判断履歴。完了フェーズは「アーカイブ索引」→ `decisions_archive/<phase>.md`）
3. CLAUDE.md → `instructions/phase/current.md`（**現在: phase 04 完了・phase 05 未起票**）→ `.claude/rules/` の順に必要分を読む
4. **設計の正は暫定仕様 04〜07（保存系リデザイン・すべてユーザー確定済）**。着手対象は
   [04_keymap_set_new_and_default_dir.md](../../instructions/history/04_keymap_set_new_and_default_dir.md)（Phase α・v0.3）。
   番号対応: **α=phase05/暫定04 / β=phase06/暫定05 / γ=phase07/暫定06 / プリセット=phase08/暫定07**。
5. session.md.next_action から作業を再開する

## 現在の作業の 1 行サマリ
**保存系リデザインの暫定仕様 4 本（04=α/05=β/06=γ/07=プリセット）を敵対的レビュー反映・ユーザー確定まで完了（コミット dfa8f95）。次は Phase α（暫定04）を `/phase_start` で phase 05 として起票し実装着手**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ず .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
直近のベースライン（phase 04 完了時）: compile clean / tests 86 / tests_ui 74 / smoke pass。
※ Phase α は**挙動変更フェーズ**なので、着手後は新挙動の特性テスト追加で件数が増える（暫定 04 §8）。

## 次アクション（session.md.next_action より）
- **保存系リデザインの暫定仕様 4 本は確定・コミット済（dfa8f95）**。次は **Phase α（暫定 04）を `/phase_start` で
  phase 05 として起票し、実装に着手**する（順序: α→β→γ→プリセット。α は独立・小さいので先行）。
  - Phase α タスク見込み: `new_config` 空パス化 / `save_keymap_set` 空パス→別名分岐 / `import_config` 無条件クリア /
    起動時ディレクトリ骨格作成 / 別名保存 initialfile=`keymap_set.json` / `prompt_if_missing` 撤去（新規出力停止・残置許容）。
  - **α は挙動変更フェーズ**（挙動不変ではない）。特性テストで新挙動を固定する（暫定 04 §8）。
- 実装は `.claude/rules/agent_selection.md` の既定（codex-implementer）へ委任。各タスクで reviewer 必須。統合・確定前は Codex レビュー併用。
- β/γ/プリセットは α 完了後に順次 `/phase_start`（暫定 05/06/07 が設計の正）。
- idea 位置づけ更新（β 起票時）: idea_05→β 内包・idea_06→β 達成見込みを INDEX へ反映。

## 直前フェーズの要点（保存系リデザインの設計・暫定 04〜07 確定）
- ユーザー要望（保存系統の改善・点1〜5）を 4 フェーズへ分割し、暫定仕様先行モードで設計を確定した（**未実装**）。
  - **04 α**: 新規=ファイルなし（`keymap_set_path=""`）/ 保存の空パス→別名保存分岐 / 既定保存先を固定 default.json から
    ディレクトリ `config/user/keymap_sets/` へ / 起動時ディレクトリ骨格作成 / `prompt_if_missing` 撤去（新規出力停止・
    既存残置許容）。**複数独立 keymap_set の完全対応は β 以降**（同一 dir では子ファイルを共有・上書きする制約が残る）。
  - **05 β**: keymap_set 保存時に変更のある子（keymap/trigger_set/sequence）ごとに 保存/別名/しない を選ぶ確認ダイアログ。
    子JSON に参照元（上位ファイル）を記録し誤爆上書きを防ぐ（**未知の参照元は安全側で別名保存を既定**）。保存は依存関係つき
    「保存計画」を application が実行（失敗時は旧索引維持）。既定命名変更は **trigger_set のみ**（keymap_set 名基準）。
    **idea_05（trigger_set source_path 分断）を内包**、idea_06（子保存共通化）を達成見込み。
  - **06 γ**: 停止/トグルキー（`hook_stop_key`/`hook_toggle_key`）の全体デフォルトを `config/config.json` に新設（空スタート）。
    keymap_set に `hook_keys_individual` フラグ追加。OFF=全体デフォルト使用、OFF編集は config.json を直接更新（keymap_set 非dirty）、
    OFF保存で個別値を空文字クリア（キーは残す＝既存キー削除禁止順守）。移行=正規化後どちらか非空なら個別ON。
  - **07 プリセット**: hotkey プリセットを keymap_set 参照から `config/config.json` のグローバル参照（固定 default.json）へ一本化。
    keymap_set payload から生成停止（既存キーは無視）。プリセットマネージャがグローバルへ即時保存、カスケードはプリセットを書かない。
- 各仕様に codex-adversarial-reviewer を実施（04=4件/05=critical1+high3/06=6件/07=4件）→ 全指摘を精査・ユーザー確定のうえ反映。

## 注意事項・blockers
- **blockers: なし**。次は Phase α の `/phase_start`（ユーザー着手指示待ち）。
- **保存系の実コード把握（設計時に確認済）**: keymap_set 保存 = `KeymapSetIo.save_keymap_set_to`→`config_service.save_runtime_data`
  （全子を無条件上書き・config_root 内は trigger_set/presets を固定 default.json へ）。config.json=起動エントリ
  （`preferred_startup_path`=`_startup_entry_path`）。hook キーは keymap_set に保存・`InputRouter` が `app.data` 直読み。
  プリセットは keymap_set の `hotkey_presets_path`→固定 default.json。dirty は子単位（`INTERNAL_*_DIRTY`/`trigger_set_dirty`）。
- **【Codex 運用】ジョブが詰まった/ハング検知/state 手修復は `instructions/common/rules_detail/codex_operations.md`**
  （要点は `.claude/rules/agent_selection.md` 冒頭）。**Codex 申告のテスト結果は信用せず必ず verifier で `.venv` 再実行**。
  Codex 投入時はジョブログ停滞の Monitor をセットで。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/`・`instructions/`・code とも、main 側の絶対パス
  （パスに `.claude\worktrees\<name>\` を含まない）を編集すると commit から漏れる。編集は必ず worktree ルート配下で。
- **【罠】`git grep` は追跡済みのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。行数計測は `wc -l`。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近: 04_config_io_controller_split / 03_startup_font_settings_cleanup / 02_hotkey_validation）。
- 未着手/保留 idea: idea_03（hotkey 保存正規化・低）/ idea_04（FontSettingsController・保留）/ idea_07（参照元掃除・β後）/
  idea_08（個別プリセット・07後）。idea_05→β 内包 / idea_06→β 達成見込み。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
