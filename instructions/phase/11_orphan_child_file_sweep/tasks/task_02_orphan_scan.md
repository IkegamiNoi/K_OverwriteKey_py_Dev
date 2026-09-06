# task_02_orphan_scan

## 目的

**走査（参照側の列挙）と孤児判定**を application に新設する。task_01 の参照パス収集器
（`reference_scan.collect_reference_paths`）へ渡す keymap_set の一覧を作り、候補側を列挙・形状検証し、
判定名 4 種で分類した結果を返す。根拠は暫定仕様 10 **§3-2**（走査範囲）/ **§3-3 のグローバルプリセット項**
/ **§3-4**（候補側・形状検証・保護対象・判定名）/ **§3-5-1・§3-5-3**（走査の不完全性の記録）。

- **レイヤ制約**: **application 限定**。domain / presentation / infrastructure は不変。**スキーマ不変**。
- **副作用禁止**: 本タスクの成果物は**ファイル・ディレクトリを一切作らない・書かない**（読み出しのみ。
  受け入れ条件 15）。`ensure_split_config_dirs` / `os.makedirs` を呼ばない。
- **`app` を参照しない**（§3-11）。走査ディレクトリ・保護対象・起動エントリ / 現在のセットのパスは
  **すべて引数で受け取る**。
- 正本の規範: `data_schema.md` **§5.7**（**canonical 値は比較専用**。結果の `stored_path` へ混入させない）/
  **§5.8.4**（分岐は判定名で行い表示文言で分岐しない）/ **§5.10**（`user/hotkey_presets/global/` は予約）。

## 対象範囲（application 限定・新規モジュール + ファサード 1 行委譲のみ）

### 新規: `keyseq/application/config_service/orphan_scan.py`

`parent_refs_cleanup.py` / `reference_scan.py` と**同じ書き方**にする（`from __future__ import annotations` /
モジュール関数は **`service` を第 1 引数**に取る / 結果は `@dataclass(frozen=True)` /
`__init__.py` を import しない〔循環回避〕。兄弟モジュールは `from . import reference_scan, split_loading`）。

**定数**

```python
ORPHAN_CANDIDATE = "candidate"    # 孤児候補（隔離の対象）
ORPHAN_REFERENCED = "referenced"  # 参照集合に含まれる
ORPHAN_PROTECTED = "protected"    # 保護対象
ORPHAN_EXCLUDED = "excluded"      # 候補側にあるが対象外（形状検証で落ちたもの）

KIND_KEYMAP = "keymap"
KIND_TRIGGER_SET = "trigger_set"
KIND_SEQUENCE = "sequence"
KIND_HOTKEY_PRESETS = "hotkey_presets"
```

**候補側ディレクトリと形状検証の必須キー**（§3-4。モジュール内の定数表として持つ）

| kind | ディレクトリ（config_root 相対） | 必須キー（トップレベル） | 型 |
|---|---|---|---|
| `KIND_KEYMAP` | `user/keymaps` | `mappings` | `dict` |
| `KIND_TRIGGER_SET` | `user/trigger_sets` | `triggers` | `list` |
| `KIND_SEQUENCE` | `user/sequences` | `actions` | `list` |
| `KIND_HOTKEY_PRESETS` | `user/hotkey_presets` | `hotkey_presets` | `list` |

**結果型**

```python
@dataclass(frozen=True)
class OrphanEntry:
    kind: str          # KIND_*
    stored_path: str   # to_config_relative_or_absolute による表記（表示・後続の隔離が使う）
    state: str         # ORPHAN_*


@dataclass(frozen=True)
class OrphanScanResult:
    entries: tuple[OrphanEntry, ...]                    # 候補側で列挙できた全ファイル（4 判定名すべて）
    unreadable_sources: tuple[tuple[str, str], ...]     # (入力表記, 理由コード) — reference_scan の結果をそのまま
    non_keymap_set_sources: tuple[str, ...]             # keymap_set と解釈できなかった JSON
    missing_scan_dirs: tuple[str, ...]                  # 見つからなかった指定ディレクトリ（入力表記のまま）
```

**公開関数**

```python
def scan_orphans(
    service,
    *,
    config_root: str,
    scan_dirs: list[str],
    startup_keymap_set_path: str,
    current_keymap_set_path: str,
    protected_paths: list[str],
) -> OrphanScanResult:
```

振る舞い:

