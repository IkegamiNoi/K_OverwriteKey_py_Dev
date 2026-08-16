# task_04_cleanup_ui

## 目的

参照元の掃除を**メニューから実行できるようにする**（暫定仕様 09 **§3-3 / §3-4**）。
検査（task_01）→ 確認 UI（1 枚）→ 除去（task_02）→ 結果通知 を 1 本のフローとして配線し、
**未保存の構成セットでは先に保存の確認**を出す。

**レイヤ制約**: **presentation 中心**。application 側は
**`ConfigService` への委譲メソッド 2 本の追加のみ**（ロジックは足さない）。
**`parent_refs_cleanup.py` と `reference_cleanup_text.py` を変更しない**（task_01〜03 の成果を使う）。

## 対象範囲（変更ファイル単位）

### 1. `keyseq/application/config_service/__init__.py`（**委譲 2 行のみ**）

presentation から兄弟モジュールを直接 import しない規約のため、**公開面だけを足す**:

- `inspect_parent_refs(self, runtime, *, config_root, keymap_set_path)`
- `prune_parent_refs(self, inspections, *, runtime, config_root, keymap_set_path)`

いずれも **`parent_refs_cleanup` のモジュール関数へ 1 行で委譲する**だけにする
（**同ファイルは 737 行で分割保留中**。ロジック・分岐を足さない）。

### 2. `keyseq/presentation/dialogs/reference_cleanup_dialog.py`（新規）

- **`tk.Toplevel` を継承**し、`dialogs/` の流儀に揃える
  （**`__init__` で `suspend_hook_for_dialog()` / `destroy()` の override で `resume_hook_after_dialog()`**。
  `LayoutDeleteDialog` が先例）。
- **読み取り専用のスクロール可能な一覧**（`Text` を `state="disabled"` 等）に、
  task_03 の `format_cleanup_plan` が返した**行をそのまま**表示する。
  **ダイアログ側で内容を要約・省略しない**（消えるパスの全件提示が要件）。
- ボタンは **実行 / キャンセルの 2 つ**。**行ごとの選択は設けない**。
- **結果は `self.result`（bool）** で返す（実行 = `True` / キャンセル・× で閉じる = `False`）。
  **既定は `False`**（× や Esc で閉じたときに実行されないこと）。
- `transient` / `grab_set` / `protocol("WM_DELETE_WINDOW", ...)` は**同フォルダの既存ダイアログと同じ作法**。
  **grab の復元処理は書かない**（[idea_10](../../../backlog/idea_10_nested_modal_grab_restore.md) の課題。挙動を揃える）。

### 3. `keyseq/presentation/dialogs/__init__.py`（**1 行追加**）

`ReferenceCleanupDialog` を**明示列挙**で再輸出する（`import *` を使わない）。

### 4. `keyseq/presentation/controllers/config_io/reference_cleanup_io.py`（新規）

`ReferenceCleanupIo`（`app.reference_cleanup_io`）としてフローを持つ。**公開メソッドは 1 本**:

```python
def run_cleanup(self) -> None:
```

**処理の順序**（この順で・途中終了は必ず「何も書かない」で戻る）:

1. **未保存（`app.keymap_set_path` が空）なら保存を確認する**
   （`messagebox.askyesno`。文言は「掃除するには構成セットの保存が必要です。保存しますか？」相当）。
   - **いいえ / キャンセル → 何もせずに終了**（検査もしない）。
   - **はい → 既存の保存経路を呼ぶ**（`app.keymap_set_io` の保存。空パスなので**別名保存**になる）。
     **保存が成功しなかったら終了**（掃除しない）。**保存経路そのものを変更しない**。
2. **検査**: `config_service.inspect_parent_refs(app.data, config_root=..., keymap_set_path=...)`。
3. **0 件なら `CLEANUP_EMPTY_MESSAGE` を通知して終了**（一覧ダイアログを出さない）。
4. **確認ダイアログ**を出す（`format_cleanup_plan` の行を渡す）。
   **`result` が `False` なら何も書かずに終了**。
5. **除去**: `config_service.prune_parent_refs(...)`。
6. **結果を通知**（`format_cleanup_result` の行を結合して `messagebox.showinfo`）。
- **runtime・dirty を変更しない**（暫定仕様 §2。`app.data` を書き換えない）。
- **例外の扱い**: 個々のファイルの失敗は task_02 が結果へ集約するので、
  **ここで握りつぶさない**。フロー全体が例外になる経路を新設しない。

