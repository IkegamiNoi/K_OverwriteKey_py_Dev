# 暫定仕様 04: 新規作成と保存先ディレクトリの整理（keymap_set_new_and_default_dir）

> 状態: **凍結（正本へ昇格済・phase 05 完了 2026-07-28）**。以後**本書は改訂しない**（履歴として保存）。
> 昇格先: `instructions/common/spec_detail/data_schema.md` **§5.4 配下「keymap_set の保存先と『ファイルなし』状態」**
> （新規/Import/空起動の 3 経路・既定ディレクトリ・別名保存分岐・初期名 `keymap_set.json`）と
> **§5.6**（keymap_set 未設定時の trigger_set ファイル名フォールバック）/
> `instructions/common/codebase_map.md`（App の起動時ディレクトリ作成・KeymapSetIo・StartupIo の責務）。
> 判断履歴は `.claude_data/state/decisions_archive/05_keymap_set_new_and_default_dir.md` が正。
> （凍結前の状態: v0.3・主入力・ユーザー確定済。フェーズ中は本書が正で、正本は直接改訂しなかった）
> 版履歴: v0.1 起票（2026-07-27）→ **v0.2** codex-adversarial-reviewer 指摘 4 件を反映
> （① Import 後の path 無条件クリア / ② 子ファイル共有の制約を明記し複数独立セット対応を β へ後送り /
> ③ `prompt_if_missing` は残置許容へ方針変更・受入条件を緩和 / ④ 起動時にディレクトリ骨格を一括作成）→
> **v0.3 ユーザー確定（2026-07-27）**: §7-1 = 別名保存の初期ファイル名は **`keymap_set.json`**（一般名）に確定。
> 起票元: ユーザー要望（2026-07-26〜27・保存系統の改善討議）。保存系リデザイン全体（点1〜5）のうち
> **点1・点2 と「デフォルト保存先＝ディレクトリ」への訂正、および死にフラグ `prompt_if_missing` の撤去**を扱う。
> 後続フェーズ: Phase β（子ファイル保存の確認ダイアログ・暫定 05 予定）/ Phase γ（停止・トグルキーの
> config.json 既定化・暫定 06 予定）/ プリセットの config.json グローバル化（暫定 07 予定）。

---

## §1 目的 / 背景

構成セット（keymap_set）の**新規作成・保存の挙動**を、ユーザーの想定に合わせて整える。
本フェーズは**挙動変更を伴う**（挙動不変フェーズではない）。

解決する不満（ユーザー討議 2026-07-26〜27）:

- **点1**: 新規作成しても内部で既定パスが設定されているため、「保存」を押すと**別名保存が走らず、
  既存の既定ファイルに無言で上書き**される。新規作成直後は「ファイルなし」で、最初の保存は別名保存であってほしい。
- **点2 + 訂正**: ファイルラベルフレームの保存/別名保存の既定保存先は本来
  **`config/user/keymap_sets/`（ディレクトリ）** で、用途別に複数ファイルを置いて読み分ける想定。
  固定 `default.json` を既定の保存ターゲットにする現状がそぐわない。
- 起動設定の `prompt_if_missing` フラグは**保存・正規化されるがどこからも参照されない死にフラグ**であり、整理対象。

### 現状監査（2026-07-27）

対象は `keyseq/presentation/controllers/config_io/keymap_set_io.py`（KeymapSetIo）と
`keyseq/presentation/config_paths.py`（ConfigPaths）、`keyseq/presentation/controllers/config_io/startup_io.py`
（StartupIo）、`keyseq/application/config_service.py`（ConfigService）、`keyseq/presentation/startup_settings.py`。

**新規作成 / 保存 / 起動フローの現挙動**:

1. `new_config`（`keymap_set_io.py:26-42`）は末尾で
   **`self._app.keymap_set_path = self._app.paths.preferred_keymap_set_path()`（:33）**を設定する。
   `preferred_keymap_set_path()`（`config_paths.py:19-20`）は **`config/user/keymap_sets/default.json`**（固定）。
2. `save_keymap_set`（`:44-49`）は `save_keymap_set_to(self._app.keymap_set_path, ...)` を呼ぶ。
   新規作成直後は上記のとおり `keymap_set_path` が `default.json` を指すため、**別名保存を経ずに
   `default.json` へ書き込む（＝点1 の無言上書き）**。
