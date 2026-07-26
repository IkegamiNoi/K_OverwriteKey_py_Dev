# 暫定仕様 05: 子ファイル保存の確認ダイアログと参照元記録（child_file_save_dialog）

> 状態: **未凍結・v0.2・主入力・ユーザー確定済（実装着手可）**。本書がこのフェーズ（保存系リデザインの
> Phase β）の確定設計（フェーズ中は正本を直接改訂しない）。フェーズ末タスクで正本
> `instructions/common/spec_detail/` へ昇格し本書を凍結する。
> 版履歴: v0.1 起票（2026-07-27）→ **v0.2** codex-adversarial-reviewer 指摘 4 件（critical 1 + high 3）を反映
> （① 未知の参照元は安全側で別名保存を既定に / ② ③ 保存計画に依存関係＋application 側で計画確定・失敗時ロールバック /
> ④ 既定命名変更は trigger_set のみ・監査の配置誤りを修正・keymaps/sequences は現行命名＋①と衝突ダイアログで安全化）。
> ユーザー確定 2026-07-27。
> 起票元: ユーザー要望（2026-07-26〜27・保存系統の改善討議・点3/4）。Phase α（暫定 04）の後続。
> 依存: **Phase α（暫定 04）完了が前提**。本フェーズは
> [idea_05](../backlog/idea_05_trigger_set_source_path_inconsistency.md) を内包し、
> [idea_06](../backlog/idea_06_individual_json_io_unification.md) の共通化を達成する見込み。

---

## §1 目的 / 背景

構成セット（keymap_set）の「保存」が**子ファイル（keymap / trigger_set / sequence）をまとめて無条件上書き**する
現挙動を、**変更のある子ファイルごとに保存方法を選べる確認ダイアログ**へ置き換える。あわせて、子ファイルが
どの上位ファイルに属するかを記録し、**他所の keymap_set に属する子ファイルの誤爆上書きを防ぐ**。
本フェーズは**挙動変更を伴う**。

解決する不満（ユーザー討議 2026-07-26〜27・点3/4）:

- keymap_set の「保存」で子ファイルがまとめて保存されるが、**保存対象が何か分からず、上書き確認も飛ばされる**。
- 保存対象を一覧提示し、項目ごとに **保存/別名保存/保存しない** をラジオで選びたい。
- **利用している上位ファイルを記録**し、**上位が一致しない/複数のときは別名保存をデフォルト**にしたい。
  ただし「意図的に共有したいファイル」もあるため、共有を**可視化**して選べるようにしたい。
- トリガー一覧からの出力シーケンス保存も同様（**シーケンスの直接の上位はトリガー一覧**、keymap_set は間接）。

### 現状監査（2026-07-27・v0.2 で配置を修正）

**子ファイルの一括保存（無条件上書き）**:

- keymap_set の「保存」→ `KeymapSetIo.save_keymap_set_to`（`keymap_set_io.py:68-92`）→
  `config_service.save_runtime_data`（`config_service.py:200-252`）が、**keymap_set / trigger_set / keymaps / sequences /
  hotkey_presets / startup を一括で・無条件に上書き**する（`:227-246`）。個別の上書き確認・対象提示は無い。
- config_root 内へ保存する場合、trigger_set / hotkey_presets は**全セット共通の固定パス**
  （`user/trigger_sets/default.json` / `user/hotkey_presets/default.json`）へ書かれる（`_build_split_save_payloads:468-476`）。
  → 複数 keymap_set が同じ子ファイルを共有・上書きする（Phase α §9 の制約の根拠）。

**子ファイルの既定配置（v0.2 修正・指摘④）**:

- **keymaps**: `user/keymaps/` に **label / id 基準**で命名（`keymap_file_io.py` の suggest）。
- **trigger_set**: config_root 内では **固定 `user/trigger_sets/default.json`**（`_build_split_save_payloads:468-471`。
  keymap_set 名基準ではない ＝ 複数セットで衝突する唯一の子）。
- **sequences**: config_root 内では **`user/sequences/`**（`_is_default_trigger_set_area` 判定時。
  ※ v0.1 の「`<trigger_set>/sequences/` に置く」は**誤り**。config_root 内は `user/sequences/`）。
- hotkey_presets: `user/hotkey_presets/default.json`（**本フェーズでは触らない**・プリセットは暫定 07 でグローバル化）。

**変更（dirty）管理は子単位で存在する**（`dirty_state.py`）: keymap ごと `INTERNAL_KEYMAP_DIRTY` / trigger_set 全体
`trigger_set_dirty` / sequence ごと `INTERNAL_SEQUENCE_DIRTY` / keymap_set 全体 `config_dirty`。
`has_individual_dirty()`（`:47-57`）が走査判定。

