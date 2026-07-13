# task_18_infrastructure_settings.md

## 配置層

infrastructure

## 目的

設定ファイルの読込基盤を実装する。

## 実装内容

* アプリ設定ファイルの読込
* クイック作成マス数などの設定値管理
* 将来のキーマップ差し替えや UI 設定追加に耐えられる構造にする

## 要件

* PySide6 依存を持たない
* JSON または同等の簡易形式を利用可能とする

## 完了条件

* 設定値を読み込める
* application / presentation から参照可能