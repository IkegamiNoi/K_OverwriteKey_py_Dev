# phase.md

## フェーズ名

アプリの窓が前面のときはキーリピートしない（repeat_stop_on_own_foreground）

## フェーズの目的

key_hold のキーリピート（phase 52）の最中に、アプリ自身のダイアログ（messagebox・ファイル選択・独自ダイアログ）が前面に来て、リピートした `enter` 等がダイアログを閉じる・意図しない選択をするのを防ぐ。
**方式 = 前面ウィンドウ判定**（送り直しの発火ごとに OS の前面の窓が自プロセスかを確かめ、そうなら止める・再開しない）。**application（`KeyRepeater`）・infrastructure（前面判定）・presentation（App の配線）。JSON の変更なし。ダイアログを出す側は変えない。**

- 起票元: [idea_42](../../backlog/idea_42_suppress_repeat_on_all_dialogs.md)（2026-10-11 phase 52 完了判定前レビュー・ユーザーが次フェーズで実装を希望）。
- 主入力（暫定仕様）: [37_repeat_stop_on_own_foreground.md](../../history/37_repeat_stop_on_own_foreground.md)（v0.4・ユーザー確定済 2026-10-11）
- モード: **暫定仕様先行モード**。番号対応: phase 53 / 暫定 37 / decisions 53。

## 確定（ユーザー 2026-10-11）

暫定 37 §2 の 1〜7 が正（本書に再掲しない）。要点: 前面の窓のプロセス判定 / 止めたら再開しない / メイン画面が前面でもリピートしない / 開始時は判定せず発火時だけ /
前面の窓が NULL なら止める・Win32 の例外は止めない / 判定と送信の間の競合は受容。

## スコープ

### 含む

- 暫定 37 §3・§4・§6 の実装とテスト（前面判定の関数・`KeyRepeater` の `is_blocked`・App の配線・tests_ui の抑止のテストの差し替え）
- 正本反映（暫定 37 §10）

### 含まない（後送り）

- 暫定 37 §9 のとおり（ダイアログを出す側の変更・前面が戻ったときの再開・リピート以外の送信の抑止）

## このフェーズで読むファイル

1. `instructions/history/37_repeat_stop_on_own_foreground.md`（全体）
2. `keyseq/application/key_repeat.py`（全体）
3. `keyseq/infrastructure/input_gateway.py`（`keyboard_repeat_timing`・`_read_keyboard_setting` の形）・`keyseq/presentation/modal.py:15-31`（専用の user32 インスタンスの作り方）
4. `keyseq/presentation/app.py`（`KeyRepeater` の生成 :126-130）
5. テスト: `tests/test_key_repeat.py`・`tests/test_input_gateway_repeat.py`・`tests_ui/test_key_hold_presentation.py`
6. 正本: `instructions/common/spec_detail/features.md` §4.2.12「キーリピート」/ `key_input.md` §7.7 / `codebase_map.md` の phase 52 の項

## タスク

- task_01: 前面判定の関数（infrastructure）・`KeyRepeater` の `is_blocked`（`_fire` だけ）・App の配線とテスト（暫定 37 §3・§4・§6・§8 の 1〜8）。**実装後にユーザーの実機目視**（§8 の 9〜11） — **完了**（2026-10-11・ユーザー実機目視 OK〔§8 の 9〜11〕・codex-implementer・reviewer 採用・tests 1501 / tests_ui 942 / smoke pass）
- task_02: 統合確認（tests / tests_ui / smoke・deep-reviewer + codex-reviewer）
- task_03: 正本反映（暫定 37 §10 の昇格・凍結）・`decisions_archive/53_repeat_stop_on_own_foreground.md`・decisions.md の索引・current.md の完了記載・idea_42 を INDEX_done へ・`/refactor_check`

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: **前面判定の真偽の向き**（NULL = 止める・例外 / Windows 以外 = 止めない）/ 判定は `_fire` だけで `start` では呼ばない / 止めた後に再開しない（世代・予約の取り消し）/
  共有の `windll` の属性を書き換えない / 例外のログは初回だけ / tests_ui が実環境の前面に依存しない / テストが実入力を送らない・実 `config/` を汚さない
- 統合確認（task_02）: `deep-reviewer` + `codex-reviewer` / 完了判定前（task_03）: `deep-reviewer` + `codex-adversarial-reviewer`
- 実機目視（ユーザー・**ホスト OS**）: task_01
