# decisions_archive / 02_hotkey_validation

フェーズ **02_hotkey_validation**（hotkey 検証ロジックの層移設）の判断履歴。
索引は `.claude_data/state/decisions.md`「アーカイブ索引」。
フェーズ定義: `instructions/phase/02_hotkey_validation/phase.md`。
**設計の正（凍結）**: 暫定仕様 `instructions/history/01_hotkey_validation.md`（v1.1・凍結）。

- 期間: 2026-07-17 〜 2026-07-18
- モード: **暫定仕様先行モード**（番号対応: phase 02 / 暫定 01 / decisions 02。暫定仕様は独立採番）
- 目的: App（presentation）に住む hotkey 検証を domain / application へ移し、
  ① application → presentation の**層の逆転を解消** ② **テスト容易性**（`tk.Tk` 不要で単体テスト）
- 結果: **完了**（task_01〜05）。標準検証全緑・実機目視 OK・reviewer/codex-reviewer 指摘なし。**挙動不変**。
- 起票元: [idea_01](../../instructions/backlog/idea_01_hotkey_validation_to_domain.md)（計画04 W7 の残留ロジック分類から分離）

---

## 設計判断（暫定仕様 §2・ユーザー確定 2026-07-17）

- **設計案 C を採用** → **採用**。domain = 純粋な文法検査（3種のエラー）/ application = 合成 + キー名検証
  （4種目）/ presentation = 薄い委譲。層の境界と関心が一致し、domain の既存スタイル
  （標準ライブラリのみ・クラス0・DI なし）を崩さない。案 A（domain に Callable 注入）・
  案 B（application 集約で domain 不使用）は退けた。
- **parts の再構成を廃止** → **採用**。domain が `(error, normalized, parts)` を返し application が
  `parts` をそのまま使う（`normalized.split("+")` 復元をしない）。公開契約 `(error, normalized)` は不変。
- **命名**: `domain/hotkey.py::validate_hotkey_syntax` / `application/hotkey_service.py::HotkeyService.validate` → **採用**。
- **安全網の特性テストを追加し移設後も残す** → **採用**。移設後も無変更で pass することが挙動不変の証明。

## 敵対的レビューの指摘処理（暫定仕様 §2・codex-adversarial-reviewer 2026-07-17）

- 「`normalized.split("+")` の 2 回目アロケーションが `MemoryError` で未捕捉例外になる」（medium）
  → **却下（根拠不成立）**。現行実装も `try` 外で同種のアロケーションをしており挙動の種類は変わらない。
- ただし下層の論点（parts 二度手間）は妥当で reviewer も独立指摘 → 「冗長性の除去」を理由に
  上記「parts 再構成廃止」として**採用**（MemoryError 対策としてではない）。
- `parts` が空リストになる経路は存在せず `p` 未定義の `NameError` は起きないことを確認済み。

## 実装上の事故ポイント（各タスクで回避を確認）

- **キー名検証ループは明示的な `for`**（内包表記/map/any 不可）。Python 3 では内包表記のループ変数が
  外へ漏れず `except` 内の `p` が `NameError` になり挙動が変わる（task_03 で明示的 for を厳守）。
- `try` はループ全体を包み `except` がループ変数 `p`（失敗キー）を参照する現行構造を厳守。
- 新規ファイルは未追跡のため確認 grep は `git grep` ではなく**直接 grep**（`git grep` は追跡済みのみ検索）。

## task_04 実機目視で判明した既存挙動 → idea_03 分離 + §6-11 補正（ユーザー判断 2026-07-18）

- 実機目視（ユーザー）: プリセットダイアログの正規化保存 OK / hotkey アクションの実行 OK ＝ **挙動不変を確認**。
- 判明（**task_04 とは無関係の既存非対称**）: アクション（シーケンス）の hotkey は `ActionDialog.on_ok`
  （`dialogs.py:123-134`）が**生値のまま保存**（プリセットは `validate_hotkey` を通し `normalized` を保存）。
  実行時は `ActionExecutor` が正規化・検証するため機能実害なし。`config/user/sequences/a.json` に
  `"Ctrl+ A"` が残る。`dialogs.py` は task_04 で無変更＝移設前と同一挙動。
- **ユーザー判断 (A)**: 今フェーズでは触らず → [idea_03](../../instructions/backlog/idea_03_action_hotkey_save_normalization.md)
  として起票（優先度低・要設計・挙動変更を伴う。暫定仕様 §7「単キー検証の統一」と同種の負債）→ **保留（別 idea へ）**。
