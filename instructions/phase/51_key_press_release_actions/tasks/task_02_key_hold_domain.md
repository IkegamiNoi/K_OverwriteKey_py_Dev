# task_02_key_hold_domain

## 目的

種類 `key_hold` の domain 部品を作る: 種類・向き・ボタンの定数 / 行の検証（実行時エラーの判定）/ 一覧の書式（暫定 35 §3・§7 の書式）。
**domain 限定**（keyboard 等の外部ライブラリに依存しない）。application / infrastructure / presentation は不変（呼び出し側は task_03〜05）。JSON の読込の正規化は変えない（§3）。

## 対象範囲（domain 限定・新規 1 + 既存 1）

### 新規 `keyseq/domain/key_hold.py`
- 定数: `ACTION_TYPE_KEY_HOLD = "key_hold"` / `EDGE_DOWN = "down"` / `EDGE_UP = "up"` / `MOUSE_BUTTONS = ("left", "right", "middle")`
- `@dataclass(frozen=True) class KeyHoldSpec`: `edge: str`（"down" / "up"）/ `button: str | None`（マウスの行ならボタン名・キーボードなら None）/ `key: str | None`（キーボードの行なら trim + 小文字のキー名・マウスなら None）/ `position: tuple[int, int] | None`（マウスの座標・無ければ None）
- `parse_key_hold(action: Mapping[str, Any]) -> KeyHoldSpec | str`: 行を検証し、正しければ `KeyHoldSpec`、不正なら**利用者向けのエラー文言（日本語・1 行）**を返す。規則（暫定 35 §3）:
  - `edge` が文字列で trim + 小文字が `down` / `up` 以外・非文字列 → エラー
  - 判別: `button` が**空でない文字列**（trim 後）ならマウスの行、それ以外（キー無し・空・非文字列）ならキーボードの行
  - キーボード: `value` が文字列でない・trim 後に空・`+` か `,` を含む → エラー（キー名がキーボードとして実在するかの検査は infrastructure の `validate_key_name` で行うため**ここではしない**）
  - マウス: `button` の trim + 小文字が `MOUSE_BUTTONS` 以外 → エラー / `x` と `y` は**両方ある**ときだけ使い、`int()` で変換できなければエラー（`"100"`・`10.9` は受け入れる＝mouse_click の `x` / `y` と同じ）・**片方だけ**ならエラー。キーボードの行の `x` / `y` は無視
- `format_key_hold_value(action: Mapping[str, Any]) -> str`: 一覧の値の表示。`parse_key_hold` が成功なら `[押す] shift` / `[離す] shift` / `[押す] マウス左` / `[押す] マウス左 (100, 200)`（ボタン = 左 / 右 / 中）。
  失敗なら `[key_hold] <value または button の文字列表現>`（不正な行も一覧に出せるように）

### 既存 `keyseq/domain/config.py` の `format_action_list_item`
- `action_type == "key_hold"` の分岐を足し、`format_key_hold_value` の結果を使う。表示は `NN. [押す] shift`・ラベルがあれば `NN. [押す] shift: <label>`（**`[key_hold]` の型名は前に付けない**。制御アクションと同じく値の表示が種類を兼ねる）

### テスト（新規 `tests/test_key_hold.py`）
- `parse_key_hold`: キーボードの down / up・大文字や前後の空白の正規化・edge 不正 / 非文字列・value 空 / 非文字列 / `+` / `,`・マウスの 3 ボタン・不正ボタン・`button` が空文字や非文字列ならキーボード扱い・座標あり（`"100"`・`10.9`）・片方だけ・変換不能・キーボードの行の x / y は無視
- `format_key_hold_value` と `format_action_list_item` の表示（ラベルあり / なし・座標あり / なし・不正な行）

## 読むファイル

- `instructions/history/35_key_press_release_actions.md` §3・§7（一覧の書式）
- `keyseq/domain/sequence_control.py:1-45`（定数と `action_type` の作法）
- `keyseq/domain/config.py:418-460`（`format_action_list_item`）
- `instructions/common/spec_detail/data_schema.md` §5.11.2（mouse_click の x / y の変換規則）

## 含まない

- 送信・押下中の集合・ActionExecutor（task_03）/ 自動で離す入口（task_04）/ ダイアログ・省略表示の要約・ステータス（task_05）
- キー名の実在の検査（infrastructure・task_03）
- 正本の改訂（task_07）

## 確認

- 上記テストの追加（実行は verifier: `unittest discover -s tests`）
- domain が keyboard / pyautogui / tkinter を import していないこと
- reviewer（5 観点）
