# task_05_trigger_effective_row

## 目的

同じトリガー一覧に同じキーの行が複数あるとき、一番上の行を有効とし、下の行をグレー表示（「上のトリガーと重複」）にする規則を入れる
（暫定 30 §5.1 冒頭・§5.2）。重複を作る操作（貼り付け・並べ替え）はまだ無いため、テストはデータへ重複を直接入れて確かめる。
**domain（重複判定の純関数・新規）+ presentation（一覧の表示・キー変更・呼び出しのドロップダウン）。application は確認とテストのみ（入力判定・呼び出しの解決は既に先頭一致）。スキーマ不変。**
有効な行の交代と進行中の拒否・グレーの行を選んだときの表示は task_05a。

## 対象範囲

### `keyseq/domain/trigger_duplicates.py`（新規・tkinter 非依存）

- `shadowed_duplicate_indices(triggers: Sequence[Any]) -> frozenset[int]`: キー（`normalize_key_name`）が空でなく、それより上の行に同じキーがある行の位置の集合（dict でない要素は数えない）
- `effective_trigger_index(triggers: Sequence[Any], key: str) -> int | None`: そのキーの一番上の行の位置（無ければ None）
- `is_effective_trigger(triggers: Sequence[Any], index: int) -> bool`: その行が有効な行か（キーが空の行は False）

### 一覧の表示（`keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py` の `refresh_triggers` 付近）

- 各行のグレー表示と理由: 現行のキー単位の重なり（停止 / トグル / 切替）があればそれを優先して表示（現行どおり・同じキーの全行に付く）。
  無く、行が `shadowed_duplicate_indices` に含まれれば、グレー表示＋理由「上のトリガーと重複」（§5.2 の優先順 停止 > トグル > 切替 > 上のトリガー）
- フル表示・省略表示の両方の一覧に付く（現行の `_trigger_lists` の仕組みのまま）

### キー変更（`rename_trigger`・§5.2）

- **キーが変わらない編集（ラベル等）では重複検査（`key_exists`）をしない**（現行は自分以外の同じキーの行に当たって拒否される）
- キーを変える場合の重複拒否は現行どおり
- 変えた行が**変更前のキーで有効な行ではなかった**（グレーだった）場合:
  - 実行中の状態（位置・周回・履歴など）を旧キーから新キーへ**移さない**（状態は有効な行のもの）
  - 同じ一覧の呼び出しの `target` を**書き換えない**
- 有効な行のキーを変えた場合は現行どおり（状態を移す・呼び出しを書き換える）。そのとき旧キーに下の行が残るケースの扱いは task_05a

### 呼び出しのドロップダウン（`keyseq/presentation/controllers/trigger_panel/action_edit.py` の `_call_dialog_options`・§5.2）

- 候補から重複でグレーになった行（`shadowed_duplicate_indices`）を除く。停止 / トグル / 切替との重なりでグレーの行は現行どおり出す
- 呼び出し先の解決（`find_trigger`）は現行どおり先頭一致（= 有効な行）

### 入力判定・呼び出しの実行・キーボード表示（application / presentation・**確認とテストのみ**）

- 現行の先頭一致（`trigger_service.find_trigger_by_key`・`input_router.py:120-123`・`keyboard_window.py:100-107`・呼び出しの解決）が有効な行の規則と同じ結果になることをテストで固定する。
  上の行のアクションが空なら、そのキーはトリガーとして無いもの（下の行も実行しない）= `key_input.md` §7.3（§5.1 末尾）もテストで固定する
- コードの変更が必要と分かった場合は最小の修正にとどめ、完了報告で理由を示す

### テスト

- `tests/test_trigger_duplicates.py`（新規）: 3 関数（空キー・dict でない要素・3 行以上の重複・大文字小文字の正規化）
- `tests/`（application）: 重複キーのデータで入力判定が上の行のトリガーを返す / 上の行が空なら置換へ落ちる / 呼び出しの解決が上の行（既存のテストファイルへ追記または新規）
- `tests_ui/`（新規 `tests_ui/test_trigger_effective_row.py`）: 重複の下の行がグレー＋「上のトリガーと重複」・停止キーとの重なりが優先 /
  キーを変えずにグレーの行のラベルを変えられる / グレーの行のキー変更で状態が移らず呼び出しが書き換わらない / 有効な行のキー変更は現行どおり /
  呼び出しのドロップダウンに重複のグレー行が出ない / キーボード表示に上の行の番号が出る

### 設計メモ / 制約

- presentation に `"triggers"` 直値を書かない（`domain/keymap_triggers.py` の口を使う・`tests/test_keymap_triggers.py` の静的検査）
- `trigger_panel_controller.py` は大きい（約 626 行）。新しい判定は domain の関数を呼ぶ形にし、controller に足すのは最小限

## 読むファイル

- 暫定仕様 §5.1・§5.2
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:90-180`（選択・`refresh_triggers`・理由の文言）・`:465-530`（`rename_trigger`）
- `keyseq/presentation/controllers/trigger_panel/action_edit.py:340-360`（`_call_dialog_options`）
- `keyseq/application/trigger_service.py:1-40`・`keyseq/application/input_router.py:90-135`・`keyseq/presentation/keyboard_window.py:90-110`
- `keyseq/application/key_overlap.py:1-60`（重なりの表の形）
- 既存テストの流儀: `tests_ui/test_trigger_panel_controller_action_edit.py:1-60`

## 含まない

- 有効な行の交代の判定・状態の破棄・進行中の拒否・削除時の扱い・グレーの行を選んだときのシーケンス欄（`▶` を出さない等）（task_05a）
- 保存の識別子（task_06）/ 重複を作る操作（貼り付け・並べ替え。task_07）/ 正本の更新（task_09）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest tests.test_trigger_duplicates tests_ui.test_trigger_effective_row` と追記した application のテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（task_05a と合わせた完了判定前に deep-reviewer + Codex レビュー = phase.md レビュー方針）。
- 実機目視は task_07（重複を作る操作ができてから）でまとめて実施。
