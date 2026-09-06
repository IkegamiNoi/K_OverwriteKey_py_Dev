# phase.md

## フェーズ名

孤児ファイルの棚卸し（orphan_child_file_sweep）

## フェーズの目的

**どの keymap_set からも参照されていない子ファイル（孤児）を検出し、可逆な「隔離」を経て削除できるようにする。**
phase 10 の「参照元の掃除」が持つ「現在の構成セットしか見ないため孤児判定が成立しない」という制約を、
**逆方向検査（上位 → 子の索引走査）**の新設で部分的に解く。

- **対象レイヤ**: **application**（走査・参照集合の構築・孤児判定・隔離 / 復元 / 削除の実行）+
  **presentation**（メニュー・確認 UI・走査ディレクトリ設定）。domain は変更しない。
- **スキーマ変更**: **あり**（`config/config.json` に走査ディレクトリ設定のキーを**追加**。
  既存キーの削除・意味変更はしない）。
- **本アプリ初のディレクトリ走査**（`keyseq/` に `os.listdir` / `glob` / `os.walk` は現在 0 箇所）
  かつ**初のファイル削除機能**である。
- 起票元: [idea_12](../../backlog/idea_12_orphan_child_file_sweep.md)（2026-08-16 起票・phase 10 から分離。
  前提だった phase 10 の完了 = 2026-09-05 で充足）。
- 主入力（暫定仕様）: [10_orphan_child_file_sweep.md](../../history/10_orphan_child_file_sweep.md)
  （**v0.4・ユーザー確定済**）。
- モード: **暫定仕様先行モード**。番号対応: **phase 11 / 暫定 10 / decisions_archive 11**。

## 確定（ユーザー 2026-09-06）

暫定仕様 10 §2 / §4 が正。要点のみ再掲する（**条項の正は暫定仕様 10**）。

- **到達範囲 = 検出 + 隔離 + 復元 + 隔離済みの削除**。削除は**隔離ディレクトリ内のみ**。
- **走査（参照側）= `user/keymap_sets/` 直下 + 起動エントリ + 現在開いているセット + ユーザー指定ディレクトリ**。
  指定ディレクトリは**設定として記録**し、**不在ならスキップして完了後にパス表示**（警告のみ・危険信号にしない）。
- **候補側 = config 配下の既定 4 ディレクトリ直下のみ**（keymap / trigger_set / sequence / 個別 hotkey_presets）。
  **形状検証あり**。`user/hotkey_presets/global/` は除外。
- **`hotkey_presets_individual` が OFF でも `hotkey_presets_path` は参照ありと数える**（意図的 superset）。
- **隔離ルート = `<config_root>/quarantine/`**（`user/` の外）。実行単位 = `<YYYYMMDD_HHMMSS>/`。
- **読めなかった参照側があっても隔離・削除とも許す**（警告 + 「実行 / キャンセル」の 2 択。
  degraded 方式は検討のうえ**不採用**）。残存リスクは暫定仕様 §3-12-5。
- **削除は通常のファイル削除**（OS のゴミ箱へ送らない。新規依存を追加しない）。
- **フェーズは分割しない**。ただし**「検出まで」を先に green にしてから**隔離 / 復元 / 削除へ進む。

## スコープ

### 含む

- 参照側の走査と**2 段辿り**（keymap_set → trigger_set → sequence）による参照集合の構築。
- 候補側の列挙・形状検証・**孤児判定**（判定名 `ORPHAN_CANDIDATE` / `ORPHAN_REFERENCED` /
  `ORPHAN_PROTECTED` / `ORPHAN_EXCLUDED`）と**保護対象**の適用。
- 走査ディレクトリ設定の永続化（`config.json` へキー追加・**起動設定の書き出し経路 1 本**を通す）。
- 隔離（**マニフェストを移動前に原子書込み**）・復元・削除（**実行単位 ID + 4 検証**）。
- 設定メニュー 2 項目と確認 UI（`ReferenceCleanupDialog` の**ヘッダ / ボタンラベル引数化**を含む）。
- 上記に対する `tests/` `tests_ui/` のテスト追加。

### 含まない（後送り）

- `external_keyboard_layouts` を候補側にすること / そのパス基準の非対称の是正
  → [idea_13](../../backlog/idea_13_external_layout_path_base_asymmetry.md)。
- `_parent_refs` の仕組み変更・保存フローの改変。
- 候補側の再帰走査、config 外に置かれた子の棚卸し。
- 孤児候補の**行ごと**の選択 UI。
- phase 10 の未対応指摘（H8 / H10 / H11 / H13 / H14）の是正（**新規コードで同じ形を作らない**にとどめる）。
- `config_service/__init__.py`（767 行）の分割（`current.md`「別タスク化候補」で追跡中）。

## このフェーズで読むファイル

