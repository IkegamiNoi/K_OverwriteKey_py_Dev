# task_13c_windows_spec_sources

## 目的

Windows の `.spec`（`packaging/windows/keyseq.spec`）の `sources/` の作り方を、task_13b で Mac の `.spec` に入れた修正と同じにする（暫定 57 §6.3「対応するソースの同梱」= 同梱した版のソースのアーカイブを入れる）。

- 今の Windows の `.spec` は `packaging/sources/` を丸ごと `dist/keyseq/sources/` へ重ねてコピーする（`copytree(..., dirs_exist_ok=True)`）。前のビルドの古い版や、関係のないファイル（`.sha256` 等）が残る・入る。
- 照合が前方一致（`<名前>-<版>.` で始まる）なので、`.sha256` だけがあってもビルドが通る。

## 対象範囲（`packaging/windows/keyseq.spec` の `collect_distribution()` だけ）

- 照合をファイル名全体にする: `<package>-<version>.tar.gz` か `<package>-<version>.zip`（大文字小文字は区別しない）。どちらも無ければ今と同じ `FileNotFoundError` で止める。
- `dist/keyseq/sources/` を毎回消してから作り直し、照合で選んだアーカイブだけをコピーする（`shutil.copy2`）。
- 手本は `packaging/macos/keyseq.spec` の `collect_distribution()`（`SOURCE_EXTENSIONS`・`selected`・`rmtree` → `makedirs` → `copy2`）。置き場所は Windows の今のまま（`dist/keyseq/sources/`・README も `dist/keyseq/README.txt` のまま）。

## 対象外

- Mac の `.spec`・README（`packaging/README.md`・`README_dist.txt`）・`third_party.json`・アプリのコード。
- 共通部品への切り出し（task_13b の判断どおり 2 つの `.spec` は別々に持つ）。
- テストの追加（`.spec` は PyInstaller の中でしか動かないため、ビルドの実測で確かめる）。

## 確認

verifier（Windows）で次を実測する。

1. `packaging/sources/` に 2 つの sdist（MouseInfo-0.1.3.tar.gz・pynput-1.8.2.tar.gz）と、無関係なファイル（例 `dummy.sha256`）を置き、`dist/keyseq/sources/` に古いファイル（例 `old-0.0.1.tar.gz`）を置いた状態でビルドする → 成功し、`dist/keyseq/sources/` には 2 つの sdist だけがある。
2. `packaging/sources/` に `pynput-1.8.2.tar.gz.sha256` だけ（pynput の本体なし）ではビルドが `Missing source archive` で止まる（確認後に戻す）。
3. 1 のビルドの exe が起動する（smoke 相当・起動して終了）。

## 完了条件

確認 1〜3 が通り、reviewer の別視点レビューを通す。
