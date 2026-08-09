# phase.md

## フェーズ名

プリセットの config.json グローバル化（hotkey_presets_global）= 保存系リデザイン **プリセット案2**

## フェーズの目的

hotkey プリセットを「keymap_set ごとの参照」から **`config/config.json` が指すアプリ全体のライブラリ**へ
一本化する。**挙動変更 + スキーマ変更を伴う**。影響レイヤは **application（読込元の切替・保存カスケードからの除外・
payload 生成停止）+ presentation（プリセットマネージャの即時保存）+ スキーマ（config.json への追加）**で、
**domain のプリセット構造そのものは変えない**。

- 起票元: ユーザー要望（2026-07-26〜27・保存系統の改善討議・プリセットの位置づけ **P-a**）。
- 主入力（暫定仕様）: [07_hotkey_presets_global.md](../../history/07_hotkey_presets_global.md)
  （**v0.3**・ユーザー確定済。§4 の検討事項 A のみ本フェーズ内で確定する）
- モード: **暫定仕様先行モード**。番号対応: **phase 08 / 暫定 07 / decisions_archive 08**。
- 同型の先行フェーズ: **Phase γ = phase 07**（暫定 06・hook キーの全体デフォルト化）。
  解決点を 1 箇所へ集約しフック層を無変更に保つ設計がそのまま参考になる。

## 確定（ユーザー 2026-07-27 / 追加確定 2026-08-06）

暫定仕様 07 §2 のとおり（要点のみ再掲。詳細は暫定仕様が正）:

- config.json に **`hotkey_presets_path`（グローバル）** を持たせ、**全 keymap_set がこれを使う**。
  グローバルパスは既存の固定 `user/hotkey_presets/default.json` に**標準化**する（keymap_set からの引き上げはしない）。
- **keymap_set payload から `hotkey_presets_path` を外す**（新規保存では書かない）。既存キーは**読込時に無視**し、
  能動削除はしない（再保存で自然消滅）。
- **プリセットマネージャの編集はグローバルファイルへ即時保存**（成否付き）。
  **`save_runtime_data` / β のカスケードはプリセットを書かない**（唯一の書き手はプリセットマネージャ）。
- **【2026-08-06 追加】計画06 からの持ち越し = 「runtime を新規化・置換する入口の一本化」を本フェーズで設計・確定する**
  （暫定仕様 07 **§4 検討事項 A**）。プリセットの供給が hook キーと同型になるため、
  現状の「各入口で注入 API を呼ぶ規約」を続けると **4 経路 × 2 種類**になり、注入漏れの再発面が倍になる
  （task_07b の指摘 A で 1 度発生済み・`app.py` の生成 1 箇所は順序依存だけで守られている）。
  **task_03 で方式をユーザー確定してから実装する**（設計先行の不変原則）。

## スコープ

### 含む

- config.json への `hotkey_presets_path` 追加と**既定値補完**（未設定なら固定既定へ縮退）
- **プリセットの読込元の切替**（config.json 起点）+ keymap_set 側の同キーの**読込時無視**
- **keymap_set payload の生成停止** + **保存カスケードからのプリセット書出の除外**
- **プリセットマネージャの即時保存**（成否付き・失敗時に編集内容を失わない）
- **runtime を新規化・置換する入口の一本化**（設計確定 + 実装。hook キーの注入も新しい入口へ寄せる）
- 上記を固定する特性テスト（`tests` / `tests_ui`）と実機目視

### 含まない（後送り）

- **keymap_set ごとの個別プリセット（オーバーライド）** → [idea_08](../../backlog/idea_08_per_keymap_set_preset_ownership.md)
  （本フェーズ完了後に着手条件を満たす）
- **プリセット編集 UI の刷新**（読込元 / 保存先の変更のみ。ダイアログの操作体系は変えない）
- レガシー `settings/` 配下へのフォールバック経路 → [idea_09](../../backlog/idea_09_legacy_settings_save_path_fallback.md)

## このフェーズで読むファイル

1. `instructions/history/07_hotkey_presets_global.md` — **主入力（確定設計）**
2. `instructions/common/spec_detail/data_schema.md` — 正本（**§5.9** = hook キーの同型パターン / JSON 後方互換）
3. `instructions/common/codebase_map.md` — 責務（config_service の hook キー解決点 4 つの記述が設計の下敷き）
4. `keyseq/application/config_service/__init__.py` — `HOTKEY_PRESETS_RELATIVE_PATH:24` / `new_default_data` /
   `new_empty_data` / `apply_global_hook_key_defaults:434`
5. `keyseq/application/config_service/split_loading.py` — `:84` プリセットの読込（`keymap_set.get("hotkey_presets_path")`）/
   `load_global_hook_keys`（同型の読み出し API）
