# task_03_acceptance_tests

## 目的

暫定仕様 15 §6 の受け入れ条件のうち**自動化可能なもの**を `tests_ui` へ固定し、**変異検査**で
偽 pass を排除する。task_01 / task_02 の実装が「結線されたつもり」で空振りしていないことを、
**実 App（`app.py` の結線）を通した経路**で担保するのが狙い。

**テスト専用タスク。`keyseq/` 配下は本タスクで不変**（変異検査の一時変更は確認後に必ず戻す）。
スキーマ不変。

## 対象範囲（tests_ui 限定・新規 1 モジュール）

### 1. 新規 `tests_ui/test_minimize_grab_custody.py`

**実 `App()` を使う**（`app.py` の `install_minimize_grab_custody(self)` の結線ごと固定するため。
既存の `tests_ui/test_modal_grab.py` は自前の `tk.Tk()` に手で `install` する形なので、
**`app.py` の結線が消えても落ちない**＝この経路のテストが別途必要）。

| # | 受け入れ条件 | 内容 |
|---|---|---|
| A1 | §6-1 の自動化可能部分 | **実 `App` + 実ダイアログ**（`ActionDialog` 等 `grab_modal` 経由の窓）で `iconify()` → grab が外れ、`deiconify()` → **同じ窓へ戻る**。**`app.py` の結線が無ければ落ちる**こと |
| A2 | §6-4 | **3 段ネスト**で最小化 → 復元後、**phase 14 の LIFO 復元が従来どおり働く**（内側を閉じたら 1 つ外側へ戻る） |
| A3 | §6-8 / §3-5 | **最小化中に grab 保持者を `destroy()`** → 復元後、**生存かつ表示中の最内モーダル**へ張り直される（台帳フォールバック） |
| A4 | §6-6 | **`<Map>` ハンドラが `deiconify()` / `lift()` / `focus_force()` を呼ばない**（3 つとも `patch.object` で**呼び出し 0 回**を固定） |
| A5 | §6-11 | **`grab_current()` が `KeyError` を送出する状況**で `<Map>` が **`grab_set()` を呼ばない**（0 回） |
| A6 | §6-7① | **最小化中に別の窓が grab を取得**していたら、復元時に**上書きしない**（新しい保持者が保たれる） |
| A7 | §6-7② | **記録した窓が復元時も非表示**（`withdraw()` 済み）なら**その窓を掴まない**（見えない窓が入力を握らない） |
| A8 | §6-12 | **実運用の発火源**: `App` 内のフレームを `pack_forget()` して `<Unmap>` を発生させても**預かりが起きない**（FullView / CompactView 切替の経路） |
| A9 | §6-10 後半 | **預かり中に開いた新しいモーダルが、復元より前に閉じられた**場合も、**復元時に正しい窓（預かっていた窓）が grab を持つ** |

- **既存 `tests_ui/test_modal_grab.py` と重複させない**。既に固定済みの以下は**再実装しない**:
  `test_iconify_releases_hidden_grab_holder` / `test_deiconify_restores_same_grab_holder` /
  `test_unmap_preserves_visible_grab_holder`（§6-9）/ `test_child_unmap_does_not_take_custody` /
  `test_new_modal_restores_holder_taken_into_custody`（§6-10 前半）/
  `test_repeated_grab_modal_in_custody_restores_same_holder`。
- **既存テストのアサーションは 1 行も触らない**（追加のみ）。

#### ハーネスの制約（必ず守る）

- `setUpClass` で `App()` を共有する既存モジュールの作法に合わせる
  （`tests_ui/test_nested_modal_grab.py:26-42` を流用可）。
- **`iconify()` したまま tearDown しない**。**各テストの cleanup で必ず `deiconify()` して戻す**
  （iconic 状態が後続モジュールへ漏れる・§4）。
- `iconify()` / `deiconify()` の後は **`update()` / `update_idletasks()` でイベントを流してから**
  判定する（`<Unmap>` / `<Map>` は WM 経由で届く）。
- **例外監視**: `report_callback_exception` を patch して `assert_not_called` を cleanup に入れる
  （ハンドラ内の未捕捉例外を検出する）。
- **モジュール状態の初期化**: `_active_modals` / `_custody_window` を `patch.object` で毎テスト初期化する。
- テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されないこと。

