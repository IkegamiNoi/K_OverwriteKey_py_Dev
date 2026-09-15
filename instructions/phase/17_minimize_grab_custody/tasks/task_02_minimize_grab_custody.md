# task_02_minimize_grab_custody

## 目的

暫定仕様 15 §3-1 / §3-2 に基づき、**最小化の間だけ grab を預かる**機構を実装する。
App が unmap（最小化）されたら**隠れた grab 保持者**から grab を外し、map（復元）されたら
同じ窓へ張り直す。これによりシェルの復元要求が App へ届き、**ダイアログを開いたまま
最小化しても復元できる**ようになる（§1 の実測が根拠）。

**presentation 限定・domain / application / infrastructure 不変・スキーマ不変。**
台帳（task_01 で追加した `_active_modals`）を**初めて読む**のは本タスク。

## 対象範囲（presentation 限定・`modal.py` / `app.py` / `tests_ui/test_modal_grab.py`）

### keyseq/presentation/modal.py

#### 1. 預かり状態（モジュールレベル）

- `_custody_window: tk.Toplevel | None = None` を追加する（**預かり中の窓。無ければ `None`**）。
  `grab_modal` からも見える位置に置く（§3-2(7) のため・§3-3）。

#### 2. `install_minimize_grab_custody(app: tk.Misc) -> None`

- **App の初期化で 1 度だけ呼ぶ**前提の結線関数。**引数の型注釈に `App` を使わない**
  （`modal.py` → `app.py` の循環 import になる。`tk.Misc` で受ける・§3-3）。
- `app.bind("<Unmap>", ..., "+")` と `app.bind("<Map>", ..., "+")` を結線する
  （**必ず `add="+"`**。既存・将来のハンドラを消さない）。

#### 3. `<Unmap>`（預かる）— ガードは以下を**すべて**満たすときだけ預かる

1. **`event.widget is app`**（App 自身の unmap に限定。**`Frame.pack_forget()` 等でも
   toplevel のバインドへ届く**ため必須・§3-2(4)）
2. **まだ預かっていない**（`_custody_window is None`。二重発火の防止）
3. **`grab_current()` が解決できる**こと。**`tk.TclError` / `KeyError` は吸収し、
   解決不能なら預からない**（stdlib ダイアログが grab 中。§3-2(5)・対象外と確定済）
4. 保持者が **`None` でない**こと
5. **保持者が既に非表示**（`winfo_exists()` かつ **`winfo_viewable()` が 0**）であること。
   **表示されたままの保持者は預からない**（`transient` を持たない窓・呼び出し元を先に破棄された子は
   最小化で隠れず症状も起きない。外すと**表示中のモーダルから grab を奪う**・§3-2(1)）

満たしたら `grab_release()` してから `_custody_window` に保持者を記録する
（**解放に失敗（`tk.TclError`）したら記録しない**）。

#### 4. `<Map>`（返す）

1. **`event.widget is app`** でなければ何もしない
2. `_custody_window is None` なら何もしない
3. **預かりはこの時点で必ず解除する**（`_custody_window = None`）。以降で張り直さない場合も同じ
4. `grab_current()` が**解決不能なら何もしない**（`grab_set()` を呼ばない。「保持者なし」と
   同一視すると **stdlib ダイアログの grab を奪う**・§3-2(5)）
5. **現在の保持者が `None` でなければ張り直さない**（別窓が既に grab 中なら上書きしない・§3-2(2)）
6. 張り直し先の決定:
   - 記録した窓が **`winfo_exists()` かつ `winfo_viewable()`** ならその窓
   - そうでなければ **台帳 `_active_modals` を末尾から探し、最初に見つかった
     「`winfo_exists()` かつ `winfo_viewable()`」な窓**（= 生存かつ表示中の最内モーダル・§3-5）
   - どちらも見つからなければ**何もしない**
7. **`deiconify()` / `lift()` / `focus_force()` を呼ばない**（WM が既に復元済み。
   実測で中間窓が消えた・§3-1）

#### 5. `grab_modal` の結線（預かり中に新しいモーダルが開いた場合・§3-2(7)）

- `previous = current_holder()` が **`None` かつ `_custody_window` が非 `None`** のとき、
  **`previous` を預かり中の窓にし、預かりを解除する**（`_custody_window = None`）。
- こうしないと新窓の `previous` が `None` になり、**新窓を閉じたときに誰も grab を持たない**。
- **それ以外の分岐（保持者が居る場合）では預かり状態に触らない**
  （`<Map>` のガード 5 が「別窓が grab 中なら張り直さない」を担保する）。
