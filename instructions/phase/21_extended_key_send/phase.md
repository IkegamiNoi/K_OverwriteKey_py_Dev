# phase.md

## フェーズ名

拡張キーを拡張キーとして送る（extended_key_send）

## フェーズの目的

hotkey アクションで `shift+right` / `ctrl+shift+end` 等を送っても範囲選択にならない不具合を直す。
原因は `keyboard` ライブラリが矢印・Home・End 等を**拡張キーフラグなし**で送ること（`_winkeyboard._send_event` が `keybd_event` に KEYEVENTF_EXTENDEDKEY を付けない）で、
2026-09-18 に実機で確定した（検証: `keyboard.send("shift+right")` は選択されず / 拡張キーフラグ付きの `keybd_event` は選択された）。

**infrastructure 限定（`InputGateway` の送信部分）。application / domain / presentation・hotkey の書式と検証・JSON は不変**。

- 起票元: ユーザー要望（2026-09-18・範囲選択が効かない）。関連 = [idea_23](../../backlog/idea_23_key_press_release_actions.md)（押す / 離すアクション。本フェーズの対象外）。
- 主入力（暫定仕様）: なし（直接改訂モード）。正本の改訂文言は下記「確定」に記載（ユーザー確定済）。
- モード: **直接改訂モード**。番号対応: phase 21 / 暫定なし / decisions 21。

## 確定（ユーザー 2026-09-18）

- **対象は拡張キー全般**（移動キー 10 個に限らない）。**hotkey アクションとキーマップの送信先キーの両方**に適用する。
- 拡張キーの判定は `keyboard` ライブラリの対応表を使わず、**アプリ側にキー名 → (仮想キー, スキャンコード) の表を持つ**（ライブラリの表は同じ名前に拡張 / 非拡張が混在し、`windows` は表に無い = メイン実測）。
- 正本 `spec_detail/key_input.md` に次の節を追加する（文言確定）:

```markdown
### 7.7 キーの送信

* アプリが送るキー（出力シーケンスの hotkey アクション・キーマップの送信先キー）のうち、
  Windows の**拡張キー**は拡張キーとして送る（テンキーや左側のキーとして扱われないようにする。
  例: 拡張キーとして送らないと `shift+right` がテンキーの 6 と Shift の組み合わせとして扱われ、範囲選択にならない）
* 対象のキー名（別名は keyboard ライブラリの名前の正規化に従う）:
  up / down / left / right / home / end / page up / page down / insert / delete /
  right ctrl / right alt / windows・left windows・right windows / menu（アプリケーションキー）/ print screen / num lock
  * 左右を指定しない `windows` は左の Windows キーとして送る。`ctrl` / `alt` / `shift` は左側（非拡張）のまま
  * 名前で区別できないテンキーの Enter・`/` は対象外（名前は主キーボード側のキーを指す）。`alt gr` は従来どおり
* 組み合わせは記述順に押し、逆順に離す（従来どおり）。テキスト入力（text）・マウス操作は対象外
* hotkey の書式・検証（`codebase_map.md` の hotkey 文法）は変えない
```

## スコープ

### 含む

- 正本 `key_input.md` §7.7 の追加（上記の文言）。
- `keyseq/infrastructure/input_gateway.py`: `send_hotkey` / `press_key` / `release_key` を、対象の拡張キーだけ拡張キーフラグ付きで送り、それ以外は従来どおり `keyboard` で送る形にする。
  拡張キーの表は infrastructure に置く（配置は task_01 で決める）。
- `tests/`: 送信部分の単体テスト（OS への実送信はモックで置き換える）。
- `codebase_map.md` に InputGateway の送信部分（`send_hotkey` / `press_key` / `release_key`・拡張キー対応）の記述を新設（既存は HotkeyService 節とフック関連節に分散した言及のみ）。

### 含まない（後送り）

- 押す / 離すアクション（[idea_23](../../backlog/idea_23_key_press_release_actions.md)）。
- hotkey の書式・検証の変更（`,` 区切りの連続送信の扱い等）/ キーマップの送信先キー名の検証強化。
- テンキーの Enter・`/` を名前で送り分けること。text アクション（`keyboard.write`）・マウス操作。
- 自アプリのフックが注入したキーをどう受け取るかの変更（送信中は send guard で素通しのまま）。

## このフェーズで読むファイル

1. `keyseq/infrastructure/input_gateway.py`（編集対象）
2. `keyseq/application/action_executor.py:76-102`（`send_hotkey` / `press_key`・`release_key` の呼び出し元）
3. `keyseq/domain/hotkey.py` / `keyseq/application/hotkey_service.py`（hotkey 文法 = `+` 区切り・小文字化。読むだけ）
4. `.venv/Lib/site-packages/keyboard/__init__.py`（`send` / `press` / `release` / `parse_hotkey` の順序）/ `keyboard/_canonical_names.py` の `normalize_name` / `keyboard/_winkeyboard.py` の `_send_event`（読むだけ）
5. `instructions/common/spec_detail/key_input.md` / `codebase_map.md` の hotkey 文法（HotkeyService 節）とフック関連節（InputGateway の独立節は無い = task_01 で新設）

**読まない**: `keyseq/presentation/` / `keyseq/application/config_service/` / 凍結済み暫定仕様。

## タスク

1. **task_01**: 正本 `key_input.md` §7.7 の追加 + `InputGateway` の拡張キー対応（hotkey・press / release）+ 拡張キーの表 + `tests/` の単体テスト + `codebase_map.md`。
2. **task_02（最終）**: 統合確認（`tests` / `tests_ui` 全体 + `smoke_app`）+ 二次レビュー（`deep-reviewer` + `codex-reviewer`）+ **ユーザーによる実機目視**
   （メモ帳等で hotkey `shift+right`・`ctrl+shift+end` → `ctrl+c` の範囲選択とコピー / キーマップで別のキーを `right` 等へ割り当てて物理 Shift と併用 / 通常キーの hotkey・text が従来どおり）+
   `decisions_archive/21_extended_key_send.md` + `current.md` 完了記載 + **`/refactor_check`** + 完了判定前レビュー（`deep-reviewer` + `codex-adversarial-reviewer`）。

タスク定義は着手する順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点:

- **対象キーの表** — §7.7 の名前（別名の正規化後）と仮想キー / スキャンコード / 拡張フラグの対応が Windows の定義と一致するか。対象外のキー（`ctrl` / `alt` / `shift` / `enter` / `/` / `alt gr`）の送り方が変わっていないか。
- **押す順・離す順** — 組み合わせは記述順に押し逆順に離す。拡張キーと通常キーが混在しても順序が崩れないか。例外時に押したままのキーを残さないか。
- **層と依存** — 変更が infrastructure に閉じ、application の呼び出し形（`send_hotkey(normalized)` / `press_key` / `release_key`）が変わっていないか。OS 依存（`ctypes`）が infrastructure の外へ漏れないか。
- **テストの検出力** — 実送信をモックし、拡張フラグの有無・順序を検証しているか（呼び出し回数だけで済ませていないか）。

エージェントの使い分けは `.claude/rules/agent_selection.md`:

- 各タスクの必須レビュー = `reviewer` / 実装 = `codex-implementer` / テスト実行 = `verifier`
- task_02 の統合確認時 = `deep-reviewer` + `codex-reviewer` / フェーズ完了判定前 = `deep-reviewer` + `codex-adversarial-reviewer`
