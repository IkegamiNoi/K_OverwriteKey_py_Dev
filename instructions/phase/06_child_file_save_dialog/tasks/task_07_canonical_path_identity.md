# task_07_canonical_path_identity

## 目的

パスの同一性判定を **canonical identity**（config_root から解決 → `normpath` → `normcase`）へ統一し、
Windows でパス文字列の大文字小文字が食い違ったときに config_root 内のパスが「外」と誤判定される
実バグを解消する（暫定仕様 05 **v0.3-B** / §6 末尾・受入条件 13）。

現象は素の文字列一致（`os.path.commonpath([p, root]) == root`）に起因し、次のカスケードを起こす:
①デフォルト配下なのに「デフォルト外に保存されます」確認が出る → ②`_parent_refs` と起動設定が
相対化されず絶対パスで記録される → ③その絶対パスが `source_path` に載ると次回保存で既定領域判定が
外れ、新規シーケンスが `user/sequences/` ではなく `user/trigger_sets/sequences/` へ落ちる。
（2026-07-29 の実機で発生。発生経路は VS Code の ▶ 実行がドライブ文字を小文字 `c:\` で渡すこと。）

- レイヤ制約: **application（`config_service.py`）+ presentation（`config_paths.py` /
  `config_io/child_save_rows.py`）限定**。domain 不変・**スキーマ不変**。
- **JSON へ保存する文字列の表記は変えない**（config_root 内=相対 / 外=絶対。暫定仕様 §4）。
  canonical identity は**比較専用**であり、保存値・戻り値・ダイアログ表示文字列に混入させない。

## 対象範囲（比較ロジック限定・保存表記は不変）

### 1. `keyseq/application/config_service.py` — canonical identity ヘルパーの新設

公開メソッドを 2 本追加する（既存の `to_config_relative_or_absolute` /
`_normalize_path_separators` と同じ場所＝ `ConfigService` に置く。**新規モジュールは作らない**）。

```python
def canonical_path(self, path: str, config_root: str) -> str:
    """比較専用の正規形。相対は config_root から解決し、normpath → normcase を適用する。"""

def is_path_within(self, path: str, ancestor_dir: str, config_root: str = "") -> bool:
    """path が ancestor_dir 配下（同一パスを含む）かを canonical identity で判定する。"""
