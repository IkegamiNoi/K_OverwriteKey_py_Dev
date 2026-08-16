# 提案書 07: phase 09（個別プリセット）後のリファクタ

> `/refactor_check`（phase 09 完了時・2026-08-16）の判定結果から起票。
> **ユーザー承認済（2026-08-16）→ 「計画07」として実施中**（下記「実施形態」）。
> 挙動保存が原則（挙動・エラーメッセージ・保存ファイルのバイト列を変えない）。

## 実施形態（ユーザー確定 2026-08-16）

**(b) 次フェーズ前の独立ミニ計画 = 「計画07」**。運用は**計画05 / 計画06 と同じ**:

- **本提案書自体を確定設計として扱う**（暫定仕様書は起票しない）。
- **フェーズ番号を消費しない**（次フェーズは引き続き `10_<topic>`）。
- **1 項目 = 1 コミット**。項目 0 →項目 1 →項目 2 →項目 3 の順（項目 3 は単独でも可）。
- 判断の記録先は `.claude_data/state/decisions.md` の**「計画07」節**
  （フェーズではないため `decisions_archive/` は作らない）。
- **本計画自体が `/refactor_check` の産物**のため、完了時の `/refactor_check` は不要。
- 実装は `codex-implementer` へ委任 → **`verifier` で実測** → `reviewer`（`.claude/rules/agent_selection.md`）。

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

## 項目 0: 安全網の確認（先行・必須）→ **調査完了（2026-08-16・`Explore`）→ 特性テストを追加中**

分割前に、対象領域が既存テストで守られていることを確認する。**不足していれば特性テストの追加を先に行う。**

- 対象 = `PresetManagerDialog` の UI 契約（`spec_detail/data_schema.md` §5.10.3 の
  「プリセットマネージャの UI 契約」）。
- 既存カバレッジ: **`tests_ui/test_app_ui_flows.py` の 1 ファイルに集中**（`tests/` に UI 契約のテストは無い）。
  契約 1〜5（OK / キャンセルの不変性・トグルの読み直し・破棄確認・OFF で開いた時点の一覧確定・
  上書き確認の 3 択と adopt / cancel）は**強い**。

### 判明した空白（＝抽出で壊れても検知されない）

1. **`_update_source_labels()` 本体（`dialogs.py:495-523`）が完全に無テスト** — 最大の穴。
   テストされているのは**純関数 `format_preset_manager_source_labels` だけ**で、
   `resolve_hotkey_presets_save_path(..., individual=)` の呼び分け・`external` 系での既定パス再解決・
   3 つの `Var` への `set()` がすべて未検証。**契約 6・7 の「理由表示」も実質ここが未カバー**。
2. **`__init__` が初期化する状態**（`_individual_state` / `_displayed_source` /
   `_global_hotkey_presets_path` / `_keymap_set_saved`）。トグル系テストはヘルパが
   **`object.__new__` で手埋めする**ため、`__init__` の初期化が壊れても検知されない。
3. **イベント配線**（`Checkbutton(command=...)` / `listbox.bind("<Double-Button-1>", ...)`）。
   既存テストはハンドラを**直接呼ぶ**ので配線が外れても green。
   → **本提案書 項目 1 の「`_bind_events` の順序」リスクはテストで守られていない**。
4. **`suspend_hook_for_dialog` / `resume_hook_after_dialog` の呼出**（patch されるだけで assert 無し）。
5. **`_refresh()` による listbox の実内容**（実構築テストは `_temp` しか見ない）。

### 追加する特性テスト（項目 1 の着手前・**実構築**で書く）

(a) 実構築ダイアログの `save_destination_var` / `source_var` / `individual_unavailable_var` の実値
（OFF + グローバル可 / ON + 個別可 / **ON + config 外**〔既定パスへの再解決〕の 3 ケース）/
(b) **`individual_check.invoke()` 経由**（＝ `command` 配線込み）のトグル /
(c) `suspend_hook_for_dialog` / `resume_hook_after_dialog` の呼出 assert /
(d) `listbox.get(0, "end")` の内容。

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
- **完了条件**: `-m unittest discover -s tests_ui` が pass（**項目 0 で追加した分を含む件数から減らさない**）/
  `-m tests.smoke_app` が pass / `__init__` が **40 行以内**。
- **リスクと戻し方**: 構築順序が変わると Tk の変数トレースが初期化前に発火し得る。
  **`_bind_events` は状態と widget の構築後**に置く。単一ファイル内の移動のみなので `git checkout` で戻せる。