3. `save_keymap_set_to`（`:68-92`）は空パスでも `normalize_keymap_set_save_path("")`（`config_paths.py:62-64`）が
   `preferred_keymap_set_path()` を返すため、**空でも `default.json` にフォールバックする**。
4. `save_as`（`:51-66`）は `asksaveasfilename` の `initialdir` を `suggest_keymap_set_dialog_dir()`、
   `initialfile` を `suggest_keymap_set_dialog_path()` の basename で提示する（別名保存自体は正しくパス選択させる）。
5. `import_config`（`:124-148`）は `if not self._app.keymap_set_path:` のとき
   `preferred_keymap_set_path()` を設定する（`:137-138`）。**保存済みセットを開いた状態で Import すると
   `keymap_set_path` は既存セットのまま残り、保存で元セットを上書きしうる**（敵対的レビュー指摘 ①）。
6. 起動時 `load_startup_and_config`（`startup_io.py:11-35`）は冒頭で
   `self._app.keymap_set_path = self._app.paths.preferred_keymap_set_path()`（`:18`）を置き、
   `config/config.json` の `keymap_set_path` が指すファイルが在れば読む。**無い/読めない場合は無言で
   `new_empty_data()` 起動**（`:34`）だが、`keymap_set_path` は `default.json` を差したまま残る。

**分割保存の子ファイル配置（本フェーズの制約の根拠）**:

- `save_runtime_data` は config_root 内へ保存する場合（`choose_split_base_dir` が空を返す場合）、
  trigger_set / hotkey_presets を **全セット共通の固定パス**（`user/trigger_sets/default.json` /
  `user/hotkey_presets/default.json`）へ書き込む（`config_service.py:468-476`）。
  → **同一ディレクトリに複数の keymap_set を保存すると、子ファイルを共有・上書きする**（敵対的レビュー指摘 ②）。
  子ファイルのセット別分離は **Phase β + プリセット案2** の領域であり、本フェーズでは扱わない（§9 制約）。

**ディレクトリ作成のタイミング**:

- 起動時（`app.py:56`）に作られるのは `user/` のみ。keymap_sets 等の骨格は
  `_ensure_split_config_dirs`（`config_service.py:926-933`）が**保存時に**まとめて作成する（`:226`）。
  → 新規プロファイルの初回 Save As では `config/user/keymap_sets/` が未作成で、
  `suggest_keymap_set_dialog_dir` が `config_root` を返し config 直下が初期ディレクトリになる（敵対的レビュー指摘 ④）。

**`prompt_if_missing` の現状（死にフラグ）**:

- 保存・正規化される: `config_service.py:545` / `startup_settings.py:17` / `startup_io.py:38-42`
  （`write_startup` の base 既定）/ `keymap_set_io.py:202`（`set_startup_keymap_set` が明示的に `True` を書く）。
- **どこからも「見つからないときに確認する」挙動を駆動していない**（`load_startup_and_config` は
  フラグを参照せず常に無言で空起動）。→ **完全な死にフラグ**。
- **注意（残置の性質）**: `load_startup_settings` は未知キーを保持し、`write_startup` は `_startup_settings` を
  base へ update するため、コードから当該4行を消しても**既存 config.json の `prompt_if_missing` は次回保存で
  再出力される**（自然消滅しない）。→ §6 の方針を「残置許容」に確定（敵対的レビュー指摘 ③）。

**`config/config.json` = 起動エントリ**（`config_paths.py:16-17` `preferred_startup_path` /
`config_service.py:935-936` `_startup_entry_path` が一致）。**初回保存時に作成**され、以後起動時に最初に読む。

## §2 確定事項（ユーザー 2026-07-26〜27）

- **新規作成は「ファイルなし」にする**。`new_config` は `keymap_set_path` を**空**にし、内部で既定ファイルを設定しない。
- **保存（`save_keymap_set`）は、`keymap_set_path` が空なら別名保存（`save_as`）へ分岐する**。
  ファイルがまだ無い状態で「保存」を押すと実質 save_as になる挙動を**許容**する（ボタン名は「保存」のまま）。
