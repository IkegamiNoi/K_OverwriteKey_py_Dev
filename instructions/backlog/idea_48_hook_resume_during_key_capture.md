# idea_48_hook_resume_during_key_capture.md

## 概要

**キーの取得中にフック開始ボタンでフックを再開できてしまう**のを防ぐ。メイン窓の停止 / トグルキーの取得中や、非モーダルのキーボードUI の編集中にフックを再開すると、取得のための打鍵がフックにも流れて実行・送信され得る。

## 起票経緯（2026-10-16）

暫定 44（phase 60・取得中の IME）の Codex 敵対的レビューの指摘から分離（暫定 44 §4.3・§2）。IME と独立した既存の穴のため、phase 60 のスコープ外とした。

## 現状

* フック開始ボタンは `hook.toggle_hook` を直接呼ぶ（`keyseq/presentation/views/full_view/hook_frame.py:21`）
* `start_hook` は取得・ダイアログによる一時停止の数（`hook_suspend_count`）を見ない（`controllers/hook_controller.py:120-145`）
* 取得中にボタンへ届くのは #1 停止 / トグルキーの取得（メイン窓）と #7 キーボードUI の編集（非モーダル）。モーダルのダイアログの取得は該当しない見込み（未確認）

## 提案（方向性・要設計）

* 一時停止中（`hook_suspend_count > 0`）はフック開始を受け付けない（ボタンの無効化 / `start_hook` で拒否）か、開始したら取得を終える、のどちらかを選ぶ
* 一時停止の数が 0 に戻ったときの「元の状態へ戻す」（`resume_hook_after_dialog`）との整合

## 想定スコープ

* 含む: 取得中のフック再開の扱い / 影響レイヤ = presentation（hook_controller・ボタン）
* 含まない: 取得中の IME（phase 60）
* 仕様変更: `features.md` §4.5（フックの開始・停止）または `key_input.md` §7.4 に規定を足す見込み