```

- `canonical_path`: 空文字は空文字を返す。相対パスは `config_root` から解決（`config_root` が
  空なら `os.path.abspath` の既定＝ cwd 解決に委ねる）。`os.path.abspath` → `os.path.normpath` →
  `os.path.normcase` の順。**戻り値を保存・表示に使わない**ことを docstring に明記する。
- `is_path_within`: 双方を `canonical_path` した上で `os.path.commonpath` を使う
  （`startswith` による前方一致は `c:\configx` が `c:\config` 配下と誤判定されるため**使わない**）。
  `commonpath` の例外（ドライブ違い等）は現行どおり握って `False` を返す。

### 2. `keyseq/application/config_service.py` — 既存判定の置き換え

| 箇所 | 現在 | 変更後 |
|---|---|---|
| `to_config_relative_or_absolute`（:1485-1494） | `commonpath(...) == root` | 内外判定を `is_path_within` へ。**相対化は元の絶対パスから `os.path.relpath` で作る**（canonical 形から作らない＝保存表記に `normcase` を持ち込まない） |
| `_is_default_trigger_set_area`（:1292-1297） | 同上 | `is_path_within(trigger_set_path, os.path.join(config_root, "user", "trigger_sets"), config_root)` |
| `_merge_parent_ref`（:1520-1540） | `_normalize_path_separators` で重複判定 | `canonical_path` で重複判定（**絶対で記録済みの既存参照と、相対表記の同一パスを二重登録しない**）。**追加する値は現行どおり `to_config_relative_or_absolute` の戻り値** |

### 3. `keyseq/application/config_service.py` — 保存先の重複検出（衝突キー）

`used_relative_paths` / `used_paths` は現在 `_normalize_path_separators`（区切り文字のみ）を
キーにしているため、ケース違いの `source_path` を別ファイル扱いし、**同一ファイルへ複数 payload を
順に書く**余地が残る。**衝突キーを `canonical_path` に変える**。

- 対象: `_build_keymap_payloads` の `used_relative_paths`（:1042-1050 付近）/
  `_resolve_sequence_save_path` の `used_paths`（:1227-1241）/
  `_allocate_unique_relative_path`（:1299-1315）/ `_allocate_unique_absolute_path`（:1317-1335）
- **戻り値（＝保存に使う文字列）は現行のまま**。集合に入れる値だけを canonical へ変える。
  `_allocate_unique_relative_path` は `config_root` を受け取っていないため**引数を追加**し、
  呼び出し側を合わせる（呼び出しは `_resolve_sequence_save_path` / `_allocate_unique_keymap_path` 経由）。

### 4. `keyseq/presentation/config_paths.py` — 内外判定の委譲

- `is_within_config_root`（:97-101）と `is_within_legacy_settings`（:54-60）を
  `self._config_service.is_path_within(...)` へ委譲する（自前の `commonpath` 比較を消す）。
  空文字の扱い（`is_within_legacy_settings("")` は `False`）は現行を維持する。

### 5. `keyseq/presentation/controllers/config_io/child_save_rows.py` — 所有判定（§5）

- `judge_share_state` / `_stored_parent_refs` / `_stored_parent_path` の比較を
  `_normalize_separators`（区切り文字のみ）から **canonical identity** へ変える。
  既存 JSON に**絶対パスで記録済みの参照元**と、現在の上位（相対表記）が**同一と判定される**こと。
- `ChildSaveRow.target_path` / `share_text` など**表示用の値は変えない**。

### 6. テスト

| ファイル | 内容 |
|---|---|
| `tests/test_config_service.py` | `canonical_path` / `is_path_within` の単体（相対解決・`normcase`・`c:\configx` を `c:\config` 配下と誤判定しない・ドライブ違いで `False`）。**プラットフォーム非依存**として必ず実行される |
| `tests/test_config_service.py` | **Windows 限定の統合テスト**（`@unittest.skipUnless(sys.platform == "win32", ...)`）。同一 config_root を**大文字小文字だけ変えた 2 表記**で通し、①内外判定 ②起動設定 `keymap_set_path` と `_parent_refs` が相対で記録される ③trigger_set の既定領域判定 ④`_parent_refs` の重複排除（**絶対で記録済みの既存参照を含む**）⑤新規シーケンスが `user/sequences/` へ配置、をすべて確認する（受入条件 13） |
| `tests/test_config_paths.py` | `is_within_config_root` / `is_within_legacy_settings` がケース違いでも正しく判定する |
| `tests/test_child_save_rows.py` | 絶対で記録済みの `_parent_refs` と相対表記の現在の上位が `SHARE_SOLE` と判定される（従来は `SHARE_OTHER_PARENT` へ落ちていた） |

### 設計メモ / 制約

- **canonical identity を保存値へ混ぜないこと**が最大の落とし穴。`normcase` を通した文字列が
  `_parent_refs` / `keymap_set.json` の索引 / 起動設定 / ダイアログ表示へ出たら不合格。
  比較する直前に作り、比較が終わったら捨てる。
- 既存の `os.path.normcase(os.path.abspath(...))` 比較（`keymap_set_io._trigger_target_changed` /
  `config_service._sequence_save_path_changed`）は**既に正しい**。canonical ヘルパーへ寄せてよいが、
  **挙動が変わらないこと**を確認する（寄せるかどうかは実装者判断。無理に触らなくてよい）。
- 既に絶対パスで書かれてしまった既存 JSON（実機の `config/` に存在）は**移行処理を書かない**。
  比較時に解決して照合すれば整合するため、次回保存で自然に相対へ戻る。
- `config_service.py` は 1300 行超だが、**このタスクでは分割しない**（フェーズ末の `/refactor_check` で判定）。

## 含まない

- **一覧再表示の廃止と再計算先の上書き確認（v0.3-A / A2）— task_08**。
  本タスクでは `_collect_child_save_plan` の while ループに手を入れない。
- **一覧ダイアログのレイアウト（v0.3-C）— task_09**。
- **正本 `spec_detail/` への反映 — task_10**（本タスクでは正本を編集しない）。
- レガシー `settings/` 経路の保存先フォールバック（[idea_09](../../../backlog/idea_09_legacy_settings_save_path_fallback.md)）。
  `is_within_legacy_settings` は**判定方法のみ**を直し、フォールバック挙動は変えない。
- 参照元の掃除機能（idea_07）/ 孤児ファイル検出 / パス移行スクリプト。

## 確認

`.venv` の python で実行する（worktree ルートから `..\..\..\.venv\Scripts\python.exe`）。

1. `-m compileall -q keyseq main.py tests_ui` が clean
2. `-m unittest discover -s tests` が全 pass（新規テストを含む。現行 131 件 + 追加分）
3. `-m unittest discover -s tests_ui` が全 pass（現行 107 件）
4. `-m tests.smoke_app` が pass
5. **受入条件 13 の Windows 統合テストが pass**（①〜⑤すべて）
6. 既存の特性テスト（`tests_ui/test_config_io_characterization*.py` / `tests/test_config_service.py` の
   バイト列比較）を**緩めずに** pass すること。保存 JSON のバイト列が変わっていないこと
7. `grep` で `commonpath` の素の文字列一致（`== ` 比較）が `keyseq/` に残っていないこと

## 完了条件

- 上記確認 1〜7 が pass・**reviewer 採用**。
- 実機目視は**本タスクでは行わない**（task_09 完了後に task_10 の前でまとめて実施する）。
