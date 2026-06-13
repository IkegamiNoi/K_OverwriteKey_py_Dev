# JSON仕様

## 重要

- 後方互換必須
- 未定義キーは無視

---

## 基本構造

{
  "triggers": [...],
  "hotkey_presets": [...],
  "hook_stop_key": "f12"
}

---

## 拡張キー

### run_to_end

- 型：bool
- 連続実行

### run_to_end_delay_ms

- 型：int
- デフォルト：300

---

## ルール

- 既存キー削除禁止
- 意味変更禁止

---

## 分離JSONの本流

| 機能 | 形式 |
| --- | --- |
| 保存 | split |
| 読込 | split |
| 起動 | split |
| Import | 単一JSON |
| Export | 単一JSON |

---

## split読込

- 通常読込では `keymap_set.json` を直接選択する
- `config/config.json` は起動時に読む `keymap_set_path` を保持する
- `keymap_set.json` は trigger_set / hotkey preset / keymap の実体JSONをファイルパスで参照する

---

## 個別JSON

### trigger_set

- `config/user/trigger_sets/` 配下に保存する
- `triggers[]` は `key` / `suppress` / `sequence_path` を持つ
- `sequence_path` は出力シーケンスJSONへの参照

### sequence

- `config/user/sequences/` 配下に保存する
- `label` / `run_to_end` / `run_to_end_delay_ms` / `actions` を持つ
- `run_to_end` / `run_to_end_delay_ms` はUI上の「連続実行」「間隔(ms)」

### 旧形式互換

- 旧形式の `triggers[].label` / `triggers[].run_to_end` / `triggers[].run_to_end_delay_ms` / `triggers[].actions` は読込互換を維持する
- 保存時は trigger_set + sequence の新形式へ寄せる

---

## パス保存ルール

- `config` 配下のパスは `config` ルート基準の相対パスで保存する
- `config` 配下ではない外部パスは絶対パスで保存する
- 読込時は絶対パスをそのまま使い、相対パスは `config` ルート基準で解決する
- trigger_set / sequence / keymap 個別保存でも同じルールを適用する
