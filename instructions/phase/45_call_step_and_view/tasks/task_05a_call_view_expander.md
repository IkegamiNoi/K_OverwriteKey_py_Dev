# task_05a_call_view_expander

## 目的

task_05 の実機目視でのユーザー判断（2026-10-05）により、フル表示の呼び出し先の表示枠を**常設の Expander** にし、境界線の主張を弱める（暫定 31 v0.6 §5.1 末尾・§5.2・§10-17・§10-18）。
**presentation 限定（`call_view_controller.py`・`call_view_frame.py`・`sequence_box.py`・選択の変化の配線）。application・JSON・config.json のキーは変えない。**
表示する中身の出どころ（runner の要約）は今の `CallViewSummary` のまま使い、参照による連動（§4.5）への切替は task_08 以降で行う。

## 対象範囲（presentation 限定）

### `keyseq/presentation/views/full_view/call_view_frame.py`

- 見出しを**クリックで開閉できる Expander の見出し**にする: 閉 = `▸ 呼び出し先`・開 = `▾ 呼び出し先　<経路>`（経路が無ければ `▾ 呼び出し先`）。見出しのクリック（`<Button-1>`）を外へ知らせる口（コールバック）を持つ
- 本体（一覧 + スクロールバー）を出し入れできる形にする（閉じているときは見出しの 1 行だけ）
- 一覧に「呼び出し中ではありません」を 1 行で出す口（読み取り専用のまま・`▶` なし）

### `keyseq/presentation/views/full_view/sequence_box.py`

- 境界線（`action_panes` の sash）を控えめにする: `sashrelief="flat"`・`sashwidth` を 3〜4 にし、背景を周囲より少しだけ違う色にする（出力シーケンス欄の複製・上へボタン程度の主張。ボタンより目立たない）
- **閉じているとき**: 見出しの 1 行を一覧の下に常に出す（PanedWindow の下の枠に見出しだけを入れ、境界線のドラッグは効かない〔高さ固定 = 見出しの要求高さ〕か、PanedWindow の外に見出しを置くかは実装者が選ぶ。どちらでも**閉じている間は境界線を出さない**こと）
- **開いているとき**: 今の task_05 と同じく境界線の下に枠（保存した高さ・最小 = 見出し + 3 行）
- ウィンドウの最小の高さ・横の 3 枠の幅の配分を変えない（閉じた状態の見出し 1 行ぶんは一覧が縮んで吸収する。一覧の最小 3 行は守る）

### `keyseq/presentation/controllers/call_view_controller.py`

- **開閉の状態をトリガーごとに持つ**: `dict[(trigger_set_id, key), bool]`（開いているか）と、手で操作したトリガーの集合。メモリ上だけ・保存しない。起動時・未使用のトリガーは閉
- 対象のトリガー S = トリガー一覧で選んでいるトリガー（`app.trigger_panel.selected_trigger_key()`）。S が無いときは閉じて見出しだけ
- `on_summary(summary)`: 要約を覚え、表示を描き直す。**自動で開く** = 要約の経路の先頭（呼び出し元のキー）が S と同じで、S が手で操作されていなければ S を開にする。**自動では閉じない**（None を受けても開閉を変えない）
- **表示する中身**: 開いていて、覚えている要約の経路に S が含まれるなら今の task_05 と同じ描画（`▶`・ループの色・カウンター）。含まれない / 要約が None なら「呼び出し中ではありません」
- 見出しのクリック: S の開閉を反転し、S を「手で操作した」にする
- **選択の変化**: 選んでいるトリガーが変わったら開閉と中身を描き直す口 `on_selection_changed()` を持ち、`trigger_panel_controller.py` の `refresh_actions` の末尾（トリガーの選択の変化で必ず通る所）から呼ぶ
- 境界線の高さの保存（`call_view_heights`）は今のまま。閉じた状態の見出しの高さは保存値に混ぜない

### テスト（追加・修正まで）

- `tests_ui/test_call_view_frame.py` を v0.6 に合わせて修正・追加:
  - 起動直後は見出しだけ（`▸`）で境界線が無い・一覧が残りを使う
  - 選んでいるトリガーが呼び出し元の要約を受けると開く / 手で閉じた後は要約を受けても開かない / None を受けても閉じない
  - 開閉がトリガーごと（f1 を開、f2 を選ぶと閉、f1 に戻すと開）
  - 選んでいるトリガーが経路に無い・要約が None なら「呼び出し中ではありません」
  - 見出しのクリックで開閉が反転する
  - 境界線の sash の relief が flat・幅が 3〜4
  - 既存の読み取り専用・高さの保存・最小の高さ・幅の配分の確認は残す（開いた状態で）

## 読むファイル

- 暫定 `instructions/history/31_call_step_and_view.md` §5.1・§5.2（v0.6）
- `keyseq/presentation/controllers/call_view_controller.py`（全体）
- `keyseq/presentation/views/full_view/call_view_frame.py`（全体）・`keyseq/presentation/views/full_view/sequence_box.py`（全体）
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:105-130`・`:248-300`（選択中のトリガー・`refresh_actions`）
- `tests_ui/test_call_view_frame.py`（全体）

## 含まない

- 参照による連動（§4.5）と、それに合わせた要約の問い合わせ方式（§5.3 v0.6）（task_08 以降）
- 省略表示の枠（task_06。本タスクの Expander と開閉の状態を使う）/ 正本反映（task_07）
- 開閉の保存・トリガーごとの高さ（スコープ外）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加・修正したテストが全 pass
- `-m unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass（tests_ui は verifier 1 つで）

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- **実機目視（本タスクで実施）**: ①起動時は一覧の下に `▸ 呼び出し先` の 1 行だけ ②ステップの呼び出しで止まると開き、終わっても閉じない（「呼び出し中ではありません」）③見出しのクリックで開閉でき、手で閉じたトリガーは次の呼び出しで勝手に開かない ④トリガーを切り替えると開閉がトリガーごと ⑤境界線が控えめ。
