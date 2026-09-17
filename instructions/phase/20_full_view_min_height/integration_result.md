# integration_result.md（phase 20: full_view_min_height）

## 統合確認（task_03・verifier・2026-09-18）

| 項目 | 結果 |
|---|---|
| `compileall -q keyseq main.py tests tests_ui` | clean |
| `unittest discover -s tests` | 451 OK（skipped 7） |
| `unittest discover -s tests_ui` | 437 OK（task_03b 後に再実行しても 437 OK） |
| `-m tests.smoke_app` | SMOKE OK（task_03b 前） |

既知の無害ノイズ: `tests_ui` の stderr に `_clear_flash_message` の破棄後 `after` 実行 / `tests` の `ResourceWarning: unclosed file`。

## 二次レビュー（差分 `5e25218..e1393a6`。task_03b 着手前）

task_03b（`86accae`）は別途 `reviewer` が単体レビュー = 採用。

- `codex-reviewer`: 指摘なし。
- `deep-reviewer`: 修正要（中 1）。ユーザー採否（2026-09-18・詳細は `decisions.md` の phase 20 節）:
  - 指摘 1（自動拡大した高さが最小の低下で縮む）→ **task_03b で修正**（`86accae`）。変異検査で `test_font_growth_expands_only_below_minimum` が検出。
  - 指摘 2・3・6（テスト補強・変数名）→ task_03b で採用。
  - 指摘 5（`show_full_view` の呼び出し順の記述）→ task_04 で正本に追従。
  - 指摘 4（一時メッセージのラベルを App 属性で参照）→ 保留。

## 実機目視（ユーザー・2026-09-18）: OK

1. 標準 / ＋3 / −3 で縦に最小まで縮めても、ヘッダ・3 枠の中身・ステータス欄・ステータスバーが切れない。
2. ＋3 で起動すると 820 より高く開く。
3. 省略表示では縦にも縮められ、フル表示へ戻すと最小の高さが効く。
4. 標準フォント起動直後の一覧の見た目が phase 19 時点と同じ。
5. ＋3 で高くなった後、標準へ戻しても高さが縮まない（task_03b）。

## 完了判定前（task_04・2026-09-18）

- `codex-adversarial-reviewer` medium / `deep-reviewer` 指摘 3（最大化の解除で広がった高さが縮む）→ **task_04b で修正**（`ba31614`）。変異検査で `test_unmaximize_expanded_height_survives_minimum_decrease` が検出。
- task_04b 後の再実行: compile clean / `tests` 451 OK（skipped 7）/ `tests_ui` 438 OK / smoke SMOKE OK。
