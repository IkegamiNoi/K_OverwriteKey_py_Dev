# phase.md

## フェーズ名

選んでから実行（select_before_run）

## フェーズの目的

一覧で選ばれていない（フォーカスされていない）トリガーのキーを押したら、1 回目は一覧でそのトリガーを選ぶだけにし、選ばれた状態でもう一度押したら実行するモードを加える（シーケンス欄で位置と中身を確かめてから実行するため）。
**domain / application / presentation。keymap_set と sequence の JSON にキー `select_before_run` を 1 つずつ追加（後方互換）。単発の待機明けの選び直しの既存挙動を変える（暫定 34 §2-8）。**

- 起票元: ユーザー要望（2026-10-07）。
- 主入力（暫定仕様）: [34_select_before_run.md](../../history/34_select_before_run.md)（v0.4・ユーザー確定済 2026-10-08）
- モード: **暫定仕様先行モード**。番号対応: phase 50 / 暫定 34 / decisions 50。

## 確定（ユーザー 2026-10-07〜08）

暫定 34 §2 の 1〜9 が正（本書に再掲しない）。要点: 1 回目は選ぶだけ（一時メッセージ）・2 回目で実行 / 全体（構成セット）とトリガーごと（シーケンス）のどちらかが ON なら対象 /
直接置換・停止系・戻す・先頭へだけのトリガーは対象外 / 処理中・再開・待機中は従来どおり / 省略表示は全体のチェックを表示のみ /
待機の間に選択が変わっていたら待機明けに選び直さない（既存挙動の変更）/ 選ぶだけの押下は離すまでのリピートを無視。

## スコープ

### 含む

- 暫定 34 §3〜§8 の実装とテスト（保存 §6・判定 §3 / §4・リピート・待機明け §8・UI §5・責務 §7）
- 既存テストの追随（待機明けの選び直しの変更に当たるもの）
- 正本反映（暫定 34 §12）

### 含まない（後送り）

- 暫定 34 §11 のとおり（時間制限・控え・直接置換への適用・全体設定のアプリ全体化・省略表示での設定の操作・1 回目の suppress の変更）

## このフェーズで読むファイル

1. `instructions/history/34_select_before_run.md`（全体）
2. `keyseq/application/sequence_runner/input_acceptance.py:120-210`・`sequence_runner.py:290-310, 360-380`・`send_wait.py:20-70`
3. `keyseq/application/input_router.py:74-133`・`keyseq/application/key_state_manager.py`（リピートの判定材料）・`action_executor.py:183-205`
4. 保存: `keyseq/application/config_service/split_loading.py:100-115, 485-515`・`split_payloads.py:445-480, 530-545`・`config_service/__init__.py:455-470`・`config_service/child_file_io.py`（個別保存・読込）・`keyseq/domain/config.py:100-235`
5. UI: `keyseq/presentation/views/full_view/hook_frame.py`・`views/compact_view/hook_frame.py`・`views/full_view/sequence_box.py:60-90`・`controllers/trigger_panel/trigger_panel_controller.py:370-405, 475-525`・`presentation/app.py:120-140, 230-245, 510-530, 590-615`
6. テスト: `tests/test_sequence_runner.py`・`tests/test_input_router.py`・保存の往復テスト（`tests/test_config_service*.py`）・`tests_ui/test_app_ui_flows.py`

## タスク

