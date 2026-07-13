# app_overview.md

## 概要

本ツールは、Python + tkinter + keyboard を用いた**キーボード入力置換シーケンサーアプリ**である。
単キートリガーでキーボード入力を捕捉・置換し、登録した出力シーケンス（アクション列）を実行する。

エントリーポイントは `main.py`。パッケージは `keyseq/`（オニオンアーキテクチャ）。

## 主要概念

- **トリガー**: 単キー。グローバルフックで捕捉し、対応するシーケンスを実行する。重複禁止。
- **シーケンス**: 出力アクション列。`label` / `run_to_end` / `run_to_end_delay_ms` / `actions` を持つ。
- **keymap**: キー割り当ての管理単位。UI から編集・個別保存/読込ができる。
- **構成セット（keymap_set）**: trigger_set / hotkey preset / keymap の実体JSONを
  ファイルパス参照で束ねる分離JSON（split 構成）の本流。
- **フック**: keyboard によるグローバルフック。`suppress=True`。UI 編集中は停止（ネスト対応）。

## 実装前提

- 実装言語は Python、GUI は tkinter、キーフックは keyboard（他に pyautogui / pynput を使用）
- アーキテクチャはオニオンアーキテクチャ（presentation / application / domain / infrastructure）
- UI 更新は必ず UI スレッドで行う（`after()` 使用）
- JSON は後方互換を必ず維持する（`common/spec_detail/data_schema.md` に従う）
- フック安全（暴走防止・suppress 副作用・例外吸収）を最優先する
- テストは pytest（単体: `tests/` / UI フロー: `tests_ui/`）

## 基本方針

- 入力置換の安全性を最優先する（詳細は `common/spec_detail/design.md`）
- フック処理と UI を分離する
- 保存データと UI を分離し、データ形式は仕様書を正とする
- 既存設計・命名を尊重し、タスク指示なしの再設計をしない

## 詳細仕様の参照先

| 内容 | ファイル |
|---|---|
| 設計思想 | `common/spec_detail/design.md` |
| アーキテクチャ・依存ルール | `common/spec_detail/architecture.md` |
| 機能要件・UI 構成 | `common/spec_detail/features.md` |
| JSON 仕様・パス保存ルール | `common/spec_detail/data_schema.md` |
| キー入力・フック仕様 | `common/spec_detail/key_input.md` |
| 非機能要件（安全設計） | `common/spec_detail/nonfunctional.md` |
| コード構造マップ（実装状態の正） | `common/codebase_map.md` |
| コーディング規約・実装ルール | `.claude/rules/implementation.md` / `.claude/rules/python_rules.md` |
