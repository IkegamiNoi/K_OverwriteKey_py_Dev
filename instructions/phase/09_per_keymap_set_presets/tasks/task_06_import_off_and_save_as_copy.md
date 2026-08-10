# task_06_import_off_and_save_as_copy

## 目的

**Import で個別指定を強制 OFF にし、別名保存で個別ファイルを複製して追随させる**
（暫定仕様 08 **§2【K】【L】/ §3-2 / §3-3**・受入条件 **7 / 12 / 16**）。
外部ファイル由来の個別指定が**外部パスへ書く経路**にならないようにし（【K】）、
別名保存で「専用」と見せているプリセットが**元の keymap_set と共有されたままになる**のを防ぐ（【L】）。

**レイヤ制約**: **application（キーの落とし方・ファイル複製）+ presentation（呼び出し位置）**。
**domain 不変・解決順序（task_03）不変・保存先の算出（task_04 / 05c）不変・
プリセットマネージャ（task_05）不変**。

## 対象範囲

### 1. Import での強制 OFF（【K】）

#### 1-a. `keyseq/application/config_service/` — キーを落とす API

```python
def clear_individual_hotkey_presets(self, runtime: dict[str, Any]) -> dict[str, Any]:
```

- **`hotkey_presets_individual` を `False`、`hotkey_presets_path` を `""`（空文字）**にする
  （**キーが無くても両方を設定する**。以後の保存で 2 キーは常に出力されるため値が一意に決まる）。
- **`hotkey_presets`（内容）には触らない**。他のキーも変更しない。
- 置き場は実装者判断（`config_service/__init__.py` か既存の兄弟モジュール）。
  **`ensure_config_compatibility` には入れない**（通常読込へ波及させないため。§2【K】）。

#### 1-b. `keyseq/presentation/controllers/config_io/keymap_set_io.py` — 呼び出し位置

`import_config`（`:549-573`）の **`load_legacy_runtime_data` の直後・`apply_global_defaults` の前**
（現行 `:561` と `:562` の間）で §1-a を呼ぶ。

- **Import 経路のこの 1 箇所だけ**（`load_split_config` 等の通常読込には入れない）。
- 呼び出し後に `apply_global_defaults` が走ることで、**プリセットはグローバルから供給される**
  （入口台帳 E5。**プリセット単独の注入 API は作らない**）。
- Export 側（`export_runtime_data`）は**現状のまま**（runtime を丸ごと出力）。

### 2. 別名保存での個別ファイル複製（【L】）

#### 2-a. `keyseq/application/config_service/` — 複製 API

```python
def relocate_individual_hotkey_presets(
    self, runtime, *, config_root: str, keymap_set_path: str
) -> str:
```

**新しい keymap_set の保存先 stem から個別パスを再計算し、必要なら複製する**。戻り値は
確定した保存表記パス（何もしなかった場合は空文字）。

- **個別指定が OFF（フラグ無しを含む）なら何もしない**（空文字を返す）。
- 新パス = **task_04 の `default_individual_hotkey_presets_path`** で算出（`keymap_set_path` は
  **新しい保存先**）→ **保存表記へ変換**（`to_config_relative_or_absolute`）。
- **複製する条件は「コピー元が有効かつ実体がある」かつ「コピー先に実体が無い」**:
  - **コピー先に実体があれば複製しない**（それを使う。§5.8.3 の既定規則と同じ思想。
    **上書き確認を新設しない**）
  - **コピー元が存在しない**（ON だが未確定で実体が無い）**なら複製しない**。
    新パスを指すだけで、次のマネージャ確定で作られる
  - **コピー元が無効（config 外）なら複製しない**（v0.6【O3】と同じく「使えるパスが無い」扱い。
    パスだけ新パスへ更新する）
  - コピー元とコピー先が**同一パスなら何もしない**
- **複製はファイルのコピー**であり、**runtime の内容を書き出さない**
  （書き手はマネージャ 1 本のまま。§2【B】）。**内容の正規化もしない**。
- **元ファイルは消さない**。
- コピー元の有効判定は **`resolve_individual_hotkey_presets_path` を再利用**する
  （新しいパス判定を書かない）。

#### 2-b. `keymap_set_io.save_keymap_set_to`（`:101-146`）— 呼び出し位置

**保存先が変わるとき（＝別名保存）だけ**呼ぶ。

