# task_07g_overwrite_confirm_adopt_existing

## 目的

**上書き確認【S】を 3 択（上書きする / 既存を読み込む / キャンセル）にする**
（暫定仕様 08 **§2【S】/ §3-4**〔**v0.10**〕・受入条件 **21**、19 は文言のみ改訂）。

task_07 の実機目視（項目 17）でユーザーが検出。v0.9 は 2 択だったため、
**既存ファイルの内容を採る手段が UI に無かった**（記録パスが空だと【I】のトグル読み直しが空振りし、
**`hotkey_presets_path` が記録されるのはプリセットの保存が成功した後**なので、確認を断り続ける限り
その実体には到達できない＝「上書きする」か「専用化を諦める」しか残らない）。

**レイヤ制約**: **presentation 中心**（`hotkey_presets_io.py` / `app.py` / `dialogs.py`）+
**application は「判定と同時に保存先の実体の内容を返す」形への拡張のみ**。
**解決順序（task_03）不変・保存先算出（task_04 / task_05c）不変・【O3】【O4】不変・
【I2】（task_07f）不変・スキーマ不変・プリセット単独の runtime 注入 API を作らない**。

## 対象範囲（presentation 中心 / application は戻り値の拡張のみ）

### 1. `keyseq/application/config_service/`（`split_loading.py` + `__init__.py`）

task_07f で追加した上書き確認の要否判定を、**判定と既存内容を同時に返す形へ拡張する**
（**同じファイルを 2 回読まないため**）。

- 例: `describe_individual_hotkey_presets_overwrite(service, stored_path, loaded_presets, *, config_root)`
  が `{"conflict": bool, "existing": list | None}` を返す（`existing` は**正規化後**。
  実体が無い / 読めない場合は `None`）。
- **判定規則は v0.9 のまま変えない**（実体なし → `conflict=False` / `loaded_presets=None` →
  `conflict=False` / 読めない → `conflict=True` / 内容不一致 → `conflict=True`）。
- **`ConfigService` の委譲メソッドを更新する**（presentation から `split_loading` を直接 import しない）。
  既存の bool 版が不要になるなら**残さず置き換える**（互換レイヤーを作らない）。

### 2. `keyseq/presentation/controllers/config_io/hotkey_presets_io.py`

**3 択ダイアログ**を追加する（`messagebox` の 2 択では表現できないため、
**`child_save_dialog.py` と同型の自作 `Toplevel`**）。

- ボタン文言は **「上書きする」/「既存を読み込む」/「キャンセル」**。戻り値は
  `"overwrite" | "adopt" | "cancel"` 相当の 3 値。
- **`existing` が `None`（実体が読めない）ときは「既存を読み込む」を出さない**（2 択にする）。
- 本文には**保存先パス**と、**既存ファイルの内容が表示中の一覧と異なる**旨を出す。
- **モーダルとして開き、閉じるまで待つ**（`transient` / `grab_set` / `wait_window` の既存作法に合わせる）。
  **× で閉じた場合は「キャンセル」扱い**。

### 3. `keyseq/presentation/app.py` — `save_hotkey_presets`

**判定順序（【O3】→【O4】→【S】→ 書き込み）を保ったまま、3 値を扱えるようにする**。

- 衝突時の選択と、選択が `adopt` だった場合の**一覧の差し替えはダイアログ（呼び出し元）が行う**。
  `App` と `PresetManagerDialog` は**どちらも presentation** なので、
  **`save_hotkey_presets` へ「衝突時ハンドラ」を渡す形**にしてよい
  （例: `on_overwrite_conflict: Callable[[str, list | None], str]`。既定 `None` = 従来どおり書き込む）。
- **`adopt` / `cancel` はどちらも `False` を返す**（`write_presets` へ進まない・
  `data`・dirty・ファイルのいずれも変更しない・ダイアログを閉じない）。
- **`overwrite` のときだけ従来どおり書き込む**。

### 4. `keyseq/presentation/dialogs.py` — `PresetManagerDialog`

- `on_ok` から**衝突時ハンドラを渡す**。ハンドラは `hotkey_presets_io` の 3 択を呼び、
  **`adopt` を選ばれたら `_temp` と `_loaded_temp` を `existing` で差し替え、`_refresh()` と
  `_update_source_labels()` を呼ぶ**（**保存しない・閉じない**）。
