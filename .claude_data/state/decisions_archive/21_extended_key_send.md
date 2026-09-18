# decisions_archive / phase 21: 拡張キーを拡張キーとして送る

対応表: phase 21 / 暫定仕様なし（**直接改訂モード**）/ decisions 21。
起票元: ユーザー要望（2026-09-18・hotkey で範囲選択が効かない）。関連 = idea_23（押す / 離すアクション・**未着手のまま**）。
完了 2026-09-19。**infrastructure 限定・hotkey の書式 / JSON 不変**。
正本 = `spec_detail/key_input.md` **§7.7「キーの送信」**（新設）/ `codebase_map.md`「キーの送信」節（新設）。

## 問題

hotkey アクションで `shift+right` / `ctrl+shift+end` を送っても範囲選択にならない。
原因は `keyboard` ライブラリが矢印・Home・End 等を**拡張キーフラグなし**で送ること
（`_winkeyboard._send_event` が `keybd_event` に KEYEVENTF_EXTENDEDKEY を付けない。`right` = scan 0x4D = テンキー 6 と同じ）。
実機検証で確定（A `keyboard.send("shift+right")` = 選択されず / B 拡張フラグ付き `keybd_event` = 選択された）。
**押す / 離すアクションの追加では直らない**（同じ送信経路のため）→ idea_23 へ分離。

## 確定した設計判断

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | **対象は拡張キー全般 18 名**（up / down / left / right / home / end / page up / page down / insert / delete / right ctrl / right alt / windows・left windows・right windows / menu / print screen / num lock）（ユーザー） | 推奨の移動キー 10 個のみ = 右 Ctrl・Windows・menu 等が非拡張のまま残る |
| 2 | **hotkey アクションとキーマップの送信先キーの両方**に適用（ユーザー） | 片方のみ = 同じキーが経路で別扱いになる |
| 3 | **拡張キーの表はアプリ側に持つ**（キー名 → 仮想キー / スキャンコード。`keyseq/infrastructure/input_gateway.py` の `_EXTENDED_KEYS`） | `keyboard` の `from_name` = 同名に拡張 / 非拡張が混在し `windows` が表に無い（メイン実測） |
| 4 | **拡張キーを含む hotkey だけ自前経路**（含まなければ従来どおり `keyboard.send(hotkey)`） | 全部を自前送信 = 通常キーの既存挙動まで変わる |
| 5 | **記述順に押し逆順に離す・例外時も押したキーを逆順に離してから再送出**（従来どおり） | 例外を握りつぶす = キーが押されたまま残る |
| 6 | **`windows` は左 Windows として送る**。`ctrl` / `alt` / `shift` は非拡張のまま | 左右未指定を右扱い = 既存の hotkey の意味が変わる |
| 7 | **テンキーの Enter・`/` は対象外**（名前で区別できない）。**`alt gr` も従来どおり** | 名前で送り分ける = §7.7 の範囲を超える（下記「記録のみ」6 を参照） |
| 8 | **名前の正規化は公開 API `keyboard.normalize_name`**（task_02b。0.13.5 で公開 = メイン実測） | 非公開 `keyboard._canonical_names` の直 import = ライブラリ更新で壊れる |

## フェーズ中の追加判断

### 【task_02】二次レビューの採否（ユーザー 2026-09-19）
- 統合確認: compile clean / `tests` 459 OK / `tests_ui` 438 OK / smoke OK。`codex-reviewer` = 指摘なし。`deep-reviewer` = 完了可（条件付き）。
- **採用 → task_02b**: 指摘 1（拡張キーフラグを検証するテストが無く、フラグを外しても 8 本とも通る）/ 指摘 8a（上表 #8）。変異検査でフラグを外すと追加テストのみ失敗を確認。
- **採用 → 実機目視に 2 項目追加**（⑥自己起動 / ⑦ `windows`・`menu`・右 Alt・`num lock`・`print screen`）。
- **記録のみ（保留）**: ①送信の途中で失敗すると先行キーが実際に OS へ出る（`keyboard.send` は全解決後に送るため差がある。検証を先に通るので確率は低い）②`,` 区切りの多段 hotkey は現状アプリの検証で弾かれるため到達不能（将来許すなら `split("+")` の分岐を見直す）③離す側の例外は最初の例外を優先して握られる ④`requirements.txt` の `keyboard` はバージョン非固定。

