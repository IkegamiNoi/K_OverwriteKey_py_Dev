# Codex CLI 運用手順書（詳細版）

> 本書は `.claude/rules/agent_selection.md`（要点版・毎セッション自動読込）から参照される手順書。
> 自動読込の対象外であり、**Codex（codex-implementer / codex-reviewer 等）のジョブが詰まった・
> cancel が効かない・ハングを検知したいときにのみ読む**。
> エージェントの使い分け自体は要点版が正。本書は「Codex CLI ランタイム（companion）の操作」に限る。

環境依存の実測メモを含む（Windows / Git Bash〔MSYS〕/ PowerShell 併用環境）。
根拠は 2026-07-24 の調査（phase 04 task_01 実装中の Codex ハング）。

---

## §0 前提

- Codex の実装ジョブは `codex-implementer` エージェントが
  `node "<plugin>/scripts/codex-companion.mjs" task --write ...` で投入する（companion = ランタイム本体）。
- companion スクリプトのパス:
  `C:\Users\ikega\.claude\plugins\cache\openai-codex\codex\<version>\scripts\codex-companion.mjs`
  （`<version>` は更新で変わる。`ls "C:\Users\ikega\.claude\plugins\cache\openai-codex\codex\"` で確認）。
- ジョブ状態の実体（ログ・記録）はここ:
  `C:\Users\ikega\.claude\plugins\data\codex-inline\state\<worktree名>-<hash>\`
  配下に `state.json`（全ジョブの索引）/ `jobs/<job-id>.json` と `.log` / `broker.json`。

### 【重要】worktree 内の Codex は `.venv` python を実行できない（構造的制約）

**Codex にテスト実行を依頼しない**。python 実行を伴う検証は `verifier` の責務
（`.claude/rules/agent_selection.md`）。理由:

- companion は `task --write` を **`sandbox: "workspace-write"`** で起動する
  （`scripts/codex-companion.mjs`）。書込・実行が許されるのは **cwd（= worktree）配下のみ**。
- `.venv` は**リポジトリルート**（worktree の外）にあるため、`..\..\..\.venv\Scripts\python.exe` の
  **起動だけが拒否**される。`pwsh` 経由でも同じ（実測: `Resolve-Path` / `Get-Command` は exit 0、
  python 実行のみ exit 1。phase 05 task_01・2026-07-27 のジョブログ）。
- → **worktree で作業する限り毎回再現する**。「Codex は `.venv` python を実行できる」という
  旧メモ（2026-07-24 記載）は worktree 外での実測であり、現行の運用形態には当てはまらない。
- 回避したい場合の選択肢は `--cwd <リポジトリルート>`（companion に `-C/--cwd` あり。worktree も
  `.venv` も同一ルート配下に入る）。ただし **Codex が main の作業ツリーを誤って編集する事故**の
  危険が上がるため既定にはしない（phase 02・03 で再発した罠）。採用するならユーザー判断で。

### 【重要】Codex の自己申告を信じない

- テスト実行を依頼しない運用でも、**「静的確認した」「差分は範囲内」等の申告は鵜呑みにしない**。
  最終的な pass/fail は必ず `verifier` が `.venv` で実測する。
  実例: 申告が届かないまま「19 件全 ERROR」だったケースを verifier 実行で検出できた。
  検証コマンドは `.claude/rules/python_rules.md`（`.venv` 必須）。

---

## §1 ジョブ状態の確認と「可視性」

```bash
node "<plugin>/scripts/codex-companion.mjs" status --all
```

出力の `Session runtime:` に注目する。

- **`shared session`**: broker エンドポイント（環境変数 `CODEX_COMPANION_APP_SERVER_ENDPOINT`
  または state ディレクトリの `broker.json`）が見えている文脈。**この文脈だけがジョブを掴める**。
- **`direct startup`（No jobs recorded yet / No job found）**: broker が見えていない。
  ジョブが存在しないのではなく、**その文脈から見えていないだけ**。

観測則:

- 実測では **Bash からは `shared session`・素の PowerShell からは `direct startup`** になった
  （PowerShell 文脈に broker エンドポイントが伝わっていなかったため）。ただしこれは相関であって
  原因ではない。**真実の情報源は `status` の表示**。Bash でも broker.json が消えれば `direct startup` になりうる。
- **cancel / status は「ジョブが見える文脈」からのみ有効**。`direct startup` なら、それは
  kill の問題ではなく可視性の問題 → §3 の cancel を試す前にまず可視性を確認する。

---

## §2 ハング検知（Monitor）

### 誤り: `wait` キーワードでは判定できない

ジョブログには `Starting collaboration tool: wait` → `Collaboration tool wait completed` の
ペアが**正常動作中も何度も出る**（実測で 21 回）。`wait` の出現自体は健全な挙動であり、
これを grep すると健全なジョブでも鳴りっぱなしになる。**検知条件に使ってはいけない**。

### 正しい信号: ログ停滞（staleness）

ハングの実体は「**ジョブ status が `running` のまま、ログが一定時間まったく進まない**」。
最後の `Starting ... wait` の後に `completed` が来ず、ログが沈黙したまま固まる。

Monitor は「沈黙」を検知する。`tail -f` の grep では沈黙は拾えないため、**ポーリングで
ログの最終行（またはサイズ・mtime）が N 分進んでいないかを見る**:

```bash
# ジョブログの停滞を検知する例（LOG は jobs/<job-id>.log の絶対パス）
prev=""; stall=0
while true; do
  cur=$(wc -c < "$LOG" 2>/dev/null || echo 0)
  if [ "$cur" = "$prev" ]; then stall=$((stall+1)); else stall=0; fi
  prev=$cur
  if [ "$stall" -ge 3 ]; then echo "STALLED: no log growth for ~3 min"; break; fi
  sleep 60