- 条件は **`save_path` が現在の `self._app.keymap_set_path` と異なる**こと
  （`self._app.keymap_set_path` の更新は `:123`。それより**前**で判定する）。
  **同じパスへの通常保存では絶対に走らせない**（記録済みの個別パスを勝手に付け替えないため）。
- 呼び出しは **`save_runtime_data`（`:114`）の直前**。返り値が非空なら
  **`self._app.data["hotkey_presets_path"]` へ反映**してから保存する
  （**新しい keymap_set の payload に新パスが載る**ようにするため）。
- **既存の `try` 内**に置き、例外は現行の `except`（`保存失敗` 表示）に委ねる。
- **dirty の扱いは変えない**（保存完了時の `set_dirty(False)`（`:130`）のまま。
  task_05c の dirty 規則は `App.save_hotkey_presets` 側の話で、ここには持ち込まない）。

### 設計メモ / 制約

- **【M】同一 stem の複数 keymap_set が同じ個別ファイルを共有し得る**のは**既知の制約**。
  複製先が既にある場合に**共有になるのは仕様どおり**（警告・確認を足さない）。
- **保存カスケードはプリセットの内容を書かない**（正本 §5.10.3）。§2 で行うのは
  **ファイルのコピー**だけで、内容の生成ではない。
- **読み出し側【O2】・保存先の算出（task_04 / 05c）を変更しない**。
- **Import 後の runtime は個別 OFF**なので、その後の保存で
  `hotkey_presets_path=""` が payload に載る（受入条件 16）。

## 含まない

- Export 側の変更（現状のまま runtime を丸ごと出力）
- 複製時の**上書き確認ダイアログ**・共有の検知警告（**仕様で不採用**。【M】）
- 元ファイルの削除・移動 / プリセット内容の書き出し
- 統合確認・実機目視 → **task_07** / 正本反映 → **task_08**

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **222** + 追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **199** + 追加分）
- `-m tests.smoke_app` が pass

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests/test_config_service.py`**:

1. **強制 OFF**: キーがある runtime / **キーが無い** runtime のどちらでも
   `hotkey_presets_individual is False` かつ `hotkey_presets_path == ""` になる。
   **`hotkey_presets`（内容）は不変**。
2. **複製の 5 分岐**: ①コピー元あり + コピー先なし → **複製される**（内容一致・**元も残る**）/
   ②コピー先に実体あり → **複製しない**（**コピー先の内容が保たれる**）/
   ③コピー元の実体なし → 複製しないが**戻り値は新パス** / ④OFF → **空文字・何もしない** /
   ⑤コピー元が config 外（無効）→ 複製しないが**戻り値は新パス**。
3. **戻り値のパス表記**が §5.7 準拠（config 配下は相対・`/` 区切り）で、
   **新しい stem から算出**されている（`user/hotkey_presets/<新 stem>.json`）。

**`tests_ui/test_app_ui_flows.py`** または
`tests_ui/test_config_io_characterization_keymap_set_startup.py`（既存の Import / 別名保存テストの近く）:

4. **Import 後**に `data["hotkey_presets_individual"] is False` /
   `data["hotkey_presets_path"] == ""`（**残置 `hotkey_presets_path` を持つファイルを取り込んでも**）。
   **プリセットはグローバル由来**になっている。
5. **別名保存で個別ファイルが複製され**、**保存された keymap_set の
   `hotkey_presets_path` が新パス**になっている（保存後のファイルを読んで確認）。
6. **同じパスへの通常保存では複製も再計算も起きない**（`hotkey_presets_path` が不変）。

> `filedialog` / `messagebox` は**必ず patch する**（モーダルはテストを永久ブロックする）。
> `AppUiFlowsTest` は App を共有するため **dirty は絶対値で assert せず `set_dirty` の
> 呼出有無**で見ること。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: **強制 OFF が Import 経路 1 箇所だけ**か
  〔`ensure_config_compatibility` や通常読込に入れていないか〕/ **複製が別名保存でだけ走る**か
  〔同一パスの通常保存で走らないか〕/ **コピー先に実体があるとき上書きしていない**か /
  **元ファイルを消していない**か / **runtime の内容を書き出していない**か〔書き手 1 本の維持〕/
  判定が既存関数の再利用か / 保存カスケード・読み出し側・マネージャを変更していないか /
  後続タスク（task_07 / task_08）の先取りがないか）。
- **実機目視は本タスクでは行わない**（**task_07** でまとめて実施）。
