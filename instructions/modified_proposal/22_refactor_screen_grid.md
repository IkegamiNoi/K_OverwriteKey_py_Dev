# 提案書 22: phase 56（画面の枠でカーソル移動・クリック）後のリファクタ

> 状態: **実施済**（2026-10-13・phase 56 task_09_refactor。`domain/config.py` に `KEYMAP_OPTIONAL_KEYS` / `copy_keymap_optional_keys` を置き 3 か所を置換・`_LETTER_ROWS` を `AUTO_ASSIGN_ORDER` から作る・reviewer 採用）。

## 判定の要約

範囲 `git diff c58a817..HEAD -- keyseq`（28 ファイル・+1939 / -17）。メトリクスは verifier の実測、M3・M4・M6 はメインで裏取り（下記の ファイル:行）。

- **M3・M4 該当**: keymap の任意キー `grid` をそのまま写す 2 行の分岐が、0 → **3 か所**に増えた（同じ形）。keymap に任意キーが増えるたびに 3 か所を直す形
  - `keyseq/application/config_service/__init__.py:182-183`（個別読込・取り込み）
  - `keyseq/application/config_service/split_loading.py:457-458`（split の個別 JSON の読込）
  - `keyseq/application/config_service/split_payloads.py:522-523`（個別保存）
- **M6 該当**: `keyseq/domain/screen_grid/assignment.py:10-15` の `_LETTER_ROWS`（`qwertyuiop` / `asdfghjkl;` / `zxcvbnm,./` / `1234567890`）が、`models.py:13` の `AUTO_ASSIGN_ORDER` と同じ文字の並びを直値で重ねて持つ
- 既知（提案書に含めない・`current.md`「別タスク化候補 > 画面の枠」に記載）: `keymap_panel_controller.py` 641 行（+93・M1 の +100 未満）と枠の関数の置き場所（task_07 L6・idea_45）。色 `#202028` の重複（`dialogs/grid_editor_window.py:50`・`screen_grid/grid_overlay_window.py:15`）は M6 の照合範囲〔import している定数〕に当たらず非該当（同じ節に記載・idea_44）
- M1（600 行超かつ +100 以上は無し）・M2（80 行超の新規関数なし）・M5（0 件）: 非該当

## 項目 0: 安全網の確認

- 対象領域のテスト: `tests/test_config_service.py`（個別 JSON の読込 → 保存で `grid` が保たれる・`grid` の無い keymap の保存に `grid` が出ない・不正な `grid`）/ `tests/test_per_keymap_triggers_load.py`（取り込みで保たれる）/ `tests/test_domain_config.py` / `tests/test_screen_grid.py`（`reassign_top_keys`）
- 完了条件: 着手前に `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui` / `-m tests.smoke_app` が全 pass（基準線）

## 項目 1: keymap の任意キーの受け渡しを 1 か所の定義にまとめる（M3・M4）

- 対象: 上記 3 か所
- 変更: keymap の「中身を解釈せずそのまま写す任意キー」の一覧と写す関数を domain に 1 つ置き、3 か所から呼ぶ（正規化は従来どおり `domain/config.py` の `_normalize_keymap_compat_fields` が行う）
  ```python
  # 変更前（3 か所）
  if "grid" in raw_keymap:
      keymap["grid"] = safe_deepcopy(raw_keymap["grid"])
  # 変更後（例・置き場所は domain の keymap の正規化の近く = domain/config.py）
  KEYMAP_OPTIONAL_KEYS: tuple[str, ...] = ("grid",)
  def copy_keymap_optional_keys(source: dict, target: dict) -> None:
      for key in KEYMAP_OPTIONAL_KEYS:
          if key in source:
              target[key] = safe_deepcopy(source[key])
  # 呼び出し
  copy_keymap_optional_keys(raw_keymap, keymap)
  ```
- 完了条件: 項目 0 のコマンドが全 pass。`grep -n '"grid" in' keyseq/application/config_service` が 0 件
- リスクと戻し方: 挙動は不変（同じキーを同じ写し方で写す）。戻すなら 3 か所に 2 行を書き戻す
- 依存: なし

## 項目 2: 振り直しの段を自動割当の順から作る（M6）

- 対象: `keyseq/domain/screen_grid/assignment.py:10-15`
- 変更: `_LETTER_ROWS` を `AUTO_ASSIGN_ORDER`（`models.py:13`・Q 段 → A 段 → Z 段 → 数字段の 10 文字ずつ）から作る
  ```python
  # 変更前
  _LETTER_ROWS = (tuple("qwertyuiop"), tuple("asdfghjkl;"), tuple("zxcvbnm,./"), tuple("1234567890"))
  # 変更後
  _LETTER_ROWS = tuple(AUTO_ASSIGN_ORDER[i:i + 10] for i in range(0, len(AUTO_ASSIGN_ORDER), 10))
  ```
- 完了条件: `tests/test_screen_grid.py`（`reassign_top_keys` の 4 段・5 段・reserved）が pass。項目 0 のコマンドが全 pass
- リスクと戻し方: 挙動は不変（同じ 4 つの並び）。戻すなら直値に戻す
- 依存: なし

## 実施のしかた（ユーザーに選んでもらう）

- (a) phase 56 の末尾の追加タスク `task_09_refactor` として実施 / (b) 次フェーズ前の独立ミニフェーズ / (c) 見送り（判断を `decisions_archive/56` に記録）
