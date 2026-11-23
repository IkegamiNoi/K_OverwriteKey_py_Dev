# phase.md

## フェーズ名

アクションの hotkey の保存時の検査と正規化（action_hotkey_save_validation）

## フェーズの目的

出力シーケンスの hotkey アクションを、OK（保存）の時点でプリセット編集と同じ `validate_hotkey`（構文の検査 + 各キーを `validate_key_name` で検査）に通す。不正な値は保存せずにエラーを出し、通った値は正規化して保存する。**変更は presentation（`ActionDialog.on_ok`）だけにとどめ、検証には既存の application の `HotkeyService` を使う。JSON スキーマは変えない（保存値が正規化された形になるだけ）。**

- 起票元: [idea_03](../../backlog/idea_03_action_hotkey_save_normalization.md)（2026-11-15 追記の「保存時もホワイトリスト方式で検査する」を含む）。
- 主入力（暫定仕様）: なし（直接改訂モード）。正本 = `instructions/common/spec_detail/key_input.md` §7.7「キーの送信」（L232）・§7.9「macOS」の「他方の OS のキー名」（L346）。
- モード: **直接改訂モード**。番号対応: phase 78 / 暫定なし / decisions 78。

## 確定（ユーザー 2026-11-23）

- 保存時の扱い = **検査して、不正なら拒否・通れば正規化した値を保存**する（プリセット編集・key_hold の OK と揃える）。選んでいるレイアウトと OS の backend で解決できないキー名も保存時に弾く（これまで実行時エラーになっていたものが早く出るだけ）。
- 既存の `sequences/*.json` に残る正規化前の値（例 `"Ctrl+ A"`）は**移行しない**。実行時の正規化で今までどおり動き、そのアクションを編集して OK を押せば正規化される。読み込み時の正規化は入れない。
- 仕様変更は直接改訂モードで進める（正本を先に改訂してから実装する）。

## スコープ

### 含む

- 正本 `key_input.md` §7.7・§7.9 の改訂（「hotkey のアクションは保存時にキー名を検査しない」と、その例外である「他方の OS の修飾キーの名前だけは拒否する」の書き換え）
- `ActionDialog.on_ok` の hotkey の保存処理（`validate_hotkey` を通し、エラーなら表示して保存しない・正規化値を保存）。他方の OS の修飾キーの拒否（phase 75）は今の挙動とメッセージのまま残す
- 上の保存処理のテスト（tests_ui の action_dialog 系）
- `codebase_map.md` の更新（L912 の「hotkey の通常の未知名は保存時には検査しない」）

### 含まない（後送り）

- 既存ファイルの移行・読み込み時の正規化
- 実行時の正規化・検証（`action_executor._execute_hotkey`）の変更（既存ファイルのために残す）
- hotkey の文法・`validate_hotkey` / `HotkeyService` 自体の変更
- text など hotkey 以外の種類の保存処理・単キー検証の統一（暫定仕様 01 §7 の別ネタ）
- プリセット編集の変更

## このフェーズで読むファイル

1. `instructions/common/spec_detail/key_input.md` §7.7（L204〜・特に L232）・§7.9（L307〜・特に L346）
2. `keyseq/presentation/dialogs/action_dialog.py:253-265`（hotkey / text の `on_ok`）・`:320-330`（key_hold の検査。比較用）
3. `keyseq/application/hotkey_service.py`・`keyseq/presentation/app.py:861-866`（`validate_hotkey`）
4. `keyseq/presentation/dialogs/preset_manager.py:315-360`（プリセット側の保存。揃える相手）
5. `tests_ui/test_action_dialog_*.py` のうち hotkey の OK を扱うもの（どれに足すかはタスクで決める）
6. `instructions/common/codebase_map.md:912`

## タスク

- task_01: **完了（2026-11-23・メイン〔文書〕・reviewer 採用）** 正本 `key_input.md` §7.7・§7.9 の改訂（文言をユーザーに提示して確定）。L232 と、それを例外として参照する L346 の言い回しを同時に直す
- task_02: **完了（2026-11-23・codex-implementer〔Luna high〕・reviewer 修正して採用 → test_action_dialog_labels の fake root に validate_hotkey を追加〔メイン〕・verifier pass）** `ActionDialog.on_ok` の hotkey の保存時の検査と正規化・テスト。他方の OS の修飾キーの検査（`accepts_key_name`）は `validate_hotkey` より前に置き、メッセージを変えない
- task_03a: **完了（2026-11-23・codex-implementer〔Luna high〕+ メイン 1 語修正・reviewer 採用・verifier pass）** 完了判定前レビュー（deep 2・3・4）採用分のテスト補強（他方 OS の検査が先・既存行の編集で正規化・エラー文の表示）
- task_03: **完了（2026-11-23・統合確認 pass〔tests 2278 / tests_ui 1319 / smoke〕・実機目視 OK・完了判定前レビュー deep-reviewer + codex-adversarial-reviewer の採否確定・refactor_check 不要）** 統合確認・実機目視・記録（`codebase_map.md`〔L912 の「保存時には検査しない」と `ActionDialog.on_ok` の呼び出し元の記述〕・`decisions_archive/78`・`current.md`・idea_03 の INDEX_done への移動・`/refactor_check`）

## レビュー方針

共通観点（`.claude/rules/review.md`）に加え、次を確認する。

- 変更が hotkey の保存だけに収まっていること（text・他の種類・プリセット・実行時の経路が変わっていない）
- 他方の OS の修飾キーの拒否が phase 75 のまま効いていること（メッセージを含む）
- 保存値が `validate_hotkey` の正規化値と一致すること・エラー時は `_dialog_result` が設定されず窓が閉じないこと
