# task_03_mode_transition_polish.md

## 配置層

presentation のみ

## 目的

通常モードを中継点とする統一された遷移規則を仕上げる。
具体的には:

- **すべての非通常モードからの Esc 復帰先を NORMAL に統一**
- **編集モードのダイアログ外クリックで編集キャンセル → NORMAL 復帰**
- **UI クリック後でもキー入力主体は ApplicationMode 制御側にある**ことを確認

仕様正本: `instructions/common/spec_detail/key_input.md` §6.1 / §6.2、`features.md` 4.8（編集モード）

---

## 実装内容

### A. Esc 復帰の通常モード一元化

- `src/presentation/input_controller.py` の各モード Esc ハンドラを点検
- `CUSTOM_CREATE` / `CONNECT` / `HELP` から Esc で NORMAL に戻ることを確認 / 修正
  - 既存実装で動いている場合は無変更
  - 復帰時に選択ノード ID / ビュー状態が破綻しないこと

### B. 編集モードのダイアログ外クリックでキャンセル

- `src/presentation/edit_overlay.py` または `canvas_widget.py` で、編集オーバーレイ表示中にキャンバス領域がクリックされた場合の挙動を点検
- 仕様: ダイアログ外クリックは Esc 相当として編集をキャンセルする
- 現挙動が仕様と異なる場合のみ修正

### C. UI クリック後のキー操作権

- メニューやヘルプダイアログ等を一度クリックした後でも、キャンバスにキー入力が届くことを確認
- 必要なら `canvas_widget.setFocus()` 系の呼び出しを追加（ただし最小限）

---

## 要件

- domain / application 層は変更しない
- 既存の各モード本体ロジックは変更しない（遷移先の整理のみ）
- 通常モードのマウス操作は無変更
- VIEW / GRID モードは本タスクでは扱わない（task_04 / task_05 でも Esc 復帰は同じ規則に従う）

---

## 完了条件

### 機能面

- 各モードで Esc を押下すると通常モードに戻る
  - CUSTOM_CREATE / CONNECT / HELP / DIALOG（既存）
- 編集モード中にキャンバス領域をクリックすると編集がキャンセルされ、NORMAL に戻る
- ヘルプダイアログを表示 → 閉じた後でも、キャンバスのキー入力が機能する

### 静的確認

- `python -m compileall -q src main.py` がクリーン
- domain / application 層に PySide6 import が増えていないこと

### レビュー

- サブエージェントレビュー（仕様適合性 / 不要変更の有無 / 既存挙動への影響）
- 判定明示

---

## 注意事項

- 既存挙動が既に仕様通りなら無変更で完了扱いにしてよい
- 「念のため」のフォーカス強制設定は最小限に。既存動作が壊れる可能性あり
- IME 未確定状態時の Esc は IME 側に渡す既存挙動を維持（key_input.md §5.2 IME ルール）

---

## スコープ外

- VIEW / GRID モードの追加（task_04 / task_05）
- キーマップ変更（task_02）
- 描画変更
