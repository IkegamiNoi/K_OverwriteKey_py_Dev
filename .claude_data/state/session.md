# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-11T23:30:00
phase: なし（phase 54 は 2026-10-11 完了）。次採番 = phase 55 / 暫定 39 / decisions 55 / 提案書 21。次フェーズはユーザー判断
直前の完了フェーズ = **phase 54**（テンキーの区別・`decisions_archive/54_numpad_key_distinction.md`）。その前 = phase 53（アプリの窓が前面のときはキーリピートしない）/ phase 52（key_hold のキーリピート）
last_commit_location: `claude/physical-device-inspection-a9201a`（phase 52〜54 完了まで。main へのマージはユーザー）
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: present
focus: **phase 52・53・54 完了。アクティブなフェーズなし・次フェーズはユーザー判断待ち。main へのマージはユーザー。**
mode: active

## last_action
ts: 2026-10-11T23:30:00
who: main
summary: |
  phase 52 完了（task_03〜05・実機目視 §8-12〜15 OK・修飾キー判定の `_` 綴りを修正・UI 操作のダイアログの抑止は idea_42 へ分離）。
  phase 53 完了（暫定 37 v0.4・送り直しの発火ごとに前面の窓が自プロセスなら止める・実機目視 OK・レビュー指摘は文書のみ）。
  phase 54 完了（暫定 38 v0.5・テンキーを `num 0`〜`num 9` / `num add` 等で入力〔is_keypad + スキャンコード〕・送信〔SendInput スキャンコード入力〕・記録〔Tk の keycode + 拡張ビット〕で区別・既存の名前は入力では主キーボードだけ・実機目視 OK・`/` の key_identity の 0xE0xx を修正）。
result_files:
  - instructions/history/36〜38（凍結）/ instructions/phase/52〜54/ / decisions_archive/52〜54
  - keyseq/domain/numpad_keys.py（新規）・key_hold.py / keyseq/application/key_repeat.py・input_router.py・key_state_manager.py / keyseq/infrastructure/input_gateway.py / keyseq/presentation/app.py・tk_keys.py・記録の入口 / tests・tests_ui
verified:
  compile: clean
  tests: 1525 OK（skipped 7）
  tests_ui: 945 OK
  smoke: pass
  review: phase 52〜54 の完了判定前 deep-reviewer + codex-adversarial-reviewer の指摘は反映 / 裁定済

## next_action
- 次フェーズはユーザー判断（着手時は `/phase_start`）。main へのマージはユーザーが行う
- 別タスク化候補に `input_gateway.py` の責務の並び（phase 54 の /refactor_check・境界事例）を追記済み

## blockers
- なし

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **素の `python` を Bash で呼ばない**（必ず `..\..\..\.venv\Scripts\python.exe`）。Bash の heredoc の前に `cat > file` を単独で書かない（stdin 待ちでハングする）。
- **Codex は互換の工夫・テストの期待値の推測を足すことがある**（phase 54 でも新規テストの期待値・Mock の戻り値の誤りが 2 件）。差分を直読みしてから verifier / reviewer へ。Codex は LF を混ぜることがある（コミットは git が正規化）。
- キー入力の要点: 押下中の集合 = `application/held_inputs.py` / リピート = `application/key_repeat.py`（`is_blocked` = 前面判定・発火時だけ）/ 送信・同じキー・名前の検査 = `infrastructure/input_gateway.py` / テンキーの名前 = `domain/numpad_keys.py`（入力）・`presentation/tk_keys.py`（記録）。正本は `key_input.md` §7.7・§7.8・`features.md` §4.2.12
- `tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・current.md「テスト負債」）。
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜38）の条項を実装の根拠に引かない。
