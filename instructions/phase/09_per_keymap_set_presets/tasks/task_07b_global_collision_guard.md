# task_07b_global_collision_guard

## 目的

**個別プリセットの保存先ガード（グローバル保護）を入れ、`hotkey_presets_path` の
payload 正規化を直す**（暫定仕様 08 **§2【G】【O4】（v0.7 で新設）/ §3-1 / §3-3**・
受入条件 **9 / 11 / 18**）。

task_07 の 2 本立てレビュー（`deep-reviewer` + `codex-adversarial-reviewer`）が**独立に同じ穴**を
検出したことを受けた是正。**設計の骨格は両レビューとも「正しく実現されている」判定**で、
作り直しは不要。

**レイヤ制約**: **application（判定）+ presentation（理由表示）**。
**読み出し側【O2】不変・解決順序（task_03）不変・【O3】のリダイレクト（task_05c）不変・
プリセットマネージャの表示契約（task_05）不変**。

## 対象範囲

### 1. `keyseq/application/config_service/` — 保存先ガード【O4】

**書き込み直前の最終関門**として、個別の保存先が次のいずれかに当たるかを判定する。
**【O3】のリダイレクトより後**（寄せた結果も判定対象）。

1. **保存先が `user/hotkey_presets/global/` 配下**（予約ディレクトリ違反）
2. **保存先がグローバルの読み先と同一ファイル**
   （`load_global_hotkey_presets_path` の解決値との比較）

- **判定は既存の比較専用 API を使う**（`is_path_within` / `canonical_path`）。
  **新しいパス判定を書かない**。`canonical_path` の戻り値を**保存値・表示値へ混ぜない**
  （比較専用。session.md の不変条件③）。
- **`global/` の場所は定数から導く**（`HOTKEY_PRESETS_RELATIVE_PATH` のディレクトリ部分。
  `"global"` の文字列を散らさない。task_01 / task_04 と同じ流儀）。
- **理由を区別できる形で返す**（例: `""`（問題なし）/ `"reserved_dir"` / `"global_conflict"`）。
  **文言は返さない**（文言は presentation）。
- 置き場と関数の形は実装者判断（`split_loading.py` か `save_path_resolution.py`）。
  **既存の `resolve_hotkey_presets_save_path` の戻り値と契約は変えない**
  （task_05c で 3 値タプルを畳んだ経緯があるため、**再びステータスを混ぜない**）。
- `ConfigService` へ委譲メソッドを追加する。

### 2. `keyseq/presentation/` — 拒否の実施と理由表示

- **`App.save_hotkey_presets`**（`app.py:416-` ）で、**`write_presets` を呼ぶ前**に §1 を判定し、
  当たったら**保存せずに `False` を返す**。
  - **`self.data` を一切変更しない**（プリセット・パス・フラグ）。**dirty を立てない**。
  - **戻り値 `False` によりダイアログは閉じない**（既存の成否契約。`dialogs.py` は**無変更**）。
  - **ON → OFF の確定（書き込みが起きない分岐）は対象外**【H2】。
    **OFF のままの保存（グローバルへ書く）も対象外**。
- **モーダルは `hotkey_presets_io.py` に集約する**（`app.py` に新しい `showerror` を増やさない。
  tests_ui の fail-fast ガードがこのファイルを見ているため）。
  **理由の 2 種類で文言を分ける**:
  - 予約ディレクトリ違反 … 「`global/` はグローバル用のため、専用プリセットの保存先にできない」旨
  - グローバルと同一 … 「保存先がグローバルライブラリと同じファイル。**`config.json` の
    `hotkey_presets_path` を `global/` 配下へ直す**」旨（＝**移行手順②への誘導**）
  - **どちらの文言にも現在の保存先パスを含める**。

### 3. `keyseq/application/config_service/split_payloads.py` — パス表記の正規化

`build_keymap_set_payload`（`:324`）の `hotkey_presets_path` を、**同じ payload の
`trigger_set_path` と同様に `to_config_relative_or_absolute` を通す**。

- 手編集・別実装由来の `user\hotkey_presets\main.json`・config 内絶対パスを
  **その表記のまま書き戻さない**（受入条件 11）。
