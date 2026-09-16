# task_03_pane_drag_and_window_min

## 目的

task_02 の `PaneLayoutController` を拡張し、**境界線ドラッグの可動範囲制限・中ボタン無効・希望幅と表示幅の保持・
収まらない場合の一括適用と `wm minsize`・フォント変更後の再計算・省略表示との切替順**を実装する。
根拠: 暫定仕様 16（v0.3）§2-2・§2-3・§2-6・§2-9・§2-11・§2-12 / §3-2 / §3-4（ウィンドウ最小幅・省略表示との関係）/
§3-5 / §3-7。

**presentation 限定。`pane_width_rules.py` の関数を使う（同モジュールは変更しない）。
保存（`write_startup`）と起動時の保存値の復元は入れない（task_04）。スキーマ不変。**
実装は **Claude `implementer`**（Codex 利用上限のためユーザー許可 2026-09-16）。

## 対象範囲（presentation 限定・変更 2 + テスト新規 1）

### 1. `keyseq/presentation/controllers/pane_layout_controller.py`（拡張）

**状態**

- `self.desired: PaneWidths | None` — 希望幅（§3-5）。task_02 の `apply_default_widths()` で**既定幅を入れる**
  （task_04 で保存値があればそれに置き換える）。
- `self.min_widths: MinWidths | None` — 直近に実測した最小幅。
- 省略表示中にフォントが変わったことを示すフラグ（例 `self._remeasure_pending`）。
- ドラッグ状態（押下したサッシュの番号 / 押下位置とサッシュ座標の差 / その側の枠の開始時の表示幅）。**押下がサッシュ上でなければ持たない**。

**レイアウト適用 `apply_layout()`**（§3-7。起動時の初回・フォント変更後・フル表示へ戻った後に共通で呼ぶ）

1. `update_idletasks()` 後に `resolve_layout(desired, min_widths, sash_total=2*SASH_WIDTH,
   window_extra=app.winfo_width() − panes.winfo_width(), current_window_width=app.winfo_width(),
   screen_width=app.winfo_screenwidth())` で最終値を 1 回だけ計算する。
2. **`app.minsize(plan.window_min_width, 1)`**（高さは制約しない）。
3. **ウィンドウ幅が変わる場合だけ** `app.geometry(f"{plan.window_width}x{現在の高さ}")`（位置は変えない）。
   **途中の値を geometry に当てない**。
4. `update_idletasks()` 後、`paneconfigure(keymap_box, width=plan.keymap)` / `paneconfigure(sequence_box, width=plan.sequence)`、
   3 枠の `paneconfigure(minsize=...)` を最小幅で更新する。
- task_02 の `apply_default_widths()` は「最小幅の実測 → 既定幅を `desired` へ → `apply_layout()`」に置き換える
  （初回 `<Configure>` で 1 回だけ呼ばれる点は維持。**既定配置が変更前と一致する task_02 のテストを壊さない**）。

**ドラッグ（§3-2・§3-5）** — `panes` の**インスタンスバインド**で処理し、標準のクラスバインドを `"break"` で止める:

- `<Button-1>`: `panes.identify(x, y)` がサッシュ（戻り値が `(index, "sash")` 相当）ならドラッグ状態を記録して `"break"`。
  サッシュ以外なら何もせず標準処理に任せる（`"break"` しない）。
- `<B1-Motion>`: ドラッグ中なら、押下時の差を保ったまま**その側の枠の新しい幅**を求め、
  `drag_limits(total_width=panes.winfo_width(), own_min=…, other_side_width=反対側の枠の現在幅, trigger_min=…, sash_total=…)` +
  `clamp` で制限して `paneconfigure(その枠, width=…)` を当て `"break"`。
  - サッシュ 0 → キーマップ管理の幅 = サッシュの左端 x。サッシュ 1 → 出力シーケンスの幅 = `panes.winfo_width() − (サッシュの左端 x + SASH_WIDTH)`。
  - **反対側の枠の幅・ウィンドウ幅は変えない**（差分はトリガー一覧が吸収）。
