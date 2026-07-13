# task_02_data_model_domain.md

## 配置層

domain

## 目的

コアとなるデータ構造を定義する。

## 実装内容

## Node

* id
* text

## Edge

* from
* to
* type

## Grid

* Row
* Column

## Position

* node_id
* row_id
* column_id

## ViewState 用の概念整理

* これは domain ではなく presentation で持つ前提とする
* domain に UI 表示状態を混ぜない

## 要件

* 外部 GUI ライブラリに依存しない
* UI に依存しない
* Python 標準的なデータ構造または dataclass で扱いやすいこと

## 完了条件

* 純粋なデータモデルとして扱える
* テストで生成・比較可能