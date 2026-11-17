# task_12_app_data_root_and_relaunch

## 目的

ビルド後（PyInstaller の onedir）にも設定の保存先・同梱物の場所・再起動が正しく働くよう、基点を 1 か所に揃える（暫定 57 §6.1〔v0.21〕・§6.2・§8 Q3）。

- 設定のルート: `AppIdentity.app_data_root(dev_root)` を新設し、`App` の `base_dir` をこれから作る。開発実行は今と同じ値（リポジトリの直下）・ビルド後は Windows = exe のあるフォルダ / Mac = `~/Library/Application Support/keyseq`。どちらもその下に `config/`（v0.21）。
- 同梱物: `bundled_root()` をビルド後は `sys._MEIPASS` にする。
- レイアウトの見本: ユーザーの設定フォルダに `user/keylayout` が無いときだけ、同梱の見本を全部コピーする（v0.21・上書きしない）。
- 再起動: `windows/app_relaunch.py` を OS 共通の置き場へ移し（phase.md の M4）、ビルド後は argv[0] の重複を除く。Mac も同じ関数を使う。
- **開発実行の振る舞いは変えない**（パスの値・再起動のコマンドとも今と同じ）。JSON のスキーマ・domain は不変。`sys.platform` の分岐は足さない（ビルドかどうかは `getattr(sys, "frozen", False)` で見る）。

## 対象範囲（infrastructure の os_backend・presentation の基点・新規 1 モジュール）

### `keyseq/infrastructure/os_backend/contracts.py`

- `AppIdentity` に `def app_data_root(self, dev_root: Path) -> Path: ...` を足す（`dev_root` = 開発実行のときに返す基点。呼ぶ側が `bundled_root()` を渡す）。

### `keyseq/infrastructure/os_backend/app_relaunch.py`（`windows/app_relaunch.py` から移動）

- `git mv` で移す。旧パスに横流しのモジュールは残さない（`file_organization_rules.md`）。
- `relaunch_app(startup_cwd)` の argv: ビルド後（`getattr(sys, "frozen", False)`）は `[sys.executable, *sys.argv[1:]]`、開発実行は今どおり `[sys.executable, *sys.argv]`。`OSError` を返す・ログに残す振る舞いは今どおり。

### `keyseq/infrastructure/os_backend/windows/backend.py`

- `WindowsAppIdentity.relaunch` の委譲先を新しい場所の `relaunch_app` に変える。
- `app_data_root(dev_root)`: ビルド後は `Path(sys.executable).resolve().parent`、開発実行は `dev_root` を返す。

### `keyseq/infrastructure/os_backend/macos/backend.py`

- `MacAppIdentity.relaunch` を「未実装の OSError」から、共通の `relaunch_app` への委譲に変える（`.app` を `open -n` で起こすかは task_13 のビルド後の実測で決める）。
- `app_data_root(dev_root)`: ビルド後は `Path.home() / "Library" / "Application Support" / "keyseq"`、開発実行は `dev_root`。

### `keyseq/presentation/bundled_paths.py`

- `bundled_root()`: ビルド後は `Path(sys._MEIPASS)`、開発実行は今どおり `Path(__file__).resolve().parents[2]`。
- `bundled_keylayout_dir() -> Path` を足す: `bundled_root() / "config" / "user" / "keylayout"`（同梱の見本の置き場。開発実行ではリポジトリの今の場所と同じ。ビルドの datas をこの相対配置に揃えるのは task_13）。

### `keyseq/infrastructure/bundled_layouts.py`（新規）

- `install_bundled_layouts(source_dir: Path, user_root: Path) -> bool`: `user_root / "keylayout"` が無く、`source_dir` があるときだけ、`source_dir` の `*.json` をコピーして `True`。それ以外は何もせず `False`（開発実行ではリポジトリの `config/user/keylayout` が既にあるので何もしない。同じ場所かの比較は置かない・起票レビュー L1）。
- **半端なフォルダを残さない**（起票レビュー M1）: 一時フォルダ `user_root / "keylayout.tmp"`（前回の残りがあれば先に消す）へ全件コピーし、全部成功したら `os.replace` で `keylayout` へ改名する。途中の `OSError` では一時フォルダを `shutil.rmtree`（`ignore_errors=True`）で消してから送出する（呼ぶ側の扱いは下）。

### `keyseq/presentation/app.py`（`__init__` の基点の箇所・`:121-123` 付近のみ）

- `self.base_dir = str(backend.app.app_data_root(bundled_root()))`（`backend` は今 `__init__` で使っている os_backend）。`config_root` / `user_root` の作り方は今どおり。
- `ensure_split_config_dirs` の直後に `install_bundled_layouts(bundled_keylayout_dir(), Path(self.user_root))` を呼ぶ。`OSError` は `logging` に残して起動を続ける（見本が無くても起動できる・今の `resolve_keylayout_dir` の戻り先が働く）。

