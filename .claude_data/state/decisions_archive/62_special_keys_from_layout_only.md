# decisions_archive / phase 62: 特殊キーの名前をレイアウトだけが決める

対応表: phase 62 / 暫定 45（v0.5・凍結）/ decisions 62。起票元: idea_49（2026-10-17・phase 61 の起票時の議論から分離）。
完了 2026-10-18。

- 影響範囲:
  - domain: 既知の特殊キーの表を削除
  - presentation: `keyboard_layouts`・`LayoutController`・`app.py` の注入
  - infrastructure: `InputGateway` の解決の一本化
- **JSON スキーマ不変**（v0.4 で足した `extra_scan_codes` は v0.5 で取り下げ）
- 正本:
  - `key_input.md`: §7.1「フックの実行時のキー名の出どころ」/ §7.4 / §7.7「キー名 → 走査コードの解決の順」/ §7.8
  - `features.md` §4.6「レイアウトの JSON の `scan_code`」
- 地図: `codebase_map.md`（`keyboard_layouts.py`・`LayoutController`・キーの送信の節）

## 確定した設計判断（ユーザー 2026-10-18）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | 受け取る側（フック・画面の枠の編集の窓）は既知の表を外し、レイアウトの `scan_code` だけで引く（引けなければ `event.name`） | JIS 系のレイアウトのときだけ既知の表 = 判定が暗黙になる |
| 2 | 送る側は テンキー → 拡張 → keyboard → **選んでいるレイアウトの `id` → `scan_code`** の順に引き、既知の表は削除 | 表を送信用に残す = 自作レイアウトの自由な `id` を送れず、名前の出どころが 2 つになる / レイアウトだけ = keyboard が知る名前まで縛られる |
| 3 | 特殊キーを書いていないレイアウト（US TKL）では `muhenkan` 等は送れない。後方互換は考慮しない | 表を残して US TKL でも送る（ユーザーが単純さを優先） |
| 4 | レイアウトが変わる前に押したままのキーをすべて離す（案 B）。起動中の JSON の書き換えによる受け取りと送信のずれは受容 → idea_51 | 案 A = 受け取りと送信で同じ写しを使う（範囲が広い）/ gateway が押したときの値を覚える（入口が多くロックが要る） |
| 5 | （v0.4 → v0.5 で取り下げ）受け取り用の `extra_scan_codes` | 実機目視で、押下だけが続けて届くキーには効かないと判明（下記）→ idea_52 |

## タスク中の判断

### 【起票】暫定仕様先行モード
- 現状監査で、**出力の `muhenkan` 等は検査を通るのに送れていなかった**と判明
  - 実測: `keyboard.parse_hotkey('muhenkan')` が `ValueError`
  - 原因: 送信が既知の表を見ず、keyboard に名前をそのまま渡していた
- 起票時の deep-reviewer の判定は「修正して採用」。指摘 9 件を反映した:
  - 離し損ね
  - 外部レイアウトの毎回の読み直し
  - `scan_code` の範囲
  - 解決の成功条件
  - 渡し方
  - テストの漏れ
  - 受け入れ条件
- Codex 敵対的レビュー（needs-attention・high 2 / medium 1）
  - 指摘: release_all の失敗・同じ id の読み直し・受け取りと送信の読み方の違い
  - 対応: ユーザー判断 = 案 B（#4）
- 整合チェックの reviewer: 採用（参考 2 件を task_01 の行へ）

### 【task_01】受け取り（presentation）
- Codex 実装・reviewer 採用
- tests 1693 / tests_ui 1111 / smoke OK

### 【task_02】送信と既知の表の削除
- Codex 実装・reviewer 採用
- 落ちたテストは 1 件。`num lock` の検査が keyboard を呼ぶことまで確かめていたテストで、拡張キーが先に当たる §4.1 の順と合わなかった → 期待値を仕様に合わせてメインが修正

### 【task_03】レイアウトが変わる前の離し
- Codex 実装・reviewer 採用
- テストのスタブの戻り値の不備（`Mock` を反復）をメインが修正
- tests 1706 / tests_ui 1111 / smoke OK

### 【task_03 実機目視・2026-10-18】
- 受け取り: 半角/全角・かな OK、無変換・変換 NG
- 送信: 出力の `muhenkan`・`zenkaku_hankaku` OK（物理キーと同じ動き）
- US TKL: 実行時エラー（仕様どおり）。hotkey のアクションは保存時に検査しない（既存）

