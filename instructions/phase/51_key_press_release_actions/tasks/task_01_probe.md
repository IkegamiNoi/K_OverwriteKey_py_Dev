# task_01_probe

## 目的

実装の前に、暫定 35 §6 の 1〜3（合成の修飾キーを押したままのトリガー判定・text / 改行 / バックスペースへの影響・左右の ctrl / alt の押し離し）を実測し、結果で §4.4・§6 を見直す（違えばユーザー確認）。
コード不変（scratchpad の probe スクリプトのみ）。

## 対象範囲（probe のみ・コード不変）

- テスト用の Tk の Text を前面に出し、`keyseq.infrastructure.input_gateway.InputGateway` の `press_key` / `release_key` / `write_text` / `send_hotkey` で合成の入力を送り、
  `GetAsyncKeyState` で OS 上の押下状態・Text の中身・keyboard のフックで受けたイベント（名前・スキャンコード）を記録する
- アプリと同じく keyboard のフックが動いている状態と動いていない状態の両方で測る

## 読むファイル

- `instructions/history/35_key_press_release_actions.md` §4.3・§4.4・§6
- `keyseq/infrastructure/input_gateway.py:17-50, 85-131`・`keyseq/application/input_router.py:143-153`・`.venv/Lib/site-packages/keyboard/__init__.py:361-390, 783-871`

## 含まない

- 物理の押下での確認（task_06 の実機目視）

## 確認

- 結果（2026-10-10・メイン実測・ユーザー在席で実行）:
  1. 合成の shift を押したまま、合成の `a` / `1` → フックのイベントは名前 `A` / `!`・スキャンコード 30 / 2（不変）。判定はスキャンコードから引くのでトリガーとして判定される
  2. shift を押したまま text `ab\ncX\bd` → `ab\ncd`（文字は変わらず改行・バックスペースも効く）/ ctrl を押したまま `p\nq` → 改行だけ（文字は Ctrl+P / Ctrl+Q）/
     **フックが動いている状態で right ctrl を押したまま text を送ると、right ctrl を離しても left ctrl が OS 上に残る**（フックなしでは起きない。keyboard の `stash_state` / `restore_modifiers` が拡張キーで送った right ctrl を記録し、left ctrl として押し直すため）/ hotkey `right` では起きない
  3. left ctrl と right ctrl は別々に押し離しできる。`ctrl` で押して `left ctrl` で離すと離れる
- 反映: 暫定 35 v0.4（§4.4・§6・§2-14〜15・§10 の 7c）→ v0.4 の Codex 敵対的 needs-attention 3 件で v0.5（押下中のキーボードのキーすべてを送る間だけ離す・送信後に keyboard に修飾キーを押し直させない〔既存の不具合の修正〕・送信の失敗は押し直さず止めて離す）。ユーザー判断 2026-10-10
- probe の後に押下状態がすべて離れていることを確認済み
