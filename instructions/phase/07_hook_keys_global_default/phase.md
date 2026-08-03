# phase.md

## フェーズ名

停止/トグルキーの全体デフォルト化（hook_keys_global_default）＝ 保存系リデザイン **Phase γ**

## フェーズの目的

フック停止トリガー（`hook_stop_key`）と有効/無効トグルキー（`hook_toggle_key`）の**全体デフォルトを
`config/config.json`（起動エントリ）へ持たせ**、keymap_set 側のチェックで**このキーマップセットだけ
個別指定**できるようにする。新規作成のたびにキーを設定し直す手間をなくす。

**アーキテクチャ上の方針**:

- **キー解決の単一点は「keymap_set 読込時」**（application 層）。ここで `app.data` の
  `hook_stop_key` / `hook_toggle_key` を解決済みの値に確定させるため、
  **フック層（`input_router` / `app.data` 直読み）は変更しない**。
- **対象レイヤ**: presentation（チェック UI / 所有者切替 capture / config.json 編集経路）+
  application・domain（解決・正規化・移行判定）。
- **スキーマ変更あり（後方互換必須）**: config.json に 2 キー追加 / keymap_set に
  `hook_keys_individual` 追加。**既存キーは削除しない**（`spec_detail/data_schema.md` の既存キー削除禁止）。

- 起票元: ユーザー要望（2026-07-26〜27・保存系統の改善討議・点5）。
- 主入力（暫定仕様）: [06_hook_keys_global_default.md](../../history/06_hook_keys_global_default.md)
  （**v0.2・ユーザー確定済 2026-07-27**・敵対的レビュー指摘 ①〜⑥ 反映済）
- モード: **暫定仕様先行モード**。番号対応: **phase 07 / 暫定 06 / decisions_archive 07**。
  （暫定仕様はフェーズとは独立採番のためズレる。計画05 はフェーズ番号を消費していない）

## 確定（ユーザー 2026-07-27・暫定仕様 06 §2〜§5）

- `config/config.json` に全体デフォルト `hook_stop_key` / `hook_toggle_key` を新設（**初期値 = 空**）。
- keymap_set に明示フラグ **`hook_keys_individual`（bool）**。偽/未設定 → 全体デフォルト / 真 → 個別値。
- **移行規則**: 既存 keymap_set は**正規化後に stop/toggle の少なくとも一方が非空**なら個別指定 ON、
  両方空なら OFF。**既存キーは残す**。
- **OFF 時のキー編集は config.json の全体デフォルトを編集**し、keymap_set を dirty にしない
  （OFF 前の dirty 状態を記録して操作後に復元する方式）。ON 時は個別値を編集。
- **ON→OFF 切替**: keymap_set の個別値は内部保持し、表示・挙動は全体デフォルトへ。
  **再 ON で復活するのは保存前の同一セッション内のみ**。
- **OFF のまま保存**: 個別値を**空文字にクリア**し `hook_keys_individual=false` で保存
  （キー自体は残す）。保存後は再 ON しても空。
- **全体デフォルト更新 API は成否を返す**。**保存成功時のみ** UI / ランタイムの表示を確定する
  （現状 `write_startup` は例外を握り潰す）。

## スコープ

### 含む

- config.json / keymap_set のスキーマ追加と後方互換（移行判定を含む）
- キー解決（keymap_set 読込時の全体デフォルト注入）と保存時の空文字化
- 成否を返す全体デフォルト更新経路（config.json への書き込み）
- フックラベルフレームの「このキーマップセットで個別指定する」チェック UI（full / compact 両方）
- capture / clear の所有者切替（ON=keymap_set 個別値 / OFF=全体デフォルト）と dirty 非汚染
- 受入条件 1〜8 を固定する特性テスト（`tests` / `tests_ui`）

### 含まない（後送り）

- **プリセットの config.json グローバル化** → phase 08（[暫定 07](../../history/07_hotkey_presets_global.md)）。
  同型パターンだが本フェーズでは共通化しない（2 例目が出てから判断する）
- hook キー以外の設定（レイアウト等）の config.json 移動。**本フェーズは hook 2 キーに限定**
- 子ファイル保存ダイアログ / 参照元記録（Phase β = phase 06 で完了済み）
- [idea_08](../../backlog/idea_08_per_keymap_set_preset_ownership.md)（keymap_set 個別プリセット）

## このフェーズで読むファイル

**計画05（2026-08-03）で `config_service` はパッケージへ分割済み**。暫定仕様 06 の「現状監査」に
書かれた行番号（`config_service.py:269-270` / `:595-596` 等）は**分割前のもので現在は無効**。
現在の所在は下記が正。

1. `instructions/history/06_hook_keys_global_default.md` — **主入力**（確定設計）
2. `instructions/common/spec_detail/data_schema.md` — JSON 後方互換・既存キー削除禁止（正本）
3. `instructions/common/spec_detail/key_input.md` — フック挙動（正本）
4. `keyseq/domain/config.py` — 既定値（`:60-61`）と正規化（`:154-155`）。移行判定の置き場候補
5. `keyseq/application/config_service/split_loading.py` — **keymap_set からの読込**（`:30-31`）。
   **キー解決点の第一候補**
