# task_03_compact_pane_heights

## 目的

暫定 33 §2-2・§2-3・§2-5・§2-6・§2-8・§5・§6・§7 の実装: 省略表示の縦の PanedWindow（トリガー一覧 / シーケンス欄 / 呼び出し先の枠）の
**高さの配置・ドラッグ・保存を 1 か所へ集め**、シーケンス欄の開閉と希望の高さを `config.json` の `compact_sequence_view` に保存・読込する（初回は開く）。
**presentation 限定・domain / application 不変。`config.json` にキー `compact_sequence_view` を追加（後方互換）。フル表示の呼び出し先の枠の挙動は不変。**

## 対象範囲（presentation 限定）

### 新規 `keyseq/presentation/compact_pane_heights.py`（tkinter 非依存の純関数・`call_view_heights.py` と同じ置き場と作法）

- `COMPACT_SEQUENCE_VIEW_KEY = "compact_sequence_view"`
- `parse_compact_sequence_view(raw) -> tuple[bool, int | None]`: §7。dict でなければ (True, None)。`open` は bool のときだけ採用（それ以外・欠落は True）/ `height` は bool を除く int で 1 以上のときだけ採用（それ以外は None）。値ごとに判定
- `plan_compact_heights(...)`: 省略表示の 3 段の表示の高さを決める。入力 = 使える高さ（PanedWindow の高さ − 境界の数 × 境界の太さ）/ トリガー一覧のペインの最小と下限（シーケンス欄を閉じているときは見出し 1 行分を含む）/
  開いている欄ごとの (希望の高さ, 最小, 見出しの高さ)。出力 = シーケンス欄・呼び出し先の枠の表示の高さ（閉じていれば None）。規則（§2-5・§2-8）:
  1. 各欄はまず希望の高さ（最小未満なら最小へ引き上げ）
  2. トリガー一覧が最小を割るなら、**呼び出し先の枠 → シーケンス欄** の順に最小まで縮める
  3. まだ割るなら、トリガー一覧が最小を割って縮む（下限 = シーケンス欄を閉じていれば見出し 1 行分・開いていれば 0）
  4. それでも入らなければ **呼び出し先の枠 → シーケンス欄** の順に一覧の部分が最小を割って縮む（下限 = 各欄の見出しの高さ）。それも入らなければ見切れる（受容）
  - 保存値（希望の高さ）は変えない（表示だけ収める）
- 単体テスト（新規 `tests/test_compact_pane_heights.py`）: parse の正常・不正の組み合わせ / plan の規則 1〜4（収まる・呼び出し先から縮む・トリガー一覧が割る・見出しまで縮む）/ 片方だけ開いている場合

### 新規 `keyseq/presentation/controllers/compact_pane_layout.py` — `CompactPaneLayout`

- 省略表示の PanedWindow（`compact_view.trigger_box.trigger_panes`）の**配置・ドラッグ・保存の唯一の受け持ち**。`App` が持ち（`app.compact_pane_layout`）、`CallViewController` と `CompactSequenceController` から呼ばれる
- 配置: after_idle で `plan_compact_heights` の結果に従い境界を**上から順に** `sash_place` する（開いている欄の数で境界 0 / 1 の意味が変わる）。ドラッグ中は配置しない。各ペインの `minsize` も設定する
- 既定の希望の高さ（§5）: シーケンス欄・呼び出し先の枠とも **PanedWindow の高さの 3 分の 1**（呼び出し先の枠の既定は今の `default_call_view_height` と同じ基準）。省略表示の幅にした後・レイアウトが落ち着いた後に決める（今の呼び出し先の枠と同じタイミング）
- ドラッグ（§5）: 押したときに各欄（シーケンス欄・呼び出し先の枠）の実際の高さを覚え、離したときに**変わった欄だけ**その欄の希望の高さにする。変わったキー（`compact_sequence_view` / `call_view_heights`）だけを **1 回の `startup_io.write_startup`** で書く。
  `call_view_heights` の中身の規則（もう片方〔full〕の今の希望値も一緒に書く・未確定の側は書かない）は今の `_on_release` と同じ。`compact_sequence_view` は今の `open` と `height` を書く（`height` 未確定なら書かない）
