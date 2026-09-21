# task_02_history_persistence

## 目的

履歴ファイル `config/keymap_set_history.json` の**永続化**を application に実装する
（暫定仕様 21 §3「データモデル」/ §4.2「積み方」/ §4.3「永続化の失敗」/ §4.4「読めないとき」/ §7）。
読込（不在と破損の区別・破損時の退避）・原子的書込・**記録の合流点**（`record`）までを担当する。

レイヤ制約: **application 限定**。presentation を参照しない。domain（task_01 の
`keyseq/domain/keymap_set_history.py`）は**呼ぶだけで変更しない**。
`config/config.json` のスキーマは不変（キーを足さない）。

## 対象範囲（application 限定・新規 1 ファイル + 既存 3 ファイルへの最小追記）

### keyseq/application/config_service/keymap_set_history.py（新規・本体）

`split_loading.py` と同じ **service 第 1 引数の関数群**として書く（`ConfigService` のメソッドではない）。

- `history_absolute_path(service, *, config_root: str) -> str`
  - `service.resolve_config_path(service.KEYMAP_SET_HISTORY_RELATIVE_PATH, config_root)` を返す。
- `load_history(service, *, config_root: str) -> tuple[dict[str, Any], str]`
  - 戻り値は `(正規化済み履歴, status)`。status は `contracts` の 3 定数のいずれか。
  - **ファイルが存在しない** → `(空履歴, HISTORY_OK)`。**このときファイルを作らない**（遅延作成）。
  - 存在して読めて **dict** → `(domain.normalize_history(raw), HISTORY_OK)`。
  - **存在するが読めない**（例外）**または dict でない** → §4.4 の退避を試みる:
    - 退避に成功 → `(空履歴, HISTORY_RECOVERED)`
    - 退避に失敗、または退避先の連番が尽きている → `(空履歴, HISTORY_READ_ONLY)`
- `save_history(service, history, *, config_root: str) -> tuple[bool, str]`
  - `domain.normalize_history` を通してから `service.repository.save_json` で書く（原子的置換）。
  - 成功 → `(True, "")`。失敗 → `(False, 失敗理由)`（例外を握りつぶさず `str(e)` を含める）。
- `record(service, path: str, *, config_root: str) -> tuple[bool, str]` — **記録の合流点**（§4.2 の手順）
  1. `load_history` する。status が `HISTORY_READ_ONLY` なら**何も書かず** `(False, 理由)` を返す。
  2. 保存表記 `stored = service.to_config_relative_or_absolute(path, config_root)` を作る。
     `path` が空（trim 後）なら `(False, 理由)` で何もしない。
  3. `domain.is_recent_head(history, stored, key_of=...)` が True なら
     **`save_json` を呼ばずに** `(True, "")` を返す（no-op。§4.2-3）。
  4. そうでなければ `domain.push_recent(...)` の結果を `save_history` して結果を返す。
  - **比較キー** `key_of` は `lambda p: service.canonical_path(p, config_root)`。

#### 退避の規定（§4.4）

- 退避先は履歴ファイルと**同じディレクトリ**の `keymap_set_history.broken.json`。
  既に存在する場合は `keymap_set_history.broken2.json`、`broken3`、`broken4`、`broken5` の順に探す。
- **`broken` 〜 `broken5` の 5 つがすべて埋まっていたら退避しない**（`HISTORY_READ_ONLY`）。
- 退避は `os.replace(履歴ファイル, 退避先)`。例外が出たら `HISTORY_READ_ONLY`。
- 退避後、履歴ファイルは**作り直さない**（次の記録で遅延作成される）。

### keyseq/application/config_service/contracts.py（既存・定数 3 つを追記）

```python
# keymap_set_history
HISTORY_OK = "ok"
HISTORY_RECOVERED = "recovered"
HISTORY_READ_ONLY = "read_only"
```

既存の定数群と同じ書式で、コメント見出し付きの位置に足す（dataclass は追加しない）。

### keyseq/application/config_service/\_\_init\_\_.py（既存・**委譲のみ**）