6. `keyseq/application/config_service/split_payloads.py` — **keymap_set への保存**（`:331-332`）。
   OFF 時の空文字化の実装点
7. `keyseq/application/config_service/__init__.py` — `load_startup` / `save_startup` / 公開面
8. `keyseq/presentation/controllers/config_io/startup_io.py` — `load_startup_and_config`（読込の入口）と
   **`write_startup`（例外を握り潰す = §5 の改修対象）**
9. `keyseq/presentation/controllers/key_capture.py` — `SingleKeyCaptureController`（所有者切替の対象）
10. `keyseq/presentation/views/full_view/hook_frame.py` / `views/compact_view/hook_frame.py` — チェック UI の追加先
11. `keyseq/presentation/ui_vars.py`（`stop_key_var` / `toggle_key_var`）と
    `keyseq/presentation/app.py`（`:96-102` フック層への供給 / `:119-135` capture 登録 / `:396-397` UI 反映）
12. `instructions/common/codebase_map.md` — 責務の正本（正本反映タスクで更新）

**読まない**: `tests/` 配下の広読み（対象テストのみ）/ Phase β の子ファイル保存まわり
（`child_save_*` は本フェーズと無関係）/ `instructions/history/archive/`

## タスク

| # | タスク | 概要 |
|---|---|---|
| task_01 | スキーマと移行判定 | `domain/config.py` に `hook_keys_individual` の既定・正規化・**移行判定**（正規化後どちらか非空 → ON）を追加。後方互換 |
| task_02 | キー解決点 | keymap_set 読込時に、OFF なら config.json の全体デフォルトを `app.data` へ注入する（`split_loading` + 読込経路）。フック層は変更しない |
| task_03 | 保存時の挙動 | OFF 保存で個別値を空文字クリア + `hook_keys_individual=false`（`split_payloads`）。ON はそのまま保存 |
| task_04 | 全体デフォルト更新 API | config.json への書き込みを**成否付き**で行う経路を用意する（`write_startup` の握り潰し回避）。成功時のみ確定 |
| task_05 | チェック UI | full / compact の `hook_frame` に「このキーマップセットで個別指定する」チェックを追加し、`ui_vars` / App と同期 |
| task_06 | 所有者切替 capture | `key_capture` の capture / clear を ON=個別値 / OFF=全体デフォルト へ切替。**OFF は dirty を汚さない**（前 dirty の記録と復元）+ ON⇄OFF の表示切替と個別値の内部保持 |
| task_07 | 統合確認 | 受入条件 1〜8 の確認と特性テスト（解決・移行・所有者切替・空文字化・保存失敗）。`tests` / `tests_ui` / smoke |
| task_08 | 正本反映（最終） | `spec_detail/data_schema.md`・`key_input.md`・`codebase_map.md` へ昇格 + **暫定仕様 06 を凍結** + `decisions_archive/07_hook_keys_global_default.md` 作成 + `current.md` 更新 + `/refactor_check` |

- 依存: task_01 → task_02 / task_03 → task_04 → task_05 → task_06 → task_07 → task_08。
  task_02 と task_03 は task_01 完了後なら並行可。
- タスク定義ファイルは着手するものから `tasks/task_NN_<topic>.md` へ順次起票する（`/task_new`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

1. **後方互換**（最重要）: 既存キーを削除していないか。`hook_keys_individual` 未設定の既存
   keymap_set が移行規則どおり解釈されるか。**保存 JSON のバイト列比較テスト**が壊れていないか
2. **キー解決点が 1 箇所か**: 解決ロジックが読込時の 1 点に集約され、フック層・UI 層へ
   分散していないか（分散すると「古いキーを使い続ける」不具合の温床になる）
3. **dirty 非汚染**: OFF 時の操作で keymap_set が dirty にならないか。
   dirty の記録・復元が例外経路でも成立するか（`dirty_tracker` の不変条件を壊さないか）
4. **保存失敗時の扱い**: config.json 保存が失敗したとき UI / ランタイムを確定させていないか
   （成否を握り潰していないか）
5. **セッション内復活の境界**: 「再 ON で個別値が復活するのは保存前の同一セッション内のみ」が
   実装で表現されているか（保存後に復活してしまわないか）
6. **層の分離**: application / domain に tkinter 依存を持ち込んでいないか。
   presentation が config.json を直接書いていないか（経路は task_04 の API へ集約）

- 各タスクの必須レビューは `reviewer`。**task_07（統合）と task_08（フェーズ完了判定）は
  `deep-reviewer` + Codex レビュー系**を併用する（`.claude/rules/agent_selection.md`）。
- 暫定仕様 06 は確定済みのため、**設計そのものの再レビューはしない**。
  仕様との乖離を見つけた場合は `.claude/rules/spec_change_workflow.md` に従って報告する。