### 5. `keyseq/presentation/app.py`（**配線 1 行**）

他の `config_io` コントローラと同じ位置に `self.reference_cleanup_io = ReferenceCleanupIo(self)` を足す。

### 6. `keyseq/presentation/views/menu_bar.py`（**1 行**）

**「設定」メニュー**へ項目を追加し、`app.reference_cleanup_io.run_cleanup` を呼ぶ
（保守機能のため。ショートカットは付けない＝`bind_menu_shortcuts` は触らない）。

### 7. テスト `tests_ui/test_reference_cleanup_flow.py`（新規）

**この repo のテストの罠を必ず守ること**:

- **`setUp` に fail-fast ガードを置く**（想定外の `messagebox.showerror` /
  `filedialog` 呼び出しで即失敗させる。既存 4 ファイルの `setUp` が先例）。
  **モーダルへ実際に到達するとテストが永久ブロックする**ため。
- **`patch.object` を優先する**（モジュール名前空間の文字列 patch は分割で壊れる。計画07 の教訓）。
  `ReferenceCleanupDialog` は **`patch.object` でクラスごと差し替える**か、
  `result` を返すスタブにする（**実 Toplevel を開かない**）。
- アサーションは広い `except` の内側に置かない（**失敗がハングに化ける**）。

**最低限、次を固定する**:

- **0 件のとき**: 一覧ダイアログを**開かない**・`prune` を**呼ばない**・0 件メッセージを通知する
- **キャンセル**（`result = False`）: `prune` を**呼ばない**・**ファイルが 1 つも変わらない**
- **実行**（`result = True`）: `prune` が**検査結果を引数に**呼ばれ、**結果が通知される**
- **未保存 + 「いいえ」**: **検査も保存もしない**（`askyesno` が呼ばれること / 以降が呼ばれないこと）
- **未保存 + 「はい」→ 保存成功**: 保存経路が呼ばれ、**そのまま検査へ進む**
- **未保存 + 「はい」→ 保存失敗**: **掃除しない**（`prune` を呼ばない）
- **runtime（`app.data`）と dirty が変化しない**（**共有 App の汚染に注意**。
  絶対値で assert せず前後の変化で見る）
- メニュー項目から `run_cleanup` が呼ばれること（配線の確認。**`command` を直接叩く形**）

### 設計メモ / 制約

- **`ReferenceCleanupIo` は検査・除去のロジックを持たない**（application の委譲を呼ぶだけ）。
  **文言の組み立ても持たない**（`reference_cleanup_text` の純関数を使う）。
- **hook の suspend / resume は必ず対で行う**（ダイアログ側の責務。`dialogs/` の流儀）。
- **未保存の判定は `keymap_set_path` が空かどうか**（dirty かどうかではない）。
  理由: 巻き戻りの原因は **`parent_ref` が空になること**であり、これは**パスが空のときだけ**起きる。
- **保存経路を変更しない**（子の保存計画ダイアログ等は従来どおり出てよい）。

## 含まない

- 検査・除去・文言のロジック変更（task_01〜03 の成果を**そのまま使う**）
- **実機目視** → **task_05**
- **正本反映**（`data_schema.md` §5.8.1 / `features.md` / `codebase_map.md`）→ **task_06**
- 孤児の検出・削除 / 全走査（→ [idea_12](../../../backlog/idea_12_orphan_child_file_sweep.md)）
- ネストしたモーダルの grab 復元（→ idea_10）

## 確認

- 新規テスト `tests_ui/test_reference_cleanup_flow.py` が上記の全項目を含み pass する
- **既存テストが件数・内容とも不変**で pass する（`tests` **264** / `tests_ui` **229** + 追加分）
- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` / `-m unittest discover -s tests_ui`（**ハングしないこと**）/
  `-m tests.smoke_app` がいずれも pass（実測は `verifier`）
- 実行後に worktree ルートへ `user/` が生成されていないこと

## 完了条件

- 上記確認が pass・**`reviewer` 採用**。
- 差分が上記 **7 ファイル**（うち既存の変更は
  `config_service/__init__.py` / `dialogs/__init__.py` / `app.py` / `menu_bar.py` の **4 ファイル・各 1〜2 行**）に
  収まっていること。
- 実機目視は**本タスクでは行わない**（task_05 でまとめて実施）。