**source_path**: keymap `INTERNAL_KEYMAP_SOURCE_PATH` / sequence `INTERNAL_SEQUENCE_SOURCE_PATH`（対称）/
trigger_set は**読み書き分断**（[idea_05](../backlog/idea_05_trigger_set_source_path_inconsistency.md)・本フェーズで接続）。

**参照元（上位ファイル）の記録は現状なし**。参照階層: **keymap→keymap_set / trigger_set→keymap_set / sequence→trigger_set**
（keymap_set は sequence の間接上位。`config_service.py:421` トリガーが `sequence_path` を持つ）。

## §2 確定事項（ユーザー 2026-07-26〜27 / 2026-07-27 確定）

- **概念は「子（下位）ファイルの保存」**。keymap_set 側の「保存」で、**変更（dirty）のある子ファイルごと**に一覧を提示し、
  項目ごとに **保存 / 別名保存 / 保存しない** のラジオで選ばせる。粒度は**ファイル単位**。
- **親 keymap_set.json は常に保存**（ラジオ対象にしない・索引として最後に書く）。変更のある子が無ければダイアログを出さない。
- **参照元を子JSONに記録する（案A・軽量）**。keymap / trigger_set は **keymap_set** を、sequence は **trigger_set** を記録。
  パスは config_root 内=相対 / 外=絶対（`to_config_relative_or_absolute`）。外部移動での参照不能は許容し
  掃除は [idea_07](../backlog/idea_07_reference_link_cleanup.md)。
- **【指摘①】未知の参照元（既存子JSONに `_parent_refs` 無し）は安全側で「別名保存」を既定にする**
  （共有を否定できるまで上書きしない）。
- **【指摘②③】保存は「保存計画」として原子的に扱う**:
  - 保存計画は **presentation が行ごとの指示（保存/別名パス/スキップ）を集め、application が実行**する。
  - **依存関係**: 子のパスが変わる（別名保存・新規パス）ときは、**その子を索引する上位（trigger_set / keymap_set）の
    保存を必須化**する（その上位は「保存しない」を選べない）。例: sequence を別名保存 → 親 trigger_set の保存必須。
  - **事前検証 → 書き込み**の順で行い、途中失敗時は**旧索引を維持**できるようにする（部分成功で親索引だけ旧状態に
    取り残さない）。個別 save API 再利用時も、**行ごとの粒度**（選んだ子だけ書く・他 sequence を巻き込まない）を守る。
- **【指摘④】既定命名の変更は trigger_set のみ**（現状 `default.json` に落ちる唯一の子）。keymap_set 名基準の名前にする。
  **keymaps / sequences は現状の命名ルールのまま**（衝突は上記①の安全既定＋既存の衝突ダイアログ
  `choose_save_path_with_collision` で守る）。**複数 trigger_set を持つ対応は将来課題**（本フェーズは 1 keymap_set:1 trigger_set）。
- **共有の可視化とデフォルト選択規則**（§5）: 保存ダイアログ内でのみ表示。
- **trigger_set の source_path 分断を接続する**（idea_05 内包）。
- 影響レイヤ: presentation（ダイアログ・保存計画の収集・参照元記録）+ application（保存計画の実行・事前検証・
  参照元永続化・trigger_set 既定命名）+ スキーマ（子JSONに参照元の内部キー追加・後方互換）。

## §3 子ファイル保存の確認ダイアログ（点3/4）

keymap_set の「保存」で:

1. **変更のある子を収集**（dirty フラグ）: dirty な各 keymap / dirty な trigger_set / dirty な各 sequence。無ければ
   ダイアログを出さず親 keymap_set.json のみ保存。
2. **一覧ダイアログ**を表示。各行 = 1 子ファイル。列: 種別 / 対象名 / 保存先パス / **共有状況**（§5）/ **ラジオ（保存/別名保存/保存しない）**。
   各行のデフォルトは §5 の規則（未知の参照元は別名保存）。
3. ユーザー確定後、**保存計画**（§2・行ごとの指示＋依存関係）を作り、**事前検証してから**実行:
   - **保存**: source_path（または既定パス）へ上書き。**別名保存**: `asksaveasfilename`。**保存しない**: スキップ。
   - パスが変わる子の親（trigger_set / keymap_set）は保存必須（依存関係）。
4. 子の保存完了後、**親 keymap_set.json を索引として保存**（子の最終パスを反映）。途中失敗時は旧索引を維持。

