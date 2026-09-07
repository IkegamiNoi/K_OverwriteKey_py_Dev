# task_07b_review_fixes

## 目的

**task_07 の二次レビュー 2 本（`deep-reviewer` / `codex-reviewer`）で採用が確定した 7 件を修正する**。
根拠は `integration_result.md` §3-3 の **A-1〜A-7**（ユーザー確定 2026-09-07）。

- **レイヤ制約**: **application（`orphan_scan.py` / `reference_scan.py` / `quarantine.py` /
  `quarantine_manage.py`）+ presentation（表示ラベルとダイアログ文言 1 行）**。
  domain / infrastructure は不変。**スキーマ不変**（`config.json` / `manifest.json` のキーを変えない）。
- **A-1 と A-2 は §4-A の受容前提を守るための修正**（「警告は必ず出る」「戻せない隔離物を残さない」）。
- **B 群（仕様判断が要るもの）はこのタスクでやらない**。task_08 が担当する。

## 対象範囲

### 1. A-1: 参照側の symlink を無警告で落とさない

**現状**: `keyseq/application/config_service/orphan_scan.py:150` の
`if os.path.islink(absolute_path) or not os.path.isfile(absolute_path): continue` は、
`_list_json_files` が**参照側（`:138`）と候補側（`:171`）の両方から呼ばれる**ため、
参照側でも無記録で skip する。結果、**その親が参照していた子が警告なしに孤児候補になる**。

**修正**:

- `keyseq/application/config_service/reference_scan.py` へ理由コードを追加する:
  ```python
  SOURCE_REDIRECTED = "redirected"
  ```
- `_list_json_files` に**任意の収集先**を渡せるようにし、**参照側から呼ぶときだけ**
  skip した項目を `(stored 表記のパス, SOURCE_REDIRECTED)` として記録する。
  **候補側の呼び出し（`:171`）の振る舞いは変えない**（無記録の skip のまま。
  候補側の skip は「隔離しない」= 安全側のため）。
- 記録先は既存の **`unreadable_sources`**（`tuple[tuple[str, str], ...]`）。
  **新しい報告チャネルを作らない**（`ScanResult` / `OrphanScanResult` のフィールドを増やさない）。
- `keyseq/presentation/orphan_sweep_text.py` の `_SOURCE_REASON_LABELS` へ日本語ラベルを追加:
  `SOURCE_REDIRECTED: "リンク / ジャンクションのため参照側として読みませんでした"`。

**根拠**: §3-5 の「次の 4 つは**握りつぶさず、結果に必ず出す**」と、
§4-A が受容した前提（**警告が必ず出るのでユーザーが最終判断できる**）。

### 2. A-2: 隔離ルートがリダイレクトされていたら隔離を拒否する

**現状**: 書き込み側 `keyseq/application/config_service/quarantine.py:222` の
`os.makedirs(unit_dir, exist_ok=False)` は隔離ルートのリンク / ジャンクションを**辿る**。
一方、読み出し側 `quarantine_manage.py:122` は `_is_redirected(root)` で**空タプルを返す**。
そのため**隔離は成功と報告されるのに、管理ダイアログから復元も削除もできない**状態が作れる。

**修正**:

- `quarantine.py` へ中止理由を追加する:
  ```python
  QUARANTINE_ROOT_REDIRECTED = "quarantine_root_redirected"
  ```
- **マニフェストを書く前・ディレクトリを作る前**に隔離ルートを検証し、
  **リダイレクトされていたら 1 件も動かさずに中止**する（`QUARANTINE_UNIT_DIR_FAILED` と同じ
  中止経路に載せる）。**隔離ルートが存在しない場合は従来どおり作成してよい**
  （遅延作成は §3-6 の規定）。
- 判定は `quarantine_manage._is_redirected` と**同じ基準**にする
  （`os.path.islink` または `normcase(realpath) != normcase(abspath)`）。
  A-7 で共通化する `is_real_path_within` とは別の判定なので混同しないこと。
- `orphan_sweep_text.py` の `_QUARANTINE_REASON_LABELS` へ日本語ラベルを追加:
  `QUARANTINE_ROOT_REDIRECTED: "隔離ルートがリンク / ジャンクションのため中止しました"`。

**採らない案**: 管理側でリダイレクトされたルートを許容する
（`_is_redirected` を外す）。**リンクを辿らない方針（task_05b）を崩すため不採用**。

### 3. A-3: ディレクトリ列挙の失敗を握りつぶさない

**現状**: `orphan_scan.py:146` の `os.listdir(resolved_dir)` に例外処理が無く、
`PermissionError` 等が `scan_orphans` を素通りして **Tk コールバックのトレースバック**になる
（結果が 1 つも出ない）。走査ディレクトリは **config 外を指してよい**仕様（§3-2）なので現実的。

**修正**:

- `_list_json_files` の列挙を `try` / `except OSError` で囲む。
- **参照側**（`:138` 経由）は `(stored 表記のディレクトリパス, SOURCE_DIRECTORY_UNREADABLE)` を
  `unreadable_sources` へ記録して**継続**する。
  `reference_scan.py` へ `SOURCE_DIRECTORY_UNREADABLE = "directory_unreadable"` を追加し、
  `_SOURCE_REASON_LABELS` へ
  `"ディレクトリを読み取れませんでした"` を追加する。
