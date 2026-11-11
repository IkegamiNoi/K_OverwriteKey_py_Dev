# task_07b_default_profile

## 目的

暫定 57 §8 Q2（v0.6 の詳細・ユーザー判断 2026-11-11）: 既定のホットキー・プリセットとサンプルを OS ごとのプロファイルにし、macOS は Command 系を使う。
既定データの型と Windows / macOS の 2 組は domain に置き（データのみ・OS 判定なし）、どちらを使うかは `OsBackend` が持つ。App の組み立てで `ConfigService` へ渡し、既定を作る・既定へ戻す箇所はすべて渡された既定を使う。既存の設定の自動変換はしない。

**レイヤ制約**: domain（データと引数の追加）・application（`ConfigService` が既定を保持して渡す）・infrastructure（`OsBackend` の欄）・presentation（App の組み立て 1 か所）。JSON スキーマ不変。
**Windows の動作不変**: すべての引数の既定値を Windows のプロファイルにし、既存の値・既存テストの期待値を変えない。

## 対象範囲

### domain: `keyseq/domain/default_profile.py`（新規）

```python
@dataclass(frozen=True)
class DefaultProfile:
    hotkey_presets: tuple[tuple[str, str], ...]   # (label, value)
    select_line: tuple[str, ...]                   # サンプルの行の選択
    copy: str
    paste: str
    switch_app: str
```

- `WINDOWS_DEFAULT_PROFILE`: 現在の `build_base_config` の 8 件（`domain/config.py:32-41`）と、現在の `build_sample_config` の値（`home`・`shift+end` / `ctrl+c` / `ctrl+v` / `alt+tab`）をそのまま移す。
- `MACOS_DEFAULT_PROFILE`（暫定 57 Q2）:
  - プリセット: `Command+Tab`=`windows+tab`・`Command+Space`=`windows+space`・`Command+Q`=`windows+q`・`Command+W`=`windows+w`・`Command+H`=`windows+h`・`Command+M`=`windows+m`・`Option+Command+Esc`=`alt+windows+esc`・`Ctrl+↑`=`ctrl+up`
  - サンプル: 行の選択 = `windows+left`・`windows+shift+right` / `windows+c` / `windows+v` / `windows+tab`
- OS 判定・`sys.platform`・UI ライブラリを入れない。

### domain: `keyseq/domain/config.py`

- `build_base_config(profile: DefaultProfile = WINDOWS_DEFAULT_PROFILE)`: `hotkey_presets` を `profile.hotkey_presets` から作る（`{"label", "value"}` の dict のリスト。値と順序は現在と同じ形）。
- `build_sample_config(profile=WINDOWS_DEFAULT_PROFILE)`: `build_base_config(profile)` を使い、サンプルのアクションの `home`・`shift+end` / `ctrl+c` / `ctrl+v` / `alt+tab` を `profile` の値に替える（`paste_line_to_app` の並び `[行の選択…, copy, switch_app, paste, switch_app]` も同じ）。
- `ensure_config_compatibility(data, *, profile=WINDOWS_DEFAULT_PROFILE)`: `_normalize_general_settings(config, profile)` の欠損時の既定（`:272`）を `build_base_config(profile)` から取る。

### application: `keyseq/application/config_service/`

- `ConfigService.__init__(self, repository, *, default_profile: DefaultProfile = WINDOWS_DEFAULT_PROFILE)` で `self.default_profile` に保持する。
- `new_default_data` / `new_base_data` は `self.default_profile` を渡す。
- `ConfigService` のメソッド内と、`service` を受け取るモジュール関数（`child_file_io.py:99`・`split_loading.py:334,534` 等）の `ensure_config_compatibility(...)` はすべて `profile=service.default_profile`（または `self.default_profile`）を渡す。
- `save_plan_execution.normalize_save_runtime(data)` は `profile` 引数（既定 Windows）を足し、`service` を持つ呼び出し元（`:45,289,331,355`）から `service.default_profile` を渡す。
- 漏れの確認: `grep -rn "ensure_config_compatibility(\|build_base_config(\|build_sample_config(" keyseq` で、application から既定（引数なし）のまま呼ぶ箇所が残らないこと（domain 内の互換用の内部呼び出しは除く。残す場合は理由を報告）。

