# idea_04_font_settings_controller.md

## 概要

フォント設定という 1 つの関心事が **App に散在**している（状態 `_ui_font_delta_pt` / 正規化 /
テーマ適用 / UI 変数反映 / 永続化の 5 箇所）。これを **`FontSettingsController` へ束ねる**案。

**現時点では着手しない（保留）**。対象が実質 int 1 個に収まっており、controller 新設のほうが
構造として重くなるため。**下記「着手トリガー」のいずれかが現実に発生した時点で着手を検討する**。
着手には **初期化順序設計を確定する暫定仕様が先に 1 本必要**（1 フェーズ規模）。

## 起票経緯（2026-07-23）

出所: phase [03_startup_font_settings_cleanup](../phase/03_startup_font_settings_cleanup/phase.md) の
暫定仕様 [02](../history/02_startup_font_settings_cleanup.md) §6「**案 B**」。

同フェーズでは案 B（本 idea）と案 A（最小抽出）を比較し、**案 A を採用**して 4 負債を解消した。
案 B は敵対的レビュー [medium] の指摘（初期化順序が未解決）を受けて見送りとなり、
「フォント設定項目の拡張が必要になった時点で独立した idea として起票する」と決定していた
（判断は [decisions_archive/03_startup_font_settings_cleanup.md](../../.claude_data/state/decisions_archive/03_startup_font_settings_cleanup.md)）。
本 idea はその**将来 idea 化**であり、着手の起票ではない。

ユーザー方針（2026-07-23）: 前提条件を明記した上で backlog へ記録し、状態は**保留**とする。
`instructions/phase/current.md`「次フェーズ候補」節はフェーズごとに書き換わるため、
候補としての可視性を backlog INDEX 側へ移す目的も含む。

## 現状

phase 03 完了時点（案 A 適用済）の配線。関連は `keyseq/presentation/app.py`。

| 行 | 内容 |
|---|---|
| `app.py:58` | `load_startup_settings(...)` で起動設定を読む（`config_service` 直依存） |
| `app.py:66` | `coerce_font_delta(...)` → `self._ui_font_delta_pt`（**状態の所有は App**） |
| `app.py:67` | `apply_global_theme(self, font_delta_pt=...)`（テーマ早期適用） |
| `app.py:69` | `UiVars(self, ui_font_delta_pt=...)`（UI 変数へ引数で渡す） |
| `app.py:135` | `ConfigIoController(self)` 生成（**永続化が使えるのはここから**） |
| `app.py:235-243` | `_apply_font_delta()`: 正規化 → 状態更新 → `ui_vars` 反映 → テーマ適用 → `config_io.write_startup` |
| `app.py:246-` | `set_ui_font_delta()`（`_apply_font_delta` の呼び出し口） |

- 正規化は `keyseq/presentation/theme.py` の純関数 `coerce_font_delta`（phase 03 で移設・唯一の正規化点）。
- 起動時読込は `keyseq/presentation/startup_settings.py`（phase 03 で新設）。
- phase 03 の 4 負債（責務混在 / controller → App private 逆参照 / 初期化順序制約 / ui_vars 直読み）は
  **すべて解消済**。本 idea は「壊れているものの修復」ではなく「増える時に備えた所有者の設置」である。
- 正本: 担当層の割り当ては `instructions/common/codebase_map.md` が正
  （`spec_detail/` にフォント/起動設定の担当層記述はない。phase 03 task_05 で調査済）。

### 構造上の緊張（着手時に解く必要があるもの）

フォント設定は**生存期間が 2 つに割れている**。読込は `:58`（`config_io` 未生成のため
`config_service` 直依存）、書込は `:243`（`config_io` 経由）で、その `config_io` の生成は `:135`。
初期 delta が必要な `:66` より **69 行後**である。

## 提案（方向性・要設計）

