# task_03_startup_settings_loader

## 目的

負債①（責務混在）・③（初期化順序の制約）の解消。`App._load_startup_settings` の I/O + 型ガード +
正規化 + エラー通知を、新規 `presentation/startup_settings.py` の関数へ切り出す。UI 通知（`messagebox`）は
**コールバック注入**にして関数から外す（暫定仕様 [§5](../../../history/02_startup_font_settings_cleanup.md)・
受け入れ条件 §8-3/§8-4/§8-8/§8-12）。

- **挙動不変**（真理値表どおり分岐・回数・文言を保つ・**未知キー全保持**）。**presentation 限定**・
  application（`ConfigService`）/domain/infrastructure 不変・スキーマ不変・初期化順序不変。

## 対象範囲（presentation 限定・ロジック不変移設 + テスト再編）

### 1. `keyseq/presentation/startup_settings.py`（新規作成）

App 専用の薄いローダ。`config_service` に直依存し（`config_io` に依存しない＝初期化順序問題を起こさない）:

```python
from keyseq.presentation.theme import coerce_font_delta


def load_startup_settings(config_service, startup_path, *, on_read_error) -> dict:
    """startup.json を読み、型ガードと正規化（font_delta / prompt_if_missing）を施した dict を返す。
    読込例外時は on_read_error(exc) を呼び既定 dict を返す。未知キーは全て保持する。"""
```

現行 `App._load_startup_settings`（現 `app.py` 内・旧 376-392 相当）を**ロジック不変で移設**する。等価な実装:

```python
    startup = {}
    try:
        startup = config_service.load_startup(startup_path)
    except Exception as exc:
        startup = {}
        on_read_error(exc)
    if not isinstance(startup, dict):
        startup = {}
    startup["ui_font_delta_pt"] = coerce_font_delta(startup.get("ui_font_delta_pt", 0))
    startup["prompt_if_missing"] = bool(startup.get("prompt_if_missing", True))
    return startup
```

- **未知キー全保持の契約**（受け入れ条件 §8-12・後方互換の要）: 読み込んだ dict を **in-place で 2 キーのみ
  上書きして丸ごと返す**（＝現行と等価）。`keymap_set_path` / `last_used_directory` 等の未知キーが消えないこと。
- **エラー通知の真理値表**（§5・挙動不変）を厳守: 欠損=`{}` 返却で警告なし / 読込例外=`on_read_error(exc)` を **1 回**のみ /
  非 dict=型ガードで既定化・警告なし / 正常=全キー保持 + 2 キー正規化。**`messagebox` を本モジュールに import しない**。

### 2. `keyseq/presentation/app.py`（呼び出し差し替え + メソッド削除）

- import 追加: `from keyseq.presentation.startup_settings import load_startup_settings`。
- `app.py:57`（`self._startup_settings = self._load_startup_settings()`）を新ローダ呼び出しへ差し替え、
  **例外時のみ**の警告を `on_read_error` として注入する（title/body は現行と 1 文字一致）:

```python
        self._startup_settings = load_startup_settings(
            self.config_service,
            self.startup_path,
            on_read_error=lambda exc: messagebox.showwarning(
                "startup.json 読込失敗",
                f"startup.json の読込に失敗しました。\n{exc}\n\n既定設定で起動します。",
            ),
        )
```

- `App._load_startup_settings`（現 `app.py` 内・旧 376-392 相当）を**削除**する。
- **初期化順序を壊さない**: `config_service` は `app.py:43` で生成済み。`:57` の実行位置・`config_io`（`:127`）非依存を保つ。
  `app.py` の `messagebox` import（`from tkinter import messagebox, ttk`・現行あり）はそのまま利用。

### 3. tk 不要のローダ単体テスト（新規 `tests/test_startup_settings.py`）

暫定仕様 §9 の「fake config_service + 記録用コールバック + tk 不要」テスト。`load_startup_settings` を直接検証する:

- **真理値表 4 分岐**（fake config_service が `{}` 返却 / 例外送出 / 非dict 返却 / 正常dict 返却）で
  返り値（既知2キー正規化）と `on_read_error` の**呼出回数・引数**（例外時のみ 1 回・渡された exc）を固定。
- 例外時の想定文言確認は App 側の注入 lambda で行うため、本ユニットでは **`on_read_error` が受け取る exc が一致**することまで
  （title/body 1 文字一致は tests_ui 側 or App 注入の別テストで担保。下記 4 参照）。
