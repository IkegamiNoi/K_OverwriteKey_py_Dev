# task_11d_action_list_tags

## 目的

出力シーケンスの一覧の行頭の印を、全言語共通の英語の短い名前に統一する（暫定 55 v0.7 §8 Q6・ユーザー判断 2026-11-04）。

## 対象範囲

| 種類 | 今（ja / en） | 後（全言語共通） |
|---|---|---|
| hotkey / text | `[hotkey]` / `[text]` | 変えない |
| mouse_click | `[mouse_click]` | **`[click]`** |
| mouse_scroll | `[スクロール]` / `[Scroll]`（解釈できない行は `[mouse_scroll]`） | **`[scroll]`**（解釈できない行も） |
| key_hold | `[押す]` `[離す]` / `[Press]` `[Release]` | **`[press]` / `[release]`** |
| file_line・制御（`[loop]` 等） | 内部名・英語の印 | 変えない |

- 行頭の印は**言語ファイルに置かない**（コードの定数。訳さない）。印の後ろの値（スクロールの向き・`（生）`・`（リピート）`・
  マウスのボタン名・キー名）は今のまま `tr` で訳す。
- 直す場所:
  - `keyseq/domain/config.py` の `format_action_list_item`（`[{action_type}]` を印の表へ。mouse_click → `click`・それ以外の種類は今の内部名のまま。未知の種類も今のまま `[{action_type}]`）
  - `keyseq/domain/mouse_scroll.py` の `format_mouse_scroll_value`（印 `[scroll]` をコード側で付け、`domain.mouse_scroll.display_value` / `_raw` の値から印を外す: ja `{direction}{amount}` / `{direction}{amount}（生）`・en `{direction}{amount}` / `{direction}{amount} (Raw)`）
  - `keyseq/domain/key_hold.py` の `format_key_hold_value`（`[press]` / `[release]` をコード側で付け、`domain.key_hold.display.key` / `key_repeat` / `button` の値から `[{direction}] ` を外す。
    `domain.key_hold.display.down` / `up` が一覧の表示にしか使われていなければ、使われなくなるので削除する〔`grep -rn` で確かめる〕。解釈できない行の `[key_hold]` は変えない）
  - `keyseq/presentation/controllers/action_list_rendering.py`（省略表示の要約。mouse_click を自前で組んでいる 73 行目付近も `[click]` に。
    一覧と同じ印にするため domain の印の表を使う。実装中に判明・メインが追加 2026-11-04）
- 印の表は 1 か所にまとめてよい（domain 内。過剰な共通化はしない）。
- 一覧の文字を比べているテスト（`tests/`・`tests_ui/`。`grep -rn "\[スクロール\]\|\[押す\]\|\[離す\]\|\[mouse_click\]\|\[mouse_scroll\]\|\[Scroll\]\|\[Press\]\|\[Release\]"` 等で探す）を新しい印へ合わせる。
- テスト追加: 種類ごとの印（ja と en の両方で同じ印になること・印の後ろの値は言語で変わること）。

## 含まない

- 保存する `type` 等の内部名 / アクションの編集の「種類」のコンボボックスの表示名（Q6 (a)）/ ヘルプ本文（印を引用していれば報告だけする）/ 正本の改訂（task_12）

## 読むファイル

1. 本書・暫定 55 §8 Q6（`instructions/history/55_multilingual_ui.md`）
2. `keyseq/domain/config.py`（`format_action_list_item`）・`keyseq/domain/mouse_scroll.py`・`keyseq/domain/key_hold.py`
3. ja.json / en.json の `domain.mouse_scroll.display_*`・`domain.key_hold.display.*`
4. 該当するテスト（上の grep）

## 確認（verifier）

- compileall clean / tests 全件 / tests_ui 全件（単独実行）/ smoke
