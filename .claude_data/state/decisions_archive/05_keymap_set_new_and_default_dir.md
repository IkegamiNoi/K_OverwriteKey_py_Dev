# decisions_archive / 05_keymap_set_new_and_default_dir

フェーズ **05_keymap_set_new_and_default_dir**（新規作成と保存先ディレクトリの整理 = 保存系リデザイン **Phase α**）の判断履歴。
索引は `.claude_data/state/decisions.md`「アーカイブ索引」。
フェーズ定義: `instructions/phase/05_keymap_set_new_and_default_dir/phase.md`。
**設計の正（凍結）**: 暫定仕様 `instructions/history/04_keymap_set_new_and_default_dir.md`（v0.3・凍結）。

- 期間: 2026-07-27（起票・確定）〜 2026-07-28（完了）
- モード: **暫定仕様先行モード**（番号対応: phase 05 / 暫定 04 / decisions 05。暫定仕様は独立採番）
- 目的: 新規作成直後の「無言で `default.json` へ上書き」を解消し、既定保存先を**固定ファイルからディレクトリ
  `config/user/keymap_sets/` へ**移す。死にフラグ `prompt_if_missing` を撤去。**挙動変更フェーズ**。
- 結果: **完了**（task_01〜06）。tests 90 / tests_ui 85 / smoke 全 pass・実機目視 6 項目 OK・
  二系統レビュー通過。production 差分は **5 ファイル +19/-13 行**と小さい。
- 起票元: ユーザー要望（2026-07-26〜27・保存系統の改善討議）。**idea 由来ではない**ため `backlog/INDEX.md` の
  移動対象なし。
- 後続: Phase β（暫定 05）/ Phase γ（暫定 06）/ プリセット（暫定 07）。**α→β の順**（β は α のディレクトリ化前提）。

---

## 設計判断（暫定仕様 §2・ユーザー確定 2026-07-26〜27・v0.3）

1. **新規作成は「ファイルなし」** → **採用**。`new_config` は `keymap_set_path` を空にする。
2. **保存は空パスなら別名保存へ分岐**（ボタン名は「保存」のまま） → **採用**。
3. **Import 成功時は無条件で空**（開始パスが空/非空どちらでも） → **採用**（敵対的レビュー指摘①）。
4. **既定保存先はディレクトリ `config/user/keymap_sets/`**・`default.json` への自動保存/フォールバックを廃止 → **採用**。
5. **別名保存の初期ファイル名は `keymap_set.json`（一般名）** → **採用**（v0.3 でユーザー確定。子ファイルの命名は Phase β）。
6. **起動時にディレクトリ骨格を一括作成**（config.json 本体は初回保存時のまま） → **採用**（指摘④）。
7. **`prompt_if_missing` は新規出力を止めるが既存値は残置許容**（`pop` しない） → **採用**（指摘③）。
   未知キー保持契約により自然消滅しないため、受入は「**新規作成される** config.json に含まれない」で判定。
8. **見つからないときは現状維持**（無言で空起動・選択ダイアログは作らない） → **採用**。
9. **複数の独立した keymap_set の完全対応はしない**（子ファイル共有が残る） → **採用**（指摘②・§9 制約）。Phase β + プリセット案2 へ。

## タスク進行中の判断

### task_03: `config_paths.py` を変更しない（据え置き）
- **採用**。`save_keymap_set_to` の呼び出し元は `save_keymap_set`（空パスは task_02 で `save_as` へ分岐）と
  `save_as`（空文字なら `return False`）のみで、**空パスが `normalize_keymap_set_save_path` へ到達しない**。
  暫定仕様 §5 の「据え置き可」条件を満たすため監査のみ実施し、`tests/test_config_paths.py` も無変更とした。

### task_03: `app.py:64` の `keymap_set_path` 初期化に触れない
- **採用**。`app.py:172` の `load_startup_and_config` が必ず上書きするため。
  「上書きされない経路を見つけたら実装を止めて報告」の条件付きで委任し、該当なしを確認。

### task_04: `tests_ui/test_startup_font_characterization.py` を無修正で維持
- **採用**。`_startup_settings` 側に既存値が入る入力のため、撤去後も `base.update(current)` で保存 dict に残る。
  期待値を変えないことが**残置許容（受入 6）の回帰テスト**として機能する。

### task_05: 受入 7（非変更経路の回帰）に追加テストを作らない
- **採用**。非変更経路に触れた production 差分は 4 点のみで、いずれも既存の特性テストが固定済み
  （`save_as.assert_not_called()` 付きの上書き保存テスト等）。deep-reviewer も「過大評価ではない」と追認。

## 統合レビューの指摘処理（task_05・deep-reviewer 2026-07-28 / codex-reviewer = 指摘なし）