- クラス定数を 1 つ追加: `KEYMAP_SET_HISTORY_RELATIVE_PATH = "keymap_set_history.json"`
  （既存の `HOTKEY_PRESETS_RELATIVE_PATH` 等の並びへ。**`user/` を含めない** = config 直下）。
- 公開メソッド 3 本を追加。**いずれも 1〜3 行の委譲**とし、**ロジックを書かない**
  （同ファイルは 831 行で「新規ロジックを置かない」制約がある）:
  - `load_keymap_set_history(self, *, config_root)` → `keymap_set_history.load_history(self, ...)`
  - `save_keymap_set_history(self, history, *, config_root)` → `keymap_set_history.save_history(...)`
  - `record_keymap_set_history(self, path, *, config_root)` → `keymap_set_history.record(...)`
- import は既存の `split_loading` 等と同じ書式で追加する。

### tests/test_config_service_contracts.py（既存・2 箇所）

- `INTERNAL_MODULE_NAMES`（`:14-18`）へ **`"keymap_set_history"` を追加**する。
  `:172-179` が実ファイル集合との**完全一致を assert** しているため、**追加しないと確実に赤**になる。
- **`:160` の `self.assertEqual(len(constant_names), 34)` を `37` へ更新する**。
  `contracts.py` の大文字定数は現在ちょうど **34 個**で、本タスクで 3 つ足すため
  **更新しないと確実に赤**になる（`type_names` の 9 は変えない = dataclass を追加しないため）。
  この 2 箇所以外は変更しない。

### tests/test_config_service.py（既存・テスト追加）

新しい TestCase クラスを 1 つ足す（既存クラスへ混ぜない）。**最低限、次を固定する**:

- **不在**: 履歴ファイルが無いとき `load_history` が空履歴 + `HISTORY_OK` を返し、
  **ファイルが作られない**こと。
- **正常**: 書いた内容が `normalize_history` を通って読み戻せること。
- **破損**: 壊れた JSON（例: `"{"` だけ）のとき **`keymap_set_history.broken.json` が作られ、
  元のバイト列がそのまま保たれる**こと / status が `HISTORY_RECOVERED` / 履歴ファイルが消えていること。
- **退避の連番**: `broken.json` が既にあるとき `broken2.json` へ退避されること。
- **連番が尽きた場合**: `broken` 〜 `broken5` がすべて存在するとき、**退避せず** status が
  `HISTORY_READ_ONLY` で、**`record` が書き込みを行わない**こと。
- **退避の失敗**: `os.replace` が例外を投げるようにした場合に `HISTORY_READ_ONLY` になること。
- **dict でない JSON**（例: `[]`）も破損として扱われること。
- **record（新規）**: 空の状態で `record` するとファイルが作られ、`recent[0]` に入ること。
- **record（先頭一致 = no-op）**: 同じパスをもう一度 `record` したとき
  **`repository.save_json` が呼ばれない**こと（`patch.object` で呼び出し回数を固定する）。
- **record（別表記の同一パス）**: 相対表記と絶対表記、大文字小文字違いが**同一と判定**され、
  件数が増えないこと（`canonical_path` 経由であることの確認）。
- **record（保存表記）**: config 配下は**相対**、config 外は**絶対**で記録されること（§5.7）。
- **record（上限）**: 21 件目で最古が落ちること。
- **save_history の失敗**: `save_json` が例外を投げるとき `(False, 理由)` が返り、
  理由に例外メッセージが含まれること。

### 設計メモ / 制約

- **`_load_optional_json`（`__init__.py:825-831`）をそのまま使わない**。同関数は
  **不在でも読込失敗でも `None` を返す**ため、§4.4 が要求する「不在」と「読めない」の区別ができない。
  `os.path.exists` で分岐してから `service.repository.load_json` を `try` すること。
- **比較キーは既存の `service.canonical_path(path, config_root)`**（`__init__.py:737-747`）。
  「相対は config_root から解決 → `normpath` → `normcase`」で §5.7 の規定そのものなので、
  **同等の処理を新しく書かない**。
