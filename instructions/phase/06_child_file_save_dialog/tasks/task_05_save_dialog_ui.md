# task_05_save_dialog_ui

## 目的

子ファイル保存の確認ダイアログを実装し、keymap_set 一括保存経路へ挟み込む（暫定仕様 05 §3・§5・§8）。
task_04 の行モデル（`ChildSaveRow`）を並べてユーザーに 保存 / 別名保存 / 保存しない を選ばせ、
選択を **`SavePlan` へ変換**して task_03 の実行契約に乗せる。

- レイヤ制約: **presentation 主体**（ダイアログ・選択の収集・計画の組み立て）。
  application へは**依存関係の照会 API 1 本のみ追加**（判定規則の二重実装を避けるため）。
  **domain 不変・スキーマ不変・保存の実行順序は task_03 のまま**（presentation が書き込み順を握らない）。
- **依存関係の扱い（ユーザー確定 2026-07-29）**:
  - **親 keymap_set は問わない**（「保存」操作自体が明示なので常に保存・ラジオ対象外）。
  - **trigger_set は問う**。出力シーケンスの保存先が変わるのに trigger_set が「保存しない」のときは、
    **OK 押下時に確認ダイアログ**を出し、理由（原因シーケンス・保存先・共有状況）を示して選ばせる。
    一覧のラジオは**静的に無効化しない**（「保存しない」は常に選べる）。
  - `SavePlanError`（task_03）は**内部不変条件の番人として残す**（UI からは到達しない状態にする）。

## 対象範囲（presentation 主体・application は照会 API 1 本のみ）

### 1. `keyseq/application/config_service.py` — 公開 API 1 本（新規）+ 既存 API に引数追加

```python
def find_dependency_blocked_sequences(
    self, data, *, config_root: str, keymap_set_path: str,
    split_base_dir: str = "", save_plan: SavePlan,
) -> list[str]:
    """save_plan のとおり保存したとき、trigger_set の保存が必要になる sequence の
    正規化キー一覧を返す。trigger_set が ACTION_SKIP でなければ常に空。ファイルは書かない。"""

def resolve_child_save_targets(  # task_04 の既存 API に引数追加
    self, data, *, config_root: str, keymap_set_path: str,
    split_base_dir: str = "", save_plan: SavePlan | None = None,  # ← 追加（既定 None = 空計画・現状と同一）
) -> dict[tuple[str, str], str]:
```

- **判定規則は `_validate_save_plan` の trigger_set 節（`config_service.py:732-744`）を
  private ヘルパ（例 `_sequence_keys_requiring_trigger_set_save(payloads)`）へ切り出して共有する**。
  同じ条件（`ACTION_SAVE_AS` / `source_path` 空 / 解決先が `source_path` と異なる、かつ skip でない）を
  2 箇所に書かない。`_validate_save_plan` は切り出し先を呼ぶ形へ置き換える（挙動不変）。
- payloads の生成は `resolve_child_save_targets`（task_04）と同じ流儀で**書き込みなし**に行う。
- **`resolve_child_save_targets` への `save_plan` 追加は必須**（敵対的レビュー指摘①）。
  `_resolve_sequence_save_path`（`config_service.py:1169-1192`）は **`trigger_set_path` が
  `config/user/trigger_sets/` 配下かどうかで sequence の既定保存先を
  `user/sequences/` と `<trigger_set の隣>/sequences/` に切り替える**ため、
  **trigger_set を別名保存すると他の子の保存先が変わる**。計画を渡さずに解決した結果を
  使い回すと、一覧の保存先パス・共有状況・非 dirty 子の SKIP/SAVE 判定が陳腐化する。
  既定 `None` のときは現状（空計画）と同一の結果を返すこと（task_04 のテストは無修正で pass）。

### 2. `keyseq/presentation/controllers/config_io/child_save_rows.py` — 小改修

- `collect_child_save_rows(...)` に **`split_base_dir: str = ""` と `save_plan: SavePlan | None = None` を追加**し、
  `resolve_child_save_targets` へそのまま渡す（config_root 外保存・trigger_set の別名保存で
  保存先が変わるため。既定値のときは現状と同一挙動）。
