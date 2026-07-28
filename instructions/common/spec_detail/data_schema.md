## 5. JSON 仕様

### 5.1 重要ルール（後方互換）

* 後方互換必須
* 既存キーの削除禁止
* 既存キーの意味変更禁止
* 未定義キーは無視する

※設計変更タスクの場合は、指示された範囲でのみ変更可能。

### 5.2 基本構造（単一JSON互換）

```json
{
  "triggers": [...],
  "hotkey_presets": [...],
  "hook_stop_key": "f12"
}
```

### 5.3 拡張キー

#### run_to_end

* 型: bool
* 連続実行

#### run_to_end_delay_ms

* 型: int
* デフォルト: 300

### 5.4 分離JSONの本流

| 機能 | 形式 |
| --- | --- |
| 保存 | split |
| 読込 | split |
| 起動 | split |
| Import | 単一JSON |
| Export | 単一JSON |

#### keymap_set の保存先と「ファイルなし」状態

* keymap_set の既定の保存先は**ディレクトリ `config/user/keymap_sets/`** とする。
  固定ファイル（`default.json`）を既定の保存ターゲットにしない
* 起動時に `config/user/{keymap_sets,keymaps,trigger_sets,hotkey_presets,sequences}` を作成する。
  `config/config.json` 本体は起動時に作らず、**最初に設定が永続化された時点**で作成する
  （keymap_set の保存 / フォントサイズ変更 / 起動時に読む keymap_set の指定）
* アプリが保持する現在の keymap_set パスは、次の 3 経路で**空（＝ファイルなし）**になる:
  1. 新規作成した直後
  2. Import（単一JSON）に成功した直後
  3. 起動時に `keymap_set_path` が**未設定 / 不在 / 読込失敗**の場合（無言で空データ起動する）
* パスが空の状態で「保存」した場合は**別名保存**として扱う。
  別名保存ダイアログの初期ディレクトリは `config/user/keymap_sets/`、初期ファイル名は `keymap_set.json`
* パスが空でない場合の「保存」は従来どおり当該ファイルへ上書きする
* 保存に成功すると `config/config.json` の `keymap_set_path` は保存先へ更新される
* **【制約】同一ディレクトリに複数の keymap_set を置いても、trigger_set / hotkey_presets は
  共通ファイル**（`config/user/trigger_sets/default.json` / `config/user/hotkey_presets/default.json`）
  **を共有・上書きする**。セット別の分離は後続フェーズの課題
* **【実装未追従】** 別名保存でレガシー `<アプリ配置>/settings/` 配下を選んだ場合のみ、選択パスが
  `config/user/keymap_sets/default.json` へ差し替わる実装が残っている
  （[idea_09](../../backlog/idea_09_legacy_settings_save_path_fallback.md)）。**本節の規定が正**であり、
  実装側を追従させる

### 5.5 split 読込

* 通常読込では `keymap_set.json` を直接選択する
* `config/config.json` は起動時に読む `keymap_set_path` を保持する
* `keymap_set.json` は trigger_set / hotkey preset / keymap の実体JSONをファイルパスで参照する

### 5.6 個別JSON

#### trigger_set

* `config/user/trigger_sets/` 配下に保存する
* `triggers[]` は `key` / `suppress` / `sequence_path` を持つ
* `sequence_path` は出力シーケンスJSONへの参照

#### sequence

* `config/user/sequences/` 配下に保存する
* `label` / `run_to_end` / `run_to_end_delay_ms` / `actions` を持つ
* `run_to_end` / `run_to_end_delay_ms` は UI 上の「連続実行」「間隔(ms)」
* sequence の新規保存ファイル名は label 由来にし、日本語 label もそのまま候補に使う
* ファイル名では Windows 禁止文字のみ `_` に置換する
* trigger_set の新規保存ファイル名は現在の keymap_set ファイル名由来にする。
  keymap_set が未設定（§5.4 の「ファイルなし」状態）のときは `trigger_set.json` を候補にする

#### 旧形式互換

* 旧形式の `triggers[].label` / `triggers[].run_to_end` / `triggers[].run_to_end_delay_ms` /
  `triggers[].actions` は読込互換を維持する
* 保存時は trigger_set + sequence の新形式へ寄せる

### 5.7 パス保存ルール

* `config` 配下のパスは `config` ルート基準の相対パスで保存する
* `config` 配下ではない外部パスは絶対パスで保存する
* 読込時は絶対パスをそのまま使い、相対パスは `config` ルート基準で解決する
* trigger_set / sequence / keymap 個別保存でも同じルールを適用する

---
