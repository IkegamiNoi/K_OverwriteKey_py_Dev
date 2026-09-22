# task_06_redraw_on_edit_failure

## 目的

履歴ダイアログの編集が**失敗したときも一覧を再描画**する。現在は成功時のみ再描画するため、
**破損退避が起きた直後に編集が拒否された場合、ディスクは空なのに一覧が古い内容を表示したまま**になる。
暫定仕様 21 §6「ダイアログは自分の表示内容を正とせず、読込・編集のたびに永続化済みの履歴を
読み直して再描画する」/ 正本 `features.md` §4.6 の同条項に合わせる。

フェーズ完了判定レビュー（`deep-reviewer` M5）の指摘で、**ユーザー判断 = 失敗時も再描画する**（2026-09-22）。

レイヤ制約: **presentation の 1 ファイルのみ**。domain / application / 他のコントローラは変更しない。
**永続化の成否判定・理由の文言・ボタンの有効無効の規則は変えない**（表示の更新順序だけを直す）。

## 対象範囲

### keyseq/presentation/dialogs/keymap_set_history_dialog.py（`_finish_edit` のみ）

```python
    def _finish_edit(self, result: tuple[bool, str]) -> None:
        success, reason = result
        self._redraw()
        if not success:
            messagebox.showinfo(text.TITLE, reason, parent=self)
```

- **再描画を先に行い、そのあとで理由を表示する**（モーダルの裏の一覧が最新になった状態で理由が出る）。
- 失敗時に再描画しても**失敗した編集は反映されない**（`_redraw` は controller 経由で
  永続化済みの内容を読み直すため）。暫定仕様 §4.3 と矛盾しない。
- コメント（`# 保存に失敗した場合、未確定の変更を一覧へ反映しない。`）は趣旨が変わるので
  実態に合う内容へ直すか削る。**これ以外の行は触らない**。

### tests_ui/test_keymap_set_history_flow.py（テストの追随・最小）

- 既存 `test_save_failure_preserves_tree_for_four_operations`（保存失敗の 4 操作）は
  **一覧が変わらないことの検証を維持**したまま、**失敗時にも履歴の読み直しが走る**ことを足す
  （`load_keymap_set_history` の呼び出し回数、または `_redraw` 相当の再構築が起きること）。
- **永続化済みの内容が変わっていた場合に、失敗した編集操作のあとで一覧がその内容へ追従する**ことを
  1 件追加する（例: 保存を失敗させつつ、ディスク側の履歴を差し替えておき、操作後のツリーが
  差し替え後の内容に一致する）。
- 既存テストの意図を弱めない（アサーションの削除・緩和をしない）。

## 含まない

- `_finish_edit` 以外の変更（`_load` は既に失敗時に `_redraw()` する。触らない）。
- 正本・暫定仕様の改訂（**正本 `features.md` §4.6 は既に「読込・編集のたびに再描画」と規定済み**で、
  本タスクは実装をそれに合わせるもの）。
- レビュー指摘のうち他の項目（読み取り専用の都度判定 = 正本側で決着 / 未知キー = 正本へ明記 /
  多重起動時の TOCTOU と index 陳腐化 = 受容）。いずれも**コード変更しない**と決定済み。

## 確認

`verifier` へ委任して `.venv` で実測する（Codex は python を実行できない）。

```
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests tests_ui
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```

- compile clean / `tests` = **556 ran OK（skipped 7・不変）** / `tests_ui` = **483 + 追加分で OK** /
  smoke = `SMOKE OK`。
- **副作用ゼロ**（worktree ルート・`config/` 直下とも `keymap_set_history*.json` 未生成・
  `config/config.json` の mtime 不変）。
- **既知の flaky に注意**: `tests_ui` 一括実行は `focus_force()` + `event_generate("<Escape>")` 依存の
  テストが負荷下で不定期に落ちる（[idea_18](../../../backlog/idea_18_escape_delivery_flaky_test.md)・
  症状は `get_hook_pause_count()` が `1 != 0`）。**この症状で落ちた場合は再実行して切り分ける**
  （単体実行が安定なら flaky と判定してよい）。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**（観点: 失敗時に編集が反映されていないこと /
  再描画が永続化済みの内容を読み直していること / 文言と有効無効の規則が不変であること）。
- 実機目視は**不要**（表示の更新順序のみ。task_04 で UI の一巡は確認済み）。
