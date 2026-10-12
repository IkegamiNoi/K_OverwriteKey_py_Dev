#### 5.6.1 keymap の `grid`（画面の枠・phase 56）

親: [data_schema.md](../data_schema.md) §5.6「keymap」。挙動は [features.md](../features.md) §4.7。

keymap の任意キー。**`grid` が無い keymap は枠 OFF**。

```json
"grid": {
  "enabled": true,
  "monitors": {"1920x1080+0+0": {"rows": [{"h": 0.3333, "cells": [{"w": 0.25, "key": "q"}, ...]}, ...]},
               "1024x768+0-768": {"rows": [...]}},
  "sub": {"rows": 3, "cols": 3, "keys": ["q","w","e","a","s","d","z","x","c"]},
  "label_position": "top_left"
}
```

| キー | 型 | 意味・不正時 |
|---|---|---|
| `enabled` | bool | 枠を使うか。bool 以外は false |
| `monitors` | dict（識別子 → 最上段の形） | 画面ごとの最上段の形。dict でなければ `{}`。**記録の無い画面は組み込みの既定**（3 段 × 4 列・キー `q w e r / a s d f / z x c v`・等分）を使う（既定は JSON に持たない） |
| `sub` | dict | 細分化の形（`rows` / `cols` = 1〜9 の int・R×C ≥ 2・`keys` = R×C 個を読む順）。無い・不正なら既定（3 × 3・`q w e / a s d / z x c`） |
| `label_position` | str | キーの表示位置。`"top_left"` = 枠の左上 / それ以外・無い = 中央 |

* **画面の識別子** = `<幅>x<高さ><左><上>`（左と上は符号付き・例 `1920x1080+0+0` / `1024x768+0-768`）。
  モニタの矩形（作業領域ではなくモニタ全体）から作る。座標系は [nonfunctional.md](../nonfunctional.md)「画面の枠の座標系」。
  解像度や配置が変わった画面は別の画面として扱い既定を使う（古い記録は残す）
* **最上段の形** = `{"rows": [{"h": 正の数, "cells": [{"w": 正の数, "key": キー名}, ...]}, ...]}`。
  **読込時に段の `h` の和・各段の `w` の和を 1 へ正規化**する。`key` は [key_input.md](../key_input.md) の正規化名（trim + 小文字・テンキーの区別を含む）
* **読込時に形を既定へ戻すのは、形の不正と固定の予約キーだけ**（その形だけ・警告ログ 1 回）:
  段 0・列 0・比率が正の有限数でない（bool は数として扱わない）・形の中でのキーの重複（最上段と細分化・画面どうしは同じキーでよい）・空のキー・固定の予約キー（[key_input.md](../key_input.md) §7.3）。
  最上段は画面ごとに判定し、不正な画面の記録は落とす（= 既定）。細分化も独立に判定する。
  **設定で変わる予約キー（停止 / トグル / 直接切替キー）との重なりでは戻さない**（振り分けで上が勝つ）
* `grid` が dict でなければ無いものとして扱う
* **保存**: keymap の dict に `grid` があれば書く。正規化後の `grid` は `enabled` / `monitors` / `sub` を常に持ち、
  **`label_position` は `"top_left"` のときだけ書く**（中央のときは書かない。v0.6 までの `grid` を保存し直しても差分が出ない）。
  `grid` はダイアログで「枠を使う」を ON にしたとき、または形を編集したときに作り、**OFF に戻しても消さない**（形を失わない）
* `grid` の無い keymap は読込・保存で差分が出ない
* **4 経路すべてで保持する**: 単一 JSON の正規化（`domain/config.py` `_normalize_keymap_compat_fields`・`_normalize_keymaps` から呼ばれる）/ 個別読込・取り込み（`config_service` `_normalize_loaded_keymap`）/
  split の個別 JSON の読込（`split_loading.py`）/ 個別保存（`split_payloads.py` `build_keymap_file_payload`）。複製・貼り付けは keymap を丸ごと写すのでそのまま写る
