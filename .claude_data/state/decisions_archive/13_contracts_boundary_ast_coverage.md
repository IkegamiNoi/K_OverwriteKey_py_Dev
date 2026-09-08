# decisions_archive: 13_contracts_boundary_ast_coverage

> phase 13（公開面の逆戻り防止テストの検査範囲の拡張）の判断履歴。**2026-09-08 完了**。
> **テストのみの変更・プロダクション不変・仕様変更なし・実機目視なし**。
> **正本の改訂はしていない**。`spec_detail/architecture.md` **§3.2 の条項は phase 12 で確定済みのまま不変**で、
> 本フェーズは**その条項を守れているかの検査精度を上げただけ**（根拠は下記「正本反映が不要という判断」）。
> **暫定仕様は起こしていない**（直接改訂モード）。
> 起票元 idea_15 はクローズ（`instructions/backlog/INDEX_done.md`）。
> 検出は phase 12 のフェーズ完了レビュー（`deep-reviewer` M-3 / `codex-adversarial-reviewer` medium）。

---

## 2026-09-08 (phase 13: 公開面の逆戻り防止テストの検査範囲の拡張・直接改訂モード)

規範: [`instructions/phase/13_contracts_boundary_ast_coverage/phase.md`](../../../instructions/phase/13_contracts_boundary_ast_coverage/phase.md)。
**暫定仕様なし**。番号対応: **phase 13 / 暫定仕様なし / decisions_archive 13**。
起票元 = [idea_15](../../../instructions/backlog/idea_15_contracts_boundary_ast_coverage.md)。
タスクは **task_01 / task_01b / task_01c / task_02** の 4 本
（**01b と 01c は着手後にユーザー判断で追加した枝番**。いずれもレビューが見つけた同種の穴を塞ぐもの）。

### 【起票時】モードの選択 = **直接改訂モード**（メイン判断・ユーザー承認 2026-09-08）

`.claude/rules/spec_change_workflow.md`「モードの選択」の 3 条件（局所的 / 文言確定済み / タスク 1〜2）を
**すべて満たす**。変更対象は `tests/test_config_service_contracts.py` **1 ファイル**で、
**正本の条項は変更しない**。仕様変更を伴わないため**暫定仕様書は起こさない**。

### 【起票時】idea_15 の案 A を採用（ユーザー確定 2026-09-08）

- **案 A = 検査の強化**（`ast.Attribute` の完全修飾名解決 + `asname` 追跡）。
- **案 B = 限界記述の正確化のみ**は不採用（規約とレビューだけに依存させない）。
- phase 12 の暫定仕様 11 は**凍結済のため後追い改訂しない**。判断は本アーカイブへ集約する。

### 【起票時】期待値の確定（メイン判断）

- **テストメソッド数は 3 本のまま**（既存メソッドへケースを足す）＝ **`tests` の件数は 417 のまま**。
- **現在の `keyseq/presentation/` は違反 0 件**なので、拡張後も**全テストが pass する**のが前提。
  落ちた場合は**誤検出**を先に疑う。
- **`keyseq/` の差分 0 行**。

### 【task_01】完全修飾・エイリアス経路の検査（`reviewer` = 修正要 → 是正済）

- **A-2 エイリアス表**: `Import` / `ImportFrom` を先に走査し**束縛名 → 完全修飾モジュール名**の表を作る
  （**`import a.b.c` は先頭 `a` だけを束縛する**点を正しく扱う）。
- **A-1 完全修飾名解決**: `ast.Attribute` の連鎖を末端の `ast.Name` まで辿ってドット結合し、
  先頭をエイリアス表で置換。`keyseq.application.config_service.<内部モジュール>` なら違反。
