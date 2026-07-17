# 暫定仕様 01: hotkey 検証ロジックの層移設（hotkey_validation）

> 状態: **未凍結・v1.0・主入力・ユーザー確定済（2026-07-17）・実装着手可**。
> 本書がこのフェーズの確定設計（フェーズ中は正本を直接改訂しない）。
>
> 版歴:
> - v0.1 起票。
> - v0.2: 起票時 reviewer レビュー（判定「採用」・事実誤認 0 件）の参考指摘を反映し、
>   §4.2 に `validate` の実装形（`try` がループ全体を包む形）を明記。`p` の値がずれる実装事故を防ぐため。
> - **v1.0: 敵対的レビュー（codex-adversarial-reviewer）の指摘処理と §6 確認事項 4 件のユーザー確定を反映。
>   案 C 採用 / parts 再構成の廃止 / 命名 `validate_hotkey_syntax` / 安全網テストは追加し移設後も残す。**
> フェーズ末タスクで正本 `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 起票元: [idea_01](../backlog/idea_01_hotkey_validation_to_domain.md)（計画04 W7 の残留ロジック分類から分離）。
> ユーザー方針（2026-07-17）: 計画04 の次期課題は 3 分割し「後始末（完了）→ **本件** → idea_02」の順で進める。

---

## §1 目的 / 背景

App（presentation）に住む **hotkey 検証ロジックを domain / application 層へ移す**。
App は dialogs 向け契約のための**薄い委譲**に留める。狙いは 2 点:

1. **層の逆転の解消** — application の `ActionExecutor` が presentation（`App.validate_hotkey`）の
   実装を注入経由で使っている状態をなくす。
2. **テスト容易性**（本件の最大の価値）— 現状この検証を単体テストするには `App`（= `tk.Tk`）の
   生成が必要で、**テストが 1 件も存在しない**。層を移せばモック無し / GUI 無しでテストできる。

**挙動不変**（エラーメッセージ・戻り値契約を 1 文字も変えない）。スキーマ変更なし。

### 現状監査（2026-07-17・Explore 調査による裏取り）

#### 移設元
`keyseq/presentation/app.py:416-446` `App.validate_hotkey(hotkey: str) -> tuple[str, str]`

- 戻り値 = `(エラーメッセージ, 正規化hotkey)`。正常時 `("", normalized)` / **異常時は常に `(msg, "")`**。
- 処理順: ①`(hotkey or "").strip()` → 空チェック ②`split("+")` ③各要素 `p.strip().lower()`
  ④空要素検出 ⑤`normalized = "+".join(parts)` ⑥`len(set(parts)) != len(parts)` で重複検出
  ⑦各 `p` を `self.input_gateway.validate_key_name(p)`、例外を捕捉
- **外部依存は `self.input_gateway.validate_key_name` のみ**。`self.data` 等のインスタンス状態には
  一切触れていない → **純粋関数化可能**。
- ⑦の `except` 節はループ変数 `p` を参照してメッセージを組む（`app.py:444`）。
  例外送出時の `p` = 失敗したキーであり、**この挙動を保つ**。

#### 利用側の契約（2 経路）
| 呼び出し元 | 契約 |
|---|---|
| `presentation/dialogs.py:440` / `:475` | `err_msg, normalized = self.parent.validate_hotkey(value)`。err_msg があれば `messagebox.showerror("不正なhotkey", ...理由: {err_msg})` して return。無ければ **`normalized` を採用**して `self._temp` へ保存。`self.parent` = App |
| `application/action_executor.py:20, 29, 77-80` | `validate_hotkey: Callable[[str], tuple[str, str]]` をキーワード専用引数で受け取り `self._validate_hotkey` に保持。`error_message, normalized = self._validate_hotkey(hotkey)` → エラー時 `self._on_action_error(action, error_message)` で return / 正常時 `self.input_gateway.send_hotkey(normalized)` |
| 注入元 | `app.py:71` で `validate_hotkey=self.validate_hotkey`（App のバウンドメソッド）＝**層の逆転の実体** |

#### 移設先候補の現状
- **`keyseq/domain/`（2 モジュール）**: `config.py` / `key_identifiers.py`。
  **import は標準ライブラリと domain 内のみ**＝infrastructure / application に一切依存しない（クリーン）。
  **完全にモジュールレベルの純粋関数中心。クラス 0・dataclass 0・DI の前例なし。**
  命名は動詞始まりスネークケース（`normalize_*` / `resolve_*` / `coerce_*` / `is_*` / `ensure_*` / `format_*`）。
  **専用バリデータモジュールは存在せず、`(error, value)` タプルを返す domain 関数の前例も無い。**
- **`keyseq/application/`（9 モジュール）**: domain の関数を直 import して使う。
  **infrastructure への依存は `config_service.py` の `JsonRepository` のみで、他は DI（コンストラクタ注入）**
  ＝`ActionExecutor(input_gateway=...)` のパターンが確立済み。
- **`keyseq/infrastructure/input_gateway.py:54`** `validate_key_name(self, key_name: str) -> None`:
  **bool を返さず不正時に例外を再 raise**。モジュールレベルで **`keyboard` / `pyautogui` に依存**
  （import 時点で OS キーボードフックに触れる）→ **domain から呼ぶとオニオン違反**。
  なお `input_gateway.py:8` は `keyseq.domain.key_identifiers` を import しており、
  **「特殊キーの知識は domain にあり infrastructure がそれを使う」構図が既にある**（依存の向きは正しい）。
- **テスト**: `validate_hotkey` / `validate_key_name` のテストは `tests/` `tests_ui/` とも **0 件**。
  形式は **unittest**（`class XxxTest(unittest.TestCase)`）。domain テストの既存例
  `tests/test_key_identifiers.py` は**モック無しで関数を直呼び**。`test_action_executor.py` は無い。

## §2 確定事項（ユーザー 2026-07-17）

### 前提（起票時に確定）

- **挙動不変**。エラーメッセージ 4 種（§5）・戻り値契約 `(error, normalized)`・チェック順序を変えない。
- **dialogs 契約 `parent.validate_hotkey(value)` は維持**（`App.validate_hotkey` は薄い委譲として残す）。
- 本件は**暫定仕様先行モード**で進める（設計判断を伴い・複数ファイルに跨り・タスク 3 以上）。
- 着手順は「後始末（`01_view_ref_cleanup`・完了）→ **本件** → [idea_02](../backlog/idea_02_startup_font_settings_cleanup.md)」。

### 設計判断（v1.0・旧 §6 確認事項より確定）

1. **設計案は C**（domain = 純粋な文法検査 / application = 合成 + キー名検証）。§3 の比較のとおり、
   関心と層の境界が一致し、domain の既存スタイル（標準ライブラリのみ・クラス 0・DI なし）を崩さないため。
2. **parts の再構成は廃止**。domain が `(error, normalized, parts)` を返し、application は
   受け取った `parts` をそのまま使う（`normalized.split("+")` による復元をしない）。
   **公開契約 `(error, normalized)` は不変**（§4.2）。
3. **命名**: domain `keyseq/domain/hotkey.py::validate_hotkey_syntax` /
   application `keyseq/application/hotkey_service.py::HotkeyService.validate`。
4. **安全網の特性テストは追加し、移設後も残す**（§4.4）。dialogs が使う App 経由の契約を守り続けるため。

### 敵対的レビューの指摘処理（2026-07-17・codex-adversarial-reviewer）

- 指摘: 「`normalized.split("+")` の 2 回目のアロケーションが `MemoryError` を起こすと、
  エラータプルを返す契約から外れて例外が送出される＝新たな未捕捉例外経路」（medium・needs-attention）
- **判定: 却下（根拠不成立）**。現行実装も `try` の外で `raw = s.split("+")` / `parts = [...]` /
  `set(parts)` / `normalized = "+".join(parts)` と同種のアロケーションを行っており、そこで
  `MemoryError` が起きれば同様に未捕捉で伝播する。**新設計だけが未捕捉経路を持つわけではなく、
  挙動の種類は変わらない**（増えるのはアロケーション 1 回のみ）。
- **ただし下層の構造的論点（parts の二度手間）は妥当**。reviewer（Claude）も独立に
  「`normalized.split` による復元はやや間接的」と指摘しており、**2 名が同じ箇所を挙げた**。
  コストなしで解消できるため、**「MemoryError 対策」ではなく「冗長性の除去」を理由に
  上記 §2-設計判断 2 として採用**（ユーザー確定済）。
- 併せて確認済み: **`parts` が空リストになる経路は存在しない**（`s` が非空なら `split` は必ず
  1 要素以上を返し、空要素は §4.1 ④で弾かれる）ため、`p` 未定義による `NameError` は起きない。

## §3 設計方針（案の比較）

「hotkey の文法」は domain の知識だが、「キー名が実在するか」は infrastructure の知識、という
**関心の分割**が論点。エラーメッセージ 4 種のうち **3 種（空 / `+` 前後が空 / 重複）は純粋な文法検査**で、
gateway が要るのは **1 種（不明なキー名）のみ**。

| 案 | 内容 | 評価 |
|---|---|---|
| **A** | `domain/hotkey.py` に `validate_hotkey(hotkey, validate_key_name: Callable)` の純粋関数 1 本 | モジュール 1 つで済むが、**domain に Callable 注入の前例が無く**「純粋関数・注入なし」という現 domain のスタイルを崩す。domain がキー名検証という infrastructure 関心を（間接的に）知る |
| **B** | `application/hotkey_service.py` に全部（gateway を DI）。domain は触らない | モジュール 1 つ・既存 DI パターン一致だが、**hotkey 文法が domain に載らず idea_01 の主目的が半分未達**。テストに fake gateway が必須 |
| **C（推奨）** | **分割**: domain = 純粋な文法検査（3 種）/ application = 合成 + キー名検証（4 種目） | 層の境界と関心が**正確に一致**。domain 側は**注入なしの純粋関数＝既存 domain スタイルに完全一致**し、モック無しでテストできる（既存 domain テストと同じ書き方）。application 側は gateway DI＝`ActionExecutor` パターン一致。モジュールは 2 つ増える |

**推奨: 案 C**。理由は「3/4 のエラーが注入なしでテストできる」ことと、
「domain のクリーンさ（標準ライブラリのみ・クラス 0・DI 無し）を崩さない」こと。

## §4 設計本文（案 C・確定）

### §4.1 domain — `keyseq/domain/hotkey.py`（新規）

```python
def validate_hotkey_syntax(hotkey: str) -> tuple[str, str, list[str]]:
    """hotkey の文法を検証し (エラーメッセージ, 正規化hotkey, 要素リスト) を返す。
    エラーなしならエラーメッセージは ""。キー名の実在は検証しない（infrastructure の関心）。"""
