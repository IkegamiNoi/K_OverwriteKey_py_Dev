# task_03_save_plan_execution

## 目的

keymap_set の一括保存を「**保存計画（save plan）駆動**」へ作り替える（暫定仕様 05 §2 指摘②③・§8）。
現状 `save_runtime_data` は子ファイルを**無条件・固定順**で書き出しているため、行ごとの選択（保存 / 別名保存 /
保存しない）を受け取れず、失敗時に親索引だけ新パスへ進む危険もある。本タスクで**受け皿と実行契約**を作る。

- レイヤ制約: **application 限定**（`keyseq/application/`）。**presentation は一切変更しない**
  （ダイアログも計画の組み立ても task_04 / task_05）。domain 不変・**スキーマ不変**。
- **本タスク単体では挙動を変えない**: 計画を渡さない（`save_plan=None`）ときの結果は現状と等価。
  唯一変わるのは**書き込み順序**（子 → 親 → startup。§8 の「失敗時に旧索引を維持」のため）。
- この等価性を確認してから task_05（ダイアログ）へ進む — 挙動変更の切り分けが本タスクの存在理由。

## 対象範囲（application 限定）

### 1. `keyseq/application/save_plan.py`（新規・100 行程度）

保存計画の型を `config_service.py`（既に 1200 行超）から分離して置く。**dataclass のみ・IO を持たない**。

```python
CHILD_KEYMAP = "keymap"
CHILD_TRIGGER_SET = "trigger_set"
CHILD_SEQUENCE = "sequence"

ACTION_SAVE = "save"        # 現在の解決先（source_path、無ければ既定命名）へ保存
ACTION_SAVE_AS = "save_as"  # target_path へ保存
ACTION_SKIP = "skip"        # 書かない

@dataclass(frozen=True)
class ChildSaveEntry:
    kind: str          # CHILD_* のいずれか
    key: str           # keymap = keymap の id / sequence = 正規化済みトリガーキー / trigger_set = ""
    action: str        # ACTION_* のいずれか
    target_path: str = ""   # ACTION_SAVE_AS のときのみ必須

@dataclass(frozen=True)
class SavePlan:
    entries: tuple[ChildSaveEntry, ...] = ()

    def entry_for(self, kind: str, key: str = "") -> ChildSaveEntry | None: ...

class SavePlanError(ValueError):
    """保存計画の事前検証に失敗した（この例外が出たときは 1 バイトも書いていない）。"""
```

- **`entries` に無い子の既定は `ACTION_SAVE`**（現状の全保存と等価にするため。ダイアログは dirty な子だけを
  並べるので、dirty でない子は従来どおり書かれる）。
- `SavePlan()`（空）＝ 全保存 ＝ `save_plan=None` と同義。

### 2. `keyseq/application/config_service.py` — 計画駆動の実行

| 変更対象 | 変更内容 |
|---|---|
| `save_runtime_data`(`:200`) | キーワード引数 `save_plan: SavePlan | None = None` を追加。`None` は空計画として扱う |
| 新規 private `_validate_save_plan(...)` | **事前検証**（下記）。違反は `SavePlanError` を送出し、**何も書かない** |
| `_build_split_save_payloads` / `_build_keymap_payloads` / `_build_trigger_set_payloads` | 計画を受け取り、**子ごとの保存先と「書くか否か」**を payload に含める（`"skip": bool` と最終 `path`）|
| `save_runtime_data` の書き込み部（`:226-250`） | **書き込み順序を子 → 親へ変更**（下記）。skip の子は書かない |

#### 事前検証（`_validate_save_plan`・書き込み前に全件）

1. `entries` の `kind` / `action` が定義値であること。`ACTION_SAVE_AS` は `target_path` が非空であること。
2. `key` が runtime に存在すること（keymap は id、sequence は正規化キー）。**存在しない entry はエラー**
   （UI と runtime の取り違えを早期に検出する）。
3. 同一 `(kind, key)` の entry が重複していないこと。
4. `ACTION_SAVE_AS` の `target_path` の**親ディレクトリが作成可能**であること（`os.makedirs(..., exist_ok=True)`
   を検証時に行ってよい。ファイル自体はまだ書かない）。
5. **依存関係の強制**（§2・§8）: **パスが変わる子**（`ACTION_SAVE_AS`、または現在の索引が指すパスと
   解決後のパスが異なる子）が 1 つでもあるなら、**その直接の上位を `ACTION_SKIP` にできない**。
   - sequence の上位 = **trigger_set** / keymap・trigger_set の上位 = **keymap_set**
   - keymap_set は常に保存（ラジオ対象外・暫定仕様 §2）なので、実質は
     「パスが変わる sequence があるのに trigger_set が skip」が違反ケース。
6. 違反時は**どの子のどの制約に違反したか**が分かるメッセージで `SavePlanError` を送出する。

#### 書き込み順序（§8「失敗時は旧索引を維持」）

現状は `startup → keymap_set → trigger_set → hotkey_presets → keymaps → sequences`（**親が先**）。
これを**子から親へ**変更する:

1. `ensure_split_config_dirs`
2. **sequences**（skip 以外）
3. **trigger_set**（skip なら書かない。索引の `sequence_path` は下記「skip の索引規則」に従う）
4. **keymaps**（skip 以外）
5. **hotkey_presets**（本フェーズ対象外だが keymap_set 索引に載るため keymap_set より前）
6. **keymap_set**（子の**最終パス**を索引に反映）
7. **startup / `config.json`**（`keymap_set_path` を最後に更新）
8. `keep_legacy_copy` のレガシーコピーは最後（現状どおり）

