# task_20_integration.md

## 配置層

全体統合

## 目的

各層を統合し、一連の操作が動作する状態にする。

## 実装内容

* presentation → application 呼び出し
* application → domain 呼び出し
* application → infrastructure 呼び出し
* 描画更新と状態同期
* 基本的な起動フロー整備

## 完了条件

* ノード作成
* 編集
* 接続
* 保存 / 読込
* スクロール
* パン
* ズーム

が一連で動作する