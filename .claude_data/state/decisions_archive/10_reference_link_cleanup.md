# decisions_archive: 10_reference_link_cleanup

> phase 10（参照元の掃除）の判断履歴。**2026-09-05 完了**。
> 正本は `spec_detail/data_schema.md` **§5.8.1**（参照元記録 + **参照元の掃除**〔検査範囲と既知の制約 /
> 保護対象 / 全件除去は `[]` / 孤児は警告のみ / 未保存時は先に保存 / 除去直前の読み直し / 冪等 /
> runtime へ反映しない〕）+ **§5.8.4**（`None` と `[]` はいずれも「所有元不明」で判定は不変）
> + `spec_detail/features.md` §4.6（設定メニューの項目）、および `codebase_map.md`。
> 暫定仕様 09（`instructions/history/09_reference_link_cleanup.md`・**v0.5**）は**凍結済**（経緯の参照用）。
> 起票元 idea_07 はクローズ（`instructions/backlog/INDEX_done.md`）。
> **後続**: [idea_12](../../../instructions/backlog/idea_12_orphan_child_file_sweep.md)
> （全走査 + 孤児候補の逆方向検査。**前提 = phase 10 の完了 → 充足**）。

---

規範: [phase.md](../../../instructions/phase/10_reference_link_cleanup/phase.md) /
主入力 = 暫定仕様 09（`instructions/history/09_reference_link_cleanup.md`・**最終 v0.5**）。**暫定仕様先行モード**。

### 【起票時】idea_07 の昇格と設計確定（ユーザー確定 2026-08-16）
- **検査範囲 = 現在の構成セットの子のみ**（ユーザー判断）。根拠 = ①**子は config 外にも置ける**ため
  ディレクトリ走査でも**全網羅にならない** ②**keymap_set の列挙手段が無い**
  （`keyseq/` に `os.listdir` / `glob` / `os.walk` が 1 箇所も無い）③目的は
  「実際に使っているものが余計な処理を抱えないようにする」こと。
- **孤児削除は行わず警告表示のみ**（v0.1 で「削除も選べる」と確定したが**差し戻して再判断**）。
  理由 = **この検査範囲では孤児判定が原理的に成立しない**（対象は現在のセットの索引に載っている＝使用中。
  かつ `_parent_refs` は best-effort で「どこからも参照されない」証明にならない。
  **sequence の親は trigger_set** なので trigger_set 未保存なら使用中の sequence の参照元が全滅する）。
  → 孤児検出には**逆方向検査**が要るため **[idea_12](../../../instructions/backlog/idea_12_orphan_child_file_sweep.md) へ分離**
  （ユーザー方針: **全検査と現在のセットのみを段階的に両方作る**）。
- **確認 UI は 1 枚**（読み取り専用の一覧 + 実行 / キャンセル）。削除を外して**非破壊・冪等**になったため
  行ごとの取捨選択は設けない。**消える参照元のパスは全件提示**する。
- `deep-reviewer`（起票時）= **修正要** → v0.2 で反映。**最大の指摘 = 子の列挙を
  `resolve_child_save_targets` にしていたのは誤り**（「次に保存するとしたらどこへ書くか」であり、
  **未実体化の子へ既定パスが割り当てられて無関係な既存ファイルを書き換える**）→
  **runtime の source_path 3 種**へ訂正。ほかに依存方向の逆流是正 / **現在の上位への参照は除去しない** /
  **消えるパスの全件提示** / 目的と受入条件を検証可能な形へ。
- `codex-adversarial-reviewer`（確定前）= **needs-attention（High 3）** → v0.4 で**全件反映**:
  ①**保護対象を検査時点で分離**（実行では残すのに UI が「消える」と出す乖離を解消）
  ②**未保存セットでは先に保存を確認**（`parent_ref` が空だと `_parent_refs_for_save` が
  保存先を読み直さず、**個別保存で掃除前の refs が再書き込みされて巻き戻る**。**ユーザー案を採用**）
  ③**除去直前に JSON 全体を読み直す**（全体置換なので確認中の外部変更を消し得る。
  版情報の照合までは行わず、残る窓は §5.8.3 / §5.10.3 と同水準の既知の性質として除外）。
