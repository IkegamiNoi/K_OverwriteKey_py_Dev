# task_13b_packaging_macos_build

## 目的

PyInstaller の onedir で **macOS** の配布物（`keyseq.app`）を作る仕組みを `packaging/macos/` に置き、Mac でビルドして実機で確かめる（暫定 57 §6.1・§6.2・§6.3・§9 の 6 / 7）。Mac で実施する。

- ライセンスの表に Mac の行を足す: `pyobjc`・Mac の Python / Tcl / Tk・収集結果で見つかった推移依存（§6.3）。
- `.app` からの再起動に `open -n` が要るかを実測で決める（§6.2）。要る場合だけ `MacAppIdentity.relaunch` を変える。
- `pynput` の差し替えを Mac で実測する（§6.3）。
- task_12 / 13a / 13 で入れた仕組みを Mac の `.app` で確かめる。
- コードの変更は次に限る。
  - 表（`third_party.json`）と、その文書・テスト
  - 実測で要ると分かったときだけ `MacAppIdentity.relaunch` とそのテスト
- domain / application / presentation のロジック、ユーザーの設定の JSON のスキーマ、Windows の `.spec`・`packaging/README_dist.txt`（Windows の配布物の README）は変えない。

## 対象範囲（`packaging/macos/` 新規・`requirements-build.txt`・表に Mac の行・テスト 1 本・条件つきで再起動）

### `packaging/requirements-build.txt`

- 両 OS で同梱する 10 個（pyautogui・pynput・pyscreeze・pymsgbox・pytweening・mouseinfo・pygetwindow・pyrect・pyperclip・six）は `; sys_platform == "win32"` を外す（版は Mac の `.venv` と同じ）。`keyboard` は win32 のまま。
- `; sys_platform == "darwin"` を付けて次を固定する。版は Mac の `.venv` の値を使う。
  - `pyobjc-core==13.0`
  - `pyobjc-framework-Quartz` / `-Cocoa` / `-ApplicationServices` / `-CoreText` を各 `==13.0`
  - `rubicon-objc==0.5.7`（mouseinfo の darwin の依存）
- `pyinstaller==6.22.3` はそのまま（両 OS）。

### `packaging/macos/keyseq.spec`（新規）

- Windows の `.spec`（`packaging/windows/keyseq.spec`）を手本にした単独のファイルにする。共通部品へ切り出さない（Windows の `.spec` を変えると Windows で再ビルドしないと確かめられないため）。
- onedir（`EXE` + `COLLECT`）の後に `BUNDLE` を置き、`dist/keyseq.app` を作る。
  - `console=False`。`target_arch="arm64"`（Q6）。`argv_emulation=False`。
- `BUNDLE` の Info.plist（§6.2）:
  - `bundle_identifier` は **`io.github.ikegaminoi.keyseq`**（暫定 57 §6.3 v0.24・ユーザー 2026-11-22）。
  - `CFBundleShortVersionString` と `CFBundleVersion` に `keyseq.__version__` を入れる（`read_version()` で読む）。
  - `CFBundleName` / `CFBundleDisplayName` は `keyseq`。
- アイコンは差し替え口だけ置く。`packaging/macos/keyseq.icns` があれば `BUNDLE` の `icon=` に渡し、無ければ渡さない（§6.3）。
- datas は Windows の `.spec` と同じ列挙にする（見本 5 本・`jis_test.json` は入れない・§6.3）。
- `module_collection_mode={"pynput": "py"}`。
- `excludes`: `keyseq.infrastructure.os_backend.windows`・`keyboard`。
- `SOURCE_PACKAGES` は Windows と同じ（mouseinfo 0.1.3・pynput 1.8.2）。Mac で増えた依存はどれも GPL / LGPL ではない（pyobjc = MIT・rubicon-objc = BSD-3）。
- `BUNDLE` の後で `DISTPATH` の直下（`keyseq.app` の隣）へ次を書き出す。
  - `README.txt`: `packaging/macos/README_dist.txt` の `{version}` を置き換える。
  - `sources/`: Windows と同じ検査とコピー。
  - `.app` の中には書かない（署名が壊れる）。

### `packaging/macos/README_dist.txt`（新規・配布物に入る README）

- 中身は Windows の `packaging/README_dist.txt` と同じ。日英 1 ファイル・同じ項目。次の 3 点だけ Mac の内容にする。
  - 設定の保存先は `~/Library/Application Support/keyseq/config/`（§6.1 v0.21）。
  - `pynput` の差し替え方: 置き場は下の実測で決まった `keyseq.app` の中のパス。置き換えた後に `codesign --force --deep -s - keyseq.app` で署名し直すことも書く。
  - 初回にアクセシビリティと入力監視の許可が要ること。差し替えや再署名の後は、許可をやり直す必要がある場合があること（§6.2）。
  - 署名・公証をしていないので、別の Mac で開くと Gatekeeper が止めることがあること。そのときの開き方 2 通り: システム設定の「プライバシーとセキュリティ」の「このまま開く」、または `xattr -dr com.apple.quarantine keyseq.app`（§6.3 v0.24）。

