# idea_01_hotkey_validation_to_domain.md

## 概要

App に住む **hotkey 検証ロジック（パース・正規化・重複検査、約31行）を domain / application 層へ移す**。
App は dialogs 向け契約のための**薄い委譲**に留める。
狙いは 2 つ: **application 層（ActionExecutor）が presentation の実装に注入依存している逆転の解消**と、
**単体テスト時に `tk.Tk` を生成せずに検証ロジックを直接テストできるようにすること**。

## 起票経緯（2026-07-17）

計画04（[04_widget_split_plan.md](../modified_proposal/04_widget_split_plan.md)）W7「app.py 残留メソッドの分類」で、
「どの責務分類（Tkルート管理 / 生成と配線 / View切替 / 調整役 / dialogs向け契約）にも属さない残留ロジック」
として列挙された項目。計画04 の範囲外として**保留**（判断記録は `.claude_data/state/decisions.md`
「【W7】app.py 行数の目安未達」）。設計判断を伴うため独立フェーズとして分離した。

## 現状

- **実装**: `keyseq/presentation/app.py:416-446` の `App.validate_hotkey(hotkey) -> tuple[str, str]`
  （戻り値 = `(エラーメッセージ, 正規化済み hotkey)`。エラーなしならメッセージは `""`）
  - 空文字チェック / `+` 前後の空要素検出（`ctrl++c` / `+ctrl+c` / `ctrl+c+` を弾く）/
    小文字化・空白除去による正規化 / 同一キー重複検出（`ctrl+ctrl+c`）/
    `self.input_gateway.validate_key_name(p)` による各キー名の妥当性チェック
- **利用者は 2 経路**:
  1. `keyseq/presentation/dialogs.py:440, 475` — `self.parent.validate_hotkey(value)`
     （**dialogs 向け外部契約**。計画02 S10 で「App に残すもの」と明記されている）
  2. `keyseq/presentation/app.py:71` → `keyseq/application/action_executor.py:20, 29, 77`
     — `validate_hotkey: Callable[[str], tuple[str, str]]` として注入され `self._validate_hotkey(hotkey)` で呼ばれる
- **依存**: `input_gateway`（infrastructure）の `validate_key_name`

## 問題

- 「hotkey の文法」は本来 **domain の知識**だが、実装が presentation（App）にある。
  ActionExecutor は Callable 注入で直接依存を回避しているものの、**実体は presentation 側**＝層の逆転。
- **テスト容易性**: 現状この検証ロジックを単体テストするには `App`（= `tk.Tk`）の生成が必要。
  domain へ出せば pytest で純粋にテストできる（本 idea の最大の価値）。

## 提案（方向性・要設計）

検討メモであり確定仕様ではない。

- **案A**: `keyseq/domain/hotkey_validator.py` に純粋関数 / クラスとして切り出す。
  `validate_key_name` は引数（Callable）で注入し、domain が infrastructure に依存しないようにする。
- **案B**: application 層のサービスとして置き、`input_gateway` を注入する。
- いずれの案でも:
  - App は dialogs 契約のため `validate_hotkey` を**薄い委譲として残す**
    （`parent.validate_hotkey` は外部契約なので消せない）
  - ActionExecutor は注入をやめて直接使うか、注入元を App から domain / application へ差し替える
- **論点**: domain に置く場合の `input_gateway` 依存の扱い（Callable 注入 or domain 側にキー名レジストリを持つ）。
  設計が多岐にわたるため、`.claude/rules/spec_change_workflow.md` の**暫定仕様先行モード**（`/spec_draft`）を推奨。

## 想定スコープ

- **含む**: `validate_hotkey` の実装移設 / App の薄い委譲化 / ActionExecutor の注入元見直し / 単体テスト追加
- **含まない**: **エラーメッセージ文言の変更（1文字も変えない）** / hotkey 文法自体の変更 /
  dialogs・ActionExecutor の呼び出し契約（シグネチャ・戻り値）の変更
- **影響レイヤ**: presentation / application / domain（+ infrastructure 依存の扱い）
- **仕様変更の見込み**: なし（挙動不変リファクタ）。文言・戻り値契約は維持する
- **リスク**: 中（dialogs 契約 + ActionExecutor 注入の 2 経路を壊さないこと）
