# phase.md

## フェーズ名

アクション要素と内部キーの型正規化（action_and_internal_key_type_coercion）

## フェーズの目的

正本 §5.1「型不正の共通規則」に**追従していない残り 2 系統**を片づける。

1. **アクション要素の `type` / `button`**: 非文字列だと `.strip()` で `AttributeError`
   （実行時 = `action_executor.py:51` / `:119`、一覧表示 = `domain/config.py:323`、
   ダイアログ等 = presentation の 3 箇所）。
2. **runtime 専用の内部キー（パス系 3 種）**: `ensure_config_compatibility` が生値のまま素通しし、
   読み手の `str(...)` を経て**保存先パス候補に repr が混入し得る**。

**直す場所は読込時の正規化 1 箇所（domain `keyseq/domain/config.py`）に寄せる**。
読み手（application / presentation の約 25 箇所）は触らない。
**domain 限定・JSON スキーマ不変**（読込の頑健化のみ）。

- 起票元: [idea_27](../../backlog/idea_27_mouse_click_button_type_coercion.md) /
  [idea_28](../../backlog/idea_28_runtime_internal_key_type_coercion.md)（統合・ユーザー判断 2026-09-23）。
- 主入力（暫定仕様）: なし（直接改訂モード）。
- モード: **直接改訂モード**。番号対応: phase 30 / decisions 30。
  正本の改訂は `data_schema.md` §5.11（idea_27 + `type`）と §5.7 の ※ 注記削除（idea_28）のみ。
  **task_02 の棚卸しで入口が 1 箇所に収まらないと分かった場合は、暫定仕様先行モードへ切り替える**
  （ユーザー判断 2026-09-23）。

## 確定（ユーザー 2026-09-23）

- idea_27 は**案 A**: §5.11.2 の「非文字列は未定義」を削除し、§5.1 に従う（非文字列は空扱い → 既定 `left`）。
  **案 B（実装だけ防御・仕様は未定義のまま）は採らない**。
- **`type` の非文字列も含める**（idea_27 の想定スコープ外だったが同系統・影響が大きいため。起票時の調査で発見）。
- **適用点は読込時の正規化**（`normalize_actions`）。実行・表示・ダイアログの全読み手を 1 箇所で守る。
- idea_28 は**入口側（`ensure_config_compatibility`）で `coerce_label`**（trim のみ・小文字化しない）。
  読み手側で個別に潰す案は採らない。
- **空 / 未知の `type` は現行挙動を §5.11 に明文化する**（案 A）: 実行時は `value` を文字列として入力する
  （`action_executor.py:64`）。**コードは変えない**。`type` の非文字列を空扱いにするとこの経路へ入るため、
  未規定のまま残さない。
  「何も送らずエラー通知」（案 B）は層跨ぎ・挙動変更で直接改訂に収まらないため
  [idea_35](../../backlog/idea_35_unknown_action_type_handling.md) へ分離（着手時は暫定仕様先行モード）。

## 起票時の調査（2026-09-23・grep 実測）

| # | 箇所 | 現状 | 対応 |
|---|---|---|---|
| 1 | `domain/config.py:144` `normalize_actions` | `label` のみ `coerce_label` | `type` / `button` を追加（**キーがある場合のみ**。無いキーを補わない） |
| 2 | `(... get("type") or "").strip()` | 5 箇所（`action_executor.py:51` / `domain/config.py:323` / `hook_controller.py:241` / `trigger_panel_controller.py:301` / `action_dialog.py:115,119`） | #1 で守られるため無修正 |
| 3 | `action_executor.py:119` `button` | `try` の外で `.strip()` | #1 で守られるため無修正 |
| 4 | `domain/config.py:197-203`（`_sequence_source_path`）/ `:277-283`（`_keymap_source_path`）/ 直下の `_trigger_set_source_path`（`safe_deepcopy` で素通し） | 生値コピー | `coerce_label` で受ける |
| 5 | 内部 source_path の読み手（`save_path_resolution.py` / `split_payloads.py` / `orphan_scan.py` / `parent_refs_cleanup.py` / presentation `config_io/*` / `dirty_state.py`） | `str(... or "")` 等 | #4 で守られるため無修正（task_02 で確認） |
| 6 | 内部キーの**書き手**（`split_loading.py:314,424,492` / `save_plan_execution.py:299,310,313` / `config_service/__init__.py:135,180,199,232,299` / `dirty_state.py:28`） | 計算済みの文字列を書く想定。ただし `__init__.py:299` は `str(sequence_item.get("path") or "")` | **task_02 の棚卸しで入口外の混入経路がないか確認** |