### infrastructure: `keyseq/infrastructure/os_backend/`

- `contracts.OsBackend` に `default_profile: DefaultProfile` の欄を足す。
- Windows の backend の組み立ては `WINDOWS_DEFAULT_PROFILE`、macOS（`macos/backend.py`）は `MACOS_DEFAULT_PROFILE` を渡す。

### presentation: `keyseq/presentation/app.py`

- `ConfigService(self.repository, default_profile=backend.default_profile)`（`:116`）。プリセット管理の「既定に戻す」（`preset_manager.py:257`）は `new_default_data()` 経由のため変更不要（変わらないことを確認する）。

### テスト（`tests/`）

- `default_profile`: 2 組の値（件数 8・macOS の各値）、domain が OS 判定を持たないこと（既存の import 境界の AST テストが通ること）
- `build_base_config(MACOS_DEFAULT_PROFILE)` のプリセット・`build_sample_config(MACOS_DEFAULT_PROFILE)` のアクションの値（`windows+c` 等・`paste_line_to_app` の並び）
- `ensure_config_compatibility({}, profile=MACOS_DEFAULT_PROFILE)` の `hotkey_presets` が macOS の 8 件、引数なしは Windows の 8 件（現状維持）
- `ConfigService(repo, default_profile=MACOS_DEFAULT_PROFILE)` の `new_base_data` / `new_default_data` / `load`（presets の無い JSON）で macOS の既定になること
- `OsBackend` の欄: 契約テスト（`tests/test_os_backend_contracts.py`）の欄の一致テストに `default_profile` を足す・macOS の backend が `MACOS_DEFAULT_PROFILE` を持つ
- 既存テストの期待値は変えない（引数の既定が Windows のため）

## 読むファイル

- `keyseq/domain/config.py:25-100,262-280,415-440`
- `keyseq/application/config_service/__init__.py:55-150`・`child_file_io.py:85-102`・`split_loading.py:325-340,480-540`・`save_plan_execution.py:25-50,285-360`
- `keyseq/infrastructure/os_backend/contracts.py:100-125`・`os_backend/__init__.py`・`windows/` の backend の組み立て・`macos/backend.py`
- `keyseq/presentation/app.py:108-118`・`keyseq/presentation/dialogs/preset_manager.py:245-260`
- `tests/test_os_backend_contracts.py`（欄の一致テスト）
- `instructions/history/57_mac_support.md` §8 Q2

## 含まない

- 既存の設定ファイルの自動変換（Q2）
- Command の元キーへの割り当て禁止（Q5・task_09）・UI の `Command` / `Option` の表示（task_09）
- プリセットのラベルの多言語化（ラベルはデータ・現状どおり固定文字列）
- macOS でのキー送信の実装（task_08・09。プリセットの値が送れるかは task_09 で確認）

## 確認

**Mac**（`../../../.venv/bin/python`）:

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- 追加したテストが pass
- `-m unittest discover -s tests` の失敗・エラーが基準線（失敗 6・エラー 10・`mac_test_baseline.md`）から増えない
- `-m tests.smoke_app` が pass
- `main.py` を起動し、ホットキー・プリセット（アクションの編集のプリセット一覧）に Command 系の 8 件が出ること（ユーザー目視）

**Windows**: 次に Windows で標準検証 4 種を行う機会にまとめて実施する（既定のプリセット・サンプルが従来どおり）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
  - 2026-11-12 実施: compile clean・追加テスト 22 件 OK・tests 1933 件 失敗 6 / エラー 10 / skip 28（基準線どおり）・smoke OK・プリセット関係の tests_ui 14 モジュール基準線どおり（verifier）。目視: アクションの編集のプリセットに Command 系 8 件（ユーザー・スクリーンショット）。「既定に戻す」という操作は無く、共通プリセット未保存時の切替で既定を使う（`preset_manager.py:244-257`）。reviewer 採用（参考: `OsBackend.default_profile` の既定値で将来の backend の渡し忘れが黙って Windows になる・現状は契約テストで担保）
- 実機目視: Mac のプリセットは本タスクで実施（ユーザー）。
