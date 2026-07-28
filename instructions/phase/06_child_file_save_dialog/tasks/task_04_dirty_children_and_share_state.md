# task_04_dirty_children_and_share_state

## 目的

保存ダイアログに並べる**行モデル**を作る（暫定仕様 05 §3-1・§4・§5）。すなわち
**① 変更（dirty）のある子の収集 → ② 保存先の解決 → ③ 参照元による共有状況の判定 → ④ 既定アクションの決定**まで。
**UI は作らない**（ダイアログは task_05）。

- レイヤ制約: **presentation の純ロジック**（tkinter を import しない新規モジュール）+
  **application へ 2 つの公開 API を追加**（保存先の解決と参照元の読み取り。判定ロジックの二重実装を避けるため）。
  domain 不変・**スキーマ不変**・**既存の保存挙動は変えない**（本タスクは読み取りと判定のみ）。
- §5 の既定は**安全側**（未知・別の上位に属す → 別名保存）。ここが後退すると共有ファイルを誤爆する。

## 対象範囲

### 1. `keyseq/application/config_service.py` — 公開 API 2 本（新規）

判定に必要な情報を presentation が**自前で再実装しない**ためのもの。既存の private な解決ロジックを再利用する。

```python
def resolve_child_save_targets(
    self, data, *, config_root: str, keymap_set_path: str, split_base_dir: str = ""
) -> dict[tuple[str, str], str]:
    """(kind, key) -> 保存先の絶対パス。kind は save_plan.CHILD_*。
    ACTION_SAVE（＝計画未指定）で保存した場合に書かれる先を、task_03 の実行経路と同じ規則で返す。"""

def read_parent_refs(self, path: str) -> list[str] | None:
    """指定パスの子JSON から `_parent_refs` を読む。ファイルが無い/読めない/キーが無い場合は None。"""
```

- `resolve_child_save_targets` は **task_03 の `_resolve_*_save_path` 系をそのまま使う**こと
  （同じ規則を 2 箇所に書かない）。**ファイルは書かない**。
- `read_parent_refs` は `_load_optional_json` + `_normalize_parent_refs` の組み合わせ。**例外を投げない**。

### 2. `keyseq/presentation/controllers/config_io/child_save_rows.py`（新規・150 行程度）

**tkinter を import しない**。App オブジェクトを受け取らず、**必要な値を引数で受ける**（テスト容易性のため）。

```python
SHARE_UNKNOWN = "unknown"        # 参照元が未知（`_parent_refs` 無し / 空）
SHARE_SOLE = "sole"              # 現在の上位のみ（単独所有）
SHARE_SHARED = "shared"          # 現在の上位を含み、かつ複数
SHARE_OTHER_PARENT = "other"     # 現在の上位が参照元に無い（別の構成に属す）
SHARE_NEW = "new"                # 保存先ファイルがまだ存在しない（新規作成）

@dataclass(frozen=True)
class ChildSaveRow:
    kind: str            # save_plan.CHILD_KEYMAP / CHILD_TRIGGER_SET / CHILD_SEQUENCE
    key: str             # keymap = id / sequence = 正規化キー / trigger_set = ""
    display_name: str    # 一覧の「対象名」（keymap = label or id / sequence = label or key / trigger_set = "トリガー一覧"）
    target_path: str     # 保存先の絶対パス（ACTION_SAVE 時の書き込み先）
    share_state: str     # SHARE_*
    share_text: str      # 一覧の「共有状況」列に出す文言（下表）
    default_action: str  # save_plan.ACTION_SAVE / ACTION_SAVE_AS

def judge_share_state(parent_refs, current_parent, *, target_exists) -> str
def share_text_for(share_state, ref_count) -> str
def default_action_for(share_state) -> str
def collect_child_save_rows(*, data, dirty_tracker, config_service, config_root, keymap_set_path) -> list[ChildSaveRow]
```

#### ① dirty な子の収集（§3-1）

