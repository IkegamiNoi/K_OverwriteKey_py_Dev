# task_01_domain_foundation

## 目的

暫定仕様 26 の domain 側の土台を作る。後続タスク（runner・UI）が使う**純関数と定数**だけを用意する。
- §3: `system` / `file_line` の読込時の正規化（文字列キーの型不正の扱い）
- §5.1: ループの始まり・終わりの対応（括弧の対応）と深さ・対応崩れ・深さ超過の判定、位置を囲むループの列（§4.3 の判定用）
- §11.3: 一覧の表示名（runtime の値は**引数で受け取る**・§4.5）
- §11.4: 深さ → （色相・濃さ）の対応（色値そのものは task_07）

**domain 限定**。application / presentation は変更しない。既存の種別（hotkey / text / mouse_click）の正規化・表示結果は変えない。

## 対象範囲（domain 限定・新規モジュール 1 + 既存 1 ファイルの追記）

### `keyseq/domain/sequence_control.py`（新規）

- 定数: `ACTION_TYPE_SYSTEM = "system"` / `ACTION_TYPE_FILE_LINE = "file_line"` /
  op 名 7 種（`loop_start` / `loop_end` / `counter_inc` / `counter_reset` / `wait` / `back` / `rewind`）/
  `MAX_LOOP_DEPTH = 9` / 文字コード `utf-8` / `shift_jis` / 範囲外 `error` / `empty` / `wrap` と既定値（`utf-8` / `error`）。
- `action_type(action) -> str` / `system_op(action) -> str`: trim + 小文字化して返す（非文字列は `""`）。
- `LoopStructure`（frozen dataclass）と `analyze_loops(actions) -> LoopStructure`:
  - `pairs`: 始まりの添字 → 終わりの添字（対応が取れたものだけ）。逆引き（終わり → 始まり）も持つ。
  - `depth`: 各行の深さ（その行を囲む最も内側のループの深さ。**ループの行は自分のループの深さ**・ループの外は 0）。
  - `unmatched`: 対応の無い始まり・終わりの添字の集合。
  - `too_deep`: 深さが `MAX_LOOP_DEPTH` を超える始まりの添字の集合（その始まりと対の終わりの深さも計算上の値を入れてよい）。
  - 判定は `system` かつ op が `loop_start` / `loop_end` の行だけを対象にする（他の行は無視）。
  - 対応崩れがある場合の `depth`: 対応の取れたループだけで数える。**対応の無いループ行の深さは 0**（§11.4 の「崩れた行に色を付けない」ため）。
- `enclosing_loop_starts(structure, position) -> tuple[int, ...]`: `position` を囲む（対応の取れた）ループの始まりの添字を外側から順に返す。
  **終わりの行はそのループの内側・始まりの行は外側**として数える（§4.3）。`position` が範囲外（len 以上を含む）なら `()`。
- `loop_depth_style(depth) -> tuple[str, str] | None`: §11.4 の対応。1〜9 → `("blue"|"green"|"orange", "light"|"medium"|"dark")`、
  0・範囲外 → `None`。
- `format_control_value(action, *, loop_iteration=None, counters=None) -> str`: §11.3 の `[<表示名>] <値>` を返す
  （`loop_iteration` = 実行中の周回数〔実行中でなければ None〕/ `counters` = 名前 → 値の Mapping〔None は空扱い・未登録は 0〕）。
  - `loop_start`: 非実行中 `[loop] ×3` / 無限 `[loop] ×∞`、実行中 `[loop] 2/3` / `[loop] 2/∞`。`count` は表示のみなので**生値を文字列化**（不正値の検証はしない）。
    無限の判定は `bool(infinite)`。
  - `loop_end` → `[loop_end]` / `counter_inc` → `[count+1] n (=5)` / `counter_reset` → `[count=0] n (=5)` /
    `wait` → `[wait] 500ms`（生値）/ `back` → `[back]` / `rewind` → `[rewind]`。
  - op が空・未定義 → `[system] <op の生値の文字列>`（op が空なら `[system] `）。
  - `file_line` → `[file_line] <path のファイル名部分> #<counter> (=<値>)`（ファイル名は `/` と `\` の両方で区切る。path 空なら空）。

### `keyseq/domain/config.py`（追記）

- `normalize_actions`: 既存の `type` / `button` と同じ規則（**キーがあるときだけ** `coerce_label`）を
  `op` / `counter` / `path` / `encoding` / `out_of_range` にも適用する。`count` / `ms` / `infinite` には触らない（実行時に判定・§3.1）。
  種別を問わず適用してよい（該当キーを持つのは新種別だけのため）。
- `format_action_list_item(index, action, *, loop_iteration=None, counters=None)`: キーワード専用引数を追加し、
  種別が `system` / `file_line` のときは `sequence_control.format_control_value` の結果を `NN. ` の後ろに置き、ラベルがあれば `: <label>` を付ける。
  それ以外の種別は**現行の出力と完全に同じ**（既存の呼び出し元は引数を変えずに動く）。

### テスト

- `tests/test_sequence_control.py`（新規）: `analyze_loops`（単純 / ネスト / 兄弟 / 対応崩れ〔始まりだけ・終わりだけ・順序逆〕/ 深さ 9 と 10 /
  ループ以外の行の無視 / 大文字・前後空白の op）、`enclosing_loop_starts`（始まりの行・終わりの行・本体・ループ外・範囲外）、
  `loop_depth_style`（0〜10 の境界）、`format_control_value`（全 op・無限・実行中・counters 未指定と未登録・未定義 op・file_line のパス区切り両方）。
- `tests/test_domain_config.py`（追記）: `normalize_actions` の新キーの型不正（非文字列 → 空・キーが無ければ補わない・trim）、
  `format_action_list_item` の system / file_line 行とラベル付き、既存種別の出力が不変であること。

### 設計メモ / 制約

- `config.py` は 435 行で目安超過のため、新ロジックは `sequence_control.py` へ置き、`config.py` からは呼ぶだけにする。
- `sequence_control.py` は `config.py` を import しない（循環を避ける。`config.py` → `sequence_control.py` の一方向）。
- UI ライブラリ・application への依存を持ち込まない（純関数のみ）。

## 読むファイル

- `instructions/history/26_sequence_control_actions.md` §3・§4.3・§4.5・§5.1・§11.3・§11.4（仕様）
- `keyseq/domain/config.py`（編集対象。特に 87-90 `coerce_label` / 147-161 `normalize_actions` / 404-424 `format_action_list_item`）
- `tests/test_domain_config.py:39-80`（`NormalizeActionsTest` の手本）/ `:494-535`（`FormatListItemTest` の手本）

## 含まない

- 実行モデル（ステップ・周回スタック・カウンターの保持・エラー通知）→ task_02
- 待機 → task_03 / 戻す・先頭へ → task_04 / file_line の読込と送信 → task_05
- 編集ダイアログ・追加位置・移動規則 → task_06
- 一覧への runtime 値の受け渡し・色値（hex）と背景の適用・省略表示の要約 → task_07（本タスクは関数の口と対応表まで）
- 正本・codebase_map の更新 → task_08

## 確認

- 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` がエラー無し。
- 単体: `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sequence_control tests.test_domain_config -v` が全 pass。
- 退行: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass（既存の `format_action_list_item` / `normalize_actions` 利用箇所を含む）。
- `grep` で `keyseq/domain/sequence_control.py` に `tkinter` / `keyseq.application` / `keyseq.presentation` の import が無いこと。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は不要（UI 変更なし）。一覧表示の目視は task_07 でまとめて行う。