- 内部の `_build_row` を **`build_row` として公開**する（引数・戻り値は現状のまま）。
  依存確認ダイアログで **trigger_set 行が一覧に無い（非 dirty）ときにも共有状況を提示する**ために使う。

### 3. `keyseq/presentation/controllers/config_io/child_save_plan.py`（新規・**tkinter を import しない**・120 行程度）

選択結果 → `SavePlan` の純変換。`tests/` から tkinter 無しで検証できるようにする。

```python
def build_save_plan(*, data, rows, choices, targets) -> SavePlan
```

- `choices`: `{(kind, key): (action, target_path)}`。`rows` に載っている子（＝ dirty）だけが対象。
  `ACTION_SAVE_AS` の `target_path` は task_05-4 のダイアログが確定済みの絶対パス。
- `targets`: `config_service.resolve_child_save_targets(...)` の戻り値（全子ファイル分）。
  **その時点で確定している trigger_set の選択（`save_plan`）を反映済みのもの**を受け取る前提で書く
  （再解決の責務は呼び出し元 = 5 の保存経路。この関数では解決しない）。
- **dirty でない子（`rows` に無い子）の既定**（暫定仕様 §3-1・受入条件 2・ユーザー確定 2026-07-29）:

  | 保存先ファイル | エントリ |
  |---|---|
  | 既に存在する | `ACTION_SKIP`（変更が無いので書かない） |
  | 存在しない | `ACTION_SAVE`（**索引切れ防止**。skip すると `keymap_set` の索引パスが空になる〔`config_service.py:1032-1037`〕） |

- エントリは **keymap（全 id）→ trigger_set → sequence（全キー）** の順で、
  **すべての子について明示的に**作る（計画未指定＝ ACTION_SAVE の暗黙既定に頼らない）。
- 純関数として書く（`config_service` / `dirty_tracker` を引数に取らない。存在確認の `os.path.exists` のみ許容）。

### 4. `keyseq/presentation/controllers/config_io/child_save_dialog.py`（新規・200 行程度）

`IoDialogs.ask_link_label_to_filename`（`io_dialogs.py:29-63`）と同じ流儀の**モーダル Toplevel**。
App に `self.child_save_dialog = ChildSaveDialog(self)` として登録する（`app.py:142-147` の並びへ 1 行追加）。

```python
class ChildSaveDialog:
    def ask_child_save_actions(self, rows) -> dict | None:
        """一覧を出して {(kind, key): (action, target_path)} を返す。キャンセルは None。"""
    def confirm_trigger_set_dependency(self, *, blocked_labels, trigger_set_row) -> str:
        """依存確認。戻り値は ACTION_SAVE / ACTION_SAVE_AS / ""（＝選び直す）。"""
```

- **一覧**: 1 行 = 1 子ファイル。列は **種別 / 対象名 / 保存先パス / 共有状況 / ラジオ 3 択**。
  種別の表示名は キーマップ / トリガー一覧 / 出力シーケンス。行順は `rows` の順（task_04 が確定済み）。
  各行 1 個の `tk.StringVar`（初期値 = `row.default_action`）＋ `ttk.Radiobutton` 3 個。
- **別名保存のパス確定は OK 押下時**にまとめて行う（暫定仕様 §3-2）。`ACTION_SAVE_AS` の行ごとに
  `filedialog.asksaveasfilename`（`initialdir` / `initialfile` は `row.target_path` 由来・`defaultextension=".json"`）。
  **1 つでもキャンセルされたら一覧へ戻る**（選択状態は維持・保存は開始しない）。
- **依存確認**は `messagebox.askyesnocancel`（`choose_save_path_with_collision` と同じ流儀）。
  文面に **原因の出力シーケンス名・trigger_set の保存先パス・共有状況（§5 の文言）** を入れ、
  「はい」= このまま保存 /「いいえ」= 別名で保存 /「キャンセル」= 選び直す を明記する。
  「いいえ」なら `asksaveasfilename` で trigger_set の保存先を決める（キャンセルされたら選び直しへ）。
