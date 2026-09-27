# task_02_load_registry_and_cache

## 目的

file_line の読込をワーカースレッドで行うための**読込の登録簿とキャッシュ**を、application の新規モジュールとして作る（暫定 27 §6.1・§6.2・§3.2 の判定順・§5 の上限）。
runner（task_03・04）はこの口を使って、読込を始め、確認タイマーごとに結果を問い合わせる。
**application 限定・新規モジュール + 単体テストのみ・既存ファイルは変更しない・Tk を使わない・スキーマ不変**。

## 対象範囲（application 限定・新規 2 ファイルのみ）

### `keyseq/application/file_line_loader.py`（新規）

公開する型と関数（名前は下記に合わせる）:

- `FILE_LINE_LOAD_TIMEOUT_SECONDS = 5.0`
- `file_line_load_key(path: str, encoding: str) -> tuple[str, str]`: `(os.path.normcase(os.path.normpath(path)), encoding)`（暫定 §6.1）。
- `class FileLineLoadRequest`: 1 回の file_line 実行の読込要求（runner が保留に持つ）。少なくとも `key` / `path` / `encoding` / `started_at`（単調時計）/
  自分が起動したワーカーの仕事（未起動なら None）を持つ。runner からは不透明な札として扱い、中身を触らせない。
- `class FileLinePoll`: 問い合わせの結果。`status` が `"pending"` / `"done"` / `"error"` のいずれか。`"done"` なら `lines: list[str]`、`"error"` なら `error: BaseException`。
- `class FileLineLoader`:
  - `__init__(self, *, start_worker: Callable[[Callable[[], None]], None] | None = None, clock: Callable[[], float] = time.monotonic,
    stat: Callable[[str], os.stat_result] = os.stat, load: Callable[..., list[str]] = load_file_lines, timeout_seconds: float = FILE_LINE_LOAD_TIMEOUT_SECONDS)`
    - `start_worker` の既定は `threading.Thread(target=fn, daemon=True).start()`。**テストでは差し替えて、渡された関数を任意のタイミングで呼ぶ**（決定的に試すため）。
  - `request(self, path: str, encoding: str) -> FileLineLoadRequest`: 読込を始める（§6.1「読込を始めるとき」）。同じ読込キーの登録について:
    - **上限超過の印あり** → `FileLineError("前回のファイル読込が終わっていません（ファイル: {path}）")` を送出（ワーカーを起動しない）。
    - 印なし → ワーカーを起動せず待ち合わせ状態の要求を返す。
    - 登録なし → ワーカーを起動・登録して要求を返す。
  - `poll(self, request: FileLineLoadRequest) -> FileLinePoll`: 確認タイマーのたびに runner が呼ぶ。次の順で判定する（§3.2・§6.1）:
    1. 自分のワーカーが**終わっていれば**その結果（`done` / `error`）。**上限より優先**。
    2. 待ち合わせ中（未起動）なら、登録が外れていれば自分のワーカーを起動・登録する / 印付きの登録があれば「前回のファイル読込が終わっていません」の `error`。
    3. `started_at` からの経過が上限以上なら `error`（`FileLineError("ファイルの読込が 5 秒以内に終わりませんでした（ファイル: {path}）")`。秒数は `timeout_seconds` から組み立てる）。
       このとき**自分のワーカーが起動済みで未終了なら登録に上限超過の印を付ける**。待ち合わせ中（未起動）なら印は付けない。
    4. それ以外は `pending`。
    - 一度 `done` / `error` を返した要求に再度 `poll` しても同じ結果を返す（再起動しない）。
  - `clear_cache(self) -> None`: キャッシュを全部捨て、**キャッシュの世代**を進める（§6.2。構成セットの読込等で task_05 が呼ぶ）。
- ワーカーの仕事（非公開）: 起動時のキャッシュの世代を持ち、
  1. `stat(path)` でサイズと更新日時（`st_size` / `st_mtime_ns`）を取る。**`stat` が OSError なら**キャッシュを捨てて 2 の読込へ進む（読込側の従来の文言でエラーにするため）。
  2. キャッシュ（読込キーごと）の値と両方一致すれば、ファイルを読まずキャッシュの行の一覧を結果にする。不一致・キャッシュ無しなら `load(path, encoding=encoding)`。
  3. **ロックの中で**: 結果（行の一覧 / 例外）を置く。成功で読んだ場合、世代が今と同じならキャッシュを置き換える（値 = 1 で取った**読む前の** stat）。
     例外ならその読込キーのキャッシュを捨てる。登録簿から**自分が登録されている場合だけ**外す。
  - 例外は握りつぶさず結果として置く（`FileLineError` 以外の例外もそのまま渡す。文言の組み立ては呼び出し側）。
