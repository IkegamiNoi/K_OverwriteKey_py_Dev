# task_05_integration_and_manual_check

## 目的

phase 28 の実装（task_01〜task_04）を**統合確認**し、暫定仕様 22 §8 の受け入れ条件
**1〜10 を確定**させる（11 = 正本反映は task_06）。

- **検証タスク。`keyseq/` ・ `tests_ui/` ・ `tests/` を変更しない**
  （回帰を見つけた場合は修正せず、切り分け結果を報告して枝番タスク `task_05b_*` を起票する）。
- **レイヤ制約**: コード差分を出さない（差分は本タスク定義・`.claude_data/state/` のみ）。
- 実測は **`verifier`**（**Codex に python 実行を依頼しない**）。判定はメインセッションが行う。
- 実機目視は**ユーザーが担当**し、結果をメインセッションへ報告してもらう（§8-8・§8-10）。

## 対象範囲（検証のみ・コード変更なし）

### 1. 統合確認（`verifier` へ委任・§8-7）

`.venv` の python（`..\..\..\.venv\Scripts\python.exe`）で次を実行し、結果の要約のみ受け取る。

1. `python -m compileall -q keyseq` が clean。
2. `python -m unittest discover -s tests` 全 pass（556・skipped 7 から不変）。
3. `python -m unittest discover -s tests_ui` を**連続 3 回**実行し **3 回とも全 pass**
   （502 前後）。**ran / failures / errors / skipped の 4 数値を毎回記録する**。
4. **負荷下の再現確認**（idea_18 の実測条件の再現 = §8-7）:
   **busy loop 4 本を並走させた状態**で、下記 4 クラスを**それぞれ 6 回**実行して fail 0。

   | 対象 | 由来 |
   |---|---|
   | `tests_ui.test_dialog_teardown_flows` | idea_18 の主症状（t2 → 後続 4 件の連鎖） |
   | `tests_ui.test_orphan_sweep_flow` | Escape 分岐 |
   | `tests_ui.test_quarantine_manage_flow` | Escape 分岐 |
   | `tests_ui.test_keymap_set_history_flow` | phase 27 で追加された close 経路 |

   - 負荷の掛け方は `verifier` 側の裁量（別プロセスで CPU を占有する 4 本。
     `.venv` の python で `while True: pass` 相当を起動 → 計測後に必ず終了させる）。
   - **1 回でも fail したら失敗詳細（テスト名・アサート文・診断出力）をそのまま報告する**
     （`escape_delivery.send_escape` は失敗時に `focus_get` 等を出す）。
5. **skip 件数の採取（§8-8）**: 手順 3 の一括実行時に
   `tests_ui/test_dialog_initial_focus.py` の **8 件のうち何件が skip されたか**を
   テスト名つきで報告する（`-v` で採取）。3 回分すべて記録する。
6. `python -m tests.smoke_app` が `SMOKE OK`。
7. `git diff --stat keyseq/ tests/ tests_ui/` が**空**であること（本タスクで触っていない確認）。

### 2. 二次レビュー（phase.md「レビュー方針」・複数タスクを跨ぐ差分）

**`deep-reviewer` と `codex-reviewer` を併用**する（task_01〜task_04 の累積差分 =
`main`〜HEAD を対象。`--base` で phase 28 着手直前のコミットを指定する）。

- `deep-reviewer` の重点観点: 暫定仕様 22 §3.1 の規範（`focus_force` / `lift` を呼ばない・
  二重呼び出しで `focus_set` しない）が守られているか / 群 A・A' の**初期フォーカス先が
  移行前後で同一**か / 群 C の Escape 結線先が §3.5 の表のとおりか /
  **task_04 のヘルパが検証内容を弱めていないか**（skip・アサートの削除）。
- `codex-reviewer` は標準レビュー。**指摘は提示のみ**で、採否はユーザー確認を経る。
- **【裏取り】両レビューの「コードがこうなっている」という事実主張は、採用前に
  `ファイルパス:行` を実測確認する**（`.claude/rules/agent_selection.md`）。

### 3. 完了報告へ載せる資料（§8-2 / §8-6 / §8-8 / §8-10）

- **§8-2 の対応表**: 群 A・A' の 7 経路について「移行前の `focus_set` 対象 widget →
  `grab_modal(focus=...)` へ渡している widget」の対応表（`ファイル:行` つき）。
  **task_01 の差分から作る**（実装をやり直さない）。