### `packaging/README.md`（ビルドの手順書）

- 見出しを「配布ビルド」にし、今の Windows の手順を「Windows」の節に残す（中身は変えない）。
- 「macOS」の節を足す。書くことは次のとおり。
  - Mac で使う Python（Homebrew の 3.13 + `python-tk@3.13`・Q1）
  - `python -m PyInstaller packaging/macos/keyseq.spec`
  - 配布するもの: `dist/` の `keyseq.app`・`README.txt`・`sources/` の 3 つ。`ditto -c -k --keepParent` で zip にする例も書く。`dist/keyseq/` は中間の生成物なので配らない。
  - 再ビルドすると権限の再許可が要る場合があること（§6.2）。
  - アイコンの置き場（`packaging/macos/keyseq.icns`）。
  - 依存の版を上げたら揃える 4 点: `requirements-build.txt`・`third_party.json`・`sources/`・2 つの `.spec` の `SOURCE_PACKAGES`。
  - 識別子（`io.github.ikegaminoi.keyseq`）は変えない。権限は識別子と署名に結びつくので、変えると再許可が要る。

### `third_party.json` と文書（新規）

- 末尾（`PyInstaller` の後）に `"platforms": ["darwin"]` の行を足す。

  | 行 | 版 | ライセンス | file |
  |---|---|---|---|
  | `pyobjc` | 13.0 | MIT License | `pyobjc.txt` |
  | `rubicon-objc` | 0.5.7 | BSD 3-Clause License | `rubicon_objc.txt` |
  | `Python` | 3.13.18 | PSF License | `python_macos.txt` |
  | `Tcl` | 9.1.0 | Tcl/Tk License | `tcl.txt`（Windows の行と共用） |
  | `Tk` | 9.1.0 | Tcl/Tk License | `tk.txt`（Windows の行と共用） |

  - `rubicon-objc` の行も含めて、すべて無条件に書く（mouseinfo が darwin で import するので収集される見込み）。ビルドの収集結果に `rubicon` が無かったら、メインが `third_party.json` の行・`rubicon_objc.txt`・`requirements-build.txt` の固定・`tests/test_third_party.py` の `mac_names` の 4 か所からまとめて外す。
  - ほかに表に無い依存が見つかったら、止めてユーザーに報告する。Homebrew の dylib（OpenSSL 等）も報告に含める。Windows の表にも OpenSSL 等の行は無いので、行を足すかはユーザーが決める。
- 文書は起票後にメインがコピー済み（2026-11-22）。Codex は文書を作らない・変えない。
  - `pyobjc.txt` ← `pyobjc_framework_quartz-13.0.dist-info/licenses/LICENSE.txt`（Cocoa・CoreText と同じ文書。pyobjc-core と ApplicationServices の dist-info にはライセンスの文書が無い）
  - `rubicon_objc.txt` ← `rubicon_objc-0.5.7.dist-info/licenses/LICENSE`
  - `python_macos.txt` ← Homebrew の `Python.framework/Versions/3.13/lib/python3.13/LICENSE.txt`
  - Tcl / Tk: Homebrew の `tcl-tk/license.terms` と `lib/tk9.1/demos/license.terms` は、今の `tcl.txt` / `tk.txt` と一字一句同じ（改行を除く）。なので新しい文書を作らず共用する。ファイル名の重複の検査は OS ごとなので通る。
- `pyobjc.txt` に「libffi-src は別の製品」とある。収集結果に libffi が入っていれば、dylib の報告に含める。

### `tests/test_third_party.py`

- `mac_names` を内包表記から明示の並びに替える。並びは Windows の 15 行から keyboard / Python / Tcl / Tk を除き、末尾に Mac の行を表の順で続けたもの。`:27` の暫定のコメントを消す。
- `test_library_versions_match_installed_distributions`: 行の名前と配布物の名前の対応 `{"pyobjc": "pyobjc-core"}` を置き、`importlib.metadata.version` に渡す名前を引き直す（`pyobjc` という配布物は入っていないため）。
- `test_python_tcl_and_tk_versions_match_runtime` は今のままで Mac で照合が走ることを確かめる（skip ではなく pass する）。

### 条件つき: `keyseq/infrastructure/os_backend/macos/backend.py` の `MacAppIdentity.relaunch`