- `<ButtonRelease-1>`: **ドラッグ中だった場合だけ** `update_desired_after_drag(desired, side, 開始時の表示幅, 現在の表示幅)` で
  `desired` を更新し、ドラッグ状態を消して `"break"`。**変化があったかを戻り値で判定できるようにする**
  （例: 変化時に呼ぶ内部メソッド `_on_desired_changed(new)` を置き、**本タスクでは `desired` の更新と
  `app.minsize` の再計算だけ**を行う。保存は task_04 がここに足す）。
- `<Button-2>` / `<B2-Motion>` / `<ButtonRelease-2>`: 常に `"break"`（中ボタンでサッシュを動かさない・§2-12）。
- 結線は task_02 の `install()` で**1 回だけ**、`add="+"` で行う（`"break"` を返すハンドラは `add="+"` でも標準のクラスバインドを止める）。

**フォント変更（§3-4）** — `on_font_changed()`:

- **省略表示中**（`app._compact_mode` が真）: `app.minsize` を触らず、再計算が必要という印だけ立てる。
- **フル表示中**: 最小幅を再実測して `apply_layout()`。**`desired` は変えない**（表示幅だけ最小幅へ引き上がる）。

**省略表示との切替（§3-4）**

- `release_window_min_size()`: `app.minsize(1, 1)`。
- `on_full_view_shown()`: 印が立っていれば最小幅を再実測して印を消す → `apply_layout()`。

**初回適用前の呼び出し**: `min_widths` / `desired` が未確定（初回 `<Configure>` 前）の間は、
`on_font_changed` / `on_full_view_shown` / ドラッグは**何もしない**（例外を出さない）。

### 2. `keyseq/presentation/app.py`（結線のみ）

- `_apply_font_delta`: `apply_global_theme(...)` の**直後**に `self.pane_layout.on_font_changed()`（`write_startup` の呼び出し順・引数は変えない）。
- `show_compact_view`: **`self._apply_compact_geometry()` より前**に `self.pane_layout.release_window_min_size()`。
- `show_full_view`: **`self._restore_full_geometry()` の後**に `self.pane_layout.on_full_view_shown()`。
- それ以外の初期化順序・既存処理は変えない。

### 3. `tests_ui/test_pane_drag_and_window_min.py`（新規）

前例: `tests_ui/test_full_view_panes.py`（共有 App・`write_startup` の patch・`addCleanup` での復元）。
**config を書かない。geometry / pane 幅 / `desired` / font delta / 表示モード / `minsize` をテスト後に元へ戻す。**
ドラッグは `panes.event_generate("<Button-1>"|"<B1-Motion>"|"<ButtonRelease-1>", x=…, y=…)` で合成する
（サッシュ座標は `panes.sash_coord(i)`）。最低限:

1. **サッシュ 0 を右へ限界まで**: キーマップ管理が広がり、**出力シーケンスの幅とウィンドウ幅は不変**、トリガー一覧は最小幅で止まる（§5-2・§5-3）。
2. **サッシュ 1 を左へ限界まで**: 対称（キーマップ管理とウィンドウ幅は不変）。
3. **サッシュ 0 を左へ限界まで**: キーマップ管理は最小幅で止まる。
4. **中ボタン**（`<Button-2>` → `<B2-Motion>` → `<ButtonRelease-2>`）では幅が変わらない（§5-4）。
5. **ドラッグで `desired` が更新**され、動かした側だけ変わる。**サッシュ以外で押して離しても `desired` は変わらない**（§5-8）。
6. **無効ドラッグ**（§5-9・v0.3）: `desired.keymap` を最小幅未満にして `apply_layout()` → キーマップ管理は最小幅で表示 →
   サッシュ 0 を左へドラッグして離しても `desired.keymap` は元の値のまま。続けてサッシュ 1 を動かしても `desired.keymap` は元の値のまま。
7. **ウィンドウ最小幅**（§5-6）: `app.wm_minsize()[0]` が「両端の表示幅 + トリガー一覧の最小幅 + 24 + window_extra」と一致し、
   それより狭い geometry を当てても両端の枠の幅は変わらない。
8. **省略表示**（§5-7）: `show_compact_view()` 後に `app.wm_minsize() == (1, 1)` かつ幅 270。`show_full_view()` 後に `wm_minsize()[0]` が 7 の値に戻る。
9. **省略表示中のフォント変更**（§5-7）: 省略表示中に font delta を変えても `wm_minsize()` は `(1, 1)` のまま・幅 270 のまま。
   フル表示へ戻すと最小幅が再実測されている（delta を上げた場合、キーマップ管理の最小幅が元より大きい）。
