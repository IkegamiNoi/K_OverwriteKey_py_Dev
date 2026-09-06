# task_01_reference_path_collector

## 目的

**与えられた keymap_set ファイル群から、参照されている子ファイルパスの集合（参照集合）を作る
読み出し専用の収集器**を application に新設する。根拠は暫定仕様 10 **§3-3**（参照集合の構築・2 段辿り）
+ **§3-2 の最終項**（keymap_set と解釈できない JSON の扱い）+ **§3-5-2**（読めなかった参照側の記録）。

- **レイヤ制約**: **application 限定**。domain / presentation / infrastructure は不変。**スキーマ不変**。
- **副作用禁止**: 本タスクの成果物は**ファイルを一切書かない・作らない**（読み出しのみ）。
- 正本の規範: `data_schema.md` **§5.7**（パス表記。**canonical 値は比較専用**で保存値・表示・戻り値へ混入させない）。

## 対象範囲（application 限定・新規モジュール + ファサード 1 行委譲のみ）

### 新規: `keyseq/application/config_service/reference_scan.py`

`parent_refs_cleanup.py` と**同じ書き方**にする（`from __future__ import annotations` /
モジュール関数は **`service` を第 1 引数**に取る / 結果は `@dataclass(frozen=True)` /
`__init__.py` を import しない〔循環回避〕）。

**定数（理由コード）**

```python
SOURCE_MISSING = "missing"        # 参照側ファイルが実在しない
SOURCE_UNREADABLE = "unreadable"  # 読めない / JSON として解析できない / トップレベルが dict でない
```

**結果型**

```python
@dataclass(frozen=True)
class ReferenceScanResult:
    referenced: frozenset[str]                          # canonical 表記（比較専用）
    unreadable_sources: tuple[tuple[str, str], ...]     # (入力で渡された表記, 理由コード)
    non_keymap_set_sources: tuple[str, ...]             # keymap_set と解釈できなかった JSON
```

**公開関数**

```python
def collect_reference_paths(
    service,
    keymap_set_paths: list[str],
    *,
    config_root: str,
) -> ReferenceScanResult:
```

振る舞い:

1. `keymap_set_paths` の各要素を `str(x or "").strip()` し、空なら無視する。
   **`service.resolve_config_path(path, config_root)` で解決**してから読む
   （相対値をそのまま `os.path` へ渡さない。正本 §5.7）。
2. **同一ファイルの二重読みをしない**。解決後の `service.canonical_path(...)` をキーにした
   ローカルキャッシュで、keymap_set / trigger_set とも 1 回だけ読む。
3. 読み取りは **`service._load_optional_json(resolved)`** を使う。
   - `os.path.exists` が偽 → `unreadable_sources` に `SOURCE_MISSING` で記録して次へ。
   - `None` またはトップレベルが `dict` でない → `SOURCE_UNREADABLE` で記録して次へ。
4. **keymap_set と解釈できるか**を判定する（§3-2）。判定は**キーの有無だけ**で行い、
   値の空・非空では判定しない。次の 4 キーが**1 つも存在しない**なら
   `non_keymap_set_sources` へ記録し、参照集合へ寄与させずに次へ:
   `trigger_set_path` / `keymaps` / `active_keymap_path` / `hotkey_presets_path`。
5. **1 段目（keymap_set → 子）**。次から値を取り出し、参照集合へ入れる:
   - `trigger_set_path`（str）
   - `keymaps`（list）の各要素 — **dict なら `path`、素の文字列ならその値**（旧形式・
     `split_loading.load_keymap_entry:393-398` と同じ受け方）
   - `active_keymap_path`（str）
   - `hotkey_presets_path`（str）— **`hotkey_presets_individual` の値に関わらず入れる**（§2 / §3-3。
     意図的な superset）
6. **`external_keyboard_layouts`（list）は両基準の superset**（§3-3）。各要素（dict なら `path`、
   素の文字列ならその値）について、**`config_root` 基準で解決した値**と
   **`os.path.dirname(config_root)` 基準で解決した値**の**両方**を参照集合へ入れる。
   ※ 既存実装は「`config_root` 基準で解決 → 親基準の相対表記で runtime 保持
   （`split_loading.py:526-531`）→ その値をそのまま保存（`split_payloads.py:342`）」という非対称のため、
   **ファイル内の値がどちらの基準か一意に決まらない**。
7. **2 段目（trigger_set → sequence）**。5 で得た `trigger_set_path` を解決して読み、
   `triggers`（list）の各要素（dict のみ）から **`sequence_path`** を取り出して参照集合へ入れる。
   trigger_set が実在しない / 読めない場合は `unreadable_sources` へ記録し、
   **その配下の sequence は参照集合に入らない**（過大判定になる旨は task_03 で警告表示する）。
8. 参照集合へ入れる値は、いずれも **`resolve_config_path` で解決 → `canonical_path` で正規化**した
   文字列。**空文字は入れない**。`referenced` は `frozenset` で返す。
9. **config 外を指す参照も集合へ入れてよい**（§3-3）。除外しないこと。

### 変更: `keyseq/application/config_service/__init__.py`（2 箇所のみ）

- 既存の `from . import parent_refs_cleanup, save_path_resolution, ...` 行へ **`reference_scan` を追加**する。
- **1 行委譲のファサード**を追加する（実ロジックを `__init__.py` へ置かない。同ファイルは 767 行で分割保留中）:

