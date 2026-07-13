# 目的

既存の Python アプリに以下の機能を追加する。

* キーボード表示UI（別ウィンドウ）
* キーマップ機能（単キー → 単キー）
* キーボードUIからのキーマップ編集
* トリガーとの共存

既存機能

* トリガー
* 出力シーケンス
* グローバルキーフック

との互換性を維持すること。

---

# 使用ライブラリ

必ず以下を使用する。

```
Python
tkinter
keyboard
```

---

# 重要設計ルール

入力処理は必ず次の3クラスに分ける。

```
KeyStateManager
InputRouter
ActionExecutor
```

keyboard.hook の callback は **Router に渡すだけ**にする。

---

# 入力処理アーキテクチャ

```
keyboard.hook
      │
      ▼
KeyStateManager
      │
      ▼
InputRouter
      │
      ▼
ActionExecutor
```

---

# keyboard.hook

フック関数は次のみ行う。

```
router.handle(event)
```

それ以外の処理は禁止。

---

# KeyStateManager

押されているキー状態を管理する。

保持

```
pressed_keys
```

更新

```
keydown → add
keyup → remove
```

提供する関数

```
is_pressed(key)
get_modifiers()
```

対象修飾キー

```
shift
ctrl
alt
windows
```

---

# InputRouter

Routerは

```
keyboard event → Action
```

へ変換する。

---

# Router処理順

必ず次の順序で処理する。

```
1 send_guard確認
2 hook_pause確認
3 KeyState更新
4 停止キー
5 通常モード切替キー
6 キーマップ切替キー
7 トリガー判定
8 キーマップ判定
9 通常入力
```

---

# Action構造

Routerは Action を返す。

例

```
SendKeyAction
TriggerAction
ToggleModeAction
SwitchKeymapAction
```

---

# ActionExecutor

ActionExecutor が Action を実行する。

役割

```
keyboard.press
keyboard.release
トリガー実行
状態変更
```

send_guard管理もここ。

---

# send_guard

send による再帰を防ぐ。

```
send_guard += 1
keyboard.press()
keyboard.release()
send_guard -= 1
```

Router最初に

```
if send_guard > 0:
    return
```

---

# hook_pause

UI編集時にフック停止する。

```
hook_pause += 1
hook_pause -= 1
```

Router開始時

```
if hook_pause > 0:
    return
```

---

# キーマップ仕様

キーマップは

```
単キー → 単キー
```

例

```
q → 7
z → 1
```

---

# 修飾キー透過

物理入力

```
shift + q
```

キーマップ

```
q → 7
```

結果

```
shift + 7
```

修飾キーは send に含めない。

---

# キー送信ルール

禁止

```
keyboard.send("shift+7")
```

使用

```
keyboard.press(key)
keyboard.release(key)
```

---

# keyup処理

keyupでは

```
KeyStateManager更新のみ
```

キーマップ処理は禁止。

---

# suppress

keyboard.hook は

```
suppress=True
```

で登録する。

---

# 予約キー

次のキーは予約キー。

```
停止キー
通常モード切替キー
キーマップ切替キー
```

制約

```
トリガー使用禁止
キーマップ元キー禁止
```

---

# トリガー優先

同一キーに

```
トリガー
キーマップ
```

両方ある場合

```
トリガー優先
```

---

# キーボードUI

別ウィンドウとして実装。

```
KeyboardWindow
```

描画

```
tkinter.Canvas
```

---

# キー描画

キー情報

```
id
label
x
y
w
h
```

unitベースで描画する。

---

# リサイズ

Canvasサイズ変更時

```
unit再計算
全キー再描画
```

---

# キー表示内容

キーキャップには

```
実行結果
```

のみ表示。

ルール

```
trigger → 番号
keymap → 出力キー
normal → 元キー
```

---

# キー編集

操作

```
左クリック → 編集待機
キー入力 → 置換設定
Esc → キャンセル
右クリック → クリア
```

---

# JSON構造

```
config.json
keymap_sets/
keymaps/
trigger_sets/
hotkey_presets/
```

---

# keymap_sets

keymap_set.json

内容

```
停止キー
通常モード切替キー
キーマップ切替キー
default keymap
default trigger_set
trigger enabled
```

---

# UIスレッドルール

フックからUIを直接操作してはいけない。

UI更新は

```
root.after()
```

で行う。

---

# 禁止事項

次のコードは禁止。

```
keyboard.write
keyboard.send("shift+x")
フック内UI更新
フック内JSON保存
sleep
```

---

# 最重要ルール

次の3クラス構造を必ず守る。

```
KeyStateManager
InputRouter
ActionExecutor
```

フック処理にロジックを書かない。

---

# 実装順

次の順序で実装する。

1

```
Keyboard UI描画
```

2

```
KeyStateManager
```

3

```
InputRouter
```

4

```
ActionExecutor
```

5

```
キーマップ機能
```

6

```
UI編集機能
```

---

# 既存機能

既存の

```
トリガー
シーケンス
JSON
```

機能を壊さないこと。

---


