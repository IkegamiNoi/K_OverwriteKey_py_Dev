# 暫定仕様 02: 起動設定 / フォント設定クラスタの整理（startup_font_settings_cleanup）

> 状態: **未凍結・v1.0・主入力・ユーザー確定済（2026-07-18）・実装着手可**。本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: [idea_02](../backlog/idea_02_startup_font_settings_cleanup.md)（計画04 W7 の残留ロジック分類から分離）。
> 実装フェーズ: **phase 03**（`/phase_start` で起票予定）。
> **番号対応: phase 03 / 暫定 02 / decisions `decisions_archive/03_<topic>.md`**（暫定仕様は phase と独立採番）。
> 前提: フェーズ 02_hotkey_validation 完了（2026-07-18）。**挙動不変のリファクタ**。
>
> 版歴:
> - v0.1 起票。
> - **v0.2: 起票時 reviewer レビュー（判定「完了可」・事実誤認 0 件・行番号1件の軽微誤記を訂正）と
>   codex-adversarial-reviewer の指摘 3 件を反映。①起動設定ローダに「未知キー全保持」契約を明記（§5・実害=
>   `keymap_set_path` 消失を実コードで裏取り）②警告発火の真理値表を固定（§5・欠損=無警告/例外=警告1回/非dict=無警告）
>   ③案 B を今フェーズ実装候補から外し案 A に限定（§6・案 B は初期化順序未解決のため将来 idea 化）。**
> - **v1.0: §7 確認事項 5 件をユーザー確定（2026-07-18）→ §2 へ反映。案 A 確定 / coerce→theme.py /
>   ローダ→startup_settings.py / エラー通知 on_read_error 注入 / 未知キー全保持契約。実装着手可。**

---

## §1 目的 / 背景

App（presentation）に残る**起動設定読込とフォントサイズ設定の 3 メソッド**
（`_coerce_font_delta` / `_load_startup_settings` / `set_ui_font_delta`）を整理し、次の 4 つの負債を解消する:

1. **責務混在** — `_load_startup_settings` / `set_ui_font_delta` に I/O・テーマ適用・永続化・UI 通知が同居。
2. **逆参照** — `ConfigIoController`（controller）が App private メソッド `_coerce_font_delta` を呼ぶ。
3. **初期化順序の制約** — `_load_startup_settings` は `config_io` 生成より前に実行される。
4. **ui_vars の App private 依存** — `ui_vars.py` が `master._ui_font_delta_pt`（App private 属性）を直読み。

**挙動不変**（フォント範囲 `-3〜+3`・既定 0・startup.json スキーマ・メニュー構成・エラー通知内容を変えない）。
**スキーマ変更なし**。**presentation 内での再編のみ**（application / domain / infrastructure は触らない）。

### 現状監査（2026-07-18・Explore 調査による裏取り。行番号は現コード実測）

#### 対象 3 メソッド（`keyseq/presentation/app.py`）
- **`_coerce_font_delta`**（`app.py:357-366`）— `int` 変換（失敗時 0）+ `-3..+3` クランプの**純関数**（`self` 未使用）。
- **`_load_startup_settings`**（`app.py:376-392`）— (a) `config_service.load_startup(self.startup_path)` /
  (b) 失敗時 `messagebox.showwarning`（UI 副作用）/ (c) dict 型ガード / (d) `ui_font_delta_pt` を
  `_coerce_font_delta` で正規化 / (e) `prompt_if_missing` を bool 正規化。呼び出しは **`app.py:57`** のみ（`__init__` 内）。
- **`set_ui_font_delta`**（`app.py:227-243`）— (a) coerce / (b) 現値との差分で早期 return / (c) `_ui_font_delta_pt` 更新 /
  (d) `ui_vars.ui_font_delta_var` 更新 / (e) `apply_global_theme` 再適用 / (f) `config_io.write_startup` 永続化 /
  (g) `build_menu_bar` 再構築 / (h) フラッシュ通知。呼び出しは **`views/menu_bar.py:44`**（フォントメニュー）のみ。

