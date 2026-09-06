# task_05b_quarantine_hardening

## 目的

**task_05（隔離）に対する敵対的レビュー 2 本の指摘を反映し、可逆性と誤隔離の穴を塞ぐ**。
`deep-reviewer`（実測込み）と `codex-adversarial-reviewer` の指摘のうち、ユーザーが採用を決めたものを実装する。

- **枝番タスク**（task_05 の追補）。**新機能を足さない**。task_06 の先取りもしない。
- **レイヤ制約**: **application が主**（`orphan_scan.py` / `quarantine.py`）+
  **presentation は表示文言の是正のみ**（`orphan_sweep_text.py`）。domain / infrastructure は不変。**スキーマ不変**。
- 由来: 暫定仕様 10 **§3-2**（走査はシンボリックリンクを辿らない）/ **§3-4**（候補側は config 配下のみ）/
  **§3-5**（警告を提示したうえで実行）/ **§3-6**（隔離）+ **受け入れ条件 16**。

### 裏取り済みの事実（実測。前提にしてよい）

- `service.canonical_path` は `normcase(normpath(abspath(...)))` のみで **`realpath` を通さない**
  （`config_service/__init__.py:730`）。したがって**字句上の境界判定はジャンクションを見抜けない**。
- **Windows のジャンクションは `os.path.islink()` が `False`** を返す（実測）。
  既存の `islink` スキップ（`orphan_scan.py` の `_list_json_files`）では**防げない**。
- **`os.path.realpath()` はジャンクションを解決する**（実測）。
  `commonpath` による境界判定が正しく `False` になることを確認済み。

## 対象範囲

### 1. `keyseq/application/config_service/orphan_scan.py`（候補列挙の境界検証）

**候補側の列挙でのみ**、実体（realpath）が config_root 配下であることを検証する。

- **`_collect_entries`（候補側）にだけ適用する**。
  **`_list_json_files` そのものを変えてはならない** — 同関数は**参照側（`scan_dirs`）でも使われ、
  参照側は config 外を指してよい**（§3-2-4。ユーザー指定ディレクトリは任意の場所を許す）。
  ここを取り違えると**ユーザー指定ディレクトリの走査が壊れる**。
- 判定は private ヘルパへ切り出す（例）:

  ```python
  def _is_real_path_within(path: str, root: str) -> bool:
      """realpath で実体解決したうえで root 配下かを判定する（ジャンクション対策）。"""
  ```
  `os.path.normcase(os.path.realpath(...))` 同士を `os.path.commonpath` で比較する。
  例外（`OSError` / `ValueError`。ドライブ違いは `commonpath` が `ValueError`）は
  **`False`（＝配下でない）へ倒す**（安全側）。
- 実体が config_root の外に出るファイルは **`ORPHAN_EXCLUDED`** とする
  （`ORPHAN_CANDIDATE` にしない）。**件数として見えるようにし、無音で消さない**。
- **`ORPHAN_PROTECTED` / `ORPHAN_REFERENCED` の判定より後、形状検証より前**に評価する
  （保護・参照ありの表示は維持する。無駄な読み取りもしない）。

### 2. `keyseq/application/config_service/quarantine.py`（移動直前のガードと失敗経路）

**追加する定数**

```python
QUARANTINE_UNIT_DIR_FAILED = "unit_dir_failed"   # 実行単位ディレクトリを作れなかった
QUARANTINE_SOURCE_REJECTED = "source_rejected"   # 移動直前の検査で拒否した
```

**(a) 移動直前のガード**（Codex High #1 / High #2）— `_move_file` の中で、`shutil.move` の前に:

1. **通常ファイルであること**: `os.path.isfile(source)` が真、かつ `os.path.islink(source)` が偽。
   **ディレクトリ・リンク・不在は移動しない**。
2. **実体が config_root 配下であること**: 1 の `_is_real_path_within` 相当で検証する
   （`orphan_scan` の判定と**同じ規約**にする。共有したいなら `orphan_scan` の
   private ヘルパを使わず、**`quarantine.py` 側にも同等の private ヘルパを置く**
   か、`orphan_scan` 側を公開名にして使う。**どちらでもよいが規約を二重定義で食い違わせない**こと）。
3. 満たさないものは移動せず **`QUARANTINE_SOURCE_REJECTED`** を返し、
   マニフェストのそのエントリを `ENTRY_FAILED` にして継続する。
   **`config_root` を引数で受け取れるよう `_move_file` のシグネチャを変える**（現在は `move` だけ）。

**(b) 実行単位ディレクトリの作成失敗**（deep M-1）:
`os.makedirs(unit_dir)` を `try` で囲み、失敗したら**1 件も動かさず中止**して
`aborted_reason = QUARANTINE_UNIT_DIR_FAILED` を返す（**未捕捉例外で UI に何も出ない状態をなくす**）。