- **`adopt` で追加の破棄確認は出さない**（明示的な選択のため）。
- **`_loaded_temp` も更新する**ことで、以後のトグル破棄確認【I】の比較基準と、
  次の OK での【S】判定（内容一致 → 確認なし）が正しく揃う。

### 設計メモ / 制約

- **「既存を読み込む」→ 改めて OK** で確認が出ずに保存が通ること（内容一致で `conflict=False`）が
  この設計の要。**adopt 時に即保存しない**（ユーザーが内容を確認してから確定できるようにする）。
- **判定は application・UI と文言は presentation**（task_07b 以降の方針）。
- **新しいモーダルを増やすため、`tests_ui` の fail-fast ガードを確認する**。今回は
  **`messagebox` ではなく自作 `Toplevel`** のため、**既存の `messagebox` ガードでは捕捉できない**。
  テストは**このダイアログを直接 patch する**か、**ハンドラを差し込んで** 3 値を返させること
  （**実 UI をモーダル表示させたままにしない**。ハングの温床）。
- `AppUiFlowsTest` は `setUpClass` で App を共有するため、`has_unsaved_changes()` を
  **絶対値で assert しない**。
- **【grab は対象外】ネストしたモーダルを閉じても親（マネージャ）の grab は復元されない**が、
  これは**既存の「追加」「編集」（`PresetDialog`）と同じ挙動**であり、
  **アプリ全体の課題として idea へ分離した**（v0.10 の敵対的レビュー High 2 = 除外）。
  **本タスクで `grab_set` を足さない**（新経路だけ挙動が不揃いになるため）。

## 含まない

- **【S】の発火条件そのものの変更**（v0.9 のまま。実体なし / 比較基準なし → 確認なし、
  読めない → 確認あり、内容不一致 → 確認あり）
- **トグル ON 時にも既存の読み込みを尋ねる案**（2026-08-15 にユーザーが 3 択案を選択・**対象外**）
- **【I2】を ON へ拡張する**こと（v0.9 で対象外と確定）
- **ネストしたモーダルを閉じた後の grab 復元**（既存の「追加」「編集」を含むアプリ全体の課題。
  2026-08-15 ユーザー判断で**除外し idea へ起票**）
- **adopt 後の再 OK までに保存先が外部から変更された場合の再確認 / 中止契約**
  （受入条件 21 の前提外。**確認と書き込みの間の競合は v0.9 で除外済み**）
- 正本 `spec_detail/` への反映・`codebase_map.md` 更新・暫定仕様の凍結 → **task_08**

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **242** + 本タスク追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **220** + 本タスク追加分・**ハングしないこと**）
- `-m tests.smoke_app` が pass

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests/test_config_service.py`**:

1. 判定 API が **`conflict` と `existing` を同時に返す**（実体なし → `False` / `None`、
   内容一致 → `False` / 正規化後の内容、内容不一致 → `True` / 内容、
   破損 → `True` / `None`、`loaded_presets=None` → `False`）

**`tests_ui/test_app_ui_flows.py`**（**3 択ダイアログは patch して 3 値を返させる**）:

2. **`overwrite`** … 従来どおり書き込まれる（`save_hotkey_presets` が `True`）
3. **`cancel`** … `False`・**ファイル / `data` / フラグ / パス / dirty がすべて不変**
4. **`adopt`** … `False`・**ファイルが書かれない**・`data` と dirty が不変で、
   **ダイアログの一覧と `_loaded_temp` が保存先の実体の内容へ差し替わる**
5. **`adopt` の直後に再度 OK** … **確認が出ずに保存が通り**、
   **ファイルの内容が既存のまま変わらない**（受入条件 21）
6. **保存先が読めない（破損）** … 3 択ダイアログへ **`existing=None`（＝「既存を読み込む」を出さない）**
   が渡ること
7. 確認が出ないケース（初回 ON で実体なし / 通常の ON 編集 / OFF での OK）が**従来どおり**であること

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: **3 値の扱いが `adopt` / `cancel` とも
  「書き込まない・閉じない・不変」を満たす**か / **`adopt` 後の再 OK で確認が出ない**か
  〔`_loaded_temp` の更新漏れが無いか〕/ 判定=application・UI=presentation の分離 /
  **【O3】【O4】の順序と挙動が不変**か /【I2】とトグル（task_07e / 07f）の契約を壊していないか /
  **自作モーダルがテストでハングしない**形になっているか / task_08 の先取りが無いか）。
- **実機目視は task_07 の項目 17 を差し替えて実施**する（本タスクでは行わない）。