#### 呼び出しグラフ / 依存
- `_coerce_font_delta` の呼び出し元 4 箇所: `app.py:58`（初期値算出）/ `app.py:228`（`set_ui_font_delta`）/
  `app.py:390`（`_load_startup_settings`）/ **`controllers/config_io_controller.py:278`（`write_startup` 内・逆参照）**。
  **4 箇所すべて presentation**（App と ConfigIoController のみ。application/domain からは呼ばれない）。
- **初期化順序**: `app.py:43` `ConfigService` 生成 → `:49-55` `ConfigPaths` 生成 + `startup_path` 解決 →
  **`:57` `_load_startup_settings()`** → `:58-59` `_ui_font_delta_pt` 算出 + `apply_global_theme` →
  `:61` `UiVars(self)` 生成 → **`:127` `ConfigIoController(self)` 生成**。
  → `_load_startup_settings` は **`config_service` のみに依存**（`config_io` には非依存）。
  `config_service.load_startup` の所在は application 層 `keyseq/application/config_service.py:76-79`。
- **`_ui_font_delta_pt`（App private）**: 書き込み `app.py:58`（初期化）/ `app.py:232`（`set_ui_font_delta`）。
  読み取り `app.py:59`（theme 引数）/ `app.py:229`（差分判定）/ **`ui_vars.py:17`（外部読み取り）**。
- **`ui_vars.ui_font_delta_var`**: 生成 `ui_vars.py:17`（初期値に `master._ui_font_delta_pt` を使用）/
  更新 `.set` は `app.py:233` のみ / 参照 `menu_bar.py:43`（radiobutton の `variable=`）。

#### メニュー再構築の副作用（保持必須）
- `set_ui_font_delta` は **`build_menu_bar(self)` を呼ぶが `bind_menu_shortcuts` は呼ばない**（`app.py:237-238`）。
  両者は `keyseq/presentation/views/menu_bar.py`（`build_menu_bar` = 4-51 / `bind_menu_shortcuts` = 54-65）。
  `bind` を再登録すると `add="+"` バインドが重複し挙動が変わる（計画04 W2 の判断）。**この呼び出し頻度差を保つ**。

#### 落とし先候補の現状
- **`keyseq/presentation/theme.py`**（103 行）— フォントロジックが既に集約済み: `apply_global_theme`（78-102）/
  `_NAMED_FONTS`（6-15）/ `_apply_delta`（22-28）/ `_capture_base_sizes`（47-54）等。
  **`_coerce_font_delta`（クランプ）と startup 永続化はここに無い**。純関数の追加先として自然。
- **`config_paths.py`（ConfigPaths）** — パス解決のみ（startup I/O は持たない）。
- **`controllers/config_io_controller.py`（ConfigIoController）** — 起動設定の読込 `load_startup_and_config`（240-264）/
  書き込み **`write_startup`（266-）**（既定値マージ → `_app._coerce_font_delta` 正規化 → `config_service.save_startup`）。

## §2 確定事項（ユーザー確定済 2026-07-18）

### 前提（起票時に確定）

- **挙動不変**。フォント範囲 `-3〜+3`・既定 0・startup.json スキーマ（後方互換）・エラー通知の文言/回数/タイミング・
  メニュー構成/文言・`build_menu_bar` のみ再構築（`bind_menu_shortcuts` を呼ばない副作用）を変えない。
- **presentation 内での再編に限定**。application（`ConfigService`）/ domain / infrastructure は変更しない。
- 本件は**暫定仕様先行モード**で進める（探索的・複数ファイル・タスク 3 以上）。
- 着手順: 「後始末（01・完了）→ hotkey 検証（02・完了）→ **本件（idea_02）**」（ユーザー方針 2026-07-17）。

### 設計判断（v1.0・旧 §7 確認事項より確定 2026-07-18）

