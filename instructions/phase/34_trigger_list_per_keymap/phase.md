# phase.md

## フェーズ名

トリガー一覧のキーマップ従属化（trigger_list_per_keymap）

## フェーズの目的

1 つの構成セットで複数のトリガー一覧を使い分けられるようにする。
**トリガー一覧（と従属するシーケンス）をキーマップに従属させ、「キーマップ＝モード」として置換キーとトリガーを一括で切り替える**。

**JSON スキーマ変更あり**（keymap ファイルに `trigger_set_path` / 単一 JSON の `keymaps[].triggers` を追加・
keymap_set の `trigger_set_path` とトップレベル `triggers` は旧形式の読込元へ）。**全レイヤに跨る**
（domain の正規化 / application の読込・保存・参照辿り・入力判定 / presentation の UI・保存ダイアログ）。

- 起票元: ユーザー要望（2026-09-24・「1 つの構成セットからトリガー一覧を複数使いたい」）。
- 主入力（暫定仕様）: [25_trigger_list_per_keymap.md](../../history/25_trigger_list_per_keymap.md)（v0.4・ユーザー確定済）。
- モード: **暫定仕様先行モード**。番号対応: phase 34 / 暫定 25 / decisions 34。

## 確定（ユーザー 2026-09-24）

暫定仕様 25 §2（確定事項 1〜20）が正。要点:

- トリガー一覧は keymap ファイルが参照する。旧形式はアクティブなキーマップにのみ移行（移行先は未保存・一括保存で「保存しない」不可）。
- キーマップは常に 1 つ以上 / 2 つ目以降の追加は切替キー必須 / 一覧の選択 = アクティブ化（未保存にしない）/ 連続実行中は切替不可。
- 入力判定は 停止 > トグル > 直接切替 > 置換 > トリガー。重なりはグレー表示・キーボード表示・ステータス案内で知らせ、
  フック開始を止めるのは「停止 = トグル」だけ。
- 「通常トリガー無効化」→「キーマップ一時停止」⇔「キーマップ再開」（表示のみ）。
- Import / Export も対象。共通トリガー層は作らない（[idea_36](../../backlog/idea_36_common_trigger_layer.md)）。

## スコープ

### 含む

暫定仕様 25 の §3〜§8（データモデル / 読込と移行 / 保存 / 周辺機能 / 入力判定 / UI）と §10 の受け入れ条件。

### 含まない（後送り）

暫定仕様 25 §11（共通トリガー層 / タブ方式 / 前方互換 / 一時停止まわりの内部名の改名 /
連続実行中の構成セット単位の操作制限 / 判定と実行のタイミング差）。

## このフェーズで読むファイル

1. [暫定仕様 25](../../history/25_trigger_list_per_keymap.md)（主入力。§1 の現状監査に `ファイル:行` の入口あり）
2. `instructions/common/codebase_map.md` の「KeymapSetIo」「KeymapPanelController」「JSON 読込時の型正規化」節と config_service の表
3. `instructions/common/spec_detail/data_schema.md` §5.1〜§5.6 と `data_schema/5_08_0{1..9}_*.md`（タスクに関係する子のみ）
4. `instructions/common/spec_detail/key_input.md` §7 / `features.md`（キーマップ管理・トリガー一覧・ボタン文言〔104 行付近〕）
5. 実装の入口（タスクごとに該当分のみ）: `keyseq/domain/config.py` /
   `keyseq/application/{input_router,trigger_service,keymap_service,hook_coordinator,action_executor,sequence_runner}.py` /
   `keyseq/application/config_service/` 配下 / `keyseq/presentation/controllers/` 配下（keymap_panel / trigger_panel / hook / config_io）/
   `keyseq/presentation/keyboard_window.py` / `keyseq/presentation/hook_button_texts.py`

## タスク

依存順。各タスクの定義は着手時に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

- task_01: アクティブのトリガー一覧を取る口（domain）を作り、runtime の `triggers` 直参照を付け替える（**挙動不変**・暫定 §3.3 の前段）— **完了**（2026-09-24）
  （reviewer 参考指摘 = `save_plan_execution.py:53-57` の形骸化した `isinstance` → task_01b で同箇所を触るときに簡素化）
