# decisions_archive / phase 64: 外部キーレイアウトのパス基準の統一

対応表: phase 64 / 暫定なし（直接改訂モード）/ decisions 64。起票元: idea_13（2026-09-06 起票・2026-10-20 実害確認〔読込のたびに `config/` が 1 段増え、jis が消えて再登録で重複が溜まる〕）。
完了 2026-10-21。application（`split_loading.normalize_external_keyboard_layouts`）+ presentation（`LayoutController` の登録・表示・`ConfigPaths.to_rel_if_possible` 削除）。**JSON スキーマ不変・§5.7 の規定も不変**（実装を仕様へ合わせる修正）。
正本 = `data_schema.md` §5.7（不変）・`data_schema/5_08_09_orphan_sweep.md`（superset の理由）/ 地図 = `codebase_map.md` のパス系の節「外部レイアウトのパス」。

## 確定した設計判断（ユーザー 2026-10-20〜21）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | 登録・読込・表示を `config_root` 基準の相対（`/` 区切り・config 外は絶対）へそろえる（§5.7 どおり） | 親基準へそろえる = §5.7 と食い違う |
| 2 | **既存の壊れた値の移行・同一ファイルの重複除去はしない**（利用者が JSON を手で直す） | 読込時に先頭の `config/` を外して実在する値へ直す・同じ解決先を 1 件へ = ユーザー判断「余計な処理を入れない」 |
| 3 | 登録時の重複判定は文字列比較のまま（旧表記が残ると同じファイルを再登録できるのは受容） | 解決後のパスで比較 = 表記がそろえば不要 |
| 4 | 孤児検出（§5.8.9）の両基準 superset は残す（コード不変・理由の記述のみ更新） | 外す = 手で直していない旧表記の JSON が指すレイアウトが隔離の候補に出る |
| 5 | 単一 JSON の取り込み（`keymap_set_io.py:614`）は正規化しない = 受容（2026-10-21） | 取り込み時に直す = 旧表記は直しても読めない |

## タスク中の判断

### 【起票】モード = **直接改訂**（§5.7 は不変・正本は §5.8.9 の理由の記述と codebase_map のみ・タスク 2）
- 当初は移行規則・重複除去を含む暫定仕様先行を提案 → ユーザーが「手で直せばよい」と判断し範囲を縮小（#2・#3）
- 起票の整合チェック（reviewer）: 軽微 3 件を反映（`test_layout_controller_scan_code.py` の期待値の見直し・重複判定の受容の明記・superset の確定）
### 【task_01】codex-implementer・tests 1761 / tests_ui 1122 / smoke OK・reviewer 完了可・実機目視 OK（2026-10-21）
### 【task_02 完了判定前レビュー】Codex 敵対的 needs-attention（中 1）/ deep-reviewer 完了可（中 1・低 4）→ ユーザー確定（2026-10-21・推奨どおり）
- Codex 中（採用 → task_01a）: 読込で解決を 2 回重ね、相対の `config_root` で `config/` が増える（通常の起動は絶対で実害なし）→ 解決前の値を直接渡す。deep 低 4（config 外の絶対パスの登録のテスト）も同タスクで追加
- deep 中（受容 = #5・§5.8.9 と codebase_map に明記）
- deep 低 2（採用・文書）: 旧表記の例に旧既定の置き場所の `keylayout\jis.json` を追加。低 3（既存 subTest の期待値が実装と同じ関数）・低 5（§5.8.9 の候補ディレクトリに keylayout が無い = 前からの記述）は対応不要
### 【task_01a】codex-implementer・tests 1763 / tests_ui 1122 / smoke OK・reviewer 完了可（2026-10-21）・実機目視は不要（絶対の `config_root` では挙動不変）
### 【task_02 /refactor_check】不要（2026-10-21）
- 範囲 `git diff 693f039..HEAD -- keyseq/`（3 ファイル・+6 / -14）。M1（最大 `split_loading.py` 561 行・減少）・M2〜M6 は非該当（M5 = 0 件）
- 残存リスク: 旧表記の値は黙って一覧から外れ、利用者に通知されない（ユーザー確定の範囲内）