1. **coerce_font_delta の落とし先 = `theme.py` の純関数**（§4）。App private を廃し逆参照を解消。
2. **起動設定ローダ = 新規 `presentation/startup_settings.py`**（§5）。`config_service` 直依存で初期化順序を壊さない。
3. **フォント設定の責務分離 = 案 A（最小抽出）で確定**（§6）。`_ui_font_delta_pt` は App 保持。
   **案 B（FontSettingsController 新設）は今フェーズ見送り**（初期化順序が未解決・将来 idea 化）。
4. **エラー通知 = `on_read_error(exc)` のコールバック注入**（§5）。真理値表どおり分岐・回数・文言は不変。
5. **未知キー全保持の契約**（§5）。読込 dict の全キーを保持し既知2キーのみ正規化。受け入れ条件 §8-12 + fixture で固定。

## §3 設計方針（全体像）

4 つの負債それぞれに対する最小で一貫した解を置く。**キーとなる分岐は §7 確認事項**で決める。

| 負債 | 解の方向 | 対応 § |
|---|---|---|
| ② 逆参照（coerce） | `_coerce_font_delta` を `theme.py` のモジュール純関数 `coerce_font_delta` へ。App と ConfigIoController は import して使う（App private への依存が消える） | §4 |
| ① 責務混在（load） / ③ 初期化順序 | `_load_startup_settings` の I/O + 正規化を **`config_service` 直依存**の関数に切り出し、UI 通知は**コールバック注入**。`config_io` に依存しないので生成順序問題が起きない | §5 |
| ① 責務混在（set_ui_font_delta） / ④ ui_vars 依存 | フォント設定の状態と適用/永続化の扱いを整理し、`ui_vars` の App private 直読みを解消（**案 A: 最小抽出 / 案 B: FontSettingsController 新設**の 2 案。§7-3） | §6 |

## §4 coerce_font_delta → theme.py（負債②）

- **`keyseq/presentation/theme.py` にモジュール純関数を追加**:
  ```python
  def coerce_font_delta(value) -> int:
      """int 化し -3..+3 にクランプ。失敗時 0。フォント差分の唯一の正規化点。"""
  ```
  現行 `App._coerce_font_delta`（`app.py:357-366`）の本体を**ロジック不変で移設**（クランプ範囲・失敗時 0 を保つ）。
- **`App._coerce_font_delta` は削除**（純関数化により App のメソッドである必要がない。呼び出し元 4 箇所を差し替え）。
- 呼び出し元の差し替え: `app.py:58` / `:228` / `:390` は `theme.coerce_font_delta(...)` に。
  **`config_io_controller.py:278` は `self._app._coerce_font_delta(...)` → `theme.coerce_font_delta(...)` に**（逆参照が消える）。
- 依存方向: `theme.py`・`config_io_controller.py` とも presentation 内。範囲 `-3/+3` は theme が持つフォント知識に属す。

## §5 起動設定読込の切り出し（負債①・③）

- **新規 `keyseq/presentation/startup_settings.py`**（presentation・App 専用の薄いローダ）に関数を置く:
  ```python
  def load_startup_settings(config_service, startup_path, *, on_read_error) -> dict:
      """startup.json を読み、型ガードと正規化（font_delta / prompt_if_missing）を施した dict を返す。
      読込例外時は on_read_error(exc) を呼び既定 dict を返す。未知キーは全て保持する。"""
  ```
  - I/O は `config_service.load_startup(startup_path)`（**application を直接使う正しい向き**。`config_io` に依存しない）。
  - 正規化: `ui_font_delta_pt` は `theme.coerce_font_delta` / `prompt_if_missing` は bool 化（現行 §1 の (c)(d)(e) を不変移設）。
- **`App._load_startup_settings` は削除**し、`app.py:57` を
  `self._startup_settings = load_startup_settings(self.config_service, self.startup_path, on_read_error=...)` に。
- 初期化順序: `config_service`（`:43`）は `:57` 時点で生成済み → **順序問題なし**（`config_io` は不要）。

#### ⚠️ 未知キー全保持の契約（後方互換の要。敵対的レビュー [high] 反映）

