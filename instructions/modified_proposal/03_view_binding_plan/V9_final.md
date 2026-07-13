# V9: 最終検証・実測とドキュメント更新

- 実施日: 2026-07-06

## 最終標準検証（フル）

- `py -m compileall -q keyseq main.py`: OK
- `py -m unittest discover -s tests`: 59 tests OK
- `py -m unittest discover -s tests_ui`: 9 tests OK
- `py -m tests.smoke_app`: SMOKE OK

## app.py 行数の実測

- ベースライン（c30371d）: **990 行**
- 本計画完了時: **629 行**（`wc -l` / `git show HEAD:… | wc -l` / PowerShell `[regex]::Matches($c,"`n").Count` / `(Get-Content).Count` すべて 629 で一致）
- 目安 500 行未満は未達だが、計画上「超えても完了条件違反ではない」。V8-2 の総ざらい＋本項の網羅 grep で**コントローラへの純委譲は 0 件**を確認済み。残る 629 行の内訳は実ロジック（`__init__` の生成・配線約120行 / `_build_ui` / `_build_menu` / `_build_status_area` / `validate_hotkey` / View 切替 / ショートカット / フラッシュ・フォント / 調整役 6 / 薄ヘルパ 5 / 状態エイリアス / dialogs 契約）であり、これ以上の委譲削除余地はない。

> PowerShell の `Measure-Object -Line` は一時的に 543 と表示したが、`[regex]::Matches` と `(Get-Content).Count` は 629。`Measure-Object -Line` の既知の癖（各行オブジェクト内の改行数を数える仕様）による差であり、実行数は 629 行が正。

## 網羅チェック（付け替え漏れ 0 の確認）

- 各コントローラ / views / dialogs / keyboard_window に残る `self._app._*` / `app._*` / `parent._*` / `master._*` はすべて §1.4「App に残すもの」（実ロジック `_set_flash_message` / `_sync_control_vars_from_data` / `_coerce_font_delta`、配線用薄ヘルパ `_find_trigger_by_key`、状態契約 `_indices` / `_selected_trigger_idx` / `_dialog_result` / `_startup_settings` / `_compact_mode` / `_programmatic_action_select`、Tk ルート `_apply_always_on_top`）。**削除済み委譲への参照は 0 件**。

## ドキュメント更新

- `instruction/common/codebase_map.md` の App 項を更新: 「コントローラ生成と配線（ラムダで実行時解決）・調整役メソッド（キャプチャ相互排他、ダーティ既定解決）・dialogs 向け契約（validate_hotkey / _dialog_result）・状態依存の詰め替え薄メソッド」を明記し、「views / dialogs / keyboard_window はコントローラを `app.<名前>` 経由で直接参照する」ことを追記。

## 手動確認について（重要・要ユーザー対応）

- 本作業は GUI を持たない自動実行環境で行ったため、計画が各項目で必須とした**実機での手動確認（フック ON/OFF・ダイアログ中の自動停止/復帰・停止/トグルキー・suppress・send guard・保存/読込一巡・レイアウト操作・キーマップ/トリガー操作等）は実施できていない**。
- 代替として全項目で標準検証（compile / unittest 59 / tests_ui 9 / smoke）が緑であることを確認済み。tests_ui はフックのサスペンドカウンタ・キャプチャ・パネル更新など主要な安全挙動を自動検証している。
- **V2 / V9 のフック手動 6 項目は計画で省略禁止のため、ユーザー側で実機確認をお願いしたい**（確認前に必ず停止キーを設定し、確認後はフックを停止して終了すること）。挙動は一切変更していない（参照先付け替えと未使用委譲の削除のみ）ため、リスクは低いと考える。

## 完了状態

- ブランチ `refactor/03-view-binding` に V1〜V8 の 8 コミット + 本 V9（ドキュメント）。
- `git status` クリーン化はこのコミットで達成。
- push は行わない（ユーザー実施）。
