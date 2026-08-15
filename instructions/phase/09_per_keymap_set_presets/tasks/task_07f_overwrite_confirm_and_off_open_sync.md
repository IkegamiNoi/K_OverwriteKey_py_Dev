# task_07f_overwrite_confirm_and_off_open_sync

## 目的

**個別プリセットへ書く直前の上書き確認【S】と、OFF でマネージャを開いた時点の一覧確定【I2】を実装する**
（暫定仕様 08 **§2【S】【I2】/ §3-3 / §3-4**〔**v0.9**〕・受入条件 **19 / 20**）。

task_07 のフェーズ完了判定前レビュー（`deep-reviewer` 指摘1・2）で見つかった 2 経路の是正。
v0.8 の「切替先を読んでから書く」という保証が**トグル経路にしか無く**、
①**記録パスが空のままの ON**（別名保存で既存の構成セットを上書きした後など）で既定保存先の実体が
無警告に置き換わる ②**OFF で開いてそのまま OK** すると runtime の一覧がグローバルへ書かれる、
の 2 つが残っていた。

**レイヤ制約**: **application は「上書き確認の要否判定」と「指定パスの読み出し」を追加するのみ**・
**presentation（`dialogs.py` / `app.py` / `hotkey_presets_io.py`）が確認モーダルと初期化を持つ**。
**解決順序（task_03）不変・保存先算出（task_04 / task_05c）不変・【O3】リダイレクトと【O4】ガード
（task_07b）不変・スキーマ不変・プリセット単独の runtime 注入 API を作らない**。

## 対象範囲（application は判定 API の追加のみ / presentation 中心）

### 1. `keyseq/application/config_service/split_loading.py`（+ `__init__.py` の委譲）

**指定された保存表記パスの内容と、渡された一覧を比較して「上書き確認が要るか」を返す関数**を追加する。

- 追加する判定（名前は既存の `individual_hotkey_presets_save_rejection_reason` に揃える。例:
  `individual_hotkey_presets_overwrite_conflict(service, stored_path, loaded_presets, *, config_root) -> bool`）。
  - **`stored_path` を `resolve_config_path` で解決し、実体が無ければ `False`**（＝確認不要）。
  - 実体があれば `load_hotkey_presets_file` で読む（**正本 §5.10.2 の正規化を通った結果**）。
    - **読めない（`None`）… `True`**（破損。安全側で確認する）
    - **読めた … `loaded_presets` と一致しなければ `True` / 一致すれば `False`**
  - **`loaded_presets` が `None` なら `False`**（比較基準が無い＝確認しない。§3-3）。
  - **比較は正規化後の値どうし**で行う。**パスの canonical 化は行わない**（【O4】と役割を混ぜない）。
- `ConfigService`（`config_service/__init__.py`）へ**委譲メソッド**を足す
  （task_07e で `load_individual_hotkey_presets` を足したのと同じ形。**presentation から
  `split_loading` を直接 import しない**）。

### 2. `keyseq/presentation/app.py` — `save_hotkey_presets`

**引数に「直近に読み込んだ一覧」を受け取り、【O4】拒否の後・書き込みの前に確認を挟む**。

- シグネチャ: `save_hotkey_presets(self, presets, *, individual=None, loaded_presets: list | None = None)`。
  **既定 `None`（＝確認しない）**。呼び出しを増やさない（**本タスクで渡すのは
  `PresetManagerDialog.on_ok` の 1 箇所のみ**）。
- 判定順序は **【O3】寄せ（`resolve_hotkey_presets_save_path`）→【O4】拒否 → 【S】確認 → `write_presets`**。
  - **`target_individual` が真のときだけ**判定する（OFF ＝ グローバルへの書き込みは対象外）。
  - 確認が必要なら `hotkey_presets_io` の確認モーダルを呼び、**「いいえ」なら `False` を返す**。
    このとき **`data`・dirty・ファイルのいずれも変更しない**（【O4】拒否と同じ契約 =
    `write_presets` へ進まない）。
- **既存の dirty 規則（`hotkey_presets_path` の値変化・フラグ変化）は変更しない**。

### 3. `keyseq/presentation/controllers/config_io/hotkey_presets_io.py`

**確認モーダルを追加**（**プリセット保存系のモーダルはこのファイルへ集約**する既存方針。task_07b）。

- 例: `confirm_overwrite(self, *, stored_path: str) -> bool`。`messagebox.askyesno` を使い、
  **保存先パスと「既にプリセットファイルがあり、内容が異なる」旨**を出す。
- **戻り値をそのまま可否として使う**（判定は application・文言は presentation）。

### 4. `keyseq/presentation/dialogs.py` — `PresetManagerDialog`

- **`__init__` で OFF のときだけ一覧を表示元へ合わせる**【I2】。
  - `_individual_state` / `_displayed_source` を求めた後、**チェックが OFF なら**
    既存の `_toggle_preset_replacement(False)` と**同じ解決**（グローバル → 読めなければ組込既定）で
    `_temp` / `_loaded_temp` を差し替える。**破棄確認は出さない**（開いた直後で編集が無いため）。
  - **ON のときは差し替えない**（【E】の「個別が読めなければその時点の一覧を引き継ぐ」を維持。
    別名保存でコピー先を共有した場合に旧ファイル由来の一覧が出るのは**許容**＝【S】が受け止める）。
  - 差し替えは**ダイアログ内の表示のみ**。**`parent.data` を変更しない**（反映は OK のときだけ）。