- **未知キー全保持**（`{"keymap_set_path": "X", "last_used_directory": "D", "ui_font_delta_pt": "1"}` を fake が返す →
  返り値が未知キーを保持し `ui_font_delta_pt==1` / `prompt_if_missing==True` のみ正規化）。
- 正常 dict の正規化（`ui_font_delta_pt` クランプ・`prompt_if_missing` bool 化）。

### 4. 安全網（`tests_ui/test_startup_font_characterization.py`）の再編

現行の loader 特性テストは削除される App メソッドを対象とするため、以下のとおり再編する
（**弱体化ではなく、より強い tk 不要テスト〔上記 3〕への契約移設**）:

- `test_load_startup_settings_truth_table`: **撤去**（純ローダ論理は `tests/test_startup_settings.py` が tk 不要で網羅。
  App メソッド消滅により本メソッドは対象を失う）。
- `test_load_startup_settings_preserves_unknown_keys_through_save`: **write_startup ラウンドトリップ（§8-12）の検証のみ残す**
  （App + `config_io` が必要で tests_ui が適切）。削除される `app._load_startup_settings()` 呼び出しを、
  新ローダ `load_startup_settings(...)` 呼び出し（または読込済み dict の直接構築）へ置換する。
  **保存後に `keymap_set_path` 等が `save_startup` 引数へ残ること**のアサーションは維持する。
- `test_coerce_font_delta_value_table` / `test_set_ui_font_delta_applies_only_real_changes`: **変更しない**。
- App 注入の警告文言（title「startup.json 読込失敗」/ body 1 文字一致）の担保: 上記ラウンドトリップ改修時、
  もしくは新ローダ呼び出しに `on_read_error` を渡す小テストで、**例外時に注入 lambda が想定 title/body で showwarning を呼ぶ**ことを
  1 ケース残す（受け入れ条件 §8-8。tests_ui で `app_module.messagebox` を patch して確認）。

## 設計メモ / 制約

- **実行環境**: python は必ず `..\..\..\.venv\Scripts\python.exe`（worktree 相対）。
- **依存方向**: `startup_settings.py`（presentation）→ `config_service`（application・引数注入）は正しい向き。
  `theme.coerce_font_delta`（presentation）を使う。**`config_io`・infrastructure 具象・`messagebox` に依存しない**。
- **やってはいけない**: `set_ui_font_delta` の分割（task_04）、`UiVars` 引数化（task_04）、application/domain の変更、
  スキーマ/範囲/既定/文言の変更、真理値表の分岐・警告回数の変更、`test_coerce_*`/`test_set_ui_font_delta_*` の改変。

## 含まない

- `set_ui_font_delta` の案 A 分割（`_apply_font_delta` 抽出）・`UiVars` 引数化（task_04）。
- 正本反映・記録（task_05）。
- フォント範囲・既定値・startup.json スキーマ・メニュー構成の変更（スコープ外）。

## 確認

`.venv` python で以下を実行し、いずれも pass すること:

- 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py`（clean）
- 新規ローダ単体テスト: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`（従来 82 + startup ローダ分。撤去分を差し引いた件数を確認）
- 安全網（再編後）: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui`（破綻なし・write_startup 保持と警告文言 1 ケースが pass）
- smoke: `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app`（pass）
- 受け入れ条件（暫定仕様 §8-3/§8-4）:
  - `App._load_startup_settings` が消え、`app.py` は薄い配線のみ（`grep -n "_load_startup_settings" keyseq/` が定義0・App メソッド呼び出し0）
  - `startup_settings.py` が `config_io` に依存しない（`grep -n "config_io" keyseq/presentation/startup_settings.py` が 0 件）
  - `startup_settings.py` が `messagebox` を import しない（`grep -n "messagebox" keyseq/presentation/startup_settings.py` が 0 件）
  - 初期化順序: `app.py:57` の呼び出し位置が `UiVars(:61)` / `ConfigIoController(:127 相当)` より前に保たれている

## 完了条件

- 上記「確認」全 pass・**reviewer 採用**（CLAUDE.md レビュー必須。観点: 仕様適合性/依存方向/責務分離/不要変更/チェック漏れ）。
  特に**真理値表の不変**（分岐・回数・文言 1 文字一致）と**未知キー全保持**を重点確認。
- 実機目視: 本タスクでは不要（挙動不変）。実機目視は task_04 完了後にまとめて実施する。
