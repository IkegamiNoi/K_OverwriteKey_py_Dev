# 暫定仕様 06: 停止/トグルキーの config.json 既定化と個別指定（hook_keys_global_default）

> 状態: **未凍結・v0.2・主入力・ユーザー確定済（実装着手可）**。本書がこのフェーズ（保存系リデザインの
> Phase γ）の確定設計（フェーズ中は正本を直接改訂しない）。フェーズ末タスクで正本
> `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 版履歴: v0.1 起票（2026-07-27）→ **v0.2** codex-adversarial-reviewer 指摘 6 件を反映
> （①⑤ 物理削除→空文字クリア＋復活は保存前セッション限定 / ② 移行判定を「正規化後どちらか非空」に /
> ③ capture/clear を所有者切替可能に＋dirty 保全 / ④ キー解決を keymap_set 読込時に確定 /
> ⑥ 全体デフォルト更新 API を成否付きに）。ユーザー確定 2026-07-27。
> 起票元: ユーザー要望（2026-07-26〜27・保存系統の改善討議・点5）。Phase α/β とは比較的独立。

---

## §1 目的 / 背景

フック停止トリガー（`hook_stop_key`）と有効/無効トグルキー（`hook_toggle_key`）が **keymap_set に保存**される
現状では、**新規作成のたびに設定し直す必要があり面倒**（点5）。これらの**全体デフォルトを `config/config.json`
（起動エントリ）に持たせ**、フックラベルフレームのチェックで**このキーマップセットだけ個別指定**できるようにする。
本フェーズは**挙動変更・スキーマ追加を伴う**。

### 現状監査（2026-07-27）

- `hook_stop_key` / `hook_toggle_key` は runtime data のフィールドで、**keymap_set.json に保存**される
  （`domain/config.py:60-61` の既定 / `config_service._build_runtime_data_from_split:269-270` が keymap_set から読む /
  `config_service.py:595-596` の正規化）。**現状の保存器は空文字でも常に両キーを keymap_set へ書く**（→ §3 移行判定の根拠）。
- `config/config.json`（起動エントリ・`preferred_startup_path` = `_startup_entry_path`）は startup ペイロード
  （`keymap_set_path` / `ui_font_delta_pt` / `last_used_directory` 等）を持つが、**hook キーの全体デフォルトは持たない**。
- UI: フックラベルフレーム（`views/full_view/hook_frame.py` / `views/compact_view/hook_frame.py`）。値は `ui_vars`
  （`stop_key_var` / `toggle_key_var` 等）経由で App と共有。
- **キャプチャ**: `SingleKeyCaptureController`（`key_capture.py:90-135`）は capture/clear の双方で **`app.data` の hook キーを
  書き換え、keymap_set を dirty にする**（→ §4 の所有者切替の根拠）。
- **実行時のキー解決**: フック層（`hook_controller` / `input_router`）は **`app.data` の hook キーを直読み**する
  （`app.py:96-102`）。→ 全体デフォルトを届ける経路が必要（§3）。

## §2 確定事項（ユーザー 2026-07-27）

- **`config/config.json` に全体デフォルト `hook_stop_key` / `hook_toggle_key` を新設**（初期値=**空スタート**）。
- **keymap_set に「個別指定あり」を表す明示フラグ `hook_keys_individual`（bool）を追加**する。
  - 偽/未設定 → **全体デフォルト（config.json）を使用**。
  - 真 → keymap_set の個別値を使用。
- **移行規則（指摘②）**: 既存 keymap_set は、**正規化後に stop/toggle の少なくとも一方が非空**なら「個別指定 ON」、
  両方空なら「OFF（全体デフォルト使用）」として移行する。既存キーは**残す**（削除しない）。
- **UI**: フックラベルフレームに「このキーマップセットで個別指定する」チェックを追加。
- **OFF 時のキー編集は `config/config.json` の全体デフォルトを編集**する（keymap_set を触らない・§4）。ON 時は個別値を編集。
- **ON→OFF 切替時**: keymap_set に残る個別値は**内部的に保持**し、UI 表示・挙動は全体デフォルトへ切替。
  **再 ON で個別値が復活**（**保存前の同一セッション内に限る**・指摘⑤）。
- **OFF の状態で保存したとき、個別値を消す**。ただし `data_schema` の既存キー削除禁止に従い、
  **キー自体は残し値を空文字にクリア＋`hook_keys_individual=false`**（＝機能的に個別値は消える。保存後は再 ON しても空）。
- 影響レイヤ: presentation（hook_frame の UI・所有者切替 capture・config.json 全体デフォルト編集）+ application/domain
  （キー解決＝個別 or 全体）+ スキーマ（config.json に 2 キー追加・keymap_set にフラグ追加・後方互換）。

## §3 データモデルと解決順序（指摘④）

- **config/config.json（全体デフォルト）**: `hook_stop_key` / `hook_toggle_key`（正規化して保持・空可）。
- **keymap_set.json（個別）**: `hook_keys_individual`（bool）+ `hook_stop_key` / `hook_toggle_key`（個別値・既存キー）。
- **キー解決の単一点 = keymap_set 読込時に確定する**:
  - keymap_set を読み込む際、`hook_keys_individual` が偽/未設定なら **config.json の全体デフォルトを `app.data` の
    `hook_stop_key`/`hook_toggle_key` へ注入**する。真なら keymap_set の個別値をそのまま使う。
  - これにより **フック層（`input_router` / `app.data` 直読み）は変更不要**で、常に解決済みの値を見る。
  - OFF 編集時は config.json と **`app.data`（ランタイム）の両方を更新**して即反映する（フックが古いキーを使い続けない）。

## §4 UI とキャプチャの所有者切替（指摘③）

- **チェックボックス「このキーマップセットで個別指定する」** を追加（`hook_frame.py`）。状態は `hook_keys_individual` に対応。
- **capture/clear を所有者切替可能にする**:
  - **ON**: 従来どおり keymap_set 個別値（`app.data`）を編集し、keymap_set を dirty にする。
  - **OFF**: **config.json 全体デフォルトを編集**（即保存・§5 の成否付き）+ **`app.data`（ランタイム）を更新**（§3）+
    **keymap_set を dirty にしない**。dirty 非汚染は「**OFF 前の dirty 状態を記録し、OFF 操作後に復元する**」方式で担保する
    （ユーザー案）。keymap_set の個別値（`app.data` に残る保持分）は OFF 中は触らない（内部保持・再 ON で復活）。
- ON→OFF で表示を全体デフォルト値へ、OFF→ON で保持していた個別値を復元表示する。

## §5 保存時の挙動と全体デフォルト更新 API（指摘①⑤⑥）

- **keymap_set 保存時**:
  - `hook_keys_individual` が真 → 個別値を keymap_set.json に保存。
  - 偽 → **個別値を空文字にクリアし `hook_keys_individual=false` で保存**（キーは残す・§2）。これにより保存後は
    個別値が消え、再 ON しても空（**復活は保存前セッション内のみ**・§2）。
- **全体デフォルト更新 API（config.json への書き込み）は成否を返す**（指摘⑥）。現状 `write_startup` は例外を
  握り潰す（`startup_io.py:51-56`）ため、**成否付きの経路**を用意し、**保存成功時のみ** UI/ランタイムの表示を確定する。
  失敗時は旧値へロールバック、または未保存を明示して再試行可能にする。

## §6 確認事項

（v0.2 時点で未確定なし。§2〜§5 で確定。実装時の詳細〔domain 既定は空維持・全体デフォルトの初期値源にしない〕は
タスク定義で確認する。）

## §7 受け入れ条件（ドラフト）

| # | 条件 | 対応 § |
|---|---|---|
| 1 | config.json に全体デフォルト `hook_stop_key`/`hook_toggle_key` が持て、keymap_set 読込時に解決されフック動作に反映される | §3 |
| 2 | 新規作成した keymap_set は個別指定 OFF（全体デフォルトを使う）で、hook キーの再設定が不要 | §2・§3 |
| 3 | チェック ON で個別指定でき、その keymap_set 保存時に個別値が保存される | §4・§5 |
| 4 | チェック OFF 時のキー編集が config.json の全体デフォルトを更新（成否付きで即永続化）し、keymap_set を dirty にしない | §4・§5 |
| 5 | ON→OFF で表示が全体デフォルトへ、（保存前なら）再 ON で個別値が復活。OFF のまま保存すると個別値が空文字化＋フラグ false | §2・§4・§5 |
| 6 | 既存 keymap_set（正規化後どちらか非空・フラグ無し）は個別指定 ON として移行。両方空は OFF。既存キーは残る（後方互換） | §2 |
| 7 | 全体デフォルトの config.json 保存失敗時に UI/ランタイムを確定させず、旧値維持または未保存明示 | §5 |
| 8 | `tests` / `tests_ui` / smoke が更新後の期待値で pass。解決・移行・所有者切替・削除（空文字化）・保存失敗を特性テストで固定 | §3〜§5 |

- **安全網**: キー解決（個別/全体）・移行判定・OFF 保存での空文字化・OFF 時の config.json 編集（成否）・dirty 非汚染を
  特性テストで固定する。

## §8 スコープ外（本フェーズでやらない）

- **プリセットの config.json グローバル化** → 暫定 07（別フェーズ・同型パターン）。
- **子ファイル保存ダイアログ / 参照元記録** → Phase β（暫定 05）。
- **hook キー以外の設定（レイアウト等）の config.json 移動**（本フェーズは hook 2 キーに限定）。

## §9 正本反映（フェーズ末昇格・予定）

| 対象 | 内容 |
|---|---|
| 正本 `spec_detail/` | `data_schema.md` に config.json の `hook_stop_key`/`hook_toggle_key`（全体デフォルト）と keymap_set の `hook_keys_individual`（＋OFF 時の空文字化契約）を追記。解決順序・移行規則を規定 |
| `codebase_map.md` | hook キーの全体デフォルト/個別指定の責務（解決点＝keymap_set 読込時 / 所有者切替 capture / config.json 永続化経路）を反映 |
| 実装 | `config/config.json` スキーマ / `config_service.py`・`domain/config.py`（解決・正規化・移行）/ `hook_frame.py`（チェック UI）/ `key_capture.py`（所有者切替・dirty 保全）/ 全体デフォルト更新 API（成否付き・`startup_io` 拡張 or 新規）/ 解決点 |
| テスト | `tests/`（解決・移行）/ `tests_ui/`（UI チェック・OFF 編集の永続化と成否・OFF 保存の空文字化・dirty 非汚染）|
| 別実装同期 | なし |

## 関連

- 保存系リデザイン討議: ユーザー要望（2026-07-26〜27・点5）。
- 同型パターン: プリセットの config.json グローバル化（[暫定 07](07_hotkey_presets_global.md)）/
  [idea_08](../backlog/idea_08_per_keymap_set_preset_ownership.md)（個別プリセット・同じ「全体デフォルト+個別指定」構造）。
- 敵対的レビュー: codex-adversarial-reviewer（2026-07-27・v0.1 対象・needs-attention）。指摘 ①〜⑥ を v0.2 で反映。
- 正本: `spec_detail/data_schema.md`（JSON 後方互換・既存キー削除禁止）/ `spec_detail/key_input.md`（フック挙動）/ `codebase_map.md`。
- 参照ルール: `.claude/rules/spec_change_workflow.md`。
