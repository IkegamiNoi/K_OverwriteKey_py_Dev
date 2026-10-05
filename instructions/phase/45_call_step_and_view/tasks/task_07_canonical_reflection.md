# task_07_canonical_reflection

## 目的

暫定 31（v0.6・§4.5.8 と §4.5.2 の追記を含む）を正本へ昇格し、phase 45 を閉じる（`.claude/rules/task_execution.md`「フェーズ完了時」）。**文書作業のみ（メイン）・コード不変**。

## 対象範囲

- 正本: 暫定 31 §12 の列挙どおり（`features.md` §4.2.3・§4.2.6・§4.2.8・§4.2.9・§4.2.10・§4.6 / `data_schema.md` §5.11.6・§5.4 / `codebase_map.md`）。
  v0.6 の §4.5（参照による連動）が §4.2〜§4.4 の「文脈・写し」の記述に優先するので、正本には**写し・呼び出し文脈の常駐を書かず**連動の形で書く
- 実装中に決めた補いを正本に明記する（decisions.md の phase 45 節）:
  - §4.5.1 の「キー変更」は印が消えるのではなく新しいキーへ**移る**
  - v0.5 の §10-4a（「送った」の互換）は §4.5.6 で置き換わる。§4.2.8 の例として「一括の呼び出しで送った後に位置を停止の行へ移して再開すると止まる」
  - 待機中の呼び出し先に入る時点の扱い（その押下 / 連続実行で未送信なら押下の開始へ全部戻し押下を消費しない / 送った後なら単発は一時停止・連続実行はそのステップだけ戻して一時停止）
  - §4.5.8（M3・M4・L1・L2）
  - §4.5.2 の「無視」は単発の T だけ。連続実行の T は §4.2.10 の単発の待機の取り消しを優先（2026-10-05 ユーザー確定）
  - task_03a の保留 M1（文脈の「送った」に入れ子の呼び出しの成功を数えない）は v0.6 で「送ったは連続実行 1 回ごと」に置き換わったかを確認し、残るなら明記
- `codebase_map.md`: 参照中の印（`AppState.call_refs_for`）・連鎖（`application/call_chain.py`）・押下の番号つき履歴（`sequence_history.py`）・`sequence_runner/linked_call.py` ほか runner の mixin・表示の問い合わせ（`call_view_summary_for`）・`CallViewController` の host 2 つ・`call_view_heights`
- フェーズ完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）と指摘の対応
- 暫定 31 の凍結 / `decisions_archive/45_call_step_and_view.md` / decisions.md のアーカイブ索引 / current.md の完了記載（次採番の明記）/ `/refactor_check`
- 起票元 idea: なし（ユーザー要望 2026-10-04）

## 読むファイル

- `instructions/history/31_call_step_and_view.md`（全体）
- `.claude_data/state/decisions.md` の phase 45 節
- 正本の該当節（`features.md` §4.2.3・§4.2.6・§4.2.8〜§4.2.10・§4.6 / `data_schema.md` §5.4・§5.11.6 / `codebase_map.md`「出力シーケンスの制御アクション」節）

## 含まない

- コードの変更（レビューで修正が要る場合は枝番タスクを起票する）

## 確認

- 正本の各節が暫定 31 §12 の列挙と上の補いを漏れなく含む（レビューで照合）
- 正本に v0.5 以前の「呼び出し文脈・開始時点のコピー・呼び出し先自身の状態は変えない・履歴は呼び出し全体で 1 段」の旧記述が残っていない

## 完了条件

- 上記をすべて実施し、レビュー 2 種の結果と `/refactor_check` の判定を完了報告に含める（文書のみのため reviewer は deep-reviewer で代える）。
- 実機目視: なし（task_01〜06 で実施済み）。
