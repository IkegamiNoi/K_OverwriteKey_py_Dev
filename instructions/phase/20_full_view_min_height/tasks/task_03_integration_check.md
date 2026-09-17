# task_03_integration_check

## 目的

phase 20（task_01・task_02）の成果を統合確認し、二次レビューと実機目視で暫定仕様 18 §5 の受け入れ条件を満たすことを確かめる（暫定 §5-7・§5-8）。
**コードは原則変更しない**（レビュー指摘で修正が要る場合は採否をユーザーが決め、枝番タスク task_03b 等で行う）。

## 対象範囲（検証・レビュー・記録のみ）

### 統合確認（`verifier`）

1. `-m compileall -q keyseq main.py tests tests_ui`
2. `-m unittest discover -s tests`
3. `-m unittest discover -s tests_ui`
4. `-m tests.smoke_app`

### 二次レビュー（phase 20 の差分 = `5e25218..HEAD`）

- `deep-reviewer`: 複数タスクを跨ぐ差分として暫定 18 全体との整合（§3-1〜§3-6・§5）/ 測定順序 / minsize の全箇所 / 既存挙動（幅計算・保存判定・820 での見た目）の不変。
- `codex-reviewer`: 標準レビュー。
- 指摘は提示のみ。採否はユーザー。

### 実機目視（ユーザー・暫定 §5-8）

1. 標準 / ＋3 / −3 の各フォントで、フル表示のウィンドウを縦に縮める → 最小の高さで止まり、ヘッダ・3 枠のボタン列・チェックボックス・間隔入力・ステータス欄・ステータスバーが切れず、一覧が見える。
2. ＋3 で起動したとき、ウィンドウが 820 より高く開く（作業領域に収まる環境で）。
3. 省略表示へ切り替えると縦にも縮められ、フル表示へ戻すと再び最小の高さが効く。
4. 起動直後（標準フォント・820）の一覧の見た目が phase 19 時点と変わらない。

### 記録

- 結果を `instructions/phase/20_full_view_min_height/integration_result.md` に簡潔に記録（統合確認の件数 / レビューの採否 / 実機目視の結果）。

## 読むファイル

1. `instructions/history/18_full_view_min_height.md`（§3・§5）
2. `instructions/phase/20_full_view_min_height/phase.md`（レビュー方針）

## 含まない

- 正本反映・暫定仕様の凍結・decisions_archive・refactor_check（**task_04**）。
- レビュー指摘の修正（ユーザー採否の後、枝番タスクで実施）。

## 確認

- 統合確認 4 項目がすべて pass（失敗時は今回変更との関係を切り分けて報告）。
- `deep-reviewer` / `codex-reviewer` の指摘の採否がユーザーにより決定済み。
- 実機目視 4 項目がユーザーにより確認済み。

## 完了条件

- 上記確認を満たし、`integration_result.md` へ記録済み・**reviewer 採用**（記録内容の整合確認）。
- 実機目視は**本タスクで実施**。