### テスト（追加・修正）

- `tests/test_app_relaunch.py`: import / patch の先を新しい場所へ。ビルド後の argv（`sys.frozen` と `sys.argv` を patch して argv[0] が除かれる）を足す。
- `tests/test_os_backend_contracts.py`: 両 OS の `app_data_root`（開発実行 = `dev_root`・ビルド後 = 上の場所。`sys.frozen` / `sys.executable` / `Path.home` を patch）と、Mac の `relaunch` が共通の関数へ委譲することを足す。既存の Windows の `relaunch` の patch 先（`:306`）を新しい場所へ。テストのダミーの `AppIdentity` があれば `app_data_root` を足す。
- `tests/test_bundled_layouts.py`（新規）: フォルダが無いときだけコピー（`user_root` の親ごと無い新規の一時フォルダでも、先に `ensure_split_config_dirs` を呼べば入る・起票レビュー L2）・既にあれば何もしない（中身を上書きしない）・見本のフォルダが無ければ何もしない・コピーの途中の `OSError`（`shutil.copy2` 等を patch）で `keylayout` も `keylayout.tmp` も残らず例外が出る・前回の `keylayout.tmp` が残っていても成功する。
- `bundled_root()` のビルド後（`sys.frozen` と `sys._MEIPASS` を patch）のテストを、既存の近いテストのファイルに足す（無ければ新規 `tests/test_bundled_paths.py`）。

### 文書

- `instructions/common/codebase_map.md`: os_backend の節（`app_relaunch.py` の置き場・`AppIdentity.app_data_root`）・`bundled_paths.py` / `bundled_layouts.py` の行を追従する。

## 設計メモ / 制約

- 開発実行で `bundled_root()` と今の `base_dir`（`app.py` の `dirname` 3 回）は同じリポジトリの直下を指す（メイン確認）。よって開発実行では `app_data_root(bundled_root())` = 今の値で、見本のコピーも「同じ場所」で何もしない。
- `config_paths.py` の `config` で始まる相対パスを `base_dir` から解く処理（`:63-71`）・旧 `settings/`・`keylayout/` の参照は変えない（`base_dir` が app_data_root になるだけ）。
- i18n の `catalog.py`（`Path(__file__).parent / "locales"`）は変えない。ビルド後も `__file__` は `_MEIPASS` の下を指すため、datas の相対配置を揃えれば足りる（確認は task_13）。
- presentation から `sys._MEIPASS` を見るのは `bundled_paths.py` の 1 か所だけ。

## 読むファイル

- `keyseq/infrastructure/os_backend/contracts.py:100-125`（`AppIdentity`）
- `keyseq/infrastructure/os_backend/windows/app_relaunch.py`（全体・移動対象）
- `keyseq/infrastructure/os_backend/windows/backend.py:1-15, 100-115`
- `keyseq/infrastructure/os_backend/macos/backend.py:765-775`
- `keyseq/presentation/bundled_paths.py`（全体）
- `keyseq/presentation/app.py:100-135`
- `tests/test_app_relaunch.py`（全体）・`tests/test_os_backend_contracts.py:290-320`
- `instructions/history/57_mac_support.md` §6.1・§6.2・§8 Q3

## 含まない

- `packaging/`・`.spec`・`requirements-build.txt`・datas / hiddenimports・ビルドと、ビルド後の実機確認（保存先・見本のコピー・再起動・各 OS で保存した設定の読み込み）→ task_13
- Mac の `.app` の再起動に `open -n` を使うかの判断 → task_13（ビルド後の実測）
- 同梱する見本の選別（`jis_test.json` を入れるか等）→ task_13
- `test_third_party` の第三者ライセンスの表の扱い → task_13
- 正本 `spec_detail/` への反映 → task_14
- 設定のルートの移行（既存の開発実行の設定を Application Support へ移す等）。Q8 のとおり OS 間・置き場の間の移行はしない

## 確認

- Windows（`..\..\..\.venv\Scripts\python.exe`）:
  - `-m compileall -q keyseq tests tests_ui` が clean
  - `-m unittest discover -s tests` が失敗 0（今の基準 2193 件 + 追加分）
  - `-m tests.smoke_app` が pass（開発実行で設定・レイアウトが今どおり読める）
  - tests_ui を 1 本ずつ: `test_first_launch_flow`・`test_app_ui_flows`・`test_help_window` が失敗 0
- Mac は task_13 でまとめて確認する（ユーザーが push した後に Mac の worktree で `tests`・smoke）。
- 静的: `keyseq/` で `sys.platform` を見るのが `os_backend/__init__.py` だけのまま（AST テストが pass）・`windows/app_relaunch.py` が残っていない。

## 完了条件

- 上記の確認が pass・**reviewer 採用**。
- 実機目視: 開発実行で言語の切り替え（再起動）が今どおり動くことを Windows で確認（ユーザー）。ビルド後の目視は task_13 でまとめて行う。