1. **参照側の列挙**（§3-2）。次の順で keymap_set のパス一覧を作る。
   1. `<config_root>/user/keymap_sets/` **直下**の `*.json`（**非再帰**）。
   2. `startup_keymap_set_path`（起動エントリの値。空なら無視。既定ディレクトリ外でも含める）。
   3. `current_keymap_set_path`（現在開いているセット。空なら無視。**既定外・config 外でも含める**。
      受け入れ条件 3 / H1）。
   4. `scan_dirs` の各要素の**直下**の `*.json`（**非再帰**）。
   - 各要素は `str(x or "").strip()` し、空なら無視する。
   - ディレクトリは **`service.resolve_config_path(dir, config_root)` で解決**してから
     `os.path.isdir` を見る。**偽なら `missing_scan_dirs` へ入力表記のまま記録してスキップ**
     （§3-5-1。設定からは消さない・危険信号にしない）。`<config_root>/user/keymap_sets/` が
     無い場合も同じ扱いにする（**作らない**）。
   - **シンボリックリンクを辿らない**（§3-2）: 列挙時に `os.path.islink(entry)` が真の要素は飛ばす。
   - 列挙は `os.listdir` を使い、**拡張子 `.json`（大小無視）のファイルのみ**を対象にする
     （`os.path.isfile` が偽の要素は飛ばす）。
   - 一覧の重複は**排除しない**（`reference_scan` 側が canonical キャッシュで二重読みを防ぐ。task_01）。
2. **参照集合の構築**。1 の一覧を **`reference_scan.collect_reference_paths(service, paths,
   config_root=config_root)`** へ渡す（**本タスクで参照側の読み取りロジックを書き直さない**）。
   `unreadable_sources` / `non_keymap_set_sources` は**そのまま結果へ透過**させる。
3. **グローバルプリセットを参照集合へ追加**（§3-3）。
   **`split_loading.load_global_hotkey_presets_path(service, config_root=config_root)`** の戻り値を
   `resolve_config_path` → `canonical_path` で正規化し、参照集合へ足す（空なら足さない）。
   ※ 同関数は未設定・読込失敗時に既定 `user/hotkey_presets/global/default.json` へ縮退するが、
   その既定は候補側（`user/hotkey_presets/` 直下）と交差しないため実害はない。
4. **保護対象の正規化**（§3-4 / M4）。`protected_paths` の各要素を `str(x or "").strip()` し、
   空を除いて `resolve_config_path` → `canonical_path` の集合にする。
   **実在確認をしない**（実在しなくても保護 / config 外でも保護）。
5. **候補側の列挙**。上表 4 ディレクトリの**直下**の `*.json`（**非再帰**・`islink` は飛ばす・
   `isfile` のみ）。ディレクトリが存在しない場合は**その kind を 0 件として続行**する（**作らない**）。
6. **判定**。各候補ファイルの**絶対パス**について、次の順に評価し、**最初に決まった判定名**を採る:
   1. canonical が保護対象集合にある → `ORPHAN_PROTECTED`
   2. canonical が参照集合にある → `ORPHAN_REFERENCED`
   3. **形状検証**（§3-4 / §4-E）に通らない → `ORPHAN_EXCLUDED`。
      検証は `service._load_optional_json(abs_path)` で読み、**トップレベルが `dict`** であり
      **その kind の必須キーが表の型で存在する**ことを条件にする（読めない / `None` / 型違いは不通過）。
   4. それ以外 → `ORPHAN_CANDIDATE`
   - **形状検証のための読み取りは 3 に到達したファイルだけ**に行う（保護・参照ありで決着したものは読まない）。
7. `OrphanEntry.stored_path` は **`service.to_config_relative_or_absolute(abs_path, config_root)`**
   の戻り値。**canonical 値を入れない**（正本 §5.7）。
8. `entries` は **kind の定義順 → ファイル名の昇順**で安定させて返す（表示とテストの再現性のため）。

### 変更: `keyseq/application/config_service/__init__.py`（2 箇所のみ）

- 既存の `from . import parent_refs_cleanup, reference_scan, ...` 行（`:17`）へ **`orphan_scan` を追加**する。
- **1 行委譲のファサード**を追加する（実ロジックを `__init__.py` へ置かない。同ファイルは 767 行で分割保留中）。
  既存の `collect_reference_paths`（`:393-394`）の直後に、同じ形で置く:

