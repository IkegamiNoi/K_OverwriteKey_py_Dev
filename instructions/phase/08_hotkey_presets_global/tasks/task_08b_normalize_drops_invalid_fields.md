# task_08b_normalize_drops_invalid_fields

## 目的

フェーズ完了レビュー（`codex-adversarial-reviewer` = High / `deep-reviewer` = 指摘1）で判明した
**起動不能バグ**を是正する。

`normalize_hotkey_presets` は `label` / `value` に `.strip()` を直接適用するため、
**非文字列（数値・dict 等）が入っていると `AttributeError` を送出する**。この呼び出しは
`load_global_hotkey_presets` の `try` の外にあり、**E1（`App.__init__`）・E4 は捕捉しない**ため、
**グローバルプリセットファイルに不正な要素が 1 つあるだけでアプリが起動できない**。

```
normalize_hotkey_presets([{"label": 1, "value": "ctrl+a"}])
  -> AttributeError: 'int' object has no attribute 'strip'   （.venv で実測）
apply_global_defaults(...)                                    -> 同じ例外を送出（契約違反）
```

phase 08 以前は同種の破損が `ensure_config_compatibility` 内で起き、通常読込経路（L3）の
`try/except` に拾われて**空データ起動へ縮退**していた。**回復可能だった状態が起動不能へ変わっている**。

**確定した直し方（ユーザー判断 2026-08-09）＝ 要素単位で除去**。正本は反映済み
（`spec_detail/data_schema.md` **§5.10.2**「**`label` または `value` が文字列でない要素の除去**」
「**正規化はファイル単位で失敗しない**」）。

**レイヤ制約**: **domain の純関数 1 つ + テスト**。application / presentation / スキーマは不変。

## 対象範囲

### 1. `keyseq/domain/config.py` — `normalize_hotkey_presets`

* 各要素について、**`label` と `value` が文字列でない場合はその要素を除去する**
  （現在の「非 dict 要素はスキップ」と同じ扱い）。
* **例外を送出しない**こと（`.strip()` を非文字列へ適用しない）。
* `None` は現状どおり空文字として扱う（`(p.get("label") or "").strip()` の既存挙動＝
  **`None` / キー無しは空文字**を維持する。**空文字になった要素は除去しない**）。
  ＝ 除去するのは「値が存在するが文字列でない」場合のみ。
* 正規化の中身（trim / `value` の小文字化 / `safe_deepcopy`）は**変えない**。

> **併せて `ensure_config_compatibility` も堅くなる**（同じ純関数を呼ぶため）。
> これは意図した改善（従来は例外 → 空データ起動へ無言縮退していた）。

### 設計メモ / 制約

- **`load_global_hotkey_presets` 側は変更しない**（`None` 判定の位置・`try` の範囲は現状のまま）。
  「読めない（`None`）」の定義は**ファイル単位の問題のみ**（§5.10.2）で、
  **要素の不正はファイル単位の失敗にしない**。
- `apply_global_defaults` の「例外を投げない」契約は、この修正で**実装が契約に追いつく**形になる。
  API 側に `try/except` を足して黙らせる直し方は採らない。
- 保存側（`save_global_hotkey_presets`）は**引き続き正規化しない**（§5.10.2 のとおり読み出し側 1 箇所）。

## 含まない

- `load_global_hotkey_presets` / `apply_global_defaults` / presentation の変更
- 保存側での正規化 / 破損ファイルの退避・警告
- `str()` による強制文字列化（**却下済み**。dict が `"{'x': 1}"` のようなゴミとして残るため）
- 正本 `spec_detail/` の追加改訂（**§5.10.2 は反映済み**）

## 確認

`.venv` の python で実行（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。実測は `verifier`。

- `-m compileall -q keyseq main.py tests tests_ui` が clean
- `-m unittest discover -s tests` が **pass**（基準線 **198** + 追加分）
- `-m unittest discover -s tests_ui` が **pass**（基準線 **186**）
- `-m tests.smoke_app` が pass

### テスト（追加まで実装範囲。**実行は依頼しない**）

**`tests/test_domain_config.py`**:

1. `normalize_hotkey_presets` が **`label` / `value` が非文字列（int・dict・list）の要素を除去**し、
   **例外を送出しない**。正常な要素は残る（混在ケースで値を確認）。
2. `label` / `value` が **`None` / キー無し**の要素は**除去せず空文字**になる（既存挙動の維持）。
3. `ensure_config_compatibility` が、非文字列 `label` を含むデータでも**例外を出さず**完走する。

**`tests/test_config_service.py`**:

4. **本件の本体**: 不正要素を含むグローバルプリセットファイル
   （例: `[{"label": 1, "value": "ctrl+a"}, {"label": "ok", "value": "CTRL+B"}]`）に対して
   **`apply_global_defaults` が例外を投げず**、`[{"label": "ok", "value": "ctrl+b"}]` を供給する。
5. 同じファイルで **通常読込（`build_runtime_data_from_split`）も同じ結果**になる（経路一致）。

## 完了条件

- 上記確認がすべて pass し、**`reviewer` 採用**（観点: §5.10.2 との適合〔要素単位の除去・
  ファイル単位で失敗しない〕/ `None`・キー無しの既存挙動を変えていないか /
  `load_global_hotkey_presets` 側に手を入れていないか / domain に依存が増えていないか /
  受入条件 7・9 に回帰が無いか）。
- **実機目視**: 本件は**観点 6（破損ファイル）の型違いケース**なので、
  ユーザーに**不正 label を含むファイルでの起動確認**を 1 点だけ依頼する。