`dirty_state.py` の既存フラグを使う（走査は `has_individual_dirty` と同じ流儀）:

| 種別 | dirty 判定 | key | display_name |
|---|---|---|---|
| keymap | `INTERNAL_KEYMAP_DIRTY` が真の keymap | `id` | `label`（空なら `id`）|
| trigger_set | `dirty_tracker.trigger_set_dirty` | `""` | `"トリガー一覧"` |
| sequence | `INTERNAL_SEQUENCE_DIRTY` が真の trigger | 正規化キー | `label`（空ならキー）|

- **親 keymap_set は行に含めない**（常に保存・ラジオ対象外。暫定仕様 §2）。
- 行の順序は **trigger_set → keymap → sequence** ではなく、**keymap → trigger_set → sequence** の順で安定させる
  （一覧の見え方を固定するため。実装で並べ替えたら理由をコメントに残す）。

#### ② 保存先の解決

`config_service.resolve_child_save_targets(...)` の結果を `target_path` に入れる。

#### ③ 共有状況の判定（§5 + 新規の SHARE_NEW）

`current_parent` は **keymap / trigger_set → `keymap_set_path`、sequence → その時点の trigger_set の保存先**
（`resolve_child_save_targets` の `(CHILD_TRIGGER_SET, "")` の値）。
参照元は **`target_path` のファイルから読む**（runtime が持っている refs ではなく、**これから上書きする相手**の refs を見る。
§5「保存先ファイルの参照元状態」の定義どおり）。

| 条件 | share_state | share_text | 既定 |
|---|---|---|---|
| `target_path` のファイルが存在しない | `SHARE_NEW` | 「新規作成」 | **保存** |
| `_parent_refs` が無い / 空 | `SHARE_UNKNOWN` | 「所有元不明・安全のため別名」 | **別名保存** |
| refs に現在の上位が含まれ、len == 1 | `SHARE_SOLE` | 「単独」 | 保存 |
| refs に現在の上位が含まれ、len >= 2 | `SHARE_SHARED` | 「N 個の上位で共有中・全てに影響します」 | 保存 |
| refs に現在の上位が**含まれない** | `SHARE_OTHER_PARENT` | 「別の構成に属します」 | **別名保存** |

- **`current_parent` が空文字**（keymap_set 未保存など）のときは判定不能 → **`SHARE_UNKNOWN`**（安全側）。
- パスの一致判定は **`to_config_relative_or_absolute` で保存形へ揃え、区切り文字を正規化**してから比較する
  （`_merge_parent_ref` と同じ流儀。大文字小文字は区別しない扱いにはしない ＝ 既存流儀を踏襲）。
- **`_parent_refs` が空リスト `[]`（既知・参照元ゼロ）も `SHARE_UNKNOWN` に倒す**。
  スキーマ上の「未知（None）/ 既知ゼロ（[]）」の区別は task_01 のまま維持し、**UI の既定だけ安全側に揃える**
  （どちらも「この上位が所有者だと確認できない」ため）。

#### ④ 既定アクション

`SHARE_UNKNOWN` / `SHARE_OTHER_PARENT` → `ACTION_SAVE_AS`、それ以外 → `ACTION_SAVE`（§5 の既定表）。

### 設計メモ / 制約

- **判定は presentation 側**（暫定仕様 §2「presentation が行ごとの指示を集め、application が実行」）。
  application は task_03 のとおり**渡された計画を実行するだけ**にとどめる。ここに既定判定を持ち込まない。
- `child_save_rows.py` は **tkinter を import しない**（純ロジック。UI は task_05 が使う）。
  `save_plan` の定数（`CHILD_*` / `ACTION_*`）は application から import してよい（presentation → application は正方向）。
- **`SHARE_NEW` は暫定仕様 §5 の表に無い追加**。理由: 保存先ファイルが存在しないケースは「上書き事故」が
  起こり得ず、ここを「未知 → 別名保存」にすると**新規の子すべてで別名保存ダイアログが出て実用に耐えない**ため。
  §5 の 4 状態は「既存ファイルを上書きする場合」の規則として実装し、この追加は task_07 の正本反映で明記する。
