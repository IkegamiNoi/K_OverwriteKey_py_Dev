# task_02b_custody_handback

## 目的

暫定仕様 15 **§3-2(8)（v0.5・ユーザー確定 2026-09-16）** を実装する。
預かりを §3-2(7) で新モーダルへ引き継いだ後、**その新モーダルが復元より前に破棄されると
grab 保持者がゼロになる**（phase 14 の `<Destroy>` 復元が「保持者が非表示」でスキップされ、
預かりも空のまま）。**最小化中に限り、復元できなかった保持者を預かりへ戻す**。

task_03 の受け入れテスト **A9（`test_a9_new_modal_closed_before_restore_returns_custody`）が
現在 fail しており、本タスクで pass にする**（判断の経緯は `.claude_data/state/decisions.md` の
2026-09-16 節）。**presentation 限定・スキーマ不変**。

## 対象範囲（`keyseq/presentation/modal.py` のみ）

### 1. 最小化中フラグ

- モジュールレベルに **`_app_minimized: bool = False`** を追加する。
- `install_minimize_grab_custody` の **`<Unmap>` ハンドラで `True`**、**`<Map>` ハンドラで `False`**
  にする（いずれも **`event.widget is app` のガードを通った後**。他ウィジェットの unmap で立てない）。
- **預かりが成立したかどうかとは独立**に立てる（表示中の保持者で預からなかった場合も、
  最小化中であることは事実なので `True`）。

### 2. `restore_grab`（`grab_modal` 内）からの差し戻し

- 既存の復元条件は**変えない**。**復元を行わなかった経路**のうち、
  **「`previous` が生存しているが `winfo_viewable()` が 0 で `grab_set()` しなかった」場合**に、
  **`_app_minimized` が `True` かつ `_custody_window is None` なら `_custody_window = previous`** とする。
- **差し戻さない場合**（変更しないこと）:
  - `previous` が `None`（記録なし）/ `previous` が既に破棄済み（`winfo_exists()` が偽）
  - `current` が自窓以外（= 内側のモーダルが生きている。既存の早期 return）
  - **`_app_minimized` が `False`**（最小化していないのに預かりへ入れると、
    **次の最小化で「既に預かり中」ガードに阻まれ本来の預かりが起きない**）
  - **`_custody_window` が既に非 `None`**（現に預かっている窓を上書きしない）
- `<Map>` 側は**変更不要**（差し戻された窓は既存のガードどおり「生存かつ表示中なら張り直す /
  そうでなければ台帳の最内へ」で扱われる）。

### 設計メモ / 制約

- **`<Unmap>` / `<Map>` のガード 4 種・`grab_modal` の既存分岐・台帳（task_01）は変更しない**。
  追加するのはフラグ 1 つと `restore_grab` の 1 分岐のみ。
- **`deiconify()` / `lift()` / `focus_force()` を呼ばない**（本タスクでも不変）。
- 例外の握り潰しは既存範囲を広げない（`winfo_*` / `grab_*` の `tk.TclError` のみ）。
- **`install_minimize_grab_custody` を呼んでいない環境**（`tests_ui/test_modal_grab.py` の
  自前 `tk.Tk()` 等）では `_app_minimized` は `False` のままなので、**既存の復元挙動は変わらない**。
  これを崩さないこと（既存テストが落ちたら実装を疑う）。

### テスト

- **A9 は task_03 で追加済み**（`tests_ui/test_minimize_grab_custody.py`）。**本タスクで新規追加しない**。
- ただし **`tests_ui/test_modal_grab.py` に 1 本だけ**、**最小化していないときに差し戻しが
  起きないこと**（非表示の `previous` が `_custody_window` へ入らない）を固定する
  （フラグを外すと落ちる = §3-2(8) のガードの担保）。

## 含まない

- 受け入れテストの追加・修正・変異検査（**task_03**）
- 統合確認・二次レビュー・実機目視（**task_04**）
- 正本反映・暫定仕様 15 の凍結（**task_05**）
- `<Map>` / `<Unmap>` のガード変更 / 台帳の仕様変更 / stdlib ダイアログ対応

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier`**。

1. `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
2. `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_minimize_grab_custody` で
   **A9 が pass**（A7 は task_03 で修正するため fail のままでよい）
3. `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_modal_grab` が全 pass（+ 新規 1 本）
4. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass（417・skip 7）
5. `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が通る

## 完了条件

- 上記確認が pass・**`reviewer` 採用**（観点: **フラグの立て下ろしの正しさ** /
  **差し戻し条件の過不足** / phase 14 の復元規則を壊していないか）。
- 実機目視は **task_04** でまとめて実施。
