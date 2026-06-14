# 📘 JSON分離タスク 指示書（CodeX用）

## 🎯 目的

現在の単一 `config.json` 構造を廃止し、
**JSONを責務ごとに分離した構成へ移行する**

ただし以下を厳守する：

* **既存のUI・フック処理を壊さない**
* **ランタイム構造は維持する**
* **段階的移行（最小差分）で行う**

---

# 🧠 設計の前提（必ず理解すること）

## 1. 設計思想

今回の分離は「構造の置き換え」ではなく：

> **保存形式だけを分離し、実行時は従来構造を維持する**

---

## 2. 新しい責務構造

### 起動入口

```
config/config.json
```

役割：

* 読み込む構成（keymap_set）の指定
* UI共通設定

---

### 構成セット（実運用の中心）

```
config/user/keymap_sets/*.json
```

役割：

* keymap / trigger / preset の参照
* アプリ動作設定（stopキーなど）

---

### 実体データ

```
config/user/keymaps/*.json
config/user/trigger_sets/*.json
config/user/hotkey_presets/*.json
```

---

## 3. 参照方式

### ❗重要

* IDは使わない
* **すべてファイルパス参照**
* **configルート基準の相対パス**

例：

```json
{
  "keymap_set_path": "user/keymap_sets/default.json"
}
```

---

## 4. ランタイム構造

既存の `self.data` 構造は変更しない。

```python
self.data = {
  "triggers": [],
  "keymaps": [],
  ...
}
```

👉 分離JSONは **読み込み時にこの形へ合成する**

---

## 5. keymap設計（重要）

### 保存形式（新）

```json
{
  "active_keymap_path": "user/keymaps/default.json",
  "keymaps": [
    {
      "path": "user/keymaps/default.json",
      "switch_key": "f6"
    }
  ]
}
```

### ランタイム（既存）

```python
data["keymap_switch_keys"] = {
    "f6": "..."
}
```

👉 読込時に変換する

---

## 6. 欠損時の挙動

| ケース            | 動作      |
| -------------- | ------- |
| config.json 無い | 空データで起動 |
| keymap_set 無い  | 空データで起動 |
| trigger_set 無い | 空配列     |
| keymap 一部欠損    | そのキー無効  |

👉 messageboxで通知しつつ継続

---

## 7. 保存方針

* 初期は **一括保存のみ**
* 個別保存は後タスク

---

# 📂 新しいJSON構成（確定）

## config/config.json

```json
{
  "keymap_set_path": "user/keymap_sets/default.json",
  "ui_font_delta_pt": 0,
  "last_used_directory": ""
}
```

---

## config/user/keymap_sets/default.json

```json
{
  "trigger_set_path": "user/trigger_sets/default.json",
  "hotkey_presets_path": "user/hotkey_presets/default.json",

  "active_keymap_path": "user/keymaps/default.json",

  "keymaps": [
    {
      "path": "user/keymaps/default.json",
      "switch_key": "f6"
    }
  ],

  "hook_stop_key": "f12",
  "hook_toggle_key": "",

  "keyboard_layout": "us_tkl",
  "keyboard_show_physical_key_labels": false,
  "debug_jis_special_key_events": false,
  "external_keyboard_layouts": []
}
```

---

# 🧩 実装戦略（段階的）

## フェーズ1（今回）

* configルート導入
* パス解決の統一
* 旧settingsとの互換維持

👉 **保存形式はまだ変えない**

---

## フェーズ2

* 分離JSONの読込実装
* ランタイム合成

---

## フェーズ3

* 分離保存実装

---

# ✅ タスク分割

## タスク1

configルート導入 + パス解決統一（今回）

## タスク2

分離JSON読込

## タスク3

ランタイム合成

## タスク4

分離保存

---
