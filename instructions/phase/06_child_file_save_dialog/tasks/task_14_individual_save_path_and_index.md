# task_14_individual_save_path_and_index

## 目的

個別保存 3 経路（トリガー一覧 / キーマップ / 出力シーケンス）の 2 つの実バグを直す
（暫定仕様 05 **v0.5-J** / **v0.5-N**・§7・§8・受入条件 **19**・**23**）。

1. **【J】相対 `source_path` を解決せずに書き込む**。runtime の source_path は config_root 相対で
   保持されるため（`config_service.py:544` / `:807` / `:818` / 読込時の索引文字列そのまま）、
   個別保存がそれをそのまま `repository.save_json` へ渡すと **cwd 基準**で解決され、
   **プロジェクトルート直下に `user/` ツリーを作る**（2026-08-01 実機で発生）。
2. **【N】個別「別名保存」で上位の索引が追随せず、未保存にもならない**。
   `save_trigger_set_to_path` / `save_keymap_to_path` は tracker と runtime しか更新せず
   `sync_dirty_state()` しか呼ばないため、keymap_set の索引は旧パスのまま・保存も促されず、
   **再起動で旧ファイルが読まれる**。

レイヤ制約: **application（`config_service.py` の個別保存 3 API）+ presentation（`config_io/` の 3 ファイル）**。
**domain 不変・スキーマ不変**（JSON の表記規約は変えない）。仕様変更ではなく**バグ修正**。

## 対象範囲（application の個別保存 API + presentation の個別保存 3 経路 限定）

### 1. `keyseq/application/config_service.py` — stored / resolved の分離（v0.5-J）

対象は個別保存の 3 API のみ。**一括保存経路（`save_runtime_data` / `_build_*_payloads`）は触らない**
（既に config_root から解決済み）。

| API | 現状 | 変更 |
|---|---|---|
| `save_keymap_file`（144-172） | 引数 `path` をそのまま `save_json` と `target_path` と戻り値の `INTERNAL_KEYMAP_SOURCE_PATH` に使う | 下記の分離を適用 |
| `save_sequence_file`（187-208） | 同上（`INTERNAL_SEQUENCE_SOURCE_PATH`） | 同上 |
| `save_trigger_set_file`（227-280） | `path` を `save_json` と `_build_trigger_set_payloads(trigger_set_path=os.path.abspath(path))` に使う | 同上（`abspath` ではなく config_root からの解決に置き換える） |

分離の規約:

- **resolved（絶対）** = `_resolve_config_relative_path(path, config_root)`。
  **`repository.save_json` の引数**と、`_parent_refs_for_save` / `_build_*_payload` の
  **`target_path` / `trigger_set_path`**（＝ canonical 比較・既定領域判定に使う値）へ渡す。
- **stored** = `to_config_relative_or_absolute(resolved, config_root)`。
  **戻り値の `source_path`**（`INTERNAL_KEYMAP_SOURCE_PATH` / `INTERNAL_SEQUENCE_SOURCE_PATH` /
  `save_trigger_set_file` が triggers に載せる `INTERNAL_SEQUENCE_SOURCE_PATH`）へ入れる。
- **resolved を source_path・`_parent_refs`・索引へ代入しない**（v0.3-B「canonical は比較専用」と同じ分離。
  `normcase` 済みの `canonical_path` の戻り値は従来どおり比較にしか使わない）。
- `config_root` が空文字で呼ばれた場合は現状どおり（解決せずそのまま）。既存の呼び出し元は
  すべて `config_root` を渡しているため、**引数追加やシグネチャ変更はしない**。

### 2. `keyseq/presentation/controllers/config_io/` — 上位の dirty 化（v0.5-N）

**「子の `source_path` が変わったとき**（別名保存 / 保存先未確定からの初回保存）**だけ**」上位を dirty 化する。
判定は保存前の source_path と保存後の stored 値を `config_service.canonical_path` で比較する
（**素の文字列比較を使わない**）。

| ファイル | 対象 | 変更 |
|---|---|---|
| `trigger_set_file_io.py`（`save_trigger_set_to_path`:36-57） | 上位 = keymap_set | パスが変わったとき `dirty_tracker.set_dirty(True)`（＝ `config_dirty` を立てる）。完了メッセージへ索引追随の一文を足す |
| `keymap_file_io.py`（`save_keymap_to_path`:62-80） | 上位 = keymap_set | 同上 |
| `sequence_file_io.py`（`save_sequence_to_path`:54-72） | 上位 = trigger_set | **現状の `mark_trigger_set_dirty()` を維持**（既に追随する）。パスが変わったときのみメッセージの一文を足す |