- 参照元の**読み取り対象は `target_path` のファイル**（runtime の内部キーではない）。
  runtime 側の refs は「読み込んだ元ファイルのもの」であり、別名保存や既定命名の変更で
  **書き込み先が別ファイルになる場合に誤判定する**ため使わない。
- I/O（`read_parent_refs`）は行数分だけ発生する。行数は dirty な子の数（実運用で数個〜数十個）なので許容する。
  **キャッシュや遅延読込を作らない**（過剰実装）。

## 含まない

- **ダイアログ UI・ラジオの描画・ユーザー選択の受け取り・`SavePlan` への変換** → **task_05**
- **`keymap_set_io.save_keymap_set_to` への組み込み**（保存経路への挟み込み）→ **task_05**
- **参照元の書き込み・更新**（task_01 で実装済み。本タスクは読むだけ）
- **保存計画の実行・検証**（task_03 で実装済み）
- **`dirty_tracker.trigger_set_imported` の活用可否の判断** → task_05 で判断（本タスクでは使わない）
- 正本 `spec_detail/` への反映 → **task_07**

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `../../../.venv/Scripts/python.exe`）を使う。

1. `-m compileall -q keyseq main.py tests_ui` → clean
2. `-m unittest discover -s tests` → fail 0（現在 112 件 + 新規）
3. `-m unittest discover -s tests_ui` → fail 0（現在 86 件）
4. `-m tests.smoke_app` → pass
5. **新規テスト** `tests/test_child_save_rows.py`（**tkinter を使わない**。ダミーの dirty_tracker と
   実 `ConfigService` + 一時ディレクトリで組む）:
   - 収集: dirty な keymap / trigger_set / sequence だけが行になる。**dirty が無ければ空リスト**
     （＝ task_05 でダイアログを出さない条件）。親 keymap_set は行に含まれない
   - 判定 5 パターン: `SHARE_NEW`（保存先ファイル無し）/ `SHARE_UNKNOWN`（`_parent_refs` 無し・
     および空リスト）/ `SHARE_SOLE` / `SHARE_SHARED`（refs 2 件以上・`share_text` に件数が入る）/
     `SHARE_OTHER_PARENT`（refs に現在の上位が無い）
   - 既定アクション: `SHARE_UNKNOWN` と `SHARE_OTHER_PARENT` のみ `ACTION_SAVE_AS`、他は `ACTION_SAVE`
   - `current_parent` が空文字 → `SHARE_UNKNOWN`（安全側）
   - パス比較: config_root 相対と絶対、`/` と `\` 混在でも同一の上位として一致すること
   - sequence の上位が **trigger_set の保存先**であること（keymap_set ではない。§2 の参照階層）
   - `target_path` が task_03 の実行経路と一致すること
     （`resolve_child_save_targets` の結果と、実際に `save_runtime_data(save_plan=None)` で
     書かれたファイルのパスが一致する — **二重実装していないことの担保**）
6. `read_parent_refs`: ファイル無し / JSON 壊れ / キー無し → いずれも `None` を返し**例外を投げない**

## 完了条件

- 上記確認 1〜6 がすべて pass（実測は `verifier` が `.venv` で行う。Codex の自己申告は完了根拠にしない）。
- **`reviewer` 採用**（観点: 依存方向〔`child_save_rows.py` が tkinter を持ち込んでいないか / application に
  既定判定が漏れていないか〕・仕様適合性〔§5 の既定が安全側から後退していないか〕・
  不要変更〔保存挙動を変えていないか＝読み取りと判定のみか〕・過剰実装〔キャッシュ・抽象化の作り込みが無いか〕・
  **保存先解決の二重実装が無いか**）。
- **実機目視は task_06 でまとめて実施**（本タスクでは UI 変更なし）。
