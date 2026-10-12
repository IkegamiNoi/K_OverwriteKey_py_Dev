# task_05a_pending_ratio_minsize

## 目的

完了判定前の Codex 敵対的レビュー（medium・ユーザー判断で修正）: 最大化 / 最小化中に比率が変わり、通常へ戻った後の保留の当て直し（`_apply_pending_ratio`）の予約が、
発火前に来た別の大きさの Configure で `_settle_size` の予約に置き換わると、新しい比率の `minsize` が当たらず `_ratio_pending` も残る（`features.md` §4.6「キーボード表示のウィンドウ」の「高さの下限は比率から」に反する）。
**`_settle_size` で保留中の比率を引き取る**（補正は既に新しい比率で行うため、最小サイズの当て直しと印の解除だけ足す）。
**presentation 限定（`keyboard_window.py`）・それ以外不変。**

## 対象範囲

### `keyseq/presentation/keyboard_window.py`（`_settle_size`）

- マウスのボタンの判定（押されていれば置き直して戻る）と zoomed / iconic の判定を通った後、補正の計算の前で:
  `self._ratio_pending` が真かつ `self._ratio` が None でなければ、`self._ratio_pending = False` にして `self.minsize(*minimum_size(self._ratio))` を当てる（TclError は吸収）
- それ以外の処理は変えない

### テスト（`tests_ui/test_app_ui_flows.py`・既存のキーボードUIテストの近く・後始末を守る）

- `_ratio_pending = True` の状態で、マウス未押下の差し替え・`winfo_width` / `winfo_height` を基準と違う大きさに差し替えて `_settle_size()` を呼ぶと、`minsize` が `minimum_size(window._ratio)` で呼ばれ `_ratio_pending` が False になる
- マウス押下の差し替えで呼ぶと `minsize` は呼ばれず `_ratio_pending` は真のまま

## 読むファイル

- `keyseq/presentation/keyboard_window.py`（`_on_window_configure` 〜 `_apply_ratio_to_base`）
- `tests_ui/test_app_ui_flows.py` のキーボードUIテスト（task_04b で追加した保留の当て直しのテスト）

## 含まない

- 提案書 21 のリファクタ（task_06_refactor）
- 正本の更新（条項は既に「高さの下限は比率から」で足りる）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。実機目視なし（再現に最大化 / 最小化中の切替と特定の順序が要るため UI テストで担保）。