- 通知文言は 3 経路で揃える（例: 「構成セットを保存すると索引が追随します。」）。
  **`messagebox.showinfo` の本文とフラッシュメッセージの両方**に載せる（既存の書式に合わせる）。
- **上位を自動保存しない**（v0.5-N の確定事項）。`save_keymap_set` 等をここから呼ばない。
- パスが変わらない上書き保存では **dirty 化も通知もしない**（既存挙動のまま）。

### 3. テスト

| 追加先 | # | 内容 |
|---|---|---|
| `tests/`（application） | 1 | `save_keymap_file` / `save_sequence_file` / `save_trigger_set_file` に **config 相対パス**を渡すと、**`config_root` 配下**に書かれる（cwd 直下に作らない）。テスト中に `os.chdir` で cwd を config_root 以外へ移し、**書かれた実ファイルのパスで判定**する（cwd は `try/finally` で復元） |
| 〃 | 2 | 同じ呼び出しの戻り値の `source_path` が **相対表記のまま**（絶対パスへ置換されていない）。`_parent_refs` も従来どおりの表記 |
| 〃 | 3 | **絶対パス**を渡したときの挙動が従来と同じ（回帰なし） |
| `tests_ui/` | 4 | **受入条件 19**: 初回起動相当（keymap_set 索引由来の相対 `trigger_set_source_path`）の状態で個別「トリガー一覧を保存」を実行すると、`config/user/trigger_sets/` 配下へ書かれ、**cwd 直下に `user/` が作られない** |
| 〃 | 5 | **受入条件 23**: 個別「トリガー一覧を別名で保存」/「キーマップを別名で保存」の後に `dirty_tracker.has_unsaved_changes()` が True になり、続けて keymap_set を保存すると索引（`trigger_set_path` / keymaps の索引）が**新パス**を指す |
| 〃 | 6 | **回帰**: 保存先が変わらない上書き保存では上位が dirty 化しない。sequence の個別保存は従来どおり `trigger_set_dirty` が立つ |

- `tests_ui` の 3 ファイルにある **fail-fast ガード**（`showerror` / A2 / 依存確認が呼ばれたら `AssertionError`）を
  壊さないこと。成功パスの `showinfo` は patch して**本文に通知文が含まれること**をアサートする。

### 設計メモ / 制約

- 解決の入口を散らさない。application 側の 3 API 内で「先頭で resolved / stored を決める」形にまとめ、
  presentation 側では**パス解決をしない**（presentation が `os.path.abspath` で解決する実装にしない）。
- `save_trigger_set_file` の `os.path.abspath(path)`（248 行）は、相対パスのとき cwd 基準になるため
  **必ず解決値へ置き換える**。ここが `_is_default_trigger_set_area` の判定に効いており、
  誤ると sequence が `<cwd>/user/trigger_sets/sequences/` へ落ちる（本バグの拡大経路）。
- `save_trigger_set_file` が **全 sequence を書く**現挙動は本タスクでは変えない（**task_15**）。
  本タスクは「どこへ書くか」だけを直す。
- `save_trigger_set_file_as` / `save_selected_*_as` の `initialdir` も相対 source_path を
  `os.path.abspath` している（cwd 基準）。**ダイアログ初期位置のみの影響**だが、
  同じ解決を通すよう合わせてよい（挙動変更はダイアログの初期ディレクトリのみ）。

## 含まない

- **個別「トリガー一覧を保存」の保存計画対応・子ダイアログ（v0.5-K）— task_15**。
  `save_trigger_set_file` の「全 sequence を書く」挙動と `SavePlan` 引数の追加はそこで行う。
- **一覧ダイアログの初期省略計算・マウスホイール（v0.5-L/M）— task_16**。
- **正本 `spec_detail/` への反映 — task_10**。
- 一括保存経路（`save_runtime_data` / `_build_split_save_payloads`）の変更（**触らない**）。
- 上位の自動保存・索引の即時更新（v0.5-N で不採用。dirty 化のみ）。
- 個別保存ボタンの統合（暫定仕様 §11）/ `source_path` の表記規約そのものの変更。

## 確認

`.venv` の python で実行する（worktree ルートから `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean
2. `-m unittest discover -s tests` が全 pass（現行 138 件 + 追加分）
3. `-m unittest discover -s tests_ui` が全 pass（現行 136 件 + 追加分）・**完走する**
4. `-m tests.smoke_app` が pass
5. **受入条件 19・23**: 上記テスト 1〜6 が pass
6. 既存の特性テスト（保存 JSON のバイト列比較）を**緩めずに** pass すること

## 完了条件

- 上記確認 1〜6 が pass・**reviewer 採用**。
- 実機目視（初回起動直後にトリガー一覧から保存して `config/` 配下に書かれること）は
  **task_10 の前にユーザーがまとめて実施**する。本タスクでは実施しない。
