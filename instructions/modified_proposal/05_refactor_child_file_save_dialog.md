# 05_refactor_child_file_save_dialog（Phase β 完了時の /refactor_check 提案）

> 起票: 2026-08-02（`/refactor_check`・phase 06 = 保存系リデザイン Phase β の完了処理）。
> **判定: リファクタ推奨**（M1 / M2 / M3 / M4 該当）。**本書はユーザー承認前に実施しない**。
> 対象は Phase β で変更した 12 ファイルのみ（`PHASE_BASE = b1a6f39`）。

## 判定サマリ（メトリクス実測）

| 記号 | 実測 | 判定 |
|---|---|---|
| M1 | `config_service.py` **1650 行**（base 1014 / +636）・`keymap_set_io.py` **640 行**（base 239 / +401） | **該当**（600 行超 かつ +100 行以上） |
| M2 | `_collect_child_save_plan` **130 行**（新規）・`save_runtime_data` **127 行**（53→127）・`_build_keymap_payloads` **92 行**（51→92）・`_build_trigger_set_payloads` **89 行**（49→89） | **該当**（80 行超の新規 / 大幅改変） |
| M3 | `keymap_file_io` / `sequence_file_io` / `trigger_set_file_io` の 3 ファイルに、source_path 変化判定 + 「上位の索引を保存すると追随します。」の付与が同型で存在（各 15〜20 行） | **該当**だが**既知**（→ [idea_06](../backlog/idea_06_individual_json_io_unification.md)。下記「既知」参照） |
| M4 | `CHILD_KEYMAP` / `CHILD_TRIGGER_SET` / `CHILD_SEQUENCE` の列挙が 5 ファイル（config_service 15 / keymap_set_io 22 / child_save_rows 11 / child_save_plan 6 / trigger_set_file_io 4）へ新規発生 | **該当**だが**候補送り**（下記） |
| M5 | 申し送りコメントの新規追加 **0 件** | 非該当 |
| M6 | 既存定数と同値の直値追加 **なし** | 非該当 |

**既知（提案書の項目にしない）**:
- **M3** … 個別 JSON IO 3 種の共通化は [idea_06](../backlog/idea_06_individual_json_io_unification.md) が
  **保留（前提条件付き）**とユーザー判断済みの領域。Phase β で 3 箇所目が揃ったことは着手条件③
  「共通化の実需」の材料であり、INDEX の状態列へ反映済み。本書では扱わない。

**候補送り（`current.md` の別タスク化候補へ追記）**:
- **M4** の子カテゴリ列挙（子の種類は仕様上 3 種で固定であり、増える見込みが低いため優先度低）
- `child_save_dialog.py` **370 行**（600 行未満のため M1 非該当だが実装目安 300 行超）と
  `_add_text_cell` の戻り値が素の dict
- `dirty_tracker.trigger_set_imported` が読み手不在の残置状態
- slugify 後に別々の keymap_set 名が同一 stem へ丸まる衝突（受入条件 8 の範囲外）

---

## 項目 0: 安全網の確認（**先行必須**）

- **対象**: `tests/`（144）・`tests_ui/`（153）・`tests/smoke_app.py`
- **やること**: 項目 1・2 の対象領域が特性テストで固定されているかを確認する。
  具体的には ①保存 JSON の**バイト列比較** ②保存計画の実行（依存・失敗時の旧索引維持）
  ③子一覧ダイアログの選択駆動、の 3 つが対象関数を通ることを確認する。
  カバーしていない経路があれば**特性テストの追加を先に行う**（挙動を固定してから動かす）。
- **完了条件**: 下記が全 pass（python は リポジトリルートの `.venv`）。
  ```
  ..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests_ui
  ..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests
  ..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui
  ..\..\..\.venv\Scripts\python.exe -m tests.smoke_app
  ```
- **リスクと戻し方**: なし（追加のみ）。
- **依存**: なし。項目 1・2 の前提。

## 項目 1: `config_service.py`（1650 行）から保存計画の実行を切り出す

- **対象**: `keyseq/application/config_service.py`
  （`save_runtime_data:288`(127) / `_validate_save_plan:747`(50) / `_apply_saved_child_paths:798`(33) /
  `resolve_child_save_targets:416`(40) / `_build_split_save_payloads:855`(88) /
  `_build_keymap_payloads:1025`(92) / `_build_trigger_set_payloads:1142`(89)）