`keyseq/presentation/controllers/font_settings_controller.py` を新設し、`_ui_font_delta_pt` の
所有と coerce / apply / persist を移す。ただし以下は**すべて未確定**であり、
着手時に暫定仕様として確定してから実装する（`.claude/rules/spec_change_workflow.md`）。

- **生成順序** — controller をいつ生成するか（`config_io` より前か後か）
- **初期 delta の単一所有者** — 起動時の値を誰が最初に持つか（二重所有を作らない）
- **注入時点** — `config_io` を後から注入する二段階初期化を許すか、別の解にするか
- **保存経路** — `config_io.write_startup` を controller から呼ぶか、経路を変えるか
- **保存失敗時の状態** — 現状は `write_startup` 失敗時もメモリ側 delta は更新済（表示と JSON が乖離）。
  項目が増えた際にこの扱いをどう定義するか

この設計が未確定のまま実装すると、`:67` テーマ早期適用 / `:69` UiVars 生成 / `:135`
ConfigIoController 生成のいずれかの順序を壊しうる（＝ phase 03 で見送った理由そのもの）。

### 着手トリガー（いずれか 1 つでも現実に発生したら検討開始）

1. **フォント設定項目が 2 つ目以降を持つとき**（本命。フォントファミリ / ベースサイズ絶対指定 /
   ビュー別倍率 等）。App のフィールドと適用メソッドが項目数だけ増殖し、phase 03 で解消した
   「責務混在」が再発する
2. **フォント設定ダイアログを作るとき** — 複数値を OK / キャンセルで確定する UI は
   「確定前のプレビュー状態」と「確定済み状態」の 2 つを要し、状態の所有者が必要になる
3. **保存失敗の扱いを定義したくなったとき** — 上記「保存失敗時の状態」の乖離が無視できなくなった時
4. **フォント状態の参照者が増えたとき** — 状態が App のフィールドに残る限り、別 controller が
   読みたくなれば phase 03 で潰した逆参照が復活する（参照者が 3 つ目に達したら合図）
5. **フォント設定を UI 抜きでテストしたくなったとき** — 現状は tkinter の App 起動が必要
   （`tests_ui/`）。controller 化すれば `tests/` で純粋にテストできる

トリガー未成立のまま着手しないこと（`.claude/rules/anti_patterns.md`
「将来必要そうという理由で広く実装する」に該当するため）。

## 想定スコープ

- **含む**: `controllers/font_settings_controller.py`（新規）/ `app.py`（状態の所有移動・初期化順序）/
  `ui_vars.py`・`theme.py`・`config_io_controller.py` の呼び出し口調整 / 対応する `tests/`。
- **含まない**: フォント範囲（-3..+3）・既定値・UI 文言の変更 / `theme.coerce_font_delta` の
  ロジック変更 / `startup_settings.py` の契約変更（未知キー全保持・`on_read_error` 注入）。
- **影響レイヤ**: presentation のみ（domain / application には及ばない見込み）。
- **仕様変更**: 挙動不変を目標とするなら**なし**の見込み。ただし着手トリガー 1・2・3 由来で
  着手する場合は、その機能追加自体が仕様変更を伴う（その時点で判断）。
- **規模**: 初期化順序設計の暫定仕様 1 本 + 実装タスク数件 = **1 フェーズ規模**。単独タスクではない。
- **前提**: 着手前に上記「提案」5 項目を暫定仕様として確定すること（`/spec_draft`）。

## 関連

- 分離元: 暫定仕様 [02_startup_font_settings_cleanup](../history/02_startup_font_settings_cleanup.md) §6（v1.0 凍結済）
- 前提となった判断: [decisions_archive/03_startup_font_settings_cleanup.md](../../.claude_data/state/decisions_archive/03_startup_font_settings_cleanup.md)
- 起票元フェーズの起点 idea: [idea_02](idea_02_startup_font_settings_cleanup.md)（完了・[INDEX_done.md](INDEX_done.md)）
