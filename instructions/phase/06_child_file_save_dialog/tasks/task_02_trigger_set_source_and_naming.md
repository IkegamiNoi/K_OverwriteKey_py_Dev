# task_02_trigger_set_source_and_naming

## 目的

trigger_set まわりの 2 つの既存不整合を解消する（暫定仕様 05 §6・§7。[idea_05](../../../backlog/idea_05_trigger_set_source_path_inconsistency.md) の内包）。

1. **source_path の分断を接続する**: 保存経路の読み手が**存在しない App 属性**
   `getattr(self._app, "_trigger_set_source_path", "")` を見ており、書き手 `dirty_tracker.trigger_set_source_path`
   と繋がっていない。読み手を `dirty_tracker` へ寄せて keymap / sequence と対称にする（§7 案1）。
2. **config_root 内の trigger_set 既定パスを keymap_set 名基準にする**: 現状は全 keymap_set が固定
   `user/trigger_sets/default.json` を共有・上書きする（暫定仕様 §1 現状監査 / Phase α の残課題）。
   keymap_set の stem 基準へ変更する（§6・受入条件 8）。

- レイヤ制約: **presentation（`config_io/trigger_set_file_io.py`）+ application（`config_service.py` の保存先決定）**。
  domain 不変・**スキーマ不変**（JSON のキーは増減しない。変わるのは保存先ファイル名のみ）。
- **本タスクは挙動変更を含む**（既存の特性テストが旧挙動を固定しているため、下記の対象テストを更新する）。

## 対象範囲（presentation + application・保存先決定まで）

### 1. `keyseq/presentation/controllers/config_io/trigger_set_file_io.py` — source_path の接続

| 箇所 | 変更内容 |
|---|---|
| `save_trigger_set_file`（`:10`） | `getattr(self._app, "_trigger_set_source_path", "")` → **`self._app.dirty_tracker.trigger_set_source_path`** を読む |
| `save_trigger_set_file`（`:11-13`） | 「読込で持ってきたトリガー一覧です。別名で保存しますか？」の `askyesno` 分岐を**削除する**（§7: 旧個別ダイアログは復活させない。統合ダイアログ〔task_05〕と参照元記録〔task_01〕へ寄せる） |
| `save_trigger_set_file_as`（`:22`） | 同じく `dirty_tracker.trigger_set_source_path` を読む（初期ディレクトリと初期ファイル名の算出に使われる） |

**接続後の `save_trigger_set_file` の挙動**（keymap / sequence と対称）:
- source_path **あり** → 確認なしでそのパスへ上書き（`save_trigger_set_to_path`）
- source_path **なし** → `suggest_json_path(preferred_trigger_sets_dir(), keymap_set_file_stem(), "trigger_set")` を
  初期値に `choose_save_path_with_collision` で決めてから保存（現状と同じ）

- `dirty_tracker.trigger_set_imported` は**残す**（読込由来かどうかの状態自体は有効で、書き込み側は現状のまま）。
  ただし本タスクで**唯一の読み手が消える**ため、task_05 のダイアログ表示で使うか否かを判断し、
  使わないなら task_07 の `/refactor_check` で撤去可否を判定する（**本タスクでは撤去しない**）。

### 2. `keyseq/application/config_service.py` — trigger_set 既定パスの keymap_set 名基準化

| 箇所 | 変更内容 |
|---|---|
| 定数（`:21`） | `TRIGGER_SET_RELATIVE_PATH = "user/trigger_sets/default.json"` を **`TRIGGER_SETS_RELATIVE_DIR = os.path.join("user", "trigger_sets")`** へ置き換える（旧定数の参照は `_build_split_save_payloads` の 1 箇所のみ。`tests` / `tests_ui` / `instructions/` からの参照は無いことを確認済み） |
| 新規 private | `_default_trigger_set_path(keymap_set_path, *, config_root, split_base_dir) -> str`。stem は `slugify_file_stem(os.path.splitext(os.path.basename(keymap_set_path))[0])`、空になる場合のフォールバックは **`"default"`**（レガシー既定名を維持するため）。`split_base_dir` があれば `<split_base_dir>/trigger_sets/<stem>.json`、無ければ `<config_root>/user/trigger_sets/<stem>.json` |
| `_build_split_save_payloads`（`:621-625`） | 上記ヘルパの戻り値を使う。`keymap_set_path` は同関数の引数として既に解決済みの絶対パスが渡っている |
| `hotkey_presets_path`（`:626-630`） | **変更しない**（暫定仕様 §6・§11: hotkey_presets は本フェーズで触らない） |

- `save_runtime_data` の `keymap_set_path` は空文字なら `_default_keymap_set_path()`（`user/keymap_sets/default.json`）へ
  解決済みのため、**既定構成では stem = `default` となり保存先は従来どおり `user/trigger_sets/default.json`**。
  ここが変わらないことが後方互換の要。

### 設計メモ / 制約

- **`_is_default_trigger_set_area`（`:773`）との整合**: sequence の保存先は trigger_set が
  `<config_root>/user/trigger_sets/` 配下かどうかで決まる。stem 基準にしてもディレクトリは変わらないため
  **sequences の保存先は現状維持**（`user/sequences/`）。この不変性をテストで固定すること。
