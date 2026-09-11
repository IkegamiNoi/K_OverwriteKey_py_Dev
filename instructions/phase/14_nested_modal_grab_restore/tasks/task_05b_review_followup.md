# task_05b_review_followup

## 目的

task_05 の二次レビュー（`deep-reviewer`）の指摘のうち、**ユーザーが採用と判断した分**を反映する。
暫定仕様 [12](../../../history/12_nested_modal_grab_restore.md) を task_06 で凍結する前に、
**無言失敗経路の封じ込め**と**契約条項のテスト漏れ**を解消する。

**presentation 限定。domain / application / infrastructure は不変。スキーマ不変。**
**挙動の変化は M-5（`<Destroy>` の bind を追加形式へ）の 1 点のみ**で、これは
**復元が無言で消える経路を塞ぐ是正**にあたる。

### 採否の記録（ユーザー確定 2026-09-11）

| 記号 | 指摘 | 判定 |
|---|---|---|
| H-1 | `modal.py` の docstring が撤回済みの回収機構を指示 | **採用**（本タスク） |
| H-2 | 暫定仕様 §4 に「回収が必須」が残存 | **採用**（**メインが対応済**） |
| L-1 / L-2 | §3 の「5 点」表記・§7 の版表記 | **採用**（**メインが対応済**） |
| M-4 | 連鎖破棄時の復元挙動が未規定 | **採用**（§3-5 へ追記・**メインが対応済**） |
| M-5 | `<Destroy>` の bind が `"+"` なし | **採用**（本タスク） |
| M-1 / M-2 / M-3 | テストの穴 3 件 | **採用**（本タスク） |
| M-6 | 静的検査を発見ベースへ | **保留** → task_06 の `/refactor_check` で判定 |
| L-3 〜 L-9 | 参考指摘 | **除外**（記録のみ。実害なし / 既知 / task_06 の予定どおり） |

## 対象範囲

### 1. `keyseq/presentation/modal.py`（2 点のみ）

**(a) M-5: `<Destroy>` の bind を追加形式にする**

```python
window.bind("<Destroy>", restore_grab, "+")   # 現状は第 3 引数なし（:46）
```

**理由**: 現状は既存ハンドラを**上書き**するため、同じウィンドウへ別の `<Destroy>` を
足すと復元が無言で消える。[idea_16](../../../backlog/idea_16_wm_close_skips_destroy_override.md)
（× 閉じでフック再開が走らない）の有力な対策が「後始末を `<Destroy>` へ寄せる」案であり、
**正面衝突する**。多重復元は既存の防御で起きない
（`previous is window` の早期 return / `restored` フラグ / `current is not window` 判定）。

**(b) H-1: docstring の修正**

現状の後半（「呼び出し側で子を破棄してから例外を再送出する必要がある」）は
**v0.5 で撤回された回収機構を指示している**。次の趣旨へ書き換える:
「**初期化の最後に呼ぶ**。grab 取得後に初期化を残さないこと。例外が本関数より前で出れば
子はまだ grab を取っておらず、親が grab を保持したまま残る（§3-6）。」

**これ以外のロジック変更は行わない。**

### 2. `tests_ui/test_nested_modal_grab.py`（テスト 3 本を追記）

1. **M-1: 3 段ネストの LIFO 復元**（受け入れ条件 2 後半）
   `ActionDialog` → `PresetManagerDialog` → 上書き確認の 3 段を作り、
   **中間を破棄せず内側から順に閉じる**。確認点:
   - 確認ダイアログを閉じたら `grab_current()` が **`PresetManagerDialog`**。
   - マネージャを閉じたら `grab_current()` が **`ActionDialog`**。
   既存の `test_non_lifo_manager_destroy_does_not_steal_confirmation_grab` が
   3 段を組む先例なので、その組み立てを流用する（**非 LIFO 版と対になる**）。