- **既存の「素の名前」検査（`node.value.id == "config_service"`）は残して和集合にした**。
  **この検査が唯一の検出経路になるのは、相対 import でモジュールを束縛した場合**
  （`from ..application import config_service`）。絶対形はエイリアス表が拾うため冗長になる。
  なお presentation には **`config_service` という名前の変数・引数が 29 箇所**
  （`ast.Name` 21 / `ast.arg` 8）実在するが、**これらは `ConfigService` のインスタンス**であり
  モジュール参照ではない（`controllers/config_io/child_save_rows.py:127` 等）。
  **【訂正】起票直後に「31 箇所」と記録したのは誤り**（`INTERNAL_*` の出現数 31 を取り違えた）。
  **理由づけも当初は「置き換えると検出が失われる」と書いたが、正しくは上記の相対 import のケース**
  （`deep-reviewer` M-2 の指摘で是正）。
- **重複の畳み込み**: `ast.walk` は入れ子の `Attribute` を複数回訪れるため、
  **同一（行番号, 内部モジュール名）は `setdefault` で 1 件**にする。
  アサーションは `assertEqual(forbidden, [])` なので**畳んでも失敗判定は落ちない**。
- `reviewer` = **修正要（軽微）**: docstring の限界記述に**代入による再束縛は解決できない**旨が
  抜けていた → 実測で裏取りして 1 文追記し解消。

### 【task_01b】相対 import 経路の検査（**枝番・ユーザー判断で追加**・`reviewer` = 完了可）

task_01 完了時にメインが「相対 import は R1〜R3 のいずれにも当たらず素通りする」ことを実測で発見。
**phase 12 からの既存の穴で task_01 の範囲外**だったため、**A（本フェーズで塞ぐ）/ B（後続 idea）**を
提示し、**ユーザーが A を選択**した。

- **R4**: `level - 1` 個の末尾セグメントを落として基準パッケージを求め `node.module` を連結 →
  **絶対名で R1 / R2 と同じ判定**にかける。
- **R4-fallback**: `package` が空、または `level` が深さを超えて解決できない場合は
  **`config_service` セグメント以降の末尾一致**で判定する。
  **「解決できないから素通し」にしない**のが要点。
- 呼び出し側は走査ファイルの実パスから `package` を算出して渡す（`__init__.py` はその親ディレクトリ）。
- **兄弟参照を誤検出しないことを許可例で固定**（`from .io_dialogs import IoDialogs`。
  presentation に **16 件実在**し、誤検出すれば即座にテストが落ちる）。
- **深さの実測**: `package="keyseq.presentation.controllers.config_io"` で
  **level=4 は検出 / level=3 は非検出**（オフバイワンなし）。
  `from . import X`（package が `config_service` 自身）も検出。
- `reviewer` = **完了可**。参考指摘 2 件のうち②（**`package` 空 + `from . import X` 形は
  module 名が無く縮退判定できない**）は実測のうえ **docstring へ追記**。①（関数長）は `/refactor_check` へ。

### 【task_01c】相対 import で束縛したエイリアスの解決（**枝番・ユーザー判断で追加**・`reviewer` = 完了可）

**フェーズ完了レビューで `deep-reviewer`（H-1）と `codex-adversarial-reviewer`（medium ①②）が
独立に同じ穴を指摘**。**ユーザー判断により本フェーズ内で是正**した
（`deep-reviewer` の最小案は「限界として記述して idea 起票」だったが、**塞ぐ方を選択**）。

- **塞いだ穴（いずれもメインが実測で確認）**:
  - `from ..application import config_service as cs` + `cs.orphan_scan` → 検出 0 件だった
  - `from .. import application as app` + `app.config_service.orphan_scan` → 同上
  - **絶対 import の同型は検出されていた**ため、**絶対と相対で非対称**だった
  - 違反する `as cs` の後に別スコープで許可の `as cs` があると**後の束縛が前を上書き**して違反が消えた
