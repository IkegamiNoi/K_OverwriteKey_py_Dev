# phase.md

## フェーズ名

macOS 対応（mac_support）

## フェーズの目的

Windows 専用の keyseq を macOS でも同様に動かし、OS ごとの実装を切り分けて、Windows / macOS それぞれでアプリとしてビルドできるようにする。
**OS 依存は `keyseq/infrastructure/os_backend/` に閉じ、domain・application とレイアウト JSON は変えない。JSON スキーマの変更なし（既定プリセットはプロファイルの注入で対応）。**

- 起票元: ユーザー要望（2026-11-09）。
- 主入力（暫定仕様）: [57_mac_support.md](../../history/57_mac_support.md)（v0.5・ユーザー確定済）
- モード: **暫定仕様先行モード**。番号対応: phase 75 / 暫定 57 / decisions 75。

## 確定（ユーザー 2026-11-09）

暫定 57 の §2 と §8 Q0〜Q8 が正。要点:

- 4 段階（OS 境界 → Mac で起動 → Mac の入力 → ビルド）。
- macOS の入力は `pyobjc` の CGEventTap。Windows の入力は `keyboard` のまま。
- PyInstaller の onedir・アドホック署名・Apple Silicon のみ・Python 3.13（python.org 版）。
- 段階 ① はタスクごとに Windows 実機で標準検証 4 種を行う。Windows 機を用意できない間は、選択点の導入のみに縮める。

## スコープ

### 含む

暫定 57 の §3〜§7。

### 含まない（後送り）

暫定 57 の §10（公証・配布用インストーラ・Intel Mac・Linux・CI・OS 間の設定共有）。

## このフェーズで読むファイル

1. `instructions/history/57_mac_support.md`（主入力）
2. `instructions/common/codebase_map.md` の該当節
3. `instructions/common/spec_detail/key_input.md` §7.1・§7.4・§7.7、`features.md` の該当節
4. `keyseq/infrastructure/input_gateway.py`、`win32_window.py`、`ime_control.py`、`own_ime_status.py`、`app_relaunch.py`、`config_paths.py`
5. `keyseq/application/input_router.py`、`keyseq/presentation/controllers/hook_controller.py`、`key_capture_hook.py`、`tk_keys.py`
6. `keyseq/presentation/app.py`（§6.1 の設定ルートと `win32_window` の参照箇所）

## タスク

タスク定義は着手順に `tasks/` へ起票する。

**段階 ①: OS 境界（各タスクで Windows の標準検証 4 種をゲートにする）**

Windows 機を用意できない間は（Q0）、task_01〜04 の「移動」「分解」を行わず、import の遅延と選択点の導入だけを行う。物理移動は Windows 機を用意できたときに行う。

- task_01: `os_backend` の骨格・契約・import 境界の AST テスト・公開シンボルと Protocol の一致テスト、IME の移動
- task_02: `win32_window` の移動と `WindowBackend` / `AppIdentity`
- task_03: `input_gateway` の `KeyboardBackend` / `MouseBackend` への分解
- task_04: presentation の切替（`modal.py`・`tk_keys.py` の `TkKeyTranslator`・`action_dialog.py`・ディスパッチャの注入）

**段階 ②: macOS で起動**

- task_05: Mac の `.venv`（Python 3.13）・依存の環境マーカー・macOS スタブ・Tk の差分
- task_06: probe（tap・修飾キー・権限・aqua の Tk・スレッド条件・Dock のアイコン・JIS / US の記号キーの対応表）と暫定 57 の改訂
- task_07: 既定プリセットのプロファイル注入（Q2）、macOS のテストの基準線の記録（§7）

**段階 ③: macOS の入力（開始条件 = task_06 の対応表の確定）**

- task_08: CGEventTap のフック・修飾キー・配送の滞留の規則（§5.1）
- task_09: キーの識別と送信の解決順、`Command` / `Option` の表示（§5.3）、Command の割り当て禁止（Q5）、`TkKeyTranslator` の修飾 keysym（task_04 から先送り）
- task_10: 権限の案内（§5.2）
- task_11: §5.4 の残りの機能と無効化の UI

**段階 ④: ビルド**

- task_12: `app_data_root` への統一と同梱物のパス、再起動（§6.1・§6.2）
- task_13: `packaging/` と Windows / macOS のビルド、ビルド後の実機確認（各 OS で保存した設定の読み込みを含む）

**最終**

- task_14: 正本反映（暫定 57 の昇格・凍結、`decisions_archive/75_mac_support.md`、`current.md` の完了記載、運用文書、`/refactor_check`）

## 完了条件（暫定 57 §9 との対応）

| §9 | タスク |
|---|---|
| 1 | task_01（AST テスト）・段階 ① |
| 2 | 段階 ①（task_01〜04） |
| 3 | task_05〜07 |
| 4 | task_08〜10 |
| 5 | task_11 |
| 6, 7 | task_13 |
| 8 | task_08 |
| 9, 10 | task_09 |

## レビュー方針

- 共通観点は `.claude/rules/review.md`。
- 段階 ① は Windows の動作不変と、公開面の維持を重点的に見る。
- 段階 ③ は抑止の失敗時に入力を失わないこと（素通し）と、配送の滞留の規則を重点的に見る。
- probe の結果で暫定 57 を改訂したら、`codex-adversarial-reviewer` を通す。
- 段階の区切りとフェーズ完了判定では、`deep-reviewer` と Codex レビューを併用する。
