# task_01_audit_current_state.md

## 配置層

調査のみ（コード変更なし）

## 目的

`mvp_refine` フェーズの後続タスクを安全に進めるため、**現状の実装と仕様の差分**を整理する。
Proposal の Phase 0「着手前確認」に相当。

このタスクではコードを変更しない。出力は調査結果のドキュメントのみ。

---

## 調査内容

### A. モード一覧
- `src/shared/actions.py` の `Mode` 列挙体を確認
- 仕様（`key_input.md` §3）との差分を整理
- 不足モード: `VIEW` / `GRID`

### B. キーマップ
- `src/presentation/key_map.py` の現キーバインディング全件を表に起こす
- 仕様（`key_input.md` §5）との差分を整理
- 削除予定キー（Tab / Shift+Tab / Ctrl+↑ / Ctrl+↓）と追加予定キー（W/A/S/D/V/G）を明示

### C. フォーカス取得箇所
- `src/presentation/canvas_widget.py` / `main_window.py` でキー入力を受ける場所を特定
- ダイアログ表示時のフォーカス挙動
- UI クリック後のキー操作権の受け渡し

### D. グリッド描画と保存
- `src/presentation/painters.py` `draw_grid` の描画範囲ロジック
- `src/domain/map_state.py` の保存対象構造
- 描画範囲が保存範囲に依存している箇所を特定

### E. マウス操作
- `src/presentation/canvas_widget.py` の `mousePressEvent` / `wheelEvent` 等
- パン / ズーム / クリック選択の現挙動を整理
- 通常モード以外（CUSTOM_CREATE / CONNECT 等）でのマウス挙動

### F. アクション一覧
- `src/shared/actions.py` の `Action` 列挙体
- 仕様（`key_input.md` §4）で追加予定のアクションリスト
- 既存に追加 / 撤去 / 維持を分類

---

## 出力物

調査結果を以下のいずれかで残す:

- 本タスクファイル末尾に「### 調査結果」セクションを追記
- もしくは `instructions/phase/02_mvp_refine/audit_result.md` を別途作成

最低限以下を含めること:

1. モード一覧の差分表（現実装 / 仕様 / 追加 / 維持）
2. キーマップの差分表（現実装 / 仕様 / 削除 / 追加 / 維持）
3. フォーカス受け取り位置の一覧
4. グリッド描画範囲を決めている箇所のファイル名・行番号
5. マウス操作の各イベントハンドラの責務一覧
6. アクション列挙体の差分表
7. リスクが高い箇所（後続タスクで気をつけるべき点）

---

## 完了条件

- 上記出力物がすべて揃っている
- 差分が表形式で整理されている
- リスク箇所が言語化されている
- サブエージェントレビュー（仕様適合性 / 抜け漏れ / 過剰調査の有無）が完了している

---

## 注意事項

- コードは変更しない
- `__pycache__` / `.venv` 等は読まない
- 一気に全ファイルを舐めず、§A〜§F の順に必要箇所だけ確認する
- 後続タスクの先取り実装にならないよう、調査結果には「修正案の概要」までは書いてよいが「実装」は書かない

---

## スコープ外

- コード修正
- 仕様書修正
- 後続タスクの実装

---

## 調査結果

調査日: 2026-05-08

### A. モード一覧（差分表）

ソース: [src/shared/actions.py:6-11](src/shared/actions.py)

| # | 現実装（Mode） | 仕様（key_input.md §3 / §7.4） | 差分 |
|---|---|---|---|
| 1 | `NORMAL` | 通常モード | 維持 |
| 2 | `EDIT` | 編集モード | 維持 |
| 3 | `CUSTOM_CREATE` | カスタム作成モード | 維持 |
| 4 | `CONNECT` | 接続モード | 維持 |
| 5 | `HELP` | ヘルプモード | 維持 |
| 6 | （なし） | ビューモード | **追加: `Mode.VIEW`** |
| 7 | （なし） | グリッドモード | **追加: `Mode.GRID`** |
| 8 | （なし） | ダイアログモード | 本フェーズではスコープ外。必要なら別途 backlog 化を検討 |

