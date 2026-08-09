# task_04_apply_global_defaults

## 目的

task_03 で確定した方式（暫定仕様 07 **§3-2**・**v0.5**）を実装する。
**`ConfigService.apply_global_defaults(runtime, *, config_root)` を新設**し、
hook キーの全体デフォルト注入 + グローバルプリセットの供給を 1 本に束ねて、
**入口台帳 E1〜E5** の 5 経路をこの API へ寄せる（受入条件 **7 / 8 / 9**）。
あわせてプリセットの読み出しを **`list | None`** に変え、**通常読込（L1〜L3 が使う
`build_runtime_data_from_split`）も同じ供給規則へ統一**する。

**レイヤ制約**: **application（`config_service` パッケージ）+ presentation の呼び出し配線のみ**。
**domain 不変・スキーマ不変・保存側（`split_payloads` / `save_plan_execution`）不変**。
UI の見た目・操作体系は変えない。

## 対象範囲（application の新設 + presentation の配線差し替え + テスト）

### 1. `keyseq/application/config_service/split_loading.py` — 読み出しの新設

`load_global_hotkey_presets(service, *, config_root: str) -> list[Any] | None` を新設する
（`load_global_hotkey_presets_path` の直後に置く）。

- パスは `load_global_hotkey_presets_path(service, config_root=config_root)` から取る
  （既定補完は同 API が済ませている。**呼び出し側で `os.path` 系へ渡さない**）。
- 解決は `service._resolve_config_relative_path(...)` → `service._load_optional_json(...)`
  （`_load_optional_json` は不存在・壊れた JSON で `None` を返す既存実装）。
- **戻り値の規約**:
  - **`list`（空リストを含む）** … 読めた。ファイルが dict で、根キー `hotkey_presets` が list。
    返すのは `safe_deepcopy(items)`。
  - **`None`** … 読めない。ファイルが無い / JSON が壊れている / dict でない / 根キーが list でない。
- **例外を投げない**。
- **`load_named_list` は使わない**（空と「読めない」を両方 `[]` に潰すため。§3-2 の指摘 high）。
  `load_named_list` 自体は他用途（trigger_set 等）で使われているので**変更しない**。

### 2. `keyseq/application/config_service/__init__.py` — 束ねた注入 API の新設

`apply_global_hook_key_defaults`（`:434`）の**直後**に追加する。

```python
def apply_global_defaults(self, runtime: dict[str, Any], *, config_root: str) -> dict[str, Any]:
    """runtime を新規化・置換した直後に、config.json の全体デフォルトを注入する。"""
```

- hook キー部分は **既存 `self.apply_global_hook_key_defaults(runtime, config_root=config_root)` を
  そのまま呼ぶ**（挙動不変。ロジックを複製・移動しない）。
- プリセット部分は `split_loading.load_global_hotkey_presets(self, config_root=config_root)` を呼び、
  **`list` を得たときだけ `runtime["hotkey_presets"]` を置き換える**（**空リストなら空にする**）。
  **`None` なら置き換えない**（runtime の既定を維持）。
- **runtime を破壊的に更新して返す**・**冪等**・**例外を投げない**。
- `apply_global_hook_key_defaults` は **公開のまま・名前と引数を変えない**（§3-2）。

### 3. `keyseq/application/config_service/split_loading.py` — 通常読込の供給規則統一

`build_runtime_data_from_split`（`:103-108`）のプリセット読込を、task_02 で入れた
`load_named_list(...)` から **`load_global_hotkey_presets(...)` の結果へ差し替える**。

- **`list` を得たときだけ `runtime["hotkey_presets"]` を置き換える**（空リストは採用）。
  **`None` なら置き換えない** → `new_default_data()` 由来の**組込 8 件**が残る。
- **`apply_global_defaults` は呼ばない**（通常読込は hook キーが条件付き注入のため。§3-2）。
- `keymap_set.get("hotkey_presets_path")` を再び参照しないこと（task_02 の到達点を戻さない）。

### 4. presentation — 入口台帳 E1〜E5 の配線差し替え

既存の `apply_global_hook_key_defaults(...)` 呼び出しを `apply_global_defaults(...)` へ置換する
（引数は同じ `(self._app.data, config_root=self._app.config_root)`）。

| 台帳 | 箇所 | 変更 |
|---|---|---|
| E2 | `controllers/config_io/keymap_set_io.py:54`（新規作成）| 呼び出しを置換 |
| E5 | `controllers/config_io/keymap_set_io.py:562`（Import）| 呼び出しを置換 |
| E3 | `controllers/config_io/keymap_set_io.py:600`（例を復元）| 呼び出しを置換 |
| E4 | `controllers/config_io/startup_io.py:36`（空データ起動）| 呼び出しを置換 |
| E1 | `presentation/app.py:77`（App 初期化）| `new_default_data()` の**直後に 1 行追加**（現状は呼び出しが無い）|

- **E1 は新規追加**。`self.data = self.config_service.new_default_data()` の直後で
  `self.config_service.apply_global_defaults(self.data, config_root=self.config_root)` を呼ぶ
  （`self.config_root` はこの時点で確定済み）。