- **§8-6 の判定**: Escape 依存テスト 4 箇所について「外す / 残す」の判定と理由。
  task_04 で**全件「残す（ヘルパ経由で実配送のまま）」**と決めているため、その旨と
  **案 A を併用しない理由**を再掲する。
- **§8-8 の skip 件数**（上記 1-5）。**全件 skip だった場合は「実機目視が §8-1 の
  唯一の根拠になる」旨を明記する**。
- **§8-10 のフォーカス復帰の再現結果**（ユーザー報告をそのまま記載）。

### 4. 実機目視の依頼（ユーザー担当・§8-8 / §8-10）

メインセッションは**下記の手順書をユーザーへ提示して結果を待つ**（Claude は実行しない）。
起動は `..\..\..\.venv\Scripts\python.exe -m keyseq`（リポジトリルートで実行）。

> **実施タイミング（v0.5 §2.2-10）: task_05b / task_05c の完了後に 1 回**。
> 群 A（A2）は task_05c の実装が前提のため、それ以前に目視しても不合格になる。
> **統合確認（上記 1）も task_05b / task_05c の完了後に再実行する**（差分が入るため）。

**A. 群 B の 3 ダイアログ（§8-1 の実機根拠）**
「設定」メニューから開き、**ダイアログ内を一切クリックせずに直ちに Escape** を押す。
（クリックするとフォーカスが入ってしまい、欠落を検出できない）

| # | 経路 | 開き方 | 前提 |
|---|---|---|---|
| B1 | 孤児ファイルの棚卸し（`OrphanSweepDialog`） | 設定 → 「孤児ファイルの棚卸し…」 | 構成セットの保存が必要（未保存なら保存を促される） |
| B2 | 隔離の管理（`QuarantineManageDialog`） | 設定 → 「隔離の管理…」 | **隔離された実行単位が 1 件以上必要**（無い場合は情報ダイアログのみで開かない） |
| B3 | 参照元の掃除（`ReferenceCleanupDialog`） | 設定 → 「参照元を掃除…」 | **掃除対象が必要**（無い場合は情報ダイアログのみで開かない） |

- **B2 / B3 が前提不足で開けない場合はその旨を報告する**（無理に条件を作らない）。
  B3 の `ReferenceCleanupDialog` は **B1 の確認ダイアログとしても現れる**ため、
  そちらで代替してもよい（代替した場合は報告に明記）。
- 期待: **Escape だけでダイアログが閉じ、アプリが操作可能なまま残る**。

**A2. 群 A の 4 経路（§8-12・暫定仕様 v0.5 §3.6）**
**前提: task_05b / task_05c の完了後に行う**（それ以前は Escape が未結線で確認できない）。

| # | 経路 | 開き方 | 確認 |
|---|---|---|---|
| A2-1 | `ActionDialog` | 割り当ての編集（アクション追加/編集） | ①通常時に **Escape で閉じる** ②「キー入力で記録」中に Escape → **記録が止まるだけで窓は残る** ③続けてもう一度 Escape → **閉じる** |
| A2-2 | `TriggerDialog` | トリガーの追加/編集 | ①通常時 Escape で閉じる ②「キー入力で取得」中に Escape → **取得が止まるだけで窓は残る** ③再度 Escape で閉じる |
| A2-3 | `KeymapEditDialog` | キーマップの編集 | A2-2 と同じ 3 点 |
| A2-4 | `PresetDialog` | プリセットの追加/編集 | 通常時 Escape で閉じる（Esc の別用途なし） |

- **いずれも保存されずに閉じる（キャンセル相当）こと**を確認する。
- ②で窓が閉じてしまったら**不合格**（§3.6 の規範違反）。その場合は報告して実装へ差し戻す。

**B. 群 C の Escape（§8-9 の実機確認・任意）**
テストで固定済みのため**任意**。行う場合は「別名で保存…」（子ファイルの保存）/
「レイアウトを削除…」/「プリセット編集…」のいずれかで Escape を押し、
**保存されずに閉じる**ことを確認する。

**C. フォーカス復帰の再現確認（§8-10・スコープ外の調査）**
本フェーズでは**直さない**。再現の有無だけを報告してもらう。

1. 外側ダイアログ → 内側ダイアログを開く → **内側を閉じた後**、外側で Escape が効くか。
2. 外側ダイアログを開いた状態でアプリを**最小化 → 復帰**した後、Escape が効くか。