途中で例外が出れば**そのまま送出**する（presentation 側の既存 except が拾う）。この順序により、
親索引・`config.json` は旧状態のまま残る。

#### skip の索引規則（親索引に何を書くか）

| 状況 | 索引の扱い |
|---|---|
| 子が skip + **既存ファイルあり**（source_path が解決できる） | **既存パスを維持**して索引に残す（旧内容を指したまま） |
| 子が skip + **既存ファイルなし**（新規で一度も保存されていない） | **索引に載せない**（sequence は `sequence_path` を空に / keymap はエントリを載せない）。存在しないファイルを指す索引を作らない |

- この規則は**テストで固定**すること（読込時に壊れた索引を辿らないことの担保）。

### 設計メモ / 制約

- **`ACTION_SAVE` の解決は現状ロジックのまま**（source_path があればそこ、無ければ既定命名。
  trigger_set は task_02 の `_default_trigger_set_path`）。本タスクで命名規則を変えない。
- **粒度の厳守**（§8）: trigger_set を保存しても、**skip 指定された sequence は書かない**。
  逆に sequence だけ保存して trigger_set を skip することも（パスが変わらなければ）できる。
- 参照元記録（task_01）は**書いた子にだけ**更新が乗る（skip した子のファイルには触れない）。
- `SavePlan` は**値オブジェクト**として扱い、application 内で書き換えない。presentation から渡される想定の型だが、
  presentation を知らない（import しない）こと。
- 例外クラスは `save_plan.py` に置き、`config_service` から re-export しない（呼び出し側は `save_plan` を import する）。
- 新規ファイルは 300 行以内の目安を守る（`.claude/rules/implementation.md`）。

## 含まない

- **ダイアログ・行モデル・保存計画の組み立て（presentation）** → **task_05**（収集と共有状況判定は **task_04**）
- **`keymap_set_io.save_keymap_set_to` から計画を渡す配線** → **task_05**（本タスクでは `save_plan=None` のまま）
- **個別保存ボタン経路（`save_trigger_set_file` が全 sequence を書き出す点）の粒度変更** →
  本フェーズのスコープ外（暫定仕様 §11「個別保存ボタンは統合しない」）。§8 の粒度要件は**保存計画経路**に適用する
- **参照元の共有状況判定（§5）・未知→別名保存の既定** → **task_04**
- **trigger_set / keymaps の命名規則の変更** → task_02 で確定済（再変更しない）
- 正本 `spec_detail/` への反映 → **task_07**

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `../../../.venv/Scripts/python.exe`）を使う。

1. `-m compileall -q keyseq main.py tests_ui` → clean
2. `-m unittest discover -s tests` → fail 0（現在 102 件 + 新規）
3. `-m unittest discover -s tests_ui` → fail 0（現在 86 件）。
   **tests_ui は前々回モック署名不一致でモーダルがハングした前例がある**ため、
   `save_runtime_data` をモックしているテスト（`tests_ui/test_config_io_characterization_keymap_set_startup.py:181,206,225`）が
   新しい引数で壊れないことを確認する
4. `-m tests.smoke_app` → pass
5. **等価性テスト（本タスクの最重要条件）**: `tests/test_config_service.py` に、
   **`save_plan=None` と `SavePlan()`（空）で保存した結果が、task_02 時点の出力と一致**することを固定する。
   既存の `SaveLoadRoundTripTest::test_round_trip_preserves_content` /
   `TriggerSetDefaultPathTest` / `ParentRefsSchemaTest` が**すべて無修正で pass** すること
   （落ちた場合は等価性が壊れている＝実装の誤り。テスト側を書き換えて通さないこと）
6. **新規テスト**（`tests/test_save_plan.py` を新設してよい。`tests/test_config_service.py` への追加でも可）:
   - skip: 指定した sequence / keymap / trigger_set の**ファイルが書かれない**こと（他の子は書かれる）
   - 粒度: trigger_set を保存しても skip 指定の sequence は書かれないこと
   - `save_as`: 指定パスへ書かれ、**親索引がその新パスを指す**こと
   - 依存関係: パスが変わる sequence があるのに trigger_set を skip → **`SavePlanError`**、
     かつ**ファイルが 1 つも書かれていない**こと
   - 事前検証: 未知の `key` / 不正な `action` / `target_path` 空の `save_as` / `(kind, key)` 重複 → `SavePlanError`
   - **失敗時の旧索引維持**: 子の書き込みで例外が起きるようにして（repository をモック等）、
     **`keymap_set.json` と `config/config.json` が旧内容のまま**であること
   - skip の索引規則: 既存ファイルありの skip → 索引は旧パスを維持 / 既存なしの skip →
     索引に載らない（`sequence_path` が空 / keymap エントリ無し）
   - 書き込み順序: 子 → 親 → startup の順であること（repository の `save_json` 呼び出し順で固定）

## 完了条件

- 上記確認 1〜6 がすべて pass（実測は `verifier` が `.venv` で行う。Codex の自己申告は完了根拠にしない）。
- **`reviewer` 採用**（観点: 責務分離〔計画の**決定**が application へ漏れていないか＝ application は渡された計画を
  実行するだけか〕・依存方向〔`save_plan.py` が presentation / tkinter を知らないこと〕・
  仕様適合性〔§8 の 4 契約: 事前検証・依存関係の強制・粒度の厳守・失敗時の旧索引維持〕・
  不要変更〔`save_plan=None` の経路で出力が変わっていないか〕）。
- **実機目視は task_06 でまとめて実施**（本タスクでは UI 変更なし）。
