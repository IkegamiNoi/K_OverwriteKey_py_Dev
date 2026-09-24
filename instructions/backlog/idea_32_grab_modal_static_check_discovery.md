# idea_32_grab_modal_static_check_discovery.md

## 概要

`grab_modal` の静的検査が**対象をハードコードで列挙**しているため、
**新規ダイアログを守らない**。発見ベース（`dialogs/` を走査して対象を決める）へ寄せたいが、
**発見ベース単独にすると「`grab_modal` の呼び出しが消えた」検出が失われる**ため、
併用形にするかを含めた設計判断が要る。**テストのみ・production 不変**。

## 起票経緯（2026-09-22）

phase 14（ネストしたモーダルの grab 復元）の `/refactor_check` からの候補送り。
`deep-reviewer` の M-6 指摘で、2026-09-11 にユーザー判断で保留としたもの。
**テストコードのため `/refactor_check` の対象範囲外**でもあり
`instructions/phase/current.md`「別タスク化候補」に留め置かれていた。
2026-09-22 の current.md 整理でユーザー判断により idea へ昇格。

## 現状

- `tests_ui/test_nested_modal_grab.py:260` の `test_grab_modal_is_last_initialization_statement`
  - 系統 A = `dialogs/` の **10 クラス**を `dialog_classes` 辞書で列挙（`test_nested_modal_grab.py:262-273`）。
    各 `__init__` に対し「`grab_modal` はちょうど 1 回」「`__init__` の最後の文」を検査
  - 系統 B = `controllers/config_io/` の **3 ファイル**を件数つきで列挙
    （`child_save_dialog.py`=2 / `io_dialogs.py`=1 / `hotkey_presets_io.py`=1。`:302-303`）。
    「`grab_modal` は初期化関数または try の直下」「直後は待機だけ」を検査
- **列挙は phase ごとに手で足している**（phase 27 の `KeymapSetHistoryDialog` 追加で 9 → 10 になった）。
  **足し忘れたダイアログは静的検査を素通りする**
- 一方で**件数のアサート**（系統 A の「ちょうど 1 回」・系統 B の期待値）が、
  **`grab_modal` の呼び出しが消えた**ことの検出を担っている

## 提案（方向性・要設計）

- **案 A（併用）**: 対象の**発見は走査**で行い（`dialogs/` 配下で `Toplevel` を継承するクラス等）、
  **件数の期待値は据え置き**。新規ダイアログが自動で検査対象に入る
- **案 B（発見ベース単独）**: 列挙を全廃。実装は単純だが**消失検出が失われる**
- **案 C（据え置き + 足し忘れ検出）**: 列挙は残し、「走査で見つかったクラスが列挙に無い」ことだけを
  別テストで検出する。差分は最小
- 論点: 「ダイアログとみなす条件」をどう定義するか（`Toplevel` 継承 / `grab_modal` の import 有無 /
  `dialogs/` 配下という場所）。**phase 15 の静的検査が `dialogs/` 8 クラス限定**で、
  `controllers/` を含めると phase 14 の既存検査と正面衝突する経緯があるため、
  **既存 2 検査との棲み分け**も同時に見る必要がある

## 想定スコープ

- 含む: `tests_ui/test_nested_modal_grab.py` の静的検査（必要なら phase 15 側の静的検査との整理）
- 含まない: production コード / `features.md` §4.6 の作法そのもの
- 影響レイヤ: テストのみ。**仕様変更なし**

## 状態

**完了**（[phase 33](../phase/33_grab_modal_static_check_discovery/phase.md)・2026-09-24。判断は
[decisions_archive/33](../../.claude_data/state/decisions_archive/33_grab_modal_static_check_discovery.md)）。
案 A'〔ユーザー確定〕= `dialogs/` 直下の `Toplevel` 継承クラスを走査で発見（発見条件を `grab_modal` の有無にしないので消失も検出できる）+
config_io は呼び出しファイル集合と期待件数の辞書のキー一致。列挙漏れだった `CategoryChooserDialog` が検査対象に入った。
完了判定前レビューを受け、呼び出しを全 `ast.Call` で数える補強と、phase 15 側の静的検査（static_1・2）の発見ベース化も同フェーズで実施
（ネストした子は除外リスト `NESTED_CHILD_DIALOGS`〔(ファイル名, クラス名) の組〕で持つ・クラス単位。static_3 は列挙のまま）。別名 import・多段継承は残るリスク。