- task_01b: runtime データモデルと読込・移行（暫定 §3 / §4.1・§4.3・§4.5・`DEFAULT_CONFIG` 新形式・`ensure_active_keymap` 統一・
  共有実体。口の中身をアクティブキーマップの保持へ差し替える。保存は task_02 まで「アクティブ分を従来の 1 trigger_set として書く」暫定）
  + 単一 JSON の Import / Export（往復を壊さないため task_03 から移動）— **完了**（2026-09-24）
- task_02: 一括保存のキーマップ単位化（暫定 §4.2・§4.4・§5.1・§5.3 の 1 点目・§5.4 の親変更・§5.5 の trigger_set 既定名:
  trigger_set の実体ごとの行 / sequence の合成識別子 / 計画全体の衝突回避 / keymap の `trigger_set_path` / 依存 3 段 / 移行先の未保存化と「保存しない」不可 /
  実体ごとの未保存管理。task_01b の暫定を撤去）— **完了**（2026-09-25）
  （reviewer 参考: `keymap_set_io.py` の移行判定つき set_dirty(False) の重複 / `default_trigger_set_path` の引数名 `keymap_set_path` が実態〔親 keymap のパス〕と乖離 → 後者は task_02b で同ファイルを触るときに改名）
- task_02b: 保存の安全網と命名（暫定 §5.2 / §5.3 の 2・3 点目 / §5.4 の移行時の扱いと後処理 / §5.5 の keymap 既定名と除外撤廃）— **完了**（2026-09-25）
  （付随: keymap ファイルへ `id` を書く〔§5.6 に沿う・既定名が id 由来でなくなったため〕。reviewer 参考: `resolve_trigger_set_save_path` の引数名も同様の乖離・範囲外）
- task_03: 個別保存・個別読込（暫定 §5.6。Export は task_01b へ移動）— **完了**（2026-09-25）
  （reviewer: `_path_changed` 重複定義 → メインで削除。参考 = `config_service/__init__.py` の肥大〔個別キーマップ保存計画一式 +290 行〕→ task_08 の `/refactor_check` で判定 / 個別キーマップ保存経路だけ `ensure_config_compatibility` を通らない非対称 → task_08 の統合レビューで確認）
- task_04: 参照辿り 3 段・孤児棚卸し・keymap_set の判別（暫定 §3.1 末尾 / §6）— **完了**（2026-09-25）
  （付随: `active_keymap_path` も keymap 内容を読む参照に含めた〔安全側・生成データでは `keymaps[]` と重複〕。参考: `parent_refs_cleanup.py` 318 行 → task_08 の `/refactor_check`）
- task_05: 入力判定と重複（暫定 §7: 優先順位の入れ替え / 編集時の拒否 / トリガー・キーマップのグレー表示 / キーボード表示 /
  開始検証の縮小）+ 重複キーの案内（§8.5）
- task_06: キーマップ管理 UI（暫定 §8.1〜§8.3: 選択 = アクティブ化・選択ボタン削除 / 追加・編集・削除の規則 / 連続実行中の切替禁止 / 再描画 /
  シーケンスの実行位置・選択行をトリガー一覧の実体ごとに保持〔§3.3 末尾〕）
- task_07: 一時停止の改名（暫定 §8.4）
- task_08: 統合確認と正本反映（暫定 25 の `spec_detail/` への昇格・凍結 / `codebase_map.md` / decisions_archive/34 /
  current.md の完了記載 / `/refactor_check`）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。各タスクは `reviewer`、統合（task_08 前）は `deep-reviewer` + `codex-reviewer`、
  フェーズ完了判定前は `deep-reviewer` + `codex-adversarial-reviewer`（`.claude/rules/agent_selection.md`）。
- **本フェーズ固有**:
  - **データが黙って消える / 二重になる / 別のキーマップへ付く経路が無いか**（暫定 §4・§5。
    「旧形式を読込 → 無編集で保存 → 再読込」「アクティブを変えてから保存」「共有 trigger_set」の往復テストがあるか）。
  - **後方互換**: 旧形式の構成セット・単一 JSON・例の復元が読めるか（§5.1 の JSON ルール。既存キーを削除していないか）。
  - **判定の一元化**: アクティブのトリガー一覧を service 経由で取り、`app.data["triggers"]` の直参照が残っていないか。
  - **重複の扱いの一貫性**: 入力判定の順（§7.1）・グレー表示（§7.3）・案内（§8.5）・開始検証（§7.4）が同じ優先順で揃っているか。
