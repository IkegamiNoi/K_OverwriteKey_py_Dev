# task_05c_invalid_target_redirect

## 目的

**無効な個別パス（config 外）での保存を「拒否」から「管理下の既定パスへ寄せて新規作成」へ変更する**
（暫定仕様 08 **§2【O3】（v0.6 で反転）+ dirty 規則 / §3-3 / §3-4**・受入条件 **4 / 15**）。

task_05b は v0.5【O3】= **拒否**を実装したが、**v0.6 でユーザーが反転を確定**した
（拒否は復旧手段が JSON の手編集しか無く行き止まりになる / 保存先は OK 前に表示されるため
「黙って別の場所へ書く」に当たらない / **ON + パス未設定の既存挙動と同型**にできる）。
**task_05b で入れた拒否経路は削除する**（残置しない）。

あわせて、**`hotkey_presets_path` の値が実際に変化したときだけ dirty を立てる**規則を入れる。
従来はフラグ変更への相乗りで永続化されており、**「最初から ON」の経路では永続化されない穴**があった。

**レイヤ制約**: **application（書込先の算出）+ presentation（dirty の確定・表示文言）**。
**domain 不変・読み出し側【O2】不変**（`build_runtime_data_from_split` /
`describe_hotkey_presets_source` は**変更しない**）。

## 対象範囲

### 1. `keyseq/application/config_service/split_loading.py` — 無効パスを「未設定」と同一視する

- **`resolve_hotkey_presets_save_target`（task_05b で追加した 3 値タプル版）を削除**し、
  **`resolve_hotkey_presets_save_path` に戻す**（`individual` override は task_05 のまま維持）。
  **保存側に `invalid` という状態は存在しなくなる**ため、ステータスを運ぶ必要が無い。
  `ConfigService` の委譲メソッドも同様に戻す（**恒久的な互換レイヤーを残さない**）。
- **書込先の分岐を次に変える**（実効フラグが ON のとき）:
  - **有効な個別パスがある** … そのパス（現行どおり）
  - **パス未設定 “または” パスが無効（config 外）** … **既定パス
    `user/hotkey_presets/<stem>.json` を算出して返す**（保存表記へ変換。現行の未設定分岐と同じ処理）
  - 実効フラグが OFF … 空文字（グローバル。現行どおり）
- **判定は既存の `resolve_individual_hotkey_presets_path` を再利用する**
  （**新しいパス判定を書かない**）。現行の「`stored_path` が非空なら既定へ差し替えない」条件が
  **無効パスを既定へ落とさない原因**なので、そこを**有効判定の結果で見るように直す**。

> **注意**: `config_root` が空のときは既定パスも算出できない。**現行どおり空文字（グローバル）**
> へ倒す（通常経路では起きない。`App` が必ず設定する）。

### 2. `keyseq/presentation/controllers/config_io/hotkey_presets_io.py` — 拒否経路の削除

- **`reject_invalid_target` を削除**する（呼び出し元が無くなるため）。
  `write_presets` と `messagebox.showerror` の既存契約は**不変**。

### 3. `keyseq/presentation/app.py` — 拒否の削除 + dirty 規則

`save_hotkey_presets`（`:416-446`）を次のとおり変更する:

- **`target_status == "invalid"` の分岐（`:436-437`）を削除**する。
- **`hotkey_presets_path` の値が実際に変化したときだけ `dirty_tracker.set_dirty(True)`**:
  - 反映前の値と `stored_path` を比較し、**異なるときだけ** dirty を立てる
  - **同じ値の再確定では立てない**（＝ ON + 有効パスありでの内容編集は **dirty にしない**。
    受入条件 4 を維持する要）
  - **フラグ変化による dirty（現行 `:443-445`）はそのまま**。両方が同時に成立しても
    **`set_dirty(True)` は冪等**なので特別扱いしない
  - **保存に失敗したら立てない**（`data` を変更しないのと同じ契約）
- **OFF（グローバルへ書く）ときは `stored_path` が空**で、`:441` のガードにより
  パス反映自体が起きない。**dirty も立てない**。

### 4. `keyseq/presentation/dialogs.py` — 表示文言

`format_preset_manager_source_labels`（task_05 の Tk 非依存の純関数）で、
**`individual_state == "invalid"` のときの文言を変える**:

- 現行 = 「無効である」旨のみ
- 変更後 = **これから書く既定パスを保存先として示し**、
  **記録されていた保存先が config 外のため使わない旨を添える**
  （文言は実装者判断。**新しい保存先のパス**を必ず含める）
- **出どころラベル（`displayed_source`）は不変**（読み出しは【O2】のままグローバルへ倒れる）。

### 設計メモ / 制約

- **【O2】読み出しは従来どおりグローバルへ倒す**。**読み出し側のコードを変更しない**
  （非対称は意図どおり）。`describe_hotkey_presets_source` の `invalid` は**表示のために残す**。
- **config 外の元ファイルは読まない・書かない・消さない**。新規ファイルの内容は
  **表示中の一覧**から作る（【E】＝ ON + パス未設定と同じ）。
- **ON → OFF の確定は書き込みが起きないので対象外**【H2】。無効パスのまま OFF にできる。
- **既定パスの算出は task_04 の `default_individual_hotkey_presets_path` をそのまま使う**
  （同一 stem の共有は【M】で既知の制約として許容済み。**上書き確認を新設しない**）。

## 含まない

- **Import での強制 OFF / 別名保存時の個別ファイル複製** → **task_06**
- 読み出し側【O2】の変更 / `describe_hotkey_presets_source` の**判定**の変更（文言のみ変える）
- 無効パスの**その他の自動修復**（キーの消去・OFF への強制切替）
- 正本 `spec_detail/` への反映 → **task_08**（暫定仕様 08 v0.6 が現時点の正）

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **225**。**task_05b の拒否テストは削除・
  差し替えになるため件数は減ってよい**）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **200**。同上）
- `-m tests.smoke_app` が pass

### テスト（追加・差し替えまで実装範囲。**実行は依頼しない**）

**`tests/test_config_service.py`**（task_05b で追加した 3 値ステータスのテストは**削除**し、
次へ差し替える）:

1. **無効パス（config 外）+ 個別 ON** → **既定パス**（`user/hotkey_presets/<stem>.json` の保存表記）を返す。
2. **パス未設定 + 個別 ON** → 同じく既定パス（現行の挙動が壊れていないこと）。
3. **有効パス + 個別 ON** → **そのパスのまま**（既定へ寄せない）。
4. **OFF** → 空文字。**`individual=True` の override でも上記 1〜3 が働く**こと、
   および **`runtime` が書き換わっていない**こと。

**`tests_ui/test_app_ui_flows.py`**（task_05b の拒否テストは**削除**し、次へ差し替える）:

5. **無効パスで個別へ保存すると、既定パスへ新規作成される**:
   **グローバルファイルが更新されない** / `app.data["hotkey_presets_path"]` が**既定パスへ更新**される /
   **config 外の元パスには一切触れない**（ファイルが作られず、存在しないままであること）。
6. **そのとき `set_dirty(True)` が呼ばれる**（パスの値が変わったため）。
7. **有効パスでの内容編集の保存では `set_dirty` が呼ばれない**（パスが変わらないため。受入条件 4）。
8. **OFF のままの保存は従来どおりグローバルへ書け、`set_dirty` も呼ばれない**。
9. **保存に失敗したら `set_dirty` が呼ばれず `app.data` も不変**（`messagebox.showerror` は
   **必ず patch する**）。
10. **ON → OFF の確定は無効パスでも成功する**（書き込みなし・フラグ False・パス保持・
    グローバル読み直し・`set_dirty(True)`）。

> `AppUiFlowsTest` は App を共有するため、**dirty は絶対値で assert せず `set_dirty` の
> 呼出有無**で見ること。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: **無効時にグローバルへ書かない**か /
  **既定パスへ寄せた新規作成になっている**か / **config 外の元ファイルに触れていない**か /
  **dirty がパスの値の変化時だけ**か〔内容編集で立たないか〕/ **拒否経路が残っていない**か
  〔`reject_invalid_target` / 3 値ステータスの残骸〕/ **読み出し側【O2】を変えていない**か /
  判定が既存関数の再利用か / 後続タスク（task_06 / task_08）の先取りがないか）。
- **実機目視は本タスクでは行わない**（**task_07** でまとめて実施）。