現行 `_load_startup_settings`（`app.py:390-392`）は**読み込んだ dict をその場で更新して丸ごと返す**ため、
`keymap_set_path` / `last_used_directory` 等の**既知2キー以外を保持**する。返り値は `self._startup_settings` に入り、
- `ConfigIoController.load_startup_and_config`（`config_io_controller.py:245-246`）が `keymap_set_path` を読んで起動時の keymap セットを復元
- `ConfigIoController.write_startup`（`:272-274` の `base.update(current)`）が保存時に既存キーをマージ

に使われる。**新ローダが既知2キーだけの新 dict を返すと `keymap_set_path` が失われ、起動時に構成が読めない／
次回保存で不可逆に消える**（実コードで裏取り済み）。したがって新ローダの契約を次のとおり固定する:

- 入力 dict の**全キーを保持**し、`ui_font_delta_pt` と `prompt_if_missing` の**2キーのみ正規化して上書き**する
  （＝現行の in-place 更新と等価。新 dict を作るなら入力の全キーをコピーしてから2キーを上書き）。
- **受け入れ条件 §8-12 と §9 の fixture テストで、未知キー（`keymap_set_path` 等）が読込後も保持されることを検証する。**

#### エラー通知の真理値表（挙動不変の固定。敵対的レビュー [medium] 反映）

現行分岐を**1 件も変えない**。`messagebox` 依存を関数から外すため、**例外時のみ**コールバック
`on_read_error(exc)` を呼び、App 側が `lambda exc: messagebox.showwarning("startup.json 読込失敗", ...)` を渡す。

| ケース | `config_service.load_startup` | 警告 | 返り値 |
|---|---|---|---|
| ファイル欠損 | `{}` を返す（例外なし） | **なし**（静かに既定起動） | 既定2キーのみ（正規化後） |
| JSON 破損 / 読込例外 | 例外を送出 | **`on_read_error(exc)` を 1 回**（title「startup.json 読込失敗」/ body `f"startup.json の読込に失敗しました。\n{exc}\n\n既定設定で起動します。"`） | 既定2キーのみ |
| 有効だが非 dict | 非 dict を返す（例外なし） | **なし**（型ガードで既定化） | 既定2キーのみ |
| 正常 dict | dict を返す | なし | 入力の全キー保持 + 2キー正規化 |

- **警告は「読込例外」パスのみ**（欠損・非 dict では出さない＝現行どおり）。title / body は上表と 1 文字一致。
- 欠損・非 dict で既定化した dict には既知2キーのみが入る（現行と同じ。未知キーは元々存在しないため保持対象なし）。

## §6 フォント設定の責務分離（負債①・④）

`set_ui_font_delta`（8 関心事）と `_ui_font_delta_pt`（App private）・`ui_vars` の直読みを整理する。
**本フェーズは案 A（最小抽出）で確定する**（案 B は初期化順序が未解決のため今フェーズ実装候補から外す。下記）。
案 A は挙動不変（適用順序・早期 return・メニュー再構築の副作用を保つ）。

### 案 A（採用・最小抽出）— App 内で薄く分割 + ui_vars は値受け取り

- `App.set_ui_font_delta` を 2 メソッドに分ける（App 内に留める）:
  - `_apply_font_delta(delta) -> bool`: coerce（`theme.coerce_font_delta`）→ 差分なしなら `False` →
    `_ui_font_delta_pt` 更新 → `ui_vars.ui_font_delta_var.set` → `apply_global_theme` → `config_io.write_startup` → `True`。
  - `set_ui_font_delta(delta)`（メニューハンドラ）: `if self._apply_font_delta(delta): build_menu_bar + フラッシュ`。
    ＝「状態・適用・永続化」と「UI 反応（メニュー再構築 + 通知）」を分離。
- **`ui_vars` の App private 依存の解消**: `UiVars.__init__` が `ui_font_delta_pt: int` を**引数で受け取る**
  （`app.py:61` の `UiVars(self)` → `UiVars(self, ui_font_delta_pt=self._ui_font_delta_pt)`。`master._ui_font_delta_pt` 直読みを廃止）。