注: 既存メンバ名は rename しない方針（`phase.md` / handoff 注意事項）。`VIEW` / `GRID` を追加するのみ。

---

### B. キーマップ（差分表）

ソース: [src/presentation/key_map.py](src/presentation/key_map.py)（dict 構造 `_BINDINGS_BY_MODE`、解決関数 `resolve_action()`）

#### B-1. 通常モード

| キー | 修飾 | 現アクション | 仕様アクション (§5.1) | 判定 |
|---|---|---|---|---|
| ↑↓←→ | NoMod | MOVE_SELECTION_* | move_selection_* | 維持 |
| Enter / Return | NoMod | START_EDIT | start_edit | 維持 |
| Delete | NoMod | DELETE_NODE | delete_node | 維持 |
| **Tab** | NoMod | QUICK_CREATE_RIGHT | （定義なし。§5.1 制約で「主要キーから外す」） | **削除** |
| **Tab** | Shift | QUICK_CREATE_LEFT | （定義なし） | **削除**（key_map.py:33 のエントリ） |
| **Backtab** | Shift | QUICK_CREATE_LEFT | （定義なし） | **削除**（key_map.py:32 のエントリ。task_02 で 2 件あることに注意） |
| **Ctrl+↑** | Ctrl | QUICK_CREATE_UP | （定義なし） | **削除** |
| **Ctrl+↓** | Ctrl | QUICK_CREATE_DOWN | （定義なし） | **削除** |
| **W** | NoMod | （未定義） | quick_create_up | **追加** |
| **A** | NoMod | （未定義） | quick_create_left | **追加** |
| **S** | NoMod | （未定義） | quick_create_down | **追加** |
| **D** | NoMod | （未定義） | quick_create_right | **追加** |
| **V** | NoMod | （未定義） | enter_view_mode | **追加** |
| **G** | NoMod | （未定義） | enter_grid_mode | **追加** |
| N | NoMod | START_CUSTOM_CREATE | start_custom_create | 維持 |
| C | NoMod | START_CONNECTION | start_connection | 維持 |
| F1 | NoMod | OPEN_HELP | open_help | 維持 |
| Ctrl+S | Ctrl | SAVE_MAP | save_map | 維持 |
| Ctrl+O | Ctrl | LOAD_MAP | load_map | 維持 |
| Ctrl+N | Ctrl | CREATE_NEW_MAP | create_new_map | 維持 |
| Ctrl++ | Ctrl | ZOOM_IN | zoom_in（§5.1 表に追加済 2026-05-08） | **維持**（G-1 採用済） |
| Ctrl+= | Ctrl | ZOOM_IN | zoom_in（同上） | **維持**（G-1 採用済） |
| Ctrl+- | Ctrl | ZOOM_OUT | zoom_out（§5.1 表に追加済 2026-05-08） | **維持**（G-1 採用済） |
| Ctrl+0 | Ctrl | ZOOM_RESET | zoom_reset（同上） | **維持**（G-1 採用済） |
| F | NoMod | FOCUS_SELECTED | focus_selected（§5.1 表に追加済 2026-05-08。§5.7 ビューモードでは `view_zoom_out`、モード別解決で衝突なし） | **維持**（G-2 採用済） |
| Shift+F | Shift | FIT_TO_VIEW | fit_to_view（§5.1 表に追加済 2026-05-08） | **維持**（G-2 採用済） |

#### B-2. 編集モード

| キー | 修飾 | 現アクション | 仕様アクション (§5.2) | 判定 |
|---|---|---|---|---|
| Ctrl+Enter / Ctrl+Return | Ctrl | CONFIRM_EDIT | confirm_edit | 維持 |
| Esc | NoMod | CANCEL_EDIT | cancel_edit | 維持 |

#### B-3. カスタム作成モード

