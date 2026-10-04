# task_01a_call_all_flag

## 目的

暫定 31 v0.5 §3 に合わせて、呼び出しの種類の表し方を**「ステップが標準・一括は `all: true`」へ反転**する（task_01〜03a の実機目視でのユーザー判断 2026-10-04）。
**JSON のキーを `step` → `all`（意味は反転）、表示を `[call]`（ステップ）/ `[call all]`（一括）、チェックボックスを「一括で実行」（ON で一括・既定 OFF）へ。実行の挙動そのもの（ステップ・一括それぞれの動き）は変えない。**
`all` の無い既存の呼び出しの行はステップで動くようになる（ユーザー確定・受容）。

## 対象範囲

### `keyseq/domain/sequence_control.py`

- `is_step_call(action)` を **「種別が system・op が call・`not bool(action.get("all"))`」** に変える（`step` キーは見ない・無視）。一括の判定が要る箇所のために `is_all_call(action)`（= call かつ `bool(all)`）を足してよい
- 表示名: ステップ（`all` なし・偽）= **`[call] …`**、一括（`all` 真）= **`[call all] …`**（4 形とも同じ接頭辞の規則）

### `keyseq/application/call_context.py`・`sequence_runner/{call_wait,call_run_to_end}.py`

- 段の印・文脈の開始で `is_step_call` を使っている箇所は、判定関数の変更でそのまま反転する。`step` キーを直接読んでいる箇所が残っていれば `is_step_call` へ寄せる（直接の `.get("step")` を残さない）

### `keyseq/presentation/dialogs/action_control_fields.py`

- チェックボックスの文言を **「呼び出し先を一括で実行する（停止の行は読み飛ばす）」** にし、**ON = 一括**。既定 OFF（新規追加でも OFF）
- 読込: `bool(action.get("all"))` を反映 / 結果: **ON のときだけ `"all": True`** を含め、OFF なら `all` を書かない。`step` は書かない（既存の行に `step` があっても結果は新しく組み立てるので消える）

### テスト（追加・修正まで）

- **意味の反転への追随**: 呼び出しのテストで「キーなし = 一括」を前提にしていたもの（phase 40 以来の一括の呼び出しのテスト・task_02/03/03a の一括側のテスト）は **`all=True` を付ける**。
  ステップ側のテスト（`step=True` を付けていたもの）は**キーなし**にする。テストのヘルパー（`call(target, step=...)` 等）の引数も `all=` に変える。**期待値（送る順・間隔・履歴・一時停止）は変えない**（データの付け方だけを変える）
  - 対象: `tests/test_call_context.py`・`tests/test_sequence_runner_call.py`・`tests/test_sequence_control.py`・`tests/test_domain_config.py`・`tests_ui/test_action_dialog_control.py`・`tests_ui/test_sequence_copy_paste.py`・その他 `grep -rn "op.*call\|\"call\"" tests tests_ui` で見つかる呼び出しのテスト
- 表示名: `all` なし → `[call]` / `all: True` → `[call all]`（4 形）/ `step: True` だけの行はステップ（`step` は無視）
- ダイアログ: 新規追加で OFF / ON で確定すると `all: True` / OFF で `all` キーなし / 既存の `all: True` の行を開くと ON
- 複製・貼り付けで `all` が写る

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §3（v0.5）
- `keyseq/domain/sequence_control.py:150-201`
- `keyseq/presentation/dialogs/action_control_fields.py`（全体）
- `grep -rn "is_step_call\|\"step\"\|step=" keyseq tests tests_ui` の該当箇所

## 含まない

- 実行の挙動の変更（ステップ・一括それぞれの動きは task_02〜03a のまま）
- 表示の要約・枠（task_04 以降）/ 正本反映（task_07）
- 既存の構成セットのファイルの書き換え（読込時の移行はしない）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `grep -rn "\.get(\"step\")\|\"step\":" keyseq` が 0 件
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: 新しく足した呼び出しの行が `[call]` でステップに動く・「一括で実行」を ON にすると `[call all]` で丸ごと実行する・以前に作った呼び出しの行が `[call]`（ステップ）になっている。
