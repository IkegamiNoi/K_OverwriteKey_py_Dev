# task_05b_invalid_target_save_guard

## 目的

**個別パスが無効（config 外）のまま個別へ書こうとした保存を拒否する**
（暫定仕様 08 **§2【O3】（v0.5 で追加）/ §3-3 / §3-4**・受入条件 **15**）。

task_04 / task_05 の到達点では、**書込先が個別なのにパスが config 外だと保存先が
グローバルへ倒れる**（`resolve_hotkey_presets_save_path` が空文字を返すため）。
読み出しの【O2】は「無効ならグローバルへ倒す」で正しいが、**書き込みで同じことをすると
グローバルライブラリを黙って上書きする**。v0.5 で **書き込み側は拒否**と確定した。

**レイヤ制約**: **application（拒否すべき状態の判定）+ presentation（拒否時の理由表示）**。
**domain 不変・読込側（task_03 / task_05 の `describe_hotkey_presets_source`）不変・
保存 API の書き出し形（task_04）不変**。

## 対象範囲

### 1. `keyseq/application/config_service/split_loading.py` — 書込先と理由を返す

現状の `resolve_hotkey_presets_save_path`（`:119-`）は **パス文字列しか返さない**ため、
呼び出し側が「グローバルへ倒った」のか「無効だった」のかを区別できない。**理由を返す関数を足す**:

```python
def resolve_hotkey_presets_save_target(
    service, runtime, *, config_root, keymap_set_path, individual: bool | None = None
) -> tuple[str, str]:  # (stored_path, status)
```

- `status` は **`"individual"` / `"global"` / `"invalid"`** の 3 値
  - `"individual"` … 個別へ書く（`stored_path` = 保存表記パス。**既定パスの算出も現行どおり**）
  - `"global"` … グローバルへ書く（`stored_path` = 空文字）
  - `"invalid"` … **実効的な書込先が個別だが、`hotkey_presets_path` が config 外**
    （`stored_path` は**空文字**。呼び出し側は書いてはならない）
- **`individual` override の意味は task_05 と同じ**（`None` は runtime の値。**runtime は書き換えない**）
- **`resolve_hotkey_presets_save_path` はこの関数の薄いラッパにする**（`stored_path` だけ返す）。
  **判定を二重化しない**。既存の呼び出し・既存テストはそのまま通ること
- **`"invalid"` の判定は既存の有効判定を再利用する**
  （`resolve_individual_hotkey_presets_path` が空を返し、かつ **`hotkey_presets_path` が非空**、
  かつ**実効フラグが ON**）。**新しいパス判定を書かない**
- `ConfigService` へ委譲メソッドを 1 本追加する

> **注意**: `config_root` が空のケースは既存判定でも無効側に落ちるが、**通常経路では起きない**
> （`App` が必ず設定する）。**`"invalid"` に混ぜてよい**（別扱いの分岐を増やさない）。

### 2. `keyseq/presentation/controllers/config_io/hotkey_presets_io.py` — 拒否の表示

```python
def reject_invalid_target(self) -> bool:
```

- `messagebox.showerror` で**理由を表示**し、**`False` を返す**
  （文言例: タイトル `プリセット保存失敗` / 本文は「個別プリセットの保存先が config 配下では
  ないため保存できません」+ **現在のパス** + **復旧手段**〔config 配下のパスへ直す or
  チェックを外す〕。文言は実装者判断でよいが**パスと復旧手段を必ず含める**）
- **モーダルはこのファイルに集約する**（`app.py` に新しい `showerror` を増やさない。
  tests_ui の fail-fast ガードが**このファイルの `messagebox.showerror` を見ている**ため）

### 3. `keyseq/presentation/app.py` — `save_hotkey_presets` の分岐へ拒否を追加

`save_hotkey_presets(presets, *, individual=None)`（`:416-`）で、**書き込みの前に** §1 の
`status` を取り、`"invalid"` なら **`self.hotkey_presets_io.reject_invalid_target()` を返す**。