### 【task_02】完了判定前レビューの採否（ユーザー 2026-09-19）
- `codex-adversarial-reviewer` = **指摘なし（approve）**。`deep-reviewer` = **条件付き完了可**（条件 = 完了処理の実施）。
- **採用 → task_02c**: 指摘 4（`send_hotkey` の拡張キー経路のテストが「通常キー先・拡張キー最後・1 個」の形しかなく、実装を「通常キーを先にまとめて押す」形へ変えても既存 3 本が通る）。
  → `right ctrl+c`（拡張キーが先頭）/ `right ctrl+insert`（拡張キー 2 個）の順序テストを 1 本追加。変異検査で押下順を入れ替えると**追加テストのみ** FAIL を確認。
- **採用 → 文書修正**: 指摘 2（`codebase_map.md` が旧表記 `keyboard._canonical_names.normalize_name` のまま → 公開 API へ）/ 指摘 7（`phase.md` のタスク一覧に task_02b・task_02c を追記）。
- **記録のみ**:
  - 指摘 3 = **send guard 解除と注入イベント到達のレース**。拡張キーは raw `keybd_event` のため `keyboard` の `is_replaying` による素通しが効かず、**自分が送った拡張キーがアプリのフックに届く**。現状は send guard（`action_executor.py` が張り `input_router` が即 return）が先に素通しにするので挙動は不変で、実機⑥でも自己起動しないことを確認済。ただし LL フックは別スレッドで走るため、**guard 解除とフック到達の順序は保証ではなく観測**。`keyboard.send` 経路も同型のレースであり新規リスクではないが、**guard の解除タイミングを変える改修時は再確認が要る**。
  - 指摘 6 = **`right alt` と `alt gr` は欧州系配列では同一の物理キー**だが、§7.7 は前者を拡張対象・後者を「従来どおり」と規定している。名前が違う以上仕様の矛盾ではなく、AltGr の正しい送信は Ctrl との組み合わせを伴い配列依存でフェーズ範囲を超えるため、**意図的に対象外**（現行の日本語配列では AltGr 自体が無く実害なし）。
  - 指摘 5 = canonical に無い OS 由来のキー名は表を素通りして非拡張で送られうる（§7.7「別名は keyboard の正規化に従う」に照らせば仕様適合）。**経路の実在は未実測の仮説**。
- **保留 → 別タスク化候補**: 指摘 8（`InputGateway.register_key_hook` に呼び出し元が無い = phase 21 差分外の既存デッドコード）。
- **除外（参考）**: 指摘 9（`_send_extended_event` が `keybd_event` の失敗を検知しない。`keyboard` 側も同等で新規劣化ではない）。

### 【task_02】実機目視（ユーザー 2026-09-19）
**全 7 項目 OK**（詳細は `instructions/phase/21_extended_key_send/integration_result.md`）。
`shift+right` / `ctrl+shift+end` の範囲選択とコピー / キーマップ経由 + 物理 Shift / 通常キー・text・マウス / フック停止・トグルと自己起動しないこと / `windows`・`menu`・右 Alt・`num lock`・`print screen`。

## refactor_check

**不要**（M1〜M6 該当なし。対象 = `keyseq/infrastructure/input_gateway.py` 1 ファイル・130 行 / +67 行）。
`press_key` と `release_key` の「拡張キー判定 → 分岐」は同型だが **2 箇所**（M3 の 3 箇所目は未発生）。

## 残存リスク

- 拡張キーの注入イベントがアプリのフックへ届くようになった（上記 指摘 3）。実機⑥で確認済だが順序は観測であり保証ではない。
- `num lock`（0x90 / 0x45 + EXTENDEDKEY）は MS 公式サンプル（KB177674）準拠だが、ハードウェアのスキャンコードには E0 が付かない特殊キー。実機⑦で OK のため実害なしと判断。
- 送信の途中で失敗すると先行キーが実際に OS へ出る（記録のみ ①）。
