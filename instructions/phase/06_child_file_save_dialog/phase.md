# phase.md

## フェーズ名

子ファイル保存の確認ダイアログと参照元記録（child_file_save_dialog）＝ 保存系リデザイン **Phase β**

## フェーズの目的

keymap_set の「保存」が子ファイル（keymap / trigger_set / sequence）を**まとめて無条件上書き**する現挙動を、
**変更のある子ごとに 保存 / 別名保存 / 保存しない を選べる確認ダイアログ**へ置き換える。あわせて子JSONへ
**参照元（直接の上位ファイル）を記録**し、他の keymap_set に属する子の誤爆上書きを防ぐ。

- **対象レイヤ: presentation（ダイアログ・保存計画の収集・共有状況判定）+ application（保存計画の実行・
  事前検証・参照元永続化・trigger_set 既定命名）**。
- **スキーマ変更: あり（子JSON へ参照元の内部キーを追加。追加のみ・既存キー削除なし・後方互換必須）**。
- **挙動変更を伴うフェーズ**（保存時にダイアログが挟まる / 既定が別名保存になる場合がある）。

- 起票元: ユーザー要望（2026-07-26〜27・保存系統の改善討議・点3/4）。Phase α（phase 05 / 暫定 04）の後続。
- 主入力（暫定仕様）: [05_child_file_save_dialog.md](../../history/05_child_file_save_dialog.md)
  （**v0.5**・ユーザー確定済 2026-08-01。v0.2〜v0.5 は実機目視フィードバックの反映で改訂・
  改訂内容は暫定仕様 §2 末尾の各「vX.Y の変更」節が正）
- モード: **暫定仕様先行モード**。番号対応: phase 06 / 暫定 05 / decisions_archive 06。
- 依存: **Phase α（phase 05）完了が前提**（済）。[idea_05](../../backlog/idea_05_trigger_set_source_path_inconsistency.md) を**内包**し、
  [idea_06](../../backlog/idea_06_individual_json_io_unification.md) の共通化を達成する見込み。

## 確定（ユーザー 2026-07-26〜27）

暫定仕様 05 §2 が正。要点のみ再掲する（詳細・根拠は暫定仕様を読む）。

- 粒度は**ファイル単位**。**親 keymap_set.json は常に保存**（ラジオ対象外・索引として最後に書く）。
  変更のある子が無ければダイアログを出さない。
- **参照元記録は案A（軽量）**: keymap / trigger_set は keymap_set を、sequence は trigger_set を記録。
  パスは config_root 内=相対 / 外=絶対。
- **未知の参照元（既存子JSONに参照元キー無し）は安全側で「別名保存」を既定**にする（指摘①）。
- **保存は「保存計画」として原子的に扱う**（指摘②③）: presentation が行ごとの指示を集め、application が
  事前検証 → 実行。**パスが変わる子の上位は保存必須**（スキップ禁止）。失敗時は**旧索引を維持**。
  個別 save API を再利用する場合も**行ごとの粒度**を守る（他 sequence を巻き込まない）。
- **既定命名の変更は trigger_set のみ**（keymap_set stem 基準）。keymaps / sequences は現行命名のまま（指摘④）。
- 共有状況の可視化とデフォルト選択規則は暫定仕様 §5 の 4 状態表が正。

## スコープ

### 含む

1. 子JSON への**参照元記録**（読み書き・後方互換・保存時の best-effort 更新）— 暫定仕様 §4
2. **trigger_set の source_path 接続**（idea_05 内包・案1 = `dirty_tracker.trigger_set_source_path` 軸）— §7
3. **trigger_set 既定命名の keymap_set stem 基準化**（固定 `trigger_sets/default.json` を廃する）— §6
4. **保存計画**の導入（データ構造・事前検証・依存関係の強制・粒度厳守・失敗時の旧索引維持）— §8
5. **dirty な子の収集と共有状況判定**（§5 の 4 状態 → 行ごとの既定ラジオ決定）— §3・§5
6. **子ファイル保存確認ダイアログ**（一覧・種別/対象名/保存先パス/共有状況/ラジオ）と keymap_set 保存経路への挟み込み — §3
7. **パス同一性の canonical identity 化**（内外判定・既定領域判定・所有判定・重複排除・衝突検出）— §6 v0.3-B
8. **再解決時の一覧再表示の廃止**と、再計算先が既存ファイルのときの行単位の上書き確認 — §3-3 v0.3-A / A2
9. **一覧ダイアログのレイアウト**（固定初期サイズ・リサイズ・縦スクロール・省略表示＋ツールチップ）— §3-5 v0.3-C
10. 受入条件 §10（1〜14）の回帰・特性テスト、正本昇格と記録整理