- **【厳守】`_refresh` と `_update_source_labels` のメソッド名を変えない**。
  `tests_ui/test_app_ui_flows.py` の **9 箇所以上が `patch.object(PresetManagerDialog, "_refresh")` /
  `"_update_source_labels"` でクラス属性を差し替えている**ため、リネームすると全滅する
  （項目 0 の調査で判明）。抽出で作る新しい private メソッドは**別名**にする。
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
    preset_manager.py      # PresetManagerDialog / format_preset_manager_source_labels
    preset_dialog.py       # PresetDialog（※実装時に分離。下記サイズ条件）
    trigger_dialog.py      # TriggerDialog
    keymap_edit_dialog.py  # KeymapEditDialog
    layout_delete_dialog.py# LayoutDeleteDialog
  ```
  - **`PresetDialog` は `preset_dialog.py` へ分ける**（`preset_manager.py` を 400 行以内に収めるため。
    `preset_manager → preset_dialog` の一方向依存で循環しない）。
  - **`__init__.py` の再輸出は互換レイヤー禁止の対象外**（公開面の定義。
    `file_organization_rules.md`「本リポジトリへの適用注記」）。
    ただし **`from .x import *` は使わず明示列挙**する。
  - **旧パスに横流し専用モジュールを残さない**（恒久互換レイヤーの禁止）。
- **完了条件**: **production の import 4 ファイルが無変更で通る**
  （`app.py` / `controllers/keymap_panel_controller.py` / `controllers/layout_controller.py` /
  `controllers/trigger_panel_controller.py`。いずれも `from keyseq.presentation.dialogs import ...`）/
  `-m compileall -q keyseq main.py tests tests_ui` clean /
  `tests` **238** + `tests_ui`（項目 0 で増えた件数）+ smoke がいずれも pass（**件数を減らさない**）/
  各ファイルが 400 行以内。
- **【判明済・要対応】`tests_ui/test_app_ui_flows.py` の 6 箇所が壊れる**（項目 0 の調査）:
  `patch("keyseq.presentation.dialogs.tk.Toplevel.destroy")`（3 箇所）と
  `patch("keyseq.presentation.dialogs.messagebox.askyesno")`（3 箇所）。
  `tk` / `messagebox` は共有モジュールオブジェクトなので**patch の効果自体はどの経路でも同じ**で、
  壊れるのは**属性解決だけ**（`__init__.py` に `tk` / `messagebox` 属性が無く `AttributeError`）。
  → **対応 = テスト側の patch 文字列を実体モジュール
  （`keyseq.presentation.dialogs.preset_manager.messagebox.askyesno` 等）へ更新する**。
  **アサーションは変えない**（安全網を弱めない）。
  `__init__.py` へ `tk` / `messagebox` を import して属性を維持する案は、
  **公開面でないものを公開面に置く互換維持**になるため採らない。
- **影響しない patch**（そのまま動く。壊さないこと）:
  `patch("keyseq.presentation.app.PresetManagerDialog")`（`app.py` が名前を自分の名前空間へ
  import し続ける限り安全）/ `patch.object(PresetManagerDialog, ...)`（クラス属性 patch）/
  各 `tests_ui` の fail-fast ガード（`controllers/config_io/*` の名前空間を指しており、
  共有モジュールオブジェクトのため**分割後も `dialogs` 側の `messagebox` を間接的に守る**）。
- **【循環 import の注意】**（項目 0 の調査）:
  - クラス間の依存は **`ActionDialog` → `PresetManagerDialog`** と
    **`PresetManagerDialog` → `PresetDialog`** の 2 本のみ（一方向）。
    `action_dialog.py` からの参照は **サブモジュール直指定**
    （`from keyseq.presentation.dialogs.preset_manager import PresetManagerDialog`）にする。
    パッケージ経由（`from . import ...`）にすると `__init__.py` の列挙順次第で
    **部分初期化パッケージの `ImportError`** になる。
  - **`from keyseq.presentation.app import App` は各ファイルで `if TYPE_CHECKING:` ガードの中に置く**
    （外に出すと `app → dialogs.preset_manager → app` の**真の循環**になる）。
  - モジュールレベルの共有物は `tk` / `ttk` / `messagebox` / `mouse`（`ActionDialog` のみ）/
    `format_preset_list_item` / `safe_deepcopy`（`PresetManagerDialog` のみ）/
    `normalize_key_name` / `normalize_tk_keysym`。**モジュール定数は 0 件**。
- **リスクと戻し方**: 分割は純粋な移動なので `git checkout` で戻せる。
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

## 実施タイミング（起票時の選択肢・**(b) で確定済 → 上部「実施形態」節が正**）

- (a) 同フェーズ末の追加タスク（`task_09_refactor` として起票）
  → **不採用**。phase 09 は正本反映まで終えて**すでに閉じている**（`current.md` 更新・
  `decisions_archive/09` 作成済）ため、追加タスクは閉じたフェーズを開け直すことになる。
- **(b) 次フェーズ前の独立ミニ計画** → **採用**（計画05 / 計画06 と同型。
  挙動保存のみで仕様確定の反復が不要なため、暫定仕様先行モードに載せない）。
