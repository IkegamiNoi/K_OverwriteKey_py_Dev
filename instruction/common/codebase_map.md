# コード構造

## エントリーポイント

main.py

- App を起動する

---

## アーキテクチャ

オニオンアーキテクチャ構成

presentation
- UI（tkinter）
- イベント処理

application
- ユースケース
- 実行制御

domain
- トリガー
- アクション
- ロジック

infrastructure
- keyboard フック
- JSON入出力

---

## 主な責務

### App

- UI全体の管理
- View切替（Full / Compact）
- 分離JSONの現在の構成セットパス（keymap_set_path）を管理
- 通常の保存/読込/起動時読込は keymap_set.json を入口にする

### ConfigService

- 単一JSON互換の読込/書出
- split構成の読込/保存
- config配下は相対、外部は絶対のパス保存ルールを扱う

---

## UI構成

### FullView
- 編集機能
- トリガー管理
- シーケンス管理

### CompactView
- 簡易表示
- フック制御

---

## フック関連

- keyboard によるグローバルフック
- suppress=True 使用
- UI操作中は停止

---

## 注意

- UI更新は必ず UIスレッドで行う（after使用）
- フック処理はUIと分離される
