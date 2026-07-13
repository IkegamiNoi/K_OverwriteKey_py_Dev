# task_04_view_mode.md

## 配置層

presentation（主体）+ application（着地作成のユースケース連携）

## 目的

ビューモードを新規追加する。キャンバスの移動・ズームをキーボード主体で完結させ、Space / Enter による着地操作を提供する。

仕様正本:
- `instructions/common/spec_detail/key_input.md` §5.7
- `instructions/common/spec_detail/features.md` 4.12

---

## 実装内容

### A. `src/shared/actions.py`

`Action` 列挙体に以下を追加:
- `EXIT_VIEW_MODE`
- `VIEW_SCROLL_UP` / `_DOWN` / `_LEFT` / `_RIGHT`
- `VIEW_SCROLL_FAST_UP` / `_DOWN` / `_LEFT` / `_RIGHT`
- `VIEW_ZOOM_IN` / `_OUT`
- `VIEW_SELECT_NEAREST_NODE`
- `VIEW_CREATE_AT_CENTER`

### B. `src/shared/actions.py` `Mode`

- `VIEW = "view"` を追加

### C. `src/presentation/key_map.py`

`_VIEW_BINDINGS` を新設:

| キー | アクション |
|---|---|
| W | VIEW_SCROLL_UP |
| A | VIEW_SCROLL_LEFT |
| S | VIEW_SCROLL_DOWN |
| D | VIEW_SCROLL_RIGHT |
| Shift+W | VIEW_SCROLL_FAST_UP |
| Shift+A | VIEW_SCROLL_FAST_LEFT |
| Shift+S | VIEW_SCROLL_FAST_DOWN |
| Shift+D | VIEW_SCROLL_FAST_RIGHT |
| R | VIEW_ZOOM_IN |
| F | VIEW_ZOOM_OUT |
| Space | VIEW_SELECT_NEAREST_NODE |
| Enter | VIEW_CREATE_AT_CENTER |
| Esc | EXIT_VIEW_MODE |

`_BINDINGS_BY_MODE` に `Mode.VIEW: _VIEW_BINDINGS` を追加。

### D. `src/presentation/input_controller.py`

- `ENTER_VIEW_MODE`（task_02 で追加済）のハンドラを本実装にする
  - `self._enter_mode(Mode.VIEW)`
  - フィードバック「ビューモード: WASD 移動 / Shift+WASD 高速 / R/F ズーム / Space 着地選択 / Enter 着地作成 / Esc 復帰」
- 各 VIEW_* アクションのハンドラを追加
  - スクロール: `view_state` の `pan(dx, dy)` を呼ぶ。スクロール量と高速時の倍率は定数で
  - ズーム: 既存の zoom 機構を流用（画面中心アンカー）
  - VIEW_SELECT_NEAREST_NODE: 画面中心 → ワールド座標に変換 → 全ノード距離比較で最近接を選択 → NORMAL 復帰
  - VIEW_CREATE_AT_CENTER: 画面中心 → 最近接空き交点 → 自動拡張（task_09 完了前は保存範囲内クランプ）→ ノード作成 → EDIT へ遷移
- EXIT_VIEW_MODE: NORMAL 復帰

### E. ビューモードでのマウスクリック挙動（features.md 4.12 マウス操作）

- `canvas_widget.mousePressEvent` で `Mode.VIEW` 中の左クリックは「ノード選択 + NORMAL 復帰」を実行
- パン / ズームのマウス挙動はモード横断で従来通り

### F. key_guide / help_dialog

- VIEW モード用の表示行を追加
- 現在モードに応じてフッター表示を切り替える既存機構があれば流用

---

## 要件

- domain は変更しない
- application は VIEW_CREATE_AT_CENTER のために `application/view_landing.py`（新規）または既存 usecase を拡張
- ビュー / 描画変換は既存の `view_state.py` / `coordinate_system.py` を流用
- 「最近接交点」探索は既存 `find_nearest_intersection` を再利用
- VIEW_CREATE_AT_CENTER の自動拡張は task_09 完了後に有効化される。本タスク段階では保存範囲内に最近接交点が存在する場合のみ作成、なければフィードバック警告

---

## 完了条件

### 機能面

- 通常モード中に V キーでビューモードへ遷移
- WASD でスクロール、Shift+WASD で高速スクロール、R / F でズーム
- Space で画面中心の最近接ノードを選択 → NORMAL 復帰
- Enter で画面中心の最近接空き交点へノード作成 → EDIT 遷移 → 編集確定後 NORMAL 復帰
- Esc で NORMAL 復帰
- マウスのパン / ズームはビューモード中も同じ挙動で利用可能
- マウス左クリックで最近接ノード選択 + NORMAL 復帰

### 静的確認

- `compileall` クリーン
- domain 層に PySide6 import が増えていない
- application 層に PySide6 import が増えていない

### レビュー

- サブエージェントレビュー（仕様適合性 / 依存方向 / 責務分離 / 不要変更の有無）

---

## 注意事項

- スクロール量・高速倍率・ズーム倍率は定数で。設定化は将来検討
- VIEW モード中の選択ノード ID は維持してよい（NORMAL 復帰時に有効）
- VIEW_CREATE_AT_CENTER で保存範囲外の最近接交点を扱う処理は task_09 と接続する。本タスクでは「保存範囲内クランプ」or「警告のみ」の暫定実装で良い
- WASD のキーリピート（長押し）は許可（移動系のため）

---

## スコープ外

- 自動グリッド拡張（task_09）
- 無限グリッド描画（task_07）
- グリッドモード（task_05）
- モード表示 UI（task_10）
