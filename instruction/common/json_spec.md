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
- `keymap_set.json` は trigger / hotkey preset / keymap の実体JSONをファイルパスで参照する

---

## パス保存ルール

- `config` 配下のパスは `config` ルート基準の相対パスで保存する
- `config` 配下ではない外部パスは絶対パスで保存する
- 読込時は絶対パスをそのまま使い、相対パスは `config` ルート基準で解決する
- 将来の trigger / keymap 個別保存でも同じルールを適用する
