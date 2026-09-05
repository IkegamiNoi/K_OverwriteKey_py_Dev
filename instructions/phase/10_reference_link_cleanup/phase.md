# phase.md

## フェーズ名

参照元の掃除（reference_link_cleanup）

## フェーズの目的

子JSON（keymap / trigger_set / sequence）に記録された**参照元 `_parent_refs`**（正本
`data_schema.md` §5.8.1）のうち、**実体が無い上位パス**をユーザー操作でまとめて除去する
**保守機能**を追加する。参照元記録は **best-effort 更新**で上位の移動・削除を検知しないため、
陳腐化した記録が残り、**保存時に「N 個の上位で共有中」の誤警告**や
**余分な依存確認（§5.8.5 の 4 択）**を招いている。

**新機能の追加**。影響レイヤは **application（検査・除去のロジック）+ presentation
（メニュー・確認ダイアログ）**で、**保存フロー（§5.8.3〜§5.8.6）と JSON スキーマは変更しない**
（`_parent_refs` の**値**だけを書き換える）。**掃除は非破壊・冪等**（子ファイルを削除しない）。

- 起票元: [idea_07](../../backlog/idea_07_reference_link_cleanup.md)（2026-07-27 起票）。
  着手条件だった **Phase β（phase 06）の完了（2026-08-02）**により昇格。
- 主入力（暫定仕様）: [09_reference_link_cleanup.md](../../history/09_reference_link_cleanup.md)
  （**最終 v0.5**・ユーザー確定済・**phase 10 完了に伴い凍結済**）
- モード: **暫定仕様先行モード**。番号対応: **phase 10 / 暫定 09 / decisions_archive 10**。

## 確定（ユーザー 2026-08-16）

暫定仕様 09 §2 のとおり（要点のみ再掲。詳細は暫定仕様が正）:

- **検査範囲は「現在の構成セットが参照している子」のみ**。列挙は **runtime の source_path 3 種**を
  根拠にする（**`resolve_child_save_targets` は使わない**＝「次にどこへ書くか」であり実体ではないため、
  **無関係な既存ファイルを書き換える事故**になる）。
- **孤児の削除は行わない**。「この掃除で参照元が 0 件になる」ことを**警告表示するだけ**
  （この検査範囲では**孤児判定が原理的に成立しない**ため）。
- **確認 UI は 1 枚**（読み取り専用の一覧 + 実行 / キャンセル）。
  **消える参照元のパスを全件提示**する（件数だけにしない）。
- **現在の keymap_set / trigger_set への参照は、実在しなくても除去しない**（保護対象）。
  **検査の時点で分離**し、提示・件数・0 件警告から除外する。
- **未保存（`keymap_set_path` が空）なら先に保存の確認**を出し、**保存成功時だけ掃除する**
  （キャンセル / 失敗なら中止）。
- **除去直前に対象 JSON を丸ごと読み直し**、`_parent_refs` だけ差し替えて書く。
- **掃除の結果を runtime へ反映しない**（次回読み込みで揃う・dirty も汚さない）。

## スコープ

### 含む

- 検査ロジック（子の列挙 / 実在判定 / **保護対象の分離** / 判定名 / **同一実体の重複排除**）
- 除去 API（`prune_parent_refs` 相当。**全体読み直し** / 全件除去時は **`[]`** / 失敗の報告）
- 提示テキストの整形（Tk 非依存の純関数）
- 確認ダイアログ（`presentation/dialogs/` に 1 クラス）+ **メニュー項目** + **未保存時の保存確認導線**
- 上記を固定する特性テスト（`tests` / `tests_ui`）と実機目視

### 含まない（後送り）

- **孤児ファイルの検出・削除 / `config` 配下の全走査 / 逆方向検査（上位 → 子）**
  → [idea_12](../../backlog/idea_12_orphan_child_file_sweep.md)（**本フェーズのコアを土台に次フェーズ以降**）
- **参照元記録の仕組みそのものの変更**（§5.8.1 の best-effort 方針は維持）。
  保存フロー側で自動的に stale を落とす案は**無警告で生きた参照元を消す**ため採らない
- **ネストしたモーダルの grab 復元**（[idea_10](../../backlog/idea_10_nested_modal_grab_restore.md)）
- 競合検出のための**版情報の照合**（mtime / ハッシュ）

## このフェーズで読むファイル

1. `instructions/history/09_reference_link_cleanup.md` — **主入力（確定設計・最終 v0.5・凍結済）**
2. `instructions/common/spec_detail/data_schema.md` — 正本（**§5.8.1** 参照元記録 /
   **§5.8.4** 共有状況の判定 / §5.7 パス表記 / §5.1 後方互換）