- **既定ボタンを共有状況で切り替える**（敵対的レビュー指摘②。§5 の安全側既定が依存経路だけ
  後退するのを防ぐ）。文面での推奨だけに頼らない:

  ```python
  default = messagebox.NO if row.share_state in (SHARE_UNKNOWN, SHARE_OTHER_PARENT) else messagebox.YES
  messagebox.askyesnocancel(..., default=default)
  ```

  `SHARE_UNKNOWN` / `SHARE_OTHER_PARENT` のときは**別名保存を推奨する 1 行**も文面に足す。
  専用の 3 ボタン Toplevel は**作らない**（`default=` で足りる。過剰実装）。
- フックの停止/再開（`self._app.hook.suspend_hook_for_dialog()` / `resume_hook_after_dialog()`）を
  `try/finally` で行い、`transient` / `grab_set` / `protocol("WM_DELETE_WINDOW", ...)` / `wait_window` を設定する。
- **縦スクロール（Canvas + Scrollbar）は作らない**（過剰実装。実運用の dirty 行数は数個。
  行数が多い場合の見え方は task_06 の実機目視で確認し、問題があれば別 idea とする）。

### 5. `keyseq/presentation/controllers/config_io/keymap_set_io.py` — `save_keymap_set_to` への挟み込み

`save_path` / `split_base_dir` の確定後・`save_runtime_data` 呼び出し前に挟む。
**trigger_set の保存先が変わると他の子の保存先も変わる**ため（1 の指摘①）、
「解決 → 一覧 → 依存確認」を **`while` ループ**にし、trigger_set の選択が確定するたび**解決からやり直す**。

```
pending = SavePlan()            # 確定済みの trigger_set エントリだけを持つ部分計画（初回は空）
while True:
    targets = resolve_child_save_targets(data, ..., keymap_set_path=save_path,
                                         split_base_dir=split_base_dir, save_plan=pending)
    rows    = collect_child_save_rows(..., keymap_set_path=save_path,
                                      split_base_dir=split_base_dir, save_plan=pending)
    choices = {} if not rows else ask_child_save_actions(rows)   # rows 空 → ダイアログを出さない
    if choices is None: return False                              # キャンセル
    plan = build_save_plan(data=..., rows=rows, choices=choices, targets=targets)
    if trigger_set の保存先が targets と変わる選択が入った:        # 一覧で別名保存を選んだ場合
        pending = その trigger_set エントリのみの SavePlan; continue   # 再解決 + 一覧再表示
    blocked = find_dependency_blocked_sequences(..., save_plan=plan)
    if blocked:
        result = confirm_trigger_set_dependency(...)
        if result == "": pending = SavePlan(); continue            # 選び直す
        pending = 選択した trigger_set エントリのみの SavePlan; continue  # 再解決 + 一覧再表示
    break
save_runtime_data(..., save_plan=plan)
```

- **`keymap_set_path` は「これから保存する先」`save_path`**（現在のパスではない。共有状況の判定基準）。
- **`rows` が空ならダイアログを出さない**（受入条件 2）。空でも計画は組む（＝ 非 dirty の子は書かない・親のみ保存）。
- **キャンセル（`None`）は 1 バイトも書かずに `False` を返す**（フラッシュ表示は「保存を中止しました。」）。
- **再表示の終了性**: `pending` の trigger_set 保存先が**前周と同じなら再ループしない**
  （`continue` は保存先が実際に変わったときだけ）。ユーザーが毎回別のパスを選ぶ場合を除き 2 周で確定する。
- 再表示のときは一覧の上部に 1 行の注記を出す:
  「トリガー一覧の保存先が変わったため、出力シーケンスの保存先を再計算しました。」
- 一覧で選び直した内容は**破棄して再表示してよい**（部分的な引き継ぎは作らない。過剰実装）。
- `save_runtime_data(..., save_plan=plan)` の既存引数はそのまま。
- 成功後の dirty クリアは **`ACTION_SKIP` の子だけ残す**形にする（下記 6 の選択的クリア）。
  `set_dirty(False)` の後に `dirty_tracker.sync_dirty_state()` を呼び、
  残った個別 dirty が `is_dirty` / ファイル状態表示へ反映されるようにする。
- 例外処理（`except Exception` → `messagebox.showerror("保存失敗", ...)`）は現状のまま。
  `SavePlanError` も同じ経路で表示される（**UI からは到達しない想定**の保険）。