### 2. 変異検査（**すべて期待どおり fail することを確認する**）

`keyseq/presentation/modal.py` を 1 箇所ずつ壊し、**指定したテストが fail する**ことを確認する。
**確認後は必ず元へ戻し、`git diff keyseq/` が空**であることを再確認する。

| # | 壊す箇所 | fail するべきテスト |
|---|---|---|
| M1 | `<Unmap>` の預かり処理を無効化する（`grab_release()` + 記録を行わない） | **A1**（および既存 `test_iconify_releases_hidden_grab_holder`） |
| M2 | `<Unmap>` の**非表示ガード**（`holder.winfo_viewable()` の判定）を外す | 既存 `test_unmap_preserves_visible_grab_holder` |
| M3 | `<Map>` の**「現保持者が `None`」ガード**を外す | **A6** |
| M4 | `<Unmap>` / `<Map>` の **`event.widget is not app` ガード**を外す | **A8** |
| M5 | `<Map>` の**台帳フォールバック**（`_active_modals` の走査）を消す | **A3** |

**いずれかで落ちないテストがあれば、そのテストは空振りしている**（結果を報告し、
テスト側を作り直す。production は直さない）。

### 設計メモ / 制約

- **production コードを直さない**。テストが落ちた場合、原因が task_01 / task_02 の実装にあるなら
  **報告して判断を仰ぐ**（本タスクで `keyseq/` を書き換えて通さない）。
- **A5 の作り方**: `grab_current` を `KeyError` 送出へ patch し、`grab_set` の呼び出し回数を数える
  （既存 `test_grab_current_key_error_and_restore_tcl_error_are_tolerated` の Mock の作法を流用）。
- **A4 の作り方**: `App`（および対象ダイアログ）の `deiconify` / `lift` / `focus_force` を
  `patch.object` で包み、**`<Map>` 経路で 0 回**を固定する。**テスト自身が呼ぶ `deiconify()`**
  （cleanup の復帰）と混ざらないよう、計測範囲を限定すること。
- **`assertIs` を `wm_transient()` の戻り値に使わない**（`Tcl_Obj` のため必ず失敗する）。
- **既存アサーションを弱めない**（削除・緩和は禁止）。
- 1 ファイルが肥大化しないよう、共通の足場はモジュール内のヘルパへ寄せる
  （`.claude/rules/implementation.md` の目安: 関数 30 行 / 新規 300 行）。

## 含まない

- **統合確認（`tests` / `tests_ui` 全体 + `smoke_app`）・二次レビュー・実機目視** → **task_04**
  （§6-1・§6-2 の実機確認 5 項目はユーザーが行う）
- **正本反映（`features.md` §4.6 / `codebase_map.md`）・暫定仕様 15 の凍結** → **task_05**
- **`keyseq/` 配下の変更**（本タスクで production は不変。変異検査の一時変更は必ず戻す）
- stdlib ダイアログ（`messagebox` / `filedialog`）が grab 中の経路（対象外と確定）
- [idea_18](../../backlog/idea_18_escape_delivery_flaky_test.md)（既存テストの flaky）への対応

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier`**（Codex は python を実行できない）。

1. `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
2. 新規モジュールが単体で pass:
   `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_minimize_grab_custody`（A1〜A9）
3. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass
   （**既存 337 + 新規分**。既存の件数は減らない）
4. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass（417・skip 7）
5. **変異検査 M1〜M5 がそれぞれ期待どおり fail**（上表）。**確認後に復元し `git diff keyseq/` が空**
6. **production 無変更**: `git diff --stat` に `keyseq/` が**現れない**
7. **既存テストの非改変**: `git diff -- tests_ui/test_modal_grab.py` に**削除行が無い**
   （本タスクでは原則 `tests_ui/test_modal_grab.py` を変更しない）
8. テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されていないこと

## 完了条件

- 上記確認がすべて pass・**`reviewer` 採用**（観点に「**テストが空振りしていないか**」
  「**既存アサーションを弱めていないか**」「**production が不変か**」を含める）。
- **変異検査 M1〜M5 の結果を完了報告に記載する**（どのテストが落ちたか）。
- **実機目視は本タスクでは行わない**（task_04 でユーザーが実施）。