- **是正**: ①エイリアス表へ**相対 import（`level > 0`）も登録**する。解決は
  **`_resolve_relative_module` へ切り出して R4 と共有**（**重複実装を作らない**。片方だけ直すとずれる）。
  解決できない場合は**登録しない**（誤った絶対名を作らない）。
  ②エイリアス表を **`dict[str, set[str]]`（名前 → 束縛先の集合）**にし、
  **いずれかの候補が内部モジュールへ解決されたら違反**とする（**スコープ解析はしない**保守的判定）。
- **R1 / R2 / R3 / R4 / R4-fallback・素の名前検査は無変更**。既存の禁止 10 例 / 許可 11 例も不変で、
  **禁止 3 例 / 許可 2 例を追加**（許可側に相対の `contracts` 参照 2 形を入れて誤検出を固定）。
- `reviewer` = **完了可（指摘なし）**。誤検出なし / 3 経路の検出 / R4 の挙動不変 /
  ヘルパ切り出しは**タスク定義が認めた最小分割**の範囲内（提案書 09 の分割は先取りしていない）。

### 【確定】拡張後に残る検査の限界（**docstring に明記済・実測で確認**）

1. **動的 import**（`importlib` / `__import__`）— 原理的な限界。
2. **実行時に組み立てた名前**（`getattr(pkg, name)` / 文字列連結）。
3. **代入による再束縛**（`x = config_service` の `x`）— **エイリアス解決の対象は import 束縛のみ**。
4. **縮退時**（`package` を渡さない / `level` が深すぎる）は相対 import を解決できないため
   **エイリアス登録もされず**、`from . import X` 形（module が空）は末尾一致でも判定できない。
   **presentation の走査では `package` を必ず渡すので発生しない**。

**task_01c により「相対 import で束縛したエイリアス」は限界ではなくなった**（3 → 上記 4 項目へ整理）。
残りの解消は本フェーズでは行わない。必要になった時点で**新規 idea として起票する**。

### 【残存リスク】素の名前検査の潜在的な誤検出（`deep-reviewer` M-3・**実装は変えない**）

素の名前検査は **`config_service` という名前の変数の属性**も違反にする。
現時点では `set(dir(ConfigService)) ∩ INTERNAL_MODULE_NAMES` が空のため**誤検出 0 件**だが、
**`ConfigService` に `orphan_scan` / `quarantine` 等の公開メンバが増えると、
§3.2 が許可している正当な記述でテストが落ちる**。
**その時は検査側の再判断が要る**（公開メンバ名と内部モジュール名の衝突をどう扱うか）。

### 【確定】正本反映が不要という判断（メイン判断 2026-09-08）

- 本フェーズは**仕様を一切変えていない**。公開面の規定（`ConfigService` の公開 API + `contracts.py`）は
  **phase 12 で `architecture.md` §3.2 へ昇格済**で、本フェーズはその**検査の実装を直しただけ**。
  `deep-reviewer` も**条項とテストの検査範囲が完全に一致**しており**正本反映不要は妥当**と判定した。
- したがって `spec_detail/` の改訂は行わない。**「念のため追記」もしない**
  （条項を触るなら `.claude/rules/spec_change_workflow.md` に従いユーザー確認が先）。
- `codebase_map.md` も対象外（テストファイルはパッケージ表の記載対象ではない）。

### 【フェーズ完了判定レビュー】`deep-reviewer` = 修正して完了可 / `codex-adversarial-reviewer` = needs-attention

**両者が独立に「相対 import で束縛したエイリアスの取りこぼし」を指摘**（→ **task_01c で是正**）。
`deep-reviewer` は受け入れ条件と記録の数値を**全件実測で裏取り**し、
**正本反映不要の判断・`/refactor_check` の判定・完了チェックリスト**はいずれも妥当と評価した。

- **H-1 / Codex ①② = 相対エイリアスの穴** → **task_01c で塞いだ**（記述で済ませず実装で解消）。
- **M-2 = 「31 箇所」の数値誤りと因果の誤り** → **実測値（`ast.Name` 21 / `ast.arg` 8 = 29）と
  正しい因果へ是正**（本アーカイブ・`decisions.md` 索引・`INDEX_done.md`・`session.md`）。
