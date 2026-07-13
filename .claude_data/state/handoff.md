# handoff.md

過去の会話履歴は参照しないでください。
このファイルと `.claude_data/state/session.md` を起点に作業を再開してください。

## 再開手順
1. `.claude_data/state/session.md` を読む（最重要・最新状態）
2. `.claude_data/state/decisions.md` があれば読む（過去の判断履歴）
3. CLAUDE.md → `instructions/phase/current.md` → `.claude/rules/` の順に必要分を読む
4. session.md.next_action から作業を再開する

## 最初に確認するコマンド
> プロジェクトに応じて静的解析・テストコマンドを記載
> この文章があるということは新規なので、プロジェクトに合わせて修正を行う
> 例:
> ```bash
> # Flutter プロジェクト
> flutter analyze 2>&1 | tail -5
> flutter test 2>&1 | tail -3
>
> # Node プロジェクト
> npm run lint
> npm test
>
> # Rust プロジェクト
> cargo check
> cargo test
> ```

session.md.verified の値と一致することを確認してから次のアクションへ進む。

## 注意事項
- 会話履歴の再現を試みない（トークン浪費の最大要因）
- session.md.last_action.result_files は現状の作業対象を示す
- 想定外の差分を見つけたら、`.claude/rules/anti_patterns.md` に従う

## 現在の作業の 1 行サマリ
> session.md.current.focus を参照
