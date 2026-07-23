# idea_05_trigger_set_source_path_inconsistency.md

## 概要

**トリガー一覧（trigger_set）の source_path が、読み手と書き手で別の場所を指しており繋がっていない。**
読みは未定義の App 属性、書きは誰も読まない `dirty_tracker` の属性。結果として
**「読込で持ってきたトリガー一覧です。別名で保存しますか？」の確認ダイアログが到達不能**になり、
トリガー一覧の上書き保存は毎回パス選択からやり直しになる。

keymap / sequence は対象 dict の内部キーで対称に読み書きしており、**この問題は trigger_set だけ**。

## 起票経緯（2026-07-23）

出所: 暫定仕様 [03_config_io_controller_split](../history/03_config_io_controller_split.md) 起票時の
`codex-adversarial-reviewer` による敵対的レビュー指摘（[high]）。メインセッションが実コードで裏取りし確認した。

phase 04（ConfigIoController の責務分割）は**挙動不変が絶対前提**のため、同フェーズでは
**この挙動をそのまま移設する**と決定済（暫定仕様 03 §1「既存の不整合」/ §9 スコープ外）。
分割時に「明らかな誤りだから」と直すと受け入れ条件を破るため、実装タスクに禁止事項として転記される。

## 現状

対象: `keyseq/presentation/controllers/config_io_controller.py`
（phase 04 で `controllers/config_io/` 配下へ分割される予定。着手時に現在のパスを再確認すること）

| 種別 | 箇所 | 内容 |
|---|---|---|
| 読み | `:439`（`save_trigger_set_file`）| `getattr(self._app, "_trigger_set_source_path", "")` |
| 読み | `:451`（`save_trigger_set_file_as`）| 同上 |
| 書き | `:221`（`apply_loaded_data_to_ui`）| `self._app.dirty_tracker.trigger_set_source_path = ""` |
| 書き | `:472`（`save_trigger_set_to_path`）| `self._app.dirty_tracker.trigger_set_source_path = path` |
| 書き | `:502`（`load_trigger_set_file`）| 同上 |

**確認済みの事実**（grep による実測・2026-07-23）:

- **`App._trigger_set_source_path` はリポジトリ内のどこにも定義されていない**（定義 0 件。
  参照は上記の読み 2 箇所のみ）。よって読み出しは**常に `""`**。
- **`dirty_tracker.trigger_set_source_path` は write-only**。`dirty_state.py:14` の初期化を除き、
  読み手が存在しない。

**帰結（現在の実挙動）**:

1. `save_trigger_set_file:440` の `if path and ...` は常に偽 → 「読込で持ってきたトリガー一覧です。\n
   別名で保存しますか？」の askyesno は**到達不能なデッドコード**。
2. トリガー一覧の上書き保存は常に「source_path なし」扱いとなり、毎回
   `choose_save_path_with_collision`（同名ファイルがあれば上書き確認）を通る。
3. `save_trigger_set_file_as:451` も常に `""` を読むため、初期ディレクトリとファイル名の
   サジェストが `keymap_set_file_stem()` 由来にフォールバックする（読込元のファイル名が反映されない）。

**比較（他 2 種は対称）**: keymap は `INTERNAL_KEYMAP_SOURCE_PATH`、sequence は
`INTERNAL_SEQUENCE_SOURCE_PATH` を対象 dict に持ち、同じキーを読み書きしている（`:356` / `:521` 他）。

## 提案（方向性・要設計）

いずれも**挙動変更を伴う**ため、着手時に設計を確定してから実装する
（`.claude/rules/spec_change_workflow.md`）。

- **案 1: `dirty_tracker` 側へ寄せる** — 読みを `dirty_tracker.trigger_set_source_path` に変更する。
  最小差分（2 行）。trigger_set は keymap / sequence と違い「対象 dict」が存在しない
  （`data["triggers"]` は配列）ため、状態を tracker に持つ構造自体は自然。
- **案 2: App 属性を実際に定義する** — `_trigger_set_source_path` を App に持たせ、書き手をそちらへ変更。
  ただし `dirty_tracker` が `trigger_set_imported` / `trigger_set_dirty` を持っている以上、
  source_path だけ App に置くのは責務が割れる。**非推奨**。
- **併せて要検討**:
  - 修正すると `:440` のデッドコードが復活し、**「別名で保存しますか？」ダイアログが新たに出るようになる**。
    これは UX の変化であり、ユーザー合意が必要（そもそもこの確認を出したいのか）。
  - `save_trigger_set_file_as` のサジェスト名も変わる（読込元ファイル名が反映されるようになる）。
  - keymap / sequence と挙動を揃えるべきか、trigger_set だけ別扱いのままでよいか。

## 想定スコープ

- 含む: trigger_set の source_path の読み書き経路（save / save_as / load / `apply_loaded_data_to_ui`）。
  phase 04 完了後は `controllers/config_io/trigger_set_file_io.py` 相当が対象。
- 含まない: keymap / sequence 側の変更 / `dirty_state.py` の他フィールドの整理 /
  D/E/F の共通化（→ [idea_06](idea_06_individual_json_io_unification.md)）。
- 影響レイヤ: presentation のみ。
- 仕様変更: **あり**（到達不能だったダイアログが出るようになる = UX 変化）。優先度: **中**
  （機能実害は「上書き保存のたびにパス確認が出る」程度だが、デッドコードの放置は共通化の妨げになる）。
- 前提: **phase 04（ConfigIoController の分割）の完了後に着手する**。分割前に直すと
  phase 04 の「挙動不変」検証の基準が動くため。

## 関連

- 分離元: 暫定仕様 [03_config_io_controller_split](../history/03_config_io_controller_split.md) §1「既存の不整合」/ §9
- 後続: [idea_06](idea_06_individual_json_io_unification.md)（D/E/F の共通化。**本 idea の解消が前提**）
- 関連ルール: `.claude/rules/spec_change_workflow.md`（挙動変更は仕様変更フロー）