- **Import 成功時は `keymap_set_path` を無条件で空にする**（開始パスが空/非空どちらでも次の保存が別名保存になる）。
- **既定保存先は固定 `default.json` ではなく、ディレクトリ `config/user/keymap_sets/`**。
  別名保存ダイアログの初期ディレクトリとしてこのフォルダを提示し、ファイル名はユーザーが決める。
  **`default.json` への無言の自動保存・自動フォールバックを廃止する**。
- **別名保存ダイアログの初期ファイル名は `keymap_set.json`（一般名）**（ユーザー確定 2026-07-27・§7-1）。
  子ファイル（keymaps / trigger_set / sequences）の命名は上位 keymap_set の名前を参照する方針だが、
  **子ファイルの命名・保存は Phase β の領域**（本フェーズでは keymap_set 自身の初期名のみ規定）。
- **起動時に必要ディレクトリ骨格を一括作成する**（`_ensure_split_config_dirs` 相当を起動時に呼ぶ）。
  config.json 本体の作成は従来どおり**初回保存時**のまま（起動時に空 config.json を書かない）。
- **`prompt_if_missing` は死にコードとして扱い、読み・正規化・書き込みを撤去する**（新規保存では出力しない）。
  ただし**既存 config.json に残る値は残置を許容**する（未知キー保持契約により自然消滅しないため、能動削除はしない）。
- **見つからないときは現状維持（無言で空起動）**。「見つからなければ選択ダイアログ」等の新機能は本フェーズでは作らない。
- **本フェーズは「複数の独立した keymap_set」を完全対応しない**（子ファイルの共有・上書きが残るため）。
  複数セットの子ファイル分離は Phase β + プリセット案2 で実現する（§9 制約）。
- 影響レイヤ: 原則 **presentation**（KeymapSetIo / ConfigPaths / StartupIo / App 起動時のディレクトリ作成）。
  `prompt_if_missing` 撤去に伴い application（`config_service` の startup 正規化行）に軽微な変更が入りうる。スキーマは後方互換を維持。

## §3 新規作成の挙動（点1）

`new_config`（`keymap_set_io.py:26-42`）:

- **変更点**: `:33` の `self._app.keymap_set_path = self._app.paths.preferred_keymap_set_path()` を
  **`self._app.keymap_set_path = ""`** にする。
- それ以外（`new_default_data` → `triggers=[]` → `normalize_runtime_data` → UI 同期 → インデックス初期化 →
  `set_dirty(True)` → フラッシュ「新規作成しました（未保存）。」）は**変更しない**。

結果: 新規作成直後は「ファイルなし・未保存」。この状態で「保存」を押すと §4 により別名保存になる。

## §4 保存の経路（点1・空パス → 別名保存）

`save_keymap_set`（`keymap_set_io.py:44-49`）:

- **変更点**: 先頭で `keymap_set_path` が空なら `save_as(...)` へ委譲する。
  ```python
  def save_keymap_set(self, *, show_success_dialog: bool = True) -> bool:
      if not self._app.keymap_set_path:
          return self.save_as(show_success_dialog=show_success_dialog)
      return self.save_keymap_set_to(self._app.keymap_set_path, flash_message="保存しました。",
                                     show_success_dialog=show_success_dialog)
  ```
- `confirm_save_if_dirty`（`:9-24`）は既に `if self._app.keymap_set_path: save_keymap_set() else save_as()`
  と分岐しており、空パス時に save_as へ回る挙動は現状で正しい。§4 の変更は `save_keymap_set` 内で完結させ、
  二重に save_as へ回らないようにする（`confirm_save_if_dirty` の空パス分岐はそのまま save_as を直接呼ぶため整合）。
- `save_keymap_set_to`（`:68-92`）自体のロジック（正規化・分割保存・成功/失敗ダイアログ）は**変更しない**。

## §5 デフォルト保存先のディレクトリ化 + Import + 起動時ディレクトリ作成（点2・訂正 + 指摘①④）

**方針**: 「既定＝ディレクトリ `config/user/keymap_sets/`」を単一の真実にし、固定 `default.json` を
**自動保存ターゲット・自動フォールバックから外す**。

- **起動時ディレクトリ作成（指摘④）**: App 起動時（`app.py` 初期化の `os.makedirs(self.user_root)` 付近）で
  `_ensure_split_config_dirs` 相当を呼び、`config/user/{keymap_sets,keymaps,trigger_sets,hotkey_presets,sequences}` を
  作成する。これにより初回 Save As の `initialdir`（`config/user/keymap_sets/`）が常に有効になる。
  **config.json は起動時に書かない**（初回保存時に作成）。
