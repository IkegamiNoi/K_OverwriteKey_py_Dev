# task_07_diff_and_integration

## 目的

task_01〜06 の文言変更を、実装前後の文言の抽出差分で網羅確認し（暫定 51 §6-1・§6-2・§6-2a・§6-3）、統合確認と統合レビューを行う。
保留にしていた判断（下記）をユーザーへまとめて確認する。**コードの変更は確認で見つかった漏れの最小修正だけ。**

## 対象範囲

### 抽出と差分（メイン）

- `tools/extract_ja.py` を `keyseq/` に流して実装後の一覧 `tools/after_ja_strings.md` を作る。`baseline_ja_strings.md` と比べて:
  - 変わらなかった文字列のうち、暫定 51 §2 の「やめる語」（句で定義したものは句）・§3.6 の対象（半角括弧の和文・`既に`・`不正です`・英数字と和文の間の空白・全角コロン・`...`）を含むものを抽出し、**残存一覧 `tools/residual.md`** に「据え置きの理由」（§3.1 の対象外・§3.2 の据え置き・B 項・ログ専用・D10 等）を付けて並べる。理由の付かないものは漏れとして直す
  - task_06 の D3 一覧（`d3_ellipsis_list.md`）と実装のメニュー・ボタンの「…」を照合
- 漏れの修正は数行規模ならメイン、多ければ `codex-implementer`（テストの追従を含む）

### 保留の確認（ユーザー）

- `save_plan_execution.py:440`「別名保存先のディレクトリを作成できません」の「ディレクトリ」を「フォルダ」にするか（M9 は整理・退避の画面に限って確定）
- `preset_manager.py:320・356` の題「不正なhotkey」の言い換え（例: 「hotkey が正しくありません」）
- 残存一覧で判断が割れたもの

### 統合確認・統合レビュー

- `verifier`: compileall / tests / tests_ui / smoke
- 統合レビュー: `deep-reviewer`（task_01〜06 を跨ぐ差分・`git diff 1a4ef10..HEAD`）+ `codex-reviewer`（標準レビュー）。観点 = 用語の揺れが残っていないか・タスク間で同じ概念の文言が食い違っていないか・テストの追従で意図を弱めていないか

## 読むファイル

1. `instructions/history/51_ui_terminology.md` §2・§3.1・§3.2 の据え置き・§3.6・§6
2. `tools/baseline_ja_strings.md`・`tools/after_ja_strings.md`・`tools/d3_ellipsis_list.md`

## 含まない

- 実機目視・正本反映・暫定 51 の凍結・`/refactor_check`・完了判定前レビュー（task_08）

## 確認

- `tools/residual.md` の全行に据え置きの理由が付いている（理由の無い行が 0）
- D3 一覧の全行が実装と一致
- `verifier` 全 pass・統合レビュー 2 本の指摘の採否をユーザーと決めて反映

## 完了条件

- 上記確認 pass・統合レビュー（deep-reviewer + codex-reviewer）の反映・保留の判断の記録（decisions.md）。
- 実機目視は task_08。
