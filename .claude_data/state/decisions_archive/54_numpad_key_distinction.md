# decisions_archive / phase 54: テンキーの区別

対応表: phase 54 / 暫定 38（v0.5・凍結）/ decisions 54。起票元: [idea_43](../../../instructions/backlog/idea_43_numpad_key_distinction.md)（2026-10-11・ユーザー要望）。
完了 2026-10-11。domain / application / infrastructure / presentation。JSON の形は変えない（キー名の値が増える）。**既存設定の意味が変わる**（`1` / `enter` / `end` 等は入力の判定では主キーボードだけ）。
正本 = `key_input.md` §7.7・§7.8 / `data_schema.md` §5.1 / `features.md` §4.2.12・§4.6 / 地図 = `codebase_map.md` の phase 54 の項。

## 確定した設計判断（ユーザー）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | 入力の判定・出力・記録・表示のすべてで区別 | — |
| 2 | 既存の名前は主キーボードだけ（入力の判定に限る・v0.3） | 両方に反応する名前を残す = 名前が 3 通りで重なり判定が複雑 |
| 3 | 名前 = `num 0`〜`num 9` / `num add` / `num subtract` / `num multiply` / `num divide` / `num decimal` / `num enter` | 記号のまま（`num /` 等）= `+` だけ書き方が違う・`+` / `,` と衝突 |
| 4 | NumLock に関係なく物理キーで同じ名前 | NumLock オフで別名（`num end` 等）= 同じ物理キーに 2 つの名前・トリガーが NumLock で変わる |
| 5 | 外部レイアウトの `id` より表の名前・表の名前はテンキーのイベントだけ（v0.3・v0.4 Codex 敵対的 high） | 外部レイアウト優先 = スキャンコードだけで引くため End が `num 1` になる |
| 6 | 記録は Tk の keycode（VK）+ 拡張ビット（`state & 0x40000`）で 16 キーとも区別（v0.5・task_01 の probe で keysym に `KP_` が付かないと判明） | keysym の `KP_` で変換 = Windows の Tk では来ない |
| 7 | 組み込みのキーボード表示にテンキーを足さない（v0.3） | 足す = 配置・ウィンドウ幅の変更が大きい |
| 8 | 記号の名前（`*` / `+` / `-`）の出力は従来どおり keyboard の解決（テンキーで送られ得る）（v0.3・起票時 deep-reviewer 高） | 主キーボードの位置へ shift つきで送る = 配列ごとの対応・暗黙の shift |
| 9 | `num ` で始まる表外の名前・`num_1` 等は検査でエラー（v0.4 Codex 敵対的 medium） | `num_1` を別名で受ける = トリガーの照合等にも別名が要る |

## 結果（タスク）

- task_01 probe（メイン実測・合成の `SendInput`）: フックの `is_keypad`・スキャンコード入力の送信（NumLock に従う）・偽の shift は前提どおり / Tk の記録は keycode + 拡張ビットで区別できると判明 → 暫定 38 v0.5
- task_02 名前の表・入力の名前・名前の検査（codex-implementer・reviewer 修正して採用 → 予約名の判定で `num_1` が表の名前に一致する不具合をメインで修正）
- task_03 送信（`SendInput` スキャンコード入力）と `key_identity`（codex-implementer・reviewer 採用・新規テストの Mock の戻り値をメインで修正）
- task_04 記録（codex-implementer・reviewer 採用・新規テストの期待値をメインで修正）。実機目視 §8-10〜12 OK
- task_05 統合確認（deep-reviewer 採用〔中 1・低 5〕・codex-reviewer 指摘なし）→ task_05-1 で `key_identity` の 0xE0xx を拡張として読み替え（`/` と `num divide` を同じキーに）
- task_06 正本反映・暫定 38 凍結

## 統合レビュー（task_05）の低の扱い

保留: `SendInput` の失敗時の例外（既存の後始末で離せる）/ 一部の記録の入口にテンキーの UI テストなし（共通関数は単体テスト済み・実機目視 OK）。除外: 前段の重複（目安内）・キーボード表示の窓の VK とスキャンコードの既存の取り違え（範囲外・悪化なし）。昇格時に記述: `num_lock` は有効。

## 完了判定前レビュー（task_06）

- deep-reviewer 修正して採用 → 文書の追従漏れ 4 件（L1 `codebase_map` の `send_hotkey` の分岐 / L2 phase 51 の項の記録の関数名 / L3 §7.8 の同じキーの判定の優先順 / L4 `features.md:387` の外部レイアウトの `id`）を修正
- Codex 敵対的 needs-attention（medium: 既存の `num 0`〜`num 9` の出力が主キーボードの数字からテンキーへ変わることの書き漏れ）→ ユーザー判断で `key_input.md` §7.8 に追記（コード変更なし）

## /refactor_check

**不要**（verifier 計測・メイン判定。keyseq/ 12 ファイル +254 / -30）。
M1: 600 行超なし（`input_gateway.py` 408・+107）/ M2: なし / M3: `is_replaying` の退避・イベント関数 2 つ等はいずれも 2 個目で非該当 / M4: テンキーの表 3 つは引くもの（スキャンコード / VK / 名前）が違いキー数がハードウェアで固定のため非該当 / M5: なし / M6: 新規定数のみ。
境界事例として `input_gateway.py` の責務の並び（送信・OS 設定・前面判定・名前の検査）を `current.md` の別タスク化候補に追記。
