# ========================================
# EDIT REQUIRED
# このファイルは必ずプロジェクト内容に合わせて修正してください
# これはpythonのプロジェクト作成時に使用したものになる
# ========================================

# 実装ガイド

## UI（PySide6）

* QWidget / QGraphicsView を使用
* 入力はイベントハンドラで受け取る

  * keyPressEvent
  * mousePressEvent
* 描画は専用クラスに分離

---

## イベント処理

* presentation → application に通知
* application が状態更新
* 再描画をトリガー

---

## 状態管理

* application 層で一元管理
* immutable に近い設計を意識

---

## 描画

* ノード描画とエッジ描画を分離
* 座標計算は domain / application 側で行う

---

## スクロール / ズーム

* QGraphicsView の機能を利用
* transform で拡大縮小

---

## テスト戦略

* domain：ロジック単体テスト
* application：ユースケーステスト
* presentation：最小限

---

## 実装の流れ

1. domain を作る
2. application を作る
3. UI をつなぐ
4. テストを書く
5. リファクタリング

---