- `reviewer`（phase.md の整合確認）= **修正して採用**。指摘 1 件（`current.md`「次フェーズ候補」の
  idea_07 行が着手済みに追従しておらず**文書が自己矛盾**）を反映。

### 【task_01】完了（2026-08-16）= 検査ロジック（application 新規モジュール）
- `config_service/parent_refs_cleanup.py` を**兄弟モジュール**として新設（`service` を第 1 引数に取る /
  `__init__` を import しない / **`__init__.py` へ委譲を足さない**＝737 行で分割保留中のため）。
- 公開面 = 判定名 4 定数 + 凍結データクラス `ParentRefsCleanupInspection`
  （`kind` / `stored_path` / `alive_refs` / `stale_refs` / `protected_refs` / `state`）+
  `inspect_parent_refs(service, runtime, *, config_root, keymap_set_path)`。
  **表示都合を持たせない**（行モデルは presentation 側）。
- 規則: **列挙は source_path 3 種のみ**（`resolve_child_save_targets` 不使用）/
  **keymap → trigger_set → sequence** の順で固定 / **`canonical_path` で重複排除（先着優先）** /
  **保護対象は実在しなくても `protected_refs` へ** / 判定名は優先順の表どおり
  （**stale + protected で alive 無しは `ALL_STALE` ではなく `TARGET`**）/
  戻り値から `CLEANUP_SKIP` を除外。
- 実測: compile clean / `tests` **247**（238 → **+9**・追加テスト数と一致）/ `tests_ui` **229**（不変）/
  smoke pass / **既存ファイルの変更 0 件** / **`user/` の誤生成なし**。
- `reviewer` = **完了可（指摘なし）**。特に **`os.path.exists` が解決後のパスにのみ適用**され、
  **`canonical_path` の値が保存値・戻り値へ混入していない**こと、
  **`stored_path` と各 refs が記録表記のまま**返ることを確認
  （Codex が自己申告した「過剰な正規化」は実際には入っておらず、テストの弱化も無し）。

### 【task_02】完了（2026-08-16）= 除去 API（`prune_parent_refs`）
- 同モジュールへ追加: `prune_parent_refs(service, inspections, *, runtime, config_root, keymap_set_path)`
  + 凍結データクラス `ParentRefsPruneResult`（更新したファイル / 失敗したファイル）
  + 失敗理由の定数 3 種（`PRUNE_FAILURE_UNREADABLE` / `_INVALID_DATA` / `_SAVE_FAILED`。
  **表示文言は持たせない**＝文言は task_03）。
- **判定は task_01 と共用**（`_classify_parent_refs` へ抽出）。**二重実装しない**のが要件
  （検査と実行で食い違うと UI の表示と結果が乖離するため）。
  **抽出は機械的で検査側の挙動は不変**（`reviewer` が diff の削除行と現在のコードで突き合わせ確認・
  task_01 の 9 テストも 1 件も削除 / 弱体化されていない）。
- 規則: **除去直前に JSON を丸ごと読み直す**（検査時のスナップショットを書き戻さない＝
  **全体置換で外部変更を消さない**）/ **`None`・非 dict は書かずに失敗記録** /
  **読み直した内容で判定をやり直す** / 残すのは**実在 + 保護対象**（記録順・記録表記のまま）/
  **除去 0 件なら書かない（冪等）** / **全件除去時は `[]`（キーは残す）** /
  **`_parent_refs` 以外を変えない** / **1 件の失敗で全体を止めない** / **runtime 不変**。
- 実測: compile clean / `tests` **257**（247 → **+10**・追加テスト数と一致）/ `tests_ui` **229**（不変）/
  smoke pass / 変更は 2 ファイルのみ / `user/` の誤生成なし。
