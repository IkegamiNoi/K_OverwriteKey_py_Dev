# task_08_en_catalog

## 目的

`en.json` に `ja.json` の全キーの英訳を入れ、アクションの種類とマウスのボタンの表示名を結線する（暫定 55 §3.1・§6.1・§6.3・
§8 Q4〜Q6〔v0.4 確定〕）。カタログの完全性の検査（en が ja の全キーを持つ）を戻す。**shared/i18n の locales・presentation の表示名の結線・
domain の一覧の表示 1 か所・テスト。保存される JSON の値は不変・JSON スキーマ不変**。

## 対象範囲

### `keyseq/shared/i18n/locales/en.json`

- `ja.json` の**全キー**（約 905）の英訳を入れる。`_meta.name` = `English`（既存）。並びは `ja.json` と同じ順。2 スペースの字下げ・UTF-8。
- 訳は暫定 55 §8 の **Q4（表記の規則 E1〜E6）と Q5（用語表の英語）に従う**。主な規則:
  - 大文字は文頭だけ（メニュー・ボタン・窓のタイトルも）。`/` で並べた語はそれぞれ先頭を大文字（`Press / Release`）。固有名・略語は元の形
  - 「…」の有無は ja の値と同じにする（ja に「…」があれば en にも付ける・無ければ付けない。`Import...` / `Export...` は ja どおり）
  - ラベル・ボタン・見出しは句点なし。文のメッセージは「.」で終える。`Please` を付けない
  - 数は「名詞: {n}」の形（ja が `{n}件` 等でも、en は単数 / 複数の書き分けが要らない形にする）
  - 用語は Q5 の表（構成セット = Profile / キーマップ = Keymap / キー置換 = Key remap / 出力シーケンス = Output sequence /
    トリガーセット = Trigger set / 退避 = Archive / カーソルグリッド = Cursor grid / 簡易表示 = Compact view / 詳細表示 = Full view 等）
- **差し込みの名前は ja と完全に同じ集合**にする（`{name}`・`{key!r}` の `!r` も含めて）。改行の数は文の意味が変わらない範囲で ja に合わせる。
- ja が英字のままの値（`OK`・`UTF-8`・`[call]` 等の記号的な表記・キーの名前）は同じ値にする。
- `menu.settings.language` = `Language / 言語`（暫定 55 §4.3・task_01 で入れ済み。変えない）。

### アクションの種類の表示名（Q6 (a)）

- `keyseq/shared/i18n/locales/ja.json` / `en.json` に `action.type.<内部名>` を足す（7 つ）:
  `hotkey` = ホットキー / Hotkey・`text` = 文字入力 / Type text・`mouse_click` = マウスのクリック / Mouse click・
  `mouse_scroll` = マウスのスクロール / Mouse scroll・`key_hold` = 押下・解放 / Press / Release・`system` = 制御 / Control・`file_line` = ファイルの行 / File line。
- `keyseq/presentation/dialogs/action_dialog.py` の種類の Combobox（56〜57 行・163・169・195・382・467・557・559 行付近の `type_var` の読み書き）:
  task_02 の形（呼び出し時に作るコード → ラベルの表・インスタンスが持つ逆引き・判定はコード）にし、`values` は表示名、
  内部では内部名で判定・保存する。読み込んだ action の種類が表に無い値なら、その値をそのまま表示して保存も変えない。

### マウスのボタンの表示名（Q6 (c)）

- `action_dialog.py:118` の mouse_click のボタンの Combobox（`left` / `right` / `middle`）を同じ形で表示名に（キーは既存の
  `action_dialog.key_hold.button.*`〔左 / 中 / 右〕を使い回してよい）。保存値は `left` / `right` / `middle` のまま。
- `keyseq/domain/config.py:463-466` の一覧の mouse_click の `{button}`: 表示の時点で表示名にする（`left` → 左 / Left）。
  表に無い値はそのまま出す。domain は `keyseq.shared.i18n` の `tr` を使ってよい（task_06 と同じ）。キーは domain 用に `domain.config.mouse_button.<値>` を足す。
  **これにより日本語の一覧の見た目が変わる**（`(10, 20) left x1` → `(10, 20) 左 x1`。暫定 55 §8 Q6 で確定した変更）。
  それを assert している既存テストは新しい表示へ直す（この変更に限る）。
- 一覧の行頭の `[hotkey]` 等（`domain/config.py:476-478`）は内部名のまま（Q6 (b)）。

### `tests/test_i18n.py`

- 移行中の検査（en ⊆ ja）を、**en が ja の全キーを持ち、ja が en の全キーを持ち、全キーで差し込みの名前の集合が一致する**検査へ戻す。
- 追加: en の値が空文字でない / en の値に日本語の文字（ひらがな・カタカナ・漢字）を含まない（`menu.settings.language` 等、意図して日本語を
  含むキーはテスト内の許可リストに書く）/ ja の値に「…」があるキーは en にも「…」がある（逆も）。

### テスト（表示名）

- 種類の Combobox: 表示名が出る・選ぶと内部名で保存される・既存の action を開くと表示名で出る・表に無い種類はそのまま（`fix_language("ja")` と
  `tr` を英語風に差し替えた場合の両方）。
- mouse_click のボタン: Combobox の表示名と保存値・一覧の表示（ja / en）。

## 設計メモ / 制約

- ja の文言は、Q6 で確定した 2 か所（種類の Combobox・mouse_click のボタンの表示）以外は変えない。
- 英訳の確認はユーザーが実機で行う（task_12）。本 task では規則と用語に従った訳を入れる。
- 表示名の表をモジュール定数に入れない（呼び出し時に `tr`）。

## 読むファイル

1. `instructions/history/55_multilingual_ui.md` §8（Q4〜Q6）・§3.1
2. `keyseq/shared/i18n/locales/ja.json`（全体）・`en.json`
3. `keyseq/presentation/dialogs/action_dialog.py`（種類とボタンの Combobox の周辺）・`keyseq/domain/config.py:430-480`
4. `tests/test_i18n.py`・種類 / ボタンの表示を assert しているテスト（`grep` で `mouse_click` の一覧の表示・`type_var` を探して該当箇所だけ）

## 含まない

- `help_en.json`（task_09）/ 日本語リテラルの静的検査（task_10）/ 正本の改訂（task_12）/ 一覧の行頭 `[hotkey]` の表示名化（Q6 で不採用）

## 確認

- `tests/test_i18n.py`: ja と en のキー集合が一致・差し込み名の一致・en に日本語なし（許可リスト以外）・「…」の対応
- 種類 / ボタンの表示名のテスト・既存テスト全 pass（`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui`）・
  `-m compileall keyseq` clean・`-m tests.smoke_app` OK

## 完了条件

- 上記確認 pass・**reviewer 採用**（訳の規則〔E1〜E6〕・用語〔Q5〕の遵守を抜き取りで確認）。
- 英語の実機目視は task_12。