- **`on_ok`（`:681` 付近）で `loaded_presets=self._loaded_temp` を渡す**
  （＝ダイアログを開いた時点、またはトグルで差し替えた内容。**編集後の `_temp` を渡さない**）。

### 設計メモ / 制約

- **【S】が発火する / しない の切り分け**（受入条件 19）。実装が満たすべき表:
  - **出ない**: 初回 ON で保存先に実体が無い / 記録パスのある再 ON・ON のままの内容編集
    （保存先の実体＝`_loaded_temp`）/ OFF での OK / 内容がたまたま一致している共有【M】
  - **出る**: 記録パスが空のままの ON で保存先に実体がある / **別名保存でコピー先の実体を採用した
    後の ON**【L】/ config 外パスからの移行【O2】/ 保存先が破損して読めない
- **③を「保存先パス ≠ 読み出し元パス」で実装しない**（v0.9 §4 却下記録 S-(E)）。
  別名保存【L】でコピー先の実体を採用すると**パスだけ新しくなり一覧は旧ファイル由来のまま**になるため、
  現在の状態から出どころを導くと**一致して素通りする**。**内容比較で判定する**。
- **確認と書き込みの間の競合（別プロセスによる作成・置換）は対象外**（v0.9 で除外。再検査しない）。
- **書き手は 1 本のまま**（`on_ok` → `App.save_hotkey_presets` → `HotkeyPresetsIo.write_presets`）。
  判定のための読み出しは**ファイルを作らない・消さない**。
- **新しいモーダル（`askyesno`）を増やすため、`tests_ui` の fail-fast ガードを確認する**
  （`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup` / `test_app_ui_flows` の `setUp`。
  **patch し忘れるとテストが失敗ではなく永久待機になる**）。
- **`AppUiFlowsTest` は `setUpClass` で App を共有する**ため、`has_unsaved_changes()` を
  **絶対値で assert しない**（前後の変化 / `set_dirty` の呼出有無で見る）。

## 含まない

- **正本 `spec_detail/` への反映**（**§5.10.4 の改訂**〔【I2】が「その状態で確定する」規定の例外に
  なること・【S】の追記〕を含む）・`codebase_map.md` 更新・暫定仕様 08 の凍結 → **task_08**
- **別名保存時に runtime の一覧を読み直す**案（v0.9 §4 却下記録 High の代替案）→ **採用しない**
- **【I2】を ON へ拡張する**こと（【E】を壊すため v0.9 で対象外と確定）
- 確認モーダルの**再検査 / 排他的作成**（v0.9 で除外）
- symlink / junction による containment 回避（**除外**・2026-08-10 / 08-15 の 2 回とも判断済み）
- プリセット編集 UI の刷新 → 暫定仕様 §6 でスコープ外

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **237** + 本タスク追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **213** + 本タスク追加分）
- `-m tests.smoke_app` が pass

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests/test_config_service.py`**（判定 API の単体）:

1. 保存先に**実体が無い** → `False`
2. 実体があり**内容が一致** → `False`
3. 実体があり**内容が異なる** → `True`
4. 実体があるが**壊れて読めない** → `True`
5. **`loaded_presets=None`** → `False`

**`tests_ui/test_app_ui_flows.py`**（**`askyesno` は必ず patch する**）:

6. **記録パスが空のままの ON + OK で保存先に実体がある** → 確認が出る。
   - **「いいえ」…ファイルの内容が不変・`app.data` のプリセット / フラグ / パスが不変・
     dirty が立たない・`save_hotkey_presets` が `False`**
   - 「はい」…書かれる
7. **通常の ON（記録パスあり）で内容を編集して OK** → **確認が出ない**・従来どおり保存される
8. **初回 ON で保存先に実体が無い** → **確認が出ない**・新規作成される
9. **OFF での OK** → **確認が出ない**（グローバルへの書き込みは対象外）
10. **別名保存でコピー先の実体を採用した後に ON で OK** → 確認が出る（【L】経路。受入条件 19）
11. **【I2】**: runtime に個別由来の一覧を持たせ、**グローバルが読めない状態で OFF のまま
    マネージャを開く** → 一覧が**組込既定**へ差し替わり、**OK でグローバルが組込既定として作られる**
    （**個別由来の内容が書かれない**）。**グローバルが読める場合はその内容**へ揃う
12. **【I2】は ON では効かない**: ON で開いたとき一覧が差し替えられない（【E】維持）
13. **キャンセル**: 【I2】で一覧が差し替わった後にキャンセルで閉じても、
    **`app.data`・ファイル・フラグ・dirty が不変**【J】

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: **受入条件 19 の発火 / 非発火の表を実装が
  満たしているか** / **「いいえ」で `data`・dirty・ファイルが完全に不変**か /
  判定が application・モーダルが presentation に分かれているか / **【O3】【O4】の順序と挙動が
  変わっていないか** / **【I2】が ON へ波及していない**か / トグル（task_07e）の契約を壊していないか /
  **fail-fast ガードの更新漏れ**が無いか / 後続タスク（task_08）の先取りがないか）。
- **実機目視は task_07 の観点リストへ項目を追加してまとめて実施**する（本タスクでは行わない）。
- 完了後、**task_07 の通し再実測と実機目視へ戻る**（追加観点 = 【S】の確認が出る / 出ない の各 1 件、
  【I2】の OFF 開き）。