| # | 指摘 | 処遇 |
|---|---|---|
| 1 | `data_schema.md:65`（trigger_set のファイル名は keymap_set 名由来）が「名前がある」前提。空パス時のフォールバック `trigger_set.json` が正本未定義 | **修正して採用** — task_06 で §5.6 へ追記 |
| 2 | 別名保存でレガシー `<base>/settings/` 配下を選ぶと選択パスを捨てて `default.json` へ無言保存（`config_paths.py:72-73`）。§2「フォールバック廃止」の残存経路 | **保留（後続へ）** — ユーザー判断で [idea_09](../../instructions/backlog/idea_09_legacy_settings_save_path_fallback.md) を起票。既存挙動・低頻度のため α のスコープを広げない。**正本 `data_schema.md` §5.4 に「実装未追従」として明記**し、正本＝規定 / 実装＝追従対象という関係を固定した（task_06 のフェーズ完了レビューでの追加対応） |
| 3 | `app.py:64` の初期化と `config_paths.resolve_keymap_set_path()` の引数なし分岐が実質デッド | **保留** — 実害なし（起動時に必ず上書き）。記録のみ |
| 4 | `DEFAULT_KEYMAP_SET_FILENAME` + `save_as` の分岐は ConfigPaths 側に寄せれば不要 | **保留** — 挙動同値で不要変更リスクのみ。記録のみ |
| 5 | 受入 4 の読込例外時に `keymap_set_path == ""` が未固定 | **修正して採用** — assert 1 行追加（再検証 pass） |
| 6 | `test_config_io_characterization*.py` の `app_module.os.makedirs` patch が実装とずれ（実害なし） | **保留** — 記録のみ |
| 7 | 別名保存のたび `config.json` の `keymap_set_path` が更新される既存挙動と「起動時に読むJSONを設定」メニューの関係 | **修正して採用**（記録として） — task_06 で `codebase_map.md` へ 1 行補足 |

## 実機目視（ユーザー・2026-07-28）

6 項目すべて OK: ①新規作成→保存で別名保存ダイアログ（初期名 `keymap_set.json` / 初期 dir `config/user/keymap_sets/`）
②既存セットはダイアログなしで上書き ③別名保存の初期 dir・ファイル名 ④Import 後の保存が別名保存
⑤stored セット不在時は無言で空起動 ⑥既存 `prompt_if_missing` 付き config.json で起動・保存が正常。

## 正本反映（task_06・暫定仕様 §10）

- `spec_detail/data_schema.md` **§5.4 配下に「keymap_set の保存先と『ファイルなし』状態」を新設**
  （空になる 3 経路 / 既定ディレクトリ / 別名保存分岐 / 初期名 / 保存時の `keymap_set_path` 更新 /
  **§9 の子ファイル共有制約** / **レガシー経路の実装未追従注記**）+ **§5.6** に
  keymap_set 未設定時の trigger_set ファイル名フォールバックを追記。
  配置は §5.5「split **読込**」ではなく §5.4「分離JSONの本流」配下とした（保存フローの規定のため。
  **既存の節番号は変更していない**）。
- `codebase_map.md`: App（起動時ディレクトリ骨格・config.json は起動時に書かない）/ KeymapSetIo / StartupIo の責務を追記。
- **`prompt_if_missing` は正本へ追記しない** → **採用**。正本に元々記述が無い（grep 0 件）ため削除対象がなく、
  撤去したキーをわざわざ正本へ書き足さない。なお既存値が残る仕組みは
  `load_startup_settings` の未知キー保持 + `write_startup` の `base.update(current)` による書き戻しであり、
  §5.1「未定義キーは無視する」（読み側の規定）とは別の経路である。

### フェーズ完了レビューでの追加修正（deep-reviewer + codex-adversarial-reviewer・2026-07-28）

- **[高] `codebase_map.md` の誤記を修正** → **修正して採用**。「保存成功のたび `startup_io.write_startup` 経由で
  `config.json` が更新される」は誤り。実際は `save_keymap_set_to` → `config_service.save_runtime_data` が
  `_startup_entry_path`（= `config/config.json`）を**直接**書く。`write_startup` の呼び出し元は
  「起動時に読むJSONを設定」メニューとフォント変更のみ。**誤経路を正本へ焼き付けると Phase β の設計を誤らせる**ため即修正。
- **[中] レガシー経路の未追従注記**（上表の指摘 2 参照）/ **[中] §9 子ファイル共有制約の昇格** /
  **[中] `current.md` の完了フェーズ要約を 1 行リンクへ圧縮**（同ファイル内規「旧フェーズの要約行は削除する」との
  自己矛盾を解消）→ いずれも **修正して採用**。
- **[低] 「初回保存時に作成」→「最初に設定が永続化された時点」** → 修正して採用（フォント変更・起動時読込先の指定でも
  `config.json` は作られるため）。**[低] 空起動 3 経路の (3) を「未設定 / 不在 / 読込失敗」へ明確化** → 修正して採用。
- **[低] `decisions_archive/*.md` 内の `../../instructions/...` リンクが解決不能**（正しくは `../../../`）→ **保留**。
  既存 01〜04 も同形のため、直すなら一括。

## `/refactor_check` 判定（2026-07-28）

- **不要**（M1〜M6 該当なし。対象: `keyseq/` 配下 5 ファイル / +19・-13 行）。提案書は起票しない。
- M1: `config_service.py` は 1014 行だが本フェーズ増分 **-1 行**（「600 行超**かつ** +100 行以上」の AND 条件に非該当）。
- M3: `self._app.keymap_set_path = ""` が 3 箇所（`startup_io.py:18` / `keymap_set_io.py:36` / `:147`）に増えたが、
  **同型ブロックの増殖には非該当**と判定 → **採用**。1 行の代入であってブロックではなく、3 箇所は仕様が定めた
  独立の 3 経路（新規 / Import / 空起動）。片方を直しても他方は追従しない（例: Import だけ挙動を変える改訂はありうる）。
  判定基準の「迷えば非該当」にも合致する。
- M5: 申し送りコメントの新規追加 **0 件**。M2 / M4 / M6 も該当なし。
