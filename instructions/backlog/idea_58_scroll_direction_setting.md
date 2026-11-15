# idea_58_scroll_direction_setting.md

## 概要

**スクロールのアクションの向きを、利用者が入れ替えられる設定**を足す（縦・横それぞれ、または両方まとめて）。Mac では「ナチュラルなスクロール」で向きを入れ替えて使う人が多い。アプリが送るスクロールはこの OS の設定の影響を受けないため、手で回したホイールとアクションの向きが逆に感じられる。

## 起票経緯（2026-11-15）

phase 75 task_11a の Mac 実機目視（目視 3）でユーザーが要望した。task_11a では、横の符号の誤りだけを直す（向きの設定は扱わない）。

## 現状

- `keyseq/domain/mouse_scroll.py`: 向きは up / down / left / right。`scroll_deltas` の符号は、正が上・右。
- 送信: Windows は `windows/mouse_backend.py`（SendInput）、Mac は `macos/backend.py` の `MacMouseBackend.scroll_mouse`（`CGEventCreateScrollWheelEvent`）。
- 向きを入れ替える設定は無い。正本は `spec_detail/data_schema.md`（設定の JSON）と、アクションの仕様の節。

## 提案（方向性・要設計）

- 案 A: アプリの設定（グローバル）に「スクロールの向きを反転」（縦 / 横）を足す。backend の手前（application）で符号を反転する。
- 案 B: アクションごとに反転の指定を持つ（細かいが、編集の手間が増える）。
- 案 C: Mac では OS の設定（`com.apple.swipescrolldirection`）に自動で合わせ、手動の上書きも可能にする。
- 既定は今の向き（後方互換）。

## 想定スコープ

- 含む: 設定の JSON のキーの追加（後方互換・既定 = 反転なし）・設定画面の項目・文言（ja / en）・符号の反転・テスト。
- 含まない: OS の設定そのものの変更。
- 仕様変更あり（設定の JSON・UI）。