| キー | 修飾 | 現アクション | 仕様アクション (§5.3) | 判定 |
|---|---|---|---|---|
| ↑↓←→ | NoMod | MOVE_CUSTOM_CURSOR_* | move_custom_cursor_* | 維持 |
| Enter / Return | NoMod | CONFIRM_CUSTOM_CREATE | confirm_custom_create | 維持 |
| Esc | NoMod | CANCEL_CUSTOM_CREATE | cancel_custom_create | 維持 |

#### B-4. 接続モード

| キー | 修飾 | 現アクション | 仕様アクション (§5.4) | 判定 |
|---|---|---|---|---|
| ↑↓←→ | NoMod | MOVE_CONNECTION_TARGET_* | move_connection_target_* | 維持 |
| Enter / Return | NoMod | CONFIRM_CONNECTION | confirm_connection | 維持 |
| Esc | NoMod | CANCEL_CONNECTION | cancel_connection | 維持 |

#### B-5. ヘルプモード

| キー | 修飾 | 現アクション | 仕様アクション (§5.5) | 判定 |
|---|---|---|---|---|
| Esc | NoMod | CLOSE_HELP | close_help | 維持 |
| F1 | NoMod | CLOSE_HELP | （仕様に明記なし、トグルとして残置） | 維持（補助） |

#### B-6. ビューモード（**全件追加**）

仕様 §5.7 のとおり、以下を新設:

| キー | 修飾 | 追加アクション |
|---|---|---|
| W / A / S / D | NoMod | view_scroll_up / left / down / right |
| W / A / S / D | Shift | view_scroll_fast_up / left / down / right |
| R | NoMod | view_zoom_in |
| F | NoMod | view_zoom_out |
| Space | NoMod | view_select_nearest_node |
| Enter / Return | NoMod | view_create_at_center |
| Esc | NoMod | exit_view_mode |

#### B-7. グリッドモード（**全件追加**）

仕様 §5.8 のとおり、以下を新設（推奨キーを採用）:

| キー | 修飾 | 追加アクション |
|---|---|---|
| R | NoMod | grid_select_axis_row |
| C | NoMod | grid_select_axis_column |
| T | NoMod | grid_toggle_target_scope |
| ← / ↑ | NoMod | grid_select_line_prev |
| → / ↓ | NoMod | grid_select_line_next |
| + / = | NoMod | grid_increase_spacing |
| - | NoMod | grid_decrease_spacing |
| Esc | NoMod | exit_grid_mode |

---

### C. フォーカス取得箇所

| 場所 | 行 | 役割 |
|---|---|---|
| [src/presentation/canvas_widget.py:44](src/presentation/canvas_widget.py:44) | 44 | `setFocusPolicy(Qt.StrongFocus)` — キャンバスがキー入力を受ける |
| [src/presentation/canvas_widget.py:173](src/presentation/canvas_widget.py:173) | 173-174 | `keyPressEvent` 実装（Signal emit へ） |
| [src/presentation/main_window.py](src/presentation/main_window.py) | -- | `keyPressEvent` 未実装（MainWindow 自身は処理しない） |
| [src/presentation/input_controller.py:367](src/presentation/input_controller.py:367) | 367, 379, 390 | EDIT 終了時に `self._canvas.setFocus(Qt.OtherFocusReason)` |
| [src/presentation/edit_overlay.py:27](src/presentation/edit_overlay.py:27) | 27 | `begin_edit()` で overlay にフォーカス移動 |

ダイアログ（HelpDialog 等）は Qt 標準のフォーカス挙動に依存。明示的なフォーカス制御は無し。

---

### D. グリッド描画と保存

#### D-1. 描画範囲を決めている箇所

| 箇所 | 内容 |
|---|---|
| [src/presentation/painters.py:29-58](src/presentation/painters.py:29) `draw_grid` | グリッド線・交点描画 |
| [src/presentation/painters.py:32](src/presentation/painters.py:32) | `world_extent(state)` で `(width, height)` を算出（columns / rows の合計） |
| [src/presentation/painters.py:33-34](src/presentation/painters.py:33) | `column_x_positions(state)` / `row_y_positions(state)` で各 x / y 配列 |
| [src/presentation/painters.py:40-48](src/presentation/painters.py:40) | `for x in xs + [width]` / `for y in ys + [height]` で線を引く |