### 含まない（後送り）

- 既存の個別保存ボタン（各 box）の統合 — 暫定仕様 §11
- 参照元の掃除機能 → [idea_07](../../backlog/idea_07_reference_link_cleanup.md)（β 完了後）
- hotkey_presets（触らない）/ プリセットの config.json グローバル化 → 暫定 07（phase 08）
- 停止・トグルキーの config.json 既定化 → Phase γ（phase 07 / 暫定 06）
- 複数 trigger_set 対応・keymaps / sequences の keymap_set 名前空間化（将来課題・§6）
- 孤児ファイル検出
- [idea_09](../../backlog/idea_09_legacy_settings_save_path_fallback.md)（レガシー `settings/` 経路の実装追従・α の積み残し）
  ※ 暫定仕様 05 §11 には無い項目。`current.md` / `backlog/INDEX.md` 由来の注記として、β と混同しないよう明示する。

## このフェーズで読むファイル

1. `instructions/history/05_child_file_save_dialog.md` — **主入力**（確定設計。フェーズ中はこれが正）
2. `instructions/common/spec_detail/data_schema.md` — 正本（§5.4 配下 = Phase α の保存先規定 / §5.6 / JSON 後方互換）
3. `instructions/common/codebase_map.md` — クラス構成・責務（変更時は追従が必要）
4. `keyseq/application/config_service.py` — `save_runtime_data`(200-252) / `_build_split_save_payloads`(456-) /
   `_build_trigger_set_payloads` / `_load_trigger_set` / `INTERNAL_*` 定数
5. `keyseq/presentation/controllers/config_io/keymap_set_io.py` — 保存経路の入口（`save_keymap_set_to`:78-102）
6. `keyseq/presentation/controllers/config_io/{keymap_file_io,trigger_set_file_io,sequence_file_io,io_dialogs}.py` —
   個別 save/save_as と衝突ダイアログ（`choose_save_path_with_collision`）
7. `keyseq/presentation/controllers/dirty_state.py` — dirty 管理・`trigger_set_source_path`（idea_05 の当事者）
8. `keyseq/presentation/config_paths.py` — `to_config_relative_or_absolute` / `is_within_config_root`
9. `tests/test_config_service.py` / `tests/test_dirty_state.py` /
   `tests_ui/test_config_io_characterization*.py` — 既存の特性テスト（期待値更新の対象）
10. `instructions/backlog/idea_05_*.md` / `idea_06_*.md` — 内包・達成見込みの前提

上記以外へ広げる必要が出たら、その都度タスク定義に追記する（先読みしない）。

## タスク

