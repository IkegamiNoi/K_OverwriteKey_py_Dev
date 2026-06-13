# UIルール

## 表示形式

トリガー一覧
01. key: label

出力シーケンス
01. [type] value: label

プリセット一覧
01. value: label

---

## UI構成

- FullView
- CompactView
- pack_forget で切替
- ファイルメニューの通常読込は「読込（構成セット）…」
- 起動時設定は「起動時に読む構成セットを指定…」
- Import / Export は単一JSON互換機能として扱う
- キーマップ管理には keymap 個別の 保存 / 別名で保存 / 読込 を置く
- トリガー一覧には trigger_set 個別の 保存 / 別名で保存 / 読込 を置く
- 出力シーケンスには選択中トリガーの sequence 個別の 保存 / 別名で保存 / 読込 を置く

---

## 同期

- run_to_end
- delay_ms
- suppress

---

## 注意

- grid構造を崩さない