- 下の「手順」4 の実測で、今の `relaunch_app`（`sys.executable` を直接起動する）に不具合が出たときだけ変える。
  - 不具合とは、Dock のアイコンが 2 つになる・再起動後のフックが権限で動かない・前面に出ない、のいずれか。
- 変え方: frozen で `sys.executable` が `*.app/Contents/MacOS/` の下にあるときは、`["open", "-n", <.app のパス>, "--args", *sys.argv[1:]]` を `cwd=startup_cwd` で起動する。それ以外（開発実行・`.app` の外）は今の `relaunch_app` を使う。`OSError` は今どおりログに残して返す。
- テストは `tests/test_app_relaunch.py` の形に倣い、Mac の分岐を `Popen` のモックで確かめる（`.app` の内・外・開発実行の 3 通り）。
- 不具合が出なければ変えず、実測の結果を完了報告と decisions.md に書く。

## 設計メモ / 制約

- `.app` の中のパスは `bundled_root()` = `sys._MEIPASS`（`.app` では `Contents/Frameworks`）と、`app_data_root` = `~/Library/Application Support/keyseq` に従う（task_12）。datas の相対配置は Windows と同じでよい。PyInstaller は datas を `Contents/Resources` に置き、`Frameworks` から辿れるようにする。読めないものがあれば実測で止める。
- Tk 9.1 を PyInstaller 6.22.3 で同梱できるかは未実測（Q1・decisions「PyInstaller での可否」）。ビルドや起動で Tcl / Tk の読み込みに失敗したら、回避策を探して進めずに止め、ユーザーに報告する（Q1 を見直すかはユーザーが決める）。
- arm64 では PyInstaller が `.app` に ad-hoc の署名をする。ビルドの後に `.app` の中を書き換えないこと（README と sources を `.app` の外に出す理由）。
- 権限（アクセシビリティ・入力監視）は署名で識別される。再ビルド・差し替え・置き場所の変更の後は、許可をやり直す必要がある場合がある。実測の結果は手順書に反映する。
- 署名・公証・`.dmg` は対象外（§10）。

## 手順（実行の担当）

1. **メイン**: Mac の `.venv` へ `pyinstaller==6.22.3` を入れ、`pip download` で mouseinfo 0.1.3 / pynput 1.8.2 の sdist を `packaging/sources/` に取る。
   - どちらも PyPI から取るので、先にユーザーの許可を得る。
   - `packaging/sources/` は gitignore されていて、この worktree には無い。Python 3.13 では `pip download` が通る見込み。通らなければ task_13 と同じく PyPI の sdist を直接取り、SHA256 を照合する。
   - ライセンスの文書 3 つをコピーする（上の表）。
   - **実施済み（2026-11-22・ユーザー許可）**: PyInstaller 6.22.3 を導入。`pip download` は Python 3.13 で通った。SHA256 は `MouseInfo-0.1.3.tar.gz` = `2c62fb88…f6e7`・`pynput-1.8.2.tar.gz` = `f493c871…7087`。文書 3 つもコピー済み。
2. **codex-implementer**: `requirements-build.txt`・`packaging/macos/` の 2 ファイル・`packaging/README.md`・`third_party.json` の行・`tests/test_third_party.py` を書く（再起動の変更は含めない）。
3. **verifier**（Mac・`../../../.venv/bin/python`）: 標準検証・ビルド・配布物の中身の確認・`pynput` の差し替えの実測（下の「確認」）。収集結果の照合の結果を返す（表に無い依存・dylib の一覧）。
4. **ユーザー**: 実機確認（「完了条件」）。再起動（3）で不具合が出たら、メインが再起動の変更を codex-implementer へ依頼し、verifier の検証と再ビルドの後、3 をやり直す。

## 読むファイル

- `instructions/history/57_mac_support.md` §6.1〜§6.3（`:322-351`）・§8 Q1 / Q3 / Q6（`:358-375`）
- `packaging/windows/keyseq.spec`（全体・手本）・`packaging/README.md`・`packaging/README_dist.txt`・`packaging/requirements-build.txt`（全体）
- `keyseq/presentation/bundled_paths.py`（全体）
- `keyseq/presentation/help/content/third_party/third_party.json`（全体）
- `tests/test_third_party.py:1-60`
- 条件つきのときだけ: `keyseq/infrastructure/os_backend/macos/backend.py:771-780`・`keyseq/infrastructure/os_backend/app_relaunch.py`・`tests/test_app_relaunch.py`

## 含まない

- Windows の `.spec`・`packaging/README_dist.txt`・Windows の再ビルドと実機確認（task_13 で完了）。
  - 表と `test_third_party` の変更は Windows でも流して確かめる必要がある（`mac_names` の明示化・名前の対応表）。本タスクでは行わない。**完了報告の残課題に必ず書き、task_14 の起票時に Windows 検証の項目として拾う**。
