# task_06a_completion_review_fixes

## 目的

phase 48 の完了判定前レビュー（Codex 敵対的 medium 1 件 = deep-reviewer M2・deep-reviewer L2）への対応。ユーザー判断 2026-10-07 で 2 点とも「直す」。
**presentation 限定・正本（`features.md` §4.6「省略表示のシーケンス欄」）どおりに寄せるだけ（仕様の変更なし）。**

## 対象範囲（presentation 限定）

### `keyseq/presentation/controllers/compact_sequence_controller.py`

- `_row_at`（:85-94）で横の位置も確かめる: `0 <= event.x < listing.winfo_width()` でなければ None。
  行を押した後に一覧の左右の外（スクロールバーの上・窓の外）で離したとき、次に実行を変えない（正本「一覧の外で押した / 離した場合は何もしない」）

### `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`

- `set_next_action_index`（:587-590）の判定の順序を入れ替え、**有効でないトリガーなら何もしない（拒否の一時メッセージを出さない）**確認を、呼び出し先の実行中の拒否より先に行う（正本「有効でないトリガーでは何もしない / 呼び出し先の実行中は拒否」の順）。
  フル表示の経路（`refuse_running_callee=False`）の挙動は変わらないこと。**行数を増やさない**（640 行以下）

### テスト

- `tests_ui/test_compact_sequence_view.py`:
  ①行を押して同じ高さのまま一覧の右の外（`x = listing.winfo_width() + 1`）・左の外（`x = -1`）で離しても次に実行・選択の帯が変わらない
  ②グレーの行を選んでいて、同じキーの有効な行が実行中の呼び出し先のとき、省略表示の欄のクリック / キー操作で拒否の一時メッセージが出ず、次に実行も変わらない（既存 `test_navigation_rejects_ineffective_trigger_and_running_callee` の作りを手本にする）
- 既存テストで `SimpleNamespace(y=...)` だけを渡している箇所は、一覧の内側の `x`（例 `x=5`）を足して追随する（期待値は変えない）

## 読むファイル

- `keyseq/presentation/controllers/compact_sequence_controller.py`（全体）
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:580-605`
- `tests_ui/test_compact_sequence_view.py`（全体）
- 正本 `instructions/common/spec_detail/features.md` の「省略表示のシーケンス欄」節の「操作」

## 含まない

- 提案書 20 のリファクタ（task_07_refactor）
- フル表示の一覧のクリック・キー操作の挙動（フル表示のキー操作に拒否が無いのは既存のまま）
- deep-reviewer の保留（L5 codebase_map の索引・L7 CallViewController の分岐〔task_07〕・L8 閉じたときの `_drag_heights`）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` clean
- 追加・変更したテストを含めて tests・tests_ui 全体・`-m tests.smoke_app` pass。実 `config/` を汚さない
- `trigger_panel_controller.py` の行数が 640 以下

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視: なし（挙動は task_05 の目視範囲内の端の場合のみ）