→ **描画範囲は MapState.columns / rows（保存対象）に直接依存**。ビューポートに連動しない。

#### D-2. 保存対象データ構造

| 箇所 | 内容 |
|---|---|
| [src/domain/map_state.py:9-15](src/domain/map_state.py:9) | `MapState(nodes, edges, rows, columns, positions)` |
| [src/domain/map_state.py:147-171](src/domain/map_state.py:147) | `set_grid()` — 行/列差し替え |
| [src/infrastructure/json_storage.py:37-45](src/infrastructure/json_storage.py:37) | `_state_to_layout()` — JSON は `columns[]` / `rows[]` / `positions{}` を保存 |

→ **rows / columns は描画範囲と保存範囲の両方を兼ねている**。task_06 で分離が必要。

---

### E. マウス操作

| ハンドラ | 行 | 責務 |
|---|---|---|
| `mousePressEvent` | [canvas_widget.py:176-182](src/presentation/canvas_widget.py:176) | Middle: パン開始（カーソル変更）／Left: `mouse_clicked` emit |
| `mouseMoveEvent` | [canvas_widget.py:184-190](src/presentation/canvas_widget.py:184) | パン中（Middle 押下中）のみ `pan_dragged` emit |
| `mouseReleaseEvent` | [canvas_widget.py:192-195](src/presentation/canvas_widget.py:192) | Middle 解放でパン終了 |
| `wheelEvent` | [canvas_widget.py:197-201](src/presentation/canvas_widget.py:197) | スクロール量・座標・修飾を `wheel_scrolled` emit |

モード別マウス挙動（[input_controller.py:111-147](src/presentation/input_controller.py:111)）:

| モード | 左クリック挙動 |
|---|---|
| NORMAL | ノード上 → ノード選択 ／ 交点上 → CUSTOM_CREATE 開始 |
| CUSTOM_CREATE | 交点上 → カーソル位置更新 |
| CONNECT | ノード上 → 接続先候補更新 |
| EDIT / HELP | （未分岐、特別処理なし） |

→ パン（Middle）／ホイールズームはモード非依存。仕様 §5.1 / 4.10 に従い「モード横断で維持」する方向と整合。

---

### F. アクション一覧（差分表）

ソース: [src/shared/actions.py:14-50](src/shared/actions.py:14)（現状 36 メンバ）

#### F-1. 維持（既存）

`MOVE_SELECTION_*` / `START_EDIT` / `CONFIRM_EDIT` / `CANCEL_EDIT` / `DELETE_NODE` / `QUICK_CREATE_*` / `START_CUSTOM_CREATE` / `MOVE_CUSTOM_CURSOR_*` / `CONFIRM_CUSTOM_CREATE` / `CANCEL_CUSTOM_CREATE` / `START_CONNECTION` / `MOVE_CONNECTION_TARGET_*` / `CONFIRM_CONNECTION` / `CANCEL_CONNECTION` / `OPEN_HELP` / `CLOSE_HELP` / `SAVE_MAP` / `LOAD_MAP` / `CREATE_NEW_MAP`

#### F-2. 維持（仕様外だが補助として残置候補）

| 既存アクション | 補足 |
|---|---|
| `ZOOM_IN` / `ZOOM_OUT` / `ZOOM_RESET` | 通常モード Ctrl+± のショートカット。§5.1 表には無いが「マウス操作を変更しない」原則と整合させ、キー側も維持を推奨（→ task_02 で確認） |
| `FOCUS_SELECTED` / `FIT_TO_VIEW` | 通常モードの F / Shift+F。WASD 移行で衝突しないが、§5.1 仕様外なので残置可否判断が必要（→ task_02 / G-2 参照） |

#### F-3. 追加（仕様 §4 / §5.7 / §5.8）

