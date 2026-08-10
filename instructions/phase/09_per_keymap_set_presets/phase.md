# phase.md

## フェーズ名

keymap_set ごとの個別プリセット（per_keymap_set_presets）

## フェーズの目的

hotkey プリセットに、**グローバル既定 + keymap_set ごとの個別指定（上書き）**という 2 系統を導入する。
phase 08 で作った「アプリ全体のライブラリ」（正本 §5.10）はそのまま残し、
**「この構成セット専用のプリセット」**を持てるようにする。

**挙動変更 + スキーマ変更**を伴う。影響レイヤは
**application（解決順序・保存先の算出・別名保存時の複製）+ presentation（切替 UI・保存先表示）+
スキーマ（keymap_set のキー復活 + フラグ追加 / グローバル既定パスの変更）**で、
**domain のプリセット構造そのものは変えない**。

- 起票元: [idea_08](../../backlog/idea_08_per_keymap_set_preset_ownership.md)（2026-07-27 起票）。
  着手条件だった **phase 08 の完了（2026-08-09）**により昇格。
- 主入力（暫定仕様）: [08_per_keymap_set_presets.md](../../history/08_per_keymap_set_presets.md)
  （**v0.4**・ユーザー確定済）
- モード: **暫定仕様先行モード**。番号対応: **phase 09 / 暫定 08 / decisions_archive 09**。
- 同型の先行フェーズ: **Phase γ = phase 07**（hook キーの全体デフォルト + 個別指定。正本 §5.9）。
  グローバル既定と個別指定を 1 点で解決し、フック層・保存層を巻き込まない構造がそのまま参考になる。

## 確定（ユーザー 2026-08-09）

暫定仕様 08 §2 のとおり（要点のみ再掲。詳細は暫定仕様が正）:

- **ファイル配置を変える**: グローバル既定を **`user/hotkey_presets/global/default.json`** へ移し、
  個別ファイルは **`user/hotkey_presets/<keymap_set の stem>.json`**（直下）。
  **移行は手動**で、手順は **①ファイル移動 ②config.json に明示している場合はその値も書き換え**の 2 段。
- **keymap_set の旧キー `hotkey_presets_path` を個別パスとして再利用**し、
  **新フラグ `hotkey_presets_individual`（既定 false）が真のときだけ読む**。
  **フラグを持たない既存ファイルは常に OFF**（hook キーの「非空なら ON」判定は**採らない**）。
- **書き手はプリセットマネージャの 1 本のまま**（保存先が切り替わるだけ）。
  **保存カスケードはプリセットの内容を書かない**。
- **個別が読めなければグローバルへフォールバック**。**Import は個別指定を強制 OFF**。
- **切替 UI はマネージャ内**で、**トグルは保存先の切替のみ**（一覧は差し替えない）。
  **OFF へ戻して OK してもグローバルは書き換えない**。
- **別名保存では個別ファイルを複製して追随**（コピー先に実体があれば複製しない）。

## スコープ

### 含む

- グローバル既定パスの移動（`global/` 配下へ）+ 起動時のディレクトリ骨格追加 + **移行手順の明記**
- keymap_set への `hotkey_presets_individual` 追加と `hotkey_presets_path` の再利用（payload 生成の復活）
- **解決順序**（個別 → 読めなければグローバル → 置き換えない）と **config 外パスの無効化**
- **移行規則**（フラグを持たない既存 keymap_set は常に OFF）
- プリセットマネージャの**切替 UI・保存先表示・OK / キャンセルの契約**
- **Import での強制 OFF**、**別名保存時の個別ファイル複製**
- 上記を固定する特性テスト（`tests` / `tests_ui`）と実機目視

### 含まない（後送り）

- **プリセット編集 UI の刷新**（追加/編集/削除/並べ替えの操作体系は変えない）
- **グローバルの multi-library 化**（config.json が指すのは引き続き 1 本）
- **個別プリセットの保存計画ダイアログ（§5.8）への統合**（暫定仕様【B】で不採用）
- **グローバル既定パス変更の自動移行**（暫定仕様【G】で手動と確定）
- 破損プリセットファイルの検知・警告・退避（正本 §5.10.4 の既知の制約のまま）

## このフェーズで読むファイル

1. `instructions/history/08_per_keymap_set_presets.md` — **主入力（確定設計・v0.4）**
2. `instructions/common/spec_detail/data_schema.md` — 正本（**§5.10** プリセット / **§5.8.8** 入口台帳 /
   **§5.9** 同型パターン / §5.1 後方互換 / §5.4・§5.5 / §5.6 子の既定名 / §5.7 パス表記）
3. `instructions/common/codebase_map.md` — 責務（プリセットの解決点・`HotkeyPresetsIo`）
4. `keyseq/application/config_service/split_loading.py` — `load_global_hotkey_presets(_path)` /
   `build_runtime_data_from_split`（解決順序を足す場所）
5. `keyseq/application/config_service/__init__.py` — `HOTKEY_PRESETS_RELATIVE_PATH` /
   `ensure_split_config_dirs` / `apply_global_defaults` / `save_global_hotkey_presets`
