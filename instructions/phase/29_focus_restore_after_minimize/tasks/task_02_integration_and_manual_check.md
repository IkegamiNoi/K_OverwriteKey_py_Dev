# task_02_integration_and_manual_check

## 目的

phase 29 の実装（task_01）を**統合確認**し、暫定仕様 23 §6 の受け入れ条件 **1〜6 を確定**させる（7 = 正本反映は task_03）。

- **検証タスク。`keyseq/` ・ `tests_ui/` ・ `tests/` を変更しない**
  （回帰・指摘が出た場合は修正せず、切り分け結果を報告して枝番タスク `task_02b_*` を起票する）。
- 実測は **`verifier`**（**Codex に python 実行を依頼しない**）。判定はメインセッションが行う。
- 実機目視（§6-6 ①〜⑦）は**ユーザーが担当**し、結果をメインセッションへ報告してもらう。

## 対象範囲（検証のみ・コード変更なし）

### 1. 統合確認（`verifier` へ委任・§6-1〜5）

`.venv` の python（`..\..\..\.venv\Scripts\python.exe`）で次を実行し、結果の要約のみ受け取る。

1. `python -m compileall -q keyseq` が clean。
2. `python -m unittest discover -s tests` 全 pass（556・skipped 7 から不変）。
3. `python -m unittest discover -s tests_ui` を**連続 3 回**実行し **3 回とも全 pass**（519）。
   **ran / failures / errors / skipped の 4 数値を毎回記録する**。
4. **変異検査**（phase.md「task_02 = 変異検査を含む」。**一時編集のみ・`git checkout` / `git stash` は使わない**。
   各変異の後に元へ戻し、最後に `git diff --stat keyseq/` が空であることを確認する）。
   対象 = `python -m unittest tests_ui.test_minimize_grab_custody -v`:
   a. `return_custody` の `after_idle` 予約を**即時呼び出し**（`_restore_modal_focus(app)` を直接呼ぶ）へ戻す → **a2・a3・b10 が赤**（§3.1-4）。
   b. `after_idle` 予約そのものを外す → **b1・b2・b4・b5・b9・b10・b11 が赤**（§3.1-1）。
5. `python -m tests.smoke_app` が `SMOKE OK`。
6. `git diff --stat keyseq/ tests/ tests_ui/` が**空**であること（本タスクで触っていない確認）。

### 2. 二次レビュー（phase.md「レビュー方針」task_02）

**`deep-reviewer` と `codex-reviewer` を併用**する（phase 29 の累積差分 = `--base f620257`〔phase 28 完了時点〕〜HEAD）。

- `deep-reviewer` の重点観点: §3.1-2 の戻し先の定義が全経路で一意か / `after_idle` 予約中に窓が閉じた・再最小化された場合に
  安全か（§3.1-4・-5）/ `_opened_while_minimized` の寿命（§3.1-6）が破棄・例外時も正しいか /
  `focus_force` / `lift` / `deiconify` を呼んでいないか（a4）/ テストの期待値が実装をなぞるだけになっていないか（§5）/
  b11 のテスト側 `update()` 追加が検証内容を弱めていないか。
- `codex-reviewer` は標準レビュー。**指摘は提示のみ**で、採否はユーザー確認を経る。
- **【裏取り】両レビューの「コードがこうなっている」という事実主張は、採用前に `ファイルパス:行` を実測確認する**。

### 3. 実機目視の依頼（ユーザー担当・§6-6）

メインセッションは**下記の手順書をユーザーへ提示して結果を待つ**（Claude は実行しない）。
起動は `.venv\Scripts\python.exe main.py`（**作業中の worktree で実行**。メインのチェックアウトは未マージのため不可。`-m keyseq` は存在しない）。
**復元後はダイアログ内をクリックしない**（クリックするとフォーカスが入り、欠落を検出できない）。

| # | 手順 | 期待 |
|---|---|---|
| ① | アクション編集を開いたまま **Win+D → タスクバーから復元** → Escape | クリックせずに**閉じる** |
| ② | **3 段ネスト**（アクション編集 → プリセットマネージャ → 追加・編集）で Win+D → 復元 | **3 窓とも表示されたまま**・Escape で最内から 1 つずつ閉じる |
| ③ | ①の状態で **Win+D をもう 1 回**押して復元 | ①と同じ |
| ④ | ①の状態で **Alt+Tab で最小化中の keyseq を選んで**復元 | ①と同じ |
| ⑤ | keyseq でダイアログを開いたまま**メモ帳等で入力中**に Win+D を 2 回 | **メモ帳が前面に戻り、keyseq がアクティブにならない**（メモ帳のカーソル非表示は Windows の挙動で判定対象外・v0.5） |
| ⑥ | 最小化せず Alt+Tab で離れて戻る → Escape | 効くか効かないかを**記録のみ**（本フェーズでは直さない・§7） |
| ⑦ | アクション編集で**ラベル欄をクリックして入力中**に Win+D → 復元 → 文字を打つ | **ラベル欄へ入る**（値欄へ戻っていない） |

- ①〜⑤・⑦は受け入れ条件。⑥は記録のみ（効かない場合は `/idea` 起票の要否をユーザーへ確認する）。

### 設計メモ / 制約

- 本タスクで**コードを直さない**。回帰・レビュー指摘は「切り分け結果 + 推奨対応」をユーザーへ提示し判断を仰ぐ（修正は枝番タスク）。
- 自動テストは OS フォーカスを持たずアクティブ化の経路を通らないことが多い（§5 注記）。
  **中間窓が消えないこと・文字が実際に届くことの根拠は実機目視（②・⑦）**。Claude が「たぶん動く」と補完しない。