- **何が問題か**: **M1**（1650 行・+636）と **M2**（80 行超の関数が 3 つ）。
  単一 JSON 互換 / split 読込 / 保存計画の実行 / パス規約 / 命名（slugify）と、
  **異なる責務のまとまりが 4 つ以上**同居している。
- **どう変えるか**: 所有者フォルダ方式（`.claude/rules/file_organization_rules.md`）で
  `keyseq/application/config_service/` を作り、親 `config_service.py` ごと入れる。
  ```text
  keyseq/application/config_service/
      config_service.py      # ConfigService 本体（公開面は不変）
      save_plan_execution.py # 保存計画の実行（検証 / 適用 / ロールバック）
      split_payloads.py      # _build_*_payloads 群
  ```
  公開契約（`ConfigService` の import パスとメソッド）は**変えない**。互換用の横流しモジュールは作らない。
- **完了条件**: 項目 0 のコマンドが全 pass + 保存 JSON のバイト列比較テストが無修正で pass +
  `wc -l` で親ファイルが 600 行未満。
- **リスクと戻し方**: import 経路の取り違え（`from keyseq.application.config_service import ConfigService`
  が壊れると全域が落ちるため、compileall + smoke で即検知できる）。戻しは 1 コミット revert。
- **依存**: 項目 0。

## 項目 2: `keymap_set_io._collect_child_save_plan`（130 行）を分割する

- **対象**: `keyseq/presentation/controllers/config_io/keymap_set_io.py:144`（ファイル全体 640 行）
- **何が問題か**: **M1**（640 行・+401）と **M2**（130 行の新規関数）。
  この 1 関数に「行の収集 → 一覧ダイアログ → 再計算先の上書き確認 → 依存確認の 4 択 →
  計画の再構築」という**保存計画確定の全ループ**が入っており、AI への修正依頼で
  「この関数の依存確認のところだけ」と修飾が必要になる。
- **どう変えるか**: ループ 1 周分の各ステップを private メソッドへ抽出し、
  `_collect_child_save_plan` は**手順の並びだけ**にする（既に `_confirm_recalculated_overwrites` /
  `_recalculated_overwrite_rows` が切り出されているので、同じ粒度で
  `_ask_child_actions` / `_resolve_dependency` を追加する形）。
  **新規ファイルは作らない**（ファイル分割は行数が減った後に再判定）。
  ```python
  # 変更前（130 行の while ループに全工程が同居）
  def _collect_child_save_plan(self, save_path, split_base_dir):
      while True:
          rows = collect_child_save_rows(...)          # 行の収集
          choices = self._app.child_save_dialog.ask_child_save_actions(rows)   # 一覧
          ...                                           # 再計算先の上書き確認（32 行）
          ...                                           # 依存確認の 4 択と計画再構築（40 行超）
          return plan, notice, deferred

  # 変更後（手順の並びだけを残す）
  def _collect_child_save_plan(self, save_path, split_base_dir):
      while True:
          rows, targets = self._collect_rows(save_path, split_base_dir)
          choices = self._ask_child_actions(rows)       # None ならキャンセル
          if choices is None:
              return None, "", False
          plan = self._build_plan(rows, choices, save_path, split_base_dir)
          confirmed = self._confirm_recalculated_overwrites(...)   # 既存
          if confirmed is None:
              return None, "", False
          resolved = self._resolve_dependency(plan, rows, targets, save_path)
          if resolved is RETRY:                          # 「選び直す」= 一覧へ戻る
              continue
          return resolved
  ```
- **完了条件**: 項目 0 のコマンドが全 pass + `tests_ui/test_child_save_dialog.py` が**無修正**で pass
  （＝ダイアログ駆動の挙動が不変）+ 抽出後の各メソッドが 40 行以内。
- **リスクと戻し方**: ループの再入・`continue` 条件の取り違えで依存確認が無限ループ / 空振りする
  （task_06b で実際に起きた事故）。`tests_ui` の依存確認テストが検知する。戻しは 1 コミット revert。
- **依存**: 項目 0。項目 1 とは独立（並行可）。

---

## 実施タイミング（ユーザー選択）

- (a) 同フェーズ末の追加タスク（`task_19_refactor` として起票）
- (b) 次フェーズ前の独立ミニフェーズ

**挙動保存が原則**。挙動・エラーメッセージ・保存ファイルのバイト列を変える修正は本書に含めない。
