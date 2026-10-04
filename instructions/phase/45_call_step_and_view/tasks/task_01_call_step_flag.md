# task_01_call_step_flag

## 目的

呼び出しの行に「ステップ」の印 `step` を足し、編集ダイアログで選べて一覧に `[call step]` と出るようにする（暫定 31 v0.4 §3・§10-1）。
**実行の挙動はこのタスクでは変えない**（`step` を読む実行は task_02・03）。domain の表示名 + presentation の編集ダイアログ。スキーマは呼び出しの行に任意の bool を足すだけ（後方互換）。

## 対象範囲

### `keyseq/domain/sequence_control.py`（`format_control_value` の呼び出しの表示名・`:171-182`）

- `bool(action.get("step"))` が真なら接頭辞を `[call step]` にする（`[call step] f5（ラベル）` / `[call step] f5（参照先なし）` / `[call step] （呼び出し先なし）` / `[call step] f5`）。偽・無しは現行の `[call]` のまま
- 判定用の小さな純関数を同ファイルか `domain/call_graph.py` に置く（例 `is_step_call(action) -> bool` = 種別が system・op が call・`bool(step)`）。task_02 以降も使う

### `keyseq/presentation/dialogs/action_control_fields.py`

- system の入力欄に、呼び出しを選んだときだけ出るチェックボックス **「呼び出し先の中も 1 回ずつ進める（ステップ）」**（既定 OFF）を足す（呼び出し先・注記と同じく `_show` で出し分け）
- 既存の行を開いたとき（`:201` 付近の読込）: `bool(action.get("step"))` を反映
- 結果（`_build_call_result`・`:280`）: **ON のときだけ `"step": True` を含める**。OFF なら `step` を書かない（既存の `false` も消える = 暫定 31 §3.1）

### 読込・保存・複製

- `domain/config.py` の `normalize_actions` は変えない（未知の項目を保持・読込時に正規化しない = §3.1）。テストで「`step` が保持される・型不正でも読込で書き換えない」を固定する
- 複製・貼り付け（phase 43）は行の深い写しなので `step` も写る。テストで固定する

### テスト（追加・修正まで）

- `tests/`（`sequence_control` のテストに倣う）: 表示名が `step` の真偽で `[call step]` / `[call]` に分かれる（4 形すべて）/ `step` が文字列 `"x"` 等の真の値でもステップ表示（`bool()`）
- `tests/`（config のテスト）: `normalize_actions` が `step` を保持し、型を変えない
- `tests_ui/`（ActionDialog の呼び出しのテストに倣う）: チェックボックスは呼び出しのときだけ出る / ON で確定すると `step: True` / OFF で確定すると `step` キーが無い / 既存の `step: True` の行を開くと ON
- `tests_ui/`（phase 43 の出力シーケンスの複製のテスト）: `step` を持つ呼び出しの行を Ctrl+C / V すると写しも `step` を持つ

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §3
- `keyseq/domain/sequence_control.py:150-201`
- `keyseq/presentation/dialogs/action_control_fields.py`（全体）
- `keyseq/domain/config.py:140-160`
- 手本のテスト: `grep -rln "\[call\]" tests tests_ui` で見つかる呼び出しの表示名・ダイアログのテスト

## 含まない

- ステップの実行（task_02・03）/ 表示枠（task_04〜06）/ 正本反映（task_07）
- `features.md` §4.6 の一覧の表示形式の追記（task_07）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加・修正したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: 呼び出しの編集ダイアログにステップのチェックボックスが出て、ON で保存すると一覧が `[call step] …` になる。OFF に戻すと `[call] …` に戻る。
