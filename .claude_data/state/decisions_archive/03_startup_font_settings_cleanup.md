# decisions_archive / 03_startup_font_settings_cleanup

フェーズ **03_startup_font_settings_cleanup**（起動設定 / フォント設定クラスタの整理）の判断履歴。
索引は `.claude_data/state/decisions.md`「アーカイブ索引」。
フェーズ定義: `instructions/phase/03_startup_font_settings_cleanup/phase.md`。
**設計の正（凍結）**: 暫定仕様 `instructions/history/02_startup_font_settings_cleanup.md`（v1.0・凍結）。

- 期間: 2026-07-18（起票・確定）〜 2026-07-20（完了）
- モード: **暫定仕様先行モード**（番号対応: phase 03 / 暫定 02 / decisions 03。暫定仕様は独立採番）
- 目的: App（presentation）に残る起動設定読込・フォント設定の 3 メソッド
  （`_coerce_font_delta` / `_load_startup_settings` / `set_ui_font_delta`）を整理し、4 負債
  （①責務混在 ②controller → App private 逆参照 ③初期化順序の制約 ④ui_vars の App private 直読み）を解消。
- 結果: **完了**（task_01〜05）。標準検証全緑・実機目視 OK・reviewer/codex-reviewer 指摘なし。**挙動不変**。
- 起票元: [idea_02](../../instructions/backlog/idea_02_startup_font_settings_cleanup.md)（計画04 W7 の残留ロジック分類から分離）

---

## 設計判断（暫定仕様 §2・ユーザー確定 2026-07-18・v1.0）

1. **coerce_font_delta の落とし先 = `theme.py` の純関数** → **採用**。App private を廃し逆参照を解消。
2. **起動設定ローダ = 新規 `presentation/startup_settings.py`** → **採用**。`config_service` 直依存で初期化順序を壊さない。
3. **フォント設定の責務分離 = 案 A（最小抽出）** → **採用**。`_ui_font_delta_pt` は App 保持。
   **案 B（FontSettingsController 新設）は今フェーズ見送り** → **保留（将来 idea）**。初期化順序（生成順序・初期 delta の
   単一所有者・注入時点・保存経路・保存失敗時の状態）が未確定のため、挙動不変を保証できない。
4. **エラー通知 = `on_read_error(exc)` コールバック注入** → **採用**。真理値表どおり分岐・回数・文言は不変。
5. **未知キー全保持の契約** → **採用**。読込 dict の全キーを保持し既知2キー（`ui_font_delta_pt` / `prompt_if_missing`）のみ正規化。

## 敵対的レビューの指摘処理（暫定仕様 §2 版歴・codex-adversarial-reviewer 2026-07-18・v0.2 反映）

- **未知キー全保持を契約として明記**（[high]）→ **採用**。新ローダが既知2キーだけの dict を返すと `keymap_set_path` が
  失われ起動時に構成が読めず次回保存で不可逆消失する、を実コードで裏取り。受け入れ条件 §8-12 + fixture で固定。
- **警告発火の真理値表を固定**（[medium]）→ **採用**。欠損=無警告 / 例外=警告1回 / 非dict=無警告。title/body 1文字一致。
- **案 B を今フェーズ実装候補から外す**（[medium]）→ **採用**。案 A に限定（上記設計判断3）。

## テスト再編の判断（task_01〜04・移設に伴う安全網の付け替え）

- **task_01**: 3 メソッドは現時点で App 専用のため、特性テストは App インスタンス経由（`tests_ui`）で現行挙動を固定 →
  **採用**（task_01 の制約〔依存なし・実装不変〕から一意）。tk 不要な自由関数向けユニットテストは各移設タスクで追加する方針。
- **task_02（coerce 移設）**: 特性テストの coerce 呼び出しを `theme.coerce_font_delta` へ付け替え（アサーション不変）+
  tk 不要の `tests/test_theme_coerce.py` 新規 → **採用**。削除される App メソッドへの参照を移設先へ機械的に付け替え。
- **task_03（ローダ切り出し）**: 純ローダ論理を tk 不要の `tests/test_startup_settings.py`（fake config_service + 記録
  コールバック）へ移設し、`tests_ui` の `test_load_startup_settings_truth_table` を撤去（同等以上に担保）→ **採用**。
  write_startup ラウンドトリップ（§8-12・App/config_io 必要）と警告文言（§8-8）は `tests_ui` に残す。**弱体化ではない**。
- **task_04（案A分割）**: `test_set_ui_font_delta_applies_only_real_changes` を**無改変で pass** させることが分割の挙動不変の証明 → **採用**。

## 実装上の注意点（各タスクで確認）

- **初期化順序の維持**（task_03）: 新ローダ呼び出し `load_startup_settings(app.py:58)` < `UiVars(:69)` < `ConfigIoController(:135)`。
  `config_service`（`:43`）のみ依存し `config_io`（`:127`相当）に非依存。
