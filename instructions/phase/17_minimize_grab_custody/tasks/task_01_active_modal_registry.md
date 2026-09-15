# task_01_active_modal_registry

## 目的

暫定仕様 15 §3-5 案 (i) に基づき、`keyseq/presentation/modal.py` へ**アクティブなモーダルの台帳**を
追加する。task_02 の預かり機構が「記録した保持者が最小化中に破棄されていたら**生存かつ表示中の
最内モーダル**へ張り直す」（§3-2(6)）ために、モーダルの開いた順序を知る手段が必要
（`winfo_children()` からは `grab_modal` を通った窓を判別できないため案 (ii) は不採用・§3-5）。

**本タスクでは台帳を作るだけで挙動は一切変えない**（台帳は誰も読まない）。
**presentation 限定・domain / application / infrastructure 不変・スキーマ不変。**

## 対象範囲（presentation 限定・`modal.py` と `tests_ui/test_modal_grab.py` のみ）

### keyseq/presentation/modal.py

- モジュールレベルに台帳を追加する: `_active_modals: list[tk.Toplevel] = []`。
  **並び = 開いた順**（`append`）で、**末尾 = 最内**。
- `grab_modal` の中で、**`window.grab_set()` が成功した後**に `window` を台帳へ追加する。
  - **二重呼び出しの早期 return 経路（`previous is window`）では追加しない**（重複登録の防止）。
- `restore_grab`（`<Destroy>` ハンドラ）の中で台帳から `window` を取り除く。
  - 位置は **`event.widget is not window` / `restored` のガードを通過し `restored = True` を
    立てた直後**（`previous is None` の早期 return より**前**）。どの復元分岐を通っても
    必ず除去されるようにする。
  - 除去は**同一性（`is`）で該当要素だけ**を落とす。**台帳に無ければ何もしない**
    （例外を出さない）。非 LIFO 破棄（中間の窓が先に破棄される）でも順序を崩さないこと。
- **台帳を読む処理・公開アクセサ・`__all__` 等の公開面の変更は加えない**（task_02 で追加する）。
- 既存の grab 取得 / `transient` / `<Destroy>` 復元の規則（phase 14・phase 16 の資産）は
  **一切変更しない**。`grab_modal` のシグネチャも変えない。

### 設計メモ / 制約

- **モジュール状態が増えることは phase 14 の「記録はクロージャに持つ」方針と緊張するが、
  順序を知る手段が他に無いためユーザー確定済**（暫定仕様 15 §2 / §3-5）。
  台帳は **`grab_modal` を通った窓だけ**を持ち、stdlib ダイアログ（`messagebox` / `filedialog`）は
  載らない（対象外と確定済・§2）。
- 除去に `list.remove()` を使うと `__eq__` を持つオブジェクトで誤除去し得る。
  **同一性判定で探して落とす**こと。
- `<Destroy>` は子ウィジェットからも伝播する。**既存の `event.widget is not window` ガードを
  流用**し、子ウィジェットの破棄で台帳を触らないこと。
- リーク・ゴースト（破棄済みの窓が台帳に残る）を作らないこと（phase.md「レビュー方針」）。

### tests_ui/test_modal_grab.py（台帳の一貫性テストを追加）

既存モジュールへ追加する（1 テスト 1 Tk の既存ハーネスをそのまま使う）。
**既存テスト・既存アサーションは弱めない**。

- **テスト間の独立**: 台帳はモジュール状態なので、台帳に触るテストは
  `patch.object(modal, "_active_modals", [])` 等で**空リストへ差し替える**か、
  snapshot → cleanup で復元すること（Mock を使う既存テストの残骸に影響されないため）。
- 固定する項目:
  1. `grab_modal` を通った窓が**開いた順**に載り、**末尾が最内**であること
  2. 窓の破棄で台帳から除去されること（LIFO）
  3. **非 LIFO 破棄**（中間の窓を先に `destroy()`）でも該当要素だけ除去され、残りの順序が保たれること
  4. **同じ窓へ `grab_modal` を 2 回**呼んでも重複登録されないこと
  5. **子ウィジェットの `<Destroy>`** では台帳から除去されないこと
     （既存 `test_child_widget_destroy_does_not_restore_grab` と同じ作り方）
  6. `grab_modal` を通らない `Toplevel` は台帳に載らないこと
  7. **記録した保持者が破棄済み / 非表示で復元しない分岐でも**台帳からは除去されること
     （`restored = True` 直後に除去する設計の担保）

## 含まない

- 預かり機構 `install_minimize_grab_custody(app)` の実装・`<Unmap>` / `<Map>` の結線・
  `app.py` からの呼び出し・**預かり中の `grab_modal` が `previous` を預かり窓にする**結線（**task_02**）
- **台帳を読む処理**（生存かつ表示中の最内モーダルの探索）（**task_02**）
- 暫定仕様 §6 の受け入れ条件テスト・変異検査（**task_03**）
- 統合確認（`tests` / `tests_ui` 全体 + `smoke_app`）・二次レビュー・実機目視（**task_04**）
- 正本反映（`features.md` §4.6 / `codebase_map.md`）・暫定仕様 15 の凍結（**task_05**）
- stdlib ダイアログ対応 / 窓構成の変更 / phase 14・15・16 の設計変更（フェーズ全体のスコープ外）

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier`**（Codex は python を実行できない）。

1. `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
2. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass
   （既存 324 + 追加分。特に `test_modal_grab.py` / `test_nested_modal_grab.py` の
   **静的検査（`grab_modal` は初期化の最後の文）**が落ちないこと）
3. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass
4. 追加テスト 7 項目（上記）が pass し、**台帳の追加・除去が各分岐で一貫している**こと

## 完了条件

- 上記確認がすべて pass・**`reviewer` 採用**。
- **実機目視は本タスクでは行わない**（task_04 でまとめて実施）。
- 台帳を読む実装が混入していないこと（= この時点で挙動が変わらないこと）。
