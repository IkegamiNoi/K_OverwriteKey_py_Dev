# task_07_infrastructure_json.md

## 配置層

infrastructure

## 目的

JSON による保存・読込機能を実装する。

## 実装内容

* `content.json`
* `structure.json`
* `layout.json`
* 3ファイルの一括保存 / 一括読込
* 保存時バリデーション
* 読込時バリデーション

## 要件

* domain モデルに依存する
* UI に依存しない
* PySide6 に依存しない

## 完了条件

* 保存・読込が可能
* 読込後に元データを再現できる