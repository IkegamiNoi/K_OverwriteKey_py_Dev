# task_07b_normalize_presets_on_read

## 目的

task_07 の `deep-reviewer` 指摘のうち、**ユーザーが「是正」と判断した 4 件**を最小差分で直す
（規範 = 暫定仕様 07 **v0.6**）。

| # | 内容 | 規範 |
|---|---|---|
| H1 | **グローバルプリセットの読み出しが正規化済みの値を返すようにする**（注入経路 E1/E3/E4/E5 が非正規化のままだった） | v0.6 **§3-2**「読み出しは正規化済みの値を返す」/ 受入条件 **7** |
| M1 | **死にコード `load_named_list` の削除** | `anti_patterns.md` 8「仮置きの放置」 |
| M2 | **入口台帳 E1（App 初期化）の特性テスト追加** | 受入条件 **7** |
| L3 | `App.save_hotkey_presets` の **deepcopy** | 他の runtime 更新箇所との流儀統一 |

**レイヤ制約**: **domain（純関数の切り出し）+ application（読み出しでの適用・死にコード削除）+
presentation（deepcopy 1 行）**。**UI・スキーマ・保存側は不変**。挙動変更は H1 のみ。

## 対象範囲

### 1. `keyseq/domain/config.py` — 正規化ロジックの切り出し（H1）

`ensure_config_compatibility` 内のプリセット正規化ブロック（**`:171-183`**）を、
**同ファイルの純関数へ切り出す**:

```python
def normalize_hotkey_presets(presets: Any) -> list[dict[str, Any]]:
    """プリセット一覧を正規化する（非 dict 要素は除去・label は trim・value は trim + 小文字化）。"""
```

- `ensure_config_compatibility` は**この関数を呼ぶ形へ置き換える**（**挙動は完全に不変**）。
  現状の分岐（`list` でなければ `DEFAULT_CONFIG["hotkey_presets"]` の deepcopy へ縮退）は
  **`ensure_config_compatibility` 側に残す**。純関数は「`list` を受けて正規化した `list` を返す」
  責務だけを持つ（`list` 以外を渡された場合は空リストを返す）。
- **正規化の中身は 1 文字も変えない**（`safe_deepcopy` → `label` の `strip` →
  `value` の `strip` + `lower` → 非 dict はスキップ）。

### 2. `keyseq/application/config_service/split_loading.py`

- **H1**: `load_global_hotkey_presets` の戻り値を **`normalize_hotkey_presets(...)` を通した値**にする。
  - **`None` の判定は正規化の前**に行う（読めた `list` は、正規化で空になっても `list` のまま返す）。
  - 通常読込（`build_runtime_data_from_split`）はこの後さらに `ensure_config_compatibility` を
    通るが**冪等**なので変更不要。
- **M1**: **`load_named_list` を削除**する（`keyseq` / `tests` / `tests_ui` に呼び出し 0 件を確認済み）。
  使われなくなった import が出たら併せて削除する。

### 3. `keyseq/presentation/app.py`（L3）

- `save_hotkey_presets` の `self.data["hotkey_presets"] = presets` を
  **`safe_deepcopy(presets)` の代入**へ変える（成功時のみ反映する契約は不変）。
  `safe_deepcopy` は `keyseq.domain.config` からの import（既存の import 状況に合わせる）。

### 設計メモ / 制約

- **正規化は読み出し側 1 箇所に置く**。`apply_global_defaults` 側へは置かない（v0.6 §3-2）。
- **`apply_global_defaults` の契約は不変**（冪等・例外を投げない・`None` なら置き換えない）。
- **保存側は正規化しない**（`save_global_hotkey_presets` は受け取った値をそのまま書く。
  マネージャ経由の値は UI 側で検証済み）。
- 受入条件 **8**（ON→OFF でプリセットを再読込しない）・**9**（空は採用 / `None` は非置換）に
  影響を与えないこと。

## 含まない

- **M3（`None` 時に上書き内容が入口経路で割れる）の実装的解消** → **採らないと確定**
  （v0.6「既知の制約」へ明文化済み。`new_empty_data` を変えない・確認ダイアログを足さない）
- 破損ファイルの**検知・警告・退避** → 仕様上持たない
- 正本 `spec_detail/` / `codebase_map.md` への反映 → **task_08**
- L1 / L2 / L4（移行注記・Export のデッドデータ・`hotkey_presets_path` は読むだけ）→ **task_08** で文書化
- 実機目視 → **task_07** へ差し戻して実施

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **193** + 追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **185** + 追加分）
- `-m tests.smoke_app` が pass
- `grep` で **`load_named_list` が定義・参照ともに 0 件**であること

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests/test_domain_config.py`**:

1. `normalize_hotkey_presets` が **非 dict 要素を除去**し、`label` を trim、`value` を trim + 小文字化する。
2. `list` 以外（`None` / dict / 文字列）を渡すと**空リスト**を返す。
3. **冪等**（2 回通しても結果が同じ）。

**`tests/test_config_service.py`**:

4. **H1 の本体**: 非正規化のプリセットファイル
   （例: `[{"label": "  A  ", "value": "CTRL+A"}, "garbage"]`）に対して、
   **`apply_global_defaults`（注入経路）と `build_runtime_data_from_split`（通常読込）が
   同じ正規化済みの結果**（`[{"label": "A", "value": "ctrl+a"}]`）になる。
5. `load_global_hotkey_presets` が**正規化で空になっても `None` ではなく `[]` を返す**
   （例: 中身が `["garbage"]` だけのファイル。受入条件 9 の「読めた＝置き換える」を壊さない）。

**`tests_ui`**（M2）:

6. **入口台帳 E1**: `App` の初期化で `apply_global_defaults` が呼ばれること。
   `App.__init__` 全体を回すのが重い場合は、**`config_service.apply_global_defaults` を patch して
   App 生成時に 1 回呼ばれることを確認する**形でよい（既存の App 生成方法に合わせる）。
   将来 `app.py` の 1 行が消えたら落ちることが要件。

**L3 のテストは任意**（4・6 で実害が出ないため。追加するなら
「保存成功後にダイアログ側リストを書き換えても `app.data` が影響を受けない」）。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: v0.6 §3-2 との適合〔読み出し側 1 箇所で正規化・
  `None` 判定は正規化の前〕/ `ensure_config_compatibility` の挙動が不変か / 受入条件 8・9 に回帰が無いか /
  死にコード削除が過剰でないか〔他に巻き込んでいないか〕/ domain に UI 依存を持ち込んでいないか）。
- 完了後、**task_07 の実機目視へ戻る**（破損 JSON / 非 dict 要素のケースを追加観点として実施）。
