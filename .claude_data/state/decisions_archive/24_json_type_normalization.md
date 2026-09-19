# decisions_archive / phase 24: JSON 読込の型不正の扱い統一

対応表: phase 24 / 暫定仕様 20（**暫定仕様先行モード**・v0.3 で凍結）/ decisions 24。
起票元: phase 23 完了後のユーザー指示（2026-09-19）=「keymap / trigger_set の個別読込経路を
実際に見直して必要なら直す」。
完了 2026-09-19。**挙動追従（頑健化）・スキーマ不変**。
正本 = `spec_detail/data_schema.md` **§5.1「型不正の共通規則」（新設）** / §5.2 / §5.6（**keymap 節を新設**）/ §5.11。

## 問題

文字列を期待する処理（`normalize_key_name` / `(x or "").strip()`）へ**非文字列がそのまま渡る**。

- **9 箇所で `AttributeError`**（読込そのものが落ちる。当初 6 箇所と見積もったが完了判定前レビューで 3 件 + 全走査で 1 件を追加発見）。UI 側は捕まえるが内部エラー文言が出る。
- `str()` 強制の箇所では **Python の repr 文字列が runtime に載る**
  （`{"a": {"x":1}}` → `{"a": "{'x': 1}"}` / trigger の `key` が `"{'a': 1}"` になる等）。
- 扱いが経路ごとにばらばらで、`hotkey_presets`（非 str を除去）や `actions` の要素判定
  （非 dict を除去）とは逆の流儀だった。
- 正本 §5.6 に **keymap 個別 JSON の節が無く**、`triggers[]` にも型規定が無かった
  = `spec_change_workflow.md` 検出基準 **B（仕様の不備）**。

## 確定した設計判断（ユーザー 2026-09-19）

| # | 判断 | 採らなかった案と理由 |
|---|---|---|
| 1 | **「除去に寄せる」**（`hotkey_presets` / `actions` の要素判定と同じ流儀へ統一） | 現状維持（`str()` 強制で repr を受け入れる）= 無意味なキー名・ラベルが runtime に載り続ける |
| 2 | **暫定仕様先行モード**で進める | 直接改訂 = 条項が keymap / trigger_set / 共通規則に跨り、ユーザーと反復して詰める必要があった（探索的） |
| 3 | **案 F = 全経路へ一斉適用** | **案 G（個別読込限定）= 成立しない**。`_generate_keymap_id` と `load_triggers_from_trigger_set` は個別読込と split 読込が**共有**しており、個別を直せば split も必ず変わる。加えて `actions[]` の `label` 由来の例外が個別読込にも残り「統一した」と言えない。後送りすると同じ関数を 2 フェーズで 2 回触ることになる |
| 4 | **trigger の `key` が非文字列 → 空扱いで trigger は残す** | 除去 = UI で key を入れ直す余地が消える。既存の「空 key の trigger は残る」挙動とも揃う |
| 5 | **`sequence_path` が非文字列 → 空扱い** | 参照なしとして同 trigger のインライン `actions` を使う（既存の空文字と同じ） |
| 6 | **`mappings` の target が非文字列 → 対ごと除去** | target の無いマッピングは動作しないため残す意味が無い。source 側は JSON 由来で常に str のため論点にならない |
| 7 | **`normalize_key_name(value: str)` のシグネチャは変えない**。入口関数 `coerce_key_name` / `coerce_label` を domain に足す | Any 受けへの変更 = **呼び出し 158 箇所**の意味が変わる。保存側・表示側も含むため影響が読めない |
| 8 | **R1 / R2 / R3 というラベルは正本へ持ち込まない**（§5.1 に共通規則の段落を置き各節から参照） | ラベルを正本に焼くと後の節追加で破綻する（`deep-reviewer` F-2） |
| 9 | **`suppress` / `run_to_end` / `run_to_end_delay_ms` は現状維持** | bool/int の既定値規定であり型不正の共通規則とは別軸。変えると挙動変更になる |

## レビュー指摘と裏取り（v0.1 → v0.2）

`deep-reviewer`（起票時）= 修正要 / `codex-adversarial-reviewer`（確定前）= needs-attention。
**指摘は全件 `.venv` で実測して CONFIRMED**。v0.1 の誤りは以下:

1. **「例外で落ちるのは `_generate_keymap_id` だけ」は誤り**。`normalize_actions` の `label`
   （`domain/config.py:144`）でも落ち、**sequence / trigger_set の個別読込も対象**だった
   （phase 23 の §5.11 が「dict 以外は除去」しか書かず `label` の型に触れなかったため、
   仕様・実装の両方に残っていた穴）。例外は計 6 箇所。
2. **`suppress` の記述が実装と逆**。「既定 true へ倒す」ではなく `bool()` 強制で
   `null` / `0` / `""` / `[]` は **false** になる。
3. **参照先 sequence からの repr 再流入**。`_normalize_sequence_payload` の `label` が repr 化し、
   `split_loading.py:485-486` の `trigger.update()` で参照元 trigger の `label` を上書きする。