ビューモード系（13）:
- `ENTER_VIEW_MODE` / `EXIT_VIEW_MODE`
- `VIEW_SCROLL_UP` / `_DOWN` / `_LEFT` / `_RIGHT`
- `VIEW_SCROLL_FAST_UP` / `_DOWN` / `_LEFT` / `_RIGHT`
- `VIEW_ZOOM_IN` / `VIEW_ZOOM_OUT`
- `VIEW_SELECT_NEAREST_NODE` / `VIEW_CREATE_AT_CENTER`

グリッドモード系（10）:
- `ENTER_GRID_MODE` / `EXIT_GRID_MODE`
- `GRID_SELECT_AXIS_ROW` / `GRID_SELECT_AXIS_COLUMN`
- `GRID_TOGGLE_TARGET_SCOPE`
- `GRID_SELECT_LINE_PREV` / `GRID_SELECT_LINE_NEXT`
- `GRID_INCREASE_SPACING` / `GRID_DECREASE_SPACING`

ダイアログ系（仕様 §5.6 / §6.2 で言及あり、現実装は無し）:
- `CONFIRM_DIALOG` / `CLOSE_DIALOG` — 本フェーズスコープ外（DIALOG モードを追加しないため、追加するかは task_03 で判断）

---

### G. リスクが高い箇所（後続タスクで気をつけるべき点）

#### G-1. Ctrl+± / Ctrl+0 ズームショートカットの扱い

- 現実装: NORMAL モードの Ctrl+Plus / Ctrl+Equal / Ctrl+Minus / Ctrl+0 が ZOOM_IN / OUT / RESET。
- 仕様 §5.1 の通常モード表には記載なし → **2026-05-08 ユーザー判断で §5.1 表へ追加 / 残置決定**。
- **判定: 採用**（仕様反映済 / コード変更なし）。task_02 では当該キーバインディングを**削除しない**こと。

#### G-2. F / Shift+F の扱い（FOCUS_SELECTED / FIT_TO_VIEW）

- 現実装: NORMAL の F = FOCUS_SELECTED、Shift+F = FIT_TO_VIEW。
- 仕様 §5.7 では F = view_zoom_out（**ビューモード**）。NORMAL 表には無い。
- **衝突なし**（モード別なので NORMAL の F と VIEW の F は別解決）。仕様 §5.1 にない既存キーだったが、**2026-05-08 ユーザー判断で §5.1 表へ追加 / 残置決定**。
- **判定: 採用**（仕様反映済 / コード変更なし）。task_02 では F / Shift+F の既存バインディングを**削除しない**こと。

#### G-3. Tab / Shift+Tab の Qt 既定挙動への戻り

- Tab / Shift+Tab を NORMAL のキーマップから外すと、Qt が**フォーカス遷移キー**として再解釈する可能性がある。
- canvas_widget は `Qt.StrongFocus` だが、ウィンドウ内に他フォーカス可能ウィジェット（EditOverlay 等）があれば Tab でフォーカスが移動 → NORMAL のキー入力が来なくなる事故リスク。
- **対策候補**（task_02 で検討）: keyPressEvent で Tab を「無視」せず明示的に消費する／`focusPolicy` で Tab トラバースを抑止／`event.accept()` を確実に行う。

#### G-4. WASD と既存テキスト系操作の衝突

- 現状 NORMAL の S / D / W / A は未割当。Ctrl+S（保存）と修飾子で区別される。問題なし。
- ただし将来 `start_edit` 後の EDIT モードでは WASD は文字入力。NORMAL→EDIT 遷移時にキーリピート途中の取り扱いに注意（task_03 で確認）。

#### G-5. グリッド描画と保存の癒着（task_06 / 07 / 09 の前提）

- `draw_grid` が `MapState.rows / columns` を直接参照しており、ビューポート連動描画に切り替えるには「描画用範囲」を別途算出する必要がある。
- 保存対象（layout.json）は引き続き `rows[] / columns[]` の N×M を維持（§4.4 描画/保存分離）。
- task_06 で「描画範囲のみ可変、保存範囲は固定」の責務分離を導入する設計が必要。
- 自動拡張（task_09）は domain/application 層の責務で、`set_grid` 系の使い回しではなく「端を超えた」検知ロジックを別途設ける必要がある。

