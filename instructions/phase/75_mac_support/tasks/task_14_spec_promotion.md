# task_14_spec_promotion

## 目的

phase 75（macOS 対応）の最終タスク。暫定 57（v0.25）の確定内容を正本 `instructions/common/spec_detail/` へ昇格させ、暫定 57 を凍結する。あわせてフェーズ完了時のチェックリスト（`.claude/rules/task_execution.md`「フェーズ完了時」）を実施する。

- 文書作業が主（メインが行う・`agent_selection.md`「フェーズ末の正本反映タスク」）。コードの変更はヘルプ本文の 1 文（下の §ヘルプ）だけ。domain / application / presentation のロジック・JSON スキーマは変えない。
- 正本への転記はユーザー承認済みの内容（暫定 57 の各版）に限る。暫定 57 に無い仕様を正本で新たに決めない。

## 対象範囲

### 正本の昇格（暫定 57 §11 の列挙に従う）

- `features.md`
  - §4.6「割り当て禁止のキー」: 判定するキー名に `command` / `left command` / `right command`（v0.11）と `fn`（v0.12）を足し、文言を両 OS 共通の形（v0.20・task_11d の Windowsキー・Commandキー・Caps Lock・AltGr・fn）にする。
  - macOS で無効・挙動の違う機能（443 行付近・暫定 57 §5.4 の表。メニューの処理の遅延〔v0.25〕・クリック透過の半透明〔v0.16〕・最前面とモーダル〔v0.18〕・メッセージの窓〔v0.19〕を含む）。
  - 本体のライセンスを「GNU GPL v3 以降」に（v0.23）・第三者ライセンスの一覧（1056 行付近）を `third_party.json` の今の行と英語のライセンス名に揃え、OS 列（v0.22・task_13a）を書く。
  - 修飾キーの別名の列挙（task_09f）。
  - 設定の保存先（Mac = `~/Library/Application Support/keyseq`・task_12 / 13b）。
  - サンプルの構成の説明があれば、テンキーの置換先 `num add` / `num multiply` / `num divide`（task_13b）に追従する（無ければ不要）。
- `key_input.md`: macOS のフック（CGEventTap・§5.1 / §5.1.1 のディスパッチャの契約）・キーの識別（§5.3・§5.3.1 の記号キーの表・§5.3.4 の `command` / `option`・Shift の要る文字の表と別名〔decisions 75 task_09 の reviewer 参考 1〕）・権限（§5.2）・IME（§8 Q4 の TIS 切替）。「Windows 以外」前提の 145・165・253・256・264 行付近を両 OS の記述に直す。hotkey の保存時の検査の例外（task_09f）。
- `architecture.md`: OS 境界（§3・`os_backend/` の配置と Protocol）・`bundled_root` / `app_data_root`（§6.1・v0.21）。
- `data_schema.md`（INDEX と子ファイル）: §8 Q3 の扱い・Mac 用のレイアウトの見本（§5.3.2）・既定プリセットのプロファイルの注入。
- `ui_terms.md`: 権限の案内の用語（task_10）・Mac のキー名の表記。
- `nonfunctional.md` / `design.md`: 対応 OS・ビルド（§6.2・§6.3・§10 のスコープ外）に触れている節があれば追従する（無ければ変えない）。

### 凍結

- `instructions/history/57_mac_support.md` の冒頭の状態行（今は「未凍結・v0.15」）を「凍結・v0.25」に書き換え、昇格先の一覧と日付を添える。本文の条項は変えない。
- `instructions/phase/current.md` の暫定仕様の一覧（187 行付近「57 = macOS 対応〔v0.5・未凍結〕」）を凍結済みに直す。

### 地図・運用文書

- `instructions/common/codebase_map.md`（`os_backend/`・`input_gateway.py`・`message_box.py`・`MenuCommandQueue`・`packaging/` 等の phase 75 で増えた構成）・`app_overview.md`（対応 OS）。
- `.claude/rules/python_rules.md` の実行コマンドに Mac の `.venv`（`../../../.venv/bin/python`）を足す。**編集前に `.claude_data/modes/README.md` を読む**（モードで入れ替わるファイルの制約）。
- `README.md`（リポジトリ直下）: 動作環境に対応 OS（Windows / macOS〔Apple Silicon〕）・依存の入れ方（`requirements.txt`）・Mac の権限（アクセシビリティ）・配布ビルドは `packaging/README.md` を参照、の 4 点。