4. **共有ローダーのため経路別スコープが破綻**（判断 3 の根拠）。
5. 行番号の誤り（`:166` / `:246` → 正しくは `:178` / `:248`）。
6. **falsy な非文字列は元から空扱い**（`x or ""`）。変わるのは **truthy な非文字列のみ**。
7. `mappings` の source は JSON 由来で常に str（`safe_deepcopy` は json round-trip）。

## フェーズ中の追加判断

- **完了判定前レビュー（`deep-reviewer`）で棚卸しの不足が判明し、task_03 を追加**（ユーザー判断 2026-09-19）。
  **例外箇所は 6 箇所ではなく実際は 9 箇所**だった。追加の 4 箇所（実測で確認）=
  `domain/config.py:163`（**旧形式互換の `trigger_key`**・メインの全走査で追加発見）/
  `:213` `hook_stop_key` / `:214` `hook_toggle_key` / `:287` `active_keymap_id`。
  いずれも `ensure_config_compatibility` 内で **raw JSON を直接受ける `normalize_key_name`** で、
  `str()` ガードが無かった。**確定済みの案 F（例外を全経路から消す）の趣旨を満たすため、
  後送りせず本フェーズ内で直す**判断とした（task_03）。
- **同レビューで正本の記述誤りを 3 件訂正**（いずれも実測で確認）:
  ①「空になると成立しない要素は除去」は `mappings` にしか当てはまらない。
  **`actions` の `label` が非文字列でも要素は残る**（`label=""` になるだけ）。
  `actions` の要素除去は**非 dict という形状由来**であり型由来ではない。
  `hotkey_presets` も「空だから除去」ではなく「非 dict / 非 str だから除去」で、空文字の要素は残る
  ②**単一 JSON の `keymaps[].id` だけ扱いが異なる**。ファイル名が無く stem へ倒せないため
  **要素ごと除去**され、個別 / split 読込の `_2` 付加による一意化は行われない
  ③`triggers[]` の非 dict 除去・`mappings` が dict 以外なら `{}` などの**形状の倒し方が昇格漏れ**
  だった（§5.8.9 の形状検証は孤児棚卸しの候補判定であり**目的が異なる別規定**なので、
  相互参照だけでは足りなかった）。`suppress` のキー欠如時の既定（true）も明記した。

- **reviewer の差し戻し 1 件**: `split_loading.py:422`（`load_keymap_entry` の keymap `label`）が
  適用漏れ。**タスク定義の適用先列挙でメインが `load_keymap_file` だけ見て見落とした**もの。
  実測で repr 残存（`"['a']"`）を確認し、同じ Codex へ差し戻して 1 行 + テスト 1 件で解消。
- **パス系フィールド（`path` / `switch_key` / `trigger_set_path` 等）はスコープ外**とし、
  [idea_25](../../../instructions/backlog/idea_25_path_field_type_normalization.md) へ分離（未着手）。
  例外にはならず「存在しないパス」として無視されるため実害が小さい。
- **tests_ui の 1 件 fail は既知フレーク**（`test_quarantine_manage_flow.py:326` の
  Escape 配送依存。idea_18 と同機構）。単独 20/20 pass・一括再実行 446 全 pass を確認し、
  観測を idea_18 へ追記した。**当フェーズの差分とは無関係**。

## 実測・レビュー

- compile clean / `tests` **505**（skip 7・486 → **+19**。task_01 で +12 / task_03 で +7）/
  `tests_ui` **446** / smoke pass。
- `reviewer`（phase.md 整合）= 指摘なし / `reviewer`（task_01 差分）= 1 回目 **修正要** → 2 回目 **採用** /
  `deep-reviewer`（task_02 = 正本昇格・完了判定前）= **修正要**（下記の追加判断へ反映）/
  `reviewer`（task_03 差分）= **完了可**（指摘なし・取りこぼしの再走査も実施）。
- 実機目視 = **不要**（読込経路の内部正規化のみで UI 変更なし）。
- コミット: `a1764d1`（task_01）/ `1532bf3`（task_03）/ 本フェーズ末のコミット（task_02）。
- `/refactor_check` = **不要**（PHASE_BASE `61a7c79`・対象 3 ファイル・M1〜M6 該当なし）。
  M1: `config_service/__init__.py` 829 行 / `split_loading.py` 537 行 / `domain/config.py` 353 行だが、
  増分は +25/-13 で 100 行未満。M2: 新設関数は各 2 行。M3: 同型ブロックの増殖ではなく**重複の集約**。
  M4〜M6: 該当なし（列挙ボイラープレートの増加・直値の重複追加・申し送りコメントの追加はいずれも無し）。

## 残件

- **パス系フィールドの型規定** = idea_25（未着手・優先度低）。
- `button` 非文字列の `AttributeError`（`action_executor.py:119`）= phase 22 からの
  別タスク化候補のまま。**実行時**の型不正であり読込時の正規化とは別レイヤ。
- `domain/config.py` の `keymap_switch_keys`（`:295-310`）も `str()` 強制のまま（idea_25 の範囲）。
