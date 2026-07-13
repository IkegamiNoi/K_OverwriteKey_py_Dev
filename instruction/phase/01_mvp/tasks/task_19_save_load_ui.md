# task_19_save_load_ui.md

## 配置層

presentation + infrastructure 連携

## 目的

保存・読込 UI を実装する。

## 実装内容

* PySide6 のファイルダイアログによる保存
* PySide6 のファイルダイアログによる読込
* infrastructure 層の保存読込呼び出し
* エラーメッセージ表示

## 要件

* presentation から infrastructure を直接汚く扱わず、application 経由または整理された窓口を通す
* 保存後 / 読込後の画面反映を行う

## 完了条件

* UI から保存・読込ができる
* 保存結果が再描画へ反映される