→ **再現したら `/idea` で起票する**（本タスクの範囲内。修正はしない）。

### 設計メモ / 制約

- 本タスクで**コードを直さない**。回帰・レビュー指摘が出た場合は
  「切り分け結果 + 推奨対応」をユーザーへ提示し、判断を仰ぐ（修正は枝番タスク）。
- `tests_ui/test_dialog_initial_focus.py` の `_require_app_focus` が
  **後続クラスへ影響していないか**の判断は本タスクで行う（task_04「含まない」からの引き継ぎ）。
  手順 1-3 が 3 回とも green なら**影響なしと判定してよい**。
- 実機目視は**ユーザーの操作結果が正**。Claude が代理で「たぶん動く」と補完しない。

## 読むファイル

- `instructions/history/22_dialog_keyboard_focus.md` の **§8（受け入れ条件 11 件）/ §3.5 / §5**
- `instructions/phase/28_dialog_keyboard_focus/phase.md`（レビュー方針・タスク境界）
- `tests_ui/test_dialog_initial_focus.py:40-120`（skip ガードと 8 件の内訳）
- `tests_ui/escape_delivery.py`（失敗時の診断出力の形）
- `keyseq/presentation/views/menu_bar.py:25-32`（群 B の開き方 = 実機手順書の裏取り）
- 群 A・A' の対応表を作るための **task_01 のコミット差分**（`git show 08ace46 -- keyseq/`）

## 含まない

- **コードの修正**（`keyseq/` ・ `tests/` ・ `tests_ui/`）。必要になったら `task_05b_*` を起票。
- **正本反映**（`features.md` 2 条項 + `codebase_map.md` 署名更新・件数訂正）= **task_06**。
- **暫定仕様 22 の凍結 / `decisions_archive/28` 作成 / `current.md` 更新 /
  idea の `INDEX_done.md` 移動** = **task_06**。
- **フォーカス復帰の修正**（§11 スコープ外。再現したら idea 起票のみ）。
- `/refactor_check` の実行（task_06 = フェーズ最終タスク）。
- 同型スケルトンの共通化（別タスク化候補のまま）。

## 確認

`.venv` の python を使う（`..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

1. `python -m compileall -q keyseq` clean。
2. `python -m unittest discover -s tests` 全 pass（556・skipped 7）。
3. `python -m unittest discover -s tests_ui` **連続 3 回すべて全 pass**（数値を 3 回分記録）。
4. 負荷下（busy loop 4 本）で 4 クラスを**各 6 回**実行し **fail 0**。
5. `tests_ui/test_dialog_initial_focus.py` の skip 件数を 3 回分記録（テスト名つき）。
6. `python -m tests.smoke_app` が `SMOKE OK`。
7. `git diff --stat keyseq/ tests/ tests_ui/` が空。
8. `deep-reviewer` ・ `codex-reviewer` の指摘を裏取りし、**採用 / 修正して採用 / 保留 / 除外** で整理。
9. ユーザーの実機目視結果（A・C。B は任意）を受領。

## 完了条件

- 確認 1〜7 が pass。**3 または 4 で 1 回でも落ちたら完了にしない**（切り分けて再判定）。
- **二次レビュー（`deep-reviewer` + `codex-reviewer`）を実施し、判定を完了報告に記載**
  （CLAUDE.md「レビュー（必須）」の統合時の運用形）。
- **task_05b / task_05c が完了していること**（本タスクの完了判定はそれらの後。v0.5 §2.2-10）。
  確認 1〜7 は**両タスクの差分が入った状態で再実行**した結果で判定する。
- **ユーザーの実機目視（A・A2）の結果を受領**し、次を確認する:
  - **A**: 群 B の 3 ダイアログが Escape で閉じる。前提不足で開けなかった経路はその旨を明記する。
  - **A2**: 群 A の 4 経路が通常時 Escape で閉じ、**記録中 / 取得中は停止のみで窓が残る**（§8-12）。
    **1 件でも②で閉じてしまったら完了にしない**（§3.6 の規範違反として差し戻す）。
- **§8-2 の対応表 / §8-6 の判定 / §8-8 の skip 件数 / §8-10 の再現結果 /
  §8-12・§8-13 の検証結果**を完了報告に載せる。
- **実機目視は本タスクで実施**（task_06 へ持ち越さない）。§8-10 が再現した場合は idea 起票まで行う。
