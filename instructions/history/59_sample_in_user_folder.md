# 暫定仕様 59: サンプルを config/user/ へ書き出す（sample_in_user_folder）

> 状態: **凍結（2026-11-23・phase 77 task_03・正本反映済）**。正本へ昇格済み: `data_schema.md` §5.14「書き出し」/ `data_schema/5_08_09_orphan_sweep.md` 経路 5 / `features.md` §Welcome「起動の流れ」と失敗時の扱い / `codebase_map.md`。**以後は正本が正**（本書の条項を実装の根拠に引かない）。本書は経緯記録として凍結。昇格時の補い: task_02 の採否（衝突時も標準の空フォルダはできる = 受容・リンク切れのシンボリックリンクも衝突 = task_02a）と完了判定前レビューの採否（構成セット本体のリンク切れも incomplete・false と 0 を区別 = task_03a・リンクで組んだ構成は扱わない・既存の構成セットの照合はキーマップ・トリガー一覧・出力シーケンスのみ）を正本へ反映
> 起票元: ユーザー要望（2026-11-23・サンプルを `config/sample/` に置くため、別名保存・読込の案内先が `config/user/` にならず不便）。
> 番号対応: phase 77 / 暫定 59 / decisions 77。
> 経緯: v0.2 = Codex 敵対的レビューの指摘 5 件の採否を反映（ユーザー 2026-11-23）/ v0.1 = 起票。

---

## §1 目的 / 背景

初回の「サンプル入りで始める」で書き出すサンプルを `config/sample/` ではなく `config/user/` へ書き出し、
保存・読込のダイアログが普段どおり `config/user/` の各フォルダを案内するようにする。

### 現状監査（2026-11-23）

- 書き出し先: `keyseq/application/config_service/sample_install.py:18-19`（`SAMPLE_DIR = "sample"`・`sample/keymap_sets/sample.json`）・`:41`・`:51`（子のパス）・`:71`（`split_base_dir`）
- 書き出しの順: 子（出力シーケンス → トリガー一覧 → キーマップ）→ 構成セット（`save_plan_execution.py:134-152`）。各ファイルは一時ファイル + `os.replace`（`json_repository.py:13-20`）
- 起動設定に書く構成セット: `keyseq/presentation/app.py:405`（`"sample/keymap_sets/sample.json"`）
- 孤児の掃除の参照元: `keyseq/application/config_service/orphan_scan.py:107-108`（正本 `data_schema/5_08_09_orphan_sweep.md` の経路 5）。候補側は `config/user/` の既定 4 フォルダの直下のみ（同節「候補側」）
- ダイアログの初期フォルダは「今開いている構成セット / 子のフォルダ」が最優先（`keyseq/presentation/config_paths.py:82-92`・`:100-113`）。そのため、サンプルを開いている間はどの操作でも `config/sample/` に案内される
- 「サンプル設定に戻す」はファイルを読まず、コードの既定データから作る（`features.md` §Welcome「サンプル設定に戻す / 新規作成」）。`config/sample/` は初回の読込用の書き出し先でしかない
- 正本: `data_schema.md` §5.14「書き出し」・`data_schema/5_08_09_orphan_sweep.md` 経路 5・`features.md` §Welcome「起動の流れ」とその下の失敗時の扱い
- テスト: `tests/test_sample_install.py`（`:175-196` = 構成セットの書き込みの失敗後に再試行できる）・`tests/test_orphan_scan.py:111-121`（旧サンプルの構成セットが `user/` の子を参照として守り、`sample/` を候補にしない）・`tests_ui/test_first_launch_flow.py:83`

## §2 確定事項（ユーザー 2026-11-23）

- **書き出し先を `config/user/` にする**（下位フォルダの並び・英語の固定ファイル名は今のまま）。
  構成セット = `user/keymap_sets/sample.json`、子 = `user/keymaps/` ・ `user/trigger_sets/` ・ `user/sequences/` の
  `shortcuts.json` / `right_hand.json` / `numpad.json` / `select_line.json` 等（今の名前のまま）
- **既存の `config/sample/` は移行しない**（ファイルを動かさない・書かない・起動設定の `keymap_set_path` も書き換えない）。
  旧サンプルを使っている利用者は、構成セットや子を別名保存したものから `config/user/` に移る（§3.4）
- **同じ名前の子が既にあれば書かない**（§3.2・旧 確認事項 1 = 案 A）
- **孤児の掃除の参照元 `config/sample/keymap_sets/`（経路 5）は残す**（§3.3・旧 確認事項 2 = 案 A）
- 暫定仕様先行モードで進める

## §3 設計

### §3.1 書き出し

- 書き出し先の基準を `config/user/` にする（`split_base_dir` は絶対パスの `config/user/`・参照に書くパスは今までどおり `config/` 基準の相対）。
  子 → 構成セットの順・`write_startup_entry=False` は今のまま
- 起動設定（`config.json`）に書く構成セットは `user/keymap_sets/sample.json`
- 構成セット `user/keymap_sets/sample.json` が既にあるときは今のまま: 書かずに、辿れる全ファイルがそろって読めるかを確かめ、
  そろっていれば読む / 欠けていれば手を付けず警告して空で始める
  - 利用者が自分で作った同名の構成セットでも、そろっていればそれを開く（**受容**。開くのは利用者自身の構成で、壊さない。サンプルかどうかの識別はしない）