2. **M-2: 真の × 閉じ（Tcl レベル破棄）**
   `protocol("WM_DELETE_WINDOW")` を**登録していない**クラス（`PresetDialog` 等）で、
   `dialog.tk.call("destroy", str(dialog))` により**ウィンドウマネージャの × と同じ経路**で
   破棄する。確認点:
   - **grab が親へ復元される**（`<Destroy>` 結線なので働くはず、を実測で固定する）。
   - 既存の `test_window_close_...` は `protocol` ハンドラ経由（Python の `destroy()` を呼ぶ）
     **別経路**なので、**重複ではない**。

3. **M-3: §3-4 の防御分岐**（2 分岐とも現在**無テスト**）
   - `grab_current()` が `KeyError` を送出する場合
     （`patch.object(window, "grab_current", side_effect=KeyError)` 等）に
     **記録側が `None` 扱いにして落ちない**こと（`modal.py:16-18`）。
   - 復元時の `previous.grab_set()` が `TclError` を送出する場合に
     **握りつぶして落ちない**こと（`modal.py:42-44`）。
   **この 2 分岐は現状「削除しても 303 件が green」**なので、
   **追加後に変異検査で落ちることを確認する**（確認節 5）。

   このテストは `tests_ui/test_modal_grab.py`（ヘルパ単体）側に置いてもよい。
   **実ダイアログを要しないため、そちらの方が素直なら移してよい**（判断は実装者）。

### 設計メモ / 制約

- **`modal.py` の変更は上記 (a)(b) の 2 点だけ**。復元ロジック本体・条件判定・
  クロージャの持ち方は変えない。
- **既存 8 本のテストを壊さない / ガードを弱めない**（`report_callback_exception` の
  `assert_not_called` を含む）。
- **M-6（静的検査の発見ベース化）は対象外**。task_06 の `/refactor_check` で判定する。
- 仕様側（§3-5 の連鎖破棄・§4 の v0.4 記述・§3 の「8 条」・§7 の版表記）は
  **メインセッションが対応済み**。実装者は触らない。

## 含まない

- **M-6**（静的検査の発見ベース化）→ task_06 の `/refactor_check` で判定。
- **idea_16 の是正**（× 閉じでフック再開が走らない）→ フェーズ外。
- **正本反映・暫定仕様の凍結・`/refactor_check`** → **task_06**。
- **実機目視** → task_05（ユーザーが実施中）。
- L-3 〜 L-9 の参考指摘への対応（**除外**と判定済み）。

## 確認

python は必ずリポジトリルートの `.venv`（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier` へ委任する**。

1. **静的確認**: `python -m compileall -q keyseq main.py tests tests_ui` が clean。
2. **テストが pass**: `python -m unittest tests_ui.test_nested_modal_grab -v` と
   `python -m unittest tests_ui.test_modal_grab -v` が全 pass。
3. **既存テストが据え置き**:
   - `python -m unittest discover -s tests` = pass 417（skip 7）。
   - `python -m unittest discover -s tests_ui` = **pass 306**（303 + 新規 3）。
   - `python -m tests.smoke_app` が pass。
4. **`modal.py` の差分が 2 点だけ**であること（`git diff keyseq/presentation/modal.py` で確認）。
5. **変異検査（M-3 が効くことの確認）**: `modal.py` の `grab_current()` の
   `except (tk.TclError, KeyError)` を `except tk.TclError` へ一時的に狭めると
   **M-3 のテストが fail** すること。**確認後は必ず元へ戻し、`git diff keyseq/` が
   意図した差分だけであることを再確認する**（`verifier` へ依頼）。
6. テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されていないこと。

## 完了条件

- 上記「確認」1〜6 がすべて pass。
- **`reviewer` 採用**（CLAUDE.md「レビュー（必須）」）。観点は `.claude/rules/review.md` の 5 観点 +
  **採用した指摘が過不足なく反映されているか**（M-6 を先取りしていないか / `modal.py` の
  変更が 2 点に収まっているか / 追加テストが既存と重複していないか）。
- **実機目視は本タスクでは行わない**（task_05 の項目でカバー済み。
  ただし M-5 で `<Destroy>` の結線形式が変わるため、**task_05 の目視を M-5 適用後に実施する**）。
