# task_01_global_presets_path_reader

## 目的

`config/config.json`（起動エントリ）に**グローバルなプリセット参照 `hotkey_presets_path`** を持たせ、
その**読み出し API を application に 1 本だけ**新設する（暫定仕様 07 **§2・§3**）。
本タスクは**読み出しの一点だけ**を作る。runtime への配線は task_02、payload 生成停止は task_05。

**レイヤ制約**: **application 限定**（`keyseq/application/config_service/split_loading.py`）。
**domain / presentation は不変**。**保存側（`split_payloads` / `save_plan_execution`）も不変**。
`config/config.json` への**書き込みは本タスクでは行わない**（読み手のみ。既定補完で成立する）。

先行実装の**同型パターン**は `split_loading.load_global_hook_keys`（phase 07 の成果・
`codebase_map.md` の「hook キーの解決点」）。**読み出し API はそれ自体で選択をしない**という
設計をそのまま踏襲する。

## 対象範囲（application 限定・新規関数 1 本 + テスト）

### `keyseq/application/config_service/split_loading.py`

`load_global_hook_keys` の直後に、次のモジュール関数を追加する。

```python
def load_global_hotkey_presets_path(service, *, config_root: str) -> str:
    """config/config.json（起動エントリ）のグローバルプリセットパスを返す。

    返すのは**保存されている表記のまま**（config 配下なら相対 / config 外は絶対）。
    未設定・空・非文字列・読込失敗・config_root 空 のときは既定
    `service.HOTKEY_PRESETS_RELATIVE_PATH` へ縮退する（**空文字は返さない**）。
    """
```

- 実装の骨格は `load_global_hook_keys` と同じ:
  `service._load_optional_json(service._startup_entry_path(config_root))` で起動エントリを読み、
  `dict` でなければ既定へ縮退する。
- 値の取り出しは `str(startup.get("hotkey_presets_path") or "").strip()`。
  **空になったら既定を返す**（`or` により非文字列・`None` も既定へ落ちる）。
- **パス解決はしない**（`_resolve_config_relative_path` を呼ばない）。解決は呼び出し側の責務で、
  task_02 で `load_named_list` へ渡す（`load_named_list` は内部で解決する）。
  **相対値を `os.path` 系へ直接渡さない**という既存の不変条件を崩さないため。

### `tests/test_config_service.py`

`HookKeyResolutionTest` と同じ流儀で、次を固定する特性テストを追加する（クラス名は
`GlobalHotkeyPresetsPathTest` 等・既存クラスの改変はしない）:

1. config.json に `hotkey_presets_path` があれば**その値がそのまま返る**（相対値が解決されずに返ること）
2. config.json に**キーが無い**場合は既定 `HOTKEY_PRESETS_RELATIVE_PATH` が返る
3. **空文字 / 空白のみ / 非文字列（`None`・数値）**でも既定へ縮退する
4. config.json 自体が**存在しない / 壊れている（dict でない）**場合も既定へ縮退する
5. `config_root=""` のときも既定が返る（**空文字を返さない**）

### 設計メモ / 制約

- **「明示的な空文字」も既定へ縮退させる**のは本タスクでの確定。暫定仕様 §3 は「config.json に
  無ければ既定値で補完する」までしか書いておらず空文字を未定義に残しているが、
  **プリセットの置き場は常に 1 つ**という §2 の趣旨に合わせ、未定義挙動を作らない側へ倒す。
  → task_08 の正本反映でこの契約を明記する。
- 既定値は `ConfigService.HOTKEY_PRESETS_RELATIVE_PATH`（`__init__.py:24`）を**唯一の定義元**として参照する。
  同値の直値を新たに書かない。
- `load_global_hook_keys` が `config_root` 空で `("", "")` へ縮退するのとは**縮退先が違う**
  （キーは「未設定」があり得るが、プリセットの置き場は常に既定が存在する）。この非対称は意図的。

## 含まない

- **runtime への配線**（プリセットの読込元を config.json へ切り替える）→ **task_02**
- **keymap_set 側 `hotkey_presets_path` の読込時無視** → **task_02**
- **keymap_set payload からの生成停止・保存カスケードからの除外** → **task_05**
- **プリセットマネージャの即時保存** → **task_06**
- **config.json への `hotkey_presets_path` の書き出し**（本フェーズでは書き手を増やさない。
  ユーザーが手で書いた値を読むだけで成立する）
- **runtime を新規化・置換する入口の一本化** → **task_03（設計確定）/ task_04（実装）**
- 正本 `spec_detail/` への反映 → **task_08**

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 170 + 追加分。件数が減らないこと）
- `-m unittest discover -s tests_ui` が **178 pass**（**無修正**。本タスクは presentation を触らない）
- `-m tests.smoke_app` が pass
- 追加テストが上記 1〜5 をすべて検証していること
- `git diff --stat` の変更が **`split_loading.py` と `tests/test_config_service.py` の 2 ファイルのみ**

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: 対象範囲外への波及が無いこと /
  既定への縮退が 5 経路すべてで効くこと / パス解決をしていないこと / 既存テストの無修正 pass）。
- **実機目視は本タスクでは行わない**（読み手を足すだけで挙動が変わらないため。
  実機目視は **task_07** でまとめて実施する）。
