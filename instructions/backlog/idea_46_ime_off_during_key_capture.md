# idea_46_ime_off_during_key_capture.md

## 概要

**キー入力で取得する間は IME を OFF にする**（取得を終えたら元の状態へ戻す）。IME が ON だと Tk にはどのキーも「IME が処理中のキー」（`VK_PROCESSKEY`・名前 `??`）で届き、押したキーを取得できない。
切替キー・トリガー・停止 / トグルキー・キーボードUI の編集など、取得のすべての入口が対象。

## 起票経緯（2026-10-16）

phase 59 task_04a の実機目視（ユーザー）から分離。IME が ON の状態で切替キーの取得をすると、入力が IME の変換に回り、Enter の後に IME OFF のときの値が入ったり、普通の数字キーが入らなかったりする（テンキーは IME を通らないので入る）。
phase 59 では切替キーの 2 つのダイアログで `??` を無視して案内の欄に理由を出す対応だけを入れた（暫定 43 v0.6 §3.5・task_04a / 04b）。

## 現状

* 取得は Tk の `<KeyPress>` と `presentation/tk_keys.normalize_tk_key_event` で名前を作る（`dialogs/keymap_edit_dialog.py`・`keymap_switch_batch_dialog.py`・`controllers/key_capture.py`・`keyboard_window.py` の編集 等）
* 切替キーの 2 つのダイアログだけ `??` を取得せず、案内の欄に「IME が ON の場合は OFF にしてから押してください」を出す（phase 59）。他の取得の入口は `??` をそのまま記録しうる
* IME の制御は `infrastructure/ime_control.py` に送信用（前面の窓の IME の開閉を一時的に変えて戻す）がある

## 提案（方向性・要設計）

* 取得の開始で、取得を受ける窓の IME を無効にする（例: `ImmAssociateContext(hwnd, NULL)` で入力コンテキストを外し、終了で戻す / または開閉の状態を記録して OFF → 終了で復元）。`ime_control.py` に取得用の口を足す
* 取得の終了の経路（取得できた・Esc・ボタン・窓を閉じる・例外）で必ず戻す
* 取得の入口を 1 つの共通の部品へ寄せるか、各入口から同じ口を呼ぶかは設計時に決める
* あわせて、他の取得の入口でも `??` を記録しないようにするか（phase 59 の切替キーと同じ扱い）を決める

## 想定スコープ

* 含む: すべての取得の入口での IME の一時的な無効化と復元・`??` の扱いの統一 / 影響レイヤ = presentation + infrastructure（IME の制御）
* 含まない: 送信時の IME の扱い（既存）/ IME の変換中の文字列を取得すること
* 仕様変更: `features.md`（キーの取得）・`key_input.md` に取得中の IME の規定を足す見込み