- アイコンの絵と別ライセンス（独自のアイコンを入れるとき・decisions 2026-11-18）
- 署名・公証・`.dmg`・Intel Mac（§10）
- 正本 `spec_detail/` への反映（features.md の GPL の表記・同梱物の一覧・Mac の保存先）→ task_14
- 2 枚目のモニタの目視・中クリック（保留中・本タスクの確認に含めない）
- タグを打つことと push（ユーザー）

## 確認

- 標準検証（Mac・`../../../.venv/bin/python`・tests_ui は通しで流さない）:
  - `-m compileall -q keyseq main.py tests tests_ui` が clean
  - `-m unittest discover -s tests` が失敗 0・エラー 0。基準線（2131 件・失敗 1〔test_third_party〕）から件数が減らず、`test_third_party` の失敗が解消して Python / Tcl / Tk の照合が pass する。`PyInstaller` と `pyobjc`（pyobjc-core）の版の照合も pass する。
  - `-m tests.smoke_app` が pass
  - tests_ui の `test_help_window` を単独で流して失敗 0
  - 再起動を変えたとき: `tests/test_app_relaunch.py` が pass
- ビルド（verifier）:
  - `python -m PyInstaller packaging/macos/keyseq.spec` が成功し、`dist/keyseq.app`・`dist/README.txt`（`{version}` が置き換わっている）・`dist/sources/` の 2 つのアーカイブができる。
  - `.app` の中に次がある: `LICENSE`・`third_party/*.txt`・`locales/*.json`・`status_icon/images/*.png`・`config/user/keylayout/` の 5 本（`jis_test.json` が無い）・`help/content/` は `help_ja.json`・`help_en.json`・`third_party/` だけ・`pynput/` の `.py`。それぞれの実際のパス（`Resources` / `Frameworks`）を報告する。
  - `codesign --verify --deep --strict dist/keyseq.app` が通る。
  - `plutil -p dist/keyseq.app/Contents/Info.plist` で識別子と版が入っている。
  - 収集結果（`build/keyseq/warn-keyseq.txt`・xref・`.app` の中の最上位の名前と dylib）を照合する。`keyseq`・標準ライブラリ・PyInstaller の実行時の部品以外が表の行に収まるかを報告する。収まらないものは一覧にして止める。
  - `packaging/sources/` を空にするとビルドが例外で止まる（確認後に戻す）。
  - `git status` に `packaging/macos/keyseq.spec`・`README_dist.txt` が出る（無視されていない）。
- `pynput` の差し替えの実測（verifier・§6.3）:
  - `.app` の写しの `pynput/__init__.py` の先頭に、目印のファイルを書く 1 行を足す。目印は `~/Library/Application Support/keyseq/` の外の、確認用の一時フォルダに書く。
  - 写しを `codesign --force --deep -s -` で署名し直す。写しの `Contents/MacOS/keyseq` を直接起動して（`open` を使わず PID を取る）、目印ができることを確かめる。
  - 目印ができたらすぐに、そのプロセスを**PID を指定して**終了する（起動した GUI はフックを入れることがある）。権限のダイアログで止まっても、同じく PID で終了する。写しは確認後に消す。
  - 署名し直さないと起動できるかどうかも記録する（README の記述の根拠にする）。

## 完了条件

- 上記の確認が pass・**reviewer 採用**。
- 実機確認（ユーザー・`dist/keyseq.app` を別の場所〔例 `~/Applications`〕へコピーして起動）:
  1. 初回の起動で権限の案内が出る。許可した後、`~/Library/Application Support/keyseq/config/user/keylayout` に見本 5 本がコピーされる。
  2. 設定（キーマップ等）を保存して終了し、もう一度起動すると読み込まれる（§9 の 7）。
  3. 言語を切り替えて再起動すると、`keyseq` が 1 つだけ起き直る。Dock のアイコンが 1 つで、窓が前面に出て、置換が権限つきで動く（`open -n` の要否の判定）。
  4. ヘルプのライセンスの窓に Mac の行だけが出る。keyboard と Windows の Python / Tcl / Tk の行は出ず、Mac の行がある。文言は ja / en で切り替わる。
  5. 置換・シーケンスの実行（キーとマウス）・キーの取得が、開発実行と同じように動く。
- 起票時の判断（識別子 `io.github.ikegaminoi.keyseq` 等）と、実測の結果（`open -n` の要否・`pynput` の置き場と再署名の要否・権限の再許可の要否）を decisions.md に書く。手順書と README の記述を、その結果と合わせる。
