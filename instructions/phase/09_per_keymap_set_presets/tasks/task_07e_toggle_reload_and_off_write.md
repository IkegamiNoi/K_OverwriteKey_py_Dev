# task_07e_toggle_reload_and_off_write

## 目的

**プリセットマネージャのチェック切替で一覧を切替先から読み直し、OFF での OK もグローバルへ書く**
（暫定仕様 08 **§2【I】【E】【H2 撤回】【R】/ §3-3 / §3-4**〔v0.8 で改訂〕・受入条件 **13**）。

task_07 の実機目視（項目 7）で発現した不具合の是正。v0.7 までは**トグルで一覧を差し替えなかった**
ため、**OFF → ON でグローバルの内容が個別ファイルへ上書き**された（チェックは保存先の選択なのに、
書かれる内容は直前に表示していた**別ファイル**の内容、という非対称が原因）。

**レイヤ制約**: **presentation 中心**（`dialogs.py` / `app.py`）+ **application は読み出し API の
呼び出しと組込既定の取得のみ**。**解決順序（task_03）不変・保存先算出（task_04 / task_05c）不変・
【O4】ガード（task_07b）不変・スキーマ不変・プリセット単独の注入 API は作らない**。

## 対象範囲

### 1. `keyseq/presentation/dialogs.py` — `PresetManagerDialog` のトグル

現在チェックの `command` は `_update_source_labels`（`:445`）だけを呼び、**一覧（`_temp`）を触らない**。
**一覧の差し替えを足す**。

- **OFF → ON**: **記録済みの個別パスから読む**（**読み出し用の解決** = task_07d で分けたもの。
  config 外も対象）。
  - **読めたらその内容へ差し替える**。
  - **読めない / パス未設定なら現在の一覧を引き継ぐ**【E】（＝初回 ON のコピー導線。差し替えない）。
- **ON → OFF**: **グローバルから読む**（`load_global_hotkey_presets`）。
  - **読めたらその内容へ差し替える**。
  - **読めなければ「組込既定」へ差し替える**（**現在の一覧を持ち越さない**）。
    → 個別の内容が OFF 状態へ持ち越されないため、**グローバルへ流出する経路が無くなる**。
    組込既定は **application 経由で取得する**（`new_default_data()` の `hotkey_presets` 相当。
    **presentation から `domain` の定数を直接読まない**）。
- **破棄確認**: **差し替えによって編集内容が失われる場合だけ** `messagebox.askyesno` で確認する。
  - **判定は「直近に読み込んだ一覧」との比較**（ダイアログを開いた時点、または直前のトグルで
    差し替えた内容）。**未編集なら確認しない**。
  - **引き継ぐ場合（OFF → ON で読めない）は破棄が起きないので確認しない**。
  - **キャンセル（No）なら `individual_var` を元の値へ戻し、一覧・保存先表示・何も変えずに戻る**。
- 差し替え後に `_refresh()` と `_update_source_labels()` を呼ぶ。
- **`_temp` を差し替えても runtime（`parent.data`）は変えない**。反映は **OK のときだけ**。
  **キャンセルで閉じた場合、runtime・ファイル・フラグ・dirty のいずれも変わらない**【J】。

### 2. `keyseq/presentation/app.py` — `save_hotkey_presets`（`:416-458`）

**`current_individual and not target_individual` の特別分岐（`:420-428`）を削除**し、
**OFF も通常のグローバル書き込み経路へ通す**（【H2】撤回）。

- OFF での OK は **表示中の一覧（引数 `presets`）をグローバルへ書き**、成功時に runtime へ反映する。
  - **書き込みに失敗したら従来どおり `False`**（ダイアログを閉じない・runtime を変えない）。
- **フラグ変更時の dirty（`:455-457`）と、`hotkey_presets_path` の値が変化したときの dirty
  （v0.6・`:451-454`）は現状のまま維持**する。
- **ON 側の経路（【O3】のリダイレクト・【O4】の拒否）は一切変えない**。

### 3. `keyseq/presentation/dialogs.py` — 表示（`format_preset_manager_source_labels`）

**OFF でグローバルが読めない状態**（トグル直後を含む）に、
**「グローバルを読み込めませんでした。組込既定を表示中（OK でグローバルを作成します）」**旨を出す。
既存の `builtin` 表示（`:47-48`）との重複・矛盾が出ないように整理する（**文言の重ね出しをしない**）。

### 設計メモ / 制約

