# phase.md

## フェーズ名

パス系フィールドの型正規化（path_field_type_normalization）

## フェーズの目的

JSON から読む**パス系・キー名系のフィールド**に残っている `str()` 強制を解消し、
正本 §5.1「型不正の共通規則」へ**実装を追従**させる。現在は非文字列を渡すと
**Python の repr 文字列がパス / スイッチキーとして runtime に載る**。

**domain / application 限定・JSON スキーマ不変**（読込の頑健化のみ）。
**例外（`AttributeError`）になる箇所は無い**ため、本フェーズは repr 混入の解消が目的。

- 起票元: [idea_25](../../backlog/idea_25_path_field_type_normalization.md)
  （phase 24 task_01 の全走査で発見・スコープ外として分離）。
- 主入力（暫定仕様）: なし（直接改訂モード）。
- モード: **直接改訂モード**。番号対応: phase 25 / decisions 25。
  **正本の規定 §5.1 は変更しない**（「文字列を期待するフィールド」と限定していないため、
  パス系も既に対象。追記は §5.5 / §5.7 への参照 1〜2 行のみ）。

## 確定（ユーザー 2026-09-19）

- idea_25 の**案 A**（`coerce_*` を適用）を採る。
  **案 B（現状維持 + 未定義と明記）は採らない** — §5.1 を後から緩めることになり
  `spec_change_workflow.md` の禁止事項（実装に合わせて仕様書を緩める）に当たるため。
- 挙動変更（repr 文字列だった値が空になり、要素が落ちる / 無視される）を許容する。

## 現状監査（2026-09-19・`.venv` で実測）

| # | 箇所 | 挙動 | 実害 |
|---|---|---|---|
| 1 | `domain/config.py:240` `external_keyboard_layouts[].path` | **repr が runtime に載る** | 中 |
| 2 | `split_loading.py:397` `keymaps[].switch_key` | **repr がスイッチキーとして載る**（path が有効なとき） | 中 |
| 3 | `split_loading.py:312` / `:337` / `:396` / `:399` / `:441` / `:522` / `:524` のパス系（7 箇所） | repr がパスになるがファイル不在で静かに無視 | 小 |
| 4 | `domain/config.py:301` `keymap_switch_keys` の値 | repr が id になるが `keymap_ids` の membership check で落ちる（**偶然の防御**） | なし |
| 5 | `orphan_sweep_scan_dirs` / `_parent_refs` / `hotkey_presets_path` | 非 str を除去 / `isinstance` ガード済み | なし（対象外） |

**例外になる箇所はゼロ**（すべて `str()` でラップされているため）。

## スコープ

### 含む

- `keyseq/domain/config.py`: `external_keyboard_layouts` の `path`（`:240`）と
  `keymap_switch_keys` の値（`:301`）へ `coerce_*` を適用する。
- `keyseq/application/config_service/split_loading.py`: 上表 #2 / #3 の計 8 箇所（パス系 7 + `switch_key` 1）。
- 対応する単体テスト。
- 正本 `data_schema.md` §5.5 / §5.7 へ「パス系も §5.1 に従う」を明記
  （`external_keyboard_layouts` の該当節があればそこにも 1 行）。

### 含まない（後送り）

- `orphan_sweep_scan_dirs` / `_parent_refs` / `hotkey_presets_path`（既に規定どおり）。
- keymap / trigger_set / sequence の**内容フィールド**（phase 24 で対応済）。
- `button` 非文字列（`action_executor.py:119`・**実行時**の型不正で別レイヤ・phase 22 からの候補）。
- パスの実在確認・正規化規則そのものの変更（§5.7 の表記ルールは不変）。
- `coerce_label` の改名（パスにも使うため名前が合わないが、**互換のため phase 24 の名前を継続**。
  気になるなら別タスクで扱う）。
- UI・保存 payload の変更。

## このフェーズで読むファイル

1. 正本 `instructions/common/spec_detail/data_schema.md` §5.1「型不正の共通規則」/ §5.5 / §5.7
2. `keyseq/domain/config.py:76-90`（`coerce_key_name` / `coerce_label`）/ `:232-246`
   （`external_keyboard_layouts`）/ `:293-311`（`keymap_switch_keys`）
3. `keyseq/application/config_service/split_loading.py:305-345`（`trigger_set_path` /
   `active_keymap_path`）/ `:390-445`（`load_keymap_entry` 周辺）/ `:515-530`（外部レイアウト）
4. `tests/test_domain_config.py` / `tests/test_config_service.py`（phase 24 で追加した
   `coerce_*` テストの書き方）
5. [idea_25](../../backlog/idea_25_path_field_type_normalization.md)（起票元・現状の一覧）

## タスク

- task_01: パス系・キー名系へ `coerce_*` を適用する（+ 単体テスト）— **完了**（2026-09-19・`b8636bb`）
- task_01b: 参照突合経路（`reference_scan.py`）の同種箇所を直す（task_01 のレビューで発見）— **完了**（2026-09-19・`ad0a7d0`）
- task_02: 正本反映と記録（§5.5 / §5.7 への明記 / decisions_archive/25 / current.md /
  backlog INDEX → INDEX_done / `/refactor_check`）— **完了**（2026-09-19）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。
- **本フェーズ固有**:
  - **falsy な非文字列の既存挙動が不変か**（`0` / `false` / `[]` / `{}` / `None`）。
  - **正常なパス文字列の解決結果が 1 文字も変わっていないか**（相対 / 絶対の判定・§5.7 の表記）。
  - **パスに `coerce_key_name` を使っていないか**（小文字化でパスが壊れる。パスは trim のみ）。
  - `keymap_switch_keys` の membership check という**偶然の防御に依存しない**形になっているか。
  - **取りこぼしがないか**（phase 24 で 2 度発生した。該当パターンの全走査で確認すること）。
  - 依存方向（application → domain のみ）。
