# モード切替機構（`.claude_data/modes/`）

`.claude/` 配下の一部のファイルを、モードごとに入れ替えるための仕組み。
**`.claude/` 配下または `CLAUDE.md` を編集する前に、本ファイルを読むこと。**

- `agent_mode/` — エージェント構成の切替（`switch_agent_mode.py`）。複数ファイルを一括反映
- `save_mode/` — state 保存フックの切替（`switch_save_mode.py`）。`.claude/settings.json` 1 枚を差し替え

`switch_files/` 配下は生成物ではなく、**稼働ファイルのマスターコピー（手で維持する正）**。
そのため `.claude_data/` を丸ごと Git 除外してはならない（`state/` は追跡方針、`modes/` は正本）。
除外していいのは `*/backup/`（適用前の退避）と `__pycache__/` だけ。

---

## ■ モード管理対象のパス

**この一覧に載っているファイルは、編集すると全変種へ追随させる必要がある。**
一覧は `switch_files/<mode>/` 配下の和集合（`managed_relpaths`）で、
モードフォルダに無いパスは**そのモードの適用時に削除される**。

| パス | 置かれているモード | モード固有の差異 |
|---|---|---|
| `.claude/rules/agent_selection.md` | codex / codex_medium / claude_only | **あり（3 変種すべて相異）** |
| `.claude/agents/implementer.md` | codex / codex_medium / claude_only | **あり**（claude_only のみ相異） |
| `.claude/agents/codex-implementer.md` | codex / codex_medium | なし（claude_only 適用時は削除） |
| `.claude/agents/codex-reviewer.md` | codex / codex_medium | なし（同上） |
| `.claude/agents/codex-adversarial-reviewer.md` | codex / codex_medium | なし（同上） |
| `.claude/agents/codex-explorer.md` | codex のみ | なし（他 2 モード適用時は削除） |
| `.claude/settings.json` | save_mode の登録 5 種 | あり（有効な hook の組合せ） |

管理対象**でない**もの（モードに関係なく共通）: `.claude/agents/{reviewer,deep-reviewer,verifier}.md` /
`.claude/commands/` / `agent_selection.md` 以外の `.claude/rules/` / `CLAUDE.md`。

---

## ■ 編集時の注意

### 1. 管理対象を編集したら、全変種へ追随させる

稼働側（`.claude/`）を直したら、対応モードの変種だけでなく**他モードの変種にも反映する**。
モード固有の差異は保ったまま、それ以外を揃える。

### 2. `check` は非稼働モードのズレを検知できない

`check` が比較するのは **「稼働中の `.claude/`」↔「指定モードのフォルダ」の 1 組だけ**。
モードフォルダ同士は比較されないため、非稼働モードの変種が古くなっても
`check` は「一致」と言い続け、**切り替えた瞬間に改訂が巻き戻る**。
手順 1 を守る以外に検知手段はない（実例: `codex_medium` 追加時、既存 2 変種の
「切替先」表記が 2 モード前提のまま残った）。

### 3. 参照する側は「どのモードでも真」に書く

管理対象を参照する文書（`CLAUDE.md` / 他の `.claude/rules/`）は**モード管理外**なので、
モードを切り替えても書き換わらない。したがって:

- **具体エージェント名を書かず、`agent_selection.md` の既定へ委ねる**。
  「調査 = 調査エージェント（既定は `agent_selection.md`）」のように書く。
  「調査 = `codex-explorer`」と書くと、`codex_medium` / `claude_only` では
  **削除済みのエージェントを指す**（実例: 過去に `CLAUDE.md` / `output_style.md` /
  `task_execution.md` の 3 箇所がこの形だった）
- 登録モードの列挙もしない（モードを増やすたびに直す形になる）。`modes.json` を正とする
- **中立に書けない場合は、そのファイル自体をモード管理へ昇格させる**
  （`switch_files/` の全変種へコピーする）。ただし変種の数だけ維持コストと
  注意 2 の漏れリスクが増えるため、**まず中立に書けないかを検討してからにする**

---

## ■ 変更手順

1. 稼働側（`.claude/`）を編集する
2. 対応モードの変種へ反映する
3. 他モードの変種へ、モード固有の差異以外を追随させる
4. `check`（稼働側との一致）と `diff <id>`（各モードとの差分）で確認する
5. 参照する側の文書を触った場合は、注意 3 に反していないか確認する

適用（`apply <id>`）は上書き前に管理対象を退避する
（agent_mode は `agent_mode/backup/<timestamp>/`、save_mode は `save_mode/backup/settings_<timestamp>.json`）。
稼働側にモード管理外の変更が入っていると `apply` で失われる（backup から復旧可能）。
