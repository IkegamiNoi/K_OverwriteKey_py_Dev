# task_02_remove_trigger_list_alias

## 目的

View に残る `trigger_list` alias（`full_view.py` / `compact_view.py` の
`self.trigger_list = self.trigger_box.trigger_list`）を**削除**し、tests_ui の参照経路を
所有 Widget 経由（`app.<view>.trigger_box.trigger_list`）へ変更する（[phase.md](../phase.md) スコープ「含む」2）。

この alias は計画04 W3/W4 で外部契約保持のために置いた**暫定措置**。W5 で production 側は
`TriggerPanelController._trigger_lists`（登録方式）へ移行済みのため、**現在 alias に依存しているのは
tests_ui のみ**＝テストのためだけに残る遺物になっている（`.claude_data/state/decisions.md`
「【W3/W4】分割で失われる外部属性契約を alias で保持」参照）。

**レイヤ制約: presentation 限定**（+ tests_ui の参照経路のみ）。domain / application / infrastructure 不変。
スキーマ不変。**挙動不変**。

## 対象範囲（presentation 限定 + tests_ui の参照経路のみ・3ファイル・数行）

### 1. `keyseq/presentation/views/full_view/full_view.py`

- **48 行目 `self.trigger_list = self.trigger_box.trigger_list` を削除する。**
- 前後（47 行目 `self.trigger_box = FullTriggerBox(self.main_area, app)` / 49 行目
  `self.trigger_box.pack(side="left", fill="y", padx=(12, 0))`）は**変更しない**。

### 2. `keyseq/presentation/views/compact_view/compact_view.py`

- **36 行目 `self.trigger_list = self.trigger_box.trigger_list` を削除する。**
- 前後（35 行目 `self.trigger_box = CompactTriggerBox(self.main_area, app)` / 37 行目
  `self.trigger_box.pack(side="top", fill="both", expand=True)`）は**変更しない**。

### 3. `tests_ui/test_app_ui_flows.py`

`test_trigger_lists_populated`（39-41 行目）の**参照経路のみ**を変更する:

| 現状 | 変更後 |
|---|---|
| `self.assertEqual(self.app.full_view.trigger_list.size(), 2)` | `self.assertEqual(self.app.full_view.trigger_box.trigger_list.size(), 2)` |
| `self.assertEqual(self.app.compact_view.trigger_list.size(), 2)` | `self.assertEqual(self.app.compact_view.trigger_box.trigger_list.size(), 2)` |

**アサーションは変更しない**（`assertEqual` / `.size()` / 期待値 `2` / テストメソッド名は不変）。

### 設計メモ / 制約

- **⚠️ `action_list` alias は削除しないこと**（`full_view.py:52` の
  `self.action_list = self.sequence_box.action_list`）。`trigger_list` とは性質が異なる:
  - `trigger_list`: **複数 View 共有** → W5 で登録方式（`_trigger_lists`）へ移行済み。
    production は View 経由で触らない ＝ alias は tests_ui 専用の遺物 → **削除**
  - `action_list`: **単一 View 所有**で、production の `controllers/trigger_panel_controller.py` が
    `self._app.full_view.action_list` を**実際に使用中**（計画04 §1.3-2 が認める
    「App → View → Widget のパス」そのもの）→ **据え置き**（phase.md「含まない」）
- **削除前に「production が alias に依存していない」ことを grep で再確認すること**:
  `git grep -n "\.trigger_list" -- keyseq` を実行し、残る参照が
  `views/full_view/trigger_box.py` / `views/compact_view/trigger_box.py` の**所有者側**
  （`self.trigger_list = tk.Listbox(...)` と `app.trigger_panel.register_trigger_list(self.trigger_list)`）
  のみであることを確認する。
  **`controllers/` 配下に `.trigger_list` 参照が残っていたら、独自判断で進めず報告して停止すること。**
- 各 Widget（`FullTriggerBox` / `CompactTriggerBox`）の `self.trigger_list` は**所有者の属性なので残す**。
  削除するのは View 側の alias 2 行のみ。
- 削除に伴う整形（空行の詰め直し等）はしない。

## 含まない

- `action_list` alias の削除（上記のとおり据え置き。将来やるなら別タスク）
- `views/status_bar.py` の生やし解消（**task_01**・完了済）
- 正本反映・記録・`/refactor_check`（**task_03**）
- tests_ui の**アサーション**・テストメソッド名・テストデータの変更
- `TriggerPanelController` の変更（`_trigger_lists` 登録方式は W5 で完成済・触らない）
- 計画04 W7 の次期課題（[idea_01](../../../backlog/idea_01_hotkey_validation_to_domain.md) /
  [idea_02](../../../backlog/idea_02_startup_font_settings_cleanup.md)）

## 確認

python は必ずリポジトリルートの `.venv` を使う（worktree 相対 `..\..\..\.venv\Scripts\python.exe`。
グローバル `py` は依存欠落で tests_ui / smoke が落ちる。`.claude/rules/python_rules.md`）。

1. **grep（alias 削除の確認）**:
   `git grep -nE "self\.trigger_list *= *self\.trigger_box\.trigger_list" -- keyseq` が **0 件**
2. **grep（残存参照の妥当性）**: `git grep -n "\.trigger_list" -- keyseq tests_ui` の結果が以下のみ:
   - `views/full_view/trigger_box.py` / `views/compact_view/trigger_box.py`（所有者の生成 + register 呼び出し）
   - `tests_ui/test_app_ui_flows.py`（新経路 `<view>.trigger_box.trigger_list` ×2）
   - **`controllers/` 配下に残っていないこと**
3. **grep（action_list 据え置きの確認）**:
   `git grep -n "self\.action_list *= *self\.sequence_box\.action_list" -- keyseq` が **1 件**（`full_view.py`）
4. **標準検証 4 項目**（ベースライン一致）:
   - `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py` → clean
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` → **59 pass**
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` → **9 pass**
     （**`test_trigger_lists_populated` が新経路で pass すること**＝本タスクの主目的の検証）
   - `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` → **SMOKE OK**
5. **差分確認**: `git diff -- tests_ui/test_app_ui_flows.py` の差分が
   **参照経路の 2 行のみ**（アサーション・期待値・メソッド名に差分が無いこと）

## 完了条件

- 上記「確認」1〜5 が pass。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点。CLAUDE.md「レビュー（必須）」）。
- **実機目視: 本タスクで task_01 と合わせて実施**（phase.md「レビュー方針」の手動確認）:
  - ステータスバー表示（ファイル状態 / 一時メッセージ / 「ステータス」欄）＝ task_01 の確認
  - フル・省略両ビューでのトリガー一覧の表示・選択共有 ＝ task_02 の確認
