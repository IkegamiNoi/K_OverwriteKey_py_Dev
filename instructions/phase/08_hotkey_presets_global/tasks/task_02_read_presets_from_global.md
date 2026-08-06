# task_02_read_presets_from_global

## 目的

keymap_set 読込時の**プリセットの読込元を config.json のグローバル参照へ切り替える**
（暫定仕様 07 **§2・§3**・受入条件 **1 / 2（読込側）/ 5**）。
keymap_set 側の `hotkey_presets_path` は**読込時に参照しなくなる**（＝無視。能動削除はしない）。

**レイヤ制約**: **application 限定**（`keyseq/application/config_service/split_loading.py` の 1 関数）。
**domain / presentation は不変**。**保存側（`split_payloads` / `save_plan_execution`）も本タスクでは不変**。
本タスクは**挙動変更**を含む（読込元が変わる）。

## 対象範囲（application 限定・1 箇所の差し替え + テスト）

### `keyseq/application/config_service/split_loading.py`

`build_runtime_data_from_split` 内のプリセット読込（**L103-107**）を、
task_01 で新設した `load_global_hotkey_presets_path` の戻り値から読むように差し替える。

```python
# 変更前
runtime["hotkey_presets"] = load_named_list(
    service,
    keymap_set.get("hotkey_presets_path"),   # ← keymap_set 側の参照
    root_key="hotkey_presets",
    config_root=config_root,
)

# 変更後（keymap_set は参照しない = 読込時無視）
runtime["hotkey_presets"] = load_named_list(
    service,
    load_global_hotkey_presets_path(service, config_root=config_root),
    root_key="hotkey_presets",
    config_root=config_root,
)
```

- **`keymap_set.get("hotkey_presets_path")` の参照をこの関数から無くす**こと（残っていたら未達）。
- `load_named_list` は**内部でパス解決する**ため、task_01 の API が返す「保存表記のまま」の値を
  そのまま渡してよい（**呼び出し側で `os.path` 系へ渡さない**）。
- **キーの能動削除はしない**（`keymap_set.pop(...)` 等を書かない。`data_schema.md` の既存キー削除禁止）。

### テスト（`tests/test_config_service.py` を基本とする）

次を固定する特性テストを追加する（既存クラスの改変はしない・新規クラスでよい）:

1. config.json の `hotkey_presets_path` が指すファイルからプリセットが読み込まれる
2. **keymap_set 側に別の `hotkey_presets_path` があっても無視され**、グローバル側の内容が読み込まれる
   （＝両方に異なる内容のファイルを置き、グローバル側が採用されることを値で確認する）
3. config.json に `hotkey_presets_path` が無ければ**既定 `user/hotkey_presets/default.json` から読む**
4. グローバルのプリセットファイルが**存在しない / 壊れている**場合は `[]`（既存 `load_named_list` の縮退）
5. keymap_set に `hotkey_presets_path` が残っていても**読込が例外を出さず完走する**（受入条件 5・後方互換）

### 既存テストの扱い

- 「keymap_set の `hotkey_presets_path` からプリセットが読まれること」を前提にした既存テストが
  落ちる場合は、**アサーションを緩めず「グローバルから読む」期待値へ更新する**
  （本フェーズは挙動変更フェーズ。受入条件 6 = 更新後の期待値で pass）。
- 更新した既存テストは**ファイル名とテスト名を報告に列挙する**こと。

### 設計メモ / 制約

- **既知の中間状態（task_05 まで残る）**: 保存側は依然として
  `split_payloads` がプリセットを書き出す（別ディレクトリへ保存すると `<保存先>/hotkey_presets/default.json`）。
  そのため本タスク完了時点では「**別の場所へ保存した keymap_set を読み直すとプリセットはグローバル側**」
  という非対称が残る。**これは task_05（payload 生成停止 + カスケード除外）で解消する**設計であり、
  本タスクで先取りして直さないこと。
- 単一 JSON 互換の読込（`ensure_config_compatibility` が扱う `hotkey_presets` インライン配列）は
  **別形式のため本タスクの対象外**（暫定仕様は split 構成を対象にしている）。

## 含まない

- **keymap_set payload からの `hotkey_presets_path` 生成停止 / 保存カスケードからのプリセット除外** → **task_05**
- **プリセットマネージャの即時保存** → **task_06**
- **runtime を新規化・置換する入口（新規作成 / Import / 例を復元 / 空データ起動）へのプリセット供給**
  → **task_03（設計確定）/ task_04（実装）**。本タスクは**通常読込 1 経路だけ**を変える
- **単一 JSON 互換の読込経路**の変更
- keymap_set からの `hotkey_presets_path` の**能動削除**（仕様上禁止）
- 正本 `spec_detail/` への反映 → **task_08**

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 175 + 追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 178。**更新が必要になった場合は件数と更新理由を報告**）
- `-m tests.smoke_app` が pass
- 追加テストが上記 1〜5 をすべて検証していること
- `build_runtime_data_from_split` に `keymap_set.get("hotkey_presets_path")` が**残っていない**こと

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: 読込元がグローバル 1 本になったか /
  keymap_set 側キーを能動削除していないか / 対象範囲外〔保存側・入口・presentation〕へ波及していないか /
  既存テストの更新がアサーション緩和になっていないか）。
- **実機目視は本タスクでは行わない**（**task_07** でまとめて実施）。
