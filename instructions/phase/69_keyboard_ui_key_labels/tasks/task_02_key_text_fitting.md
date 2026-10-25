# task_02_key_text_fitting

## 目的

キーボードUIの各キーの文字を、キーの内側に収まる大きさまで縮めて描き、`\n` 以外では折り返さない（暫定 52 §3）。
キー置換の枠の文字（送信先のキー名）は、レイアウトの表 `key_display_names` に名前があればその値で出す（§4.2）。
**presentation のキーボードUIの描画に限定。レイアウトの読込（task_01 で済）・最小サイズ（task_03）・幅の記録（task_04）は変えない。スキーマ不変。**

## 対象範囲（キーボードUIの描画・新規の純関数モジュール・tests 限定）

### 新規 `keyseq/presentation/keyboard_key_text.py`（Tk 非依存の純関数）

- 文字合わせの計算を描画から分ける。計測は関数を引数で受け取る（Tk のフォントを直接持たない）:
  - `fit_key_text(main: str, sub: str, inner_w: float, inner_h: float, unit: float, measure: Callable[[str, int, bool], tuple[int, int]]) -> KeyTextFit`
    - `measure(text_line, px_size, bold)` は 1 行の (幅, 行の高さ) を返す（呼び出し側が `tkfont.Font(size=-px)` の `measure` / `metrics("linespace")` で作る）
    - `KeyTextFit` = 主の大きさ px・下の大きさ px・主の行の list・下の行の list（frozen dataclass）
  - 規則（§3）:
    - 行は `\n` でだけ分ける（空の文字は行 0）
    - 上限 px: 下の文字が無いとき 主 = `unit × 0.37`。下の文字があるとき 主 = `unit × 0.27`・下 = `unit × 0.19`。整数 px（切り捨て）
    - 下限 px: 主 7・下 6。**下限は上限より優先**（上限が下限を割れば下限）
    - 主を上限から 1px ずつ下げ、下は `主 × 0.19 / 0.27` を整数（切り捨て）にしたうえで下限で止める。各候補で、丸めと下限を当てた大きさで測り直し、
      「いちばん長い行の幅 ≤ `inner_w`」かつ「主と下の行の高さの合計 ≤ `inner_h`」を満たす最初（最大）の候補を採る
    - 主が下限に達しても収まらなければ、主 = 下限・下 = `max(下限, 比例値)` で出す（はみ出しは受容）
  - 同じ入力（文字・内側の大きさ・unit）の結果を使い回すための小さな辞書のキャッシュを持ってよい（描き直しごとに全キーを測るため。持つなら上限の数を決める）

### `keyseq/presentation/keyboard_window.py`

- `redraw`（`:357-433` 付近）:
  - キーの内側 = 枠（`x1`〜`x2`・`y1`〜`y2`）から左右・上下 1px ずつ引いた範囲
  - `fit_key_text` で大きさと行を決め、主と下の行を上から積んだ塊をキーの内側の縦の中央に置く（各行は横の中央）。
    実装は「主の文字」「下の文字」をそれぞれ 1 つの `create_text`（行を `\n` で連結・`justify="center"`）で描いてよい。**`create_text` に `width` を渡さない**
  - フォントは `(family, -px, "bold")`（主）/ `(family, -px)`（下）の負の値（px 指定）。family は今と同じ `TkDefaultFont` の family
  - 今の係数（0.20 / 0.22 / 0.28・0.14）・固定のずらし（`unit × 0.12`・`y2 − max(8, unit × 0.18)`）・`width=max(10, (x2 - x1) - 8)` を除く
  - `measure` は `tkfont.Font` をフォントの (px, bold) ごとに作って使い回す（描き直しごとに作り直さない）
- `update_from_config`（`:142-206` 付近）のキー置換の枠（`display_map[source] = target`・`:178`）: 表示する文字を `self._layout.key_display_name(target) or target` にする（§4.2）。
  トリガー・`KM<n>`・`MODE`・`STOP`・割り当ての無い枠（`label`）は変えない
  - レイアウトの切替（`update_layout`）後も今のレイアウトの表で出ること（`update_layout` の後に表示の対応が作り直されるか確認し、されないなら描画時に引く形にする）

### tests

- 新規 `tests/test_keyboard_key_text.py`（純関数）: 偽の `measure`（例: 幅 = 文字数 × px × 0.6・高さ = px × 1.3）で
  - 上限で収まるときは上限 / 収まらないと縮む / 下限で止まりはみ出しを受容
  - unit 27 で下の文字ありのとき 主 ≥ 7・下 ≥ 6（§9-6b）
  - `\n` でだけ行に分かれる・`\n` が無ければ 1 行
  - 2 行の高さで縮む（幅は収まるが高さで縮むケース）
- tests_ui（既存のキーボードUIのテストにならう・App を作るなら実 `config/` を汚さない既存の手法）:
  - 描いた text の item の `width` オプションが 0（未指定）・フォントの大きさが負の値
  - jis.json を使い、キー置換の送信先が `zenkaku_hankaku` のとき枠の文字が `半角\n全角` / 表に無い送信先はキー名のまま
  - 最小の大きさ相当（unit ≒ 27）で `Home` 等の 4〜5 文字のキーが 1 行で描かれる

### 設計メモ / 制約

- 計測の関数を注入して純関数をテストする（tests で Tk を使わない）
- 0.37 / 0.27 / 0.19 / 7 / 6 / 1px は暫定 52 §2-6・§3 の確定値。定数としてモジュールの先頭にまとめる
- 普通の大きさの窓で 5 文字以上の文字が今より大きくなるのは仕様どおり（§3・受容）

## 読むファイル

- `keyseq/presentation/keyboard_window.py`（編集対象・`:142-206`・`:357-433` を中心に）
- `keyseq/presentation/keyboard_layouts.py:22-35`（task_01 の `KeyboardLayout.key_display_name`）
- `instructions/history/52_keyboard_ui_key_labels.md` §2・§3・§4.2
- 既存のキーボードUIの tests_ui（`tests_ui/` で `KeyboardWindow` を作るテストを `grep` して 1 つ手本にする）

## 含まない

- 最小サイズ・レイアウトの切替の当て直し（task_03）
- 幅の記録（task_04）
- タイトル（編集中のキー名）等、キーボードUI以外のキー名の表示（暫定 52 §10）
- 正本の更新（task_06）

## 確認

- compileall clean
- `tests.test_keyboard_key_text` pass・追加した tests_ui の単体 pass
- tests 全体 / tests_ui 全体（同時に 1 本だけ）/ smoke pass・件数が減らない
- 実行後に `config/config.json` の mtime が変わっていない・worktree ルートに `user/` 等が生成されていない

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_06 でまとめて実施
