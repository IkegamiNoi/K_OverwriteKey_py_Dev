# phase.md

## フェーズ名

タスクバーのアイコンで状態を表示（taskbar_status_icon）

## フェーズの目的

タスクバーのボタンを見るだけで、フックが ON / OFF / 一時停止のどれかが分かるようにする。
窓のアイコン（`wm iconphoto`）を状態ごとに差し替え、土台の画像の右上に色＋形の印（ON = 緑● / OFF = 赤■ / 一時停止 = 黄‖）を重ねる。
**presentation のみの変更（試作の結果しだいで infrastructure に 1 関数）・新規依存なし・JSON スキーマ不変**。

- 起票元: [idea_55](../../backlog/idea_55_taskbar_status_icon.md)（ユーザー要望 2026-10-31）。
- 主入力（暫定仕様）: [54_taskbar_status_icon.md](../../history/54_taskbar_status_icon.md)（v0.3・ユーザー確定済）。
- モード: **暫定仕様先行モード**。番号対応: phase 71 / 暫定 54 / decisions 71。

## 確定（ユーザー 2026-10-31）

- 状態はステータス欄の「フック: ON / OFF / 一時停止」と常に一致（ダイアログ・キーの取得の間は赤でよい）。
- 土台は Claude が作るサンプル画像（16 / 32 px）を同梱し、後でユーザーが同じファイル名で差し替える。
- 子窓も同じアイコン。トレイ・常駐化・オーバーレイアイコンはしない。Mac は対象外。
- タスクバーへの反映の方式（暫定 54 §3.3）と開いている子窓の方式（§5）は task_01 の試作で決める。
- 多言語対応より先に入れる。

## スコープ

### 含む

- 状態の判定関数 `hook_display_state` の切り出し（`presentation/status_text.py`）とステータス欄での利用。
- `presentation/status_icon/`（印の形の純関数・画像の読込と合成・設定・状態の記録）とサンプル画像。
- `update_status` への反映の結線・起動時の初回設定・子窓への反映。
- `presentation/help/bundled_paths.py` → `presentation/bundled_paths.py` への昇格。
- （試作の結果しだいで）AppUserModelID の設定（`infrastructure/win32_window.py`）。
- tests / tests_ui の追加・更新。正本反映。

### 含まない（後送り）

- 通知領域のアイコン・常駐化・右クリックメニュー / オーバーレイアイコン / Mac の Dock / DPI 対応の宣言 / exe の `.ico` / 本番の画像のデザイン（暫定 54 §11）。

## このフェーズで読むファイル

1. [暫定 54](../../history/54_taskbar_status_icon.md)（全体）
2. `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py`（`update_status` 409-430 行付近）
3. `keyseq/presentation/controllers/hook_controller.py`（状態の書き換え・`suspend_hook_for_dialog`）
4. `keyseq/presentation/status_text.py`
5. `keyseq/presentation/help/bundled_paths.py` とその利用元（`help/help_content.py` ・ `help/third_party.py` ・ `tests/test_help_content.py` ・ `tests/test_third_party.py`）
6. `keyseq/presentation/app.py`（`__init__`・`_build_ui` の前後）
7. `keyseq/infrastructure/win32_window.py`（試作で案 B を採るときだけ）
8. tests_ui の SimpleNamespace のフェイク App（例: `tests_ui/test_trigger_panel_controller_action_edit.py:57` ・ `tests_ui/test_action_list_rendering.py:189`）
9. 正本 `instructions/common/spec_detail/features.md` §4.5 / `instructions/common/codebase_map.md`（ステータス欄・`bundled_paths` の節）

## タスク

- task_01: 試作（実機）— 使い捨てのスクリプトで、`iconphoto` のタスクバーへの反映・`-default` が開いている子窓に効くか・使われるサイズ・AppUserModelID の要否を確かめ、暫定 54 §3.3・§5 の方式を決めて v0.4 へ反映（ユーザー確認）。コードは残さない。
- task_02: 土台の部品 — `bundled_paths.py` の昇格（`parents[2]`・`status_icon_dir()`）・`hook_display_state` とステータス欄での利用・`badge_shapes.py`（印の形の純関数）+ tests。
- task_03: アイコンの反映 — `StatusIcon`（画像の読込・合成・設定・状態の記録）・サンプル画像 2 枚・`update_status` と起動時の結線・子窓（task_01 の方式）・（案 B なら）AppUserModelID + tests_ui。
- task_04: 統合確認 — tests / tests_ui / smoke・二次レビュー（deep-reviewer + codex-reviewer）。
- task_05: 実機目視・正本反映（features.md §4.5・codebase_map・architecture・土台の画像のライセンスの扱い〔暫定 54 §12〕）・暫定 54 凍結・decisions_archive/71・current.md 完了記載・idea_55 の完了移動（INDEX.md → INDEX_done.md）・`/refactor_check`。

## レビュー方針

- ステータス欄とアイコンがずれないこと（判定の共用・反映の位置〔簡易表示の早期 return より前〕・部分失敗後の状態の記録）。
- 反映の失敗がステータス欄の更新や UI スレッドを止めないこと。
- `bundled_paths` の昇格で旧パスの横流しが残っていないこと・`bundled_root()` が同じ場所を返すこと。
- presentation の外へ依存を広げていないこと（案 B の ctypes は infrastructure の 1 関数に限る）。