- `_ui_font_delta_pt` の所有は **App のまま**（初期化 `:58` / 読み `:59,:229` / 更新は `_apply_font_delta` に一本化）。
- 長所: 最小差分・初期化順序に触れない・リスク低。短所: フォント設定状態が App に残る（クラスタの完全な外出しではない）。

### 案 B（今フェーズ見送り）— FontSettingsController 新設は将来 idea 化

- 構想: `controllers/font_settings_controller.py` を新設し `_ui_font_delta_pt` の所有と coerce/apply/persist を移す。
- **今フェーズでは採らない**（敵対的レビュー [medium] 反映）。理由: controller は永続化に `config_io`（`:127` 生成）を
  要するが初期 delta は `:58` で必要、という**初期化順序の時間差を解く設計（生成順序・初期 delta の単一所有者・
  注入時点・保存経路・保存失敗時の状態）が未確定**。この状態で実装候補に残すと UiVars 生成・テーマ早期適用・
  ConfigIoController 生成のいずれかの順序を破綻させうるため、「挙動不変」を保証できない。
- フォント設定項目の拡張（複数設定の追加等）が現実に必要になった時点で、**独立した idea として初期化順序設計を
  詰めてから**着手する。本フェーズは案 A で 4 負債を解消し、構造の完全外出しは将来課題とする。

**採用: 案 A**。理由は「4 負債すべてを解消しつつ初期化順序に手を触れず最小差分」で、
`.claude/rules/anti_patterns.md`（過剰な共通化・大きすぎる差分の回避）と整合するため。

## §7 確認事項（すべてユーザー確定済 2026-07-18 → §2 設計判断へ反映）

1. coerce_font_delta の落とし先 → **`theme.py`**（§2-設計判断1）。
2. 起動設定ローダの配置 → **新規 `presentation/startup_settings.py`**（§2-設計判断2）。
3. フォント設定の責務分離 → **案 A（最小抽出）で確定・案 B 見送り**（§2-設計判断3）。
4. エラー通知 → **`on_read_error(exc)` コールバック注入**（§2-設計判断4）。
5. 未知キー全保持の契約 → **採用**（§2-設計判断5）。

未確定事項は残っていない（実装着手可）。

## §8 受け入れ条件（ドラフト）

| # | 条件 | 対応 § |
|---|---|---|
| 1 | `App._coerce_font_delta` が消え、`theme.coerce_font_delta` に一本化（`git grep "_coerce_font_delta"` が 0 件） | §4 |
| 2 | `config_io_controller.py` が App private を呼ばない（`git grep "_app._coerce_font_delta"` が 0 件） | §4 |
| 3 | `_load_startup_settings` の I/O + 正規化 + エラー通知が App から切り出され、App は薄い配線のみ | §5 |
| 4 | 起動設定ローダが `config_service` に直依存し `config_io`（`:127` 生成）に依存しない（初期化順序を壊さない） | §5 |
| 5 | `ui_vars.py` が `master._ui_font_delta_pt` を直読みしない（`git grep "_ui_font_delta_pt" -- keyseq/presentation/ui_vars.py` が 0 件） | §6 |
| 6 | `set_ui_font_delta` の「状態・適用・永続化」と「メニュー再構築 + フラッシュ」が分離されている | §6 |
| 7 | フォント変更時に `build_menu_bar` のみ呼ばれ `bind_menu_shortcuts` は呼ばれない（副作用の保持） | §1 |
| 8 | エラー通知が**真理値表（§5）どおり**: 欠損=無警告 / 例外=警告1回（title「startup.json 読込失敗」・body 1文字一致）/ 非dict=無警告。移設前後で分岐・回数・文言が不変 | §5 |
| 9 | startup.json のスキーマ・既定値・フォント範囲 `-3〜+3` が不変（後方互換） | §2 |
| 10 | 標準検証 4 項目が全緑（compile clean / tests / tests_ui / smoke。`.venv` python）+ 特性テスト追加分 pass | §9 |
| 11 | 実機目視: 起動（startup.json **正常/欠損/破損/非dict**）で、正常・欠損・非dict は警告なしで既定 or 保存値のフォント適用、破損のみ警告表示。メニューからフォント変更 → 即時反映・永続化・再起動後も保持 | §5,§6 |
| 12 | **未知キー保持**: `keymap_set_path` 等を含む startup.json を読み込んでも、`_startup_settings` が当該キーを保持し、フォント変更保存後も `keymap_set_path` が startup.json に残る（起動時に構成が復元できる）。fixture テストで検証（§9） | §5 |

