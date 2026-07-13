# key_input_policy.md

## 1. 目的

本ドキュメントは、マインドマップツールにおけるキー入力処理の統一方針を定義する。
キー入力はモードベースで解釈し、予測可能かつ一貫した操作体験を提供する。
本方針は特定のUIフレームワークに依存しない設計とし、複数実装間で共通の操作体系を維持できるようにする。

---

## 2. 基本方針

### 2.1 モードベース入力処理

キー入力は以下の要素に基づいて解釈する。

* キー
* 修飾キー（Ctrl / Shift / Alt など）
* 現在モード
* フォーカス状態

```text
キー入力 + 修飾キー + モード + フォーカス状態 → アクション
```

---

### 2.2 入力対象の優先順位

キー入力の処理対象は以下の優先順位で決定する。

1. ダイアログ・ポップアップ
2. テキスト入力（編集モード）
3. キャンバス操作
4. グローバル操作

---

### 2.3 編集モードと非編集モードの分離

| 状態     | 挙動        |
| ------ | --------- |
| 編集モード  | 文字入力を優先する |
| 非編集モード | 操作キーとして扱う |

編集モード中は、通常モードのショートカットを無効化する。

---

### 2.4 IME制御

| 状態     | IME        |
| ------ | ---------- |
| 編集モード  | 有効         |
| 非編集モード | 無効、または英数固定 |

補足:

* 編集モード中は文字入力を最優先する
* 非編集モードではショートカット誤爆防止を優先する

---

### 2.5 長押しの扱い

| 種類        | 挙動   |
| --------- | ---- |
| 移動系       | 長押し可 |
| 作成・削除・確定系 | 単発のみ |

長押し可の対象例:

* 通常モードでの選択移動
* カスタム作成モードでの配置カーソル移動
* 接続モードでの接続先候補移動

長押し不可の対象例:

* ノード作成
* ノード削除
* 編集確定
* 接続確定
* 保存
* 新規作成

---

## 3. モード一覧

本ツールでは、少なくとも以下のモードを持つ。

* 通常モード
* 編集モード
* カスタム作成モード
* 接続モード
* ヘルプモード
* ダイアログモード

補足:

* クイック作成は通常モード内のアクションとして扱う
* ヘルプモードとダイアログモードは見た目が近くても内部状態としては分離する

---

## 4. アクション定義

キー入力は直接処理せず、いったんアクションへ変換してから実処理へ渡す。

```text
キー入力 → アクション → 実処理
```

主なアクション例:

* move_selection_up
* move_selection_down
* move_selection_left
* move_selection_right
* start_edit
* confirm_edit
* cancel_edit
* delete_node
* quick_create_right
* quick_create_left
* quick_create_up
* quick_create_down
* start_custom_create
* move_custom_cursor_up
* move_custom_cursor_down
* move_custom_cursor_left
* move_custom_cursor_right
* confirm_custom_create
* cancel_custom_create
* start_connection
* move_connection_target_up
* move_connection_target_down
* move_connection_target_left
* move_connection_target_right
* confirm_connection
* cancel_connection
* open_help
* close_help
* confirm_dialog
* close_dialog
* save_map
* load_map
* create_new_map

---

## 5. モード別キー割り当て

### 5.1 通常モード

#### 目的

* ノード操作
* モード遷移
* 基本的な編集開始

#### キー割り当て

| キー          | アクション                |
| ----------- | -------------------- |
| ↑           | move_selection_up    |
| ↓           | move_selection_down  |
| ←           | move_selection_left  |
| →           | move_selection_right |
| Enter       | start_edit           |
| Delete      | delete_node          |
| Tab         | quick_create_right   |
| Shift + Tab | quick_create_left    |
| Ctrl + ↑    | quick_create_up      |
| Ctrl + ↓    | quick_create_down    |
| N           | start_custom_create  |
| C           | start_connection     |
| F1          | open_help            |
| Ctrl + S    | save_map             |
| Ctrl + O    | load_map             |
| Ctrl + N    | create_new_map       |

---

### 5.2 編集モード

#### 目的

* ノードテキストの入力・編集

#### キー割り当て

| キー           | アクション        |
| ------------ | ------------ |
| Ctrl + Enter | confirm_edit |
| Esc          | cancel_edit  |
| Enter        | 改行           |
| 文字キー         | テキスト入力       |

#### 制約

* 通常モードのショートカットは無効化する
* 編集モード中は文字入力を最優先する

#### IMEに関する追加ルール

