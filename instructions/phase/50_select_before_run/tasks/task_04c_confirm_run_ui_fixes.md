# task_04c_confirm_run_ui_fixes

## 目的

実機目視の指摘（2026-10-08）で暫定 34 を v0.6 に改訂した（ユーザー確定 2026-10-09）。そのうち presentation の 3 点を実装する（暫定 34 §2-10〜13・§5・§10 の 11・11a）。

## 対象範囲

1. **文言**: チェックボックスの文言を「選んでから実行」→「**確認して実行**」（フル表示のフック欄・省略表示のフック欄・出力シーケンス欄の 3 か所）。一時メッセージ・変数名・JSON のキー・コードの名前は変えない
2. **フル表示のフック欄**（`views/full_view/hook_frame.py:48-64`）: 全体のチェックを個別指定チェックの**下の行**へ（`full_hook_line2` の grid row=3・columnspan=4・sticky="w"・pady=(4, 0)）。右隣のために作った `checks_line` と「同じ行に並べる」コメントは不要になるので戻す
3. **出力シーケンス欄**（`views/full_view/sequence_box.py:68-90`）: トリガーごとのチェックを「間隔(ms)」の行（`delay_line`）の**下**へ移す（並べ替えのみ）
4. **省略表示のフック欄**（`views/compact_view/hook_frame.py:48-52`）: 全体のチェックを**操作できる**状態にし、`command=app.toggle_select_before_run` を付ける（フル表示と同じ）。個別指定チェックは無効のまま
5. テスト（`tests_ui/test_select_before_run_ui.py` ほか）: 置き場（:178-182 付近の右隣の前提）・省略表示の無効の前提を新しい仕様に直し、省略表示のチェックの操作で構成セットが未保存になり、フル表示の表示と同期することを足す。文言のテストがあれば直す
6. **フル表示の最小の高さのテスト**（`tests_ui/test_full_view_min_height.py`）: 行を足すとフォント +3 で最小の高さが 920 → 931 px になる（実測・画面の高さ 966 px の環境）。このため画面に収まらず落ちるテストがあれば、**はみ出しを受容する前提**（暫定 34 §2-11）に合わせて直す。
   例: 窓の高さが最小の高さに届くことを確かめる箇所は、最小の高さが画面に収まる場合だけ確かめる。どう直したかと、直した理由を報告する。テストの意図（中身が見切れない・最小の高さの再計算）は弱めない

## 対象外

- application（task_04b）・JSON・正本の改訂（task_05）
- フル表示の他の欄の詰め直し・最小の高さの計算の変更

## 読むファイル

- `instructions/history/34_select_before_run.md` の §2-10〜13・§5・§10
- 上記の view 3 ファイル・`keyseq/presentation/app.py:595-605`（`toggle_select_before_run`）
- `tests_ui/test_select_before_run_ui.py`・`tests_ui/test_full_view_min_height.py`

## 確認

- tests_ui 全体・tests 全体・smoke pass（verifier が `.venv` で実行・tests_ui は 1 本ずつ）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視（ユーザー）: 文言・フック欄の置き場（個別指定の下）・シーケンス欄の置き場（間隔の下）・省略表示のチェックの操作と未保存・戻す・先頭への対象（task_04b）