- フォント変更（§5）: 省略表示のシーケンス欄の最小も測り直して配置し直す（`CallViewController.on_font_changed` の契機に乗せる）

### `keyseq/presentation/controllers/call_view_controller.py`

- `compact` ホストの高さの処理（`_apply_height`・`_on_press`・`_on_release`・最小の設定・`_ensure_desired` の compact 分）を `CompactPaneLayout` へ委ねる。呼び出し先の枠の希望の高さ（`desired["compact"]`）は引き続き `CallViewController` が持ってよいが、読み書きは `CompactPaneLayout` から行う
- `full` ホストの処理・呼び出し先の枠の描画・トリガーごとの開閉・自動で開く挙動は**変えない**
- `panes.add(frame.body, …)` は、シーケンス欄が開いているときもその下（最後）に入る形を保つ

### `keyseq/presentation/controllers/compact_sequence_controller.py`

- 起動時に `parse_compact_sequence_view(app._startup_settings.get(...))` で開閉と希望の高さを読む。**保存値が無ければ開いた状態**（§2-6）。開いた状態で省略表示を組み立てる
- 見出しのクリックで開閉したら `compact_sequence_view` を書く（今の `open` と、決まっていれば `height`）。配置は `CompactPaneLayout` に頼む
- task_02 の「既定は閉じる」はこのタスクで置き換える

### 既存テストの追随

- `tests_ui/test_call_view_compact.py`: シーケンス欄が既定で開くため、ペインの枚数・`sash_coord(0)`・既定の高さの前提が崩れるテストは、**setUp でシーケンス欄を閉じた状態に固定**して従来の期待を保つ（期待値そのものは変えない）。固定の方法はテスト側で行い、本体に試験用の分岐を足さない
- `tests_ui/test_compact_sequence_view.py`: 既定が開くことに合わせて追随し、次を追加: ①保存値なしで開く・`open: false` で閉じて始まる ②開閉で `compact_sequence_view` が書かれる ③境界を離すと変わった欄のキーだけ 1 回で書かれる ④開閉でウィンドウの大きさが変わらずトリガー一覧が伸び縮みする ⑤両方開いた低い窓で §2-8 の順に縮む（見出しが残る）

## 読むファイル

- `instructions/history/33_compact_sequence_view.md` §2・§5〜§7
- `keyseq/presentation/controllers/call_view_controller.py`（全体）・`presentation/call_view_heights.py`（全体）
- `keyseq/presentation/controllers/compact_sequence_controller.py`・`views/compact_view/sequence_frame.py`・`views/compact_view/trigger_box.py`（全体）
- `keyseq/presentation/controllers/config_io/startup_io.py:40-60`・`app.py:200-245`
- `tests_ui/test_call_view_compact.py`（全体）・`tests_ui/test_compact_sequence_view.py`（全体）

## 含まない

- 省略表示のウィンドウの大きさの保存・最小の高さ・ステータスの行数（task_04）
- フル表示の呼び出し先の枠の規則・見た目の変更（暫定 33 §11）
- 正本反映（task_06）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` clean
- `tests/test_compact_pane_heights.py`・`tests_ui/test_compact_sequence_view.py`・`tests_ui/test_call_view_compact.py`・`tests_ui/test_call_view_frame.py` pass
- tests・tests_ui 全体・`-m tests.smoke_app` pass。実 `config/` を汚さない

## 完了条件

- 上記確認 pass・**reviewer 採用**（重点: 配置の受け持ちが 1 か所か・フル表示の呼び出し先の枠が不変か・書き込みが 1 回にまとまるか）
- 実機目視: なし（task_05 でまとめて実施）