- **別名保存ダイアログ**（`:51-66`）: `initialdir` は現状 `suggest_keymap_set_dialog_dir()` 由来で
  `preferred_keymap_sets_dir()`（=`config/user/keymap_sets/`）へフォールバックする（`config_paths.py:82-92`）。
  起動時作成でこのディレクトリが存在するため config 直下へ逃げなくなる。`initialfile` は固定 `default.json` を
  強制せず、**`keymap_set.json`（一般名・ユーザー確定 §7-1）** を提示する。
- **Import（指摘①）**: `import_config`（`:137-138`）の `keymap_set_path = preferred_keymap_set_path()` を廃し、
  **Import 成功時は `keymap_set_path = ""`（無条件）** にする。開始パスが空/非空どちらでも次の保存が別名保存になる。
- **空起動時の path**: `load_startup_and_config`（`startup_io.py:18` / `:34` 後）で空起動する場合の
  `keymap_set_path` を **`""`** にする（`default.json` を差したまま残さない）。stored path が在って読めた場合は
  従来どおりそのパスを保持する。
- **フォールバックの後始末**: `save_keymap_set_to` に空パスが渡る経路は §4 で塞がれる。
  `normalize_keymap_set_save_path("")` が `default.json` を返す挙動は保存ターゲットとしては到達しなくなる
  （この関数自体の変更/据え置きは実装時に最小差分で判断。据え置きでも §4 により無言上書きは発生しない）。
  `preferred_keymap_set_path()` は suggest 系の内部補助としては残してよいが、**「保存先の既定値」としては使わない**。
  実装時、`default.json` を返す用途が保存ターゲットに漏れていないか grep で確認する。

## §6 `prompt_if_missing` の撤去（死にフラグ・残置許容）

- **除去対象（新規出力を止める）**:
  - `config_service.py:545` の `payload["prompt_if_missing"] = bool(...)` 正規化行。
  - `startup_settings.py:17` の型ガード行。
  - `startup_io.py:38-42` の `write_startup` base 既定から `"prompt_if_missing": True` を除去。
  - `keymap_set_io.py:202` の `set_startup_keymap_set` が書く辞書から `"prompt_if_missing": True` を除去。
  - → これらにより、**新規に作成される config.json には `prompt_if_missing` が含まれない**。
- **既存データ（残置許容・指摘③）**: 既存 config.json の `prompt_if_missing` は未知キー保持契約により
  次回保存でも再出力されうるが、**能動削除はしない**（`pop` しない）。実害のない死にキーとして残置を許容する。
  → 受入条件は「**新規作成される** config.json に含まれない」で判定する（§8-5）。
- **後方互換**: 読込側は未知キーを保持・無視する既存契約（`startup_settings.load_startup_settings`）に従い、
  古い config.json でも壊れない。他キー（`keymap_set_path` / `ui_font_delta_pt` / `last_used_directory`）は不変。
- **テスト影響**: startup 系の特性テスト（`tests_ui/test_startup_font_characterization.py` 等）で
  config.json のキー集合を固定している箇所は、**新規保存時に `prompt_if_missing` を含まない**期待値へ更新する。

## §7 確認事項（すべて確定済）

1. ~~別名保存ダイアログの初期ファイル名~~ → **確定（2026-07-27）: `keymap_set.json`（一般名）**。§2・§5 へ反映済。

## §8 受け入れ条件（ドラフト）

| # | 条件 | 対応 § |
|---|---|---|
| 1 | 新規作成直後は `keymap_set_path` が空で、「保存」を押すと別名保存ダイアログが出る（`default.json` に無言上書きしない） | §3・§4 |
| 2 | 起動時に `config/user/keymap_sets/` 等の骨格が作成され、空 config からの初回 Save As の初期ディレクトリが `config/user/keymap_sets/` になる（config 直下へ逃げない） | §5 |
| 3 | Import 成功後は `keymap_set_path` が空（開始パスが空/非空いずれでも）で、保存は別名保存になる | §5 |
| 4 | 起動時に stored keymap_set が見つからない場合、無言で空起動し、`keymap_set_path` は空である | §5 |
| 5 | `prompt_if_missing` の読み書き・正規化がコードから除去され、**新規作成される** `config/config.json` に当該キーが含まれない | §6 |
| 6 | 既存の `prompt_if_missing` 付き `config/config.json` でも起動・保存が正常（後方互換・残置許容） | §6 |
| 7 | 既存の保存済み keymap_set の読込・上書き保存・別名保存が従来どおり動作（新規/空パス/Import 以外の経路は回帰なし） | §4 |
| 8 | `tests` / `tests_ui` / smoke が更新後の期待値で pass。挙動変更点は特性テストで固定 | §3〜§6 |