10. **フル表示中のフォント変更**（§5-9 前半）: delta を上げると表示幅が最小幅以上に引き上がり、`desired` は変わらない。
11. **画面幅超過**（§5-12）: `app.winfo_screenwidth` を小さい値に patch し、`app.geometry` の呼び出しを記録して `desired` を大きくして `apply_layout()` →
    **記録された幅がすべて画面幅以下**・出力シーケンスが先に縮む・`desired` は不変。

## 設計メモ / 制約

- **`pane_width_rules.py` を変更しない**。計算はそこで済ませ、コントローラは測定・適用・イベント処理だけを持つ。
- `panes.identify` の戻り値は Tk のバージョンで形が揺れうるため、**サッシュ判定は 1 か所の小さなメソッドにまとめる**。
- コントローラが **250 行を超える場合**は、`.claude/rules/file_organization_rules.md` の親フォルダ方式
  （`controllers/pane_layout/pane_layout_controller.py` + ドラッグ処理の補助モジュール）で分割してよい。
  その場合 `app.py` の import 先も更新する。**分割したかどうかを報告する**。
- `tests_ui/test_full_view_panes.py`（task_02）の**アサーションを変えない**。apply_layout の導入で落ちた場合は実装側を直す。
  直せない理由がある場合は変更せず報告する。
  - **実装時の判断（メインセッション）**: test_05 はウィンドウを 3 枠の最小幅の合計まで狭める手順を含み、
    本タスクの `wm minsize`（§3-4・仕様どおり）に止められて失敗した。**アサーション・期待値は変えず**、
    **準備で `app.minsize(1, 1)` を呼び、後始末で元の最小幅へ戻す**形だけを許可した。
  - **テスト 8・9 の比較**: Windows の Tk は `minsize(1, 1)` 後も `wm_minsize()` がシステム下限 `(120, 1)` を返すため、
    **使い捨て Toplevel に `minsize(1, 1)` を当てて読んだ値**と一致することで「解除済み」を判定する。
- 関数はおおむね 30 行以内。keyboard フック・既存の表示切替ガード（キャプチャ中は切り替えない）を壊さない。

## 含まない

- `desired` の保存（`write_startup`）・起動時に保存値を読んで `desired` にする処理・保存値の検証の結線（**task_04**）
- 正本 / `codebase_map.md` の更新（**task_06**）
- キーボードによるサッシュ移動 / 省略表示のレイアウト変更（スコープ外）

## 確認

python は `../../../.venv/Scripts/python.exe`（素の `python` / `py` は使わない）。実測は `verifier`。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests_ui.test_pane_drag_and_window_min -v` が全 pass（上記 1〜11 が存在）。
3. `-m unittest tests_ui.test_full_view_panes -v` が 6 件 pass（task_02 のテストが無変更で通る）。
4. `-m unittest discover -s tests` が 441 実行 OK（skip 7）。
5. `-m unittest discover -s tests_ui` が全 pass（357 + 追加）。
6. `-m tests.smoke_app` が SMOKE OK。
7. `git diff --stat` が対象範囲のファイルのみ（分割した場合はその新ファイルを含む）。`git status --short config` が空。

## 完了条件

- 上記確認 pass・**`reviewer` 採用**。
- 実機目視は **task_05 でまとめて実施**（ドラッグの手触り・カーソル表示を含む）。

## 完了記録（2026-09-17）

- `reviewer` = 修正要（ドラッグ後のウィンドウ最小幅を独自式で算出 → `resolve_layout` へ一本化）→ 修正済み。
  テスト側の `_expected_window_min()` は実装と独立した検証として残した。
- **既知の残存（task_05 の二次レビュー・実機目視で扱う）**: 画面幅超過で表示幅が縮められている状態でドラッグすると、
  ウィンドウ最小幅は `resolve_layout` が**希望幅から**再計算する値になり、実際の表示幅の合計と一致しない場合がある
  （画面幅より広いレイアウトでのみ起きる。現テストは未カバー）。