### 6. `keyseq/presentation/controllers/dirty_state.py` — 選択的クリア

```python
def clear_individual_dirty_flags(self, *, skipped_keymap_ids=None, skipped_sequence_keys=None,
                                 skip_trigger_set: bool = False) -> None
```

- 既定引数なしの呼び出しは**現状と同一挙動**（全クリア）。指定された子の
  `INTERNAL_*_DIRTY` は **True のまま残す**（`*_IMPORTED` も同様に触らない）。
- 理由: 「保存しない」を選んだ子の未保存状態が消えると、**変更が黙って失われたように見える**。
- キーの正規化は `normalize_key_name` に揃える（sequence キー / keymap id の比較）。

### 設計メモ / 制約

- **決定は presentation・実行は application**（暫定仕様 §2）。`config_service` に
  ダイアログ・既定判定・依存の解決策を持ち込まない（追加 API は**照会のみ・書き込みなし**）。
- 依存の**判定規則**は application 側 1 箇所（切り出したヘルパ）に置き、presentation は結果だけ使う。
  presentation で「パスが変わったか」を再計算しない。
- `child_save_plan.py` は **tkinter を import しない**（`tests/` から直接テストする）。
  ダイアログ（`child_save_dialog.py`）は**選択を集めるだけ**で、計画の組み立て規則を持たない。
- `dirty_tracker.trigger_set_imported` は**本タスクでも使わない**（読み手不在の残置状態。task_04 からの申し送り。
  扱いは task_07 で判断する）。
- 別名保存後の `source_path` 更新・`_parent_refs` の追記は **task_01 / task_03 で実装済み**（application 側）。
  presentation から二重に書かない。
- **不変条件（敵対的レビュー 2026-07-29 の指摘①②への対応）**:
  ① **ユーザーに提示した保存先と、実際に書く保存先を一致させる**。trigger_set の保存先が変わったら
  必ず解決からやり直し、古い `targets` で組んだ計画を実行しない。
  ② **未知 / 別の上位に属す保存先を、ユーザーの明示操作なしに上書きしない**。一覧の既定（§5）だけでなく、
  依存確認の既定ボタンでも安全側に倒す。

## 含まない

- **受入条件 §10 の 1〜11 の統合退行・既存特性テストの期待値更新・実機目視** → **task_06**
- **正本 `spec_detail/` への反映**（依存確認ダイアログの仕様・`SHARE_NEW`・非 dirty 子の SKIP 規則の明記）→ **task_07**
- **既存の個別保存ボタン（各 box）の統合** → スコープ外（暫定仕様 §11）
- **参照元の掃除機能** → idea_07（β 完了後） / **hotkey_presets** → 触らない（暫定 07）
- **一覧の縦スクロール・列幅調整・並べ替え・検索**（過剰実装）
- **keymap_set 自身をラジオ対象にすること**（常に保存・ユーザー確定 2026-07-29）
- **`dirty_tracker.trigger_set_imported` の活用可否の判断** → task_07

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `../../../.venv/Scripts/python.exe`）を使う。

1. `-m compileall -q keyseq main.py tests_ui` → clean
2. `-m unittest discover -s tests` → fail 0（現在 119 件 + 新規）
3. `-m unittest discover -s tests_ui` → fail 0（現在 86 件 + 新規）
4. `-m tests.smoke_app` → pass
5. **新規** `tests/test_child_save_plan.py`（tkinter 不使用）:
   - dirty な子の選択（保存 / 別名保存 / 保存しない）がそのままエントリになる
   - **非 dirty かつ保存先が存在する子 → `ACTION_SKIP`** / **非 dirty かつ保存先が無い子 → `ACTION_SAVE`**
   - `rows` が空でも全子ファイル分のエントリが作られる（保存先が有る子はすべて SKIP）
   - エントリの重複が無く、`SavePlan` が `_validate_save_plan` を通る（`save_runtime_data` で例外が出ない）
