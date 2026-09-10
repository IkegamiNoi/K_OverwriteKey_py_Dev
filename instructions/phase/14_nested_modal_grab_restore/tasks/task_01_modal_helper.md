# task_01_modal_helper

## 目的

モーダル化と grab 復元をまとめたヘルパ `keyseq/presentation/modal.py` を新設し、
**系統 B（呼び出し側が素の `tk.Toplevel` に `transient` + `grab_set` を書いている 4 箇所）**を
そこへ寄せる。暫定仕様 [12](../../../history/12_nested_modal_grab_restore.md) §3（復元規約 8 条）と
§4「案 X: 子側で復元する」が根拠。

**presentation 限定。domain / application / infrastructure は不変。スキーマ不変。**

挙動の変化は **`hotkey_presets_io.confirm_overwrite` の 1 箇所だけ**で、これは
**暫定仕様 §1 のネスト経路 3 そのもの**（プリセット編集 → 上書き確認）であり、
**本フェーズが直そうとしている欠陥の是正**にあたる。残る 3 箇所はメインウィンドウから開く
非ネスト経路なので、ヘルパを通しても表示・戻り値・フック制御は現状と同じになる。
（起票時に「系統 B は 4 箇所とも非ネスト」と書いていたのは誤りで、実装時に訂正した。
経路 3 の**実ダイアログでのテストは task_03**。）

## 対象範囲（presentation 限定）

### 1. `keyseq/presentation/modal.py`（新規）

公開関数を 1 つだけ置く。

```python
def grab_modal(window: tk.Toplevel, parent: tk.Misc | None = None) -> None:
    """window をモーダル化し、破棄されたら直前の grab 保持者へ戻す。"""
```

**手順**:

1. `window.grab_current()` で**直前の保持者を記録する**（§3-1）。
   `tk.TclError` と `KeyError` は捕捉して `None` として扱う
   （tkinter 管理外のウィンドウが grab を持つ瞬間に `_nametowidget` が `KeyError` を出し得る。§3-4）。
2. `parent` が渡されていれば `window.transient(parent)` を呼ぶ。
3. `window.grab_set()` を呼ぶ。**ここで失敗した場合は grab を取れていないので復元は不要**。
   例外はそのまま送出する（現行の呼び出し側と同じ挙動）。
4. `window.bind("<Destroy>", ...)` で復元ハンドラを登録する。

**復元ハンドラの規約**:

- **`event.widget is window` のときだけ動く**。`<Destroy>` は**子ウィジェットでも発火する**ため、
  ガードしないと初期化中の子ウィジェット破棄で誤発火する。
- **一度だけ実行する**（§3-5 の冪等性）。
- 記録した保持者が `None` なら**何もしない**（§3-1。もともとモードレスだった親を
  モーダル化しないための条件はこれで足りる）。
  **「記録した保持者が自分自身のときだけ戻す」という条件は付けないこと**
  — 系統 A の経路 3 では開く側と grab 保持者が別物になり、この条件を付けると復元されない。
- **破棄の時点で grab を持っているのが自分自身か、誰も持っていないときだけ戻す**（§3-7）。
  他の生存モーダルが持っているなら**戻さない**（非 LIFO 終了で最内側の grab を奪わないため）。
  判定にも手順 1 と同じ `grab_current()` の防御を使う。
- 戻す相手は **`winfo_exists()` かつ `winfo_viewable()` が真のときだけ**（§3-2）。
  `winfo_exists()` だけでは `withdraw` 済みの相手を素通りして
  `TclError: grab failed: window not viewable` になる。
- `grab_set()` が `tk.TclError` を出したら捕捉してよいが、
  **握りつぶす理由をコメントで残す**（§3-4 / `.claude/rules/python_rules.md`）。

**状態の持ち方**: 記録した保持者と実行済みフラグは**クロージャに持ち、ウィジェットの属性に持たない**。
`tests_ui/test_app_ui_flows.py:72`・`:1327-1338` が `object.__new__(PresetManagerDialog)` で
インスタンスを作って `destroy` を直接呼ぶため、属性に持つと task_02 でそこが壊れる。

**docstring に明記すること**: 「**初期化の最後に呼ぶ**。呼び出し後に初期化を続けると、
そこで例外が出たときに破棄フックが発火せず grab を握ったまま残る（§3-6）」。

### 2. 系統 B の 4 箇所をヘルパへ置換

いずれも `dialog.transient(self._app)` + `dialog.grab_set()` の 2 行を
`grab_modal(dialog, self._app)` の 1 行にする。**それ以外は変えない**
（`protocol` / `bind` / `wait_window` / `suspend_hook_for_dialog` / `resume_hook_after_dialog` の
位置と順序は現状のまま）。

| ファイル | 行 | メソッド |
|---|---|---|
| `keyseq/presentation/controllers/config_io/child_save_dialog.py` | 24-25 | `ask_child_save_actions` |
| `keyseq/presentation/controllers/config_io/child_save_dialog.py` | 241-242 | `confirm_trigger_set_dependency` |
| `keyseq/presentation/controllers/config_io/hotkey_presets_io.py` | 79-80 | `confirm_overwrite` |
| `keyseq/presentation/controllers/config_io/io_dialogs.py` | 54-55 | `ask_link_label_to_filename` |

### 3. `tk.Toplevel` を差し替えているテストダブル **2 つ**を最小限だけ拡張

ヘルパが `grab_current()` と `bind()` を呼ぶため、`tk.Toplevel` を patch しているスタブに
不足メソッドを足す。**`grab_current()` は `None` を返す**
（`None` なら復元しないので `winfo_exists` / `winfo_viewable` は呼ばれない）。
**それ以外のスタブ拡張はしない**。