- **書き手は 1 本のまま**（`PresetManagerDialog.on_ok` → `App.save_hotkey_presets` →
  `HotkeyPresetsIo.write_presets`）。**トグルは読むだけ**で、**ファイルを作らない・消さない**
  （実体は OK で初めて作る【H】）。
- **プリセット単独の注入 API を作らない**（正本 §5.8.8 の注記。トグルの読み直しは
  **ダイアログ内の表示更新**であり、runtime への供給点を増やさない）。
- **新しいモーダルを増やすため、`tests_ui` の fail-fast ガードを更新する**
  （`test_child_save_dialog` / `test_config_io_characterization` /
  `test_config_io_characterization_keymap_set_startup` / `test_app_ui_flows` の `setUp`。
  **`messagebox.askyesno` を patch し忘れるとテストが失敗ではなく永久待機になる**。
  session.md の resume_hints・Codex 敵対的レビュー Medium 5）。
- **`AppUiFlowsTest` は `setUpClass` で App を共有する**ため、`has_unsaved_changes()` を
  **絶対値で assert しない**（前後の変化 / `set_dirty` の呼出有無で見る）。
- **`_keymap_set_saved` が false（未保存）ならチェックは無効化されたまま**【F】。
  本タスクでその契約を変えない。

## 含まない

- **残置パスの遮断**（v0.8【§3-5】）→ **task_07c**（**本タスクは 07c / 07d の完了後に着手する**）
- **config 外パスの読み出し許容**（v0.8【O2】）→ **task_07d**（本タスクは読み出し用の解決を**使う**だけ）
- プリセット編集 UI の刷新（追加/編集/削除/並べ替えの操作体系）→ 暫定仕様 §6 でスコープ外
- 破損グローバルの**退避・バックアップ**（組込既定で上書きする。暫定仕様 §6 でスコープ外）
- 正本 `spec_detail/` への反映・`codebase_map.md` 更新 → **task_08**

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **229** + 07c / 07d 追加分 + 本タスク追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **206** + 同上）
- `-m tests.smoke_app` が pass

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests_ui/test_app_ui_flows.py`**（**モーダルは必ず patch する**）:

1. **OFF → ON で個別が読める**: 一覧が**個別ファイルの内容**へ差し替わり、**OK 後も個別ファイルが
   グローバルの内容で上書きされない**（＝実機目視 項目 7 の再現）。
2. **OFF → ON で個別が無い**: 一覧が**そのまま引き継がれ**【E】、OK で**個別ファイルが新規作成**される。
3. **ON → OFF**: 一覧が**グローバルの内容**へ差し替わり、**OK でグローバルへ書かれる**
   （【H2】撤回。`hotkey_presets_individual` が false になり dirty が立つ）。
4. **ON → OFF でグローバルが読めない**: 一覧が**組込既定**へ差し替わり、**OK でグローバルが
   組込既定として作成される**。**個別の内容がグローバルへ書かれない**。
   **閉じて開き直してから OK しても同じ結果**（Codex 敵対的レビュー High 1 の遷移）。
5. **破棄確認**: 一覧を編集してからトグルすると `askyesno` が呼ばれる。
   - **No** … `individual_var` が**元の値へ戻り**、一覧が**編集内容のまま**（差し替えられない）。
   - **Yes** … 差し替えられる。
   - **未編集のトグルでは `askyesno` が呼ばれない**。
6. **キャンセル**: トグルして一覧が差し替わった後にキャンセルで閉じると、
   **`app.data` のプリセット・フラグ・パスが不変**・**ファイルが書かれない**・**dirty が立たない**【J】。
7. **未保存 keymap_set ではチェックが無効**（既存契約が壊れていないこと）。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: **個別の内容がグローバルへ流出する経路が
  残っていない**か〔トグル / 再オープン / 読み直し失敗の組合せ〕/ **トグルが runtime を変更していない**か
  〔反映は OK のみ〕/ **書き手 1 本**が維持されているか / **プリセット単独の注入 API を作っていない**か /
  ON 側の【O3】【O4】を変えていないか / **モーダル追加に対する fail-fast ガードの更新漏れ**が無いか /
  後続タスク（task_08）の先取りがないか）。
- **実機目視は task_07 の観点リスト（項目 5 / 7）でまとめて実施**する（本タスクでは行わない）。
- 3 タスク（07c / 07d / 07e）完了後、**task_07 の通し再実測と実機目視 16 項目へ戻る**。