#### G-6. ビューポート連動描画とパフォーマンス

- 無限グリッド（task_07）では描画範囲がビューポートに連動。`for x in xs + [width]` 方式から「画面に映る x 範囲だけ列計算」に変える。
- 既存 `column_x_positions` / `row_y_positions` の **N×M 前提を崩さない**まま、描画ループ側で「保存範囲外の追加グリッド線」を補助計算する形が最小差分（task_07 で検討）。

#### G-7. PySide6 6.11 互換（再掲）

- `event.modifiers()` / `event.button()` の戻り値、`Qt.NoModifier` 等の Flag enum は `int()` 直接不可。`.value` 経由（[canvas_widget.py:182, 199](src/presentation/canvas_widget.py:182) で対応済）。
- `Qt.Key_*` (IntEnum) は `int()` で OK。
- 新モード追加時のキーバインディングでも同方針を踏襲する。

#### G-8. モード遷移時のフォーカス整合（task_03 / task_04 の前提）

- VIEW / GRID 復帰時、選択ノードや表示位置の不整合（仕様 §5.7 補足「選択位置と表示位置に不整合が生じない」）を満たすため、入退場時に `selected_node` / `view_state` の同期点を明示する設計が必要。
- 既存 `input_controller._on_edit_canceled` / `_confirmed` のように、明示的な状態クリーン処理を VIEW / GRID にも実装する。

#### G-9. モード表示 UI（task_10）

- 現状、UI に「現在モード」表示が存在しない。`key_guide.py` がモード別キー一覧を表示しているが、現在モード自体は明示されていない可能性が高い（task_10 で確認）。
- WASD が NORMAL=クイック作成、VIEW=スクロール、GRID=軸選択 と一意ではないため、視認 UI は必須。

---

### 修正案の概要（着手前メモ。実装は各タスクで）

- **task_02**: `Mode.VIEW` / `Mode.GRID` を `actions.py` に追加 → アクション enum を追加 → `key_map.py` に WASD / V / G + 新モード分の bindings 追加 / Tab 系 bindings 削除。G-1 / G-2 / G-3 を確認。
- **task_03**: Esc 統一・編集モードのダイアログ外クリックでキャンセル → `input_controller` のモード遷移実装の見直し。
- **task_04 / 05**: 新モード固有の入力ハンドラとアクション処理を `input_controller` に追加。VIEW では着地操作（Space / Enter）の application use case が必要。
- **task_06**: `painters.draw_grid` のループを「描画範囲（ビューポート連動）」と「保存範囲（MapState 由来）」に分離。
- **task_07**: ビューポート連動でグリッド線本数を動的計算（保存外の領域でも線を引く）。
- **task_08**: 縮小時に描画スキップ（閾値 = ズーム率比較）。
- **task_09**: 端での自動拡張は domain（rows / columns 配列拡張）と application（拡張トリガー検出）を分離して実装。クイック作成 / カスタム作成 / VIEW Enter 着地の 3 経路すべてに対応。
- **task_10**: `key_guide.py` 周辺、または別ウィジェットで現在モードを表示。

---

### サブエージェントレビュー

- レビュー実施日: 2026-05-08
- 観点: 仕様適合性 / 完了条件充足 / 過剰調査の有無 / チェック漏れ / 責務分離・依存方向 / 後続タスクの先取り実装
- 結果: **採用（参考指摘あり）**
- レビュアー指摘とその反映:
  1. 表 A 行8「ダイアログモード」の補足を「task_03 で要再確認」→「本フェーズではスコープ外。必要なら別途 backlog 化を検討」に修正済
  2. G-1 / G-2 の結論先取りを撤回し「本タスクでは保留。task_02 で正式判断」に統一済
  3. 表 B-1 で Tab / Shift+Tab / Backtab を別行に展開済（key_map.py の 2 エントリを task_02 で見落とさないため）
  4. Ctrl++ / Ctrl+= も別行に分離済（同 2 エントリ）
- 判定記録は `.claude_data/state/decisions.md` に追記
