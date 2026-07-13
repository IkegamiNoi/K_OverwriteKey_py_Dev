# phase.md

## フェーズ名

MVP Refine 修正フェーズ

---

## フェーズの目的

MVP 完了後に明らかになった操作体系・描画・保存の課題を解消し、キーボード主体で破綻なく使える MVP に引き上げる。

含まれる柱（独立カテゴリ）:

- **キー操作体系の刷新**: Tab→WASD、新モード入口キー、各モードからの Esc 復帰の統一
- **新モードの追加**: ビューモード（移動・ズーム・着地操作）/ グリッドモード（軸操作・間隔変更）
- **マウス操作の整理**: パン / ズームをモード横断で有効化、クリックはモード固有
- **無限グリッド描画**: 描画範囲と保存範囲の分離 / ビューポート連動描画 / 縮小時非表示
- **端での自動グリッド拡張**: 4 方向すべてでクイック作成 / カスタム作成 / ビューモード Enter 着地に対応
- **モード表示**: 現在モードが視認できる UI

`mvp_fix` フェーズ（task_01 / task_02 完了済）の後に位置する独立フェーズ。

---

## このフェーズで読むファイル

タスクごとに対象が異なる。まず `tasks/` 配下の対象タスク本文を読み、そこで指示された仕様書を順に読むこと。

### 共通

1. `common/app_overview.md`
2. `.claude/rules/` 配下のポリシー
3. `instructions/phase/00_common/task_check.md`（各タスク完了時の共通チェック）
4. 対象タスク本文（`tasks/task_NN_*.md`）

### 仕様書（正本）

- `common/spec_detail/key_input.md`（キー / モード / アクション）
- `common/spec_detail/features.md`（4.4 グリッド、4.6 クイック作成、4.7 カスタム作成、4.10 マウス、4.11 スクロール・パン・ズーム、4.12 ビューモード、4.13 グリッドモード）
- `common/spec_detail/viewport.md`（描画 / 保存分離、無限グリッド、縮小時非表示）

### 必要な場合のみ追加で読む

- 既存実装は対象タスクの「実装内容」セクションで指定されたファイルのみ
- 過去の判断: `.claude_data/state/decisions.md` の「2026-05-07 仕様変更: mvp_refine 仕様化」セクション

---

## このフェーズの前提

- MVP の全 20 タスクおよび `mvp_fix` の task_01（JSON 適合）/ task_02（ノード交点中心描画）完了済
- アプリは動作する状態にある
- 仕様書は本フェーズ着手時点で B-1 として更新済（`spec_detail/` の各ファイル）
- 修正は仕様適合に必要な範囲のみ
- 各タスクで「対象とする層」を明示し、その範囲を超えた変更は行わない

---

## このフェーズで優先すること

- 仕様書を正本として扱い、実装側を直す
- 既存の動作を壊さない（マウス操作 / 既存ノード位置 / JSON フォーマット は維持）
- domain / application / infrastructure 層に PySide6 依存を持ち込まない
- 最小差分で動作を壊さない

---

## このフェーズで守ること

- 仕様書を独断で書き換えない（必要時は `.claude/rules/spec_change_workflow.md` に従う）
- 実装に合わせて仕様書を緩めない
- 仕様適合に直接関係のないリファクタを混ぜない
- 各タスクの「配置層」「スコープ外」を厳守する
- 既存モード名（`Mode.NORMAL` 等）は rename しない。新モードのみ追加する

---

## このフェーズで禁止すること

- タスク外の機能追加
- 仕様書の独断修正
- viewport / モード遷移の保存対象拡張（MVP では保存しない）
- 既存モード名の rename
- 通常モードのマウスパン / ズーム / クリック選択挙動の変更
- JSON フォーマットの変更（layout.json の構造）

---

## タスク一覧

