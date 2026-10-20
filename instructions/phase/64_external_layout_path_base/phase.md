# phase.md

## フェーズ名

外部キーレイアウトのパス基準の統一（external_layout_path_base）

## フェーズの目的

外部キーレイアウトの登録（`external_keyboard_layouts[].path`）が再起動のたびに消える不具合を直す。
登録・表示は `config` の親フォルダ基準、読込は `config` ルート基準で解決しているため、読み込むたびに `config/` が 1 段増え、増えたパスのファイルが無いので黙って読み飛ばされる（idea_13「実害の確認」）。
**登録・読込・表示の 3 か所を正本 §5.7 どおりの `config` ルート基準の相対表記（`/` 区切り・config 外は絶対）へそろえる。application（`split_loading`）+ presentation（`layout_controller`）。保存（`split_payloads`）は runtime 値をそのまま書く今の作りのまま。JSON スキーマ不変・§5.7 の規定も不変（実装を仕様へ合わせる修正）。**

- 起票元: [idea_13](../../backlog/idea_13_external_layout_path_base_asymmetry.md)（2026-09-06 起票・2026-10-20 実害確認で優先度を中へ・同日ユーザーが着手を判断）。
- 主入力（暫定仕様）: なし（直接改訂モード）。
- モード: **直接改訂モード**（§5.7 の規定は変えない・正本の書き換えは §5.8.9 の理由の記述と codebase_map のみ・タスク 2）。番号対応: phase 64 / 暫定なし / decisions 64。

## 確定（ユーザー 2026-10-20）

- 記録する表記は §5.7 のとおり **`config` ルート基準の相対**（例 `user/keylayout/jis.json`）・config 外は絶対・区切りは `/`
- **既存の壊れた値の移行はしない**（`config\user\…`〔親基準〕や `config/config/…` は修正後は読めず、今と同じく黙って読み飛ばす。**利用者が JSON を手で直す**）
- **同じファイルを指す要素の重複除去はしない**・登録時の重複判定は文字列比較のまま（表記がそろえば同じファイルは同じ文字列になるため。旧表記〔`\` 区切り・親基準〕の要素が残っていると同じファイルを再登録できてしまうのは受容）
- 孤児検出（§5.8.9）の「両基準を合わせて保護する」回避策は**残す**（手で直していない旧表記の JSON が指すレイアウトを誤って隔離しない・`reference_scan.py` は変えず正本の理由の記述だけ書き換える）

## スコープ

### 含む

- 読込: `split_loading.normalize_external_keyboard_layouts` を `config` ルート基準で解決 → `config` ルート基準の相対（config 外は絶対）へ。親基準への変換をやめる
- 登録: `layout_controller.add_external_keyboard_layout` の記録表記を `paths.to_config_relative_or_absolute` へ（`to_rel_if_possible`〔親基準〕をやめる）
- 表示: `collect_keyboard_layouts` / `resolve_registered_layout_path` に渡す基準を `config_root` へ（`layout_controller.py:184`・`:205`）
- テスト: 既存の期待値の見直し（`tests/test_config_service.py:1947-1953` が非対称な出力を固定している）・**登録 → 保存 → 読込を繰り返しても値が変わらない**こと・config 外の絶対パスはそのまま
- 実機目視（ユーザー）: 外部レイアウトを登録 → 再起動して一覧に残る・2 回以上再起動しても JSON の値が変わらない
- 正本反映: `5_08_09_orphan_sweep.md` の理由の記述（非対称の是正済み・旧表記の保護として残す）/ `codebase_map.md`

### 含まない（後送り）

- 既存の壊れた値の移行・救済・重複除去（ユーザー判断で不要）
- 登録時の重複判定を解決後のパスの比較にすること
- 保存経路（`split_payloads`）の変更・§5.7 の規定の変更
- 削除（`delete_keyboard_layout`）の比較方法の変更（`entry.path` は記録表記のまま持つので今の文字列比較で合う）

## このフェーズで読むファイル

1. `instructions/backlog/idea_13_external_layout_path_base_asymmetry.md`（原因・再現手順）
2. `keyseq/application/config_service/split_loading.py:540-568`（`normalize_external_keyboard_layouts`）
3. `keyseq/presentation/controllers/layout_controller.py:180-210`・`:290-313`（表示の基準・登録）
4. `keyseq/presentation/config_paths.py:94-98`・`:126-127`（`to_config_relative_or_absolute` / `to_rel_if_possible`）
5. `keyseq/presentation/keyboard_layouts.py:272-295`・`:335-338`（`collect_keyboard_layouts` / `_resolve_layout_path`）
6. `keyseq/application/config_service/reference_scan.py:204-216`（孤児検出の superset・変えないことの確認のみ）
7. 正本: `data_schema.md` §5.7・§5.5（`external_keyboard_layouts[]`）/ `data_schema/5_08_09_orphan_sweep.md:38-42` / `codebase_map.md`（LayoutController・split_loading）
8. テスト: `tests/test_config_service.py:1940-1960` 付近 / `tests/test_layout_controller_scan_code.py:34`・`:67`（スタブの app と `collect_keyboard_layouts` の基準の期待値）/ 外部レイアウトの登録・表示のテスト（`grep external_keyboard_layouts tests tests_ui`）

## タスク

- task_01: 登録・読込・表示の基準を `config` ルートへそろえる・テスト（期待値の見直し・往復で値が変わらない）。**実装後にユーザーの実機目視**（登録 → 再起動で残る）
- task_01a: 読込の解決を 1 回にする（相対の `config_root` で `config/` が増える・完了判定前の Codex 敵対的レビューの指摘〔中〕をユーザーが採用 2026-10-21）・config 外の絶対パスの登録のテスト
- task_02: 正本反映（`5_08_09_orphan_sweep.md` の理由の記述・`codebase_map.md`）・`decisions_archive/64_external_layout_path_base.md`・decisions.md の索引・current.md の完了記載・idea_13 を INDEX_done へ・`/refactor_check`・完了判定前レビュー

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: 3 か所（登録・読込・表示）が同じ基準になっている / 読込を何度通しても値が変わらない（冪等）/ config 外の絶対パスが相対に化けない・区切りが `/` / 保存経路は変えていない / 他のパス（keymaps・trigger_set 等）の解決に波及していない / 孤児検出の挙動が変わっていない（superset を残す）
