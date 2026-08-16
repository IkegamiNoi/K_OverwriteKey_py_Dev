# 提案書 07: phase 09（個別プリセット）後のリファクタ

> `/refactor_check`（phase 09 完了時・2026-08-16）の判定結果から起票。**未承認**。
> **本書は判定と提案のみ。ユーザー承認を得るまで実施しない。**
> 挙動保存が原則（挙動・エラーメッセージ・保存ファイルのバイト列を変えない）。

## 判定

**リファクタ推奨**（対象: phase 09 の変更 **9 ファイル**・`39140c5..HEAD -- keyseq/` = +708 / -17）。

| 記号 | 該当 | 内容 |
|---|---|---|
| M1 | **該当** | `dialogs.py` **1016 行**（+195）/ `config_service/__init__.py` **734 行**（+135）— いずれも 600 行超 かつ +100 行以上 |
| M2 | **該当** | `PresetManagerDialog.__init__` が **99 行**（+49。既存関数を 80 行超へ拡大）|
| M3 | 非該当 | 新規の同型 3 個目のコピーなし（`__init__.py` の 1 行委譲は既存パターン）|
| M4 | 非該当 | 列挙**箇所**は増えていない（既存箇所へ 2 フィールド追加のみ）|
| M5 | 非該当 | 申し送りコメントの新規追加 **0 件** |
| M6 | **該当** | `config_service/__init__.py:435` の `os.makedirs(os.path.join(config_root, "user", "hotkey_presets", "global"))` が `HOTKEY_PRESETS_RELATIVE_PATH` と同値の直値 |

**上位 3 項目に絞った**（`/refactor_check`「項目数は 1〜3 個まで」）。
落とした **`config_service/__init__.py` の 734 行**は `current.md`「別タスク化候補」へ送る
（**テストが `patch("keyseq.application.config_service.os.path", ntpath)` で名前空間を差し替えるため
`ConfigService` 本体とパス基盤メソッドを動かせない**という強い制約があり、
分割方針の設計判断が別途必要。効果に対してリスクが高い）。

---

## 項目 0: 安全網の確認（先行・必須）

分割前に、対象領域が既存テストで守られていることを確認する。**不足していれば特性テストの追加を先に行う。**

- 対象 = `PresetManagerDialog` の UI 契約（`spec_detail/data_schema.md` §5.10.3 の
  「プリセットマネージャの UI 契約」）。
- 既存カバレッジ: `tests_ui/test_app_ui_flows.py`（トグルの読み直し・破棄確認・
  OFF で開いた時点の一覧確定・上書き確認の 3 択・OK / キャンセルの不変性）。
- 確認コマンド（`.venv` の python を使う。`.claude/rules/python_rules.md`）:
  ```
  ..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui
  ```
- **`tests_ui` の 4 ファイルにある `messagebox` / `filedialog` の fail-fast ガード**を壊さないこと
  （壊すとモーダルで永久ブロックする）。

---

## 項目 1: `PresetManagerDialog.__init__` の UI 構築を抽出する（M2）

- **対象**: `keyseq/presentation/dialogs.py:396-495`（99 行）
- **何が問題か（M2）**: phase 09 で個別指定チェック + 保存先ラベル 2 行を足した結果、
  **ウィジェット構築・状態初期化・イベント配線・一覧の初期確定（【I2】相当）が 1 関数に同居**している。
- **どう変えるか**: 責務ごとに private メソッドへ切り出し、`__init__` は流れだけにする。

  ```python
  def __init__(self, parent, title="プリセット編集"):
      super().__init__(parent)
      self._init_state(parent)          # _temp / _loaded_temp / individual var 等
      self._build_widgets()             # 一覧・ボタン・チェック・ラベル
      self._bind_events()               # double click / チェックのトレース
      self._sync_initial_presets()      # OFF なら表示元へ合わせて一覧を確定（§5.10.3）
      self._update_source_labels()
  ```
- **完了条件**: `-m unittest discover -s tests_ui` が **223 pass**（件数不変）/
  `-m tests.smoke_app` が pass / `__init__` が **40 行以内**。