- `reviewer` = **完了可**。参考指摘 1 件（refs に重複文字列があると `not in` で両方消え得るが、
  `_normalize_parent_refs` が読み込み時に重複除去するため**発生しない**）。

### 【task_03】完了（2026-08-16）= 提示テキストの整形（presentation の純関数）
- `keyseq/presentation/reference_cleanup_text.py`（新規）: `CLEANUP_EMPTY_MESSAGE` +
  `format_cleanup_plan(inspections)` / `format_cleanup_result(result)`。**戻り値は行のタプル**
  （結合・描画はダイアログ側＝task_04）。
- **配置の判断**: `presentation/dialogs/` ではなく **presentation 直下**へ置いた。
  `dialogs/__init__.py` が全ダイアログを import する＝**`tkinter` と `pynput` を巻き込む**ため、
  そこへ置くと `tests/` から純関数だけをテストできなくなる。
  `file_organization_rules.md` の「所有者の近くに置く」より**テスト可能性を優先**した
  （`child_save_rows.py` と同じ「純モジュール」の位置づけ）。
- 規則: **消える参照元は全件列挙**（省略・「ほか N 件」への丸めをしない＝**到達不能な媒体の参照元を
  消す事故に気づけるようにする**）/ **保護対象は「残す」側にだけ出す**（消える側に混ぜると
  実行結果と食い違う）/ **`CLEANUP_ALL_STALE` にだけ警告**（0 件になる・**子ファイルは削除しない**・
  **孤児判定はこの範囲ではできない**）/ **失敗理由の定数 → 文言の変換はこの層の責務** /
  **判定名で分岐し表示文言で分岐しない**。
- 実測: compile clean / `tests` **264**（257 → **+7**）/ `tests_ui` **229**（不変）/ smoke pass /
  **`tkinter` 非依存を実証**（`sys.modules['tkinter']=None` でも import 成功・grep ヒット 0）/
  既存ファイルの変更 0 件。
- `reviewer` = **修正して採用**。指摘 1 件（**`sequence` の表示名が「シーケンス」で、既存の
  `child_save_dialog._kind_label` と正本の用語「出力シーケンス」と不一致**）を
  **メインが修正**（実装・テストとも）。再実測で 264 pass（件数不変）を確認。

### 【task_04】完了（2026-08-16）= UI 配線（メニュー / 確認ダイアログ / 保存確認導線）
- 新規 3: `controllers/config_io/reference_cleanup_io.py`（`ReferenceCleanupIo.run_cleanup` = フローのみ）/
  `dialogs/reference_cleanup_dialog.py`（`tk.Toplevel` 継承・`destroy()` override で resume・
  **読み取り専用の一覧 + 実行 / キャンセル**・**`result` の既定は `False`**）/
  `tests_ui/test_reference_cleanup_flow.py`（7 本）。
  既存 4 ファイルは **+7 / -1**（`config_service/__init__.py` の**委譲 2 本** /
  `app.py` の配線 / `dialogs/__init__.py` の再輸出 / `menu_bar.py` の「設定」メニュー 1 行）。
- **フローの分岐**: 未保存（**`keymap_set_path` が空**。dirty ではない）→ 保存確認 →
  **いいえ / 保存失敗なら検査もせず終了** → 検査 → **0 件なら一覧を出さず通知** →
  確認ダイアログ → **キャンセルなら何も書かない** → 除去 → 結果通知。
  **runtime・dirty は不変**。**`ReferenceCleanupIo` はロジックを持たない**
  （検査・除去は application の委譲 / 文言は `reference_cleanup_text` の純関数）。
- **実測で 1 件 fail → テスト側の誤りと判明**: メニュー配線のテストが
  `menubar.entrycget(1, ...)` を「設定」と決め打ちしていたが、**top-level menubar の tearoff**で
  `0=tearoff / 1=ファイル / 2=設定` とずれていた。production の配線は正しく、
  **メインがテストを「カスケードとラベルで探す」形へ修正**（`_invoke_menu_command`）。
  → **今後メニュー項目のテストを書くときはインデックスを固定しない**。