- **候補側**（`:171`）は**空リストを返して継続**する（候補が出ない = 隔離されない = 安全側。
  報告チャネルは増やさない）。
- **例外を握り潰さない**（理由コードへ落とすのは可。`except: pass` は不可）。

**task_08 への申し送り**: §3-5 の 4 カテゴリに「**読めなかった走査ディレクトリ**」が無い。
本タスクは §3-5 の「握りつぶさない」原則に沿って `unreadable_sources` へ寄せるが、
**条文の追記は task_08 でユーザーが判断する**。

### 4. A-4: 既定ディレクトリの不在を「見つからなかった指定ディレクトリ」に混ぜない

**現状**: `orphan_scan.py:118` が既定ディレクトリ `user/keymap_sets` を
`_scan_source_directory` に通すため、不在時に `:136` で `missing_dirs` へ積まれる。
§3-5-1 / §2 の「見つからなかった指定ディレクトリ」は**ユーザー指定ディレクトリ**の規定であり、
既定ディレクトリは対象外。表記も `\` 区切りの絶対パスで §5.7 の stored 表記から外れる。

**修正**: **既定ディレクトリは `missing_dirs` へ積まない**（不在なら候補 0 件として継続）。
`_scan_source_directory` に `missing_dirs=None` を許すか、既定ディレクトリだけ
`_list_json_files` を直接呼ぶ。**ユーザー指定ディレクトリの挙動は変えない**。

### 5. A-5: 管理ダイアログのヘッダを復元専用でなくする

`keyseq/presentation/dialogs/quarantine_manage_dialog.py:30` の
`"復元する実行単位を選択してください。"` を、**復元と削除の両方に合う文言**へ変える
（例: `"実行単位を選択してください。"`）。**これ以外の変更をしない**
（レイアウト・既存の属性名・ボタンラベルは維持）。

### 6. A-6: `manifest.json.tmp` の残骸で実行単位が片付かなくなるのを防ぐ

**現状**: 移動中のマニフェスト更新（`quarantine.py:274` 付近）が失敗すると `.tmp` が残る。
`_discard_manifest_tmp` は `_prepare_unit_dir`（`:227-231`）でしか呼ばれない。
`quarantine_manage.py:176-192` の `_empty_directories` は `manifest.json` 以外のファイルが
1 つでもあれば `None` を返すため、`_cleanup_unit` が常に False になり、
**§3-7 の MUST「全件が戻った実行単位は削除する」が永久に満たされない**。

**修正**: どちらか一方（実装者が選ぶ。**両方はやらない**）。

- (a) `_apply_moves` 側でもマニフェスト更新失敗時に `.tmp` を best-effort で除去する。
- (b) `_empty_directories` の後始末で `manifest.json.tmp` を**無視する**
  （`manifest.json` と同様に片付け対象として扱う）。

**まず現状を実測で確認すること**（`.tmp` が本当に残るか）。残らないなら**修正せず報告する**。

### 7. A-7: `is_real_path_within` の二重実装を 1 つに寄せる

`orphan_scan.py:206` の `_is_real_path_within` と `quarantine.py:284` の
`is_real_path_within` が**同一実装**。片方だけ直すと境界判定が割れる。

**修正**: **`quarantine.py:284` の `is_real_path_within` に寄せ**、
`orphan_scan.py` は `quarantine` から import して使う（`quarantine_manage.py` が既にそうしている）。
`orphan_scan.py:206` の重複定義は**削除する**（互換のための別名を残さない。
`.claude/rules/file_organization_rules.md`「恒久互換レイヤー禁止」）。
**循環 import にならないこと**を確認する（`quarantine.py` は `orphan_scan` を import していないこと）。

### 設計メモ / 制約

- **B 群（task_08 の仕様判断）に手を出さない**: 削除の部分失敗（B-1）/ presentation からの
  直 import（B-2）/ §3-12 追記（B-3）/ `codebase_map.md`・`phase.md`（B-4）。
- **受容済みの事項を蒸し返さない**: §3-12-5（壊れた親）/ §3-12-6・§3-12-7（削除の TOCTOU）/
  検証④のみ上書き可（v0.5）/ ゼロ埋め連番は拒否しない。
- **既存の報告チャネル（`ScanResult` / `OrphanScanResult` / `QuarantineResult` の
  フィールド構成）を増やさない**。理由コードの追加で表現する。
- 例外を握り潰さない。関数はおおむね 30 行以内・ファイルは 300 行以内を目安にする。
- **表示文言の生成は presentation の純関数のまま**（application に表示都合を持ち込まない）。

## 含まない

- **B-1 削除の部分失敗の扱い**（§3-8 の条項と実装の非対称）= **task_08**（条項変更はユーザー承認必須）。
- **B-2 §3-11 の直 import 違反**の是正 = **task_08**。
- **B-3 §3-12 への追記 3 件**（一覧に出ない残骸 / 削除経路の `_is_redirected` 非対称 /
  空隔離ルートの後始末の非対称）= **task_08**。
- **B-4 `codebase_map.md` の全面更新 / `phase.md` の v0.6 追随** = **task_08**。
- **C 群（保留・除外）**: UI スレッドのブロック / `_is_keymap_set` の判定キー /
  警告のパス表記 / 空の実行単位 / `_save_before_sweep` の分岐重複 /
  Python の最低バージョン床 / `OrphanSweepDialog.destroy` の二重呼び出し。
- **正本 `spec_detail/` の改訂** = **task_08**。
- **実機目視** = **task_07 の M1〜M8**（[manual_check.md](../manual_check.md)）。

## 確認

`.venv` の python で実行する（worktree ルートから）。

```
..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui
..\..\..\.venv\Scripts\python.exe -m tests.smoke_app
```

**単体テストの項目**（`tests/test_orphan_scan.py` / `tests/test_reference_scan.py` /
`tests/test_quarantine.py` / `tests/test_orphan_sweep_text.py` へ追記）:

1. **A-1**: 参照側ディレクトリに **symlink / ジャンクションの keymap_set** があると、
   `unreadable_sources` へ `(パス, SOURCE_REDIRECTED)` が記録される。
   **その親が参照していた子は孤児候補になるが、警告が出る**ことを両方確認する
   （symlink を作れない環境では junction で、それも無理なら `skipTest`）。
2. **A-1**: **候補側**の symlink は**従来どおり無記録で skip**され、
   `unreadable_sources` に混ざらない（安全側の挙動を変えていないこと）。
3. **A-2**: 隔離ルートが**リダイレクトされている**状態で隔離を実行すると、
   **1 件も移動せず** `QUARANTINE_ROOT_REDIRECTED` で中止する。
   **リンク先に何も書かれていない**ことを実体で確認する。
4. **A-2**: 隔離ルートが**存在しない**通常ケースでは**従来どおり作成されて隔離できる**
   （遅延作成を壊していないこと）。
5. **A-3**: `os.listdir` が `PermissionError` を送出する状況で、
   **参照側**は `(ディレクトリ, SOURCE_DIRECTORY_UNREADABLE)` を記録して**継続**する
   （`patch` で `OSError` を起こす）。**例外が外へ漏れない**。
6. **A-3**: 同じ状況で**候補側**は**空として継続**し、`unreadable_sources` に混ざらない。
7. **A-4**: 既定ディレクトリ `user/keymap_sets` が**存在しない**とき、
   `missing_scan_dirs` に**含まれない**（ユーザー指定ディレクトリの不在は**従来どおり含まれる**）。
8. **A-6**: `manifest.json.tmp` が残った実行単位でも、**全件復元すれば実行単位が片付く**
   （§3-7 の MUST）。**修正前は片付かないこと**を確認したうえでテストを書く。
9. **A-7**: `orphan_scan` の境界判定が `quarantine.is_real_path_within` と**同一の結果**を返す
   （重複定義が消えていること。`orphan_scan._is_real_path_within` が存在しないこと）。
10. **表示**: 追加した 3 つの理由コード
    （`SOURCE_REDIRECTED` / `SOURCE_DIRECTORY_UNREADABLE` / `QUARANTINE_ROOT_REDIRECTED`）が
    **日本語ラベルで出る**。**未知コードは従来どおりコードのまま**出る。

**UI フローの項目**（`tests_ui/test_quarantine_manage_flow.py` へ追記）:

11. **A-5**: 管理ダイアログのヘッダが**復元専用の文言でない**
    （既存の `test_list_buttons_modal_and_no_selection` 等を壊さないこと）。

**退行の基準**: `tests` は **399 → 増加**、`tests_ui` は **287 → 増加**（どちらも減らさない）。
skip は **5 件（Windows の symlink 権限不足）から増やさない**
（増える場合は理由を報告する）。smoke pass。
実行後に worktree ルートへ **`user/` も `quarantine/` も生成されていない**こと。
**既存テストの期待値変更が必要になったら、理由を報告に含める**
（A-4 は `test_missing_scan_dirs_keep_input_spelling_and_other_scans_continue` に、
A-7 は `orphan_scan` の import に影響し得る）。

## 完了条件

- 上記「確認」がすべて pass（実測は **`verifier`**。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（5 観点）。特に:
  - **A-1〜A-7 以外を変えていない**か（B 群・C 群に手を出していないか）。
  - **候補側の安全側の挙動（無記録 skip・空として継続）を変えていない**か。
  - **報告チャネル（dataclass のフィールド）を増やしていない**か。
  - **A-2 が遅延作成（隔離ルートが無ければ作る）を壊していない**か。
  - **A-7 で循環 import が生まれていない**か・**互換の別名を残していない**か。
- **敵対的レビューは不要**（不可逆操作の新設ではないため。task_06b とは扱いが異なる）。
- **実機目視は task_07 の M1〜M8 でまとめて実施**する（本タスク単独では行わない）。
  ただし **A-2 の確認のため、M1 の前に「`config/quarantine` をジャンクションにした状態で
  隔離を実行すると中止表示が出る」を目視観点へ追加**する。