**(c) 実行単位の衝突を顕在化**（deep M-2・Codex は High へ引き上げ推奨）:
`os.makedirs(unit_dir, exist_ok=True)` を **`exist_ok=False`** にする。
`FileExistsError` は (b) と同じ中止経路（`QUARANTINE_UNIT_DIR_FAILED`）で扱う。
**既存の実行単位のマニフェストを後勝ちで上書きしない**ことが目的。

**(d) 中止時の `.tmp` 残骸を除去**（deep H-2）:
`_discard_empty_unit_dir` の前に、**`<manifest_path>.tmp` が在れば削除**する
（`JsonRepository.save_json` は `f"{path}.tmp"` へ書いてから `os.replace` する・`json_repository.py:17`）。
削除できなければディレクトリは残るが、**それ以上は追わない**（best-effort）。
目的は**「復元も削除もできない残骸」の発生源を塞ぐ**こと。

**(e) 再判定時の警告を結果へ通す**（Codex Medium）:
`_select_targets` が捨てている再判定結果の **`unreadable_sources` を `QuarantineResult` へ載せる**。
フィールドを 1 つ追加する:

```python
rescan_unreadable_sources: tuple[tuple[str, str], ...]
```

**実行を抑止しない**（§4-A。警告を出したうえで実行を許すのが確定事項）。**結果表示に出すだけ**。

### 3. `keyseq/presentation/orphan_sweep_text.py`（表示の是正）

**(a) マニフェスト書込み失敗を「移動できなかったファイル」と混ぜない**（deep M-3）。
`failed` のうち **`manifest_write_failed`** は別行にし、
**「隔離の記録が古い可能性があります」**という趣旨が伝わる文言にする
（移動自体は成功している場合があるため）。

**(b) 全件失敗で「隔離しました」と読ませない**（deep M-3）。
`moved` が 0 件で `failed` が 1 件以上のときは、**先頭の見出しを成功形にしない**。

**(c) 新しい理由コードのラベル**を追加する:
`QUARANTINE_UNIT_DIR_FAILED` / `QUARANTINE_SOURCE_REJECTED`。
**未知コードはコードのまま出す**既存方針を維持する。

**(d) 再判定時の警告**（`rescan_unreadable_sources`）が 1 件以上あれば、
**結果の先頭に**「隔離の直前にも読めない参照側があった」旨と件数・パス・理由を出す。

**(e) `ORPHAN_EXCLUDED` の見出し**を実態に合わせる。
現在は「形状検証で対象外」だが、**実体が config 外だったもの**も入るようになるため
**「対象外: {N} 件」**のように理由を限定しない表現へ変える（既存テストの追随が必要）。

### 4. テスト

- `tests/test_orphan_scan.py` — 候補側のジャンクション越えが `ORPHAN_EXCLUDED` になること。
  **参照側（`scan_dirs`）は config 外でも従来どおり走査できる**こと（**退行防止・重要**）。
- `tests/test_quarantine.py` — 下記「確認」の項目。
- `tests/test_orphan_sweep_text.py` — 表示の是正分。既存の「形状検証で対象外」を見る
  テストは新しい文言へ追随させる。
- **ジャンクションを作れない環境では該当テストを `skipTest` する**
  （`subprocess` で `cmd /c mklink /J` を実行し、失敗したら skip。CI や権限のない環境で落とさない）。

### 設計メモ / 制約

- **`_list_json_files` を変えない**。参照側と候補側で要求が違う（参照側は config 外可）。
- **`canonical_path` の仕様を変えない**（比較専用・保存表記へ影響させない。正本 §5.7）。
  realpath による境界検証は**別の判定として追加**する。
- 実体検証の例外は**すべて「配下でない」へ倒す**（安全側）。
- **§4-A を崩さない**: 警告は出すが**実行は抑止しない**。確認用 UI を作らない。
- **H-1（`planned` のまま実体は移動済み）は本タスクで実装修正しない**。
  **「復元は `state` ではなく実体の有無で判定する」を task_06 の設計判断として確定させる**
  （task_06 の定義に明記する。本タスクは対象外）。
- 例外を握り潰さない。関数はおおむね 30 行以内。

## 含まない

- **H-1 の実装修正**（上記のとおり task_06 の設計判断で吸収する）。
- **復元 / 削除・「隔離の管理…」メニュー** = **task_06**。
- **`dropped_paths` の stored 表記への正規化**（deep L-3・現状は件数表示のみで実害なし）= 見送り。
- **例外内容（errno / メッセージ）の保持**（deep L-2・既存コード全体の流儀）= 見送り。
- **§3-11 と「presentation から application の定数を import」の矛盾**（deep L-4）=
  **task_08 で正本反映時に判断**（本タスクでは触らない）。
