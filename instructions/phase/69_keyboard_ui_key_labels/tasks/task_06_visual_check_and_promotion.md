# task_06_visual_check_and_promotion

## 目的

実機目視で暫定 52 §9 を確かめ、正本へ反映（§11）して暫定 52 を凍結し、フェーズを完了させる。
**コードは変えない（目視の不具合は枝番タスクで起票）。文書のみ。**

## 対象範囲

### 実機目視（ユーザー）

準備: メニュー「設定」→「外部レイアウトを追加…」で `config/user/keylayout/jis.json`・`us_tkl.json` を追加しておく（登録済みなら不要）。キーボードUIを開く。

1. JIS（見本）を選び、キーボードUIを右下の角のドラッグで最小まで縮める → `Esc`・`MODE`・`F2`・`半角/全角`（2 行）・`Caps`・`Enter`・`Shift` 等が単語の途中で折り返さず枠の中に出る。幅が約 399px まで縮む（以前は 510 で止まった）
2. US TKL（内蔵）を選び、同じく最小まで縮める → `Backspace`・`Home`・`PgUp`・`Scroll`・`Pause`・`Down`・`Right`・`STOP` 等が途中で折り返さない
3. 普通の大きさ（開いた直後より大きく広げた状態）で、文字の大きさが不自然でない（5 文字以上の `Enter`・`Shift`・`Space` が以前より大きく出るのは仕様どおり）
4. JIS で、あるキーに `zenkaku_hankaku` をキー置換で割り当てる → そのキーの枠に `半角` / `全角` の 2 行で出る（以前は `zenkaku_hankaku`）。`backspace` を割り当てた枠は `backspace` のまま
5. JIS で幅を変えて閉じ、開き直す → 同じ幅で開く。US TKL へ切り替える → US TKL の記録の幅（無ければ最小）になる。JIS へ戻す → JIS の記録の幅
6. 内蔵の US TKL と `US TKL（見本）` を切り替える → 配置が同じに見える。それぞれ別の幅を記録すると、切り替えでその幅になる
7. メニュー「設定」→「物理キー名を表示」を ON にして最小まで縮める → 主の文字と下の物理キー名が重ならない（はみ出しは受容）

### 正本反映（メイン）

- `features.md` §4.6「キーボードUI」: 縦横比の固定の「幅の下限 510」「新規に開くときは幅 510」→ 暫定 52 §5・§8 / 「窓の大きさ・位置・前面化は保存しない」→ 幅だけレイアウトごとに記録 / キーの文字の大きさ（§3）/ レイアウトの JSON の `key_display_names`（§4）と `label` の `\n` / 見本に `us_tkl.json`（§6）
- `data_schema.md` §5.4: `keyboard_window_widths`（§8）と config.json を作る契機の一覧
- `codebase_map.md`: `keyboard_key_text.py`・`keyboard_window_size.py` の下限と記録・レイアウトの見本・`key_display_names`
- 用語は `spec_detail/ui_terms.md` に従う
- 暫定 52 のヘッダを「凍結（YYYY-MM-DD・正本反映済）」へ
- `.claude_data/state/decisions_archive/69_keyboard_ui_key_labels.md`・`decisions.md` の索引
- `instructions/phase/current.md` の完了記載（次採番 phase 70 / 暫定 53 / decisions 70）・「直近のフェーズが扱った領域」
- `/refactor_check`（メトリクス収集は verifier）
- 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`

## 読むファイル

- `instructions/history/52_keyboard_ui_key_labels.md`（全体）
- `features.md` §4.6「キーボードUI」・`data_schema.md` §5.4・`codebase_map.md` のキーボードUIの節
- `.claude/rules/task_execution.md`「フェーズ完了時」

## 含まない

- コードの変更

## 確認

- 実機目視 1〜7 がユーザーから OK
- 正本の旧記述（510・「大きさは保存しない」）が残っていない（`grep -n "510" instructions/common/spec_detail/features.md` 等）
- 完了判定前レビュー 2 本の指摘の反映

## 完了条件

- 上記すべて・`/refactor_check` の判定を完了報告に記載
