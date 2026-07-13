---
description: テンプレートからプロジェクトを初期化する（対象ファイルを app_overview.md に合わせて一括修正）
---

`instructions/common/app_overview.md` の内容に従って、テンプレート由来の以下のファイルを
プロジェクト固有の内容に一括で書き換えてください。

## 対象ファイル

固定 4 つ:

1. `.claude_data/state/handoff.md`
2. `.claude/commands/save_state.md`（「チェックコマンド」節）
3. `.claude/commands/save_handoff.md`（「最初に確認するコマンド」節）
4. `.claude/rules/implementation.md`（Python プロジェクトでは `implementation_py.md` が実体）

条件付き（該当する場合のみ）:

5. `.claude/rules/python_rules.md` の「python 実行コマンド」節 — Python 採用時に実コマンドを記載
6. `instructions/phase/current.md` の「現在の参照先」 — 初期フェーズが確定している場合に差し替え
   （サンプルフェーズ `01_mvp` / `02_mvp_refine` の扱い〔削除 or 参考として残す〕はユーザーに確認する）
7. `.claude/rules/file_organization_rules.md` と
   `instructions/common/rules_detail/file_organization_rules.md` の「本リポジトリへの適用注記」 —
   `app_overview.md` からアーキテクチャ構成が読み取れる場合のみ読み替え例を書き換える

これら以外には触れない。フェーズ配下のタスク実行は **行わない**。

---

## 手順

### 1. 事前チェック（警告検出時は中断してユーザー対応待ち）

以下のいずれかに該当する場合、**修正に進まずユーザーへ報告して停止**する。

#### (a) `instructions/common/app_overview.md` が存在しない
- プロジェクト概要が不明では書き換え不可能 → 中断

#### (b) `# EDIT REQUIRED` マーカーが残っているファイル（対象ファイル**以外**）
- Grep で `# EDIT REQUIRED` を検索
- 対象ファイルは Claude が書き換えるのでチェック対象外
- サンプルフェーズ（`instructions/phase/01_mvp/` / `02_mvp_refine/`）内のマーカーもチェック対象外
  （過去プロジェクトの実例。削除 or 参考として残すはユーザー判断）
- それ以外で残っていれば「ユーザー手動編集の準備が未完了」として列挙し中断
  - 例: `CLAUDE.md` の `## ■ 共通ルール参照` セクション周辺

#### (c) 言語別ルールファイルが両立している
- 以下のペアが両方存在する場合、不要側の削除をユーザーに依頼して中断
  - `.claude/rules/implementation.md` ／ `.claude/rules/implementation_py.md`
  - `.claude/rules/flutter_rules.md` ／ `.claude/rules/python_rules.md`
- どちらをプロジェクトで使うかは Claude が決めず、ユーザー判断に委ねる

#### 警告フォーマット
```
## init_project: 事前チェックで停止

**未準備項目**:
- <該当ファイルパス> : <理由>
- ...

**対応依頼**: 上記をユーザー側で整理した後、再度 /init_project を実行してください。
```

### 2. プロジェクト概要の把握

- `instructions/common/app_overview.md` を Read
- 以下を抽出する（書き換え時に参照）
  - プロジェクト名 / 概要 1 行サマリ
  - 採用言語・フレームワーク（Flutter / Python / Node / Rust 等）
  - アーキテクチャ構成（レイヤ構成等。読み取れる場合）
  - 静的解析コマンド・テストコマンド（明示があれば）
  - 初期フェーズ名（`instructions/phase/NN_<topic>` 形式。明示があれば）

### 3. 対象ファイルを一括修正

各ファイルについて、テンプレート由来のメタ指示行・例示ブロックを削除し、プロジェクト固有内容に置換する。

#### `.claude_data/state/handoff.md`
- 「## 最初に確認するコマンド」内の `> プロジェクトに応じて〜` 注釈ブロックと `# Flutter プロジェクト` 等の例示ブロックを削除
- 採用言語に対応する実コマンド（例: `flutter analyze 2>&1 | tail -5` / `flutter test 2>&1 | tail -3`）に置換
- 「## 現在の作業の 1 行サマリ」の `> session.md.current.focus を参照` はそのまま保持（session.md 更新で自然に埋まる）

#### `.claude/commands/save_state.md`
- 「## チェックコマンド（参考・EDIT REQUIRED）」節の注釈ブロックを、採用言語の実コマンドに置換
- 残す内容は汎用なのでそれ以外は基本そのまま

#### `.claude/commands/save_handoff.md`
- 「## 最初に確認するコマンド（EDIT REQUIRED）」節の注釈ブロックを、採用言語の実コマンドの
  固定テンプレに置換（導入されていないツールは「スキップしてよい」と明記）

#### `.claude/rules/implementation.md`
- 冒頭の `# ========================================` ブロック（`EDIT REQUIRED` コメント）を削除
- 本文をプロジェクト固有の実装ポリシーに書き換える
  - `app_overview.md` から読み取れる方針（責務分離・座標変換・入力処理・状態管理 等）を反映
  - 既存のテンプレ記述は、採用言語と合わなければ削除して書き直す
  - 「実装時のサイズ目安」節は汎用なので残す
- 採用言語別ルールファイル（`flutter_rules.md` or `python_rules.md`）の存在を前提とし、重複は避ける

#### 条件付き対象（5〜7）
- 該当条件を満たす場合のみ、各ファイルの EDIT REQUIRED 注釈をプロジェクト固有内容に置換する
- 判断材料が `app_overview.md` に無い場合は書き換えず、完了報告の残課題に挙げる

### 4. 完了報告

以下を簡潔に出力する（3〜5 行程度）。

- 変更ファイル一覧
- 主要な反映内容（採用言語、静的解析・テストコマンド、実装ポリシーの方針）
- 残課題があれば明記（例: `app_overview.md` に静的解析コマンド未記載のため後で追記要 等）

---

## 禁止事項

- 対象ファイル以外への変更
- フェーズ配下のタスク定義の読み込み・実行
- `# EDIT REQUIRED` マーカー付きファイル（対象以外）の自動編集
  - これはユーザー責務。検出したら警告して停止する
- 言語別ルールファイル並立の自動解消（削除）
  - これもユーザー責務。検出したら警告して停止する
- `app_overview.md` の内容を超えた推測による拡張

## 注意

- このコマンドは **テンプレートからのプロジェクト初期化専用**。再実行しても破壊的変更が起きないよう、書き換え前に既存内容を確認すること
- 既に書き換え済みのファイルが含まれる場合は、その旨を報告に明記して該当ファイルの更新を行わない選択肢を取ってよい
