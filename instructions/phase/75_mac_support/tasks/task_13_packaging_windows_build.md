# task_13_packaging_windows_build

## 目的

PyInstaller の onedir で **Windows** の配布物を作る仕組み（`packaging/`）を置き、ビルドして実機で確かめる（暫定 57 §6.2・§6.3・§6.1 の v0.21）。

- 配布物には次を入れる。
  - 同梱の README
  - 依存のソースのアーカイブ
  - `pynput` の差し替え口（`.py` のまま置く）
- 第三者ライセンスの表に `PyInstaller` の行を足す。
- コードの変更は表（`third_party.json`）と、その文書・テストだけ。domain / application / presentation のロジックと、ユーザーの設定の JSON のスキーマは変えない（基点の切り替えは task_12 で済み）。
- Mac の `.spec`・Mac のビルド・Mac の行は task_13b で扱う。

## 対象範囲（`packaging/` 新規・同梱の表に 1 行・テスト 1 本・`.gitignore`）

### `packaging/requirements-build.txt`（新規）

- 先頭に `-r ../requirements.txt` を置く。
- 版を `==` で固定する。
  - `pyinstaller`（実装時に `.venv` へ入れた版。下の「手順」1）
  - 同梱する Windows のライブラリ 11 個。版は `third_party.json` の今の値（keyboard 0.13.5・pyautogui 0.9.54・pynput 1.8.2・pyscreeze 1.0.1・pymsgbox 2.0.1・pytweening 1.2.0・mouseinfo 0.1.3・pygetwindow 0.0.9・pyrect 0.2.0・pyperclip 1.11.0・six 1.17.0）。
- Windows のものには `; sys_platform == "win32"` を付ける。Mac で固定する版は task_13b で足す。

### `packaging/windows/keyseq.spec`（新規）

- onedir（`EXE` + `COLLECT`）にする。`console=False`。
  - 名前は `keyseq`（`dist/keyseq/keyseq.exe`）。Mac の `Application Support/keyseq`・`AppIdentity` の識別子と揃える。
  - 入口は `main.py`。パスは spec のある場所（`SPECPATH`）からリポジトリの直下を求めて組み立てる。cwd には頼らない。
- アイコンは差し替え口だけ置く（§6.3）。`packaging/windows/keyseq.ico` があれば `icon=` に渡し、無ければ渡さない（PyInstaller の既定）。絵そのものは置かない。
- datas は、`bundled_paths.py` と `catalog.py` が読む相対配置を `_MEIPASS` の下に揃える。
  - `LICENSE` → `.`
  - `keyseq/presentation/help/content` の `help_*.json` と `third_party/` の `*.json` / `*.txt` → 同じ相対パス（ファイルの種類で列挙し、`__pycache__` 等を入れない・起票レビュー M3）
  - `keyseq/presentation/status_icon/images` → 同じ相対パス
  - `keyseq/shared/i18n/locales` → 同じ相対パス
  - レイアウトの見本 5 本（`us_tkl` / `us_mac` / `jis` / `jis_mac` / `de` の `.json`）→ `config/user/keylayout`。
    - ファイル名で列挙する。glob で全部入れると `jis_test.json` が入るので使わない（§6.3）。
- `pynput` はアーカイブに入れず `.py` のまま置く（`module_collection_mode={"pynput": "py"}`・§6.3）。
  - backend は pyinstaller-hooks-contrib の hook に任せる。ビルド後に `pynput.keyboard._win32` / `pynput.mouse._win32` が入っていない（または exe で import エラーが出る）と分かったときだけ hiddenimports に足す（§6.2「実測で確定」）。
- `excludes` に `keyseq.infrastructure.os_backend.macos` を入れる（Windows では import しない・pyobjc の警告を減らす。必須ではない）。
- `COLLECT` の後で、配布物のフォルダ（`os.path.join(DISTPATH, "keyseq")`。`dist/` を決め打ちしない・起票レビュー M4）へ次を書き出す。
  - `README.txt`: `packaging/README_dist.txt` の `{version}` を `keyseq.__version__` に置き換える。
  - `sources/`: `packaging/sources/` の中身をコピーする。
  - 同梱するソースは `.spec` の 1 つの定数（例 `SOURCE_PACKAGES = {"mouseinfo": "0.1.3", "pynput": "1.8.2"}`）にまとめる。`packaging/sources/` に `<名前>-<版>` で始まるファイルが無いものがあれば、ビルドを例外で止める（配り忘れの防止線・§6.3・起票レビュー M1）。版は `requirements-build.txt`・表と同じ値（揃えるのは手順書の 3 点）。

### `packaging/README_dist.txt`（新規・配布物に入る README）