### §3.2 構成セットが無いときの同名の子（衝突）

- 書き出す前に、**書き出す全ての子のパス**（出力シーケンス 7・トリガー一覧 3・キーマップ 3）を確かめる
- 既にあるファイルのうち、**中身（読んだ JSON）が今回書き出すものと同じもの**は衝突にしない（そのまま書いてよい）。
  前回の書き出しが途中で失敗して残った子で、再試行を止めないため
- 中身が違うファイル（読めない・JSON でないものを含む）が **1 つでもあれば、何も書かずに**、今の「欠けている」と同じ警告を出して空で始める
  - 前回と違う言語で再試行したときもラベルが違うので衝突になる（**受容**）
- 確かめてから書き終えるまでの間に別のプロセスが同じファイルを書く場合は考えない（**除外**。初回起動の一瞬で、利用者は 1 人）

### §3.3 孤児の掃除

- 参照元の経路 5（`config/sample/keymap_sets/` 直下・参照元としてだけ見る・`config/sample/` の中身は候補にしない）は**残す**。
  旧サンプルを開いたまま子だけ `config/user/` へ別名保存した利用者で、別の構成セットを開いたときにその子が未使用の候補になるのを防ぐ
- 新しいサンプルの構成セットは経路 1（`config/user/keymap_sets/` 直下）で拾われ、その子は参照ありになる

### §3.4 旧サンプル（`config/sample/`）を使っている利用者

- 普段の読込・孤児の掃除の参照読込は今までどおり（読むだけ・書かない・移行しない）
- 構成セットを `config/user/keymap_sets/` へ別名保存しても、**変えていない子は今までの参照先（`config/sample/` 配下）のまま**で、
  その子の保存ダイアログも `config/sample/` 配下を案内する（今までどおり）。子を `config/user/` に移すには、子ごとに保存先を変えて構成を保存する

### §3.5 変えないもの

- JSON スキーマ・サンプルの中身・「サンプル設定に戻す」（ファイルを読まず書かない）・ダイアログの初期フォルダの決め方
- JIS を選んだときの外部レイアウトの登録（`user/keylayout/jis.json`）。サンプルの子のそろい具合の判定には含めない（今まで通り）

## §4 受け入れ条件（ドラフト）

1. 初回にサンプル入りで始めると、`config/user/keymap_sets/sample.json` と子 13 個が `config/user/` の各フォルダにでき、
   `config/sample/` は作られない（§3.1）
2. 起動設定の `keymap_set_path` が `user/keymap_sets/sample.json`。子の参照と JIS の `user/keylayout/jis.json` が `config/` 基準の相対で書かれ、読み直せる（§3.1）
3. 新しく書き出したサンプルを開いた状態の別名保存・読込のダイアログが `config/user/` の各フォルダを案内する（§1・実機目視）
4. 構成セットが既にあるときの今の挙動（そろっていれば読む / 欠けていれば手を付けず空で始める）が保たれる（§3.1）
5. 構成セットが無く、中身の違う同名の子が 1 つでもあると、何も書かずに警告して空で始める。既存の子は変わらない（§3.2・テスト）
6. 構成セットの書き込みだけが失敗した後、再試行で `written` になる（中身が同じ子は衝突にしない・§3.2・テスト）
7. 孤児の掃除で、新しいサンプルの子が参照ありになり、旧サンプルの構成セットが参照する `user/` の子も参照ありのまま（§3.3・テスト）
8. 既存の `config/sample/` に書き込まない（§2）

## §5 スコープ外

- 既存の `config/sample/` の移行・削除（§2）
- ダイアログの初期フォルダの決め方の変更
- サンプルのファイル名の変更（`sample_` を付ける等）
- 既存の構成セットがサンプルかどうかの識別（§3.1 で受容）
- 書き出し中の別プロセスとの競合（§3.2 で除外）

## §6 正本反映（フェーズ末昇格・予定）

- 正本: `data_schema.md` §5.14「書き出し」（書き出し先・同名の子の規則〔「子だけ残っているときは上書きしてよい」を §3.2 へ置き換え〕・利用者の同名の構成セットの受容）/
  `data_schema/5_08_09_orphan_sweep.md` 経路 5（旧サンプル用であることを明記）/
  `features.md` §Welcome「起動の流れ」・失敗時の扱い（`config/sample/` → `config/user/`・衝突時は空で始める）/ `codebase_map.md` の `sample_install.py` の行
- 実装: `keyseq/application/config_service/sample_install.py`・`keyseq/presentation/app.py:405`
- テスト: `tests/test_sample_install.py`・`tests/test_orphan_scan.py`・`tests_ui/test_first_launch_flow.py`

## 関連

- phase 73（Welcome・サンプルの書き出しを導入）: `instructions/phase/73_welcome_first_launch/phase.md`・`decisions_archive/73_welcome_first_launch.md`
- 凍結済み 暫定 56（`56_welcome_first_launch.md`）は経緯のみ（根拠に引かない）