- `tests_ui` 一括でまれに出る `get_hook_pause_count()` の `1 != 0` は idea_33 の family。出た場合は単体再実行で切り分けて記録する。

## 読むファイル

- `instructions/history/23_focus_restore_after_minimize.md` の **§3.1 / §5 / §6 / §7**
- `instructions/phase/29_focus_restore_after_minimize/phase.md`（レビュー方針・タスク境界）
- `instructions/phase/29_focus_restore_after_minimize/tasks/task_01_restore_focus_on_map.md`「完了記録」（前回の実測値・変異検査の結果）
- `keyseq/presentation/modal.py`（変異検査の対象箇所 = `return_custody` の `finally`）
- task_01 のコミット差分（`git show 0b3e6c5 -- keyseq/ tests_ui/`）

## 含まない

- **コードの修正**（`keyseq/` ・ `tests/` ・ `tests_ui/`）。必要になったら `task_02b_*` を起票。
- **正本反映**（`features.md` §4.6 / `codebase_map.md` の `modal.py` 節）= **task_03**。
- **暫定仕様 23 の凍結 / `decisions_archive/29` 作成 / `current.md` 更新 / idea_34 の `INDEX_done.md` 移動 /
  `/refactor_check`** = **task_03**。
- 最小化を伴わない再アクティブ化でのフォーカス復帰（§7。⑥は記録のみ）/ 閉じた後のフォーカスの規定 /
  idea_33・同型スケルトンの共通化。

## 確認

`.venv` の python を使う（`..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

1. `python -m compileall -q keyseq` clean。
2. `python -m unittest discover -s tests` 556 ran OK（skipped 7）。
3. `python -m unittest discover -s tests_ui` **連続 3 回すべて全 pass**（519・数値を 3 回分記録）。
4. 変異検査 a・b が期待どおり赤、戻した後に `test_minimize_grab_custody` 23 件 green・`git diff --stat keyseq/` 空。
5. `python -m tests.smoke_app` が `SMOKE OK`。
6. `git diff --stat keyseq/ tests/ tests_ui/` が空。
7. `deep-reviewer` ・ `codex-reviewer` の指摘を裏取りし、**採用 / 修正して採用 / 保留 / 除外** で整理。
8. ユーザーの実機目視結果（①〜⑦）を受領。

## 完了条件

- 確認 1〜6 が pass。**3 で 1 回でも落ちたら完了にしない**（切り分けて再判定）。
- **二次レビュー（`deep-reviewer` + `codex-reviewer`）を実施し、判定を完了報告に記載**
  （CLAUDE.md「レビュー（必須）」の統合時の運用形。本タスクの別視点レビューを兼ねる）。
- **ユーザーの実機目視 ①〜⑤・⑦ が期待どおり**。1 件でも外れたら完了にしない（切り分けて差し戻し）。⑥は結果を記録する。
- **実機目視は本タスクで実施**（task_03 へ持ち越さない）。

## 中断記録（2026-09-23）

- 確認 1〜6 は 1 回目の実測で全 pass（`tests` 556 OK〔skipped 7〕/ `tests_ui` 519 OK ×3 / 変異 a・b とも期待どおり赤 / smoke OK / 差分 空）。
  二次レビュー = `deep-reviewer` 条件付き（M1・M2 は採否待ち）/ `codex-reviewer` 指摘なし。
- **実機目視①が不合格** → 暫定仕様 23 を v0.5 へ改訂（§3.1-3 条件つき `focus_force`・§1.2 測定 4）。修正は **task_01b**（v0.5 確定後に起票）。
- **task_01b 完了後に本タスクを再開**し、確認 1〜8 をやり直す（変異検査に v0.5 分を加える・実機目視 ①〜⑦ を最初から。②は 3 段目まで開いた状態で行う）。

## 完了記録（2026-09-23・task_01b 後の再開分）

- **状態 = 完了**。確認 1〜6（`verifier`・HEAD 652cb72）: compile clean / `tests` 556 OK（skipped 7）/ `tests_ui` **532 OK ×3** / smoke OK /
  変異検査 5 種（即時呼び出し → a2・a3・b10 / 予約削除 → b1・b2・b4・b5・b9・b10・b11・c10〜c12 / `focus_force` 分岐削除 → c10 /
  前面条件除去 → c12 / `focus_get` 条件除去 → c11）すべて狙いどおり赤（スクラッチ上で実施・worktree 未変更）。
- 二次レビュー（`f620257..652cb72`）:
  - `codex-reviewer` = 指摘なし。
  - `deep-reviewer` = 条件付き（コード修正不要）。M1（昇格時の文言整理: §2-1・§4-1 の「`focus_force` を呼ばない」への v0.5 注記 /
    §1.2 の「入力を奪わないのは Tk / OS 側で保たれる」の範囲限定 / 正本はユーザー視点の条件で書き API 名は codebase_map へ /
    §7 の残存リスクを保証範囲外へ）→ **修正して採用（task_03）**。うち §3.2 の `windll` / `WinDLL` の食い違い 1 行は本タスクで訂正済。
    M2（3 段ネストで `focus_force` 発動の確認）→ **採用**（実機目視②で確認済）。L1（発動の安定性）→ ①③④を 2〜3 回ずつで確認済。
    L2〜L5 → 保留（参考）。
- **実機目視（ユーザー・2026-09-23）: ①〜⑦すべて想定どおり**（①③④は各 2〜3 回・②は 3 段目〔追加・編集〕まで開いて確認・
  ⑤は keyseq がアクティブにならない・⑥は記録のみ〔想定どおりとの報告〕）。暫定仕様 23 §6-1〜6 達成（§6-7 = task_03）。
