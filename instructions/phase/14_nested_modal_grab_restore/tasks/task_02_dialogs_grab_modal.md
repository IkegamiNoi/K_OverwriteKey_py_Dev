# task_02_dialogs_grab_modal

## 目的

**系統 A（`keyseq/presentation/dialogs/` の 9 クラス）**の `__init__` にある
`self.grab_set()` + `self.transient(parent)` を、task_01 で新設した
`keyseq/presentation/modal.py` の `grab_modal(self, parent)` へ置換する。
根拠は暫定仕様 [12](../../../history/12_nested_modal_grab_restore.md) §3（復元規約 8 条）と
§4「案 X: 子側で復元する」、および phase.md「タスク」2。

**presentation 限定。domain / application / infrastructure は不変。スキーマ不変。**
UI の見た目・戻り値・フック制御（`suspend_hook_for_dialog` / `resume_hook_after_dialog`）は変えない。

これで暫定仕様 §1 のネスト経路 1（プリセット編集 → 追加/編集）と経路 2（アクション編集 →
プリセット編集）が復元されるようになる。**これは本フェーズが直そうとしている欠陥の是正**であり、
非ネスト経路（メインウィンドウから直接開く場合）は記録される保持者が `None` になるため挙動不変。

## 対象範囲（presentation 限定・`dialogs/` の 9 ファイルのみ）

各ファイルで共通に行うこと:

1. `from keyseq.presentation.modal import grab_modal` を import に追加する
   （既存 import の書式に合わせる。`dialogs/__init__.py` は触らない）。
2. `__init__` 内の `self.grab_set()` と `self.transient(parent)` の 2 行
   （順序は 2 種類混在している）を **`grab_modal(self, parent)` の 1 行**へ置換する。
3. **`grab_modal(self, parent)` を `__init__` の最後の文にする**（§3-6）。

対象と現状の該当行:

| ファイル | 現状 | 置換時の注意 |
|---|---|---|
| `action_dialog.py` | `:119` grab_set / `:120` transient / `:122` `_sync_capture_ui()` | **`_sync_capture_ui()` を先に呼び、`grab_modal` を最後にする**（下記 §順序） |
| `keymap_edit_dialog.py` | `:53` grab_set / `:54` transient | そのまま置換（末尾） |
| `layout_delete_dialog.py` | `:50` grab_set / `:51` transient | そのまま置換（末尾） |
| `orphan_sweep_dialog.py` | `:24` transient / `:25` grab_set | そのまま置換（末尾） |
| `preset_dialog.py` | `:38` grab_set / `:39` transient | そのまま置換（末尾） |
| `preset_manager.py` | `:71` grab_set / `:72` transient | そのまま置換（末尾） |
| `quarantine_manage_dialog.py` | `:24` transient / `:25` grab_set | そのまま置換（末尾） |
| `reference_cleanup_dialog.py` | `:55` transient / `:56` grab_set | そのまま置換（末尾） |
| `trigger_dialog.py` | `:52` grab_set / `:53` transient | そのまま置換（末尾） |

（行番号は起票時点。ズレていたら該当箇所を探して適用する。）

### 設計メモ / 制約

**順序（`action_dialog.py` のみ）**
現状は `grab_set` → `transient` → `_sync_capture_ui()` の順で、grab 取得後にまだ初期化が残る。
§3-6（初期化の失敗を回収する）に従い、**`_sync_capture_ui()` を先に実行してから
`grab_modal(self, parent)` を呼ぶ**（＝ grab_modal を最後の文にする）。
`_sync_capture_ui()` はウィジェットの表示・非表示を切り替えるだけで grab に依存しないため、
先に呼んでも表示結果は変わらない。**これは「順序統一を目的とした並べ替え」ではなく
§3-6 を満たすための必要な移動**である（phase.md「含まない」の並べ替え禁止に抵触しない）。

**§3-6 の try/except は書かない**
`grab_modal` を `__init__` の最後の文にすれば、grab 取得後に失敗し得る初期化コードが
残らないため、破棄 → 復元 → 再送出の回収コードは 9 クラスとも不要になる。
**「最後の文にする」ことで §3-6 を満たす**方針とし、余分な try/except を足さない。
`grab_modal` 自体が失敗した場合は grab を取れていないので復元も不要（task_01 の規約どおり）。