- **`split_base_dir`（構成セット周辺へ保存する経路）も stem 基準にする**。§6 の本文は config_root 内の固定
  `default.json` を対象に書かれているが、目的（複数 keymap_set が同じ trigger_set ファイルを共有・上書きしない）は
  同一で、同じフォルダに複数構成セットを置いた場合に同じ衝突が起きるため。**hotkey_presets は据え置き**なので
  「trigger_set のみ変更」（指摘④）の範囲は守られる。
- **読込側は変更しない**。子の探索は keymap_set.json の `trigger_set_path` 索引を辿るため、既存の
  `default.json` を指す構成はそのまま読める（保存時に索引が新パスへ更新される）。
- runtime が持つ trigger_set の source_path を keymap_set 一括保存の書き込み先に反映するのは
  **task_03（保存計画）の担当**。本タスクは「source_path が無いときの既定名」だけを変える。
- 削除する `askyesno` 分岐は**現状デッド**（読み手が常に空文字のため到達しない）。
  接続によって初めて到達可能になるが、§7 の指示どおり**復活させずに削除**する。

## 含まない

- **保存計画（事前検証・依存関係・失敗時の旧索引維持）と、source_path を一括保存の書き込み先へ反映すること** → **task_03**
- **共有状況の判定（§5 の 4 状態）・既定ラジオ** → **task_04** / **統合保存ダイアログ** → **task_05**
- **keymaps / sequences の命名変更**（現行ルールのまま。暫定仕様 §6・指摘④）
- **hotkey_presets の命名・配置**（暫定 07 / phase 08）
- **複数 trigger_set を 1 keymap_set に持つ対応**（将来課題・§6）
- `dirty_tracker.trigger_set_imported` の撤去（上記のとおり task_05 / `/refactor_check` で判断）
- 正本 `spec_detail/` への反映 → **task_07**

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `../../../.venv/Scripts/python.exe`）を使う。

1. `-m compileall -q keyseq main.py tests_ui` → clean
2. `-m unittest discover -s tests` → fail 0（現在 97 件 + 新規追加分）
3. `-m unittest discover -s tests_ui` → fail 0（現在 85 件）
4. `-m tests.smoke_app` → pass
5. **旧挙動を固定している既存テストの更新**（実装に合わせて期待値を書き換える。**該当はこの 2 件のみ**）:
   - `tests_ui/test_config_io_characterization.py:449`
     `test_trigger_set_save_uses_collision_not_unreachable_import_prompt`
     — 「`dirty_tracker` の source_path はこの保存経路の読取先ではない」という**旧不整合を固定**しているテスト。
     接続後の期待値（source_path があれば衝突ダイアログを経ずにそのパスへ保存 / `askyesno` は呼ばれない）へ
     書き換え、テスト名も実態に合わせる（例: `test_trigger_set_save_uses_dirty_tracker_source_path`）。
     **source_path が空のときは従来どおり `choose_save_path_with_collision` を通る**ケースも残すこと。
   - `tests/test_config_service.py:269` `test_save_runtime_data_records_all_parent_refs`
     — keymap_set を `main.json` に保存しており、trigger_set の期待パスが `user/trigger_sets/default.json`。
     **`user/trigger_sets/main.json` へ更新**（sequence の `_parent_refs` の期待値も追従）。
6. **新規テストの追加**:
   - `tests/test_config_service.py`: keymap_set `gaming.json` で保存 → `user/trigger_sets/gaming.json` が作られ、
     `keymap_set.json` の `trigger_set_path` がそれを指す / **keymap_set が既定（`default.json`）なら
     従来どおり `user/trigger_sets/default.json`**（後方互換）/ **異なる 2 つの keymap_set を同じ config_root へ
     保存しても trigger_set が互いに上書きされない**（受入条件 8）/ stem が空になる名前でも `default` へ落ちる /
     **sequences の保存先が `user/sequences/` のまま**変わらない（`_is_default_trigger_set_area` の不変性）
   - `tests_ui/test_config_io_characterization.py`: `save_trigger_set_file_as` が
     `dirty_tracker.trigger_set_source_path` を初期ディレクトリ / 初期ファイル名の算出に使うこと
7. `-m unittest discover -s tests` の既存 `SaveLoadRoundTripTest.test_round_trip_preserves_content`
   （`user/trigger_sets/default.json` の存在を確認）が**修正なしで pass** すること
   ＝「既定構成では保存先が変わらない」の回帰確認。

## 完了条件

- 上記確認 1〜7 がすべて pass（実測は `verifier` が `.venv` で行う。Codex の自己申告は完了根拠にしない）。
- **`reviewer` 採用**（観点: 仕様適合性〔§6・§7 の範囲を超えて keymaps / sequences / hotkey_presets の命名に
  波及していないか〕・責務分離〔保存先決定が application に閉じているか〕・不要変更〔読込側や索引の構造を
  変えていないか〕・チェック漏れ〔更新したテストが旧不整合の再発を検出できる形になっているか〕）。
- **実機目視は task_06 でまとめて実施**（本タスクでは不要）。
