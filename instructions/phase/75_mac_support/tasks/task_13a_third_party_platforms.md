# task_13a_third_party_platforms

## 目的

第三者ライセンスの表の各行に、その行の配布物が入る OS を持たせ、ライセンスの窓と版の照合を**実行中の OS の行だけ**にする（暫定 57 §6.3・v0.22）。Windows と Mac では同梱物が違う（Windows だけ `keyboard`・Mac だけ `pyobjc`・Python / Tcl / Tk の版）。

- 本タスクは**仕組みと Windows の行の印**まで。Mac の行（`pyobjc`・Mac の Python / Tcl / Tk）は Mac で版と文書を確かめて task_13b で足す。PyInstaller の行は版を固定する task_13 で足す。
- presentation（`help/`）と os_backend の公開面だけ。domain / application・ユーザーの設定の JSON のスキーマは不変（変わるのは同梱物の `third_party.json`）。presentation で `sys.platform` を見ない（§3.1）。

## 対象範囲（presentation の help・os_backend の公開面・同梱の表）

### `keyseq/infrastructure/os_backend/contracts.py` と両 backend

- `OsBackend` に `platform_key: str` を足す（Windows = `"win32"`・Mac = `"darwin"`。値は `sys.platform` の語に揃える）。既定値を置くなら `"win32"`（今の `default_profile` と同じ流儀）だが、**両 backend の `create_backend()` では明示して渡す**。

### `keyseq/presentation/help/third_party.py`

- `ThirdPartyEntry` に `platforms: tuple[str, ...] = ()` を足す（空 = 両 OS）。
- `_parse_entries`: 必須キーは今の 4 つのまま、任意キー `platforms` だけを許す（`required <= set(item) <= required | {"platforms"}`・それ以外の余分なキーは今どおりエラー）。`platforms` は空でない文字列の配列で、値は `"win32"` / `"darwin"` のどちらか（重複は不可。許す値の組は表の検証のためだけの定数で、OS を足すときはここを直す）。検証後に **tuple へ変換して** `ThirdPartyEntry` に渡す（frozen の dataclass を hashable に保つ・起票レビュー L1）。違反は既存と同じ形の `ValueError`。文言キーは `help.third_party.platforms_invalid`（`index` を差し込む）を ja / en の両方に足す（`ui_terms.md` に従う・既存の `help.third_party.*` の並び）。
- `load_third_party(directory=None, *, platform: str | None = None)`: `platform` が None なら `get_backend().platform_key` を使い、`entry.platforms` が空か `platform` を含む行だけを返す（順は表の順）。
- `license_window.py` の呼び出し（`:40`）は変えない（既定で実行中の OS）。

### `keyseq/presentation/help/content/third_party/third_party.json`

- `keyboard`・`Python`・`Tcl`・`Tk` の行に `"platforms": ["win32"]` を足す（今の版は Windows の版）。他の 10 行は両 OS のまま。行の順・版・文書は変えない。

### テスト

- `tests/test_third_party.py`:
  - 件数・名前の順の検査を OS ごとにする: `platform="win32"` で今の 14 行（今の順）。`platform="darwin"` で `keyboard`・`Python`・`Tcl`・`Tk` を除いた 10 行（task_13b で Mac の行を足したら更新する旨をコメントに）。
  - ファイル名の一意性は **OS ごと**に見る（Mac の行が同じ文書を指せるように）。
  - 版の照合（ライブラリ・Python / Tcl / Tk）は**実行中の OS**（`load_third_party()` の既定）の行だけを対象にする。実行中の OS に Python / Tcl / Tk の行が無いときは `skipTest`（Mac で task_13b までの間）。
  - `platforms` の検査（未知の値・空の配列・文字列でない・余分なキー）のエラーのケースを足す。
  - `platform` を明示したフィルタ（両 OS）を同じ環境で検証する（暫定 57 v0.22 の Codex 再レビューの残りの確認: 「両 OS のフィルタを同じ環境で検証する」）。
- `tests/test_os_backend_contracts.py`: 両 backend の `platform_key`。
- `tests_ui/test_help_window.py:252`: `content.count(" — ") == 14` の固定値を `len(notices)`（実行中の OS の行の数）に直す（Mac では 10 行になり task_13b までの間に落ちるため・起票レビュー M1）。
- `tests/test_os_backend_contracts.py:85-92`: `OsBackend` のフィールド名の完全一致の一覧に `platform_key` を足し、既存の位置引数の構築（`:93`・`:199`）で既定値 `"win32"` になることを検査する（起票レビュー M2）。`platform_key` は**既定値つきで末尾**に足す。

### 文書

- `instructions/common/codebase_map.md`: `third_party.py`（OS で絞る）・`OsBackend.platform_key` を追従。
- `instructions/phase/75_mac_support/mac_test_baseline.md:37`: `test_third_party` の失敗 1 の解消先を「task_13a で Python / Tcl / Tk の照合が skip に・task_13b で Mac の行を足して照合」に追従（起票レビュー L6）。

## 設計メモ / 制約

- OS の判定は `os_backend/__init__.py` の 1 か所（§3.1）のまま。presentation は `get_backend().platform_key` を読むだけ（`sys.platform` を書かない・AST の境界テストが見る）。
- `platforms` を省いた行 = 両 OS（今の表の書き方を壊さない）。

## 読むファイル

- `keyseq/presentation/help/third_party.py`（全体）
- `keyseq/presentation/help/license_window.py:30-50`
- `keyseq/presentation/help/content/third_party/third_party.json`（全体）
- `keyseq/infrastructure/os_backend/contracts.py:125-145`・`windows/backend.py:118-130`・`macos/backend.py:780-792`
- `tests/test_third_party.py`（全体）・`tests_ui/test_help_window.py`（`load_third_party` を使う箇所のみ）
- `instructions/history/57_mac_support.md` §6.3

## 含まない

- Mac の行（`pyobjc` の各パッケージ・Mac の Python / Tcl / Tk の版と文書）・Mac の `test_third_party` の解消 → task_13b
- PyInstaller の行（ブートローダの例外・Apache-2.0）・依存のソースの同梱・README → task_13
- ライセンスの窓の見た目の変更

## 確認

- Windows（`..\..\..\.venv\Scripts\python.exe`）:
  - `-m compileall -q keyseq tests tests_ui` が clean
  - `-m unittest discover -s tests` が失敗 0（今の基準 2202 件 + 追加分）
  - `-m tests.smoke_app` が pass
  - tests_ui を 1 本ずつ: `test_help_window`・`test_ui_language` が失敗 0
- Mac は task_13b でまとめて確認する（task_13b までの間、Mac の `test_third_party` の Python / Tcl / Tk の照合は skip になる）。

## 完了条件

- 上記の確認が pass・**reviewer 採用**。
- 実機目視: Windows でヘルプのライセンスの窓に今と同じ 14 行が出ること（ユーザー）。