6. `keyseq/application/config_service/save_path_resolution.py` — 子の既定パス算出（trigger_set の流儀）
7. `keyseq/application/config_service/split_payloads.py` — `build_keymap_set_payload`（固定キー集合）
8. `keyseq/presentation/dialogs.py` — `PresetManagerDialog`（切替 UI・OK / キャンセル）
9. `keyseq/presentation/app.py` — `save_hotkey_presets` / `open_preset_manager`
10. `keyseq/presentation/controllers/config_io/hotkey_presets_io.py` — 保存先の受け渡し
11. `keyseq/presentation/controllers/config_io/keymap_set_io.py` — Import（強制 OFF）/ 別名保存（複製）
12. テスト: `tests/test_config_service.py` / `tests/test_save_plan.py` /
    `tests_ui/test_app_ui_flows.py` / `tests_ui/test_config_io_characterization_keymap_set_startup.py`

> 上記以外へ広げない。範囲外の調査が要るときは `Explore` へ委任し結論だけ受け取る。

## タスク

| # | 内容 |
|---|---|
| task_01 | **グローバル既定パスの移動**（`user/hotkey_presets/global/default.json`）+ `ensure_split_config_dirs` へ `global/` 追加。既存テストの期待値更新 |
| task_02 | **keymap_set のスキーマ追加**（`hotkey_presets_individual` + `hotkey_presets_path` の payload 生成復活）。**移行規則（フラグ無しは常に OFF）**を含む。読込側の解決はまだ変えない |
| task_03 | **解決順序の実装**（個別 → 読めなければグローバル → 置き換えない / **config 外パスの無効化**）。`build_runtime_data_from_split` 側 |
| task_04 | **保存先の算出**（`save_path_resolution` に個別ファイルの既定パス）+ **マネージャの保存先切替**（`HotkeyPresetsIo` / `App.save_hotkey_presets`）|
| task_05 | **切替 UI**（マネージャ内のチェック・保存先表示の出し分け・OK / キャンセルの契約・未保存なら ON 不可）|
| task_05b | **無効な個別パス（config 外）での保存を拒否する**（暫定仕様 **v0.5【O3】**。task_05 の `reviewer` 指摘から追加した枝番タスク。読み出しの【O2】は不変）※**task_05c で反転**|
| task_05c | **無効な個別パスでの保存を「拒否」から「既定パスへ寄せて新規作成」へ反転**（暫定仕様 **v0.6【O3】**）+ **`hotkey_presets_path` の値が変化したときだけ dirty** |
| task_06 | **Import での強制 OFF** + **別名保存時の個別ファイル複製**（コピー先に実体があれば複製しない）|
| task_07 | **統合確認 + 実機目視**（受入条件 1〜17）。実測は `verifier`、実機目視の観点はタスク定義で列挙 + 指摘の是正 |
| task_08 | **正本反映（最終）**: `data_schema.md` **§5.10 改訂** + §5.5 / §5.4 / §5.8.8 / §5.1 + `codebase_map.md` / 暫定仕様 08 を凍結 / `decisions_archive/09_per_keymap_set_presets.md` 作成 / `current.md` 完了更新 / `backlog/INDEX.md` の idea_08 を完了へ（`INDEX_done.md` へ移動）/ `/refactor_check` 実行 |

- タスク定義は着手するものから順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。
- 受入条件 14（`tests` / `tests_ui` / smoke が更新後の期待値で pass）は**各タスクの完了条件に含める**
  （実装委任にテスト追加・修正まで含め、実測は `verifier`）。task_07 で通しの再実測を行う。
- **task_01 と task_02 は独立**（前者はグローバル側、後者は keymap_set 側）。task_03 は両方に依存する。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

- **後方互換（最重要）**: **フラグを持たない既存 keymap_set が常に OFF** になるか
  （残置 `hotkey_presets_path` を個別指定として復活させていないか）。判定は**値**で行っているか。
- **書き手の一本化**: プリセットの**内容を決める書き手がマネージャだけ**のままか。
  別名保存時の処理が**ファイルの複製に留まり**、runtime の内容を書き出していないか。
- **グローバルの保護**: 個別ファイルの保存先がグローバルと衝突しないか。
  **OFF へ戻した OK でグローバルが上書きされない**か。
- **入口台帳との整合**: E1〜E4 が常にグローバル・E5 が強制 OFF になっているか。
  **プリセット単独の注入 API を作っていない**か（正本 §5.8.8 の注記と衝突するため）。
- **パスの扱い**: 個別パスが §5.7 の表記で保存され、**config 外は無効**として扱われるか。
  相対値を解決なしで `os.path` 系へ渡していないか（`resolve_config_path` の罠）。
- **移行の明記**: 手動移行の 2 段（ファイル移動 + config.json の明示値）が正本に書かれているか。
- エージェント: 各タスク = `reviewer` / 統合確認・フェーズ完了判定 = `deep-reviewer` + Codex レビュー系
  （`.claude/rules/agent_selection.md` の表）。**フェーズ完了時の 2 本立ては省略しない**
  （phase 08 では両者が独立に起動不能バグを検出した）。