- 実測: compile clean / `tests` **264**（不変）/ `tests_ui` **236**（229 → **+7**・ハングなし）/ smoke pass /
  `user/` の誤生成なし。`config_io/__init__.py` の `M` は**改行コードのみで内容差分ゼロ**。
- `reviewer` = **完了可**。参考指摘（委譲 2 本が 1 行スタイルで前後と不揃い）は**メインが整形**し再実測。
- **【運用】`reviewer` が 1 度セッション上限で中断**したため再実行して回収した。

### 【task_05】通し確認と 2 本立てレビュー（2026-08-16・**実機目視は未実施**）
- **通し実測**: compile clean / `tests` **267** / `tests_ui` **238**（ハングなし）/ smoke pass /
  `user/` の誤生成なし。phase 10 の実装差分は **11 ファイル・+1403 / -1**。
  新規 production 4 ファイルは **262 / 70 / 49 / 58 行**。
  `config_service/__init__.py` は **767 行**（phase 09 の 737 → **+30**。task_06 の `/refactor_check` 対象）。
- **`deep-reviewer` = 修正要**。採否:
  - **H1 = 修正して採用**: 受入条件 12 が「**特性テストで固定する**」と明記しているのに
    **「共有中 → 単独所有」のテストが 1 本も無かった**（本機能の目的そのもの）→ 追加。
  - **H2 / H9 / H12 = 修正して採用**: **実行後**の runtime・dirty 不変（従来はキャンセル経路のみ）/
    **`ConfigService` の委譲 2 本が全テストで未実行**（引数取り違えを検出できない）/
    メニューテストが共有 App の menubar を復元しない → いずれもテスト側で解消。
  - **H5 = 採用（目視項目を追加）**: フックの suspend / resume の対を確認する経路が
    **自動テストにも目視表にも無かった**（4 経路を項目 4b として追加）。
  - **H3 = 修正して採用（ユーザー確定）**: **保護対象だけの子が「対象」に数えられ、
    書き込みゼロなのにダイアログが出る** → **件数から外し、消える参照元が 0 件なら一覧を出さない**（v0.5）。
  - **H4 / H6 / H7 = 仕様へ明記（実装は変えない・ユーザー確定）**: sequence の巻き戻り前提 /
    確認中に上位が消えた場合 / 再判定で対象外になった子の通知 → **§3-5 既知の制約**として追記。
  - **H8 / H10 / H11 / H13 / H14 = task_06 送り・参考**。
- **`codex-adversarial-reviewer` = needs-attention（High 1）**。
  「**保存失敗時に 1 ファイルも書かれない保証が成立しない**」（保存は非トランザクションで、
  子を書いた後に失敗し得る）→ **条文を限定して決着（ユーザー確定）**。
  指摘の観察自体は正しいが、**当たり先は既存の保存フロー**であり、正本 **§5.8.6 が best-effort と明記**、
  暫定仕様 §6 も「保存経路を変更しない」をスコープ外に置いている。
  本フェーズが保証するのは「**掃除による書き込みが 1 件も発生しない**」ことなので、
  **受入条件 5b と §3-5 をその形へ限定**した（保存失敗で `prune` を呼ばないことは既にテスト済み）。
- **【運用・重要】Codex が並行してメインの仕様書編集を差し戻した**。
  委任中にメイン側で `instructions/history/09_*.md` を編集していたところ、Codex が
  「範囲外の差分」と判断して**巻き戻していた**（v0.5 の記述が消えた）。
  → **委任の実行中は、対象外であってもメイン側で同時に文書を編集しない**。
  編集した場合は**委任完了後に必ず差分を確認する**（今回は grep で消失に気付いて書き直した）。