- **メニュー再構築の副作用**（task_04）: フォント変更で `build_menu_bar` のみ・`bind_menu_shortcuts` を呼ばない（計画04 W2 の判断を保持）。
- 新規（未追跡）ファイルの確認 grep は `git grep` でなく**直接 grep**（`git grep` は追跡済みのみ）。
- app.py の行数計測は `wc -l`（PowerShell Measure-Object は空行を数えない）。

## 正本反映（昇格）要否（task_05・調査 2026-07-20）

- **昇格不要** → **採用**。`instructions/common/spec_detail/` に startup / font_delta / coerce の担当層記述は
  **存在しない**（grep 該当ファイル 0 件）。担当層/クラス割り当ては `architecture.md §3.5` が「codebase_map.md を正とする」と明言。
  挙動不変ゆえ仕様変更なし。追従更新は **`codebase_map.md`** のみ実施（startup_settings.py 追記 / theme.coerce_font_delta /
  App のフォント適用分割・起動設定読込委譲 / UiVars 引数化を反映）。
- 暫定仕様 `history/02_startup_font_settings_cleanup.md` は **v1.0 で凍結**。

## /refactor_check 判定（task_05・2026-07-20）

- **不要**（M1〜M6 いずれも非該当。対象: keyseq/ 5 ファイル / +55・-41 行。PHASE_BASE=`e927be7`〜HEAD）→ **採用**。
  - M1: app.py 448 行（600 未満）・実質 +17 行。config_io_controller.py 598 行だが本フェーズは +1 行のみ（非該当）。
  - M2: 80 行超の新規関数なし（最大 `load_startup_settings` 15 行）。M3: coerce を1箇所へ集約＝重複排除の方向。
  - M4: なし。M5: 申し送りコメント新規 0 件。M6: `-3/+3` は `theme.coerce_font_delta` の1箇所のみ（重複なし）。
- 提案書は起票しない。既存負債として `config_io_controller.py`（598 行・600 目安に接近）を `current.md`「別タスク化候補」へ記録。

## codebase_map / 正本仕様の更新

- `codebase_map.md`: **更新** → **採用**。presentation ツリーに `startup_settings.py` 追記 / `theme.py` に `coerce_font_delta` /
  App 責務に「起動設定読込の委譲 + フォント適用の `_apply_font_delta`/`set_ui_font_delta` 分割」/ UiVars の引数化を反映。
- `spec_detail/`: **更新不要**（上記「昇格要否」の裏取りどおり）→ **採用**。

## コミット一覧

| コミット | 内容 |
|---|---|
| `624753e` | フェーズ 03_startup_font_settings_cleanup を起票（暫定仕様 02 v1.0 確定） |
| `e927be7` | handoff 再生成（PHASE_BASE。task_01 着手前の状態） |
| `41f6f6a` | task_01: 起動設定/フォント3メソッドの特性テスト追加（安全網・実装無変更） |
| `397a9d1` | task_02: coerce_font_delta を theme.py へ移設・逆参照解消 |
| `c961b2a` | task_03: 起動設定ローダを startup_settings.py へ切り出し |
| `6c49620` | task_04: フォント適用を案A分割・UiVars を引数化 |
| （本コミット） | task_05: 正本反映・記録（codebase_map / 凍結 / decisions_archive / INDEX 移動 / refactor_check 判定） |

## 検証・レビュー

- 標準検証（全タスクで全緑・`.venv` python）: compile clean / tests **86**（77 基準 + coerce 5 + startup ローダ4）/
  tests_ui **20**（16 基準 + 特性テスト。truth_table 撤去 -1・警告文言 +1）/ smoke pass。
  **特性テスト（案A分割は無改変で pass）＝挙動不変の証明**。
- reviewer（5観点）: task_01〜04 いずれも「**完了可**・指摘なし」。
- codex-reviewer（task_04 統合の二次レビュー）: **指摘なし**。
- 実機目視（task_04・ユーザー 2026-07-20 **OK**）: 起動時 startup.json〔正常/欠損/破損/非dict〕のフォント適用・警告挙動 /
  メニューからのフォント変更の即時反映・永続化・再起動保持 / `keymap_set_path` 構成の起動復元。

## 次フェーズへの申し送り

- **案 B（FontSettingsController 新設）は将来 idea 化**（初期化順序設計を詰めてから）。フォント設定項目の拡張が
  現実に必要になった時点で着手する。
- `config_io_controller.py`（598 行）が 600 行目安に接近。次フェーズ以降の /refactor_check で再判定
  （`current.md`「別タスク化候補」に記録）。
- 未着手の派生 idea: [idea_03](../../instructions/backlog/idea_03_action_hotkey_save_normalization.md)（アクション hotkey の
  保存時正規化/検証の統一・優先度低・要設計）。
- 次採番は phase **`04`**。
