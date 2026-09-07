# task_08_spec_promotion

## 目的

**phase 11 の確定内容を正本 `instructions/common/` へ昇格し、フェーズを閉じる**。
根拠は phase.md タスク 8 + 暫定仕様 10 **§7 正本反映** + `integration_result.md` **§5 の申し送り 15 項目**。

- **原則コードを変更しない文書タスク**（`.claude/rules/agent_selection.md`「メインセッションが直接
  行ってよい作業」= フェーズ末の正本反映）。**唯一の例外**が `reference_cleanup_text.py` の
  警告文言 1 行とその追随テスト 1 行（phase.md タスク 8 / 申し送り 10）。
- **フェーズ末タスク**のため、`.claude/rules/task_execution.md`「フェーズ完了時」の一式を含む。
- 昇格が終わるまで**暫定仕様 10 が正**。昇格後は**暫定仕様 10 を凍結**し、以後は正本が正。

## 事前に確定済みの仕様判断（ユーザー確定 2026-09-08。本タスクはこれを転記する）

| # | 項目 | 確定 |
|---|---|---|
| B-1 | §3-8「部分失敗を許容し件数 + 理由を出す」が削除で未実装 | **条項を実装に合わせる**。削除の粒度は実行単位ディレクトリ（§4-B）であり、途中失敗は**中止**として「一部が削除されている可能性があります」を通知する、と正本へ書く。**実装変更なし** |
| B-2 | §3-11「presentation から内部モジュールを直参照しない」と実装の矛盾 | **条項に例外を明記**（判定名・理由コードなどの**定数と結果型**の import は当面の許容例。**関数・ロジックの直参照は不可**）。**実装変更なし**。公開面モジュールへの集約（**phase 10 分を含む**）は **idea として起票**して追跡する |
| B-3② | 削除経路だけ実行単位ディレクトリ自身のリダイレクト検査が無い | **§3-12 相当へ残存リスクとして記載**。実装変更なし（ガードを足すと一覧に出ない単位がアプリから消せなくなり §4-A と衝突する） |
| M6 | 「マニフェストが読めない」の定義（暫定仕様 v0.7） | **現状維持**。定義（JSON 解析不能 / トップレベルが object でない / `entries` が配列でない の 3 つだけ）と、**エントリ単位の妥当性は検査しない**旨を正本へ昇格 |

## 対象範囲

### 1. `spec_detail/data_schema.md`

1. **§5.8.1 の改訂（必須）** — 「孤児の削除は行わない / この検査範囲では孤児判定が原理的に
   成立しない」の記述を、**逆方向検査（§5.8.9）による部分的な補完がある**旨へ改める。
   **§5.8.1 の検査範囲自体は不変**（現在の構成セットが参照している子のみ）。
2. **新節 §5.8.9「孤児ファイルの棚卸し」を追加** — 走査範囲（参照側 4 経路）/ 参照集合の 2 段辿り /
   候補側と形状検証 / 保護対象 / 判定名 4 種 / 走査の不完全性 / 隔離（マニフェスト先行・原子書込み）/
   復元 / 削除（実行単位 ID + 検証①〜④・**④のみ強い確認で上書き可**）/ **既知の制約**。
   既知の制約には暫定仕様 §3-12 の 1〜8 に加え、**B-3② のリダイレクト単位**を含める。
3. **§5.10 への追記** — 個別プリセットの孤児扱い（**OFF のパスも参照ありと数える意図的 superset** /
   `user/hotkey_presets/global/` は候補側から除外）。**§5.5 / §5.10.1 の移行規則と矛盾して
   読めないよう明記する**。
4. **§5.4 への追記** — `config.json` の走査ディレクトリ設定キー `orphan_sweep_scan_dirs` と、
   **隔離ルートを起動時作成リストに含めない**旨。

### 2. `spec_detail/features.md` §4.6

設定メニューの 2 項目（「孤児ファイルの棚卸し…」「隔離の管理…」）を既存の並びへ追加する。

### 3. `instructions/common/codebase_map.md`