- **多重起動そのものの防止**（アプリに単一起動の仕組みは無い）= スコープ外。(c) は顕在化のみ。
- 正本 `spec_detail/` の改訂 = **task_08**。

## 確認

`.venv` の python で実行する（worktree ルートから）。

```
..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui
..\..\..\.venv\Scripts\python.exe -m tests.smoke_app
```

**単体テストの項目**（実ファイルで検証する。ジャンクション不可なら該当項目のみ `skipTest`）:

1. **候補側の親がジャンクション**（`user/keymaps` → config 外）のとき、その配下の JSON が
   **`ORPHAN_EXCLUDED` になり `ORPHAN_CANDIDATE` にならない**。
2. **参照側（`scan_dirs`）が config 外を指していても従来どおり走査され**、
   そこの keymap_set から参照された子が `ORPHAN_REFERENCED` になる（**退行防止**）。
3. **移動直前のガード**: `presented_paths` と再判定を通過しても、移動時点で
   **ディレクトリに置き換わっていたら移動しない**（`QUARANTINE_SOURCE_REJECTED`）。
   **そのディレクトリの中身が巻き込まれていない**ことを実体で確認する。
4. **移動直前のガード**: 実体が config 外（ジャンクション経由）なら移動せず
   `QUARANTINE_SOURCE_REJECTED`。**リンク先の実ファイルが動いていない**ことを確認する。
5. **ガードで拒否されたエントリのマニフェスト状態が `failed`** になり、
   **他のエントリの移動は継続**する。
6. **実行単位ディレクトリの作成失敗**（`os.makedirs` を例外に差し替え）で
   **1 件も移動せず** `aborted_reason == QUARANTINE_UNIT_DIR_FAILED` を返す。
7. **既に同名の実行単位ディレクトリが在る**状態で `os.makedirs` が `FileExistsError` になったとき、
   **既存のマニフェストを上書きせず**中止する（`_allocate_unit_id` を patch して衝突を作る）。
8. **中止時に `manifest.json.tmp` が残っていても除去され**、
   **空になった実行単位ディレクトリと隔離ルートが残らない**（deep H-2 の再現ケース。
   `save_json` を「`.tmp` を作ってから例外」に差し替える）。
9. **再判定時の `unreadable_sources` が `QuarantineResult` に載る**。
   **かつ実行は抑止されない**（隔離は行われる。§4-A）。
10. 既存の不変条件が壊れていないこと（**回帰**）: マニフェスト先行書込み / 積集合への限定 /
    元ファイルを削除しない / 対象 0 件でディレクトリを作らない。

**表示の項目**（`tests/test_orphan_sweep_text.py`）:

11. `manifest_write_failed` が**「移動できなかったファイル」とは別行**に出て、
    **記録が古い可能性がある旨**が伝わる。
12. `moved` が 0 件で `failed` が 1 件以上のとき、**先頭が成功形の見出しにならない**。
13. `QUARANTINE_UNIT_DIR_FAILED` / `QUARANTINE_SOURCE_REJECTED` に日本語ラベルが付く。
    **未知コードはコードのまま**出る。
14. `rescan_unreadable_sources` が**結果の先頭**に件数・パス・理由付きで出る。
15. `ORPHAN_EXCLUDED` の見出しが**理由を形状検証に限定しない表現**になっている。

**退行の基準**: `tests` は **336 → 増加**、`tests_ui` は **268 → 増加**（どちらも減らさない・実測 2026-09-06）。
既存の `tests_ui/test_reference_cleanup_flow.py` 9 件 / `tests/test_reference_cleanup_text.py` 8 件は
**無変更で全 pass**。`tests/test_orphan_scan.py` 27 件は**表示・判定の変更に伴う最小限の修正のみ可**
（修正理由を報告に含める）。smoke pass。
実行後に**worktree ルートへ `user/` も `quarantine/` も生成されていない**ことを確認する。

## 完了条件

- 上記「確認」がすべて pass（実測は **`verifier`**。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（5 観点）。特に:
  - **`_list_json_files` を変えておらず、参照側の config 外走査が壊れていない**か（**最重要の退行**）。
  - 移動直前のガードが **`shutil.move` の前**にあり、ディレクトリ・リンク・config 外を**確実に弾く**か。
  - `exist_ok=False` 化で**既存の実行単位を上書きしない**ことが担保されているか。
  - **§4-A を崩していない**か（警告は出すが実行を抑止しない・確認 UI を作らない）。
  - task_06 の先取りが無いか。
- **実機目視は行わない**（task_07 でまとめて実施）。ただし task_07 の目視観点に
  **「`quarantine` を書込み不可にした状態での中止表示」**を含めること。
