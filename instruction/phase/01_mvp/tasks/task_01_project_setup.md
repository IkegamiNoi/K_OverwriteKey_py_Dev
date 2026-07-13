# task_01_project_setup.md

## 目的

Python + PySide6 + オニオンアーキテクチャに基づいたプロジェクト構造を構築する。

## アーキテクチャ

* オニオンアーキテクチャを採用する
* GUI ライブラリは PySide6 を使用する

## 依存ルール

* 外側 → 内側への依存のみ許可
* 内側 → 外側への依存は禁止
* domain 層は PySide6 に依存しない
* presentation 層のみ PySide6 に依存してよい

## ディレクトリ構成

```text
src/
  domain/
  application/
  infrastructure/
  presentation/
  shared/
main.py
```

## 各層の責務

## domain

* エンティティ
* 値オブジェクト
* 純粋なロジック
* グリッド制約
* 接続制約

## application

* ユースケース
* 操作ロジック
* 表示関連の問い合わせ用サービス

## infrastructure

* JSON保存
* ファイルI/O
* 設定ファイルI/O

## presentation

* PySide6 UI
* 入力処理
* キャンバス描画
* ビュー変換
* スクロール / パン / ズーム

## 実装内容

* Python プロジェクト初期化
* PySide6 依存関係の導入
* 上記ディレクトリ作成
* `main.py` 作成
* 空のアプリ起動
* 空のメインウィンドウ表示

## 完了条件

* アプリが起動する
* PySide6 ウィンドウが表示される
* ディレクトリ構造が正しく生成されている