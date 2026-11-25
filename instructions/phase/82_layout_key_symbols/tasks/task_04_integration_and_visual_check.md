# task_04_integration_and_visual_check

## 目的

task_01〜03 を通しで確かめる。テストスイート全体・smoke・統合レビュー（複数タスクを跨ぐ差分）と、Windows の実機目視（ユーザー）で、暫定 62 §8 の受け入れ条件を満たすことを確認する。
**コードの変更は原則しない**（統合レビューや目視で問題が出たら、採否をユーザーに確かめてから枝番のタスクで直す）。

## 対象範囲（確認のみ）

### 統合確認（verifier）

- `compileall`・`unittest discover -s tests`・`unittest discover -s tests_ui`・`-m tests.smoke_app`。
- task_02 で出た `tests_ui.test_minimize_grab_custody` の偶発の失敗（decisions の task_02 の項）を、全体の実行の結果と、同モジュールの単独の再実行で確かめ直す。

### 統合レビュー

- `deep-reviewer`（Claude 側）と `codex-reviewer`（Codex 側）。対象 = phase 82 の差分全体（`7dc202ff..HEAD` のうち keyseq・tests・tests_ui・config の見本）。観点 = 暫定 62 §3〜§7 との整合・タスク間のつなぎ目（読込 → 表の受け渡し → 描き直し → 警告）・既存の表示を変えていないか。

### Windows の実機目視（ユーザー・暫定 62 §8）

開発時の構成はリポジトリの `config/` を使うので、見本の jis.json の変更がそのまま効く（暫定 62 §1）。

1. レイアウトに見本の **JIS** を選ぶ。キー置換の置換先・トリガー・key_hold に `backslash`・`\`・`ro` を使った行があれば（無ければ作る）、トリガー一覧・出力シーケンス一覧（詳細表示・簡易表示）・呼び出し先の表示枠・キーボードUIのキー置換の枠に **`＼`（全角）** で出て、`yen` は `¥` のまま（§8-1・§8-10）。
2. レイアウトを **US TKL** に切り替えると、トリガー一覧と出力シーケンス一覧もすぐ `\`（フォントにより ¥ に見える）に戻る。JIS に戻すと `＼` に戻る（§8-2・§8-7）。
3. 外部レイアウトの JSON（jis.json のコピー等）の `key_symbols` を不正（例: `"key_symbols": "x"`）にして追加すると、「追加しました」と警告の両方が出る。そのレイアウトを選ぶと、ステータスバー中央に警告が出たまま残り、ほかの一時メッセージ（例: フォントの拡大縮小）が出て消えると警告に戻る。レイアウト自体は選べ、キーの受信・送信は普段どおり（§8-5・§8-6）。
4. 3 の JSON を直してドロップダウンで選び直すと、警告が消える（§8-6）。
5. キー置換で `ro` / `backslash` を送ったときの出る文字・保存されるキー名は今までと変わらない（§8-9）。

## 読むファイル

- 暫定 62: `instructions/history/62_layout_key_symbols.md` §8
- `.claude_data/state/decisions.md` の phase 82 の節（task_02 の偶発の失敗）

## 含まない

- 正本の更新・暫定 62 の凍結・decisions_archive・current.md の完了記載・INDEX_done・refactor_check（task_05）
- macOS の実機目視（jis_mac.json には書かない・暫定 62 §2）

## 確認

- verifier: compileall clean / tests 全 pass / tests_ui 全 pass（偶発の失敗は単独の再実行の結果を併記して切り分ける）/ smoke pass
- 統合レビュー: deep-reviewer と codex-reviewer の結果（指摘の採否はユーザー）
- 実機目視 1〜5 の結果（ユーザー）

## 完了条件

- 上記確認 pass・統合レビューの指摘の採否が決まっている・実機目視 OK・**reviewer 採用**（本タスクで直した差分がある場合）。