- **M-3 = 素の名前検査の潜在的誤検出** → **残存リスクとして記録**（実装は変えない）。
- **M-4 = `session.md` / `handoff.md` 未更新** → 完了前に更新。
- **M-5 / Codex ③ = 提案書 09 の安全網が挙動保存を担保できない**（`assertTrue` では件数・文字列・
  順序を固定できない）→ **提案書の項目 0 を「期待メッセージを `assertEqual` で固定してから分割する」へ強化**。
- **L-1 / L-2 = 提案書の行番号ずれと「両側から該当」の不正確さ** → 是正（下記判定を参照）。
- **L-6 = `current.md` の自己ルール矛盾**（「旧フェーズの要約行は削除する」と実運用の食い違い）→
  **ユーザー判断**により、**過去フェーズの要約をやめ「扱っている領域」の数行 + 完了フェーズはリンクのみ**へ改め、
  `current.md` の「フェーズ完了時の指示」にもその形を明記した。
- **L-3 = 提案書のファイル名が `NN_refactor_<phase名>.md` の規約から逸脱** → **リネームして規約に合わせた**。
- L-4 / L-5 / L-7 / L-8 は提案書側へ注記として反映（実害なし）。

### /refactor_check 判定（2026-09-08）= **推奨**

提案書 [09_refactor_contracts_boundary_ast_coverage](../../../instructions/modified_proposal/09_refactor_contracts_boundary_ast_coverage.md)
（**未承認**）。PHASE_BASE = `90db223`。対象 = **変更 1 ファイル**
（task_01 / 01b で **+102 / -10**、task_01c で **+48 / -19**。**`keyseq/` の差分は 0**）。
メトリクスは `verifier` 実測 + task_01c 後にメインが再測。

- **M2 該当（提案書の項目 1）**: `collect_forbidden_refs` が **PHASE_BASE 27 行 → 100 行**
  （task_01c 適用前は 92 行）。**「40 行以上変更した既存関数のうち 80 行超」に該当**する。
  **【訂正】当初「追加した関数側にも両側から該当」と書いたのは不正確**
  （base 時点で存在した関数なので**この一本で該当**。`deep-reviewer` L-2）。
  **結論（M2 該当）は変わらない**。`.claude/rules/implementation.md` の予防目安（関数 30 行）も超過。
- **M6 は非該当**（提案書には関連項目 2 として収録）: `"config_service"` の直値は
  `CONFIG_SERVICE_PACKAGE` の**末尾セグメントと同じ文字列**だが**定数の値そのものとは同値でない**。
- **M1 非該当**（ファイル 227 行）/ **M3 非該当**（同型ブロックは 2 箇所）/
  **M4 非該当**（`INTERNAL_MODULE_NAMES` は不変）/ **M5 非該当**（申し送りの新規追加 0 件）。
- **安全網は強化が必要**（項目 0・`deep-reviewer` M-5 / Codex ③）。自己検証は
  **禁止 13 例 / 許可 13 例**で全経路を覆うが **`assertTrue`（非空）しか見ていない**ため、
  分割で**メッセージ文字列や畳み込みの先勝ちが入れ替わっても検出できない**。
  **期待メッセージを `assertEqual` で固定してから分割する**こと。
- **実施タイミングはユーザー選択**（(a) 同フェーズ末の追加タスク / (b) 独立ミニ計画 / (c) 見送り）。
  **承認前に実装しない**。

### 統合検証（`verifier` 実測 2026-09-08・task_01c 完了時 / task_02 完了時とも同値）

compileall clean / `tests` **417 pass（skip 7）** / `tests_ui` **288 pass（skip 0）** / smoke pass。
**フェーズ着手時と同値**で退行なし（**テストメソッドは 3 本のまま**）。
`git diff -- keyseq main.py tests_ui` は**空**。