- **N1（`keymap_set_io.py:56` の `normalize_runtime_data`）は供給不要**。触らない。

### 5. 変更しない箇所（明示）

- **`App.toggle_hook_keys_individual`（`app.py:439`）の ON→OFF は
  `apply_global_hook_key_defaults` を直接呼ぶまま**（受入条件 8）。
  束ねた API に変えると、キーの個別指定を切り替えただけでプリセットが再読込され、
  編集中の内容を取りこぼす。
- L1〜L3（`keymap_set_io.py:531` / `:631` / `startup_io.py:25`）は
  `build_runtime_data_from_split` が供給するので**呼び出しを足さない**。

### 6. テスト（追加・更新まで実装範囲。**実行は依頼しない**）

**更新（`tests/test_config_service.py`）** — v0.5 の規則変更に伴い期待値を更新する:

- `test_missing_or_invalid_global_presets_file_returns_empty_list`（`:400`）
  → **「読めないときは置き換えない」= 組込 8 件（`DEFAULT_CONFIG["hotkey_presets"]`）** へ更新。
  テスト名も内容に合わせて改名する。
- `test_legacy_keymap_set_presets_path_loads_without_error`（`:423`）
  → グローバルが不存在なので `[]` ではなく**組込 8 件**が残ることを確認する形へ更新。
- **アサーションを緩める形の更新は不可**（値で確認する）。更新したテスト名は報告に列挙する。

**追加（`tests/test_config_service.py`）**:

1. `load_global_hotkey_presets` が **読めた空リストで `[]` を返す**／不存在・壊れた JSON・
   非 dict・根キーが list でない場合に **`None` を返す**
2. `apply_global_defaults` が **`list`（空を含む）で `runtime["hotkey_presets"]` を置き換える**
3. `apply_global_defaults` が **`None` では置き換えない**（渡した runtime の値が保たれる）
4. `apply_global_defaults` が **hook キーを注入する**（個別指定 OFF）／
   **個別指定 ON の runtime では hook キーを書き換えない**（既存 `apply_global_hook_key_defaults` と同値）
5. `apply_global_defaults` の **冪等性**（2 回呼んで結果が同じ）
6. 通常読込（`build_runtime_data_from_split`）で **空リストが採用され**、
   **読めないときは組込 8 件が残る**（受入条件 9 = 注入経路と通常読込で規則が一致）

**追加（`tests_ui/test_config_io_characterization_keymap_set_startup.py` を基本とする）**:

7. **E2 新規作成 / E3 例を復元 / E5 Import** の後、`app.data["hotkey_presets"]` が
   **グローバルファイルの内容**になる（受入条件 7。E5 は取り込んだ単一 JSON の
   インライン `hotkey_presets` がグローバルで置き換わることを値で確認する）
8. **E4 空データ起動**でもグローバルの内容が供給される
   （配置は既存の空データ起動テストがあるファイルに合わせる）
9. **受入条件 8**: 個別指定 **ON→OFF** の切替では `hotkey_presets` が**変化しない**
   （`app.data["hotkey_presets"]` を編集した状態で `toggle_hook_keys_individual()` を
   ON→OFF し、編集内容が残ることを確認。`tests_ui/test_app_ui_flows.py` の既存 ON→OFF
   テスト群と同じ組み立てを流用する）

## 含まない

- **keymap_set payload からの `hotkey_presets_path` 生成停止 / 保存カスケードからの除外** → **task_05**
- **プリセットマネージャの即時保存（成否付き）** → **task_06**
- 破損プリセットファイルの**退避・復旧**（§3-2「既知の制約」で持たないと確定済み）
- `apply_global_hook_key_defaults` の**改名・引数変更・非公開化**（§3-2 で公開のままと確定）
- `load_named_list` のシグネチャ・挙動変更（他用途で使用中）
- **通常読込を `apply_global_defaults` 経由にすること**（§3-2 で経由しないと確定）
- 実機目視・通し再実測 → **task_07** / 正本反映 → **task_08**

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **180** + 追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **178** + 追加分）
- `-m tests.smoke_app` が pass
- 上記テスト 1〜9 がすべて存在し pass すること
- `grep` で **`apply_global_hook_key_defaults` の呼び出しが `app.py` の
  `toggle_hook_keys_individual` 内 1 箇所だけ**になっていること
  （E1〜E5 はすべて `apply_global_defaults`）
- `build_runtime_data_from_split` に `keymap_set.get("hotkey_presets_path")` が**無い**こと

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: §3-2 との適合〔`list | None` の区別・
  空リスト採用・`None` で非置換・注入経路と通常読込で規則一致〕/ 入口台帳 E1〜E5 の網羅と
  L1〜L3・N1 への非配線 / ON→OFF が単独注入のままか / 依存方向〔presentation → application の
  一方向〕/ 保存側・domain への波及がないか / 既存テスト更新がアサーション緩和になっていないか）。
- **実機目視は本タスクでは行わない**（**task_07** でまとめて実施）。