- **安全網**: 本フェーズは挙動変更のため、変更する経路（new_config / save の空パス分岐 / import 無条件クリア /
  起動時ディレクトリ作成 / 空起動 path / prompt_if_missing 新規出力停止）を**特性テストで新挙動として固定**する。
  変更しない経路（既存パスへの保存・読込）は回帰しないことをテストで担保する（`tests_ui` の monkeypatch 手法を踏襲）。

## §9 スコープ外・制約（本フェーズでやらない）

- **【制約・重要】複数の独立した keymap_set の完全対応はしない**。config_root 内へ複数セットを保存すると
  子ファイル（trigger_set / sequences / hotkey_presets）を**共有・上書き**する現挙動が残る（`config_service.py:468-476`）。
  本フェーズは「新規=ファイルなし / 別名保存分岐 / 既定ディレクトリ化 / prompt 撤去」までで、
  **子ファイルのセット別分離は Phase β（暫定 05）+ プリセット案2（暫定 07）で実現する**。
- **子ファイル保存の確認ダイアログ・参照元記録・共有可視化** → Phase β（暫定 05 予定）。
- **停止/トグルキーの config.json 既定化** → Phase γ（暫定 06 予定）。
- **プリセットの config.json グローバル化** → 独立フェーズ（暫定 07 予定・案2）。
- **「見つからなければ選択ダイアログ」等、起動時のファイル選択 UX の新設**（無言空起動を維持）。
- **trigger_set の source_path 不整合**（[idea_05](../backlog/idea_05_trigger_set_source_path_inconsistency.md)）→ Phase β で扱う。
- `config_service` の分割保存ロジック本体（`save_runtime_data` の子ファイル書き出し）→ Phase β。

## §10 正本反映（フェーズ末昇格・予定）

| 対象 | 内容 |
|---|---|
| 正本 `spec_detail/` | `data_schema.md` の startup（`config.json`）節に `prompt_if_missing` の記述があれば「撤去（新規出力停止・既存残置許容）」を反映。新規作成/保存先の挙動が spec_detail に規定されていれば追従更新。昇格タスクで grep して確定 |
| `codebase_map.md` | KeymapSetIo / StartupIo / App 起動時処理の責務記述に「新規=空パス / 保存の空パス→別名分岐 / Import 後空 / 既定はディレクトリ / 起動時ディレクトリ骨格作成」を反映（必要時） |
| 実装 | `keymap_set_io.py`（new_config / save_keymap_set / import_config）/ `startup_io.py`（空起動時の path / write_startup base）/ `config_paths.py`（default.json 用途の整理）/ `app.py`（起動時ディレクトリ作成）/ `config_service.py`・`startup_settings.py`（prompt_if_missing 正規化除去） |
| テスト | `tests_ui/`（新挙動の特性テスト追加 + startup 系の期待値更新）|
| 別実装同期 | なし |

## 関連

- 保存系リデザイン全体討議: ユーザー要望（2026-07-26〜27）。後続 Phase β/γ/プリセットへ分割。
- 関連 idea: [idea_05](../backlog/idea_05_trigger_set_source_path_inconsistency.md)（Phase β で内包）/
  [idea_06](../backlog/idea_06_individual_json_io_unification.md)（Phase β で達成見込み）。
- 敵対的レビュー: codex-adversarial-reviewer（2026-07-27・v0.1 対象・needs-attention）。指摘 ①②③④ を v0.2 で反映。
- 正本: `spec_detail/data_schema.md`（JSON 後方互換・既存キー削除禁止）/ `instructions/common/codebase_map.md`（コントローラ責務）。
- 参照ルール: `.claude/rules/spec_change_workflow.md`（挙動変更は設計先行）。