| # | ファイル | 概要 | 主な配置層 | 状態 |
|---|---|---|---|---|
| 01 | [task_01_audit_current_state.md](tasks/task_01_audit_current_state.md) | 現状把握（モード・キー・フォーカス・描画 / 保存）と差分整理 | 調査のみ | 未着手 |
| 02 | [task_02_keymap_to_wasd.md](tasks/task_02_keymap_to_wasd.md) | 通常モードのキーマップを Tab→WASD へ刷新、V / G モード入口キー追加 | presentation | 未着手 |
| 03 | [task_03_mode_transition_polish.md](tasks/task_03_mode_transition_polish.md) | Esc 復帰の通常モード一元化、編集モードのダイアログ外クリックでキャンセル | presentation | 未着手 |
| 04 | [task_04_view_mode.md](tasks/task_04_view_mode.md) | ビューモード追加（WASD / Shift+WASD / R / F / Space / Enter / Esc） | presentation + application（着地作成） | 未着手 |
| 05 | [task_05_grid_mode.md](tasks/task_05_grid_mode.md) | グリッドモード追加（軸 / スコープ / 選択ライン / 間隔変更） | presentation + application（軸操作） | 未着手 |
| 06 | [task_06_render_save_separation.md](tasks/task_06_render_save_separation.md) | グリッド描画範囲と保存範囲の分離 | presentation | 未着手 |
| 07 | [task_07_infinite_grid_render.md](tasks/task_07_infinite_grid_render.md) | 無限グリッド描画（ビューポート連動） | presentation | 未着手 |
| 08 | [task_08_grid_hide_at_zoom.md](tasks/task_08_grid_hide_at_zoom.md) | 縮小時のグリッド線非表示（閾値判定） | presentation | 未着手 |
| 09 | [task_09_auto_extend_grid.md](tasks/task_09_auto_extend_grid.md) | 端での自動グリッド拡張（4 方向、3 経路） | application + domain | 未着手 |
| 10 | [task_10_mode_indicator.md](tasks/task_10_mode_indicator.md) | 現在モードの視認 UI | presentation | 未着手 |
| 11 | [task_11_integration_check.md](tasks/task_11_integration_check.md) | 全モード遷移・受け入れ条件の総合確認 | 検証のみ | 未着手 |

### 依存関係と推奨順序

```
task_01 (audit, 全前提)
  └── task_02 (WASD)
        └── task_03 (mode transitions)
              ├── task_04 (view mode)        ─┐
              └── task_05 (grid mode)         │
                                              │
task_06 (render/save 分離)                    │
  └── task_07 (infinite render)               │
        └── task_09 (auto-extend) ───────────┘
              ├── 依存: task_04 (view 着地)
              └── 依存: task_07 (描画範囲)

task_08 (zoom hide)  ←  task_06 完了後で独立に進められる

task_10 (mode indicator)  ←  task_04 / task_05 完了後

task_11 (integration check)  ←  最後
```

並列可能ペア:
- task_04 と task_05（互いに独立）
- task_07 と task_08（task_06 完了後）

### 受け入れ条件（フェーズ全体）

- 仕様書（`key_input.md` / `features.md` / `viewport.md`）の該当項目すべてに適合
- 各タスクの完了条件を満たす
- 各タスクが `instructions/phase/00_common/task_check.md` の共通チェックを通過している
- 通常モードのマウス操作が無変更で動作
- 既存の保存ファイル（layout.json）が読み込める後方互換が保たれる
- サブエージェントレビューが各タスクで完了し、判定が `decisions.md` に記録されている

---

## 関連

- 出典の仕様書: `instructions/common/spec_detail/`
- 共通タスクチェック: `instructions/phase/00_common/task_check.md`
- 過去の判断履歴: `.claude_data/state/decisions.md`
- 仕様変更ワークフロー: `.claude/rules/spec_change_workflow.md`
- バックログ: `instructions/backlog/INDEX.md`（idea_01 / idea_02 は本フェーズで関連あれば取り込み判断）
