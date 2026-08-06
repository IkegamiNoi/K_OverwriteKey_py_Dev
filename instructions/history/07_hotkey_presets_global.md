# 暫定仕様 07: プリセットの config.json グローバル化（hotkey_presets_global）

> 状態: **未凍結・v0.5・主入力・ユーザー確定済（実装着手可）**。本書がこのフェーズ（保存系リデザインの
> プリセット案2）の確定設計（フェーズ中は正本を直接改訂しない）。フェーズ末タスクで正本
> `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 版履歴: v0.1 起票（2026-07-27）→ **v0.2** codex-adversarial-reviewer 指摘 4 件を反映
> （① 移行は固定 `default.json` に標準化・keymap_set からの「引き上げ」はしない / ② keymap_set payload 生成から
> `hotkey_presets_path` を外す / ③ プリセットマネージャは即時にグローバルへ保存・成否付き / ④ `save_runtime_data` は
> プリセットを書かない・β と協調）。ユーザー確定 2026-07-27。
> → **v0.3**（2026-08-06・phase 08 起票時）: **§4 に検討事項 A「runtime を新規化・置換する入口の一本化」を追加**
> （計画06 = [modified_proposal/06](../modified_proposal/06_refactor_hook_key_pair_enumeration.md) からの持ち越し。
> **本フェーズ内 task_03 で設計・ユーザー確定する未確定項目**。§2・§3 の確定内容は無改変）。
> → **v0.4**（2026-08-06・task_03）: **検討事項 A を確定**（**案B = 注入 API を 1 本に束ねる** /
> `app.py` も新方式へ寄せる / ON→OFF は単独注入のまま / 空リストでは置き換えない）。
> 本文を **§3-2** へ新設し、受入条件 **7・8** を追加。§2・§3 は無改変。
> → **v0.5**（2026-08-06・task_03 の敵対的レビュー指摘を**2 件とも採用**）: ①読み出しを **`list | None`** に変え
> **「読めた空リスト」と「読めない」を区別**（空は採用・`None` は置き換えない。**通常読込も同規則へ統一**）
> ②**入口台帳（実測 9 箇所・E/L/N 分類）** を §3-2 へ追加し受入条件 7 を台帳全経路へ拡張・受入条件 9 を追加。
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

（§2〜§3 は確定済。実装時の詳細〔プリセットマネージャの保存失敗 UI・β との実装順序〕は
タスク定義で確認する。**β のカスケードからプリセット除外**は本フェーズと β のどちらで実装しても、
最終的に「keymap_set 保存はプリセットを書かない」が満たされればよい。）

### 検討事項 A: runtime を新規化・置換する入口の一本化 → **確定（v0.4・ユーザー 2026-08-06）**

**確定した方式 = 案B: 注入 API を 1 本に束ねる**（§3-2 に本文を移した。以下は背景と却下案の記録）。

- **却下: 案A（供給済みファクトリ `new_runtime_data(*, config_root)` へ寄せる）** — 呼び忘れを構造的に
  防げるが、**通常読込は hook キーがフラグ次第の条件付き注入**のため素の `new_default_data()` を
  使い続けることになり、「入口は 1 つ」にはならない。公開 API 変更でテスト 6 箇所 + 呼び出し 4 箇所へ
  波及する割に得るものが小さい。
- **却下: 案C（現状維持・プリセット注入も各所へ足す）** — 呼び忘れ面が **4 経路 × 2 種類**へ倍化する。
  この規約は task_07b の指摘 A で 1 度破れている。

**背景（起票時の記録）**: Phase γ 完了時の `/refactor_check` からの候補送り。挙動保存の範囲を超えるため
計画06 では見送り、**プリセットで 2 例目が出る本フェーズで設計する**とユーザーが判断した（2026-08-06）。

**現状**: runtime を新規化・置換する経路が **4 つ**あり、**各所で `apply_global_hook_key_defaults` を呼ぶ規約**に
なっている（`keymap_set_io` の新規作成 `:53` / Import `:562` / 例を復元 `:599` / `startup_io` の空データ起動 `:35`）。
さらに `app.py:77` の `new_default_data()` には注入が無く、**起動シーケンスが必ず上書きするという順序依存だけで
守られている**（5 個目の潜在的な穴）。

---

## §3-2 全体デフォルトの注入（v0.4 で確定）

- **`ConfigService.apply_global_defaults(runtime, *, config_root)` を新設**し、
  **hook キーの全体デフォルト注入 + グローバルプリセットの供給**をこの 1 本で行う。
  - hook キー部分は**既存 `apply_global_hook_key_defaults` をそのまま呼ぶ**（挙動不変・冪等）。
  - プリセット部分は `load_global_hotkey_presets_path` → `load_named_list` で読む。
  - **runtime を破壊的に更新して返す**・**冪等**・**例外を投げない**（読めなければ縮退）。
- **呼ぶ場所 = runtime を新規化・置換する 5 経路**: 新規作成 / Import / 例を復元 / 空データ起動 /
  **App 初期化（`app.py:77`）**。**`app.py` も新方式へ寄せ、順序依存で守られていた穴を塞ぐ**。
- **束ねた API を使わない経路**: `App.toggle_hook_keys_individual` の **ON→OFF** は
  **従来どおり `apply_global_hook_key_defaults` を直接呼ぶ**。束ねた API を使うと
  **キーの個別指定を切り替えただけでプリセットまで再読込**され、編集中のプリセットを取りこぼすため。
  **「hook キー単独の注入」と「runtime 置換時の全体注入」は別物**とする。
  `apply_global_hook_key_defaults` は**公開のまま・名前と引数も変えない**。
- **プリセットの読み出しは「読めたか」を区別する**（v0.5・敵対的レビュー指摘 high を採用）。
  `load_named_list`（不存在・破損・空をすべて `[]` に潰す）は使わず、
  **`list | None` を返す読み出し**を用いる:
  - **読めた場合 = `list`**（**空リストを含む**）… ファイルが読め、根キー `hotkey_presets` が list である。
  - **読めない場合 = `None`** … ファイルが無い / JSON として壊れている / 根キーが list でない。
- **供給規則（注入・通常読込で共通）**:
  - `list` を得たら**それが唯一の正**として `runtime["hotkey_presets"]` を**置き換える**
    （**空リストなら空にする** = ユーザーが全削除した意思を尊重する）。
  - `None` なら**置き換えない**（runtime の既定を維持 = 新規作成は組込 8 件 / 空データ起動は空 /
    通常読込は `new_default_data` 由来の組込 8 件）。**破損ファイルを既定値で黙って上書きしない**ため。
- **通常読込（`build_runtime_data_from_split`）も同じ供給規則に従う**（v0.5 で変更）。
  通常読込は `apply_global_defaults` を**経由しない**が、**読み出しと供給規則は共通**にする。
  → **経路によってプリセット集合が変わらない**（§2「全 keymap_set が同じグローバルライブラリを使う」を満たす）。
- **Import（レガシー単一 JSON・入口台帳 E5）の帰結**: 取り込んだファイルが**インラインで持つ
  `hotkey_presets` は、グローバルが読めればそれに置き換わる**（§2 の帰結）。
  グローバルが読めない（`None`）ときだけインラインの内容が残る。

### 入口台帳（v0.5・受入条件 7 の検査対象）

`app.data` を置き換える箇所は**実測 9 箇所**。**新しい全体デフォルトを追加するときは、この台帳の
全経路について供給の要否を判断する**（次の取りこぼしを防ぐための正本）。

| 分類 | 箇所 | 供給方法 |
|---|---|---|
| E1 | `presentation/app.py:77`（App 初期化）| **`apply_global_defaults`** |
| E2 | `config_io/keymap_set_io.py:53`（新規作成）| **`apply_global_defaults`** |
| E3 | `config_io/keymap_set_io.py:599`（例を復元）| **`apply_global_defaults`** |
| E4 | `config_io/startup_io.py:35`（空データ起動）| **`apply_global_defaults`** |
| E5 | `config_io/keymap_set_io.py:561`（Import = レガシー単一 JSON）| **`apply_global_defaults`** |
| L1 | `config_io/keymap_set_io.py:531`（keymap_set の読込）| `build_runtime_data_from_split` が供給 |
| L2 | `config_io/keymap_set_io.py:631`（構成セットの変更）| 同上 |
| L3 | `config_io/startup_io.py:25`（起動時の構成セット読込）| 同上 |
| N1 | `config_io/keymap_set_io.py:56`（新規作成直後の再正規化）| **供給不要**（E2 の直後で同一 runtime を正規化するだけ）|

### 既知の制約（v0.5）

- **破損ファイル（`None`）のときも、プリセットマネージャの保存は従来どおりファイルを上書きする**
  （task_06 の範囲）。破損内容を退避する仕組みは持たない。

**選択の経緯**（v0.3 時点の未確定記述・却下案の詳細）は
`.claude_data/state/decisions.md` の phase 08 節 task_03 が正。

## §5 受け入れ条件（ドラフト）

| # | 条件 | 対応 § |
|---|---|---|
| 1 | config.json の `hotkey_presets_path`（既定 default.json）からプリセットが読み込まれ、全 keymap_set で共通に使える | §3 |
| 2 | keymap_set payload に `hotkey_presets_path` が生成されず、読込時も参照しない（既存キーは残るが無視） | §2・§3 |
| 3 | プリセットマネージャの編集がグローバルファイルへ即時保存され、保存失敗時に編集内容を失わない | §3 |
| 4 | keymap_set の保存（`save_runtime_data` / β カスケード）でプリセットファイルが書き込まれない | §2 |
| 5 | 既存 keymap_set（`hotkey_presets_path` あり）でも起動・保存が正常（後方互換・無視） | §3 |
| 6 | `tests` / `tests_ui` / smoke が更新後の期待値で pass。読込元・保存先・カスケード除外を特性テストで固定 | §3 |
| 7 | **入口台帳の全経路**（E1〜E5 / L1〜L3 / N1）が分類どおりに供給され、E1〜E5 では `apply_global_defaults` が呼ばれる。**台帳のどの経路でもプリセット集合が一致する** | §3-2 |
| 8 | 個別指定 **ON→OFF** の切替では**プリセットが再読込されない**（hook キーだけが注入される） | §3-2 |
| 9 | グローバルが**読めた場合は空リストでも採用**（全削除が復活しない）、**読めない場合（不存在・破損）は置き換えない**。この規則が**注入経路と通常読込で一致する** | §3-2 |

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
| `codebase_map.md` | プリセットの読込元/保存先・プリセットマネージャの即時保存・カスケード除外を反映。**加えて §3-2 の注入契約**（`apply_global_defaults` を呼ぶ 5 経路 / ON→OFF は単独注入 / 通常読込は経由しない / 空リストでは置き換えない）|
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