### 【task_05】完了（2026-09-05）= 実機目視 14 項目すべて OK
- ユーザーが §3 の表 **14 項目を実機で実施し全項目 OK**（不具合なし・**是正なし・コード変更なし**）。
  重点項目（7 = 保護対象 / 9〜11 = 未保存時の保存確認導線 3 経路 / 13 = 保護対象だけの子は一覧を出さない〔v0.5〕/
  4b = フックの suspend / resume 4 経路）も期待どおり。
- 受入条件 **1〜15 のすべて**を自動テストまたは実機目視で充足確認 → **task_05 完了**。
  結果は `tasks/task_05_integration_check.md` 末尾へ追記。
- 残るは **task_06 = 正本反映（最終）**。

### 【task_06】完了（2026-09-05）= 正本反映（最終）

- **正本へ昇格**: `data_schema.md` **§5.8.1 改訂**（「掃除は後続課題」を本機能の記述へ差し替え /
  「追加のみ」への例外 / 検査範囲の既知の制約〔全網羅でない〕/ 保護対象 / 全件除去は `[]` /
  孤児は 0 件警告のみ / 未保存時は先に保存 / 除去直前の読み直し / 冪等 / runtime へ反映しない /
  **§3-5 の既知の制約 3 件**）+ `features.md` §4.6（設定メニュー 1 行）+ `codebase_map.md`
  （新規 4 ファイル + ConfigService 表を 5 → 6 ファイル + 設計の芯 3 点）。
- **§5.8.4 は無改訂**と判断（判定表が既に「`_parent_refs` が無い / 空 → 所有元不明」を規定しており、
  `None` と `[]` で判定が変わらない旨は **§5.8.1 側に明記**したため。不要な改訂をしない）。
- 暫定仕様 09（v0.5）を**凍結**。idea_07 を `INDEX_done.md` へ移動。`current.md` を完了更新
  （**次採番 = phase 11 / 暫定仕様 10**。idea_12 の前提〔phase 10 完了〕**充足**）。
- **回帰確認**（`verifier` 実測・文書のみの変更のため参考値）: compile clean / `tests` **267** /
  `tests_ui` **238**（ハングなし）/ smoke pass / `user/` の誤生成なし。
  差分は**文書のみ**（`keyseq/` `tests/` `tests_ui/` に差分なし）。

### `/refactor_check` 判定（2026-09-05）= **不要**

- 対象 = `2b12ef8..HEAD` の `keyseq/` **8 ファイル**（+485 / -1。新規 4 / 既存 4 は計 +36 / -1）。
- **M1 非該当**: `config_service/__init__.py` は **767 行**で 600 行超だが**増分 +32**（閾値は
  「600 行超 **かつ** +100 行以上」）。phase 09 で M1 該当・分割保留中の状態は変わらず、
  `current.md` の「別タスク化候補」で追跡を継続する。
- **M2 / M3 / M4 / M5 非該当**: 80 行超の関数なし（最大 `_inspect_child` 46 行）/
  `config_io` の `except Exception → showerror → return False` は **6 箇所で増減 0**
  （新規 `reference_cleanup_io.py` はこの型を含まない）/ 子カテゴリ列挙の使用ファイル数は **8 で不変** /
  申し送りコメントの新規追加は **0 件**。
- **M6 = 既知として抑止**: 新規 2 ファイル（`parent_refs_cleanup.py` / `reference_cleanup_text.py`）が
  `save_plan.CHILD_*` を import せず**同値の文字列直値**を使う。これは `current.md`
  「別タスク化候補」の**子カテゴリ列挙（Phase β の候補送り）**がカバーする既知領域のため提案書へ含めない。
  **境界事例の定性材料も 2 つとも非該当**（責務のまとまりは検査 / 除去の 2 つ・対象箇所は一言で説明できる）
  → **「不要」に倒し、`current.md` へ 1 行追記**して次フェーズ以降の再判定に委ねた。
- **提案書は作成しない**（`modified_proposal/` の次採番は **`08_<topic>`** のまま）。

