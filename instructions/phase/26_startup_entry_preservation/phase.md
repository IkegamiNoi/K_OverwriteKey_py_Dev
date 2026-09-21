# phase.md

## フェーズ名

起動エントリの保存時据え置き（startup_entry_preservation）

## フェーズの目的

`config/config.json` の `keymap_set_path`（起動時に読む構成セット = **起動エントリ**）を、
**構成セットの保存では上書きしない**ようにする。現在は保存のたびに無条件で保存先へ書き換わるため、
**別名保存を含む直近の保存先が常に次回の起動対象になり**、メニュー「起動時に読む構成セットを指定…」で
指定した内容が意図せず失われる。

**起動エントリの変更経路をメニュー 1 本へ寄せる**のが目的。ただし**起動エントリが空、または
起動時に読めなかった場合は保存で更新する**（自己修復。指定前の新規作成状態で起動してしまうのを防ぐ）。

**presentation / application 限定・JSON スキーマ不変**（既存キーの書き込み契機のみを変える）。

- 起票元: ユーザー要望（2026-09-21）。
- 主入力（暫定仕様）: なし（直接改訂モード）。
- モード: **直接改訂モード**。番号対応: phase 26 / decisions 26。
  **正本 `data_schema.md` §5.4 の該当条項を先に改訂してから実装する**
  （現行の規定「保存に成功すると `keymap_set_path` は保存先へ更新される」と逆になるため）。

## 確定（ユーザー 2026-09-21）

- 保存時、起動エントリが**空または読めない**なら保存先で更新し、**有効なら更新しない**。
- **「読めない」の判定は起動時の実読込結果を真偽値で保持し、保存時に application へ渡す**（案 A）。
  **不在・壊れた JSON・読込例外のすべてが「読めない」**に含まれる。
  保存時の `os.path.exists` による確認（案 B）は採らない — 壊れた JSON が自己修復されないため。
- **別名保存で起動エントリ自身を移動 / リネームしても起動エントリは据え置き**。
  別名保存は元ファイルを消さないため起動エントリは有効なまま残り、次回起動は旧ファイルを読む。
  変更したい場合はメニューで指定し直す。
- **起動対象の可視化 UI は追加しない** — 開けば現在のセットが分かり、起動対象とのズレは
  ユーザーが認識していれば足りるため。
- **起動エントリを空へ戻す解除手段は追加しない** — メニューで指定し直せば足りるため。

## 現状監査（2026-09-21・実測）

| # | 箇所 | 現在の挙動 |
|---|---|---|
| 1 | `split_payloads.py:359`（`build_startup_payload`・`:347-` 定義） | `payload["keymap_set_path"]` を**無条件で保存先に設定**。保存経路はここ 1 本 |
| 2 | `startup_io.py:17` `load_startup_and_config` | 起動エントリを読み、**不在 / 読込例外なら無言で空データ起動**（成否を記録していない） |
| 3 | `keymap_set_io.py:649` `set_startup_keymap_set` | メニュー指定。`write_startup` で `keymap_set_path` のみ更新（既存キーは `base.update` で保持） |
| 4 | `orphan_sweep_io.py:51` | 孤児棚卸しの走査経路 2 が `_startup_settings["keymap_set_path"]`、経路 3 が現在のセット。**両方を渡しているため走査範囲は実質不変** |

`resolve_child_save_targets`（`save_plan_execution.py:145`）も `build_split_save_payloads` を通すが
**`startup_data=None` で結果を捨てる**（書き込まない）ため、分岐追加時に影響がないことを確認する。

## スコープ

### 含む

- 正本 `instructions/common/spec_detail/data_schema.md` §5.4 の該当条項の改訂。
- 正本 `data_schema/5_08_09_orphan_sweep.md` 走査経路 3 の**根拠文 1 行**の更新
  （「通常読込は config.json を書かない」→ 保存も書かなくなるため理由づけが変わる。**走査範囲は不変**）。
- `keyseq/presentation/controllers/config_io/startup_io.py`: 起動エントリを読めたかの真偽値を保持し、
  メニュー指定・保存の成功で更新する。