```

- 現行 `App.validate_hotkey` の**ステップ ①〜⑥**（空チェック / split / strip+lower / 空要素検出 /
  正規化 / 重複検出）をそのまま移す。**ステップ ⑦（キー名検証）は含まない**。
- 標準ライブラリのみ・**注入なし・クラスなし**（既存 domain スタイル準拠）。
- 戻り値: 異常時 `(msg, "", [])` / 正常時 `("", normalized, parts)`。
  **`parts` を返すのは application がキー名検証で使うため**（§2-設計判断 2。再 split をしない）。
  `normalized == "+".join(parts)` が常に成り立つ。
- **公開契約 `(error, normalized)` は application 側（§4.2）が担保する**。3 タプルは内部インターフェース。

### §4.2 application — `keyseq/application/hotkey_service.py`（新規）

```python
class HotkeyService:
    def __init__(self, *, validate_key_name: Callable[[str], None]) -> None: ...
    def validate(self, hotkey: str) -> tuple[str, str]:
        """(エラーメッセージ, 正規化hotkey)。App.validate_hotkey と同一契約。"""
```

- `validate_hotkey_syntax(hotkey)` を呼び、**エラーがあればそのまま返す**（＝文法エラーが優先。現行の順序を保持）。
- エラーが無ければ **domain から受け取った `parts` をそのまま**各要素へ `validate_key_name(p)` を適用
  （§2-設計判断 2。`normalized.split("+")` による**再構成はしない**）。
- **依存は `validate_key_name` の Callable のみ**（`input_gateway` オブジェクト全体ではなく必要な関数だけ受け取る。
  `ActionExecutor` が `validate_hotkey: Callable` を受け取る前例と同型で、テスト時に fake を渡せる）。

#### 実装形（`validate` の本体・現行 `app.py:440-446` の構造を厳密に踏襲）

**`try` はループ全体を包み、`except` はループ変数 `p` を参照する**（現行と同じ形）。
`try` を各要素の内側に置くと `p` の値がずれる / 早期 return の位置が変わるため、**下記の形を厳守**:

```python
def validate(self, hotkey: str) -> tuple[str, str]:
    error_message, normalized, parts = validate_hotkey_syntax(hotkey)
    if error_message:
        return error_message, ""

    try:
        for p in parts:
            self._validate_key_name(p)
    except Exception as e:
        return f"不明なキー名があります: '{p}'（詳細: {e}）", ""

    return "", normalized