**`<Destroy>` の `"+"` なし bind（task_01 の `reviewer` 保留指摘）**
`grab_modal` は `window.bind("<Destroy>", ...)` を `"+"` なしで呼ぶため、同じウィンドウへ
別の `<Destroy>` ハンドラを足すと復元が無言で消える。
**9 クラスの現状に `<Destroy>` の bind は 1 件も無い**（`bind("<Escape>", ...)` のみ）ので
本タスクでは衝突しない。**実装中に該当が見つかった場合は、その場で対処せずユーザーへ報告する**。

**`destroy()` override との関係**
9 クラス中 8 クラスは `destroy()` を override してフック再開等を行っている
（`preset_dialog.py` のみ override なし）。`grab_modal` の復元は `<Destroy>` イベント経由なので
override とは独立に動く。**`destroy()` override 側に復元処理を書き足さない**。

**`object.__new__` 経路**
`tests_ui/test_app_ui_flows.py:72` と `:1327` は `object.__new__(PresetManagerDialog)` で
インスタンスを作り `PresetManagerDialog.destroy(dialog)` を直接呼ぶ。
`grab_modal` は復元状態をクロージャに持ちウィジェット属性を増やさないため、
**`__init__` を通っていないインスタンスでも新たな属性参照は発生しない**。
この経路で `AttributeError` を増やさないこと。

**やってはいけないこと**
- `transient` / `grab_set` の順序統一を目的とした、上表以外の並べ替え。
- ダイアログ同型スケルトン（Escape bind / `protocol` / `destroy` override）の共通化。
- `ActionDialog` の親付け替え。
- `modal.py` の実装変更（task_01 で確定済み。修正が要ると判断したらユーザーへ報告する）。

## 含まない

- **ネスト経路 3 系統のテスト追加**（プリセット編集 → 追加/編集 / アクション編集 →
  プリセット編集 / プリセット編集 → 上書き確認）→ **task_03**。
  `_FakeSaveDialog` の拡張要否判断も task_03。
- **契約 3 条のテスト**（初期化失敗 / 非 LIFO 終了 / コールバック例外）→ **task_04**。
- **統合確認と実機目視**（stdlib ダイアログ 4 経路）→ **task_05**。
- **正本反映・暫定仕様の凍結・`/refactor_check`** → **task_06**。
- ダイアログ同型スケルトンの共通化 / `ActionDialog` の親付け替え / stdlib ダイアログの grab
  （いずれも phase.md「含まない」）。

## 確認

python は必ずリポジトリルートの `.venv`（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier` へ委任する**（Codex は python を実行できない）。

1. **静的確認**: `python -m compileall -q keyseq main.py tests tests_ui` が clean。
2. **既存テスト全 pass**:
   - `python -m unittest discover -s tests` = pass 417（skip 7）で据え置き。
   - `python -m unittest discover -s tests_ui` = pass 295 で据え置き（本タスクは新規テストを足さない）。
   - `python -m tests.smoke_app` が pass。
3. **適用漏れの確認**: `grep -rn "grab_set" keyseq/presentation/ --include=*.py` の結果が
   **`modal.py` のみ**（ヘルパ内の 2 行 = `window.grab_set()` と復元側 `previous.grab_set()`）で、
   `dialogs/` 9 件・`controllers/` 0 件になること。
   `grep -rn "transient" keyseq/presentation/ --include=*.py` も `modal.py` の 1 行のみ。
4. **`__init__` の末尾確認**: 9 クラスとも `grab_modal(self, parent)` が `__init__` の
   最後の文であること（`action_dialog.py` は `_sync_capture_ui()` の後）。
5. テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されていないこと。

## 完了条件

- 上記「確認」1〜5 がすべて pass。
- **`reviewer` 採用**（CLAUDE.md「レビュー（必須）」）。観点は `.claude/rules/review.md` の 5 観点 +
  phase.md「レビュー方針」の固有観点（復元条件の取り違え / 自動発火の過信 / 適用漏れ / スコープ逸脱）。
- **実機目視は本タスクでは行わない**（task_05 でまとめて実施）。
