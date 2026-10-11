# phase.md

## フェーズ名

テンキーの区別（numpad_key_distinction）

## フェーズの目的

テンキーのキーを主キーボードのキーと区別する。入力の判定・出力（送信）・記録で、テンキーは専用の名前（`num 0`〜`num 9` / `num add` / `num subtract` / `num multiply` / `num divide` / `num decimal` / `num enter`）で扱い、既存の名前は入力の判定では主キーボード側だけを指す。
**domain（名前の表・名前の関数）・application（入力の名前の決定）・infrastructure（送信・名前の検査・同じキーの判定）・presentation（記録）。JSON の形は変えない（キー名の値が増える）。既存設定の意味が変わる（テンキーで反応していた `1` / `end` 等の設定はテンキーで反応しなくなる）。**

- 起票元: [idea_43](../../backlog/idea_43_numpad_key_distinction.md)（2026-10-11 ユーザー要望）。
- 主入力（暫定仕様）: [38_numpad_key_distinction.md](../../history/38_numpad_key_distinction.md)（v0.4・ユーザー確定済 2026-10-11）
- モード: **暫定仕様先行モード**。番号対応: phase 54 / 暫定 38 / decisions 54。

## 確定（ユーザー 2026-10-11）

暫定 38 §2 の 1〜10 が正（本書に再掲しない）。要点: 全場面で区別 / `num` + 数字・単語の名前 / 既存名は入力の判定では主キーボードだけ / NumLock に関係なく物理キーで同じ名前 /
外部レイアウトより表の名前・表の名前はテンキーのイベントだけ / 記録で区別できないキーは受容 / キーボード表示は足さない / 記号の出力は従来どおり / `num_1` 等はエラー。

## スコープ

### 含む

- 暫定 38 §3〜§6 の実装とテスト（名前の表・入力の名前の関数・送信・同じキーの判定・名前の検査・記録）
- task_01 の probe（送り方・Tk の keysym・偽の shift）の結果による暫定 38 の改訂（違えばユーザー確認）
- 正本反映（暫定 38 §10）

### 含まない（後送り）

- 暫定 38 §9 のとおり（テンキーのカンマ等・既存設定の自動移行・組み込みのキーボード表示・両方に反応する名前・記号の記録の既存の問題）

## このフェーズで読むファイル

1. `instructions/history/38_numpad_key_distinction.md`（全体）
2. `keyseq/application/input_router.py`（`_extract_key_name` :143-152）・`keyseq/application/key_state_manager.py`（:88-112）
3. `keyseq/domain/key_identifiers.py`・`keyseq/domain/config.py`（`normalize_key_name` :84-89）・`keyseq/presentation/keyboard_layouts.py`（:320-340）
4. `keyseq/infrastructure/input_gateway.py`（拡張キー :21-40・送信 :125-216・`key_identity` :228-247・`validate_key_name` :255-261）・`keyseq/domain/hotkey.py`・`keyseq/domain/key_hold.py`（`parse_key_hold`）
5. `keyseq/presentation/tk_keys.py`・`controllers/key_capture.py`・記録を使うダイアログ（`action_dialog.py` :369-410・`action_key_hold_fields.py`・`trigger_dialog.py`・`keymap_edit_dialog.py`・`keymap_switch_batch_dialog.py`）
6. keyboard ライブラリ（参照のみ）: `../../../.venv/Lib/site-packages/keyboard/_winkeyboard.py`（`keypad_keys` :442・`is_keypad` :528）
7. 正本: `instructions/common/spec_detail/key_input.md` §7.3・§7.7 / `data_schema.md` §5.11 / `features.md` §4.1・§4.2.12 / `codebase_map.md` のキーの送信の節

## タスク

- task_01: probe（ユーザーの実機・ホスト OS・テンキーのあるキーボード）— 送り方（`SendInput` のスキャンコード入力で NumLock オン / オフに 1 / End が入るか・`shift+num 1`）・Tk の keysym（テンキー各キー・NumLock オフ・Enter / `/`）・偽の shift のフックのイベント列。結果で暫定 38 §5・§6・§4 を確かめ、違えば改訂してユーザー確認
- task_02: domain の名前の表・入力の名前の関数（`input_router` / `key_state_manager` の両方・外部レイアウトの表の名前はテンキーだけ）・名前の検査（`num ` / `num_` の予約）とテスト（暫定 38 §3・§4・§6 の検査・§8 の 1〜5・7・7a）
- task_03: 送信（表の名前をスキャンコード + 拡張フラグで・hotkey の分岐）と `key_identity` とテスト（§5・§8 の 6）
- task_04: 記録（`tk_keys.py` の `KP_` の変換・probe の結果に従う）とテスト（§6・§8 の 8）。**実装後にユーザーの実機目視**（§8 の 10〜12）
- task_05: 統合確認（tests / tests_ui / smoke・deep-reviewer + codex-reviewer）
- task_06: 正本反映（暫定 38 §10 の昇格・凍結）・`decisions_archive/54_numpad_key_distinction.md`・decisions.md の索引・current.md の完了記載・idea_43 を INDEX_done へ・`/refactor_check`

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: **テンキーの入力が誤った名前になる経路が無いか**（`is_keypad` と表・`num lock` / 126 の除外・外部レイアウトの `id`・2 か所の名前の決定の一致・NumLock の切替をまたぐ押下状態）/
  suppress の判断と名前の一致 / 表の名前が keyboard の名前の API に渡らない / 送信が NumLock に従う / `num_` 等の予約 / 記号の出力は従来どおり / 既存テストの期待値の書き換えが §2-3 の範囲に収まる
- 統合確認（task_05）: `deep-reviewer` + `codex-reviewer` / 完了判定前（task_06）: `deep-reviewer` + `codex-adversarial-reviewer`
- 実機目視・probe（ユーザー・**ホスト OS**・テンキーのあるキーボード）: task_01・task_04