- **単体操作ではダイアログを出さない**（本ダイアログは keymap_set 一括「保存」経路にのみ挟む）。
- **既存の個別保存ボタン（各 box）は本フェーズでは統合しない**（§11）。

## §4 参照元記録（案A・軽量・参考表示）

- 子JSON に内部キー（例 `_parent_refs`）で**直接の上位ファイルパスの集合**を記録（keymap/trigger_set→keymap_set /
  sequence→trigger_set）。パスは `to_config_relative_or_absolute`。
- **更新（best-effort）**: 子を保存/別名保存した際、現在の上位パスを集合へ追加。上位の移動・削除は検知せず残置（→ idea_07）。
- **後方互換**: 既存子JSON に `_parent_refs` は無い → **未知**として扱い、**§5 で「別名保存」を既定**にする（指摘①・安全側）。
  既存キーは削除しない（追加のみ）。

## §5 共有の可視化とデフォルト選択規則（指摘①反映）

| 保存先ファイルの参照元状態 | 既定のラジオ | ダイアログ表示 |
|---|---|---|
| **未知（`_parent_refs` 無し）** | **別名保存** | 「所有元不明・安全のため別名」 |
| 現在の上位のみ（単独所有） | **保存（上書き）** | 「単独」 |
| 現在の上位を含み、かつ複数（共有） | **保存（上書き）** | 「N 個の上位で共有中・全てに影響します」警告 |
| 保存先が**別の上位に属す**（現在の上位が参照元に無い） | **別名保存** | 「別の構成に属します」注意 |

- いずれもデフォルトであり、ユーザーは上書き/別名/しない を選び直せる。共有情報は**保存ダイアログ内でのみ**表示。

## §6 子ファイルのデフォルト命名（trigger_set のみ・指摘④反映）

- **trigger_set**: source_path が無い場合の既定名を **keymap_set の stem** にする
  （例 keymap_set `gaming.json` → `user/trigger_sets/gaming.json`）。現状の固定 `user/trigger_sets/default.json`
  （`config_service.py:468-471`）を keymap_set 名基準へ変更 ＝ **複数 keymap_set の trigger_set 衝突を回避**。
- **keymaps / sequences**: **現状の命名ルールのまま**（keymap=label/id、sequence=`user/sequences/` の個別名）。
  衝突は §5 の未知→別名既定と既存の衝突ダイアログ（`choose_save_path_with_collision`）で守る（追加の命名変更はしない）。
- hotkey_presets は**触らない**（暫定 07 でグローバル化）。
- **複数 trigger_set を 1 keymap_set に持つ運用は将来課題**（そのとき trigger_set の命名名前空間を再検討）。

## §7 idea_05 の内包（trigger_set の source_path 接続）

- trigger_set の source_path を**接続**する（**案 1＝`dirty_tracker.trigger_set_source_path` へ寄せる**を軸に設計）。
- 旧「読込で持ってきた…別名で保存しますか？」個別ダイアログ（`trigger_set_file_io.py:12`）は復活させず、
  **§3 の統合ダイアログ＋参照元記録（§4/§5）へ寄せる**。
- 詳細はタスク定義で確定。

## §8 application 層の保存計画（指摘②③反映）

- 現状 `save_runtime_data` は子を無条件書き出しする。これを、**presentation が集めた保存計画（子ごと: 保存/別名パス/スキップ
  ＋依存関係）を application が実行**する形へ変更する。
- **実行契約**:
  - **事前検証**: 全対象の書込み可能性（パス妥当・依存関係の充足）を先に確認する。
  - **依存関係の強制**: パスが変わる子の親（trigger_set / keymap_set）保存を必須化し、スキップを禁止する。
  - **粒度の厳守**: 選んだ子だけを書く（trigger_set 保存が全 sequence を巻き込まない）。
  - **失敗時**: 旧索引（keymap_set / trigger_set の子パス参照）を維持できる順序・復元手順にする（完全なトランザクションは
    tkinter/ファイル系では困難なため best-effort。少なくとも親索引を新規パスへ進める前に子の書込み成功を確認する）。
- presentation オーケストレーションで個別 save 経路（`keymap_io` / `trigger_set_io` / `sequence_io`）を子ごとに呼ぶ場合も、
  上記契約（粒度・依存・検証）を満たすよう保存計画駆動にする（idea_06 の共通ドライバをここで実現）。

## §9 確認事項

（v0.2 時点で設計上の未確定なし。実装時の詳細〔保存計画の内部表現・事前検証の粒度・trigger_set stem の正規化〕は
タスク定義で確認する。参照元の内部キー〔子→上位の逆リンク〕と keymap_set 索引〔上位→子の順リンク〕は役割が異なる
〔前者＝共有判定 / 後者＝読込経路〕ことを設計で明示する。）

