# task_02_keymap_to_wasd.md

## 配置層

presentation のみ

## 目的

通常モードのクイック作成キーを **Tab / Shift+Tab / Ctrl+↑ / Ctrl+↓ → W / A / S / D** に置換する。
さらに新モード入口キー **V（ビューモード）/ G（グリッドモード）** を通常モードに追加する。

仕様正本: `instructions/common/spec_detail/key_input.md` §5.1 / §8

---

## 実装内容

### A. `src/presentation/key_map.py`

- `_NORMAL_BINDINGS` から以下を削除:
  - `KeyBinding(int(Qt.Key_Tab), _NO_MOD, Action.QUICK_CREATE_RIGHT)`
  - `KeyBinding(int(Qt.Key_Backtab), _SHIFT, Action.QUICK_CREATE_LEFT)`
  - `KeyBinding(int(Qt.Key_Tab), _SHIFT, Action.QUICK_CREATE_LEFT)`
  - `KeyBinding(int(Qt.Key_Up), _CTRL, Action.QUICK_CREATE_UP)`
  - `KeyBinding(int(Qt.Key_Down), _CTRL, Action.QUICK_CREATE_DOWN)`

- `_NORMAL_BINDINGS` に以下を追加:
  - `KeyBinding(int(Qt.Key_W), _NO_MOD, Action.QUICK_CREATE_UP)`
  - `KeyBinding(int(Qt.Key_A), _NO_MOD, Action.QUICK_CREATE_LEFT)`
  - `KeyBinding(int(Qt.Key_S), _NO_MOD, Action.QUICK_CREATE_DOWN)`
  - `KeyBinding(int(Qt.Key_D), _NO_MOD, Action.QUICK_CREATE_RIGHT)`
  - `KeyBinding(int(Qt.Key_V), _NO_MOD, Action.ENTER_VIEW_MODE)`
  - `KeyBinding(int(Qt.Key_G), _NO_MOD, Action.ENTER_GRID_MODE)`

### B. `src/shared/actions.py`

- `Action` 列挙体に以下を追加（実体は本タスクでは未実装、定義のみ）:
  - `ENTER_VIEW_MODE = "enter_view_mode"`
  - `ENTER_GRID_MODE = "enter_grid_mode"`
- 注: ビュー / グリッドモード本体のアクション群（`view_scroll_*` / `grid_select_*` 等）は task_04 / task_05 で追加する

### C. `src/presentation/input_controller.py`

- `ENTER_VIEW_MODE` / `ENTER_GRID_MODE` の受口を追加（本タスクでは未遷移ハンドラとして "未実装" feedback を出すだけで良い）
  - 例: `self._feedback.info("ビューモードは未実装")` 程度
  - task_04 / task_05 で本実装に置換する

### D. `src/presentation/key_guide.py` / 関連ヘルプ表示

- フッターのキー表示（`↑↓←→ 選択移動 Enter 編集開始 ...`）を新キーマップに合わせて更新
- Tab / Shift+Tab / Ctrl+↑↓ の表示を撤去
- WASD（クイック作成）/ V / G の追加表示
- ヘルプダイアログ（`src/presentation/help_dialog.py`）も同様に更新

---

## 要件

- domain / application 層は変更しない
- アクション列挙体への追加は最小限（`ENTER_VIEW_MODE` / `ENTER_GRID_MODE` のみ）
- 既存のクイック作成ロジック（`src/application/quick_create.py`）には触らない（キー → アクション → 既存 usecase の経路を維持）
- 既存の Ctrl+S / Ctrl+O / Ctrl+N / F1 / 矢印 / Enter / Delete / N / C は無変更
- マウス操作は無変更

### 維持するキー一覧（task_02 で削除しないこと）

2026-05-08 ユーザー判断で仕様 §5.1 に追加 / 残置決定された通常モードの補助キーボードショートカット。本タスクで誤って削除しないこと。

| キー | 修飾 | アクション | ソース |
|---|---|---|---|
| Ctrl + + | Ctrl | ZOOM_IN | [src/presentation/key_map.py:42](src/presentation/key_map.py:42) |
| Ctrl + = | Ctrl | ZOOM_IN | [src/presentation/key_map.py:43](src/presentation/key_map.py:43) |
| Ctrl + - | Ctrl | ZOOM_OUT | [src/presentation/key_map.py:44](src/presentation/key_map.py:44) |
| Ctrl + 0 | Ctrl | ZOOM_RESET | [src/presentation/key_map.py:45](src/presentation/key_map.py:45) |
| F | NoMod | FOCUS_SELECTED | [src/presentation/key_map.py:46](src/presentation/key_map.py:46) |
| Shift + F | Shift | FIT_TO_VIEW | [src/presentation/key_map.py:47](src/presentation/key_map.py:47) |

### Tab フォーカストラバース対策（必須）

Tab / Shift+Tab / Backtab を `_NORMAL_BINDINGS` から削除すると、Qt が既定で「フォーカス遷移キー」として再解釈し、canvas 以外のフォーカス可能ウィジェットへフォーカスが飛ぶリスクがある（task_01 §G-3 参照）。

**対策（採用済 / 案 a）**: [src/presentation/canvas_widget.py](src/presentation/canvas_widget.py) の `keyPressEvent` 冒頭で `Qt.Key_Tab` / `Qt.Key_Backtab` を検知し `event.accept()` で消費する。Signal は emit せず、それ以上の処理も行わない。

```python
def keyPressEvent(self, event: QKeyEvent) -> None:
    key = event.key()
    if key == Qt.Key_Tab or key == Qt.Key_Backtab:
        event.accept()
        return
    # 既存処理...
```

注: Qt の `Key_Tab` は IntEnum なので `int()` 直接 OK（PySide6 6.11 互換ルールに従う）。

---

## 完了条件

### 機能面

- 通常モードで W / A / S / D を押下するとクイック作成が動作する（既存の動作と一致）
- Tab / Shift+Tab / Ctrl+↑ / Ctrl+↓ を押下しても何も起きない（フォーカスが canvas 外へ飛ばないこと = 案 a の対策が効いていること）
- V / G を押下するとフィードバック表示（または未実装メッセージ）が出る
- 通常モードで Ctrl + + / Ctrl + = / Ctrl + - / Ctrl + 0 / F / Shift + F が**従来どおり**動作する（既存挙動を壊していないこと）
- key_guide フッターとヘルプダイアログの内容が新キーマップと一致

### 静的確認

- `python -m compileall -q src main.py` がクリーン
- domain / application 層に PySide6 import が増えていないこと

### レビュー

- 別エージェントによるサブエージェントレビュー（仕様適合性 / 依存方向 / 責務分離 / 不要変更の有無 / チェック漏れ）
- 判定: 採用 / 修正して採用 / 保留 / 除外

---

## 注意事項

- **WASD と矢印キーの衝突に注意**: 現実装は矢印キーが選択移動。本タスクで WASD を追加してもクイック作成のキー（W/A/S/D）と衝突しない
- **WASD のキーリピート**: `key_input.md` §2.5「移動系は長押し可」「作成系は単発のみ」に従う。クイック作成は単発のため、長押し時の連続発火が起きないことを確認
- ENTER_VIEW_MODE / ENTER_GRID_MODE のハンドラ未実装は task_04 / task_05 で完成させる前提

---

## スコープ外

- ビューモード / グリッドモードの本実装（task_04 / task_05）
- 自動拡張（task_09）
- 描画変更（task_06 以降）
