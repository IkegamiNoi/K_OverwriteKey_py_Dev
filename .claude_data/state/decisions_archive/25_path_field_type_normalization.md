# decisions_archive / phase 25: パス系フィールドの型正規化

対応表: phase 25 / **暫定仕様なし（直接改訂モード）** / decisions 25。
起票元: [idea_25](../../../instructions/backlog/idea_25_path_field_type_normalization.md)
（phase 24 task_01 の全走査で発見・スコープ外として分離）。
完了 2026-09-19。**挙動追従（頑健化）・スキーマ不変**。
正本 = `spec_detail/data_schema.md` §5.5（split 読込）/ §5.7（パス保存ルール）へ型の規定を追記。
**§5.1「型不正の共通規則」の本文は変更していない**。

## 問題

JSON から読む**パス系・キー名系**のフィールドに `str()` 強制が残っており、非文字列を渡すと
**Python の repr 文字列がパス / スイッチキーとして runtime に載る**。

**例外（`AttributeError`）になる箇所はゼロ**（すべて `str()` でラップされているため）。
phase 24 とは異なり、本フェーズは**repr 混入の解消**が目的。

## 現状監査（2026-09-19・`.venv` で実測）

| # | 箇所 | 挙動 | 実害 |
|---|---|---|---|
| 1 | `domain/config.py:240` `external_keyboard_layouts[].path` | **repr が runtime に載る** | 中 |
| 2 | `split_loading.py:397` `keymaps[].switch_key` | **repr がスイッチキーとして載る**（`path` が有効なとき） | 中 |
| 3 | `split_loading.py` のパス系 **7 箇所**（`:312` / `:337` / `:396` / `:399` / `:441` / `:522` / `:524`） | repr がパスになるがファイル不在で静かに無視 | 小 |
| 4 | `domain/config.py:301` `keymap_switch_keys` の値 | repr が id になるが `keymap_ids` の membership check で落ちる（**偶然の防御**） | なし |
| 5 | `reference_scan.py:185` `_source_path`（task_01b で発見） | repr が `referenced` 集合に紛れる | 小 |
| 6 | `orphan_sweep_scan_dirs` / `_parent_refs` / `hotkey_presets_path` | 非 str を除去 / `isinstance` ガード済み | なし（対象外） |

## 確定した設計判断（ユーザー 2026-09-19）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | **idea_25 の案 A（`coerce_*` を適用）** | **案 B（現状維持 + 正本へ「未定義」と明記）は採れない**。phase 24 で新設した §5.1 は「文字列を期待するフィールド」と書いており**フィールドを限定していない**ため、パス系も既に規定の対象。案 B は §5.1 を後から緩めることになり `spec_change_workflow.md` の禁止事項（実装に合わせて仕様書を緩める）に当たる |
| 2 | **直接改訂モード** | 暫定仕様先行 = 仕様変更が無い（§5.1 の規定は変えず、§5.5 / §5.7 へ参照を足すだけ）ため不要。idea_24 / phase 23 と同じ「規定が正・実装が未追従」の構図 |
| 3 | **パスは `coerce_label`（trim のみ）/ キー名・id は `coerce_key_name`（trim + 小文字化）** | パスに `coerce_key_name` を使うと**小文字化でパスが壊れる**（`User/Keymaps/A.json` → `user/keymaps/a.json`）。§5.7 の同一性判定で使う `normcase` は**比較専用**であり、記録する表記は大文字小文字を保持する |
| 4 | **`keymap_switch_keys` の値も `coerce_key_name` へ** | 現状は `keymap_ids` の membership check で**偶然**落ちているだけ。偶然の防御に依存しない形にする |
| 5 | **参照突合経路（`reference_scan.py`）も揃える**（task_01b） | 放置 = 同じフィールドを 2 経路で違う扱いにしたままになる（本フェーズが解消しようとしている状態そのもの）。実害は小さいが、後送りすると同じファイルを 2 度触ることになる |
| 6 | **`startup_io.py:18` の `keymap_set_path` は対象外** | config.json の生値を読むが **presentation 層**で、phase.md が presentation 不変と宣言しているため。実害は「存在しないパスとして無視される」のみ。**残件として記録する** |

## フェーズ中の追加判断

- **task_01 の完了後レビューで `reference_scan.py` の取りこぼしを検出** → ユーザー判断で
  **後送りせず task_01b として本フェーズ内で直した**。変更は `_source_path` の本体 1 行 + import
  （`_entry_path` / `_path_value` は `_source_path` を呼ぶだけなので全経路が吸収される）。
- **起票時レビューで `task_01` の行番号誤記 1 件**（`active_keymap_path` を `:339` と書いたが
  実際は `:337`）を指摘され修正。phase.md 側は正しかった。
- `orphan_scan.py` / `quarantine.py` の `str(x or "").strip()` は、`normalize_scan_dirs` で
  正規化済みの値・内部生成の値・startup 設定を受ける引数であり、**生 JSON のフィールドを
  直接読む箇所ではない**ため対象外と判断した。

## 実測・レビュー

- compile clean / `tests` **514**（skip 7・505 → **+9**。task_01 で +6 / task_01b で +3）/
  `tests_ui` **446** / smoke pass。
- `reviewer`（phase.md 整合）= **採用**（§5.1 がパス系も対象と読めることを裏取り）/
  `reviewer`（task_01 差分）= **完了可**（`reference_scan` の取りこぼしを参考指摘）/
  `reviewer`（task_01b 差分）= **完了可**（指摘なし）。
- 実機目視 = **不要**（読込経路の内部正規化のみで UI 変更なし）。
- コミット: `b8636bb`（task_01）/ `ad0a7d0`（task_01b）/ 本フェーズ末のコミット（task_02）。
- `/refactor_check` = **不要**（PHASE_BASE `f0e5887`・対象 3 ファイル・M1〜M6 該当なし）。
  M1: **いずれも 600 行未満**（`split_loading.py` 537 / `domain/config.py` 353 / `reference_scan.py` 198）で、
  増分も +13/-11 と 100 行未満（M1 は「600 行超 **かつ** +100 行以上」の両立が条件）。M2: 新規関数なし（phase 24 の `coerce_*` を再利用）。
  M3: 同型ブロックの増殖ではなく**既存ヘルパへの集約**。M4〜M6: 該当なし。

## 残件

- **`startup_io.py:18` の `keymap_set_path`**（presentation 層・判断 6）。
- **runtime 専用の内部キー（`_keymap_source_path` / `_sequence_source_path` / `_trigger_set_source_path`）**
  が §5.1 に未追従（完了判定前 `deep-reviewer` 指摘 B・実測で確認）。`ensure_config_compatibility` が
  **生値のまま素通し**するため、手編集の単一 JSON に非文字列を入れると runtime に残り、
  `save_path_resolution.py:127` の `str(...)` を経て**保存先パスの候補に repr が混入し得る**。
  内部キーは永続化しない（§5.8.2）ため実害は限定的だが、**正本 §5.7 に【実装未追従】として明記した**。
- `button` 非文字列の `AttributeError`（`action_executor.py:119`）= phase 22 からの
  別タスク化候補のまま。**実行時**の型不正であり読込時の正規化とは別レイヤ。
- `coerce_label` はパスにも使うため名前が内容と合わない（改名は見送り。触りたくなった時に単独タスク化）。