3. `instructions/common/codebase_map.md` — 責務（`config_service` の構成・`config_io` の分割）
4. `keyseq/application/config_service/__init__.py` — `read_parent_refs` / `_normalize_parent_refs` /
   `_parent_refs_for_save` / `_merge_parent_ref` / `resolve_config_path` / `canonical_path`
5. `keyseq/application/config_service/split_loading.py` — 子の読み込みと runtime の内部キー
6. `keyseq/presentation/controllers/config_io/child_save_rows.py` — 行モデルの流儀（判定名で分岐）
7. `keyseq/presentation/dialogs/layout_delete_dialog.py` — `dialogs/` の流儀
   （`tk.Toplevel` 継承 + `destroy()` override で hook resume）
8. `keyseq/presentation/views/menu_bar.py` — メニュー項目の追加箇所
9. `keyseq/presentation/app.py` — コントローラ配線 / 保存経路の入口
10. テスト: `tests/test_child_save_rows.py` / `tests/test_config_service.py` /
    `tests_ui/test_child_save_dialog.py`（**`_replace_parent_refs` で陳腐化を仕込める**）

> 上記以外へ広げない。範囲外の調査が要るときは `Explore` へ委任し結論だけ受け取る。

## タスク

| # | 内容 |
|---|---|
| task_01 | **検査ロジック**（application 新規モジュール）。子の列挙（**runtime の source_path 3 種**）/ 実在判定（`resolve_config_path` 経由）/ **保護対象の分離** / **判定名 4 種** / **同一実体の重複排除**（`canonical_path`）。**表示都合を持たない結果**を返す |
| task_02 | **除去 API**（`prune_parent_refs` 相当）。**除去直前に JSON 全体を読み直す** / 保護対象を再適用 / 全件除去時は **`[]`**（キーは残す）/ `_parent_refs` 以外を変えない / **1 件の失敗で中止しない** |
| task_03 | **提示テキストの整形**（presentation の純関数）。**消えるパスの全件列挙** / **0 件になる子の警告** / 保護対象の扱い。Tk 非依存 |
| task_04 | **UI 配線**。確認ダイアログ（`presentation/dialogs/` に 1 クラス・**読み取り専用の一覧 + 実行/キャンセル**）+ **メニュー項目** + **未保存時の保存確認導線**（保存成功時だけ実行）+ 結果通知 |
| task_05 | **統合確認 + 実機目視**（受入条件 1〜15）。実測は `verifier`、目視の観点はタスク定義で列挙 |
| task_06 | **正本反映（最終）**: `data_schema.md` **§5.8.1 改訂**（+ 必要なら §5.8.4 の注記）/ `features.md` / `codebase_map.md` / 暫定仕様 09 を凍結 / `decisions_archive/10_reference_link_cleanup.md` 作成 / `current.md` 完了更新 / `backlog/INDEX.md` の idea_07 を `INDEX_done.md` へ / `/refactor_check` |

- タスク定義は着手するものから順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。
- 受入条件 13（`tests` / `tests_ui` / smoke が pass）は**各タスクの完了条件に含める**
  （実装委任にテスト追加まで含め、実測は `verifier`）。task_05 で通しの再実測を行う。
- **task_01 → task_02 → task_03 は依存順**。task_04 は task_01〜03 に依存する。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

- **既存の保護を弱めていないか（最重要）**: 掃除が §5.8.4 の誤爆上書き防止に使う記録を
  過剰に削っていないか。**保護対象（現在の keymap_set / trigger_set）が検査・実行の両方で
  一貫して除外**されているか（**表示と実行結果が食い違わない**こと）。
- **列挙の根拠**: 子の列挙が **runtime の source_path 3 種**に基づいているか。
  **`resolve_child_save_targets` を使っていないか**（使うと未実体化の子へ既定パスが割り当てられ、
  **無関係な既存ファイルを書き換える**）。
- **非破壊・冪等**: 変更が `_parent_refs` の**値のみ**に閉じているか。
  **除去直前に JSON 全体を読み直しているか**（確認中の外部変更を消さない）。
  2 回実行して結果が変わらないか。
- **パスの扱い**: 実在確認が `resolve_config_path` を通っているか
  （**相対値を直接 `os.path.exists` へ渡していないか**＝2 度踏んだ罠）。
  **`canonical_path` の値を保存値・表示へ混入させていないか**。
- **`None` / `[]` の区別**: 所有元不明（`None`）を対象外にしているか。
  全件除去で **`[]` を書きキーを残す**か（§5.1）。
- **巻き戻り**: 未保存セットでの保存確認導線が入っているか（無いと個別保存で掃除が巻き戻る）。
- エージェント: 各タスク = `reviewer` / 統合確認・フェーズ完了判定 = `deep-reviewer` + Codex レビュー系
  （`.claude/rules/agent_selection.md` の表）。**フェーズ完了時の 2 本立ては省略しない**。