- 台帳への追加・除去（task_01）と既存の復元規則は**変更しない**。

### keyseq/presentation/app.py

- `install_minimize_grab_custody` を import し、`__init__` の**最後**
  （`self.protocol("WM_DELETE_WINDOW", self.on_close)` の直前か直後）で
  **`install_minimize_grab_custody(self)` を 1 度だけ呼ぶ**。
- **他の変更を加えない**（`app.py` はこの 2 行のみ）。

### 設計メモ / 制約

- **例外の扱いを明示する**: イベントハンドラ内の未捕捉例外は `report_callback_exception` を
  経由して**既存テストを落とす**（`tests_ui/test_nested_modal_grab.py:40-42`）。
  吸収するのは **`grab_current()` の `tk.TclError` / `KeyError`** と
  **`grab_release()` / `grab_set()` / `winfo_*` の `tk.TclError`** に限る。握り潰しの範囲を広げない。
- **`<Map>` のガード 6 の補足（実装判断）**: 暫定仕様 §3-2(6) / §3-5 は「**保持者が破棄されていた
  場合**」の張り直しを規定するが、本タスクでは「**記録した窓が生存かつ表示中でない場合**」
  （= 破棄済み **または** 非表示）を台帳フォールバックの条件とする。**非表示の窓を掴まない**という
  §3-2(2) のガードは保たれ、見えない窓が入力を握る事態を作らない。
- 預かり状態は `_custody_window` のみ。**ウィジェット属性を増やさない**（phase 14 の方針）。
- **`install_minimize_grab_custody` を複数回呼ぶ想定はしない**（App 初期化の 1 回のみ）。
  多重呼び出しのガードは**実装しない**（過剰実装）。

### tests_ui/test_modal_grab.py（最小限の結線テストを追加）

**受け入れ条件 12 項目の網羅と変異検査は task_03**。本タスクでは**結線が働くこと**を固定する:

1. `install_minimize_grab_custody(root)` 後、`root.iconify()` で**隠れた保持者から grab が外れる**
   （`grab_current()` が `None` になる）
2. `root.deiconify()` で**同じ窓へ grab が戻る**
3. **表示されたままの保持者からは grab を外さない**（`<Unmap>` を送っても `grab_current()` 不変）
4. **App 以外の `<Unmap>`**（`event.widget` が別ウィジェット）では預かりが発生しない
5. 預かり中に `grab_modal` で新しい窓を開き、それを破棄すると**預かっていた窓へ grab が戻る**

- **ハーネスの注意**: `tests_ui` は `setUpClass` で App を共有するモジュールがある。
  **`iconify()` したまま tearDown すると iconic 状態が後続モジュールへ漏れる**ため、
  cleanup で必ず `deiconify()` して戻すこと（§4）。
- **テスト独立**: `_active_modals` に加え **`_custody_window` も `patch.object` で
  毎テスト初期化**する（モジュール状態）。
- 既存テスト・既存アサーションは**弱めない**。

## 含まない

- 暫定仕様 §6 の受け入れ条件 12 項目の網羅テスト・**変異検査**（**task_03**）
- 統合確認（`tests` / `tests_ui` 全体 + `smoke_app`）・二次レビュー・実機目視（**task_04**）
- 正本反映（`features.md` §4.6 の `:92` 限定 + 条項追加 / `codebase_map.md` の `modal.py` 節）・
  暫定仕様 15 の凍結（**task_05**）
- **stdlib ダイアログ（`messagebox` / `filedialog`）が grab 中の最小化**（対象外と確定・症状は残す）
- 窓構成の変更（ダイアログをタスクバーに載せる等）/ phase 14・15・16 の設計変更 /
  `deiconify()` 等による能動的な復元

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier`**（Codex は python を実行できない）。

1. `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
2. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass
   （既存 331 + 追加分。`test_nested_modal_grab.py` の**静的検査**・`test_dialog_transient_parent.py`・
   `test_dialog_teardown_flows.py` が落ちないこと）
3. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass
4. `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が通る（App 初期化に結線を足すため）
5. 追加テスト 5 項目（上記）が pass

## 完了条件

- 上記確認がすべて pass・**`reviewer` 採用**（観点に phase.md「レビュー方針」の
  **ガードの欠落** / **phase 14 の資産への影響** / **復元時に窓を触っていないか**を含める）。
- **実機目視は本タスクでは行わない**（task_04 でまとめて実施）。
- `app.py` の変更が import 1 行 + 呼び出し 1 行に収まっていること。
