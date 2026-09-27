# task_05_clear_cache_wiring

## 目的

**構成セットの読込等**（実行位置を消す契機）で file_line の読込キャッシュを全部捨てる配線をする（暫定 27 §6.2）。
その後、ユーザーの実機目視で、応答しないパスでも UI が止まらないこと・終了時に例外が出ないことを確かめる（暫定 27 §8-11）。
**application（`app_state.py` にリセット時の通知口）+ presentation（`app.py` の登録 1 行）・スキーマ不変**。

## 対象範囲（`app_state.py` / `presentation/app.py` とテストのみ）

### `keyseq/application/app_state.py`

- `AppState` に `reset_listeners: list[Callable[[], None]] = field(default_factory=list)` を追加する。
- `reset_indices()` の最後で、`reset_listeners` を登録順に呼ぶ（例外は握りつぶさない＝そのまま送出）。
  `reset_indices` は「実行位置を消す契機」（構成セットの読込等: `config_io/keymap_set_io.py` の 5 箇所・`trigger_set_file_io.py:264`）の共通の入口であるため、ここ 1 箇所で足りる。
- 既存の呼び出し元（presentation 側の 6 箇所）は**変更しない**。

### `keyseq/presentation/app.py`

- `self.state = AppState()` の後（loader の生成後であること）で `self.state.reset_listeners.append(self.file_line_loader.clear_cache)` を 1 回だけ登録する。
  loader の生成が state より後なら、生成順を入れ替えず登録位置を loader 生成の後にする。
- それ以外は変更しない。

### テスト

- `tests/` の AppState のテスト（既存の `reset_indices` を扱うテストファイルがあればそこへ・無ければ `tests/test_app_state_reset_listeners.py` を新規）:
  `reset_indices()` で登録した関数が登録順に 1 回ずつ呼ばれる / 未登録でも従来どおり動く。
- `tests/test_file_line_loader.py` は変更不要（`clear_cache` の挙動は task_02 で検証済み）。

## 読むファイル

- `instructions/history/27_file_line_async_read.md` §6.2（`:130-141` 付近）
- `keyseq/application/app_state.py:1-70`（`AppState` の定義と `reset_indices`）
- `keyseq/presentation/app.py:115-160`（executor・loader・state の生成順）
- `tests/` 内で `reset_indices` を呼んでいるテスト（`grep -rn "reset_indices" tests`）の 1 ファイルの冒頭のみ（書き方の手本）

## 含まない

- `reset_indices` の呼び出し元（`config_io/*`）の変更
- トリガー一覧の破棄・キーの変更・キーマップの切替でのキャッシュ破棄（暫定 §6.2 は「構成セットの読込等」のみ）
- codebase_map / 正本の更新（task_07）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- 追加テストが pass・`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` が全 pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass
- **実機目視（ユーザー）**: 下記の手順

### 実機目視の手順（ユーザー）

1. 通常のローカルファイル（数行）を file_line に指定し、カウンター +1 とループで回す。単発・連続実行とも従来どおり行が順に送られる
2. 実行中にそのファイルを書き換えて保存 → 次の実行から新しい内容が送られる（キャッシュの更新確認）
3. 応答しないパス（例: 存在しない PC の UNC `\\192.0.2.1\share\list.txt`、または切断したネットワークドライブ）を指定して実行 →
   **UI が固まらない**（ウィンドウの移動・一覧の操作ができる）、約 5 秒で「ファイルの読込が 5 秒以内に終わりませんでした」の通知
4. 3 の直後にもう一度同じトリガーを押す → 即座に「前回のファイル読込が終わっていません」（OS がまだ読込中の場合）。別のファイルの file_line は動く
5. 3 の読込中に停止トリガー / キーマップの一時停止 → すぐ止まる
6. 3 の読込中にアプリを終了 → 例外ダイアログやコンソールのエラーが出ない

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 通知口が汎用で最小か / 呼び出し元を変えていないか / 登録が 1 回だけ / 後続タスクの先取りなし）。
- 実機目視: **本タスクで実施**（ユーザー報告をもって完了）。