### 【無変換・変換の切り分け】
- keyboard の hook の実測: 無変換 = 走査コード 241・変換 = 242（`name=None`）
- v0.4（`extra_scan_codes`・Codex 敵対的の指摘 2 件を反映）→ task_03b を実装 → 実機で二重送信と、変換で IME が ON になる
- 低レベルフックの生の値:
  - 無変換・変換とも、押下（`VK_IME_OFF` / `VK_IME_ON`・`ext=1`）が約 60 ms の間に 3 回届き、**離しが無い**
  - 半角/全角は UP 0xF4 → DOWN 0xF3
- 環境:
  - MS-IME のキーの割り当てはオフ
  - `Scancode Map` も、キーを置き換える常駐ツールも無い
  - OS のキーボードは `PCAT_106KEY`
  - → キーボード本体が LANG2 / LANG1 で送る見込み
- 仕組み: 2 回目の押下が送信ガードの最中に届いて素通りし（`input_router.py:88-90`）、3 回目で再び置換する
- ユーザー判断 A: task_03b を戻し（コードは 26913ee と同一）、§3.1 を取り下げ → idea_52

### 【task_04 /refactor_check】不要（2026-10-18）
- 範囲: `git diff 75123ac..HEAD -- keyseq/`（5 ファイル・+122 / -96）
- M1: 600 行超は `app.py` 754 行（+4）のみ
- M2・M5: 0 件
- M3: 同型は最大 2 か所
  - `press_key` / `release_key` の対
  - `layout_controller` の「id が変わるときだけ離す」2 行
- M4: 種類分岐の場所（`press_key` / `release_key` / `key_identity`）は phase 前から同じ 3 か所で、場所の数は増えていない
- M6: 範囲 1〜255 の直値が `input_gateway._resolve_key` と `keyboard_layouts.resolve_layout_scan_code_from_key_name` の 2 か所。既存の定数と同じ値ではないため非該当 → current.md の別タスク化候補へ 1 行

### 【task_04 完了判定前レビュー】deep-reviewer 修正して完了 / Codex 敵対的 needs-attention（high 1・medium 1）→ ユーザー確定（2026-10-18「推奨どおり」）

- **medium（Codex）・中（deep 1）→ 案 a（採用・task_04b）**
  - 指摘: 構成の読込・新規作成は `sync_keyboard_layout_controls` を呼ぶだけで、外部レイアウトの登録を読み直していなかった（`app.py:599`・メインが裏取り）。送信が前の構成のレイアウトを引き得て、正本・暫定 45 §6 の「構成の読込で読み直す」とも食い違う（前提の誤り）
  - 対応: `_sync_control_vars_from_data` から `reload_keyboard_layouts` を呼ぶ。起動時は 2 回呼ばれるが、登録の収集が重なるだけなので残す
  - 結果: Codex 実装・reviewer 採用
- **high（Codex）→ 受容**
  - 指摘: 離しに失敗したまま切り替えると、再試行が新しいレイアウトで引いて別の走査コードへ離しを送り、成功扱いで記録が消える。元のキーは押されたまま残る
  - 対応: SendInput の失敗と切替が重なるときだけなので受容。正本 §7.7 の受容に明記し、idea_51 に追記
- **deep の低（採用・文書）**
  - 2: §7.4 の「「`」が揃った」は誤りなので削る（フックは `event.name`・未確認、キーボードUI は `grave`）
  - 3: 「MS-IME の割り当てに関係しない」→「オフにしても起きる」
  - 4: §4.6 に「押下だけで届く走査コードを `scan_code` に書かない」を追加
  - 5: `release_all` はマウスも離す・離してから置き換えるまでの間の受容
  - 6・8: codebase_map にデバッグ出力の判定とテストファイル
  - 9: 受け入れ条件 #10 の「別名の正規化」は「大文字小文字・空白」と読み替え
- **除外**
  - deep 7: 未使用の引数。別タスク化候補へ
  - deep 10: `send_hotkey` の事前判定。検査と送信の間にレイアウトが変わるときだけ
- 残存リスク:
  - 送信の 123 / 121 が物理キーと同じ動きになることは、1 台・MS-IME の実機目視でしか確かめていない
  - フックの `event.name` の値（「`」・`半角/全角`）は未確認
