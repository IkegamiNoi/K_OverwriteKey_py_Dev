# block_review_checklist.md

## 目的

本ドキュメントは、実装タスクの進行に応じて品質を確認するための評価チェックタイミングを定義する。チェック内容は`確認内容`にて示しているファイルを参照する。

評価は以下の2段階で行う。

1. 各タスク完了時の軽い評価
2. 区切りごとの塊評価

---

## 1. 各タスク完了時の共通チェック

### 確認内容
`01_mvp/check/common_check.md`

---


## 2. 区切りごとの評価チェック

---

### ブロック1 レビュー観点チェックリスト

対象: Task 01〜07

#### 対象範囲

* task_01_project_setup.md
* task_02_data_model_domain.md
* task_03_domain_logic.md
* task_04_application_usecase.md
* task_05_quick_create_usecase.md
* task_06_custom_create_usecase.md
* task_07_infrastructure_json.md

#### 確認内容
`01_mvp/check/check_block/1.md`

---

### ブロック2 レビュー観点チェックリスト

対象: Task 08〜12

#### 対象範囲

* task_08_presentation_base.md
* task_09_view_transform_and_navigation.md
* task_10_grid_render.md
* task_11_node_render.md
* task_12_edge_render.md

#### 確認内容
`01_mvp/check/check_block/2.md`

---

### ブロック3 レビュー観点チェックリスト

対象: Task 13〜17

#### 対象範囲

* task_13_input_handling.md
* task_14_edit_mode.md
* task_15_key_guide.md
* task_16_feedback.md
* task_17_view_navigation_features.md

#### 確認内容
`01_mvp/check/check_block/3.md`

---

### ブロック4 レビュー観点チェックリスト

対象: Task 18〜20

#### 対象範囲

* task_18_infrastructure_settings.md
* task_19_save_load_ui.md
* task_20_integration.md

#### 確認内容
`01_mvp/check/check_block/4.md`

---

### ブロックレビュー実施ルール

#### 1. 各タスク完了後

* [ ] タスク単体の完了条件を確認する
* [ ] 仕様書との差分を記録する

#### 2. 各ブロック完了後

* [ ] 本チェックリストで横断レビューを行う
* [ ] 設計崩れがないか確認する
* [ ] 次ブロックへ進む前に、手戻りが必要か判断する

#### 3. レビュー結果の記録

各ブロックレビューでは、最低限以下を残す。

* 問題なし
* 要修正
* 保留
* 次ブロックで吸収可能
* 設計見直しが必要

---

# まとめ

本チェックリストは、単体タスクの完了確認だけでは見落としやすい以下を補うためのものである。

* 層の責務の崩れ
* 仕様とのズレ
* 表示と入力の不整合
* 将来拡張時の手戻りリスク

各ブロック完了時に本チェックリストを使うことで、後半フェーズでの大きな手戻りを減らしやすくする。