- **ユーザー判断 (B)**: 暫定仕様 §6-11 の文言（「アクション編集ダイアログで…正規化されて保存される」）は
  実装と食い違うため、「プリセット＝保存時正規化 / アクション＝実行時正規化。アクション保存時の正規化・検証は
  idea_03 で対応予定」と補正 → **修正して採用**（idea_03 実施を前提とした文言・task_05 で反映）。

## 正本反映（昇格）要否（task_05・Explore 調査 2026-07-18）

- **昇格不要** → **採用**。`instructions/common/spec_detail/` に hotkey 検証（文法・正規化・エラーメッセージ・
  担当層）の記述は**存在しない**（`hotkey` 出現は JSON プリセットのデータ構造参照のみ）。
  検証の担当層/クラス割り当ては `instructions/common/spec_detail/architecture.md` §3.5 が
  「codebase_map.md を正とする」と明言しており spec_detail 外。挙動不変ゆえ仕様変更もなし。
- 追従更新は spec_detail 外の **`codebase_map.md`** のみ実施（`HotkeyService` / `domain/hotkey.py` の追記、
  App の `validate_hotkey` を薄い委譲と整理）。
- 暫定仕様 `history/01_hotkey_validation.md` は **v1.1 で凍結**（§6-11 補正込み）。

## /refactor_check 判定（task_05・2026-07-18）

- **不要**（M1〜M6 いずれも該当なし。対象: `keyseq/` 3 ファイル + tests 3 ファイル / +253・-27 行）→ **採用**。
  PHASE_BASE = `09c1400`（フェーズ起票）〜 HEAD。
  - M1: `app.py` 466 行（600 行未満）・正味 +4 行。新規 `hotkey.py` 27 行 / `hotkey_service.py` 24 行。非該当。
  - M2: 80 行超の新規関数なし（最大 `validate_hotkey_syntax` 24 行）。M3: 旧ロジックは**移動（削除）**でコピー増殖なし。
  - M4: なし。M5: 申し送りコメント新規 0 件。M6: エラーメッセージは domain へ一本化し旧 `app.py` 側は削除＝重複なし。
- 提案書は起票しない。

## codebase_map / 正本仕様の更新

- `codebase_map.md`: **更新**（App の `validate_hotkey` を「`HotkeyService.validate` への薄い委譲」と明記 +
  「HotkeyService / domain/hotkey.py」節を新設）→ **採用**。
- `spec_detail/`: **更新不要**（上記「昇格要否」の裏取りどおり）→ **採用**。

## コミット一覧

| コミット | 内容 |
|---|---|
| `09c1400` | フェーズ 02_hotkey_validation を起票（PHASE_BASE） |
| `5ca5799` | task_01: `App.validate_hotkey` の特性テストを tests_ui へ追加（安全網・実装無変更） |
| `2e0efa7` | task_02: `domain/hotkey.py::validate_hotkey_syntax`（文法検査）+ tests |
| `c0b782a` | task_03: `application/hotkey_service.py::HotkeyService`（合成 + キー名検証）+ tests |
| `8765acb` | task_04: presentation の委譲化・`HotkeyService` 生成・注入元差し替え（層の逆転を解消） |
| `dcd733d` | idea_03 起票 + task_04 完了を state 反映 |
| （本コミット） | task_05: 正本反映・記録（codebase_map / §6-11 補正 / 凍結 / decisions_archive / INDEX 移動 / refactor_check 判定） |

## 検証・レビュー

- 標準検証（全タスクで全緑・`.venv` python）: compile clean / tests **77**（59 基準 + 9 + 9）/
  tests_ui **16**（9 基準 + 特性テスト 7）/ smoke pass。**特性テスト 7 件は移設後も無変更で pass**＝挙動不変の証明。
- reviewer（5観点）: task_04 起票内容・実装とも「**完了可**・指摘なし」。
- codex-reviewer（task_04 統合の二次レビュー）: **指摘なし**。
- 実機目視（task_04・ユーザー 2026-07-18 **OK**）: プリセットの正規化保存 / hotkey アクションの実行。

## 次フェーズへの申し送り

- 次候補は [idea_02](../../instructions/backlog/idea_02_startup_font_settings_cleanup.md)（起動設定/フォント クラスタ・
  初期化順序の解決が前提）。次採番は phase **`03`**。
- 未着手の派生 idea: [idea_03](../../instructions/backlog/idea_03_action_hotkey_save_normalization.md)
  （アクション hotkey の保存時正規化/検証の統一・優先度低・要設計）。
- 据え置き継続: `action_list` alias（`full_view.py`・production が使う生きたパス。decisions_archive/01 参照）。