done
```

- 目安: **3 分（60s × 3 回）ログが伸びなければハング**とみなす（実作業なら通常この間に進捗が出る）。
- 検知したら §3 の cancel（**生きているうちに速やかに**）→ 実装先を implementer / メインへ切替。
- Codex を本格投入するタスク（分割本体など）では、投入と同時にこの Monitor をセットで仕掛ける。

---

## §3 cancel（詰まったジョブを止める）

### まず可視性を確認（§1）

`status` が `shared session` を示すこと。`direct startup` なら cancel は「No job found」で
効かない → 可視性の問題として扱う（別文脈から実行するか、§4 の state 手修復へ）。

### ユーザーが止める場合: `/codex:cancel`（推奨・最も確実）

`/codex:cancel <job-id>` はプラグイン文脈（PowerShell 起動の MCP サーバ）で動く。この文脈は
broker を持ち（ジョブが見える）、`SHELL` を持たない（taskkill が cmd.exe 経由で正常）。
**生きているジョブなら確実に止まる**。

### メイン/エージェントが Bash から止める場合: `MSYS_NO_PATHCONV=1` を前置き

companion の kill は `taskkill /PID <pid> /T /F` を `spawnSync(..., {shell: process.env.SHELL || true})`
で実行する（`scripts/lib/process.mjs`）。**Git Bash は `SHELL` をセットするため taskkill が bash 経由になり、
MSYS のパス変換で `/PID` が `C:/Program Files/Git/PID` に化けて失敗する**。

→ **その一発だけ**環境変数を前置きして回避する（グローバル設定は禁止。他コマンドのパス変換を壊す）:

```bash
MSYS_NO_PATHCONV=1 node "<plugin>/scripts/codex-companion.mjs" cancel <job-id>
# MSYS2_ARG_CONV_EXCL='*' でも可
```

`MSYS_NO_PATHCONV=1` / `MSYS2_ARG_CONV_EXCL='*'` / cmd.exe 経由（SHELL 無し）のいずれでも
taskkill は正常動作することを実測で確認済み（素の Bash 〔SHELL 有り〕だけが壊れる）。

---

## §4 state 手修復（PID 消滅ジョブの居座り）

**cancel が効かない最悪ケース**: ジョブの worker プロセスが既に死んでいる（例: codex.exe を再起動した）
場合、`taskkill` は「対象なし」を返し、**companion は記録を `running` のまま残す**。
`shared session` ランタイムでは、この居座り 1 件が後続タスクを `phase: starting` で**全て詰まらせる**
（codex.exe を再起動しても解消しない。記録は state ファイル側にあるため）。

手順（**必ずバックアップを取ってから**）:

1. `state.json` と該当 `jobs/<job-id>.json` を別ディレクトリへコピー（バックアップ）。
2. 両ファイルの当該ジョブの `"status": "running"` を `"cancelled"` に、`"phase"` も `"cancelled"` に書き換え、
   `"endedAt"` を補う。`.log` は**保全**（消さない）。
3. `status --all` で Active jobs が空になったことを確認。

- PID がまだ生きているか確認: PowerShell `Get-Process -Id <pid>`（無ければ消滅済み）。
- **予防が最優先**: §2 の Monitor で早期検知し、**PID が生きているうちに §3 で cancel** すれば
  ここには来ない。codex.exe を安易に再起動しない（PID を失うと手修復しか手が残らない）。

---

## §5 関連

- `.claude/rules/agent_selection.md` — エージェントの使い分け（本書はそこから参照される運用詳細）。
- `.claude/rules/python_rules.md` — `.venv` python の実行パス（verifier 検証もこれ）。
- 調査の一次記録: phase 04 task_01 実装中（2026-07-24）。詳細判断は当該フェーズの decisions を参照。