6. `keyseq/application/config_service/split_payloads.py` — `:39-42` / `:102` / `:299` / `:337`（payload 生成の 4 箇所）
7. `keyseq/application/config_service/save_plan_execution.py` — `:135` カスケードの書込
8. `keyseq/presentation/dialogs.py` — `PresetManagerDialog:345`（編集結果の確定点）と `:341` の呼び出し
9. `keyseq/presentation/app.py` — `open_preset_manager:406` / `:77` の runtime 生成
10. `keyseq/presentation/controllers/config_io/startup_io.py` — config.json への書込 1 本道（`write_startup` / `write_global_hook_keys`）
11. `keyseq/presentation/controllers/config_io/keymap_set_io.py` — 新規作成 `:53` / Import `:562` / 例を復元 `:599`（入口 3 経路）
12. テスト: `tests/test_config_service.py` / `tests/test_save_plan.py` /
    `tests_ui/test_config_io_characterization_keymap_set_startup.py`

> 上記以外へ広げない。範囲外の調査が要るときは `Explore` へ委任し結論だけ受け取る。

## タスク

| # | 内容 |
|---|---|
| task_01 | config.json の `hotkey_presets_path` をスキーマへ追加し、**未設定時の既定補完**付きの読み出し API を新設（同型 = `load_global_hook_keys`）|
| task_02 | **プリセットの読込元を config.json へ切替**。keymap_set 側の `hotkey_presets_path` は読込時に無視（能動削除しない）|
| task_03 | **【設計確定】runtime を新規化・置換する入口の一本化**（4 経路 + `app.py` の生成 1 箇所を棚卸し → 方式をユーザー確定 → 暫定仕様 07 を **v0.4** へ改訂。敵対的レビュー必須・**実装は含まない**）|
| task_04 | task_03 の確定方式で入口を実装（**プリセットと hook キーの供給を新しい入口へ寄せる**。通常読込の条件付き注入との等価性を維持）|
| task_05 | **keymap_set payload から `hotkey_presets_path` を外す** + 保存カスケードからプリセット書出を除外（`save_runtime_data` は書かない）|
| task_06 | **プリセットマネージャの編集をグローバルファイルへ即時保存**（成否付き・失敗時に編集内容を失わない・dirty を汚さない）|
| task_07 | **統合確認 + 実機目視**（受入条件 **1〜6**）。特性テストの実測は `verifier`（compile / `tests` / `tests_ui` / smoke）、実機目視の観点はタスク定義で列挙 + 指摘の是正 |
| task_07b | **横断レビュー指摘の是正**（`deep-reviewer` の H1 / M1 / M2 / L3。**読み出し側で正規化**・死にコード削除・E1 の特性テスト・deepcopy）。規範は暫定仕様 **v0.6** |
| task_08b | **フェーズ完了レビューの High 是正**（`normalize_hotkey_presets` が非文字列 `label`/`value` で例外 → E1 が捕捉せず起動不能。**要素単位で除去**。規範 = 正本 `data_schema.md` §5.10.2）|
| task_08 | **正本反映（最終）**: `spec_detail/data_schema.md` + `codebase_map.md` へ昇格 / 暫定仕様 07 を凍結 / `decisions_archive/08_hotkey_presets_global.md` 作成 / `current.md` 完了更新 / `backlog/INDEX.md` の **idea_08** 行を着手可へ更新 / `/refactor_check` 実行 |

- タスク定義は着手するものから順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。
- 受入条件 6（`tests` / `tests_ui` / smoke が更新後の期待値で pass）は**各タスクの完了条件に含める**
  （実装委任にテスト追加・修正まで含め、実測は `verifier`）。task_07 で通しの再実測を行う。
- **task_03 の確定前に task_04 へ着手しない**（設計先行の不変原則・`.claude/rules/spec_change_workflow.md`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

- **後方互換**（最重要）: 既存 keymap_set の `hotkey_presets_path` が残っていても起動・保存・再保存が壊れないか。
  **既存キーの能動削除をしていないか**（`data_schema.md` の既存キー削除禁止）。
- **書き手の一本化**: プリセットファイルの書き手が**プリセットマネージャだけ**になっているか。
  保存カスケード・`save_runtime_data` からの書込経路が残っていないか。
- **注入漏れ**（phase 07 の再発防止）: runtime を新規化・置換する**全経路**でプリセットが供給されるか。
  task_04 以降は「入口の棚卸し表」と実装を突き合わせて確認する。
- **成否の扱い**: config.json / プリセットファイルへの書込失敗時に、**編集内容を失わず・確定もしない**か
  （phase 07 の `write_global_hook_keys` と同じ契約）。
- エージェント: 各タスク = `reviewer` / **task_03（設計確定）= `codex-adversarial-reviewer`**（縮退時は `deep-reviewer`）/
  統合確認・フェーズ完了判定 = `deep-reviewer` + Codex レビュー系（`.claude/rules/agent_selection.md` の表）。