- **共有状態（登録簿・キャッシュ・世代・各仕事の結果と上限超過の印）はすべて 1 つの `threading.Lock` の中で読み書きする**。`stat` / `load` はロックの外で呼ぶ。
- Tk・`after`・runner・executor を import しない。

### `tests/test_file_line_loader.py`（新規）

`start_worker` を差し替え（渡された関数をリストに貯め、テストが明示的に呼ぶ）、`clock` / `stat` / `load` も差し替えて**実スレッドと sleep を使わない**。最低限:

1. 読込キーの正規化（大文字小文字・区切り文字の揺れが同じキー / 文字コード違いは別キー）
2. 起動 → 未終了は `pending` → ワーカー実行後 `done`（行の一覧）/ `load` の例外は `error` で同じ例外オブジェクト
3. キャッシュ: 2 回目は stat が同じなら `load` を呼ばない / stat が変われば呼ぶ / エラーでキャッシュが消える / `stat` の OSError で `load` の例外がそのまま結果になる
4. キャッシュの値は**読む前の** stat（読込中に stat が変わるよう差し替え、次の実行で読み直すこと）
5. `clear_cache` 後に、それ以前に起動したワーカーが終わってもキャッシュへ書かない（次の実行で `load` が呼ばれる）。結果自体は要求へ渡る
6. 同じ読込キーは同時に 1 本: 走行中に 2 つ目の `request` はワーカーを起動しない（起動関数の呼び出し回数）→ 1 本目の終了後の `poll` で 2 つ目が自分のワーカーを起動し、**1 本目の結果を使わない**
7. 上限: 経過 5 秒で `error`（文言）・登録に印 → 同じキーの `request` は即 `FileLineError`（文言）/ 別キーは起動できる / 印付きのワーカーが終わると登録が外れ、次の `request` は起動できる
8. 上限の直前に終わった結果は、`poll` 時点で経過が 5 秒以上でも `done`（結果を優先）・印は付かない
9. 待ち合わせ中の要求が上限を超えても印は付かない（1 本目のワーカーの登録に印が付かない）
10. `done` / `error` を返した後の再 `poll` は同じ結果・再起動しない

### 設計メモ / 制約

- 登録簿の「自分が登録されている場合だけ外す」は、上限超過で放置された古い仕事が、後から起動した新しい仕事の登録を外さないため（通常は同時 1 本なので起きないが、防御として必須）。
- 待ち合わせ中の要求は複数あってよい。先に `poll` された要求から起動する（§6.1）。
- `request` の送出する `FileLineError` は `keyseq.application.file_line_reader.FileLineError` を使う（新しい例外型を作らない）。
- 目安 250 行以内。超えるなら要求 / 仕事のデータ型を同じモジュール内で整理する（別モジュールへ分けない）。

## 読むファイル

- `instructions/history/27_file_line_async_read.md` §3.2・§5・§6（`:65-75`・`:101-140` 付近）
- `keyseq/application/file_line_reader.py`（全体・`load_file_lines` と `FileLineError` の口）
- `tests/test_file_line_reader.py:1-30`（テストの書き方の手本）

## 含まない

- runner / executor / app_state への組み込み・確認タイマー（`after`）・読込トークン（task_03・04）
- `clear_cache` の呼び出し元の配線・実スレッドでの起動の配線（task_05）
- codebase_map / 正本の更新（task_07）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_file_line_loader -v` が全 pass（上記 1〜10 を含む）
- 同じコマンドを **3 回連続**で実行して全 pass（実スレッド・sleep を使っていないことの確認）
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が全 pass（既存の失敗なし）
- `git diff --stat` / `git status` で変更が新規 2 ファイルのみ

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 共有状態がすべてロック下か / stat・load がロック外か / §3.2 の判定順・印の付け方・自分の登録だけ外す・世代違いは書かない / Tk 非依存 / 後続タスクの先取りなし）。
- 実機目視: なし（task_05 でまとめて実施）。