| # | タスク | 概要 |
|---|---|---|
| task_01 | `parent_refs_schema` | 子JSON の参照元キーを application 層で読み書き（追加のみ・後方互換・未知は未知として区別）。テスト追加 |
| task_02 | `trigger_set_source_and_naming` | trigger_set の source_path 接続（idea_05）＋ 既定命名を keymap_set stem 基準へ（§6・§7） |
| task_03 | `save_plan_execution` | 保存計画の型と application 側実行（事前検証・依存関係の強制・粒度厳守・失敗時の旧索引維持）。既定計画＝全保存で既存挙動と等価 |
| task_04 | `dirty_children_and_share_state` | dirty な子の収集と共有状況判定（§5 の 4 状態）→ 行モデル + 既定ラジオの決定 |
| task_05 | `save_dialog_ui` | 子ファイル保存確認ダイアログの実装と keymap_set 保存経路への挟み込み（変更なしなら出さない） |
| task_06 | `integration_regression` | 受入条件 §10 の 1〜11 を通す統合退行・特性テスト更新・実機目視 |
| task_06b | `review_fixes` | task_06 の 2 本立てレビュー指摘 A〜F の修正（trigger_set source_path の二重管理解消＝条件9 未達 / 確定エントリの計画反映 / 依存確認の無限ループ / 条件9 とダイアログ本体のテスト補強 / 参照元のマージ） |
| task_07 | `canonical_path_identity` | パス同一性を canonical identity（解決 → `normpath` → `normcase`）へ統一し 7 箇所へ適用（v0.3-B）。実機目視③④の解消 |
| task_08 | `save_dialog_no_recheck` | 一覧再表示の廃止と、再計算先が既存ファイルのときの行単位の上書き確認（v0.3-A / A2）。実機目視①の解消 |
| task_09 | `save_dialog_layout` | 一覧ダイアログのレイアウト（固定初期サイズ・リサイズ・縦スクロール・省略表示＋ツールチップ）（v0.3-C）。実機目視⑤の解消 |
| task_10 | `finalize_records` | **正本反映**（`data_schema.md` / `codebase_map.md` 昇格）+ 暫定仕様 05 凍結 + `decisions_archive/06` +
`current.md` 完了記載 + `backlog/INDEX.md`（idea_05 クローズ・idea_06 / idea_07 の条件更新）+ `/refactor_check` |
| task_11 | `save_dialog_flex_layout` | 一覧ダイアログの可変列化（対象名・保存先パスが幅追随／ラジオ列を切らさない）と、最小サイズでも OK・キャンセルが見えるボタン配置（v0.4-C 追記・受入条件 14b）。実機目視⑥の解消 |
| task_12 | `dependency_confirm_scope` | 依存確認ダイアログの提示条件の縮小（単独 / 新規作成は確認なし自動保存）と 4 択化＋deferred index 例外（v0.4-D/E/F/I・§8）。実機目視⑦の解消と受入条件 18 の再現テスト |
| task_13 | `data_replace_state_reset` | `data` を新規化・置換する全入口（`new_config` / `restore_default`）で trigger_set の状態をリセット（v0.4-H・受入条件 17） |
| task_14 | `individual_save_path_and_index` | 個別保存 3 経路の相対パス解決（cwd 直下へ書くバグ）と、子のパスが変わったときの上位 dirty 化（v0.5-J/N・受入条件 19・23）。実機目視①の解消 |
| task_15 | `trigger_set_individual_save_plan` | 個別「トリガー一覧を保存」を保存計画駆動にし、dirty な sequence があれば子ダイアログを出す（v0.5-K・§8・受入条件 20・21・21b）。実機目視②の解消 |
| task_16 | `save_dialog_initial_fit_and_wheel` | 一覧ダイアログの初期表示の省略計算と、スクロール領域のマウスホイール対応（v0.5-L/M・受入条件 22）。実機目視③④の解消 |

- 依存順は上表のとおり（task_01 → 09 → **11 → 12 → 13 → 14 → 15 → 16** → 10。**task_10 が最終**）。
  タスク定義は着手時に `/task_new` で順次起票する。
- **task_14〜16 は 2026-08-01 の実機目視フィードバックによる追加**（暫定仕様 05 **v0.5**）。
  task_15 は task_14 の J（パス解決）を前提とするため **14 → 15** の順で進める。
  判断履歴は `decisions.md` の「3 回目の実機目視フィードバック」節。
- **task_11〜13 は 2026-07-30 の実機目視フィードバックによる追加**（暫定仕様 05 **v0.4**）。
  判断履歴は `decisions.md` の「2 回目の実機目視フィードバック」節。
- **task_07〜09 は 2026-07-29 の実機目視フィードバックによる追加**（暫定仕様 05 v0.3）。
  旧 task_07（`finalize_records`）は **task_10 へ繰り下げ**。判断履歴は `decisions.md` の
  「実機目視フィードバック」節。task_07 → 08 の順に進める（A2 の判定が canonical identity に依存するため）。
- task_03 は**ダイアログ導入前に既存挙動と等価**であることを確認してから task_05 へ進む（挙動変更の切り分け）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有として以下を必ず見る。

- **依存方向**: 保存計画の**決定は presentation / 実行は application**。application にダイアログ（tkinter）依存を
  持ち込んでいないか。逆に presentation が JSON 書き込み順序を直接握っていないか。
- **後方互換**: 参照元キー無しの既存子JSON で保存・読込が壊れないか。既存キーの削除・意味変更が無いか
  （`spec_detail/data_schema.md`）。
- **粒度と依存関係**: 選んだ子だけを書くか（他 sequence を巻き込まない）。パスが変わる子の上位保存が
  必須化されスキップ不能か。失敗時に親索引だけ先へ進んでいないか。
- **過剰実装**: idea_06 の共通化は「子保存ドライバとして自然に達成される範囲」まで。共通化のための共通化を足さない。
  スコープ外（個別保存ボタン統合・掃除機能・hotkey_presets）へ踏み込んでいないか。
- **既定の安全側**: 未知の参照元・別の上位に属す子が「保存（上書き）」既定になっていないか（指摘① の後退）。
- タイミング別のレビュアー選択は `.claude/rules/agent_selection.md` のレビュー表に従う
  （task_06 の統合確認・task_07 前のフェーズ完了判定では `deep-reviewer` + Codex レビュー系を併用）。