- **OFF のときの空文字は空文字のまま**（【N】のパス保持と競合させない。
  `to_config_relative_or_absolute` に空文字を渡さないこと）。
- **保存 JSON のキー順を変えない**（`tests/test_save_plan.py::test_saved_keymap_set_json_keeps_stable_key_order`
  が固定している）。

### 設計メモ / 制約

- **読み出しはガードの対象外**。グローバルと同一ファイルでも**読めてしまってよい**
  （内容が同じなので実害がない）。**`build_runtime_data_from_split` /
  `describe_hotkey_presets_source` を変更しない**。
- **【O3】のリダイレクトを消さない**。順序は **無効 → 既定へ寄せる →【O4】判定**。
- **自動修復をしない**（別名へ逃がす・キーを消す・OFF へ強制切替はいずれも不可。
  §2【G】の「衝突を避けて別名へ逃がさない」と整合）。
- **`config_root` が空**のときは個別を選ばない既存挙動のままで、ガードに入らない。

## 含まない

- 読み出し側【O2】の変更 / `describe_hotkey_presets_source` の変更
- **symlink / junction の追随**（`is_path_within` の realpath 化）→ **対応しない**
  （canonical identity 比較の全体に波及するため phase 09 のスコープ外。
  必要になったら idea 起票）
- **N3（残置パスの初回 ON）/ N4（複製失敗時の成否）/ N6（OFF 復帰時にグローバルが読めない）**
  → **挙動は変えない**。暫定仕様 v0.7 に**既知の制約として明記済**で、正本への反映は **task_08**
- **N5**（application 側の未保存ガード）→ **不要と判断**（Import は task_06 で強制 OFF・
  新規作成は data ごと差し替わるため、到達経路が残っていない）
- 正本 `spec_detail/` への反映・`codebase_map.md` 更新 → **task_08**

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **225** + 追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **202** + 追加分）
- `-m tests.smoke_app` が pass

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests/test_config_service.py`**:

1. **予約ディレクトリ**: 個別パスが `user/hotkey_presets/global/xxx.json` → **拒否理由が返る**。
2. **同一ファイル**: config.json が `user/hotkey_presets/default.json` を指し、
   keymap_set の stem が `default` → 算出された既定パスが**グローバルと同一** → **拒否理由が返る**
   （**B1 の再現テスト**。表記違い〔`\` 区切り・絶対パス〕でも canonical 比較で**一致と判定**されること）。
3. **正常系**: 既定どおり（config.json → `global/default.json` / 個別 → `user/hotkey_presets/main.json`）
   なら**拒否されない**。
4. **payload 正規化**: `hotkey_presets_path` に `user\hotkey_presets\main.json` や config 内絶対パスを
   入れて payload を作ると **`user/hotkey_presets/main.json`** になる。
   **OFF の空文字は空文字のまま**。**キー順が変わらない**。

**`tests_ui/test_app_ui_flows.py`**:

5. **B1 の遮断**: 上記 2 の状態で `App.save_hotkey_presets(..., individual=True)` を呼ぶと
   **戻り値 False** / **保存 API がまったく呼ばれない**（**グローバルファイルの内容が変わらない**）/
   **`app.data` が完全に不変** / **`set_dirty` が呼ばれない** / `messagebox.showerror` が呼ばれる
   （**必ず patch する**）。
6. **予約ディレクトリの遮断**も同様（文言が同一ファイル用と**別**であること）。
7. **ON → OFF の確定は拒否されない**（衝突状態でも成功する。復旧経路を塞がない）。
8. **OFF のままのグローバル保存は拒否されない**。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: **グローバルファイルが上書きされない**か /
  **ON→OFF と OFF のままの保存を誤って拒否していない**か / 拒否時に `data`・dirty が完全に不変か /
  **判定が既存の比較専用 API の再利用**か〔`canonical_path` の値を保存・表示へ混ぜていないか〕/
  **`resolve_hotkey_presets_save_path` の契約を変えていない**か /
  読み出し側【O2】・【O3】を変えていないか / **正規化で空文字・キー順が壊れていない**か /
  後続タスク（task_08）の先取りがないか）。
- 是正後、**task_07 の通し再実測と実機目視へ戻る**（実機目視は task_07 の観点リストで実施）。
