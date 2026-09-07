# 提案書 08: phase 11（孤児ファイルの棚卸し）後のリファクタ

`/refactor_check` の判定 = **推奨**（**M6 該当**）。**判定と起票のみで、実施はユーザー承認後**。
PHASE_BASE = `3d0354c`（phase 10 の最終コミット）/ 対象 = `keyseq/` の変更 **16 ファイル・+1658 行**。

## 判定の要約

| 記号 | 結果 | 根拠 |
|---|---|---|
| M1（600 行超 かつ +100 行） | 非該当 | 最大は `config_service/__init__.py` **828 行**だが増分は **+61**。新規モジュールは最大 310 行 |
| M2（80 行超の関数の新規発生） | 非該当 | 新規・大幅変更関数に 80 行超なし |
| M3（同型ブロック 3 個目以降） | **該当**（ただし**候補送り**） | 下記「提案書に含めない項目」参照 |
| M4（列挙型ボイラープレート増） | 非該当 | 増加なし |
| M5（申し送りコメント） | 非該当 | `keyseq/` 配下に該当行なし |
| M6（既存定数と同値の直値） | **該当** | 項目 1 |

## 項目 0（先行）: 安全網の確認

**目的**: 項目 1 が挙動を変えていないことを既存テストで検出できるか確認する。

- 確認対象: `tests/test_orphan_scan.py` / `tests/test_quarantine_manage.py`
  （候補側 4 ディレクトリの分類・復元先ガードの両方を突くテストがあるか）。
- カバーしていない場合は、**特性テストの追加を項目 1 より先に行う**。
- 実行コマンド（`.venv` 必須）:

```
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests
..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui
..\..\..\.venv\Scripts\python.exe -m tests.smoke_app
```

- 期待: `tests` **413**（skip 7）/ `tests_ui` **288** / `SMOKE OK`（本提案の実施前後で不変）。

## 項目 1（M6）: 候補側ディレクトリ 4 値の単一定義化

- **対象**: `keyseq/application/config_service/orphan_scan.py:20-25`（`_CANDIDATE_SPECS`）/
  `keyseq/application/config_service/quarantine_manage.py:22-25`（`_CANDIDATE_DIRS`）
- **何が問題か（M6）**: **同じ 4 つのディレクトリ表記**
  （`user/keymaps` / `user/trigger_sets` / `user/sequences` / `user/hotkey_presets`）が
  **2 モジュールで独立にハードコード**されている（`quarantine_manage.py` は `orphan_scan` を import していない）。
  候補側ディレクトリは**孤児判定の対象範囲**であると同時に**復元先ガードの許可範囲**でもあり、
  **片方だけ変えると「隔離はできるが復元できない」ズレ**が生まれる。
  正本 `data_schema.md` §5.8.9 は両者を同じ 4 種として規定している。
- **どう変えるか**（挙動不変）:

```python
# 変更前: orphan_scan.py
_CANDIDATE_SPECS = (
    (KIND_KEYMAP, "user/keymaps", "mappings", dict),
    ...
)
# 変更前: quarantine_manage.py
_CANDIDATE_DIRS = ("user/keymaps", "user/trigger_sets", "user/sequences", "user/hotkey_presets")

# 変更後: 定義を 1 箇所に置き、両者がそこを参照する
#   （置き場は path_boundary.py と同じ「兄弟が共有する小さなモジュール」方式。
#    `_RESERVED_DIR = "user/hotkey_presets/global"` も同じ場所へ寄せる）
CANDIDATE_DIRS = ("user/keymaps", "user/trigger_sets", "user/sequences", "user/hotkey_presets")
RESERVED_DIR = "user/hotkey_presets/global"
```

- **配置の判断**（`file_organization_rules.md`）: 利用箇所が `orphan_scan` / `quarantine_manage` の
  2 モジュール = **Feature Shared** 相当。`config_service/` 直下に**内容を表す名前**の小さなモジュールを
  置く（`utils` / `helper` などの雑多名は禁止）。**`__init__.py` には置かない**（1 行委譲のみの方針・828 行）。
  **`orphan_scan` から直接 import する形は取らない**（`quarantine.py` → `orphan_scan` の import があり、
  依存の向きが読みにくくなるため）。
- **完了条件**: 上記コマンドが件数不変で pass。`grep -n "user/keymaps" keyseq/` の結果が
  **新モジュール 1 箇所のみ**になる。
- **リスクと戻し方**: 低。定数の移動のみで挙動に触れない。戻しは 1 コミットの revert。
- **依存**: なし。ただし [idea_14](../backlog/idea_14_config_service_public_surface.md)（公開面モジュールへの
  定数・結果型の集約）を先に実施するなら、**その公開面モジュールを置き場にして本項目を吸収できる**。

## 提案書に含めない項目（判定は該当だが候補送り）

- **M3: ダイアログの同型スケルトン**（`Toplevel` + `suspend_hook_for_dialog` / Escape bind /
  `protocol(WM_DELETE_WINDOW)` / `transient` + `grab_set` / `destroy` override）。
  本フェーズで `orphan_sweep_dialog.py` / `quarantine_manage_dialog.py` の 2 コピーが増えたが、
  **同じ形は 9 ダイアログ中 8 ファイルに広がる既存パターン**であり、統一するとフェーズ外の
  6 ファイルへ手が入る（`/refactor_check` の禁止事項「フェーズで触っていないコードを提案書に含めない」）。
  → `current.md` の「別タスク化候補」へ送る。**[idea_10](../backlog/idea_10_nested_modal_grab_restore.md)
  （ネストしたモーダルの grab 復元）と同じ領域**なので、着手するなら合流させる。
- **M3: `config_io` の IO クラス骨格 / `*_text.py` の整形関数の同型**。
  1 個目は phase 10 の `reference_cleanup_io.py` / `reference_cleanup_text.py`（フェーズ外）。
  骨格が薄く、各実装の分岐・文言は独立しているため共通化の利得が小さい。→ 候補送り。
- **M6: `RESTORE_ABORTED_INVALID_ID` と `DELETE_REJECTED_INVALID_ID` が同値**
  （`quarantine_manage.py:14,17` = `"invalid_unit_id"`）。**復元と削除で理由コードの名前空間を
  分ける意図的な設計**で、片方を変えても他方を変える必要はない。→ 対象外。

## 実施タイミング（ユーザー選択）→ **(b) 独立ミニ計画「計画08」で実施・完了（2026-09-08）**

- 項目 0 = **安全網は十分**（既存 2 テストが定数の値に依存）→ 特性テストの追加なし。
- 項目 1 = **完了**。`config_service/candidate_dirs.py`（新規・葉モジュール）へ
  `CANDIDATE_DIRS` / `RESERVED_DIR` を集約し、`orphan_scan.py` は
  `zip(_CANDIDATE_SHAPES, CANDIDATE_DIRS, strict=True)` で対応づける（**添字参照は使わない**）。
  実測 = `tests` **414**（+1）/ `tests_ui` **288** / smoke pass、直値は 1 箇所のみ。
  `reviewer` = **完了可・指摘なし**。
- 候補送り分（ダイアログ / IO / text の同型スケルトン）は `instructions/phase/current.md` の
  「別タスク化候補」で追跡する。**本提案書はこれで役目を終える**。
- 判断の経緯は `.claude_data/state/decisions.md`「計画08」節。