1. `instructions/history/10_orphan_child_file_sweep.md`（**主入力・v0.4**）
2. `instructions/common/spec_detail/data_schema.md` §5.4 / §5.5 / §5.7 / §5.8.1 / §5.8.4 / §5.10 / §5.10.1
3. `instructions/common/spec_detail/features.md` §4.6
4. `keyseq/application/config_service/__init__.py`（パス基盤・`ensure_split_config_dirs`・ファサード）
5. `keyseq/application/config_service/split_loading.py`（子キーの読み手・2 段辿りの根拠）
6. `keyseq/application/config_service/split_payloads.py`（保存側のキー・`build_keymap_set_payload`）
7. `keyseq/application/config_service/parent_refs_cleanup.py`（phase 10 のコア・結果型と判定名の型）
8. `keyseq/presentation/reference_cleanup_text.py` / `keyseq/presentation/dialogs/reference_cleanup_dialog.py`
9. `keyseq/presentation/controllers/config_io/reference_cleanup_io.py`（入口の同型）/
   `.../keymap_set_io.py`（`confirm_save_if_dirty` の意味・`config.json` 書き込み経路）
10. `keyseq/presentation/views/menu_bar.py` / `keyseq/presentation/config_paths.py`
11. `tests/test_parent_refs_cleanup.py` / `tests/test_reference_cleanup_text.py` /
    `tests_ui/test_reference_cleanup_flow.py`（守る対象と書き方の見本）

## タスク

1. **task_01 参照パス収集器**（application・新規モジュール）— keymap_set / trigger_set から
   子パスを読み出す**読み出し専用**の収集器と**2 段辿り**。`external_keyboard_layouts` は
   **両基準 superset**。単体テスト。
2. **task_02 走査と孤児判定** — 既定 / 起動エントリ / 現在のセット / 指定ディレクトリの列挙、
   候補側の収集と**形状検証**、保護対象の適用、判定名 4 種、走査の不完全性の記録。単体テスト。
3. **task_03 検出フローの入口と表示** — 表示文言の純関数 + `config_io` の新規 IO + 設定メニュー
   「孤児ファイルの棚卸し…」+ 未保存時の**「保存する / 中止する」2 択**（`confirm_save_if_dirty` は使わない）。
   **受け入れ条件 17 の「警告文の生成と一覧先頭への配置」はこのタスクが担当**
   （読めなかった参照側・対象外件数・走査範囲外の注記。0 件時は通知へ含める）。
   **ここまでで「検出のみ」が green になる**（§4-F の段取り）。
4. **task_04 走査ディレクトリ設定** — `config.json` へのキー追加（**起動設定の書き出し経路**を通す・
   `_startup_settings` 更新）+ 棚卸しダイアログ内のリスト UI（追加 / 削除）+ 不在時の報告。
5. **task_05 隔離** — 隔離ルートの遅延作成、**マニフェストの原子書込み（移動前）**、相対構造を保った移動、
   **〔提示済み〕∩〔再判定でも孤児〕**への限定、部分失敗の継続と結果表示。
   **受け入れ条件 17 の「実行 / キャンセルの 2 択」はこのタスクが担当**
   （警告があっても実行できること・確認用 UI を作らないこと）。
   **`ReferenceCleanupDialog` のヘッダ / ボタンラベル引数化もここ**（「隔離する」ボタンが必要なため
   task_06 から前倒し。既定値は現行文字列で既存挙動を変えない）。
6. **task_06 隔離の管理（復元 + 削除）** — 「隔離の管理…」メニューと実行単位のリスト選択 UI、
   復元（`original_path` のガード・同名スキップ・全件復元時の後始末）、
   削除（**実行単位 ID + 4 検証**・再帰削除・不可逆の明記）。
   `ReferenceCleanupDialog` は **task_05 で引数化済みのものを使うだけ**（再改修しない）。
7. **task_07 統合確認** — テストスイート全体 + smoke を `verifier` で実測し、
   **実機目視の観点リストを作成**してユーザーへ提示・結果を受領。
8. **task_08 正本反映（最終タスク）** — `data_schema.md` §5.8.1 の**改訂**と新節の追加、
   §5.10 / §5.4 への追記、`features.md` §4.6、`codebase_map.md`、
   `reference_cleanup_text.py` の警告文言の見直し、暫定仕様 10 の**凍結**、
   `decisions_archive/11_orphan_child_file_sweep.md` の作成、`current.md` の完了更新、
   `backlog/INDEX.md` の idea_12 を `INDEX_done.md` へ移動、`/refactor_check` の実行。

> タスク定義ファイルは着手するタスクから順に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

## レビュー方針

共通観点は `.claude/rules/review.md`。本フェーズ固有の観点は次のとおり。

- **誤隔離の経路**を最優先で疑う。参照集合に入れるべきキーの漏れ、保護対象の取りこぼし、
  パス解決基準の取り違え（正本 §5.7。**canonical 値を保存値・表示へ混入させない**）。
- **破壊的 I/O の失敗時の状態**（部分失敗・中断・マニフェスト不整合）で可逆性が壊れないか。
- **削除ガードが UI の入力を信用していないか**（`is_path_within` は**同一パスも配下と判定する**）。
- **依存方向**: application は `app` を参照せず、保護対象・走査対象を**引数で受け取る**。
  presentation から `config_service` の内部モジュールを直参照しない。
- タスク単位は `reviewer`、統合確認とフェーズ完了判定は `deep-reviewer` + Codex レビューの 2 本立て
  （`.claude/rules/agent_selection.md`）。
