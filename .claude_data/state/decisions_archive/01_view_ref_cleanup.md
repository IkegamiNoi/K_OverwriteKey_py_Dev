# decisions_archive / 01_view_ref_cleanup

フェーズ **01_view_ref_cleanup**（View 参照の後始末）の判断履歴。
索引は `.claude_data/state/decisions.md`「アーカイブ索引」。
フェーズ定義: `instructions/phase/01_view_ref_cleanup/phase.md`。

- 期間: 2026-07-17
- モード: **直接改訂モード**（仕様変更なし・暫定仕様なし。正本 `spec_detail/` の更新も不要）
- 目的: 計画04（Widget分割・フォルダ再編）で**意図的に残した** View まわりの残存参照 2 件を解消する
- 結果: **完了**（実装 2 タスク + 記録 1 タスク。標準検証全緑・実機目視 OK・reviewer 全て「完了可」）
- 起票元: ユーザー要望（2026-07-17）+ `current.md`「別タスク化候補」（計画04 W7 の残課題のうち機械的なもの）。
  **起票元 idea なし** → `backlog/INDEX.md` の更新は対象外

---

## task_01: status_bar 生やしのローカル変数化

- `views/status_bar.py` の `app.runtime_status_frame` / `app.status_bar` をローカル変数化
  → **採用**（reviewer「完了可」・指摘なし）
- **根拠**: 計画04 W5 では「ボタン/入力ウィジェットの逆流ではない」として対象外にしたが、
  調査の結果この 2 属性は `build_status_area` 関数内でしか使われておらず**読み手なし**＝
  W5 で処理した write-only 生やし（`topmost_chk` 等）と**同型**だった。よって同じ扱いで解消できる。
- 着手前 grep で読み手不在を再確認（App 属性を消すため見落とせば即 AttributeError）。
  完了後 `git grep -nE "app\.(runtime_status_frame|status_bar)" -- keyseq` = **0 件**。
- 挙動不変: 差分は「`app.` 除去に伴う識別子変更のみ」。親子関係・pack/grid 引数・style・
  textvariable・生成順（top→bottom）は不変（reviewer が旧実装と突合）。
- `app.ui_vars.*` / `app._update_file_status()` / シグネチャ `build_status_area(app, parent)` は維持。

## task_02: trigger_list alias 削除 / action_list alias 据え置き

- `full_view.py` / `compact_view.py` の `self.trigger_list = self.trigger_box.trigger_list` を削除
  → **採用**（reviewer「完了可」・指摘なし）
- tests_ui は**参照経路のみ**変更（`app.<view>.trigger_box.trigger_list`）。
  **アサーション・期待値・メソッド名は不変**（計画04 §4-6 のテスト変更禁止に抵触しない。
  W5 で `keymap_listbox` に対して行った前例と同型）。

### 【重要】`action_list` alias を据え置いた理由（trigger_list との性質差）

同じ「View の alias」でも扱いが異なる。取り違えると回帰になるため記録する:

| | `trigger_list` | `action_list` |
|---|---|---|
| 種別 | **複数 View 共有**（full / compact 両方に存在） | **単一 View 所有**（full のみ） |
| production の参照方法 | W5 で**登録方式**（`TriggerPanelController._trigger_lists`）へ移行済み。**View 経由で触らない** | `controllers/trigger_panel_controller.py` が `self._app.full_view.action_list` を**実際に使用中** |
| alias の位置づけ | **tests_ui 専用の遺物**（production は非依存） | 計画04 §1.3-2 が認める「**App → View → Widget のパス**」そのもの＝生きた参照経路 |
| 判定 | **削除**（採用） | **据え置き**（保留。将来やるなら別タスク） |

- 削除前に `git grep -n "\.trigger_list" -- keyseq` で production の alias 非依存を裏取り
  （残存は `views/*/trigger_box.py` の所有者側のみ。`controllers/` に参照なし）。
- 完了後の grep: alias 定義 **0 件** / `action_list` alias **1 件**（`full_view.py`・据え置き確認）。
- 結果として、View → App の生やしと View 内の暫定 alias は、**意図して残した `action_list` を除き解消**。

## /refactor_check 判定（2026-07-17）

- **不要**（M1〜M6 いずれも該当なし。対象: `keyseq/` 配下 3 ファイル / **+11・-13 行**）→ **採用**
  （内訳: `compact_view.py` -1 / `full_view.py` -1 / `status_bar.py` +11 -11）
- 提案書は起票しない。M5（申し送りコメントの新規追加）も 0 件。
- PHASE_BASE = `1ec8873`（フェーズ起票コミット）〜 HEAD = `bfdf616`。
- 補足: 本フェーズは挙動不変リファクタであり `/refactor_check` の
  「挙動不変が前提のフェーズはスキップしてよい」に該当したが、規定どおり実行した（結果は「不要」）。

## codebase_map / 正本仕様の更新要否

- **いずれも不要**と判断 → **採用**
- 根拠: 挙動・仕様に変更がなく（`spec_detail/` の対象外）、生やし / alias は
  `codebase_map.md` の記載対象（クラス構成 / 関数責務 / JSON 構造 / UI 構成）に該当しない。
  W5 の登録方式・App→View→Widget パスの記述は本フェーズでも有効なまま。

## コミット一覧

| コミット | 内容 |
|---|---|
| `1ec8873` | フェーズ 01_view_ref_cleanup を起票（PHASE_BASE） |
| `66f1d4c` | task_01: status_bar の生やしをローカル変数化 |
| `bfdf616` | task_02: View の trigger_list alias を削除 |
| （本コミット） | task_03: 正本反映・記録（decisions_archive / current.md / refactor_check 判定） |

## 検証・レビュー

- 標準検証（全タスクで全緑）: compile clean / tests **59** / tests_ui **9** / smoke pass
  （`.venv` python。`test_trigger_lists_populated` は task_02 後も新経路で pass）
- reviewer（5観点）: 起票内容 / task_01 / task_02 とも「**完了可**・指摘なし」
- 実機目視（task_01 + task_02 まとめて・ユーザー確認 **OK**）:
  ステータスバー表示（ファイル状態 / 一時メッセージ / 「ステータス」欄）/
  フル・省略両ビューのトリガー一覧表示と選択共有

## 次フェーズへの申し送り

- 次は [idea_01](../../instructions/backlog/idea_01_hotkey_validation_to_domain.md)（hotkey 検証を domain へ。
  設計判断を伴うため `/spec_draft` 推奨）→
  [idea_02](../../instructions/backlog/idea_02_startup_font_settings_cleanup.md)（起動設定/フォント クラスタ）の順。
- `action_list` alias の解消は据え置き中（上記の理由。やるなら単独タスク）。
