# 06_refactor_hook_key_pair_enumeration（Phase γ 完了時の /refactor_check 提案）

> 起票: 2026-08-05（`/refactor_check`・phase 07 = 保存系リデザイン Phase γ の完了処理）。
> **判定: リファクタ推奨**（**M4 のみ該当**）。**本書はユーザー承認前に実施しない**。
> 対象は Phase γ で変更した 12 ファイルのみ（`PHASE_BASE = caf41a7`・`keyseq/` 配下 +171 / -12 行）。

## 判定サマリ（メトリクス実測・`verifier` 収集）

| 記号 | 実測 | 判定 |
|---|---|---|
| M1 | 最大は `keymap_set_io.py` **674 行**（600 行超）だが本フェーズの増分は **+13 / -1** | 非該当（+100 行未満）|
| M2 | 新規・大幅改変関数の最大は `_apply_key` 約 20 行 / `toggle_hook_keys_individual` 約 17 行 | 非該当 |
| M3 | `keymap_set_io.py` に `apply_global_hook_key_defaults(...)` 呼び出し 3 箇所・`discard_retained_hook_keys()` **4 箇所**（いずれも **1 行の API 呼び出し**で、ブロックの複製ではない）| 非該当（判断に迷う → 非該当に倒す）**候補送り**（下記）|
| M4 | stop / toggle を**対で列挙**する箇所が **5 → 10** へ増加（新規 = `apply_global_hook_key_defaults` / `load_global_hook_keys` / `write_global_hook_keys` / `toggle_hook_keys_individual` / `_apply_key` の data_key 分岐）| **該当** |
| M5 | 申し送りコメントの新規追加 **0 件**（`-- keyseq/` でパス限定して測定）| 非該当 |
| M6 | 既存定数と同値の直値追加 **なし**（空文字既定・`False` 既定の既存パターンの踏襲のみ）| 非該当 |

**候補送り（`current.md` の別タスク化候補へ追記済み）**:

- **M3 由来**: runtime を新規化・置換する入口が 4 経路（`new_config` / `restore_default` / Import /
  起動時の空データフォールバック）あり、**それぞれで注入 API を呼ぶ規約**になっている。
  task_07b の指摘 A（Import 経路の注入漏れ）はこの規約の取りこぼしだった。入口の一本化は
  設計変更を伴い挙動保存の範囲を超えるため、本書には含めない。

---

## 項目 0: 安全網の確認（**先行必須**）

現状の特性テストが対象領域を覆っているかを先に実測する。不足があれば**テスト追加を先行**させる。

- 確認する観点: ①解決（OFF で全体デフォルトが注入される / ON は個別値）②移行判定（フラグ有無・
  正規化後の非空判定・冪等）③OFF 保存の空文字化 + フラグ false（保存 JSON のバイト列比較）
  ④OFF 編集の config.json 更新と成否（失敗時に確定しない）⑤dirty 非汚染
- 現時点の基準線: `tests` **169 pass** / `tests_ui` **178 pass** / smoke pass（task_07b 実測）
- 完了条件: 上記 5 観点を固定するテストの所在を対応表にできること（空欄があれば追加）

## 項目 1: hook キー 2 本の「対の列挙」を 1 箇所へ寄せる（M4）

**対象**: `keyseq/domain/config.py`（キー名の定義元）/
`keyseq/application/config_service/{__init__.py, split_loading.py, split_payloads.py}` /
`keyseq/presentation/{app.py, controllers/key_capture.py, controllers/config_io/startup_io.py, ui_vars.py}`

**何が問題か（M4）**: `hook_stop_key` / `hook_toggle_key` を**対で列挙**する箇所が本フェーズで
5 → 10 へ倍増した。キー名の文字列リテラルが application / presentation の両層へ散っており、
3 本目の hook キーを足す・キー名を変える・正規化規則を変えるときに**全箇所の追随が必要**になる。

**どう変えるか（挙動保存）**: `domain/config.py` に**キー名の対を表す定数と、対に対する薄い純関数**を置き、
各所はそれを使う。オブジェクト化（値オブジェクト新設）はしない＝差分を最小に保つ。

```python
# domain/config.py（案）
HOOK_KEY_FIELDS: tuple[str, str] = ("hook_stop_key", "hook_toggle_key")

def normalize_hook_key_pair(stop_key: str, toggle_key: str) -> tuple[str, str]:
    return (normalize_key_name(stop_key), normalize_key_name(toggle_key))
```

```python
# 呼び出し側（例: apply_global_hook_key_defaults）
for field, value in zip(HOOK_KEY_FIELDS, load_global_hook_keys(service, config_root=config_root)):
    runtime[field] = value
```

**やらないこと**: `hook_keys_individual` を含めた 3 キーの構造体化 / UiVars・hook_frame の
ウィジェット生成の共通化（full と compact は Widget を共通化しない方針・`codebase_map.md`）/
保存 payload のキー列挙の動的化（バイト列比較テストの前提を崩さないため**明示列挙のまま**）。

**完了条件**（`.venv` の python で実行）:

- `-m compileall -q keyseq main.py tests tests_ui` clean
- `-m unittest discover -s tests` **169 pass** / `-m unittest discover -s tests_ui` **178 pass**
- `-m tests.smoke_app` pass
- 保存 JSON のバイト列比較テストが**無修正で pass**（＝出力バイト列が不変）

**リスクと戻し方**: リスク**低**（純粋な参照の置換・挙動不変）。ただし解決点は phase 07 で
安定したばかりで、`split_payloads` の明示列挙は後方互換の要である点に注意。
戻し方はコミット単位の revert（1 コミットで完結させる）。

**依存**: 項目 0 の完了。phase 08（プリセットの config.json グローバル化）と**同じ構造**を扱うため、
**phase 08 の着手前に実施するか、phase 08 完了後に 2 例そろえてから実施するかはユーザー判断**
（2 例目が出てから共通化する方針なら**見送り**も妥当な選択肢）。

---

## 実施形態（ユーザー判断待ち）

- (a) phase 07 末の追加タスク（`task_09_refactor_hook_key_pair`）として起票
- (b) 次フェーズ前の独立ミニフェーズ（計画05 と同じ「計画」運用）
- (c) **見送り**（phase 08 で 2 例目が出てから再判定。`/refactor_check` は毎フェーズ走るため悪化すれば再検出される）

> 推奨は **(c) 見送りまたは (b)**。効果は「将来の追随箇所を減らす」で中程度、緊急性は低い。
