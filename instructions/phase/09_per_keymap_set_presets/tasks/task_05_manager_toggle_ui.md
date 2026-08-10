# task_05_manager_toggle_ui

## 目的

**プリセットマネージャに「この構成セット専用にする」切替 UI を載せ、OK / キャンセルの契約を確定する**
（暫定仕様 08 **§2【D】【E】【F】【J】【Q】【R】【H2】【N】 / §3-4**・受入条件 **4 / 8 / 10 / 13**）。
task_04 までで**読み書きの配線は通った**が、**ユーザーが個別／グローバルを切り替える手段が無い**。
本タスクでそれを付ける。

**レイヤ制約**: **presentation（UI・OK/キャンセルの契約）+ application（表示状態の判定 API）**。
**domain 不変・解決順序（task_03）不変・保存 API（task_04）の書き出し形は不変**。
**Import の強制 OFF・別名保存時の複製は task_06**。

## 対象範囲

### 1. `keyseq/application/config_service/` — 表示状態の判定（presentation で組み立てない）

**判定は application に置く**（task_04 と同じ方針。`split_loading.py` の既存関数を再利用し、
解決順序を二重化しない）。

#### 1-a. 保存先プレビュー: `resolve_hotkey_presets_save_path` に override を足す

```python
def resolve_hotkey_presets_save_path(
    service, runtime, *, config_root, keymap_set_path, individual: bool | None = None
) -> str:
```

- `individual is None` … **現行どおり** runtime のフラグに従う（既存呼び出しは無変更で通る）
- `individual` が真偽値 … **runtime のフラグの代わりにその値で判定**する
  （**runtime は書き換えない**。チェックを入れただけの状態で「次はどこへ書くか」を出すため）
- 戻り値の意味は不変（個別なら保存表記パス / グローバルなら**空文字**）
- `ConfigService.resolve_hotkey_presets_save_path`（`__init__.py:497-509`）も同じ引数を通す

#### 1-b. グローバルパスの公開

チェック OFF のときに**表示するパス**（＝ config.json が指すグローバルパス）を presentation が
取れるようにする。`split_loading.load_global_hotkey_presets_path`（`:45-63`）へ委譲する
薄い `ConfigService` メソッドを 1 本足すこと（**presentation から `split_loading` を直接呼ばない**）。

#### 1-c. 一覧の出どころの判定: `describe_hotkey_presets_source`

`split_loading.py` へ追加する。**実際に読める／読めないを見る**ため、
`resolve_individual_hotkey_presets_path`（`:99-116`）/ `load_hotkey_presets_file`（`:66-87`）/
`load_global_hotkey_presets`（`:90-96`）を**再利用**して組む（判定を書き直さない）。

```python
def describe_hotkey_presets_source(service, runtime, *, config_root) -> dict[str, str]:
```

返す 2 つの値（**独立**。優先順位を付けて片方を隠さない）:

| キー | 値 | 意味 |
|---|---|---|
| `individual_state` | `"off"` | 個別指定 OFF（フラグ無しを含む）|
| | `"active"` | 個別指定 ON・パス有効・**ファイルが読めた** |
| | `"missing"` | 個別指定 ON・パス有効だが **読めない**（未作成・破損）|
| | `"invalid"` | 個別指定 ON だが **パスが config 外**（【O2】。パスが空のときは `"missing"` 扱い）|
| `displayed_source` | `"individual"` / `"global"` / `"builtin"` | **いま一覧に出ている内容の出どころ**（`"builtin"` = 個別もグローバルも読めず組込既定が出ている状態）|

- **戻り値は dict / NamedTuple のどちらでもよい**（実装者判断）。**文言は返さない**（文言は presentation）。
- `ConfigService` へ委譲メソッドを足す。

### 2. `keyseq/presentation/dialogs.py` — 切替 UI（`PresetManagerDialog`・`:345-513`）

#### 2-a. ウィジェット