| ファイル | クラス | 不足していたもの |
|---|---|---|
| `tests_ui/test_child_save_dialog.py:149` | `_FakeSaveDialog` | `grab_current` |
| `tests_ui/test_config_io_characterization.py:66` | `_FakeDialog` | `grab_current` / `bind` |

**起票時は `_FakeSaveDialog` しか挙げていなかった**（監査漏れ）。`_FakeDialog` は
`io_dialogs.ask_link_label_to_filename` の特性テスト 4 件を落としたため実測で判明し、
task_01 の範囲として追加した。`grep -rn "def grab_set" tests_ui/` でスタブは**この 2 つで全部**。

### 4. `tests_ui/test_modal_grab.py`（新規）— ヘルパ単体のテスト

実 `tk.Tk` と `tk.Toplevel` を使って以下を固定する。

1. **基本の記録と復元**: A を `grab_modal` でモーダル化 → B を `grab_modal` でモーダル化 →
   B を破棄 → `grab_current()` が A を指す。
2. **記録が `None` なら復元しない**: 誰も grab を持たない状態で B をモーダル化 → 破棄 →
   `grab_current()` が `None`（親がモーダル化されない）。
3. **`withdraw` 済みの親**: A をモーダル化 → `A.withdraw()` → B をモーダル化 → B を破棄 →
   `TclError` を送出しない。
4. **破棄済みの親**: A をモーダル化 → B をモーダル化 → A を破棄 → B を破棄 →
   `TclError` を送出しない。
5. **非 LIFO 終了**（§3-7）: A → B → C を順にモーダル化 → **B だけを破棄** →
   grab は **C のまま**（A へ戻らない）。
6. **子ウィジェットの `<Destroy>` で誤発火しない**: B をモーダル化した後、
   B の中の子ウィジェットだけを破棄 → grab は B のまま。
7. **冪等**: 同じウィンドウへ `grab_modal` を 2 回呼んでも復元が 1 回だけ起き、壊れない。

**テストの後始末**: 各テストで生成した `Toplevel` を `addCleanup` で破棄し、
`grab_release()` して次のテストへ grab を持ち越さない。

## 設計メモ / 制約

- **`transient` と `grab_set` の順序**は系統 B の現状（`transient` → `grab_set`）に合わせる。
  系統 A には逆順のものがあるが、**本タスクでは系統 A に触らない**。
  順序統一そのものを目的とした並べ替えは暫定仕様 §8 でスコープ外。
- **`wait_window()` は呼び出し側に残す**。ヘルパは待たない（案 X は「開く側に触らない」のが要点）。
- 置き場所は `keyseq/presentation/modal.py`。`dialogs/` と `controllers/config_io/` の両方から
  使うため、`.claude/rules/file_organization_rules.md` の Feature Shared（レイヤフォルダ直下）に当たる。
  `config_paths.py` / `listbox_utils.py` と同じ枠。**`utils` / `helper` のような雑多名にしない**。
- **`ConfigIo` 系のクラスへメソッドとして生やさない**（`dialogs/` から使えなくなる）。
- 新規の外部依存を追加しない（標準の `tkinter` のみ）。

## 含まない

- **系統 A（`dialogs/` の 9 クラス）への適用** → task_02。本タスクでは `dialogs/` を一切変更しない。
- **ネスト経路 3 系統の実ダイアログでのテスト** → task_03。
- **§3-6（初期化失敗の回収）と §3-8（コールバック例外）の実ダイアログでのテスト** → task_04。
  本タスクの範囲は**ヘルパ単体での挙動固定**まで（上記 4 の 7 項目）。
- **`_FakeSaveDialog` の `winfo_exists` / `winfo_viewable` 追加** → 必要になったら task_03 で判断する。
- 統合確認（テストスイート全体 + smoke）→ task_05。実機目視も task_05。
- 正本反映・`codebase_map.md` 更新・idea 起票 → task_06。
- stdlib ダイアログ（`messagebox` / `filedialog`）への対応（暫定仕様 §6-3 で対象外）。
- `hotkey_presets_io.confirm_overwrite` がフックを停止・再開していない点
  （他の 3 箇所と非対称だが**本タスクの対象外**。気づいた場合は報告のみ）。

## 確認

python は必ずリポジトリルートの `.venv` を使う（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**テストの実行は `verifier` が行う**（`codex-implementer` には依頼しない）。

1. `python -m compileall -q keyseq main.py tests tests_ui` が clean。
2. `python -m unittest tests_ui.test_modal_grab` が pass し、**上記 4 の 7 項目すべてを含む**。
3. `python -m unittest tests_ui.test_child_save_dialog` と
   `python -m unittest tests_ui.test_config_io_characterization` が pass
   （スタブ拡張の対象 2 ファイル。件数が減っていないこと）。
4. `python -m unittest discover -s tests` が pass（**417 件・skip 7 から減っていないこと**）。
5. `python -m unittest discover -s tests_ui` が pass（**288 件から減っていないこと**）。
6. `grep -rn "grab_set" keyseq/presentation/controllers/` の結果が
   **`modal.py` 経由のみ**になっている（系統 B に直呼びが残っていない）。
7. `grep -rn "grab_set" keyseq/presentation/dialogs/` が **9 箇所のまま**（task_02 の範囲を先取りしていない）。
8. テスト実行後、worktree ルートに `user/` も `quarantine/` も生成されていない。

## 完了条件

- 上記「確認」1〜8 がすべて pass。
- **`reviewer` 採用**（CLAUDE.md「レビュー（必須）」）。観点は `.claude/rules/review.md` の 5 観点に加え、
  phase.md「レビュー方針」の**復元条件の取り違え**（§3-1 と §3-7 の混同）と**適用漏れ・スコープ逸脱**。
- 実機目視は**本タスクでは実施しない**（task_05 でまとめて実施）。