```python
def scan_orphans(
    self,
    *,
    config_root: str,
    scan_dirs: list[str],
    startup_keymap_set_path: str,
    current_keymap_set_path: str,
    protected_paths: list[str],
) -> Any:
    return orphan_scan.scan_orphans(
        self,
        config_root=config_root,
        scan_dirs=scan_dirs,
        startup_keymap_set_path=startup_keymap_set_path,
        current_keymap_set_path=current_keymap_set_path,
        protected_paths=protected_paths,
    )
```

### 新規: `tests/test_orphan_scan.py`

`tests/test_reference_scan.py` / `tests/test_parent_refs_cleanup.py` の書き方に合わせる
（`tempfile.TemporaryDirectory` + 実ファイル作成。**`patch.object` を優先**し、
モジュール名前空間の patch を新規に増やさない）。

### 設計メモ / 制約

- **`user/hotkey_presets/global/` は列挙されない**（候補側は**直下の `*.json` のみ**で、
  `global/` はサブディレクトリのため `isfile` が偽）。したがって
  **`global/` 用の明示的な除外判定は書かない**（受け入れ条件 4 はテストで担保する）。
  **隔離ルート `<config_root>/quarantine/` も同様**に候補側 4 ディレクトリと交差しないため
  除外判定を書かない（§3-4 / §4-D / L6）。
- **`build_runtime_data_from_split` / `load_keymap_entry` / `load_trigger_set` /
  `resolve_child_save_targets` を使わない**（task_01 と同じ理由。副作用・誤爆上書きの回避。
  `resolve_child_save_targets` は正本 §5.8.1 のとおり「次に保存するとしたらどこへ書くか」で意味が違う）。
- **`_parent_refs` を参照しない**（§3-12-4。best-effort で孤児判定の根拠にできない）。
- **判定名の優先順位（保護 → 参照 → 形状 → 候補）は本タスクで定める規約**。
  `ORPHAN_CANDIDATE` 以外はいずれも「隔離しない」で等価だが、**表示と再現性のため決定的にする**。
- `canonical_path` の戻り値を `stored_path` / `missing_scan_dirs` へ混入させない
  （`missing_scan_dirs` には**入力で渡された表記をそのまま**入れる）。
- 例外を握り潰さない。`os.listdir` が `FileNotFoundError` を出す経路は**事前の `isdir` 判定で避ける**
  （`try/except` で黙って握らない）。`_load_optional_json` が `None` を返す経路はそのまま扱う。
- 関数はおおむね 30 行以内・新規ファイルは 300 行以内を目安に分割する
  （`.claude/rules/implementation.md`）。private ヘルパは同モジュール内に置く。
- **phase 10 の未対応指摘と同じ形を新規コードで作らない**（presentation からの内部モジュール直参照を
  前提にした API にしない = ファサード経由で使える形にする）。

## 含まない

- **表示文言の生成・警告文・一覧先頭への配置・メニュー・IO クラス・未保存時の「保存する / 中止する」2 択**
  = **task_03**（受け入れ条件 17 の警告文生成も task_03）。本タスクは**データを返すところまで**。
- **走査範囲外の keymap_set から参照され得る旨の併記**（§3-5-4）= **task_03**（固定文言）。
- **走査ディレクトリ設定の `config.json` への永続化・リスト UI** = **task_04**。
  本タスクは `scan_dirs` を**引数で受け取るだけ**（設定を読みに行かない）。
- **保護対象を実際に集める処理**（`app.keymap_set_path` / runtime の子 source_path 3 種 /
  `runtime["hotkey_presets_path"]`）= **task_03**（presentation 側が集めて渡す。§3-11 / M4）。
- **隔離 / 復元 / 削除・マニフェスト・隔離直前の再判定** = **task_05 / task_06**。
  本タスクは `quarantine/` を作らない・触らない。
- **候補側の再帰走査 / config 外の子の棚卸し / `external_keyboard_layouts` を候補側にすること** = スコープ外
  （§3-12-1・2 / §6 / idea_13）。
- 正本 `spec_detail/` の改訂 = **task_08**（フェーズ中は正本を直接改訂しない）。

## 確認

`.venv` の python で実行する（`.claude/rules/python_rules.md`。worktree ルートから）。

```
..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui
..\..\..\.venv\Scripts\python.exe -m tests.smoke_app
```

**単体テストの項目**（`tests/test_orphan_scan.py`・すべて実ファイルで検証する）:

