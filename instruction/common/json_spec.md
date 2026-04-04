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