6. **新規** `tests/test_dependency_query.py`（または `tests/test_config_service.py` へ追加）:
   - trigger_set が `ACTION_SKIP` + sequence が `ACTION_SAVE_AS` → 該当キーが返る
   - trigger_set が `ACTION_SKIP` + sequence が `source_path` 未設定（初回保存）→ 該当キーが返る
   - trigger_set が `ACTION_SAVE` → 常に空リスト
   - **照会だけでファイルが 1 つも作られない**（呼び出し前後でディレクトリ内容が不変）
   - 同条件で `save_runtime_data` を呼ぶと `SavePlanError` になる（判定規則の一致 = 二重実装が無いことの担保）
   - **`resolve_child_save_targets` の `save_plan` 反映**（指摘①）: trigger_set を
     `config/user/trigger_sets/` **外**へ `ACTION_SAVE_AS` する計画を渡すと、`source_path` を持たない
     sequence の解決先が `user/sequences/` から **`<trigger_set の隣>/sequences/`** へ変わる。
     `save_plan=None` の結果は task_04 と同一（既存テスト無修正で pass）
7. **新規** `tests_ui/test_child_save_dialog.py`（既存 `tests_ui` の monkeypatch 手法を踏襲。
   `ask_child_save_actions` / `confirm_trigger_set_dependency` / `asksaveasfilename` を差し替える）:
   - dirty な子が無い → **ダイアログが呼ばれず**、親 keymap_set.json のみ更新（子ファイルの mtime / バイト列が不変）
   - dirty な子がある → 一覧が 1 回呼ばれ、選択どおりに書かれる（保存＝上書き / 別名＝新パス /
     保存しない＝**旧ファイルのバイト列が不変**）
   - **キャンセル（`None`）→ 親も子も 1 バイトも書かれない**・戻り値 `False`
   - **依存**: sequence を別名保存 + trigger_set を保存しない → `confirm_trigger_set_dependency` が
     **1 回呼ばれる**。「保存」を選べば trigger_set が書かれる／「選び直す」を返せば一覧が再表示され、
     2 回目でキャンセルすると何も書かれない
   - 依存が無いとき（sequence を全て保存しない等）は `confirm_trigger_set_dependency` が**呼ばれない**
   - **保存しないを選んだ子の dirty フラグが残る**（保存後も `has_unsaved_changes()` が True）
   - **再解決と一覧再表示**（指摘①）: trigger_set を `config/user/trigger_sets/` 外へ別名保存すると
     **`ask_child_save_actions` が 2 回呼ばれ**、2 回目の `rows` の sequence の `target_path` が
     新しい trigger_set の隣へ変わっている。**保存先が変わらない選択では再表示されない**（1 回のみ）
   - **陳腐化した判定で書かない**（指摘①）: 上記の再解決後、非 dirty sequence が
     新保存先に実体が無ければ書かれ（索引切れなし）、新保存先に**既存の別ファイルがあっても
     ユーザー選択なしに上書きしない**（＝ 再表示された一覧の共有状況・既定が新パス基準になっている）
8. **既定ボタン**（指摘②）: `messagebox.askyesnocancel` を差し替えて kwargs を捕捉し、
   trigger_set の共有状況が `SHARE_UNKNOWN` / `SHARE_OTHER_PARENT` のとき **`default=messagebox.NO`**、
   `SHARE_SOLE` / `SHARE_SHARED` / `SHARE_NEW` のとき `default=messagebox.YES` で呼ばれること
8. 静的確認: `child_save_plan.py` / `child_save_rows.py` が `tkinter` を import していないこと（grep）。
   `config_service.py` に `tkinter` / ダイアログ呼び出しが増えていないこと

## 完了条件

- 上記確認 1〜8 がすべて pass（実測は `verifier` が `.venv` で行う。Codex の自己申告は完了根拠にしない）。
- **`reviewer` 採用**（観点: 依存方向〔ダイアログが application に漏れていないか / `child_save_plan.py` が
  純ロジックか〕・仕様適合性〔§3 の挟み込み条件・§5 の既定・依存確認のユーザー確定内容
  〔親は問わない・trigger_set は問う・静的無効化しない〕〕・責務分離〔計画の組み立て規則が
  ダイアログ側に散っていないか〕・不要変更〔保存の実行順序・既存 API の互換を壊していないか〕・
  チェック漏れ〔キャンセル時に 1 バイトも書かないこと・SKIP 子の dirty 保持〕）。
- **実機目視は task_06 でまとめて実施**（本タスクでは自動テストのみ）。