1. `user/keymap_sets/` 直下の複数 keymap_set から **2 段辿り（trigger_set → sequence）**まで参照が効き、
   参照済みの子が `ORPHAN_REFERENCED`、未参照の子が `ORPHAN_CANDIDATE` になる（受け入れ条件 1）。
2. **`hotkey_presets_individual` が false でも** `hotkey_presets_path` の指す個別プリセットが
   `ORPHAN_REFERENCED` になる（受け入れ条件 2）。
3. **既定ディレクトリの外（config 外）にある「現在開いている keymap_set」**を
   `current_keymap_set_path` で渡すと走査され、**その子が `ORPHAN_CANDIDATE` にならない**
   （受け入れ条件 3 / H1）。`config.json` を書かずに成立すること。
4. **起動エントリ（`startup_keymap_set_path`）が指す既定ディレクトリ外の keymap_set** も走査される。
5. 候補側は **4 種の既定ディレクトリ直下のみ**。`user/hotkey_presets/global/` に置いたファイルが
   **`entries` に 1 件も現れない**（受け入れ条件 4）。**サブディレクトリに置いた子も現れない**（§3-12-2）。
6. **保護対象**に渡したパスは、参照集合に無くても `ORPHAN_PROTECTED` になる。
   **実在しないパス・config 外のパスを渡しても例外にならない**（受け入れ条件 5）。
7. **形状検証**: 必須キーを欠く JSON / トップレベルが list の JSON / 壊れた JSON が
   `ORPHAN_EXCLUDED` になり、`ORPHAN_CANDIDATE` にならない（受け入れ条件 18 / §4-E）。
   4 種それぞれの必須キー（`mappings` / `triggers` / `actions` / `hotkey_presets`）で確認する。
8. **見つからない `scan_dirs`** はスキップされ、`missing_scan_dirs` に**入力表記のまま**記録される。
   例外にならず、他のディレクトリの走査は続く（受け入れ条件 7 / §3-5-1）。
9. **`scan_dirs` に指定したディレクトリの keymap_set** から参照された子が `ORPHAN_REFERENCED` になる。
10. `unreadable_sources` / `non_keymap_set_sources` が **`reference_scan` の結果どおり透過**する
    （壊れた keymap_set 1 件 + 4 キーを持たない JSON 1 件を置いて確認。受け入れ条件 8）。
11. **`config.json` の `hotkey_presets_path`（グローバル）が参照集合に入る**。
    候補側ディレクトリ（`user/hotkey_presets/` 直下）にそのファイルを置いた場合に
    `ORPHAN_REFERENCED` になる（§3-3）。
12. **`external_keyboard_layouts` が候補側ディレクトリを指す場合、両パス基準のどちらで記録されていても
    保護される**（`ORPHAN_REFERENCED`。受け入れ条件 22 / Codex Medium）。
13. **書き込みゼロ**: 実行の前後で `config_root` 配下のファイル一覧・各ファイルのバイト列が不変で、
    **`user/` 配下の未作成ディレクトリが作られない**・**`quarantine/` が作られない**
    （受け入れ条件 15 / 16 / L3）。`user/keymaps` 等が存在しない config_root でも例外なく 0 件で返る。
14. `stored_path` が **config 相対表記**（`canonical_path` の戻り値でない）であること。
    `entries` の順序が **kind 定義順 → ファイル名昇順**で安定していること。
15. **`ConfigService.scan_orphans` の戻り値がモジュール関数の戻り値と一致**する
    （既存 `test_config_service_cleanup_delegates_match_module_functions` と同じ方針）。

**退行の基準**: `tests` は **279 → 増加**（減らさない・実測 2026-09-06）、`tests_ui` は **238 のまま**、
smoke pass。実行後に**worktree ルートへ `user/` が生成されていない**ことも確認する。

## 完了条件

- 上記「確認」がすべて pass（実測は **`verifier`** が行う。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（`.claude/rules/review.md` の 5 観点。特に
  **誤隔離の経路**〔参照集合・保護対象の取りこぼし / パス解決基準の取り違え〕・
  **依存方向**〔application が `app` を参照しない・設定を読みに行かない〕・
  **不要変更の有無**〔`__init__.py` の変更が import 行 + 委譲メソッドの 2 箇所に収まっているか〕）。
- **実機目視は本タスクでは行わない**（UI に到達しないため。**task_07 でまとめて実施**する）。
