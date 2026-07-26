# 暫定仕様 07: プリセットの config.json グローバル化（hotkey_presets_global）

> 状態: **未凍結・v0.2・主入力・ユーザー確定済（実装着手可）**。本書がこのフェーズ（保存系リデザインの
> プリセット案2）の確定設計（フェーズ中は正本を直接改訂しない）。フェーズ末タスクで正本
> `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 版履歴: v0.1 起票（2026-07-27）→ **v0.2** codex-adversarial-reviewer 指摘 4 件を反映
> （① 移行は固定 `default.json` に標準化・keymap_set からの「引き上げ」はしない / ② keymap_set payload 生成から
> `hotkey_presets_path` を外す / ③ プリセットマネージャは即時にグローバルへ保存・成否付き / ④ `save_runtime_data` は
> プリセットを書かない・β と協調）。ユーザー確定 2026-07-27。
> 起票元: ユーザー要望（2026-07-26〜27・保存系統の改善討議・プリセットの位置づけ P-a）。
> Phase γ（暫定 06）と同型。keymap_set ごとの個別プリセットは
> [idea_08](../backlog/idea_08_per_keymap_set_preset_ownership.md)（本フェーズ完了後）。

---

## §1 目的 / 背景

hotkey プリセットは**アプリ全体で共有するライブラリ**としての運用が近い（ユーザー判断 P-a）。
現状は各 keymap_set が `hotkey_presets_path` で参照しており、**構成セットごとに参照が分かれて**いる。
これを **`config/config.json`（起動エントリ）が指すグローバルなプリセットファイル**へ一本化する。
本フェーズは**挙動変更・スキーマ変更を伴う**。

### 現状監査（2026-07-27）

- プリセットの実体は固定 `config/user/hotkey_presets/default.json`（`config_service.py:22` `HOTKEY_PRESETS_RELATIVE_PATH`）。
- **keymap_set.json が `hotkey_presets_path` を持ち**（`config_service.py:592` 保存 / `:287` 読込）、
  runtime へは `_load_named_list(keymap_set.get("hotkey_presets_path"))`（`:286-290`）で読み込まれる。
- **keymap_set payload は毎回再生成される**（`_build_keymap_set_payload` 相当が `hotkey_presets_path` を新規生成・`:592`）。
  → 既存生JSONをそのまま保持していないため「残置・無視」は payload 生成から外す形で行う（§3・指摘②）。
- 保存時は `save_runtime_data` のカスケードで `hotkey_presets_path` へ**無条件書込**（`:234-235` / `:503-521`）。
- **プリセット編集**: `PresetManagerDialog`（`open_preset_manager` 経由）は OK 時に `parent.data` を更新するのみで、
  実際の書き出しは keymap_set のカスケード保存に依存する（→ §3・指摘③でグローバルへ即時保存に変更）。
- config.json はプリセット参照を持たない。

## §2 確定事項（ユーザー 2026-07-27・P-a=案2）

- **プリセットを config.json のグローバル参照へ移す**。config.json に **`hotkey_presets_path`（グローバル）** を持たせ、
  **全 keymap_set がこのグローバルプリセットを使う**。
- **【指摘①】グローバルパスは既存の固定 `config/user/hotkey_presets/default.json` に標準化**する。
  keymap_set 個別の `hotkey_presets_path` からの「引き上げ」は**しない**（複数セットが別パスを持つ場合の勝者未定義を回避）。
- **keymap_set は既定ではプリセットを参照しない**。keymap_set ごとの個別プリセット（オーバーライド）は**本フェーズ対象外**
  → [idea_08](../backlog/idea_08_per_keymap_set_preset_ownership.md)（後続）。
- **【指摘②】keymap_set payload 生成から `hotkey_presets_path` を外す**（新規保存では書かない）。既存 keymap_set に
  残る同キーは**読込時に無視**する（`data_schema` 既存キー削除禁止に従い能動削除はしない・再保存で自然に消える）。
- **【指摘③】プリセットマネージャの編集はグローバルファイルへ即時保存**（成否付き）。keymap_set 保存に依存しない。
- **【指摘④】`save_runtime_data`（keymap_set カスケード）はプリセットを書かない**。Phase β のカスケードからも
  プリセット書出を外す（β §11「hotkey_presets は触らない」と協調）。プリセットの唯一の書き手はプリセットマネージャ。
- 影響レイヤ: application（プリセットの読込元を config.json へ・カスケードから除外）+ presentation（config.json 参照の配線・
  プリセットマネージャの即時保存）+ スキーマ（config.json にプリセットパス追加・keymap_set 側は生成停止＋残置無視）。

## §3 データモデルと解決順序（指摘①〜④反映）

- **config/config.json（グローバル）**: `hotkey_presets_path`（既定 `user/hotkey_presets/default.json`・相対）。
  config.json に無ければ既定値で補完する（keymap_set からの引き上げはしない）。
- **プリセットの読込**: runtime 構築時、**config.json の `hotkey_presets_path`** から読む
  （keymap_set の `hotkey_presets_path` は参照しない・生成もしない）。
- **プリセットの保存**: プリセットマネージャの編集結果を、**config.json が指すグローバルファイルへ即時保存**する
  （成否付き。失敗時は編集内容を失わず再試行可能に）。`save_runtime_data` はプリセットを書かない。
- **後方互換**: 既存 keymap_set の `hotkey_presets_path` は読込時に無視。payload 生成停止により再保存で自然消滅。
  既存キーの能動削除はしない。

## §4 確認事項

（v0.2 時点で未確定なし。§2〜§3 で確定。実装時の詳細〔プリセットマネージャの保存失敗 UI・β との実装順序〕は
タスク定義で確認する。**β のカスケードからプリセット除外**は本フェーズと β のどちらで実装しても、
最終的に「keymap_set 保存はプリセットを書かない」が満たされればよい。）

## §5 受け入れ条件（ドラフト）

| # | 条件 | 対応 § |
|---|---|---|
| 1 | config.json の `hotkey_presets_path`（既定 default.json）からプリセットが読み込まれ、全 keymap_set で共通に使える | §3 |
| 2 | keymap_set payload に `hotkey_presets_path` が生成されず、読込時も参照しない（既存キーは残るが無視） | §2・§3 |
| 3 | プリセットマネージャの編集がグローバルファイルへ即時保存され、保存失敗時に編集内容を失わない | §3 |
| 4 | keymap_set の保存（`save_runtime_data` / β カスケード）でプリセットファイルが書き込まれない | §2 |
| 5 | 既存 keymap_set（`hotkey_presets_path` あり）でも起動・保存が正常（後方互換・無視） | §3 |
| 6 | `tests` / `tests_ui` / smoke が更新後の期待値で pass。読込元・保存先・カスケード除外を特性テストで固定 | §3 |

- **安全網**: プリセットの読込元（config.json・既定補完）・プリセットマネージャの即時保存（成否）・カスケードからの
  除外を特性テストで固定する。

## §6 スコープ外（本フェーズでやらない）

- **keymap_set ごとの個別プリセット（オーバーライド）** → [idea_08](../backlog/idea_08_per_keymap_set_preset_ownership.md)。
- **プリセット編集 UI の刷新**（読込元/保存先の変更のみ）。
- **停止/トグルキーの config.json 既定化** → Phase γ（暫定 06・同型だが別フェーズ）。

## §7 正本反映（フェーズ末昇格・予定）

| 対象 | 内容 |
|---|---|
| 正本 `spec_detail/` | `data_schema.md` に config.json の `hotkey_presets_path`（グローバル・既定 default.json）と、keymap_set 側の同キーの扱い（生成停止・残置無視）を追記 |
| `codebase_map.md` | プリセットの読込元/保存先・プリセットマネージャの即時保存・カスケード除外を反映 |
| 実装 | `config_service.py`（読込元を config.json へ・カスケードからプリセット除外・payload 生成停止）/ `config/config.json` スキーマ / `PresetManagerDialog`（グローバル即時保存・成否）|
| テスト | `tests/`（読込元・カスケード除外）/ `tests_ui/`（プリセットマネージャの即時保存と成否）|
| 別実装同期 | なし |

## 関連

- 保存系リデザイン討議: ユーザー要望（2026-07-26〜27・P-a）。
- 後続: [idea_08](../backlog/idea_08_per_keymap_set_preset_ownership.md)（keymap_set 個別プリセット）。
- 協調: Phase β（[暫定 05](05_child_file_save_dialog.md)・カスケードからプリセット除外）。
- 同型パターン: Phase γ（[暫定 06](06_hook_keys_global_default.md)）。
- 敵対的レビュー: codex-adversarial-reviewer（2026-07-27・v0.1 対象・needs-attention）。指摘 ①〜④ を v0.2 で反映。
- 正本: `spec_detail/data_schema.md`（JSON 後方互換）/ `codebase_map.md`。
- 参照ルール: `.claude/rules/spec_change_workflow.md`。
