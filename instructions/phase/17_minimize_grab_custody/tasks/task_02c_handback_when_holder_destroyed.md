# task_02c_handback_when_holder_destroyed

## 目的

暫定仕様 15 **§3-2(8) の v0.6 拡張**（ユーザー確定 2026-09-16）を実装し、task_04 の二次レビューが
実測で示した残穴 **H-1** を塞ぐ。あわせて同レビューのテスト側の指摘 **M-3 / M-4** を閉じる。

H-1: 最小化中に新モーダル N が開き（§3-2(7) で預かりが N の `previous` へ移譲）、
**預かり窓 H と N の両方が復元前に破棄**されると、v0.5 の差し戻しは「生存しているが非表示」しか
拾わないため発火せず、`<Map>` は `_custody_window is None` で即 return して**台帳フォールバックへ
到達しない** → **生存・表示中の外側モーダルが非モーダルのまま復元される**（実測で再現済み）。

**presentation 限定・スキーマ不変。**

## 対象範囲

### 1. `keyseq/presentation/modal.py`（H-1 の修正）

- `restore_grab` の差し戻し分岐を、**復元できなかった理由（非表示 / 破棄済み）で区別しない**形にする。
  現在の「`previous.winfo_exists()` が真のときだけ判定する」入れ子をやめ、
  **`previous` を `grab_set()` できなかったすべての場合**に、
  **`_app_minimized` かつ `_custody_window is None` なら `_custody_window = previous`** とする。
- **`<Map>` 側は変更しない**。破棄済みの窓が預かりに入っても、既存の候補ループが
  「記録窓が使えなければ**台帳の最内**（生存かつ表示中）」へ落とすため正しい窓が掴む。
- 既存のガード（`event.widget` / 二重発火 / 現保持者 / 非表示の保持者のみ）と台帳の扱いは**変更しない**。

### 2. `tests_ui/test_minimize_grab_custody.py`（H-1 の回帰 + M-3）

| # | 内容 |
|---|---|
| A10 | **H-1 の回帰**: 最小化 → 新モーダル N を開く → **H と N の両方を破棄** → 復元 で、**生存かつ表示中の外側モーダルが grab を持つ**（`grab_current()` が `None` でない） |
| A11 | **M-3**: `<Unmap>` 時に **`grab_current()` が `KeyError`** を送出する状況では**預からない**（`grab_release` 呼び出し 0 回 / `_custody_window` が `None` のまま） |
| A12 | **M-3**: `<Unmap>` 時に**保持者が破棄済み**なら預からない |
| A13 | **M-3**: **既に預かり中**なら 2 回目の `<Unmap>` で記録を上書きしない |

### 3. テストのモジュール状態の初期化（M-4）

- `tests_ui/test_modal_grab.py` と `tests_ui/test_minimize_grab_custody.py` の `setUp` で、
  **`_app_minimized` も `patch.object` で初期化**する（現在は `_active_modals` / `_custody_window` のみ）。
  **`test_modal_grab` 単独実行後に `_app_minimized` が True のまま残る**ことを実測で確認済み
  （後続モジュールが「最小化していないのに差し戻しが起きうる」状態で走る）。
- 既存のアサーションは**弱めない**（追加・初期化の変更のみ）。

### 設計メモ / 制約

- **`<Map>` / `<Unmap>` のガードと台帳の仕様は変更しない**。追加するのは `restore_grab` の条件の
  組み替えのみ（**分岐は増やさない**）。
- **破棄済みの窓を `_custody_window` に置くことを許す**のが v0.6 の要点。
  `<Map>` が必ず預かりをクリアするため、状態が滞留しない。
- `deiconify()` / `lift()` / `focus_force()` は本タスクでも呼ばない。

## 含まない

- `<Map>` 側のロジック変更 / 台帳の仕様変更 / `app.py` の変更
- **M-1 / M-2 / L-2 の文書反映**（正本・アーカイブへの記載は **task_05**）
- 統合確認の再実施・実機目視（**task_04** に戻って実施）
- 正本反映・暫定仕様の凍結（**task_05**）

## 確認

python は**リポジトリルートの `.venv`**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
**実測は `verifier`**。

1. `compileall -q keyseq main.py tests tests_ui` が clean
2. `unittest tests_ui.test_minimize_grab_custody` が全 pass（**A1〜A13**）
3. `unittest tests_ui.test_modal_grab` が全 pass
4. `unittest discover -s tests` / `discover -s tests_ui` が全 pass（既存件数は減らない）
5. `tests.smoke_app` が通る
6. **変異検査**（確認後に必ず復元し、`keyseq/` の差分が本タスクの意図した変更だけであること）:
   - **M7**: 差し戻しから「破棄済みでも戻す」拡張を元に戻す（v0.5 相当）→ **A10 が fail**
   - **M8**: `<Unmap>` の `grab_current()` の `KeyError` 吸収を外す（例外を通す）→ **A11 が fail**

## 完了条件

- 上記確認が pass・**`reviewer` 採用**。
- 実機目視は **task_04** でユーザーが実施（本タスクでは行わない）。