* 編集モード中に未確定のIME変換が存在する場合、Esc はまずIME側のキャンセルに使う
* IME未確定状態が存在しない場合のみ、アプリケーション側の編集キャンセルを行う

---

### 5.3 カスタム作成モード

#### 目的

* 任意位置へのノード作成

#### キー割り当て

| キー    | アクション                    |
| ----- | ------------------------ |
| ↑     | move_custom_cursor_up    |
| ↓     | move_custom_cursor_down  |
| ←     | move_custom_cursor_left  |
| →     | move_custom_cursor_right |
| Enter | confirm_custom_create    |
| Esc   | cancel_custom_create     |

---

### 5.4 接続モード

#### 目的

* ノード間接続の作成

#### キー割り当て

| キー    | アクション                        |
| ----- | ---------------------------- |
| ↑     | move_connection_target_up    |
| ↓     | move_connection_target_down  |
| ←     | move_connection_target_left  |
| →     | move_connection_target_right |
| Enter | confirm_connection           |
| Esc   | cancel_connection            |

---

### 5.5 ヘルプモード

#### 目的

* 操作説明の表示

#### キー割り当て

| キー    | アクション                |
| ----- | -------------------- |
| Esc   | close_help           |
| ↑ / ↓ | move_selection       |
| Enter | confirm_dialog または無効 |

#### 制約

* 背後のキャンバス操作を無効化する

---

### 5.6 ダイアログモード

#### 目的

* 確認・通知・選択操作

#### キー割り当て

| キー    | アクション          |
| ----- | -------------- |
| Esc   | close_dialog   |
| Enter | confirm_dialog |
| ↑ / ↓ | move_selection |

#### 制約

* 背後のキャンバス操作を無効化する

---

## 6. 共通ルール

### 6.1 Esc の統一動作

Esc キーは「現在の状態を1段階戻す」動作とする。

| 状態        | 挙動        |
| --------- | --------- |
| 編集モード     | 編集キャンセル   |
| カスタム作成モード | モード終了     |
| 接続モード     | モード終了     |
| ヘルプモード    | ヘルプを閉じる   |
| ダイアログモード  | ダイアログを閉じる |

補足:

* 編集モードでは IME 未確定状態を優先する

---

### 6.2 Enter の統一動作

Enter キーは「現在対象の確定」または「対象操作への遷移」に寄せる。

| 状態        | 挙動   |
| --------- | ---- |
| 通常モード     | 編集開始 |
| カスタム作成モード | 作成確定 |
| 接続モード     | 接続確定 |
| ダイアログモード  | 決定   |
| 編集モード     | 改行   |

---

## 7. 実装指針

### 7.1 キーマッピングはテーブルで管理する

キーとアクションの対応はハードコードしない。

最低限、以下の要素を持つテーブル構造で管理する。

* mode
* key
* modifiers
* action

---

### 7.2 入力処理と実処理を分離する

以下の構造を必ず守る。

```text
キー入力 → アクション変換 → 実処理
```

入力イベント内で直接業務ロジックを書かない。

---

### 7.3 フォーカス管理

* 編集中はテキスト入力対象にフォーカスを移す
* 非編集時はキャンバスにフォーカスを戻す
* ダイアログ表示中はダイアログへフォーカスを移す

---

### 7.4 モード管理

状態は単一の状態管理で保持する。

例:

* NORMAL
* EDIT
* CUSTOM_CREATE
* CONNECT
* HELP
* DIALOG

複数モードが曖昧に重ならないようにする。

---

### 7.5 キー割り当ての差し替え性

キー割り当ては固定実装にせず、定義テーブルから読み込む構造にする。

MVPでは以下のいずれかで保持すればよい。

* コード内の定義テーブル
* 設定ファイル

将来的には、ユーザー設定によるキー割り当て上書きを可能にする。

---

## 8. MVP推奨キーセット

MVPでは少なくとも以下を実装対象とする。

* 矢印キー（選択移動）
* Enter（編集開始）
* Ctrl + Enter（編集確定）
* Esc（キャンセル）
* Delete（削除）
* Tab / Shift + Tab（左右クイック作成）
* Ctrl + ↑ / ↓（上下クイック作成）
* N（カスタム作成）
* C（接続）
* Ctrl + S（保存）
* F1（ヘルプ）

---

## 9. まとめ

本設計は以下を実現する。

* モードによる明確な責務分離
* 予測可能なキー操作
* IMEとの安全な共存
* 拡張可能なキーマッピング構造
* 複数実装間で統一しやすい操作体系

これにより、キーボード主体でも快適に操作できるUIを実現する。