```python
def collect_reference_paths(
    self,
    keymap_set_paths: list[str],
    *,
    config_root: str,
) -> Any:
    return reference_scan.collect_reference_paths(
        self, keymap_set_paths, config_root=config_root
    )
```

### 新規: `tests/test_reference_scan.py`

`tests/test_parent_refs_cleanup.py` の書き方に合わせる（`tempfile.TemporaryDirectory` +
実ファイル作成。**`patch.object` を優先**し、モジュール名前空間の patch を新規に増やさない）。

### 設計メモ / 制約

- **`build_runtime_data_from_split` / `load_keymap_entry` / `load_trigger_set` を使わない**。
  これらは ID 採番・互換補正・フォールバック解決と一体で、**副作用が大きく重い**（暫定仕様 §1 現状監査）。
  **本タスクはキーから値を拾うだけ**でよい。
- **`canonical_path` の戻り値を表示・保存・`unreadable_sources` の値へ混入させない**
  （正本 §5.7 / `__init__.py:673-676` の docstring）。`unreadable_sources` には
  **入力で渡された表記をそのまま**入れる。
- **`resolve_child_save_targets` を使ってはならない**（正本 §5.8.1。「次に保存するとしたらどこへ書くか」であり、
  未実体化の子へ既定パスが割り当てられる）。
- 例外を握り潰さない。`_load_optional_json` が `None` を返す経路以外で例外が出るなら、そのまま伝播させる。
- 関数はおおむね 30 行以内・新規ファイルは 300 行以内を目安に分割する
  （`.claude/rules/implementation.md`）。private ヘルパは同モジュール内に置く。

## 含まない

- **ディレクトリ走査（どの keymap_set を渡すかの列挙）**= **task_02**。
  本タスクの入力は**呼び出し側から渡されるパスのリスト**。
- **`config.json` のグローバルプリセットパス（`hotkey_presets_path`）を参照集合へ加えること** = **task_02**。
- **候補側の列挙・形状検証・孤児判定・保護対象の適用** = **task_02**。
- **表示文言・メニュー・IO クラス・未保存時の確認** = **task_03**。
- **走査ディレクトリ設定の永続化** = **task_04**。**隔離 / 復元 / 削除** = **task_05 / task_06**。
- 正本 `spec_detail/` の改訂 = **task_08**（フェーズ中は正本を直接改訂しない）。
- `external_keyboard_layouts` のパス基準の非対称そのものの是正（→ idea_13）。**本タスクは superset で回避**する。

## 確認

`.venv` の python で実行する（`.claude/rules/python_rules.md`。worktree ルートから）。

```
..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui
..\..\..\.venv\Scripts\python.exe -m tests.smoke_app
```

**単体テストの項目**（`tests/test_reference_scan.py`・すべて実ファイルで検証する）:

1. 1 つの keymap_set から **4 キーすべて**（`trigger_set_path` / `keymaps[].path` /
   `active_keymap_path` / `hotkey_presets_path`）が参照集合に入る。
2. `keymaps` の要素が**素の文字列**（旧形式）でも拾える。
3. **`hotkey_presets_individual` が `false` でも** `hotkey_presets_path` が入る。
4. **2 段辿り**: `trigger_set` の `triggers[].sequence_path` が入る。
5. **trigger_set が読めない**とき、`unreadable_sources` に記録され、
   **その sequence は参照集合に入らない**。
6. keymap_set が**実在しない**とき `SOURCE_MISSING`、**壊れた JSON** のとき `SOURCE_UNREADABLE` で記録される。
7. **4 キーを 1 つも持たない JSON** は `non_keymap_set_sources` に入り、
   **`unreadable_sources` には入らない**。
8. `external_keyboard_layouts` の値が **`config_root` 基準・親基準の両方**で解決され、
   **両方が参照集合に入る**。
9. **同じ子を指す相対 / 絶対 / 区切り違い（`\` と `/`）が 1 つの canonical へ寄り、重複排除される**。
10. **同じ trigger_set を 2 つの keymap_set が指しても読み取りは 1 回**
    （`patch.object(service, "_load_optional_json", wraps=...)` 等で呼び出し回数を assert）。
11. **読み出し専用**: 実行の前後で対象ファイルのバイト列が不変で、**新規ファイル・ディレクトリが増えない**。
12. **`ConfigService.collect_reference_paths` の戻り値がモジュール関数の戻り値と一致**する
    （既存 `test_config_service_cleanup_delegates_match_module_functions` と同じ方針）。

**退行の基準**: `tests` は **267 → 増加**（減らさない）、`tests_ui` は **238 のまま**、smoke pass。
実行後に**worktree ルートへ `user/` が生成されていない**ことも確認する。

## 完了条件

- 上記「確認」がすべて pass（実測は **`verifier`** が行う。**Codex に python 実行を依頼しない**）。
- **`reviewer` 採用**（`.claude/rules/review.md` の 5 観点。特に**依存方向**〔application が `app` を参照しない〕・
  **不要変更の有無**〔`__init__.py` の変更が import 行 + 委譲メソッドの 2 箇所に収まっているか〕）。
- **実機目視は本タスクでは行わない**（UI に到達しないため。**task_07 でまとめて実施**する）。
