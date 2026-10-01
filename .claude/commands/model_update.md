---
description: エージェントが使うモデルの ID・推論レベルを更新する（新バージョンへの追従 / 担当モデルの変更）。稼働側とモード変種を漏れなく揃える
---

エージェント定義が指定しているモデルを更新してください。対象は 2 種類:

- **バージョンの追従**: 同じ系統の新しい版が出た（例: Codex の Sol が `gpt-6-sol` → `gpt-6.1-sol`）。役割・推論レベルは変えない
- **担当モデルの変更**: どのエージェントにどのモデル・推論レベルを使うかを変える（運用判断。ユーザー確定が必要）

**系統ごとにバージョンは独立して進む**（例: Sol は 6.1、Luna は 6 のまま）。版番号の一括置換（`gpt-6` → `gpt-6.1` 等）は**しない**。
系統名を含む完全な ID 単位で置き換える。

## 手順

### 1. 対象の確定

- ユーザーの指示から「系統（例: Sol / Luna / Claude の sonnet・opus）・新しい ID・変える役割（バージョン追従のみか）」を整理する
- 担当モデルの変更（役割・推論レベルが変わる）なら、変更案を示してユーザー確定を得てから進む

### 2. 新しい ID の実在確認（推測で書かない）

- Codex: `~/.codex/config.toml` の `model` と、`~/.codex/models_cache.json` に現れる ID を確かめる
  （例: `grep -ohE "gpt-[0-9.]+-(sol|luna)" ~/.codex/models_cache.json | sort | uniq -c`）。見つからなければユーザーに確認する
- Claude 側エージェントの `model:` 欄は別名（`sonnet` / `opus` 等）で指定している。別名のままでよいなら変更不要

### 3. 指定箇所の洗い出し

次を `grep` で探す（旧 ID の完全一致で。系統名の呼び名〔「Sol medium」等〕は版を含まないので、役割を変えない限り触らない）:

- 稼働側: `.claude/agents/*.md`（`--model` / `--effort`・`spawn_agent` の `model` / `reasoning_effort`・frontmatter の `model:`）/ `.claude/rules/agent_selection.md`
- モード変種: `.claude_data/modes/agent_mode/switch_files/<各モード>/.claude/` 配下（存在するモードすべて。一覧は `modes.json`）
- **書き換えない**: 過去の記録（`.claude_data/state/decisions_archive/`・`instructions/phase/<過去フェーズ>/`・`instructions/history/`・`decisions.md` の過去節）。当時の事実なので残す

### 4. 編集（`.claude_data/modes/README.md` の変更手順に従う）

1. **先に `.claude_data/modes/README.md` を読む**（`.claude/` 配下を編集するときの必須手順）
2. 稼働側を直す
3. 同じ変更を、そのファイルを持つ**全モードの変種**へ反映する（モード固有の差異は保つ。非稼働モードの変種を直し忘れると、切り替えた瞬間に戻る）
4. 担当モデルの変更なら、`agent_selection.md` の表・各エージェントの `description` の記述も、全変種で揃える

### 5. 確認

- `grep` で旧 ID が稼働側・全モード変種から消えたこと（過去の記録を除く）と、他系統の ID を巻き込んでいないことを確かめる
- 稼働側と稼働中モードの変種の一致: `switch_agent_mode.py` は対話式のため、`diff --strip-trailing-cr` で管理対象を 1 つずつ比べる
  （例: `for f in $(cd <switch_files>/<mode> && find . -type f); do diff -q --strip-trailing-cr "$f" "<switch_files>/<mode>/$f"; done`）
- 編集したファイルについて、モード変種同士も比べる（モード固有の差異以外が一致すること）

### 6. 記録とコミット

- バージョンの追従のみ: コミットだけでよい（メッセージに系統・旧 ID → 新 ID を書く）
- 担当モデルの変更: `.claude_data/state/decisions.md` に判断（ユーザー確定日・理由）を 1 行残してからコミットする
- 完了報告: 直した箇所（ファイル数・行）/ 確認した ID の根拠 / 触らなかった箇所（他系統・過去の記録）を簡潔に書く

## 禁止事項

- 実在を確かめていない ID を書くこと
- 版番号だけの一括置換・他系統の ID の巻き込み
- 稼働側だけ直してモード変種を放置すること
- 過去の記録の書き換え
