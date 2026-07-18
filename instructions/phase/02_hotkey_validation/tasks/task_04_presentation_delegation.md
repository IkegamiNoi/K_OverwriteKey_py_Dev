# task_04_presentation_delegation

## 目的

task_02（domain）/ task_03（application）で用意した hotkey 検証を、**presentation で実際に配線し直す**
（＝このフェーズの山場・初めて実挙動に影響する）。暫定仕様
[§4.3](../../../history/01_hotkey_validation.md)（設計の正）に従い:

1. `App.__init__` で `HotkeyService` を生成する。
2. `ActionExecutor` への `validate_hotkey` 注入元を `App.validate_hotkey`（バウンドメソッド）から
   `self.hotkey_service.validate` へ差し替える ＝ **application → presentation の層の逆転を解消**する。
3. `App.validate_hotkey` を `HotkeyService.validate` への**薄い委譲**に置き換える
   （dialogs 契約のため**削除しない**）。

**レイヤ制約: presentation 限定**（`keyseq/presentation/app.py` のみ変更）。
**domain / application / infrastructure は一切変更しない**。**スキーマ不変・挙動不変**。

## 対象範囲（presentation 限定・`app.py` のみ）

### 1. `keyseq/presentation/app.py` — `HotkeyService` の生成（`__init__`）

`self.input_gateway = InputGateway()`（現 `app.py:67`）の**後**、
`self.action_executor = ActionExecutor(...)`（現 `app.py:69`）の**前**に、以下 1 行を追加する:

```python
self.hotkey_service = HotkeyService(validate_key_name=self.input_gateway.validate_key_name)
```

- `input_gateway` の**メソッド参照だけ**を渡す（gateway オブジェクト全体ではない。暫定仕様 §4.2）。
- import を追加する: `from keyseq.application.hotkey_service import HotkeyService`
  （既存の application import 群と同じ場所・スタイルに合わせる）。

### 2. `keyseq/presentation/app.py` — 注入元の差し替え（`app.py:71`）

`ActionExecutor(...)` の引数を差し替える:

```python
#   validate_hotkey=self.validate_hotkey,          # 変更前
    validate_hotkey=self.hotkey_service.validate,   # 変更後
```

- これが**層の逆転の解消**の実体（ActionExecutor は application のオブジェクトのメソッドを受け取る）。
- **`ActionExecutor` の呼び出し順序に注意**: `self.hotkey_service` は `ActionExecutor(...)` 生成より
  **前**に代入済みである必要がある（上記 1 の配置順を守る）。

### 3. `keyseq/presentation/app.py` — `validate_hotkey` の薄い委譲化（現 `app.py:416-446`）

現行の実装ロジック（ステップ ①〜⑦）を**全て削除**し、委譲 1 行に置き換える。
**docstring は現行を維持**する（dialogs 向け契約の説明であり、契約は不変のため）:

```python
def validate_hotkey(self, hotkey: str) -> tuple[str, str]:
    """
    hotkey を検証し、(エラーメッセージ, 正規化したhotkey) を返す。
    エラーなしならエラーメッセージは ""。
    """
    return self.hotkey_service.validate(hotkey)
```

- **メソッド自体は削除しない**（`dialogs.py:440, 475` が `self.parent.validate_hotkey(value)` で使う外部契約）。
- シグネチャ `(hotkey: str) -> tuple[str, str]` を変えない。

### 設計メモ / 制約

- 変更は `app.py` の 3 箇所のみ（import 追加 / `HotkeyService` 生成 / 注入元差し替え / `validate_hotkey` 本体）。
  **他のメソッド・他ファイルには触れない**。
- `App.validate_hotkey` から `self.input_gateway.validate_key_name` の直接呼び出しが**消える**
  （検証は `HotkeyService` 経由に一本化）。ただし `input_gateway` 自体は他用途で使うため残る。
- **挙動不変が絶対要件**。委譲後も task_01 の特性テスト 7 件が**無変更で pass** することが証明になる。

## 含まない

- `keyseq/application/action_executor.py` の変更（暫定仕様 §7 スコープ外。
  `validate_hotkey: Callable` のシグネチャは不変・注入元が変わるだけ）。
- `keyseq/application/hotkey_service.py` / `keyseq/domain/hotkey.py` の変更（task_02 / task_03 で完成済み）。
- `keyseq/presentation/dialogs.py` の変更（`parent.validate_hotkey` 契約を維持するため触らない）。
- **単キー検証の統一**（`controllers/keymap_panel_controller.py:144, :376` / `key_capture.py:125` の
  `validate_key_name` 直呼び）＝暫定仕様 §7 スコープ外（別 idea 候補）。
- 正本反映・記録（昇格 / 凍結 / `codebase_map.md` / decisions_archive / `/refactor_check`）は **task_05**。
- hotkey 文法・エラーメッセージの変更 / `app.py` の行数削減それ自体（暫定仕様 §7）。

## 確認

python は必ずリポジトリルートの `.venv` を使う（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. **委譲の確認**（暫定仕様 §6-1）:
   `git grep -n "def validate_hotkey" -- keyseq/presentation/app.py` が **1 件**で、
   本体が `self.hotkey_service.validate(hotkey)` への委譲のみ（①〜⑦の実装ロジックが残っていない）。
2. **層の逆転の解消**（暫定仕様 §6-2）:
   `app.py` の `ActionExecutor` 注入が `validate_hotkey=self.hotkey_service.validate` に
   なっている（`validate_hotkey=self.validate_hotkey` を注入していない）。
3. **生成順序**: `self.hotkey_service = HotkeyService(...)` が `ActionExecutor(...)` 生成より前にある。
4. **action_executor.py の無変更**（暫定仕様 §6・§7）:
   `git diff -- keyseq/application/ keyseq/domain/ keyseq/infrastructure/` が**空**。
5. **エラーメッセージ 4 種の不変**（暫定仕様 §5・§6-4）: 特性テスト（tests_ui）が無変更で pass することで担保。
6. **標準検証 4 項目**:
   - `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py` → clean
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` → **77 pass**（変化なし）
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` → **16 pass**
     （**特性テスト 7 件を含め無変更で pass** ＝ 挙動不変の証明。暫定仕様 §6-9）
   - `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` → **SMOKE OK**
7. **差分の範囲**: `git diff --stat` が `keyseq/presentation/app.py` のみ。

## 完了条件

- 上記「確認」1〜7 が pass。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点）。重点は
  **層の逆転の解消（注入元が `hotkey_service.validate`）**、
  **`validate_hotkey` が薄い委譲のみ（実装ロジック残存なし）**、
  **`action_executor.py` / `dialogs.py` を変更していないこと**、
  **特性テスト 7 件が無変更で pass（挙動不変）**、**差分が `app.py` に限定**。
- **統合確認のため二次レビュー（`codex-reviewer`）を併用**する
  （CLAUDE.md「統合テスト時・フェーズ区切りでは二次レビューを併用する」）。
- 実機目視: **本タスクで実施**（アクション編集ダイアログで不正 hotkey〔空 / `ctrl++c` / `ctrl+ctrl+c` /
  不明キー〕のエラー表示・正常 hotkey の正規化保存・hotkey アクションの実行。暫定仕様 §6-11）。
  実機目視はユーザーが行い、結果をメインセッションへ報告する。
