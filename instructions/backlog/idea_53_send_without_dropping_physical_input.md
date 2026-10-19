# idea_53_send_without_dropping_physical_input.md

## 概要

**アプリが送信している最中に届いた物理の入力が、アプリのフックに届かず OS へ素通りする**のを直す。
自分の送信だけを見分けて除き、物理の入力はいつでもフックで判定する。
直れば、押下だけのキー（無変換・変換）のリピートを戻せる（暫定 46 v0.4 でリピートなしにした理由の解消）。

## 起票経緯（2026-10-20）

phase 63 task_03 の実機目視の NG の計測（[暫定 46](../history/46_make_only_keys.md) §1「実機目視の NG の計測」）から分離。
リピートのたびに BackSpace を送ると、その最中に届いた無変換（`VK_IME_OFF`）の押下が OS へ素通りして IME が切り替わり、離しの 2 回組も崩れた。
phase 63 は送信を変えない範囲で「リピートなし」にして対処（ユーザー 2026-10-20）。

## 現状

- keyboard は送信の間 `_listener.is_replaying` を立て、その間のイベントを**物理の入力も含めて**フックへ渡さず通す（`.venv/Lib/site-packages/keyboard/__init__.py:233`・`:377-389`）
  - `keyboard.press` / `release` / `send` / `write` はライブラリの中で旗を立てる
  - アプリの拡張キー・走査コードの送信（`keyseq/infrastructure/input_gateway.py:141`・`:183`）も、自分の送信を拾わないように同じ旗を立てる
- アプリの送信ガード（`action_executor._send_guard_count`）の間も、`input_router.handle` は入力を素通しにする（`keyseq/application/input_router.py:89`）
- 正本は既存の性質として受容（`key_input.md` §7.7 の :170「記録に載らないごく短い間に届いた物理入力は keyboard のフックが拾わない」・:175 キーリピートで頻度が上がる）
- keyboard のイベントは `LLKHF_INJECTED` / `dwExtraInfo` を持たない（`_winkeyboard.py:531-548` で落とす）ので、フック側で自分の送信か見分けられない

## 提案（方向性・要設計）

- 案 A: 自分の送信を `SendInput` に統一し、`dwExtraInfo` に目印を付ける。keyboard の低レベルのハンドラを差し替えるか自前の低レベルフックを持ち、目印のあるイベントだけを除く
  - `is_replaying` と送信ガードの素通しをやめる（物理の入力は送信の最中でも判定する）
- 案 B: 送信の最中に届いた物理の入力を覚えておき、送信の後で判定し直す（OS へは通さない）。遅れが出る・順序が崩れ得る
- 共通の注意:
  - keyboard の押下の記録（`stash_state` / `restore_modifiers`）に載せない理由（phase 51 の右 ctrl が残る不具合）を壊さない
  - 送信のループ（送った置換先を自分で拾って再び置換する）を防ぐ
  - `keyboard.write`（text・file_line）の Unicode 送信（`VK_PACKET`）の扱い

## 想定スコープ

- 含む: 送信の全経路（hotkey・直接置換・key_hold・キーリピートの送り直し・text・file_line）・送信ガードの素通し・押下だけのキーのリピートの復活（暫定 46 v0.3 の §3.2 の「リピート」）
- 影響レイヤ: infrastructure（`input_gateway.py`）・application（`input_router.py`・`action_executor.py`・`make_only_keys.py`）・presentation（キーボードUI の色を緑へ戻す）
- 仕様変更あり: `key_input.md` §7.7 の受容を覆す。phase 51 / 52 の実機目視のやり直しが要る
- 含まない: Mac 対応