## §9 安全網（テスト・予定）

- 現状 `_coerce_font_delta` / `_load_startup_settings` / `set_ui_font_delta` の単体テストは**要調査**（おそらく無し）。
- **移設前に特性テストで現行挙動を固定**（`/refactor_check`「項目 0: 安全網」の精神）:
  - `coerce_font_delta` の純関数テスト（範囲外/非数値/境界 `-3,+3`）。
  - 起動設定ローダの**真理値表（§5）テスト**: 欠損/JSON例外/非dict/正常dict の 4 ケースで、
    (a) 返り値の既知2キー正規化 (b) `on_read_error` の**呼出回数・引数**（例外時のみ1回）(c) title/body の 1 文字一致
    を、**fake config_service（欠損→`{}` / 例外送出 / 非dict / dict を返す差し替え）+ 記録用コールバック**で検証。
  - **未知キー保持テスト（§8-12）**: `keymap_set_path` 等を含む dict を返す fake で読み込み、返り値が当該キーを保持し、
    かつ `ui_font_delta_pt` / `prompt_if_missing` のみ正規化されることを確認（`tk.Tk` 不要）。
  - フォント変更の適用（差分なし早期 return・メニュー再構築が `build_menu_bar` のみで `bind_menu_shortcuts` を呼ばない）
    の確認は tests_ui。
- 移設後もこれらが**無変更で pass** することが挙動不変の証明。形式は既存に準拠（tests=unittest / tests_ui）。

## §10 スコープ外（本フェーズでやらない）

- フォントサイズの仕様変更（範囲・既定）/ startup.json スキーマ変更 / メニュー構成・文言の変更。
- application（`ConfigService`）/ domain / infrastructure の変更。
- [idea_03](../backlog/idea_03_action_hotkey_save_normalization.md)（アクション hotkey の保存時正規化）。
- `app.py` の行数削減それ自体（結果的に減るが目的にしない）。

## §11 正本反映（フェーズ末昇格・予定）

| 対象 | 内容 |
|---|---|
| 正本 `spec_detail/` | **要調査**: 起動設定/フォントの担当層を規定する節があるか。担当クラス割り当ては `architecture.md §3.5` により `codebase_map.md` が正のため、原則 spec_detail の更新は不要見込み（挙動不変） |
| `codebase_map.md` | App の責務から font/startup の実装を除き、`theme.coerce_font_delta` / `startup_settings.py` /（案 B なら FontSettingsController）を追記。`UiVars` の初期化引数変更を反映 |
| 実装 | `theme.py`（coerce 追加）/ `startup_settings.py`（新規）/ `app.py`（3 メソッド整理）/ `ui_vars.py`（引数化）/ `config_io_controller.py`（逆参照解消）/（案 B なら controller 新設） |
| テスト | `tests/`（coerce / startup ローダ）/ `tests_ui/`（フォント変更フロー特性テスト） |
| 別実装同期 | なし |

## 関連

- 起票元: [idea_02](../backlog/idea_02_startup_font_settings_cleanup.md)
- 前フェーズ: `02_hotkey_validation`（[decisions_archive/02_hotkey_validation.md](../../.claude_data/state/decisions_archive/02_hotkey_validation.md)）
- 計画04（完了）: [04_widget_split_plan.md](../modified_proposal/04_widget_split_plan.md)。本件は W7 の残留ロジック分類から分離。
- 参照した過去判断: `decisions.md`「【W2】`_bind_menu_shortcuts`…」（メニュー再構築の副作用）/「【W7】app.py 行数の目安未達」。