## §10 受け入れ条件（ドラフト）

| # | 条件 | 対応 § |
|---|---|---|
| 1 | 変更のある子が 2 個以上あるとき一覧ダイアログが出て、行ごとに保存/別名/しないを選べる | §3 |
| 2 | 変更のある子が無いときはダイアログを出さず親のみ保存する（回帰なし） | §3 |
| 3 | 未知の参照元（`_parent_refs` 無し）の子は既定が別名保存になる（共有破壊防止） | §4・§5 |
| 4 | 別の keymap_set に属する子へ保存しようとすると既定が別名保存になる | §5 |
| 5 | 意図的な共有ファイルは「N 個で共有中」警告つきで上書きを選べる | §5 |
| 6 | 子のパスが変わる（別名保存）とき、その親（trigger_set/keymap_set）の保存が必須化され、スキップできない | §2・§3・§8 |
| 7 | 保存途中で失敗しても親索引が旧状態のまま取り残されない（旧索引維持 or 整合的に進む） | §8 |
| 8 | 複数 keymap_set を `config/user/keymap_sets/` に保存しても、trigger_set が keymap_set 名基準で分離され既定では互いに上書きしない | §6 |
| 9 | trigger_set の source_path が接続され、keymap/sequence と一貫して扱える（idea_05 解消） | §7 |
| 10 | 既存の子JSON（`_parent_refs` 無し）でも保存・読込が正常（後方互換） | §4 |
| 11 | `tests` / `tests_ui` / smoke が更新後の期待値で pass。挙動変更点は特性テストで固定 | §3〜§8 |

- **安全網**: 保存計画（収集・依存・検証・失敗時の旧索引維持）・参照元判定（未知→別名含む）・trigger_set 既定命名を
  特性テストで固定。保存 JSON はバイト列比較。ダイアログは monkeypatch で選択を駆動（`tests_ui` 手法踏襲）。

## §11 スコープ外（本フェーズでやらない）

- **既存の個別保存ボタン（各 box）の統合**。
- **参照元の掃除機能** → [idea_07](../backlog/idea_07_reference_link_cleanup.md)（β 完了後）。
- **プリセットの config.json グローバル化** → 暫定 07。hotkey_presets は本フェーズで触らない。
- **停止/トグルキーの config.json 既定化** → Phase γ（暫定 06）。
- **複数 trigger_set / keymaps・sequences の keymap_set 名前空間化**（将来課題・§6）。
- **孤児ファイル検出**（掃除機能の逆方向・別 idea 候補）。

## §12 正本反映（フェーズ末昇格・予定）

| 対象 | 内容 |
|---|---|
| 正本 `spec_detail/` | `data_schema.md` に子JSON の参照元キー（`_parent_refs` 等）と trigger_set source_path の扱い、trigger_set 既定命名（keymap_set 名基準）を追記。保存計画（子ごと保存・依存関係）の規定があれば追従 |
| `codebase_map.md` | 子ファイル保存ダイアログ・参照元記録・保存計画の責務（presentation/application の分担）を反映 |
| 実装 | `config_io/*`（保存計画収集・参照元記録・trigger_set 既定命名・source_path 接続）/ `config_service.py`（保存計画実行・事前検証・trigger_set 命名）/ 新規ダイアログ（`io_dialogs.py` 拡張 or 専用モジュール）|
| テスト | `tests_ui/`（ダイアログ・参照元判定・依存関係・idea_05）/ `tests/`（application の保存計画実行・失敗時）|
| 別実装同期 | なし |

## 関連

- 前フェーズ: Phase α（[暫定 04](04_keymap_set_new_and_default_dir.md)）。
- 内包/達成: [idea_05](../backlog/idea_05_trigger_set_source_path_inconsistency.md)（内包）/
  [idea_06](../backlog/idea_06_individual_json_io_unification.md)（子保存共通化で達成見込み）。
- 後続: [idea_07](../backlog/idea_07_reference_link_cleanup.md)（掃除機能）。
- 敵対的レビュー: codex-adversarial-reviewer（2026-07-27・v0.1 対象・needs-attention）。指摘 ①〜④ を v0.2 で反映。
- 正本: `spec_detail/data_schema.md`（JSON 後方互換・既存キー削除禁止）/ `codebase_map.md`。
- 参照ルール: `.claude/rules/spec_change_workflow.md` / `.claude/rules/anti_patterns.md`（過剰共通化の回避）。