```

- 現行同様、**最初に失敗したキーで例外が送出され `p` はその失敗キーを指す**（Python のループ変数リーク）。
- 例外の捕捉は現行と同じく `except Exception`（`validate_key_name` は不正時に元例外を再 raise する）。

### §4.3 presentation — `keyseq/presentation/app.py`

- `__init__`: `self.input_gateway = InputGateway()`（現 `app.py:67`）の**後**、
  `ActionExecutor` 生成（現 `app.py:69`）の**前**に
  `self.hotkey_service = HotkeyService(validate_key_name=self.input_gateway.validate_key_name)` を生成。
- **`app.py:71` の注入元を差し替える**: `validate_hotkey=self.validate_hotkey`
  → `validate_hotkey=self.hotkey_service.validate`。**これで層の逆転が解消**する
  （ActionExecutor は application のオブジェクトを受け取る）。
- `App.validate_hotkey` は**薄い委譲**に:
  ```python
  def validate_hotkey(self, hotkey: str) -> tuple[str, str]:
      return self.hotkey_service.validate(hotkey)
  ```
  （dialogs が `parent.validate_hotkey` で使う外部契約のため**削除しない**。docstring は現行を維持）
- **`application/action_executor.py` は変更しない**（`validate_hotkey: Callable` のシグネチャのまま。
  注入元が変わるだけ）。

### §4.4 安全網（テスト）

現状 `validate_hotkey` のテストは 0 件。**移設前に特性テストで現行挙動を固定する**
（`/refactor_check` の「項目 0: 安全網の確認」の精神）。

- **移設前**: `tests_ui/test_app_ui_flows.py` に `App.validate_hotkey` の特性テストを**新規追加**
  （4 エラー + 正常系）。**既存テストのアサーションは変更しない・追加のみ**。
  これが移設後も無変更で pass することが挙動不変の証明になる。
- **移設後**: `tests/test_hotkey.py`（domain・モック無し）/ `tests/test_hotkey_service.py`
  （application・fake `validate_key_name` を注入）を追加。形式は **unittest**（既存 `tests/` に準拠）。

## §5 エラーメッセージ（不変・完全一覧）

**1 文字も変更しないこと。** 出典は現行 `app.py`。

| # | 契機 | 文字列 | 移設後の担当 |
|---|---|---|---|
| 1 | 空 | `hotkey が空です。` | domain |
| 2 | `+` 前後が空 | `hotkey の '+' の前後が空です（例: 'ctrl++c' や '+ctrl+c' や 'ctrl+c+' は不可）。` | domain |
| 3 | 同一キー重複 | `hotkey に同じキーが重複しています（例: 'ctrl+ctrl+c'）。` | domain |
| 4 | 不明なキー名 | `f"不明なキー名があります: '{p}'（詳細: {e}）"` | application |

## §6 受け入れ条件（確定）

| # | 条件 | 対応 § |
|---|---|---|
| 1 | `git grep -n "def validate_hotkey" -- keyseq/presentation/app.py` が 1 件で、本体が `self.hotkey_service.validate(hotkey)` への委譲のみ（実装ロジックが残っていない） | §4.3 |
| 2 | `app.py` の `ActionExecutor` 注入が `validate_hotkey=self.hotkey_service.validate` になっている（presentation のバウンドメソッドを注入していない）＝**層の逆転が解消** | §4.3 |
| 3 | `keyseq/domain/hotkey.py` が標準ライブラリのみに依存（`git grep -n "^from\|^import" keyseq/domain/hotkey.py` で確認）。domain → application / infrastructure の import が無い | §4.1 |
| 4 | エラーメッセージ 4 種が §5 と 1 文字一致（移設前後で diff なし） | §5 |
| 5 | **`git grep -n "split(\"+\")" -- keyseq/application/hotkey_service.py` が 0 件**（parts 再構成をしていない＝§2-設計判断 2 の遵守） | §4.2 |
| 6 | `HotkeyService.validate` の `try` が**ループ全体を包む**形になっている（`p` が失敗キーを指す。§4.2 の実装形と一致） | §4.2 |
| 7 | `tests/test_hotkey.py` が **App / tk.Tk を生成せず**モック無しで pass（テスト容易性の達成） | §4.4 |
| 8 | `tests/test_hotkey_service.py` が fake `validate_key_name` の注入で pass | §4.4 |
| 9 | 移設前に追加した特性テスト（tests_ui）が**移設後も無変更で pass** | §4.4 |
| 10 | 標準検証 4 項目が全緑（compile clean / tests **59+新規** / tests_ui **9+新規** / smoke pass。`.venv` python） | — |
| 11 | 実機目視: アクション編集ダイアログで不正 hotkey（`ctrl++c` / `ctrl+ctrl+c` / 空 / 不明キー）を入力してエラーが従来どおり出る。正常 hotkey が正規化されて保存される。hotkey アクションが実行される | §4.3 |

## §7 スコープ外（本フェーズでやらない）

- [idea_02](../backlog/idea_02_startup_font_settings_cleanup.md)（起動設定 / フォント クラスタ）
- **単キー検証の統一** — `presentation/controllers/keymap_panel_controller.py:144, :376` /
  `key_capture.py:125` が `self._app.input_gateway.validate_key_name(...)` を直接呼んでいる
  （hotkey ではなく単キー検証）。同種の層越えだが**本フェーズでは触らない**（別 idea 候補）
- `action_executor.py` の変更（注入元が変わるのみ・シグネチャは不変）
- hotkey 文法自体の変更 / エラーメッセージの改善 / `validate_key_name` の例外→戻り値化
- `app.py` の行数削減それ自体（本件で減るのは約 31 行）

## §8 正本反映（フェーズ末昇格・予定）

| 対象 | 内容 |
|---|---|
| 正本 `instructions/common/spec_detail/` | **要調査**: hotkey 検証の仕様が記載された節があるか（あれば担当層の記述を更新）。無ければ**昇格不要**（挙動不変のため仕様変更なし） |
| `instructions/common/codebase_map.md` | 「主な責務」へ `HotkeyService`（application）/ `domain/hotkey.py` を追記。App の責務から hotkey 検証の実装を除き「dialogs 向け契約（薄い委譲）」に整理 |
| 実装 | `keyseq/domain/hotkey.py`（新規）/ `keyseq/application/hotkey_service.py`（新規）/ `keyseq/presentation/app.py`（委譲化・注入元差し替え） |
| テスト | `tests/test_hotkey.py`（新規）/ `tests/test_hotkey_service.py`（新規）/ `tests_ui/test_app_ui_flows.py`（特性テスト追加） |
| 別実装同期 | なし |

## 関連

- 起票元: [idea_01](../backlog/idea_01_hotkey_validation_to_domain.md)
- 前フェーズ: `01_view_ref_cleanup`（判断は [decisions_archive/01_view_ref_cleanup.md](../../.claude_data/state/decisions_archive/01_view_ref_cleanup.md)）
- 計画04（完了）: [04_widget_split_plan.md](../modified_proposal/04_widget_split_plan.md)。
  本件は W7「app.py 残留メソッドの分類」で「どの分類にも属さない残留ロジック」とされた項目。
- 後続: [idea_02](../backlog/idea_02_startup_font_settings_cleanup.md)