- **保存表記は既存の `service.to_config_relative_or_absolute`**（`__init__.py:729-735`）。
- 書込は `service.repository.save_json`（`infrastructure/json_repository.py:13-20`）。
  `.tmp` → `os.replace` の原子的置換とディレクトリ作成は同関数がやるので**自前で書かない**。
  手本は `save_hotkey_presets`（`__init__.py:627-637`）。
- **ファイルを「読むだけ」で作らない**（遅延作成。§3）。
- 関数は 30 行以内を目安（`.claude/rules/implementation.md`）。新規ファイルは 300 行以内。
- 失敗理由の文字列は**ユーザーへ出す前提**（task_03 / task_04 がステータスバーへ出す）。
  例外型だけでなくメッセージが分かる形にする。

## 読むファイル

- `instructions/history/21_keymap_set_load_history.md` の **§3 / §4.2 / §4.3 / §4.4 / §7**（根拠）
- `keyseq/domain/keymap_set_history.py`（task_01 で追加済み・全体。呼び出す関数の確認）
- `keyseq/application/config_service/split_loading.py:45-92`（service 第 1 引数の関数群の書式・`None` 縮退の手本）
- `keyseq/application/config_service/__init__.py:24-32`（クラス定数）/ `:610-637`（書込の手本）/
  `:725-748`（`resolve_config_path` / `to_config_relative_or_absolute` / `canonical_path`）/ `:825-831`（`_load_optional_json`）
- `keyseq/infrastructure/json_repository.py`（全体・21 行）
- `keyseq/application/config_service/contracts.py:1-14`（定数の書式）
- `tests/test_config_service_contracts.py:12-20`（`INTERNAL_MODULE_NAMES`）
- `tests/test_config_service.py` の既存 TestCase を 1 つだけ（`config_root` を一時ディレクトリへ向ける
  セットアップの書き方の手本。**全体は読まない**）

## 含まない

- **`record` の呼び出し点への接続**（`keymap_set_io.py` / `startup_io.py` / `record()` の口）= **task_03**
- **パス指定の共通読込入口**の追加 = **task_03**
- **履歴ダイアログ・Treeview・メニュー項目・整形関数・`DIALOG_FILES` の更新** = **task_04**
- **正本 `spec_detail/` の改訂・`codebase_map.md` の追記・暫定仕様の凍結** = **task_05**
- `keyseq/domain/keymap_set_history.py` の変更（task_01 で確定済み。**不足を見つけたら実装せず報告する**）
- `config/config.json` へのキー追加（履歴パスは固定・暫定仕様 §3）
- `*.broken*.json` を一覧・復元する UI（暫定仕様 §10・スコープ外）

## 確認

1. 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` が clean。
2. 契約テスト: `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_config_service_contracts` が
   **全 pass**（`INTERNAL_MODULE_NAMES` と定数数 37 の更新の確認）。
3. 追加テスト: `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_config_service` が **全 pass**。
   上記「tests/test_config_service.py」節の項目をすべて含むこと。
4. 退行なし: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` が
   **pass 539 以上**（task_01 完了時点 539・skip 7 が基準）。
5. `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が **449 pass**
   （1 件程度の fail は既知フレーク。**単独実行で再現するか必ず確かめる**）。
6. `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が `SMOKE OK`。
7. **副作用**: 上記実行後に worktree ルートへ `keymap_set_history.json` / `user/` /
   `quarantine/` が生成されていないこと。`config/config.json` の mtime が不変であること。
8. `keyseq/application/config_service/__init__.py` の差分が
   **クラス定数 1 行 + import + 委譲メソッド 3 本のみ**であること（ロジックが入っていない）。

※ テストの実行は `verifier` が行う（Codex は python を起動できない）。

## 完了条件

- 上記確認 1〜8 が pass・**reviewer 採用**（観点: 暫定仕様 §3 / §4.2 / §4.3 / §4.4 との適合・
  **不在と破損の区別**・**退避でデータが失われないこと**・依存方向〔presentation を参照しない〕・
  `__init__.py` に新規ロジックが入っていないこと・後続タスクの先取りが無いこと）。
- 実機目視: **不要**（UI が出るのは task_04。目視は task_04 でまとめて実施する）。