- task_01: domain / application（保存）— keymap_set と sequence（trigger_set 内・単一 JSON のインラインを含む）の `select_before_run` の読み書きとテスト（往復: 保存 → 再読込 / Import → Export / 個別保存 → 個別読込）（暫定 34 §6） — **完了**（2026-10-08・codex-implementer・reviewer 完了可。出力を固定している既存テスト 11 件〔キー集合・順序・保存バイト列〕を §6「常に書く」に合わせて追随＝仕様起因。tests 1330 / tests_ui 895 / smoke pass）
- task_02: application（判定）— 選ぶだけの判定（§3・§4・戻す・先頭へだけの除外）・リピートの無視（InputRouter の印 + runner）・待機明けの選び直しの変更（§8）・注入口（省略時は機能 OFF）とテスト・既存テストの追随（§3・§4・§7・§8） — **完了**（2026-10-08・codex-delegating-implementer〔Luna サブエージェント使用〕・reviewer 修正要〔on_trigger の内省による互換 → `(key, repeat)` に固定・app.py の配線 1 行を含む〕→ メインで修正。既存の切替テスト 1 件は離さず再押下＝repeat の印が付くのが正しいため種類とキーの比較へ。tests 1345 / tests_ui 895 / smoke pass）
- task_03: presentation — フル表示のフック欄の全体のチェック（dirty・読込等での同期）・省略表示の表示のみのチェック・出力シーケンス欄のトリガーごとのチェック（同期・書き戻し・dirty）・選択の口の注入と配線とテスト（§5・§7）。**実装後にユーザーの実機目視** — **実装・検証済・実機目視待ち**（2026-10-08・codex-delegating-implementer〔サブエージェント不使用〕・reviewer 修正要〔テスト用の getattr の逃げ道・view から controller の直 import・import の並び〕→ メインで修正。検証でフォント +3 のフル表示の最小の高さが画面の上限を超えた〔フック欄に行を足したため〕→ 全体のチェックを個別指定チェックと**同じ行の右隣**へ（省略表示は次の行・§5「置き場は実装時に決め実機目視」の範囲）。新規テストの期待値〔label の補完〕もメインで修正。tests 1345 / tests_ui 907 / smoke pass）
- task_04: 統合確認（tests / tests_ui / smoke・deep-reviewer + codex-reviewer）と**ユーザーの実機目視**（暫定 34 §10） — **統合レビュー済・ユーザー判断と実機目視待ち**（2026-10-08・deep-reviewer 修正要〔軽微: M1 待機明けの判定方法が暫定 34 §7/§8 の文言と違う・M2 条件 7 と 8 のテスト不足・低 L1〜L13〕/ codex-reviewer P2 1 件〔トリガー以外のキーの押下で長押しの無視が終わらない = deep L1〕。判断待ちの 2 点 → ユーザー判断 2026-10-08 でどちらも実装を正とする案 A・暫定 34 v0.5）
- task_04a: 統合レビューの指摘対応（判断 2 点を暫定 34 v0.5 の文言に反映・受け入れ条件 7・8 のテスト追加。本体不変）— **完了**（2026-10-08・codex-implementer・メインでテスト 3 本の期待値を修正〔実行後の既存の選び直し・メッセージの累積〕・reviewer 採用。task_05 で揃える: 暫定 34 の send_wait の行番号表記・条件 8 と §8 の言い回し。tests pass）
- task_04b: application — 対象指定の無い戻す・先頭への対象を一覧の選択に・戻す・先頭へだけのトリガー自身を選ばない（暫定 34 v0.6 §2-14・§3a）。実機目視の指摘（2026-10-08）・v0.6 ユーザー確定（2026-10-09・Codex 敵対的 high 1 を反映）
- task_04c: presentation — 文言「確認して実行」・フック欄は個別指定の下の行・シーケンス欄は間隔の下・省略表示の全体のチェックを操作可（暫定 34 v0.6 §2-10〜13）。**実装後にユーザーの実機目視**
- task_05: 正本反映（暫定 34 §12 の昇格・凍結）・`decisions_archive/50_select_before_run.md`・decisions.md の索引・current.md の完了記載・`/refactor_check`。起票元 idea なし

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: 機能 OFF（両方の設定 OFF・注入なし）で従来と完全に同じか / 選ぶだけの押下が実行状態（位置・周回・保留・戻す履歴・直前のトリガー・一時停止中のもの・他の待機）を一切変えないか /
  §4.2.10 の判定順（処理中 → 再開 → 自身の保留 → 空 → 選ぶだけ → 開始）/ リピートの無視の始まりと終わり / 待機明けの選び直しの変更が他の選択の動き（実行後・連続実行・呼び出し・file_line）に波及しないか /
  保存の往復で値が落ちないか・古い JSON が OFF で読めるか / テストが実 `config/` を汚さないか
- 統合確認（task_04）: `deep-reviewer` + `codex-reviewer` / 完了判定前（task_05）: `deep-reviewer` + `codex-adversarial-reviewer`
- 実機目視（ユーザー）: task_03・task_04（全体 / 個別の ON・OFF・選ぶだけの案内・2 回目の実行・長押し・待機中の選択・省略表示の表示・保存して再読込）
