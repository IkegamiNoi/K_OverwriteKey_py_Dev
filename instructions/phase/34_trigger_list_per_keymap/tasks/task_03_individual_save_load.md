# task_03_individual_save_load

## 目的

個別保存・個別読込（キーマップ / トリガー一覧 / シーケンス）をキーマップ単位のトリガー一覧に合わせる（暫定仕様 25 §5.6・§5.5 末尾のフォールバック名）。
一括保存（task_02 / 02b）で確立した「trigger_set の親 = keymap」「keymap ファイルの `trigger_set_path`」「共有実体」を個別経路でも崩さない。

**JSON スキーマ不変**。presentation（`controllers/config_io/` の個別 I/O）と application（`config_service` の個別保存・読込）。

## 対象範囲

### トリガー一覧の個別保存・別名保存・読込（`trigger_set_file_io.py` / `config_service.save_trigger_set_file` / `load_trigger_set_file`）

- 対象は**アクティブキーマップのトリガー一覧の実体**（現行どおり口経由）。
- **親参照**: 個別保存で書く trigger_set の `_parent_refs` の親は**アクティブキーマップ（実体の代表キーマップ）の保存先**（keymap_set ではない。§5.4）。
  親 keymap がまだファイルを持たない場合は親参照を加えない（既存の「上位が未確定なら加えない」扱いに揃える）。
- **保存先・参照が変わったら親 keymap を未保存にする**（共有実体なら全メンバー。task_02 で入れた別名保存の最小対応を、**新規保存〔source なし → 保存〕と個別読込**にも広げる）。keymap_set も従来どおり未保存にしてよい。
- **個別読込**: 読み込んだトリガー一覧は**アクティブキーマップにだけ**付く（参照はキーマップごと）。アクティブが他のキーマップと実体を共有していた場合は、
  アクティブだけが新しい実体を持ち、他のキーマップは元の実体のまま（共有が外れる）。既に同じパスの実体を持つキーマップがあればその実体を共有する。
- **フォールバック名**（§5.5 末尾）: 個別「トリガー一覧を保存」で source_path が無いときの既定名 = 親 keymap の保存先 stem → 無ければ `trigger_set`。

### キーマップの個別保存（`keymap_file_io.save_keymap_to_path` / `config_service.save_keymap_file`）

- **保存計画で実行**し、**そのキーマップの dirty な trigger_set / sequence（§5.2 の source なしを含む）があれば一覧ダイアログを出す**
  （個別トリガー一覧保存が sequence 行だけのダイアログを出すのと同じ構図。keymap 自身は行に出さない）。
  trigger_set の保存先が決まってから keymap の `trigger_set_path` を書く（依存 3 段の順）。キャンセルなら何も書かない。
- 移行先キーマップ（§4.2）を個別保存した場合は keymap_set を未保存のまま残す（task_02 で規定済み・崩さない）。
- **保存後の runtime 反映で triggers の同一性を壊さない**: 現行は保存後にキーマップ要素を正規化コピーで丸ごと差し替えており（`keymap_file_io.py:73`）、
  共有実体の同一性とトリガー一覧 UI が見ているリストが切れる。**要素の内部キー・`trigger_set_path` 相当の反映だけを行い、`triggers` のリストオブジェクトは差し替えない**。

### キーマップの個別読込（`keymap_file_io.load_keymap_file` / `config_service.load_keymap_file`）

- 読み込む keymap ファイルの `trigger_set_path` を読み、**参照先のトリガー一覧・シーケンスも一緒に読む**（split 読込の `attach_trigger_set` 等、task_01b の読込処理を流用し規則を複製しない）。
  既に同じ解決済みパスの実体を持つキーマップがあれば共有する。読めない場合は split 読込と同じ扱い。
- 読み込んだキーマップを runtime へ**追加**する現行動作は維持（切替キー必須化・追加前の既存キーマップへの切替キー設定は **task_06** の追加フローで行う）。

### シーケンスの個別保存・読込（`sequence_file_io.py`）

- 親参照（trigger_set）と未保存化の対象が**アクティブキーマップの実体**になっていること・合成キー（task_02）と整合していることを確認し、崩れていれば直す（規則は変えない）。

### テスト（追加・更新）

- 既存テストの期待値更新は、親参照が keymap になったこと・個別保存が保存計画で行になることによるもののみ。アサーションを緩めない。テスト補助で runtime を書き換えない。
  キーマップ 0 個のフィクスチャを作らない。未モックの子保存ダイアログを開かない（各テストクラスのガードに従う）。
- 新規:
  1. 個別トリガー一覧保存の `_parent_refs` に親 keymap のパスが入る（keymap_set ではない）。
  2. 個別トリガー一覧の新規保存・別名保存・読込で親 keymap が未保存になり、続く一括保存で keymap ファイルの `trigger_set_path` が新パスになる。
  3. 共有実体のアクティブへ個別読込 → アクティブだけ新しい実体、他は元の実体のまま。
  4. フォールバック名: 親 keymap の stem / 親が未保存なら `trigger_set`。
  5. キーマップの個別保存で dirty な trigger_set / sequence が一覧に出る・キャンセルで何も書かない・保存後に `triggers` が同一オブジェクトのまま（共有も保たれる）。
  6. キーマップの個別読込で参照先のトリガー一覧・シーケンスが付く・既存実体と同じパスなら共有される。

## 読むファイル

- `instructions/history/25_trigger_list_per_keymap.md` §5.4〜§5.6（該当節のみ）
- `instructions/common/spec_detail/data_schema/5_08_07_individual_save.md`
- `keyseq/presentation/controllers/config_io/{trigger_set_file_io,keymap_file_io,sequence_file_io}.py`（全体）
- `keyseq/application/config_service/__init__.py:120-330`（個別保存・読込）
- `keyseq/application/config_service/split_loading.py:320-420`（`attach_trigger_set` 等の流用元）
- `keyseq/domain/keymap_triggers.py`（全体）
- 手本のテスト: `tests/test_per_keymap_bulk_save.py:1-80` / `tests_ui/test_config_io_characterization.py` の個別保存テスト（該当メソッドのみ）

## 含まない

- キーマップ追加時の切替キー必須化・個別読込への追加規則の適用・一覧の選択 = アクティブ化（**task_06**）
- 参照辿り 3 段・孤児棚卸し（task_04）/ 入力判定（task_05）/ 改名（task_07）
- `instructions/` 配下の編集（task_08）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass（skip 7 据え置き）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass（ハングしないこと）
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass
- `git grep -n '"triggers"' -- keyseq/presentation` が 0 件 / `git status --short -- instructions` は本タスク定義のみ
- 期待値を更新した既存テストの一覧と理由を報告に含める

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_06 以降でまとめて実施。