- **リスクと戻し方**: 構築順序が変わると Tk の変数トレースが初期化前に発火し得る。
  **`_bind_events` は状態と widget の構築後**に置く。単一ファイル内の移動のみなので `git checkout` で戻せる。
- **依存**: 項目 0。

---

## 項目 2: `dialogs.py` を `dialogs/` パッケージへ分割する（M1）

- **対象**: `keyseq/presentation/dialogs.py`（**1016 行**・6 ダイアログクラス + 純関数 1）
- **何が問題か（M1）**: 600 行を大きく超え、phase 09 だけで +195。
  **1 ファイルに独立した 6 つのダイアログが同居**し、修正時に無関係な領域を読むコストが常に乗る。
- **どう変えるか**: `.claude/rules/file_organization_rules.md`「フォルダ化」の**親フォルダ方式**で
  `keyseq/presentation/dialogs/` を作り、クラス単位で分ける。

  ```
  presentation/dialogs/
    __init__.py            # 公開面（既存の import パスを維持する再輸出）
    action_dialog.py       # ActionDialog（+ キーキャプチャ）
    preset_manager.py      # PresetManagerDialog / PresetDialog / format_preset_manager_source_labels
    trigger_dialog.py      # TriggerDialog
    keymap_edit_dialog.py  # KeymapEditDialog
    layout_delete_dialog.py# LayoutDeleteDialog
  ```
  - **`__init__.py` の再輸出は互換レイヤー禁止の対象外**（公開面の定義。
    `file_organization_rules.md`「本リポジトリへの適用注記」）。
    ただし **`from .x import *` は使わず明示列挙**する。
  - **旧パスに横流し専用モジュールを残さない**（恒久互換レイヤーの禁止）。
- **完了条件**: `import keyseq.presentation.dialogs` 経由の既存 import が**すべて無変更で通る** /
  `-m compileall -q keyseq main.py tests tests_ui` clean /
  `tests` **238** + `tests_ui` **223** + smoke がいずれも pass（**件数不変**）/
  各ファイルが 400 行以内。
- **リスクと戻し方**: `tests_ui` が `keyseq.presentation.dialogs.messagebox` 等を
  **モジュール名前空間ごと patch している場合、patch 先が分割後のモジュールへ移る**。
  **着手前に `grep -rn "presentation.dialogs" tests tests_ui` で patch 対象を洗い出す**こと
  （`config_service` で同型の制約を踏んでいる）。分割は純粋な移動なので `git checkout` で戻せる。
- **依存**: 項目 1（先に `__init__` を整理してから移動する方が差分を読みやすい）。

---

## 項目 3: `global/` ディレクトリ作成の直値を定数由来にする（M6）

- **対象**: `keyseq/application/config_service/__init__.py:435`
- **何が問題か（M6）**: `os.path.join(config_root, "user", "hotkey_presets", "global")` が
  **`HOTKEY_PRESETS_RELATIVE_PATH`（`user/hotkey_presets/global/default.json`）と同値の直値**。
  同フェーズの他 2 箇所（`save_path_resolution.py:189` / `split_loading.py:181`）は
  `os.path.dirname(service.HOTKEY_PRESETS_RELATIVE_PATH)` で定数由来にしており、**ここだけ非対称**。
  定数を変えると**このディレクトリだけ旧位置に作られる**（例外は出ない）。
- **どう変えるか**:
  ```python
  os.makedirs(
      os.path.join(config_root, os.path.dirname(self.HOTKEY_PRESETS_RELATIVE_PATH)),
      exist_ok=True,
  )
  ```
- **完了条件**: `tests` **238** + `tests_ui` **223** + smoke が pass（**作られるディレクトリのパスが不変**であることを
  既存の起動時骨格テストで確認）。
- **リスクと戻し方**: 1 行。ほぼ無リスク。
- **依存**: なし（単独で実施可能）。

---

## 実施タイミング（ユーザー選択）

承認する場合、`/refactor_check` の規定により次のいずれかを選ぶ:

- **(a) 同フェーズ末の追加タスク**（`task_09_refactor` として起票）
- **(b) 次フェーズ前の独立ミニ計画**（計画05 / 計画06 と同じ形。**フェーズ番号を消費しない**）

**項目 3 だけ先に単独実施する**選択もある（1 行・無リスク）。
