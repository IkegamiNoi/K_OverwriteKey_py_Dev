# template_pull 同期状態

`/template_pull`（`.claude/commands/template_pull.md`）が参照・更新するマーカー。
方向は **template → このプロジェクト**（逆同期）。

- `last_pulled` = template 側で取り込み判定済みの最終コミット。次回はここから `HEAD` までが対象
- 空の場合は初回モード（許可リストの全比較。コマンドの手順 2b）で扱う

| source | path | last_pulled | date |
|---|---|---|---|
| 00_claude_template | D:/Claude/doc/00_claude_template | 7791fa7 | 2026-09-10 |

---

## ■ ファイルの対応関係（名前が同じでも対応先が違うもの）

分類（手順 3）で突き合わせる相手を間違えないための対応表。

| このプロジェクト | template | 備考 |
|---|---|---|
| `.claude/rules/implementation.md` | `.claude/rules/implementation_py.md` | `/init_project` で python 版を採用し tkinter へ具体化。template の `implementation.md` は flutter 版なので**対応先ではない** |
| （無し） | `.claude/rules/flutter_rules.md` | 他言語向け。取り込まない |
| （無し） | `.claude/commands/template_sync.md` / `.claude/template_sync_state.md` | template 専用（`/init_project` で削除される側） |

## ■ 除外メモ

恒常的に「取込不要」。**節単位で切る**（ファイル単位で除外すると、template 側の他節の改訂を
取りこぼす）。

- `.claude/rules/python_rules.md` の「python 実行コマンド」節 — template は `EDIT REQUIRED` 維持、
  こちらは `.venv` の実パスを記入済み。他節は比較対象
- `.claude/rules/file_organization_rules.md` /
  `instructions/common/rules_detail/file_organization_rules.md` の
  「本リポジトリへの適用注記」節 — こちらは Python / オニオン構成へ具体化済み
  （実測: 差分はこの節のみ。基本原則・昇格ルール等の他節は完全一致＝比較対象）
- `.claude/rules/implementation.md` — 全面改訂済み（tkinter / keyboard 向け）。ファイル単位で除外
- `instructions/common/app_overview.md` / `codebase_map.md` / `spec_detail/` — プロジェクト固有
- `AGENTS.md` — こちら固有の入口ドキュメント（template に相当物なし）

## ■ template と意図的に差分にした箇所

こちらの内容が正。template 側の `/template_sync`（順方向）では候補に出るが、
template を直すか差分のままにするかは別途判断する。

- モード切替先の表記「他モードへの切り替えは」 — `.claude/rules/agent_selection.md`（稼働側）と
  `.claude_data/modes/agent_mode/switch_files/{codex,claude_only}/.claude/rules/agent_selection.md`
  の計 3 ファイル（template は 2 モード前提の「非 Codex 環境向け構成へ」「Codex 併用構成へ」のまま）
- `CLAUDE.md` のモード列挙 → 「登録モードで切り替える」（`modes.json` を正とする）。
  および調査エージェント記述 →〔既定はモードごとに同ファイルが定義〕
  （template は〔Codex 併用時は codex-explorer / Claude のみは Explore〕）
- `.claude_data/modes/README.md` — こちらで新設（template はこの知識をルート `README.md` に置いている）
- `.claude_data/modes/save_mode/switch_files/*.json` の SessionStart command
  → git 実測ヘッダ（branch / worktree_root）付き
- **Codex 使用量の削減（2026-09-17）**: `.claude/agents/codex-implementer.md`（稼働側 + `switch_files/{codex,codex_medium}`）の
  転送文 = 規約は `implementation` / `python_rules` / `anti_patterns` の 3 つのみ・読む範囲を指定 /
  `.claude/commands/task_new.md` の「読むファイル」節（7 節構成）/ `.claude/rules/implementation.md` の実装前手順 1
  （codebase_map は対象節のみ。ファイル単位除外済みだが記録として残す）
- `.claude/commands/template_pull.md` / 本ファイル — こちらで新設（逆同期用）。
  順方向で template へ取り込むかは template 側の判断

**意図的差分ではないもの**: `.claude/rules/output_style.md:42` と
`.claude/rules/task_execution.md:16` の調査エージェント記述は、**template 側が既に中立化済み**
で、こちらの `1a80dfd` は差分ではなく追随（実差は語尾 1 語）。次回は「既反映」で扱う。

## ■ 履歴メモ

- 2026-09-10: `aa2f827^..7791fa7`（3 コミット）を取込。①モード切替機構を
  `instructions/{agent_mode,save_mode}/` → `.claude_data/modes/` へ移動 ②`codex_medium`
  モード追加 ③`.gitignore` の一部（モード backup 2 行のみの部分取込）。
  `codex_medium` の `agent_selection.md` は template の汎用版ではなくこちらの `codex` 変種を
  ベースに 3 箇所差替。`deep-reviewer` の指摘 F1〜F12 のうち F1/F2/F3/F4/F5/F6/F8/F11 を反映、
  F10（`modes.json` の並びが id 1,3,2）は機能影響なしで対応不要、F12（配置の代替案）は参考のみ。
  **未実施: F7**（`.claude_data/state/decisions.md` への判断履歴記録）、
  **F9**（`codex_medium` 適用前の `Explore` 可用性確認）、
  `.claude/rules/output_style.md:41-42` の `claude_only` モードで食い違う記述（既存のズレ）
- 2026-09-10: 本コマンドとマーカーを新設。`deep-reviewer` の指摘のうち
  `.gitignore` の許可リスト漏れ・pathspec 併用時に `-M` が効かない罠・grep 対象からの
  `.claude_data/modes/` 漏れ・初回モードの手順欠落・確認ゲートの出力形式などを反映