- 日本語と英語の両方を 1 ファイルに書く（日本語が先）。書くことは §6.3 のとおり。
  - 本体: Key Replacer Sequencer、`Copyright (C) 2026 池上ノイ (Ikegami Noi)`、GNU GPL v3 以降（v0.23）。
  - 対応するソース: https://github.com/IkegamiNoi/K_OverwriteKey_py_Dev のタグ `v{version}`。
  - PyInstaller のブートローダの例外。
  - 第三者ライセンスはヘルプの「ライセンス」の窓で見られること。
  - `sources/` に同梱した GPL / LGPL の依存のソース（mouseinfo・pynput）。
  - `pynput` の差し替え方（`_internal/pynput/` を変更版に置き換える）。
  - 設定は exe の隣の `config/` に保存されること（§6.1）。

### `packaging/README.md`（新規・ビルドの手順書）

- 手順を次の順に書く。
  1. `.venv` に `packaging/requirements-build.txt` を入れる。
  2. ソースのアーカイブを `packaging/sources/` へ取る（`pip download --no-binary :all: --no-deps mouseinfo==0.1.3 pynput==1.8.2 -d packaging/sources`）。
  3. リポジトリの直下で `python -m PyInstaller packaging/windows/keyseq.spec` を実行する。
  4. 収集結果（`build/keyseq/warn-keyseq.txt`・`xref-keyseq.html`）と表を照合する。
  5. ビルドした版のタグ `v<版>` を打ち、push する。
- 依存の版を上げたら、次の 3 つを揃えることを書く: `requirements-build.txt`・`third_party.json`・`sources/`。
- アイコンの置き場（`packaging/windows/keyseq.ico`）も書く。

### `.gitignore`

- `packaging/sources/` を足す（取ってきたアーカイブを git に入れない。`build/` と `dist/` は既に除外されている）。
- `:41` の `*.spec` で `.spec` が無視されるため、その後ろに `!packaging/**/*.spec` を足す（起票レビュー H1）。

### `keyseq/presentation/help/content/third_party/third_party.json` と `pyinstaller.txt`（新規）

- 末尾（`Tk` の後）に次の行を足す。`platforms` は付けない（両 OS）。
  `{"name": "PyInstaller", "version": "<固定した版>", "license": "GNU GPL v2 or later (with bootloader exception) / Apache-2.0", "file": "pyinstaller.txt"}`
- `pyinstaller.txt` には、入れた版の dist-info のライセンスの文書をそのまま入れる。GPL v2 本文・ブートローダの例外・ランタイムの hook の Apache-2.0 が含まれていること（§6.3）。
  - Apache-2.0 の部分が含まれていない文書だったら、PyInstaller の配布元の Apache-2.0 の文書を後ろに足す。
  - 中身はメインがコピーする（`.venv` の外の読み取りは Codex に頼らない）。
- ビルドの収集結果に、表に無い同梱の依存（例: Pillow）があれば止めてユーザーに報告する。行を足すかはユーザーの判断。

### `tests/test_third_party.py`

- 名前の順の期待値（`windows_names`）の末尾に `PyInstaller` を足す（Windows 15 行・Mac は内包表記で 11 行）。`:27` の「ten-row」のコメントを 11 行に直す。
- 版の照合は今のままで動く（PyInstaller が入っていない環境では、その subTest が skip になる）。

## 設計メモ / 制約

- ビルド後のパスは task_12 の `bundled_root()` = `sys._MEIPASS`（onedir では `_internal/`）と `app_data_root` = exe のフォルダに従う。datas の相対配置をずらすと、ヘルプ・文言・見本が読めなくなる。
- `.spec` は Python なので `COLLECT` の後に任意の処理を書ける。README とソースのコピーはここに置き、手作業のコピーを手順書に書かない（配り忘れを防ぐ）。
- タグを打つのと push はユーザーが行う。タグの名前は `v` + `keyseq.__version__`（今は `0.1.0`）。配布の前に `__version__` を上げるかはユーザーが決める。
- `requirements-build.txt` で固定するのは `pyinstaller` と同梱物だけ。PyInstaller の依存（altgraph・pefile・pyinstaller-hooks-contrib 等）は固定しない（起票レビュー L2・参考）。

## 手順（実行の担当）

1. **メイン**: PyInstaller を `.venv` へ入れる（PyPI からの取得になるので、先にユーザーの許可を得る）。
   - Python 3.14 に対応した最新の安定版を入れ、その版を `requirements-build.txt` と表に書く。
   - あわせて、ソースのアーカイブ 2 つを `packaging/sources/` へ `pip download` する（同じ許可で）。Python 3.14 で sdist の metadata が作れず失敗したら、PyPI のその版の sdist を直接取る（起票レビュー M2）。どちらで取ったかを手順書に書く。
   - `pyinstaller.txt` を dist-info からコピーする。