- `keyseq/application/config_service/`: `save_runtime_data` → `build_split_save_payloads` →
  `build_startup_payload` へ真偽値を通し、**更新要否の判定は application 側に置く**。
- 対応するテスト（application 層の単体 + `tests_ui` の経路確認）。
  既存 4 アサーション（`tests/test_config_service.py:66` / `:127` / `:2516` /
  `tests_ui/test_config_io_characterization_keymap_set_startup.py:1306`）は `startup_data={}` か
  `write_startup` 経由のため**修正不要の見込み**（task_02 で実測確認する）。

### 含まない（後送り）

- 起動対象の可視化 UI・起動エントリの解除手段（ユーザー判断で不採用）。
- 起動時に読めなかったときの通知（現行どおり**無言で空データ起動**。§5.4 の経路 3 を変えない）。
- 別名保存で起動エントリ自身を移動したときの追従（据え置きで確定）。
- `startup_io.py` の `keymap_set_path` の**型正規化**（phase 25 の残件①。別件・同じ行に触れるが目的が違う）。
- `config.json` の他キーの書き込み契機の見直し。
- 孤児棚卸しの走査範囲そのものの変更。

## このフェーズで読むファイル

1. 正本 `instructions/common/spec_detail/data_schema.md` §5.4（`:113-121` 付近）
2. 正本 `instructions/common/spec_detail/data_schema/5_08_09_orphan_sweep.md`（走査範囲の 4 経路）
3. `keyseq/presentation/controllers/config_io/startup_io.py`（全体・約 80 行）
4. `keyseq/presentation/controllers/config_io/keymap_set_io.py:101-145`（`save_keymap_set_to`）/
   `:626-661`（`set_startup_keymap_set`）
5. `keyseq/application/config_service/split_payloads.py:23-90`（`build_split_save_payloads`）/
   `:347-367`（`build_startup_payload`）
6. `keyseq/application/config_service/save_plan_execution.py:21-32` / `:135` / `:145-175`
   （`save_runtime_data` と `resolve_child_save_targets`）
7. `keyseq/application/config_service/__init__.py:311-327`（`save_runtime_data` のシグネチャ）
8. `keyseq/presentation/app.py:75-85` / `:196`（`_startup_settings` の初期化と `load_startup_and_config` 呼び出し）
9. テスト: `tests/test_config_service.py:60-70` / `:120-130` / `:2510-2520`、
   `tests_ui/test_config_io_characterization_keymap_set_startup.py:1300-1310`

## タスク

- [task_01](tasks/task_01_spec_revision.md): 正本改訂（`data_schema.md` §5.4 の条項差し替え +
  `5_08_09_orphan_sweep.md` の根拠文）— **完了**（2026-09-21・reviewer 採用）
- [task_02](tasks/task_02_startup_entry_guard.md): 実装 — 起動エントリの読込成否を保持し、
  保存経路の更新要否を application で判定する（+ テスト）
- task_03: 記録と完了（`decisions_archive/26` / `current.md` / `/refactor_check`）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。
- **本フェーズ固有**:
  - **起動エントリが有効なとき、`config.json` の他キーは従来どおり書けているか**
    （`ui_font_delta_pt` / `last_used_directory` / `orphan_sweep_scan_dirs` / hook キー /
    `hotkey_presets_path`。**据え置くのは `keymap_set_path` だけ**）。
  - **真偽値が更新される 3 経路に漏れがないか**（起動読込の成功 / 保存の成功 / メニュー指定の成功）。
    特に**起動時に読めなかったセッションで 2 回目以降の保存が起動エントリを動かさない**こと。
  - **既定引数で従来挙動へ倒れていないか**（application の新引数の default 値）。
    書き込まない経路（`resolve_child_save_targets`）に影響していないか。
  - **責務分離**: presentation は「起動時に読めたか」という**事実**だけを渡し、
    **更新要否の判定は application** にあるか。
  - **依存方向**: application が presentation を参照していないこと。
  - 孤児棚卸しの走査経路 2 / 3 が実質的に変わっていないこと（`orphan_sweep_io.py:51`）。
