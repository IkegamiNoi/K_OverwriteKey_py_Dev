# decisions_archive / phase 26: 起動エントリの保存時据え置き

対応表: phase 26 / **暫定仕様なし（直接改訂モード）** / decisions 26。
起票元: **ユーザー要望（2026-09-21）**・idea なし。
完了 2026-09-21。**仕様変更（既存キーの書き込み契機の変更）・JSON スキーマ不変**。
正本 = `spec_detail/data_schema.md` §5.4（条項を差し替え）/ `data_schema/5_08_09_orphan_sweep.md`（根拠文 1 行）。

## 問題

`config/config.json` の `keymap_set_path`（起動時に読む構成セット = **起動エントリ**）が
**構成セットの保存のたびに無条件で保存先へ書き換わる**。
別名保存を含む直近の保存先が常に次回の起動対象になり、メニュー
「起動時に読む構成セットを指定…」で指定した内容が意図せず失われる。

原因は `split_payloads.build_startup_payload`（旧 `:359`）が保存経路で常に
`payload["keymap_set_path"]` を設定していたこと。**正本 `data_schema.md:121` にも
「保存に成功すると保存先へ更新される」と規定されていた**ため、実装バグではなく
**仕様変更**と判定した（`spec_change_workflow.md`）。

## 現状監査（2026-09-21・実測）

| # | 箇所 | 変更前の挙動 |
|---|---|---|
| 1 | `split_payloads.py:359`（`build_startup_payload`） | `keymap_set_path` を**無条件で保存先に設定**。保存経路はここ 1 本 |
| 2 | `startup_io.py:17` `load_startup_and_config` | 起動エントリを読み、**不在 / 読込例外なら無言で空データ起動**（成否を記録していない） |
| 3 | `keymap_set_io.py:649` `set_startup_keymap_set` | メニュー指定。`write_startup` で `keymap_set_path` のみ更新（既存キーは `base.update` で保持） |
| 4 | `orphan_sweep_io.py:51` | 孤児棚卸しの走査経路 2 = 起動エントリ / 経路 3 = 現在のセット。**両方を渡しているため走査範囲は実質不変** |

`resolve_child_save_targets`（`save_plan_execution.py:145`）も `build_split_save_payloads` を通すが
**`startup_data=None` で結果を捨てる**ため、分岐追加の影響を受けないことを確認した。

## 確定した設計判断（ユーザー 2026-09-21）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | **保存では起動エントリを更新しない。ただし空 / 起動時に読めなかった場合のみ更新する**（自己修復） | 完全な据え置きは、起動エントリ未指定の新規状態で起動したセッションが**永久に空のまま**になる。変更経路はメニュー 1 本へ寄せつつ、未確定状態だけ保存で埋める |
| 2 | **「読めない」の判定 = 案 A（起動時の実読込結果を真偽値で保持し保存時に渡す）** | **案 B（保存時に `os.path.exists` で確認）は除外**。状態を持たずに済むが、**壊れた JSON は「存在する」と判定されて自己修復されない**（毎回空起動のまま固定される）。案 A は**不在・壊れた JSON・読込例外のすべて**が「読めない」に入る |
| 3 | **直接改訂モード** | 改訂対象が §5.4 の 1 条項 + §5.8.9 の根拠文 1 行、タスク 3 本に収まるため暫定仕様先行は不要 |
| 4 | **別名保存で起動エントリ自身を複製しても据え置き** | 別名保存は元ファイルを消さないため起動エントリは有効なまま残り、次回起動は**別名保存前のファイル**を読む。例外規定（保存元が起動エントリと一致するときだけ追従）は「有効なら触らない」の一貫性を崩すため除外 |
| 5 | **起動対象の可視化 UI は追加しない** | 開けば現在のセットが分かり、起動対象とのズレはユーザーが認識していれば足りる |
| 6 | **起動エントリを空へ戻す解除手段は追加しない** | メニューで指定し直せば足りる |

## 実装上の判断（task_02）

- **presentation は事実・application が判定**。`StartupIo.entry_loaded`（起動時に起動エントリを
  読めたか）という**事実**だけを presentation が持ち、`save_runtime_data` →
  `build_split_save_payloads` → `build_startup_payload` へ `startup_entry_loaded: bool` を貫通させる。
  **更新要否の判定は `split_payloads.py:363` の 1 箇所**に集約し、presentation 側に分岐を持たせない。
- `entry_loaded` の更新契機は **3 経路**（`startup_io.py:31` 起動読込成功 /
  `keymap_set_io.py:135` 保存成功 / `keymap_set_io.py:655` メニュー指定成功）。
- **`write_startup` には入れない**。一律に立てると、起動エントリ不在のままフォント変更等で
  config.json を書き出したセッションで**自己修復が失われる**。
- **新引数の既定値は False**（従来挙動 = 更新する側へ倒れる）。`resolve_child_save_targets` と
  既存呼び出しの挙動は不変。既存 4 アサーション（`startup_data={}` / `write_startup` 経由）は
  **予想どおり無修正で pass**。
- 据え置く対象は **`keymap_set_path` だけ**。`ui_font_delta_pt` / `last_used_directory` /
  `orphan_sweep_scan_dirs` / hook キー / `hotkey_presets_path` は従来どおり保存で書かれる。

## 実測・レビュー

- compile clean / `tests` **518**（skip 7・514 → **+4**）/ `tests_ui` **449**（446 → **+3**）/ smoke pass。
  追加 7 件は個別実行でも全て pass。
- `reviewer`（task_01 差分）= **採用**（節番号・見出しの差分ゼロ）/
  `reviewer`（task_02 差分）= **完了可（採用）**。
- **実機目視 = OK**（2026-09-21・ユーザー確認）。
- `features.md:119` は**改訂不要**（メニュー項目名のみで書き込み契機を含まない）と実測確認した。
- **Codex が書いた行が LF で CRLF ファイルへ混在**していたためメインで CRLF へ揃えた（差分内容は不変）。
- コミット: `f720b46`（task_01）/ `9d476bd`（task_02）/ 本フェーズ末のコミット（task_03）。

## 残件

- **`existing_entry`（非空判定）と `startup_io.py:19` の `.strip()` で「空」の定義が字面上非対称**
  （`reviewer` の参考指摘）。`entry_loaded=True` かつ値が空白のみという組み合わせは
  3 経路のいずれからも生成されず**到達不能**（config.json を手編集した場合のみ）のため**据え置き**。
  `current.md`「別タスク化候補」の Phase 26 項へ送った。
- **`startup_io.py` の `keymap_set_path` の型正規化**（phase 25 残件①）は**未着手のまま**。
  本フェーズは同じ行に触れるが目的が違う（書き込み契機の変更であって型正規化ではない）。
- 起動時に読めなかったときの**通知は追加していない**（現行どおり無言で空データ起動・§5.4 経路 3 不変）。
- 孤児棚卸しの走査範囲は不変（経路 2 = 起動エントリ / 経路 3 = 現在のセットを両方渡すため）。