- **チェックボックス「この構成セット専用にする」**（`self.individual_var` = `tk.BooleanVar`。
  初期値は `parent.data.get("hotkey_presets_individual") is True`）。
- **保存先ラベル**（チェックに**追従して更新**）と、**出どころラベル**（**ダイアログを開いた時点で確定・
  トグルでは変えない**）の 2 行。**一覧（`_temp`）はトグルで差し替えない**【I 撤回】。
- 文言（【R】）:
  - 保存先: チェック ON → `保存先: <個別パス>` / OFF → `保存先: グローバル（<グローバルパス>）`
  - `individual_state == "invalid"` … **無効である旨**（例: `個別の保存先が config 外のため無効です`）
  - 出どころ: `"individual"` → 表示しない（保存先と同じため）/ `"global"` かつ個別 ON →
    **`グローバルを表示中`** / `"builtin"` → **`読み込めませんでした（既定を表示中）`**
    （**「グローバルを表示中」と誤表示しない**）
- **【F】keymap_set 未保存（`parent.keymap_set_path` が空）ならチェックを `disabled` にし、
  理由を表示する**（例: `構成セットを保存すると専用にできます`）。
  **【Q】の再評価は「ダイアログを開くたびに構築し直す」ことで満たす**
  （保存 / 読込 / 新規作成のたびにイベントを配る仕組みは**足さない**）。
- **文言の組み立ては Tk に依存しない純関数**（`dialogs.py` のモジュールレベル関数）へ出し、
  ウィジェットはその戻り値を貼るだけにする（テストから文言を固定できるようにするため）。

#### 2-b. `on_ok` の契約（`:505-508`）

チェック値を渡して `parent.save_hotkey_presets` を呼び、**True のときだけ閉じる**（現行の成否契約は不変）。

```python
if self.parent.save_hotkey_presets(self._temp, individual=bool(self.individual_var.get())):
    self.destroy()
```

#### 2-c. キャンセル

**現行の `destroy` のまま**（フック再開のみ）。**フラグ・dirty・ファイルのいずれも変えない**【J】。
チェックを触ってからキャンセルしても同じ（`parent.data` を触らないので自然に満たされるが、
**テストで固定する**）。

### 3. `keyseq/presentation/app.py` — OK の挙動（`save_hotkey_presets`・`:416-427`）

```python
def save_hotkey_presets(self, presets: list, *, individual: bool | None = None) -> bool:
```

`individual is None` は**現行の挙動そのまま**（フラグも dirty も変えない）。真偽値のときの分岐:

| 現在のフラグ | 指定 | 挙動 |
|---|---|---|
| OFF | OFF | **現行どおり**グローバルへ書く。**dirty を触らない** |
| ON | ON | **現行どおり**個別へ書く。**dirty を触らない** |
| OFF | **ON** | 保存先を `individual=True` で解決して**個別へ書く**。成功時のみ `hotkey_presets` / `hotkey_presets_path` / `hotkey_presets_individual=True` を反映し **dirty True** |
| ON | **OFF** | **書き込まない**【H2】。`hotkey_presets_individual=False` にし、**`hotkey_presets_path` は保持**【N】、**グローバルを読み直して** `hotkey_presets` へ反映（`None` なら**置き換えない**）、**dirty True**、`True` を返す |

- **失敗時は `self.data` を一切変更しない**（フラグも書き換えない＝「先にフラグを立ててから戻す」形にしない）。
- **dirty は「フラグの値が実際に変わったときだけ」**（【J】/ 受入条件 4。内容編集では dirty にしない）。
- グローバル読み直しは `ConfigService` 経由（`load_global_hotkey_presets` 相当）。
  **プリセット単独の注入 API は作らない**（正本 §5.8.8 の注記。runtime へ代入するだけ）。

### 設計メモ / 制約