2. **codex-implementer**: `packaging/` の 4 ファイル・`.gitignore`・`third_party.json` の行・`tests/test_third_party.py` を書く。
   - CRLF のファイルは、依頼前に LF に揃える。
3. **verifier**: 標準検証を実行し、ビルド（`python -m PyInstaller packaging/windows/keyseq.spec`）と配布物の中身の確認をする（下の「確認」）。
4. **ユーザー**: 実機確認（下）。

## 読むファイル

- `instructions/history/57_mac_support.md` §6.1〜§6.3（`:322-350`）
- `keyseq/presentation/bundled_paths.py`（全体・datas の相対配置の根拠）
- `keyseq/shared/i18n/catalog.py:1-20`（locales の場所）
- `main.py`（入口）・`requirements.txt`・`keyseq/__init__.py`（`__version__`）
- `keyseq/presentation/help/content/third_party/third_party.json`（全体）
- `tests/test_third_party.py:1-60`
- `.gitignore`（全体）

## 含まない

- Mac の `.spec`・`.app`・`Info.plist` の識別子・Mac のビルドと実機確認・`open -n` の要否 → task_13b
- Mac の行（pyobjc・Mac の Python / Tcl / Tk）と、Mac の `requirements-build.txt` の固定 → task_13b
- アイコンの絵と、その別ライセンス（`ASSETS_LICENSE.md`）→ 独自のアイコンを入れるとき（decisions 2026-11-18・未着手）
- 正本 `spec_detail/` への反映（features.md の GPL 表記・同梱物の一覧）→ task_14
- インストーラ・署名・自動更新・CI でのビルド
- タグを打つことと push（ユーザー）

## 確認

- 標準検証（Windows・`..\..\..\.venv\Scripts\python.exe`）:
  - `-m compileall -q keyseq tests tests_ui` が clean
  - `-m unittest discover -s tests` が失敗 0（今の基準 2203 件）。`test_third_party` は PyInstaller の版の照合を含めて pass
  - `-m tests.smoke_app` が pass
  - tests_ui の `test_help_window` が失敗 0
- ビルド（verifier）:
  - `python -m PyInstaller packaging/windows/keyseq.spec` が成功する。
  - 配布物について次を確認する。
    - `dist/keyseq/keyseq.exe`・`README.txt`（`{version}` が置き換わっている）・`sources/` の 2 つのアーカイブがある。
    - `_internal/` に `LICENSE`・`keyseq/presentation/help/content/third_party/*.txt`・`keyseq/shared/i18n/locales/*.json`・`keyseq/presentation/status_icon/images/*.png` がある。
    - `_internal/config/user/keylayout/` が 5 本で、`jis_test.json` が無い。
    - `_internal/pynput/` に `.py` のファイルがある。
  - `packaging/sources/` を空にしてビルドすると例外で止まる（確認後に戻す）。
  - `_internal/keyseq/presentation/help/content/` には `help_ja.json`・`help_en.json`・`third_party/` だけがある。
  - 収集結果（`_internal/` の最上位と xref）の、`keyseq` と標準ライブラリ以外の最上位の名前が、表の行（と `pywin32-ctypes` 等の PyInstaller の実行時の部品）に収まる。収まらなければ止めて報告する。
  - `git status` に `packaging/windows/keyseq.spec`・`README_dist.txt`・`README.md`・`requirements-build.txt` が出る（無視されていない）。`packaging/sources/` は出ない。
- `pynput` の差し替えの実測（verifier。§6.3）:
  - 配布物の写しの `_internal/pynput/__init__.py` の先頭に、exe のフォルダへ目印のファイルを書く 1 行を足す。
  - その exe を起動して目印ができることを確かめ、そのプロセスを**PID を指定して**終了する（python.exe を一括で終了しない）。
  - 写しは確認後に消す。

## 完了条件

- 上記の確認が pass・**reviewer 採用**。
- 実機確認（ユーザー・`dist/keyseq/keyseq.exe`）:
  1. 初回起動で exe の隣に `config/` ができ、`config/user/keylayout` に見本 5 本がコピーされる。
  2. 設定（キーマップ等）を保存して終了し、再起動すると読み込まれる。
  3. 言語の切り替えで再起動すると、exe が 1 つだけ起き直る（argv[0] の重複なし）。
  4. ヘルプ・ライセンスの窓が開き、15 行（最後が PyInstaller）が出る。文言が ja / en で切り替わる。
  5. 置換・シーケンスの実行（キーとマウス）が開発実行と同じように動く。
