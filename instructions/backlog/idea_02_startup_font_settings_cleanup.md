# idea_02_startup_font_settings_cleanup.md

## 概要

App に残る**起動設定読込とフォントサイズ設定の 3 メソッド**
（`_load_startup_settings` / `_coerce_font_delta` / `set_ui_font_delta`、計約 44 行）を整理し、
**責務混在**と **controller → App private への逆参照**を解消する。
**3 件は呼び出し関係と制約（初期化順序）を共有するため、個別ではなく 1 クラスタとして扱う**。

## 起票経緯（2026-07-17）

計画04（[04_widget_split_plan.md](../modified_proposal/04_widget_split_plan.md)）W7「app.py 残留メソッドの分類」で、
「どの責務分類にも属さない残留ロジック」として列挙された項目。計画04 の範囲外として**保留**
（判断記録は `.claude_data/state/decisions.md`「【W7】app.py 行数の目安未達」）。

なお当初「`_coerce_font_delta` は純関数で簡単なので先に単独で切り出す」案があったが、
**落とし先が本クラスタの設計判断（`theme.py` か、新設するかもしれないフォント設定担当か）で初めて決まる**ため、
先行して移すと二度移動になると判断し、本 idea に統合した。

## 現状

- **`App._load_startup_settings`**（`keyseq/presentation/app.py:374-390`, 約17行）
  - startup.json 読込（`config_service.load_startup`）+ 失敗時 `messagebox.showwarning` + 正規化
    （`ui_font_delta_pt` / `prompt_if_missing`）
  - `app.py:56` の `__init__` 中に呼ばれる
- **`App._coerce_font_delta`**（`app.py:355-364`, 約10行）
  - int 化 + `-3〜+3` クランプ + 失敗時 0 を返す**純関数**
  - 呼び出し元 4 箇所: `app.py:57` / `app.py:226` / `app.py:388` /
    **`keyseq/presentation/controllers/config_io_controller.py:278`
    （`self._app._coerce_font_delta(...)` = controller から App private メソッドへの逆参照）**
- **`App.set_ui_font_delta`**（`app.py:225-241`, 約17行）
  - `keyseq/presentation/views/menu_bar.py:44` の「フォントサイズ」メニューから呼ばれる
  - クランプ → 同値なら早期 return → `_ui_font_delta_pt` 更新 → `ui_vars.ui_font_delta_var` 更新 →
    `apply_global_theme` → `config_io.write_startup`（永続化）→ メニュー再構築 → フラッシュ通知
    と **6 つの関心事が混在**
- **関連する結合**: `keyseq/presentation/ui_vars.py:17` が `master._ui_font_delta_pt`
  （App の private 属性）を直接読んでいる

## 問題 / 制約

- **責務混在**: 設定 I/O・テーマ適用・永続化・UI 通知が 1 メソッドに同居
- **逆参照**: controller（ConfigIoController）が App の private メソッドを呼んでいる
- **⚠️ 初期化順序（最大の設計制約）**: `_load_startup_settings` は `app.py:56` で呼ばれるが、
  `self.config_io = ConfigIoController(self)` の生成は `app.py:125`。
  **単純に ConfigIoController へ移すと未生成のコントローラを呼ぶことになる**
- **UI 依存**: `messagebox` を含むため完全な非 presentation 化は不可
  → エラー通知はコールバック注入にするのが筋
- **⚠️ メニュー再構築の副作用**: `set_ui_font_delta` は `build_menu_bar` のみ呼び
  `bind_menu_shortcuts` は呼ばない（呼ぶと `add="+"` バインドが重複し挙動が変わる）。
  計画04 W2 の判断（`decisions.md`「【W2】`_bind_menu_shortcuts` を menu_bar.py へ移すか」参照）。
  **この呼び出し頻度差を壊さないこと**

## 提案（方向性・要設計）

検討メモであり確定仕様ではない。

- **`_coerce_font_delta` の落とし先を本フェーズで一度だけ決める**
  （`theme.py` / 新設のフォント設定担当 / `ConfigPaths` 等）。二度移動を避けるため先行移設はしない
- **`_load_startup_settings`** を ConfigIoController / ConfigPaths へ。
  初期化順序は「コントローラ生成順の入れ替え」or「`ConfigService` を直接使う」の設計判断が必要
- **`set_ui_font_delta`** の責務分離（フォント設定担当へ集約する案）
- **`ui_vars.py`** の `master._ui_font_delta_pt` 依存の解消（コンストラクタで値を受け取る等）

## 想定スコープ

- **含む**: 上記 3 メソッドの移設・責務分離 / 初期化順序の解決 /
  ConfigIoController からの App private 逆参照の解消 / ui_vars の App private 依存の解消
- **含まない**: フォントサイズの仕様変更（範囲 `-3〜+3`・既定 0）/
  startup.json のスキーマ変更（**後方互換必須**・`spec_detail/data_schema.md`）/
  メニュー構成・文言の変更
- **影響レイヤ**: presentation のみ（想定）
- **仕様変更の見込み**: なし（挙動不変）。ただし初期化順序の変更は起動フローに触れる
- **リスク**: 中（起動フロー + メニュー再構築の副作用）
