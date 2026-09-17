# task_01_extended_key_send

## 目的

正本 `spec_detail/key_input.md` §7.7「キーの送信」（2026-09-18 ユーザー確定・本タスクで追加済み）に従い、
`InputGateway` の `send_hotkey` / `press_key` / `release_key` が **Windows の拡張キーを拡張キーフラグ付きで送る**ようにする。

**infrastructure 限定**（`keyseq/infrastructure/input_gateway.py` のみ）。application の呼び出し形・hotkey の書式と検証・domain・presentation・JSON は不変。

## 対象範囲（infrastructure 1 ファイル + tests 新規 1 ファイル）

### `keyseq/infrastructure/input_gateway.py`

1. **拡張キーの表**（モジュール定数）: 正規化後のキー名 → `(仮想キー, スキャンコード)`。すべて KEYEVENTF_EXTENDEDKEY 付きで送る。

   | キー名 | 仮想キー | スキャンコード |
   |---|---|---|
   | up / down / left / right | 0x26 / 0x28 / 0x25 / 0x27 | 0x48 / 0x50 / 0x4B / 0x4D |
   | home / end / page up / page down | 0x24 / 0x23 / 0x21 / 0x22 | 0x47 / 0x4F / 0x49 / 0x51 |
   | insert / delete | 0x2D / 0x2E | 0x52 / 0x53 |
   | right ctrl / right alt | 0xA3 / 0xA5 | 0x1D / 0x38 |
   | windows・left windows / right windows | 0x5B / 0x5C | 0x5B / 0x5C |
   | menu | 0x5D | 0x5D |
   | print screen | 0x2C | 0x37 |
   | num lock | 0x90 | 0x45 |

2. **名前の解決** `_resolve_extended_key(name: str) -> tuple[int, int] | None`（private・純関数）:
   `keyboard._canonical_names.normalize_name(name.strip())` で正規化（例: `pgup` → `page up` / `del` → `delete` / `apps` → `menu` / `win` → `windows`）し、表に無ければ `None`。
   正規化で例外が出たら `None`（従来の `keyboard` 経路へ回し、エラーの出方を変えない）。

3. **OS への送信** `_send_extended_event(vk: int, scan: int, key_up: bool) -> None`（private）:
   `ctypes.windll.user32.keybd_event(vk, scan, KEYEVENTF_EXTENDEDKEY | (KEYEVENTF_KEYUP if key_up else 0), 0)`。
   `ctypes.windll` はこの関数の中で参照する（import 時に Windows 以外で落ちない・テストでこの関数を patch できる）。

4. **`press_key(key)` / `release_key(key)`**: `_resolve_extended_key(key)` が値を返せば `_send_extended_event`（押す / 離す）、`None` なら従来どおり `keyboard.press` / `keyboard.release`。

5. **`send_hotkey(hotkey)`**:
   - `hotkey.split("+")` の各要素（前後空白を除く）に**拡張キーが 1 つも無ければ従来どおり `keyboard.send(hotkey)` をそのまま呼ぶ**（通常の hotkey の挙動を変えない）。
   - 拡張キーを含む場合は、**要素を記述順に `press_key` で押し、逆順に `release_key` で離す**。
     押している途中や離す途中で例外が出ても、**押し終えたキーは逆順にすべて離してから**例外を再送出する（押したままのキーを残さない。離す側の例外は握りつぶさず、最初の例外を優先して再送出）。

### `tests/test_input_gateway_send.py`（新規）

`keyboard.send` / `keyboard.press` / `keyboard.release` と `input_gateway._send_extended_event` を `unittest.mock.patch` で置き換え、**1 本の呼び出し記録（順序付き）**に集めて検証する。OS へは送らない。

1. `send_hotkey("shift+right")` → `press shift` → `ext(0x27, 0x4D, down)` → `ext(0x27, 0x4D, up)` → `release shift` の順。`keyboard.send` は呼ばれない。
2. `send_hotkey("ctrl+shift+end")` → ctrl・shift を押し → end（0x23/0x4F）を拡張で押す / 離す → shift・ctrl の順に離す。
3. `send_hotkey("ctrl+c")` → `keyboard.send("ctrl+c")` が 1 回だけ呼ばれ、press / release / 拡張送信は呼ばれない。
4. `press_key("right")` / `release_key("right")` → 拡張送信（down / up）。`press_key("a")` → `keyboard.press("a")`。
5. 別名と左右: `pgup` → 0x21/0x49、`del` → 0x2E/0x53、`apps` → 0x5D、`win` と `windows` → 0x5B、`right windows` → 0x5C、`right ctrl` → 0xA3/0x1D、`right alt` → 0xA5/0x38、`print screen` → 0x2C/0x37、`num lock` → 0x90/0x45。
6. 対象外: `ctrl` / `alt` / `shift` / `enter` / `/` / `alt gr` は `_resolve_extended_key` が `None`（keyboard 経路）。
7. 例外時の後始末: `send_hotkey("ctrl+shift+end")` で end を押す拡張送信が例外を出したら、shift → ctrl の順に `keyboard.release` が呼ばれ、例外が呼び出し元へ伝わる。
8. 空白を含む要素: `send_hotkey("shift + right")` のように要素の前後に空白があっても拡張キーとして解決される（要素は strip してから押す）。

### 設計メモ / 制約

- **application（`ActionExecutor` 等）を変えない**。send guard はこれまでどおり呼び出し元が張る。
- 拡張キーの表・解決・OS 送信は `input_gateway.py` の中に置く（利用はこのファイルだけ = Private。新規モジュールは作らない）。
- `keyboard` のフックが注入キーをどう受け取るかは変えない（送信中は呼び出し元の send guard で素通し）。
- `keyboard.press` / `release` に渡すのは要素文字列そのもの（strip 後）。`keyboard.send` の経路では元の `hotkey` 文字列をそのまま渡す。
- 既存テストの期待値は変えない。

## 読むファイル

1. `instructions/common/spec_detail/key_input.md` §7.7
2. `keyseq/infrastructure/input_gateway.py`（全体・編集対象）
3. `keyseq/application/action_executor.py:76-102`（呼び出し元。変更しない）
4. `keyseq/domain/hotkey.py`（hotkey の書式 = `+` 区切り。読むだけ）
5. `.venv/Lib/site-packages/keyboard/_canonical_names.py` の `normalize_name`（`rg -n "def normalize_name"`）/ `keyboard/__init__.py` の `send` / `press` / `release`（`rg -n "^def (send|press|release)\b"`）

## 含まない

- 統合確認・二次レビュー・実機目視・完了処理（**task_02**）。
- 押す / 離すアクション（idea_23）/ hotkey の書式・検証の変更 / text・マウス送信 / テンキーの Enter・`/` の送り分け。
- `codebase_map.md` の更新はメインが本タスク内で行う（実装者は触らない）。

## 確認

実行は `verifier`。python は `..\..\..\.venv\Scripts\python.exe`。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests.test_input_gateway_send -v` の 8 項目が pass。
3. `-m unittest discover -s tests` が全 pass。
4. `-m tests.smoke_app` が SMOKE OK（import・起動に影響がないこと）。
5. **変異検査**: `_send_extended_event` の flags から `KEYEVENTF_EXTENDEDKEY` を外す変更は実送信をモックしているため検出されない → 代わりに表の `right` の仮想キーを 1 だけずらした状態で項目 1 が失敗することを確認し、元に戻す（verifier がリポジトリに残さない）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は **task_02** で実施（OS へ実際に送る挙動はモックでは確かめられないため必須）。