- **【H】ON にしただけではファイルを作らない**。実体は OK の保存で初めて作られる。
- **【E】ON 直後の内容は編集中の一覧をそのまま引き継ぐ**（＝グローバル由来の内容が個別へ書かれる）。
- **【O】config 外へは書かない**（判定は task_03 の関数が担保。presentation で緩めない）。
- 保存先・出どころの**判定を presentation で組み立てない**（§1 の API を呼ぶだけ）。
- `open_preset_manager`（`:409-414`）の**フラッシュメッセージ条件は変えない**
  （プリセット内容の差分で出す。フラグだけ変えた場合に出ないのは許容）。

## 含まない

- **Import での強制 OFF / 別名保存時の個別ファイル複製** → **task_06**
- 解決順序・保存 API の書き出し形の変更（task_03 / task_04 の到達点）
- プリセット編集 UI（追加/編集/削除/並べ替え）の変更 / メインウィンドウへの切替 UI 追加【D で不採用】
- 「ON にした時点でファイルを作る」実装（**仕様で不採用**）/ 正本の更新（**task_08**）

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **220** + 追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **189** + 追加分）
- `-m tests.smoke_app` が pass

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests/test_config_service.py`**:

1. **保存先プレビュー**: `individual=True` を渡すと runtime のフラグが OFF でも**個別パス**（未設定なら
   既定パス）を返し、`individual=False` なら**空文字**。**`runtime` が書き換わっていない**ことを確認。
2. **`describe_hotkey_presets_source` の 4 状態**: OFF → `("off", "global")` /
   ON + 実体あり → `("active", "individual")` / ON + 実体なし + グローバルあり →
   `("missing", "global")` / ON + config 外パス → `("invalid", ...)` /
   **両方読めない** → `displayed_source == "builtin"`。

**`tests_ui/test_app_ui_flows.py`**（既存の `save_hotkey_presets` 系の近くへ）:

3. **OFF → ON で OK**: **個別ファイルへ書かれ**、`hotkey_presets_individual` が True、
   `hotkey_presets_path` が確定し、**`set_dirty(True)` が呼ばれる**。
4. **ON → OFF で OK**: **保存 API がまったく呼ばれない**（グローバルファイルが**更新されない**）/
   フラグ False / **`hotkey_presets_path` が保持**される / **グローバルの内容が runtime へ載る** /
   `set_dirty(True)` が呼ばれる / 戻り値が True。
5. **フラグ変化なしの OK**（OFF→OFF・ON→ON）: 現行どおり保存され、**`set_dirty` が呼ばれない**。
6. **ON への切替で保存失敗**: 戻り値 False・**`app.data` が一切不変**（フラグも `hotkey_presets_path` も）・
   ダイアログを閉じない。`messagebox.showerror` は**必ず patch する**。
7. **キャンセル**: チェックを切り替えてから閉じても `parent.data` ・ dirty ・ ファイルが**すべて不変**。
8. **文言**（§2-a の純関数を直接呼ぶ）: 4 状態 + 未保存時の理由文言 + **`"builtin"` で
   「グローバルを表示中」と出ない**こと。

> **実装前に確認すること**: `PresetManagerDialog` は `grab_set` / `wait_window` を使うため、
> 既存テストは `SimpleNamespace` + `PresetManagerDialog.on_ok` 直呼びで回避している
> （`test_app_ui_flows.py:406-429`）。**同じ形で足せるか**を先に確認し、
> ウィジェット構築が要るテストは避ける（文言は §2-a の純関数で固定する）。
> **`AppUiFlowsTest` は App を共有する**ため、dirty は**絶対値で assert せず
> `set_dirty` の呼出有無**で見ること。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: **OFF へ戻す OK でグローバルが上書きされない**か /
  **トグルで一覧（`_temp`）が差し替わらない**か / **dirty がフラグ変化時だけ**か /
  **失敗時に `data` が完全に不変**か / **判定が application 側 1 箇所**か〔presentation で組み立てていないか〕/
  **ON でファイルを作っていない**か【H】/ `hotkey_presets_path` を消していないか【N】/
  未保存時の ON 不可【F】が UI で担保されているか）。
- **実機目視は本タスクでは行わない**（**task_07** でまとめて実施）。