- 新規モジュール: `config_service/reference_scan.py` / `orphan_scan.py` / `quarantine.py` /
  `quarantine_manage.py` / **`path_boundary.py`**（境界判定 `is_real_path_within` の唯一の定義）。
- presentation: `orphan_sweep_text.py` / `quarantine_manage_text.py` /
  `config_io/orphan_sweep_io.py` / `quarantine_manage_io.py` /
  `dialogs/orphan_sweep_dialog.py` / `quarantine_manage_dialog.py`、設定メニューの 2 項目。
- `ConfigService` の委譲表（1 行委譲のファサード）。
- `ReferenceCleanupDialog` の `header` / `run_label` 引数化。

### 4. コード（唯一の例外・軽微）

`reference_cleanup_text.py:56` の「孤児かどうかはこの検査範囲では判定できません。」を、
**「孤児ファイルの棚卸し」へ誘導する文言**へ改める（§5.8.1 の改訂と整合させる）。
`tests/test_reference_cleanup_text.py:138` の追随を含む。**それ以外のコードは触らない**。

### 5. 受け入れ条件の是正（`integration_result.md` F-1 / F-2）

正本へ昇格する条件文のうち、**条件 21 を「既定では拒否される」へ限定**し、
**条件 16 の件数を実測値へ**改める（暫定仕様側の記述も同時に直す）。

### 6. フェーズ完了処理

1. **暫定仕様 10 の凍結**（状態行を「凍結済」にし、**条項を実装の根拠に引かない**旨を明記）。
2. `.claude_data/state/decisions_archive/11_orphan_child_file_sweep.md` の作成
   （`decisions.md` の phase 11 節を集約し、本体は「アーカイブ索引」の 1 行リンクへ置換）。
3. `instructions/phase/current.md` の完了記載更新（**次採番 = `instructions/phase/12_<topic>`**）。
4. `instructions/backlog/INDEX.md` の **idea_12 を完了へ更新し `INDEX_done.md` へ移動**。
5. **idea の新規起票**（B-2 の追跡）: 公開面モジュールへの定数・結果型の集約
   （**phase 10 の `reference_cleanup_text.py` / `reference_cleanup_io.py` を含む**）。
6. **`/refactor_check` の実行**と判定結果の完了報告への記載。

## 対象外

- **B-1 / B-2 / B-3② の実装修正**（いずれも「条項側 / 追跡側で処理する」とユーザー確定済み）。
- `external_keyboard_layouts` のパス基準の非対称（idea_13）。
- phase 10 の未対応指摘（H8 / H10 / H11 / H13 / H14）の是正。
- `config_service/__init__.py`（828 行）の分割。

## 確認

1. 正本 4 ファイル（`data_schema.md` / `features.md` / `codebase_map.md` + 暫定仕様の凍結）が
   更新され、**申し送り 15 項目すべてに反映または対象外の判断が付いている**。
2. **正本と実装が食い違っていない**（特に §5.8.9 の削除の検証④・部分失敗・
   「マニフェストが読めない」の定義）。**条項の根拠を `ファイルパス:行` で裏取りする**。
3. **§5.1（後方互換）に反する記述を入れていない**（既存キーの削除・意味変更をしない）。
4. `reference_cleanup_text.py` の文言変更が **`verifier` の実測で green**
   （`tests` / `tests_ui` / smoke。件数が減っていない）。
5. **`deep-reviewer` によるフェーズ完了判定**（設計文書 + 複数タスクを跨ぐ差分）と、
   **`codex-adversarial-reviewer` による敵対的レビュー**の 2 本立てを実施している
   （`.claude/rules/agent_selection.md` のレビュー表・フェーズ完了判定行）。
6. `/refactor_check` を実行し、判定結果を完了報告に記載している。

## 完了条件

- 上記「確認」1〜6 をすべて満たす。
- **フェーズ完了処理 1〜6 が済んでいる**（`.claude/rules/task_execution.md`「フェーズ完了時」）。
- 正本が更新されたことで、**暫定仕様 10 を読まなくても phase 11 の仕様が追える**状態になっている。
