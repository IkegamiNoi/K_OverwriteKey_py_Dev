# task_04_integration

## 目的

phase 15 の task_01〜03 を**まとめて**検証し、フェーズ完了判定の材料を揃える。
暫定仕様 [13](../../../history/13_dialog_teardown_on_close.md)（v0.4）の **§7 受け入れ条件 9・10**
（退行なし / 実機目視）と phase.md「タスク」4 が根拠。

**検証と判定のみ。実装は行わない**（指摘が出た場合の修正は別タスクとして切り出すか、
ユーザー確認のうえ最小修正する）。

## 対象範囲（検証のみ・コード変更なし）

### 1. 統合確認（`verifier` へ委任）

phase 15 の全差分（`ecdb3eb..HEAD` = task_01 / task_02 / task_03）に対して実測する。

- `python -m compileall -q keyseq main.py tests tests_ui` が clean。
- `python -m unittest discover -s tests` = **pass 417 / skip 7**。
- `python -m unittest discover -s tests_ui` = **pass 320**。
- `python -m tests.smoke_app` が pass。
- **単独実行でも pass**（順序依存の確認）: `tests_ui.test_dialog_teardown_flows` /
  `tests_ui.test_hook_controller_teardown` / `tests_ui.test_nested_modal_grab`。
- テスト実行後に worktree ルートへ `user/` / `quarantine/` が生成されていないこと。

### 2. 二次レビュー（`deep-reviewer` + `codex-reviewer`）

**対象は `ecdb3eb..HEAD` の差分全体**（単一タスクではなくフェーズ横断のため `deep-reviewer`）。
観点は phase.md「レビュー方針」の固有観点:

- **二重実行** — `destroy()` override と破棄イベントの両方で解除が走っていないか。
- **`event.widget` 判定** — 子ウィジェットの破棄で解除が走らないか。
- **phase 14 との干渉** — `grab_modal` の `"+"` 結線を潰していないか。
  `grab_modal` が `__init__` の最後の文のままか。grab 復元が退行していないか。
- **終了ガードの網羅** — ダイアログ経路と try/finally 経路の両方で、終了時にフックが再開しないか。
- **`window` 省略時の非変更** — try/finally 形 5 系統の挙動が変わっていないか。
- **静的検査の対象限定** — `controllers/` を巻き込んでいないか（既存検査と衝突する）。
- **スコープ逸脱** — スケルトン共通化 / `key_capture`・`keyboard_window` / 親付け替え（idea_17）を
  取り込んでいないか。

**両者の指摘は提示のみ。修正・採否はユーザー確認を経て決める**
（`.claude/rules/agent_selection.md`）。**事実主張は `ファイルパス:行` で裏取りしてから採用する**。

### 3. 残課題の要否判定（`after` 予約の後片付け）

`tests_ui` 全体実行で stderr へ
`invalid command name "...resume_hook_after_dialog" (while executing "after" script)` が **6 回**出る。

- **task_03 由来ではない**（新規テストを外しても同数出る）。**task_01 / task_02 の `after(0)` 予約が
  App 破棄時に残る**ことによる Tk のバックグラウンドエラー。
- テスト結果は OK（fail 0）で、**production の終了経路は暫定仕様 §4-2 が意図した挙動**
  （終了時は保留中の `after` が実行されない）。
- **判定する内容**: ①production 側に手当てが要るか（例: 破棄時に `after_cancel`）
  ②テスト側の後片付けで消すべきか ③このまま受容して記録するか。
  **判定はユーザー。本タスクは材料（発生箇所・実害の有無）を揃えて提示する**。

### 4. 実機目視（ユーザーが実施）

`python main.py` で起動し、以下を確認してユーザーがメインセッションへ結果を報告する。

1. **フック ON の状態でダイアログを × で閉じる** → **次にダイアログを開いたときフックが止まる**
   （＝カウンタがずれていない。受け入れ条件 10）。
2. **OK / キャンセルで閉じた場合も同様**にフックが止まる（二重解除でカウンタが負にならない）。
3. **ネストしたダイアログ**（プリセット管理 → プリセット追加）を × で閉じて、
   **親のモーダル性が戻る**（phase 14 の非退行・受け入れ条件 8）。
4. **フック ON のままアプリを × で終了**して、**終了時にエラーダイアログが出ない**
   （受け入れ条件 4）。

### 設計メモ / 制約

- **本タスクでコードを書き換えない**。指摘への対応は判定後に切り分ける。
- レビュー結果は `instructions/phase/15_dialog_teardown_on_close/integration_result.md` へ記録する
  （phase 14 と同じ流儀）。**生ログは載せない**（判定と根拠のみ）。
- **レビュー・検証エージェントの起動はメインセッションの責務**。

## 含まない

- **正本反映・暫定仕様 13 の凍結・`decisions_archive/15` の作成・`current.md` の完了記載・
  `backlog/INDEX_done.md` への移動・`/refactor_check`** → **task_05**。
- 指摘に基づく実装修正（必要と判定されたら別タスクへ切り出す）。
- 非ダイアログ経路 5 系統の結線方式の変更 / スケルトン共通化 / idea_17（暫定仕様 §9）。

## 確認

python は必ずリポジトリルートの `.venv`（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. 上記「1. 統合確認」の全項目が pass（`verifier` の実測報告で確認）。
2. `deep-reviewer` と `codex-reviewer` の**両方**が完了し、指摘が整理されている
   （**採用 / 修正して採用 / 保留 / 除外** の判定つき）。
3. 「3. 残課題」について**ユーザー判定が得られている**。
4. 「4. 実機目視」4 項目の結果が**ユーザーから報告されている**。
5. `integration_result.md` に 1〜4 の結果が記録されている。
6. `git status` に本タスク由来のコード変更が無い（記録文書のみ）。

## 完了条件

- 上記確認 1〜6 をすべて満たす。
- **二次レビューの指摘がすべて処理済**（対応 / 別タスク化 / 保留 / 除外のいずれかが確定）。
- **実機目視は本タスクで実施する**（ユーザー）。未実施のままフェーズを完了扱いにしない。