- **ON → OFF の確定（【H2】の分岐）は対象外**。**書き込みが起きない分岐なので拒否もしない**
  （無効パスを抱えたまま「専用をやめる」操作は**成功させる**。これが主要な復旧手段のため）。
  → **拒否判定は「実効的な書込先が個別」の分岐でだけ行う**
- 拒否時は **`self.data` を一切変更しない**（プリセット・パス・フラグ・dirty のすべて）。
  **戻り値 `False` によりダイアログは閉じない**（既存の成否契約に乗るだけ。`dialogs.py` は無変更）

### 設計メモ / 制約

- **【O2】読み出しは従来どおりグローバルへ倒す**。**読み出し側を拒否側へ揃えない**
  （非対称は意図どおり。`build_runtime_data_from_split` / `describe_hotkey_presets_source` は**不変**）。
- **キーの値を書き換えない**（拒否時に `hotkey_presets_path` を消さない・既定パスへ差し替えない）。
- **UI 表示（task_05 の「無効である旨」）は変えない**。本タスクで足すのは**保存時の拒否**だけ。
- `dialogs.py` は**無変更**（`on_ok` は戻り値 False で閉じない契約が既にある）。

## 含まない

- **Import での強制 OFF / 別名保存時の個別ファイル複製** → **task_06**
- 読み出し側の挙動変更（【O2】は維持）/ `describe_hotkey_presets_source` の変更
- 無効パスの**自動修復**（既定パスへの差し替え・キーの消去）= 仕様で却下（暫定仕様 08 §4 の O3 行）
- 正本 `spec_detail/` への反映 → **task_08**（暫定仕様 08 v0.5 が現時点の正）

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **222** + 追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **196** + 追加分）
- `-m tests.smoke_app` が pass

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests/test_config_service.py`**:

1. **`status` の 3 値**: 個別 ON + config 配下パス → `("…", "individual")` /
   OFF → `("", "global")` / **個別 ON + config 外パス → `("", "invalid")`** /
   個別 ON + パス未設定 → **既定パス + `"individual"`**（無効ではない）。
2. **override**: `individual=True` を渡すと runtime のフラグが OFF でも上記判定が働く
   （config 外パスなら `"invalid"`）。**`runtime` が書き換わっていない**こと。
3. **後方互換**: `resolve_hotkey_presets_save_path` の戻り値が**従来と同じ**
   （`"invalid"` でも空文字）。

**`tests_ui/test_app_ui_flows.py`**:

4. **無効パスで個別へ保存しようとすると拒否される**: 戻り値 False /
   **保存 API がまったく呼ばれない**（**グローバルファイルが更新されない**ことも確認）/
   `app.data` が完全に不変（プリセット・`hotkey_presets_path`・フラグ）/
   `set_dirty` が呼ばれない / `messagebox.showerror` が呼ばれる（**必ず patch する**）。
5. **OFF → ON の切替で無効パスだった場合も拒否**され、**フラグが ON にならない**。
6. **ON → OFF の確定は無効パスでも成功する**（拒否しない）: 書き込みなし・フラグ False・
   `hotkey_presets_path` は保持・グローバル読み直し・`set_dirty(True)`・戻り値 True。
7. **OFF のままの保存は無効パスがあっても通常どおりグローバルへ書ける**（誤って拒否しない）。

> `AppUiFlowsTest` は App を共有するため、**dirty は絶対値で assert せず `set_dirty` の
> 呼出有無**で見ること。`showerror` の fail-fast ガード（`setUp`）があるため、
> 拒否を期待するテストは**そのファイルの `messagebox.showerror` を patch** すること。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: **無効時にグローバルへ書かない**か /
  **ON → OFF の復旧経路を塞いでいない**か【H2】/ 拒否時に `data`・dirty が完全に不変か /
  **判定が application 側 1 箇所**か〔既存の有効判定を再利用しているか〕/
  **読み出し側【O2】を変えていない**か / モーダルを `hotkey_presets_io` に集約しているか /
  後続タスク（task_06 / task_08）の先取りがないか）。
- **実機目視は本タスクでは行わない**（**task_07** でまとめて実施）。
