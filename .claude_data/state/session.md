# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-28T06:10:00
phase: `instructions/phase/06_child_file_save_dialog`（保存系リデザイン **Phase β**）
last_commit_location: claude/phase-beta-bfbdd2 ※現在地はセッション開始時の git 実測値が正

## current
focus: **Phase β（06_child_file_save_dialog）起票完了（phase.md + current.md + INDEX.md）。次は task_01（参照元キーの読み書き基盤）の `/task_new` 起票 → 実装委任**。
mode: implementing

## last_action
ts: 2026-07-28T06:10:00
who: main
summary: |
  【`/phase_start` = Phase β 起票】文書のみ・コード差分ゼロ。ユーザー指示「Phase βへ進んで」で着手確定。
  - `instructions/phase/06_child_file_save_dialog/phase.md` を新規起票（暫定仕様先行モード・
    主入力＝暫定仕様 05 v0.2〔ユーザー確定済〕）。スコープ含む 7 項目 / 含まない 7 項目 /
    読むファイル 10 件 / **タスク task_01〜07**（01 参照元スキーマ → 02 trigger_set source_path 接続＋既定命名 →
    03 保存計画の実行契約 → 04 dirty 収集＋共有状況判定 → 05 ダイアログ → 06 統合退行 → 07 正本反映）/
    フェーズ固有レビュー方針（依存方向・後方互換・粒度と依存関係・過剰実装・既定の安全側）。
  - **task_03 はダイアログ導入前に既存挙動と等価**であることを確認してから task_05 へ進む設計（挙動変更の切り分け）。
  - `current.md`: 「現在の参照先」先頭へ Phase β を追加 / 次採番を **07** へ / 候補節の idea_05 行を打消し。
  - `backlog/INDEX.md`: idea_05 を「**着手**（→ phase 06 / 暫定 05 §7 が内包）」へ更新。
  - **整合チェック（reviewer・整合確認限定）= 完了可**。指摘は軽微 1 件（「含まない」の idea_09 が暫定仕様 05 §11 に
    無い追加情報）→ 出典注記を追記して解消。
result_files:
  - instructions/phase/06_child_file_save_dialog/phase.md（新規）
  - instructions/phase/current.md
  - instructions/backlog/INDEX.md
verified:
  コード差分: なし（`keyseq/` `tests/` `tests_ui/` すべて無変更）
  review: reviewer（整合確認限定）= 完了可（軽微指摘 1 件は対応済）
  compile/pytest: not_run（文書のみのため）

## next_action
- **task_01（`parent_refs_schema`）を `/task_new` で起票する**（`instructions/phase/06_child_file_save_dialog/tasks/task_01_parent_refs_schema.md`）。
  内容: 子JSON への参照元キー（例 `_parent_refs`）を application 層（`keyseq/application/config_service.py`）で
  読み書き。keymap / trigger_set → keymap_set、sequence → trigger_set。パスは `to_config_relative_or_absolute`。
  **キー無し＝「未知」として区別できる形**にする（§5 の別名保存既定の入力）。追加のみ・既存キー削除禁止。
- 起票後、`codex-implementer` へ実装委任（テストコード追加まで含め、**テスト実行は依頼しない**）→
  `verifier` で `.venv` 実測 → `reviewer` で差分レビュー → `/save_state` + `/task_commit`。

## blockers
- なし。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **Phase β の設計の正は暫定仕様 [05](../../instructions/history/05_child_file_save_dialog.md)（v0.2・ユーザー確定済）**。
  フェーズ中は正本 `spec_detail/` を直接改訂せず、task_07 で昇格＋凍結する。
- **Phase β の勘所**（暫定仕様の指摘①〜④由来。実装時に後退しやすい）:
  ① 未知の参照元・別の上位に属す子は**別名保存が既定**（安全側）/ ② 保存計画は
  **presentation が決定・application が実行**（application に tkinter 依存を持ち込まない）/
  ③ パスが変わる子の上位は**保存必須**・失敗時は**旧索引維持**・**行ごとの粒度**（他 sequence を巻き込まない）/
  ④ 既定命名の変更は **trigger_set のみ**（keymap_set stem 基準。現状は固定 `user/trigger_sets/default.json`）。
- Phase β の主な触点: `config_service.save_runtime_data`(200-252) / `_build_split_save_payloads`(456-) /
  `config_io/keymap_set_io.py`(`save_keymap_set_to`:78-102) / `controllers/dirty_state.py`（idea_05 の当事者）/
  `config_io/io_dialogs.py`（`choose_save_path_with_collision`）。
- **保存系リデザインの番号対応**: α=phase05/暫定04〔完了〕 / **β=phase06/暫定05〔進行中〕** /
  γ=phase07/暫定06〔独立・未着手〕 / プリセット=phase08/暫定07〔β とカスケード除外で協調〕。
- **Phase α の成果は正本 `spec_detail/data_schema.md` §5.4 配下が正**（新規/Import/空起動で keymap_set パスが空 →
  保存は別名保存 / 既定はディレクトリ `config/user/keymap_sets/` / 子ファイルは全セット共有〔β の課題〕/
  レガシー `settings/` 経路のみ実装未追従 = idea_09）。
- config_io は `controllers/config_io/` の 6 クラスへ分割済（App が `app.keymap_set_io` 等で直接公開）。
- **レビュアーは 2 本立て**: `reviewer`（sonnet・単一タスクの実装差分）/ `deep-reviewer`（opus・設計文書 /
  複数タスクを跨ぐ差分 / フェーズ完了判定）。使い分けは `.claude/rules/agent_selection.md` のレビュー表が正。
  出力の作法は `.claude/rules/output_style.md`。
- **【Codex 運用の手順書】ジョブが詰まった / cancel が効かない / ハング検知 / state 手修復は
  `instructions/common/rules_detail/codex_operations.md` を読む**。**Codex 申告のテスト結果は信用せず必ず verifier で再実行**。
  **Codex は python をまったく実行できない**（サンドボックス制約・回避不能）→ 委任にテスト実行を含めない。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**（main 側を編集すると commit から漏れる）。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規（未追跡）ファイルの確認には**直接 `grep`** を使う。
  行数計測は `wc -l`（PowerShell `Measure-Object -Line` は空行を数えない）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 03_startup_font_settings_cleanup / 04_config_io_controller_split / 05_keymap_set_new_and_default_dir。
- 未着手 idea: idea_03（hotkey 保存時正規化・優先度低）/ idea_07（参照元の掃除・**β 完了後**）/
  idea_08（keymap_set 個別プリセット・プリセット案2 完了後）/ idea_09（レガシー settings/ フォールバック・α の積み残し）。
  保留 idea: idea_04（FontSettingsController）/ idea_06（D/E/F 共通化・**β で達成見込み**）。idea_05 は β が内包（着手中）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