### ヘルプ（task_11d の L1）

- `help_ja.json:590` / `help_en.json:331` の「Ctrl・Alt・Windowsキーを押している間は素通し」を、Mac のキー（Control・Option・Command）も含む両 OS 共通の文言にする。文言は `ui_terms.md` に従い、**ユーザーに案を出して確定してから**直す。
- 同じ機会に `help_ja.json:932`（左右の Shift・Ctrl・Alt は別のキー）が Mac のキーの説明として足りるかを見る。足りなければ同じく案を出す（足りていれば触らない）。

### フェーズ完了の記録

- `.claude_data/state/decisions_archive/75_mac_support.md` を作り、`decisions.md` の phase 75 の判断を集約する。`decisions.md` はアーカイブ索引に 1 行を足し、本文から phase 75 の節を外す（既存のフェーズと同じ形）。
- `instructions/phase/current.md`: phase 75 を完了に・アクティブなフェーズ = なし・次採番（phase 76 / 暫定 58 / decisions 76 / 提案書 28 / idea 66。冒頭 11 行目付近の「idea 62」も直す）。
- `instructions/phase/75_mac_support/phase.md`: task_14 の行とフェーズの状態を完了に。
- 起票元 idea: なし（ユーザー要望）。`instructions/backlog/` の更新は不要。
- `/refactor_check`（メトリクス収集は verifier・判定と提案書の起票はメイン）。

## 読むファイル

1. 本書・`instructions/history/57_mac_support.md`（全体。昇格の元）
2. 昇格先の `spec_detail/` の各ファイルの該当節（上の行番号付近・`grep` で節を探す）
3. `.claude_data/state/decisions.md` の phase 75 の節・`decisions_archive/74_key_symbol_display.md`（アーカイブの形の手本）
4. `.claude/rules/task_execution.md`「フェーズ完了時」・`.claude/commands/refactor_check.md`
5. `.claude_data/modes/README.md`（python_rules.md の編集前）

## 含まない

- 暫定 57 §10 のスコープ外（公証・インストーラ・Intel Mac・Linux・CI・OS 間の設定共有）。
- 検討段階の idea（idea_45・59〜65。C ライブラリの行は idea_65）・2 枚目のモニタの目視と中クリック（保留・ユーザー判断）。
- `/refactor_check` が「要」と判定した場合の実施（提案書の起票まで。実施はユーザー承認後の別フェーズ）。
- `__version__` の変更・タグ・push・main へのマージ（ユーザー）。

## 確認

1. 暫定 57 §11 の列挙と §9 の受け入れ条件 1〜15 について、昇格先（`spec_detail/` のファイル名と節）を対応表にして完了報告に載せる（漏れが無いこと）。
2. `grep -rn "Windows 以外\|Windows のみ\|Windows 専用\|win32\|Win32\|keyboard ライブラリ" instructions/common/` の各ヒットを見て、Mac 対応後に偽になった記述が残っていない（Windows の backend の説明として正しいものは残す）。
3. ヘルプの文言を直した後: verifier で compileall clean / `tests` 全件 / `tests_ui/test_help_window.py` / smoke（Windows）。
4. フェーズ完了判定のレビュー: `deep-reviewer`（本タスクの差分 + 正本整合・昇格漏れ・凍結）と `codex-adversarial-reviewer`（フェーズ全体の差分）を併用する（phase.md「レビュー方針」）。
5. `/refactor_check` の判定結果を完了報告に書く。

## 完了条件

- 確認 1〜5 を満たし、**deep-reviewer 採用**（本タスクの必須レビューはフェーズ完了判定の deep-reviewer で兼ねる。`agent_selection.md` のとおり reviewer は重ねない。Codex の敵対的レビューの指摘の採否はユーザー）。
- 実機目視: ヘルプの文言の変更だけ（Windows でヘルプのその節を開いて確認・ユーザー）。Mac の目視は不要（文言の表示の仕組みは変わらない）。