## スコープ

### 含む

- `keyseq/domain/config.py`: `normalize_actions` で `type` / `button` を `coerce_label`（キーがある場合のみ）。
- `keyseq/domain/config.py`: `ensure_config_compatibility` でパス系内部キー 3 種を `coerce_label`。
- 上記の単体テスト（`tests/test_domain_config.py` 等）。
- 正本 `data_schema.md`: §5.11.1 / §5.11.2 の改訂（task_01・**実装前に確定**）、§5.7 の ※ 注記削除（task_02）。
- task_02 の棚卸しで見つかった**入口外の混入経路**（#6）の最小修正。

### 含まない（後送り）

- `x` / `y` / `clicks` / `drag` / `to_x` / `to_y` / `drag_speed` / `value` の型規則の見直し。
- 空 / 未知の `type` の挙動変更（エラー通知化・ダイアログの空 `type` = hotkey との食い違い解消）→
  [idea_35](../../backlog/idea_35_unknown_action_type_handling.md)。
- 読み手側（#2 / #3 / #5）の書き換え（入口で守るため不要。読み手の防御的な書き直しもしない）。
- 内部キーのうちパス以外（`_*_imported` / `_*_dirty` / `_*_parent_refs`）。
- `type` の小文字化を保存値へ反映すること（読み手が `.lower()` 済み。§5.1 の小文字化対象外）。
- 内部キー名の定数を domain へ移すこと（domain は既に文字列直値で持っている。既存構造）。
- UI・保存 payload の変更。

## このフェーズで読むファイル

1. 正本 `instructions/common/spec_detail/data_schema.md` §5.1「型不正の共通規則」/ §5.7 / §5.11.1〜§5.11.2
2. `instructions/common/spec_detail/data_schema/5_08_02_runtime_internal_keys.md`（内部キーの一覧）
3. `keyseq/domain/config.py:84-85`（`coerce_label`）/ `:144-155`（`normalize_actions`）/
   `:157-311`（`ensure_config_compatibility`。内部キーは `:197-203` / `:277-283`）/ `:322-338`（`format_action_list_item`）
4. `keyseq/application/action_executor.py:50-64` / `:112-128`（`type` / `button` の読み手）
5. task_02 のみ: 上表 #6 の書き手（`split_loading.py` / `save_plan_execution.py` / `config_service/__init__.py`）
6. `tests/test_domain_config.py`（phase 24 / 25 の `coerce_*` テストの書き方）
7. 起票元 [idea_27](../../backlog/idea_27_mouse_click_button_type_coercion.md) /
   [idea_28](../../backlog/idea_28_runtime_internal_key_type_coercion.md)

## タスク

- task_01: §5.11 の改訂（先行）→ `normalize_actions` で `type` / `button` を正規化（+ 単体テスト）— **完了**（2026-09-23）
- task_02: 内部キーの書き手の棚卸し（#6）→ `ensure_config_compatibility` でパス系内部キーを正規化（+ 単体テスト）→
  §5.7 注記削除 → 記録（decisions_archive/30 / current.md / backlog INDEX → INDEX_done / `/refactor_check`）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。
- **本フェーズ固有**:
  - **無いキーを補っていないか**（`button` / `type` を持たないアクションに空文字キーが増えると保存出力が変わる）。
  - **正常な文字列値の挙動が不変か**（trim 以外の変化がないこと。パスは小文字化しない）。
  - falsy な非文字列（`0` / `false` / `[]` / `{}` / `None`）の挙動が不変か。
  - **全読込経路が `normalize_actions` / `ensure_config_compatibility` を通るか**
    （split 読込・個別 sequence / keymap 読込・単一 JSON。§5.11 冒頭の規定）。
  - 読み手を無修正にした判断の妥当性（入口外の混入経路の取りこぼし。phase 24 で 2 度発生した）。
  - 依存方向（domain は application の定数を import しない）。
