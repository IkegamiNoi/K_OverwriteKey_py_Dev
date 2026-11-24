# task_02a_review_fixes

## 目的

フェーズ完了判定前レビュー（2026-11-25・ユーザー判断「推奨どおり」・decisions.md の phase 80 の節）で採用した 4 点を直す。
正本 = `features.md` §4.6 の例外（Windows）（App から transient の連鎖で **3 段目以降**のモーダル）。
**presentation（`modal.py`）とテストのみ・契約・JSON スキーマ不変**。

## 対象範囲（modal.py + テスト）

### `keyseq/presentation/modal.py`

1. **Codex 1・4 段目以降の検出**: `_deferred_check` の切り離しは、**transient を変える前に**台帳の全窓の深さと元の親を求めてから外す
   （今は開いた順に測っては外すため、3 段目を外した後の 4 段目は連鎖が途切れて対象外になる）。
   記録済み（`_detached_transients` にある）窓の扱い（再最小化で隠し直す）は今のまま。
2. **deep 3・予約の取り残し**: `_deferred_return` で付け直しを予約する前に、既存の `_reattach_transients_id` があれば `after_cancel` する。
   `_reattach_transients` は冒頭で `_app_minimized` が真、または `app.wm_state() == "iconic"` なら何もしない（記録は残す。予約 id は None に戻す）。
3. 切り離しの処理を `_deferred_check` から 1 つの関数（例: `_detach_deep_transients(app)`）へ切り出してよい（関数 30 行の目安・deep 10）。挙動は変えない。

### `tests_ui/test_minimize_grab_custody.py`（テストの追加）

既存の task_02 のテスト（`test_deep_transient_*` 等）の**後ろへ**足す（既存テストの途中に差し込まない・既存の期待値は変えない）。

- **4 段**: アクション → プリセット管理 → プリセット追加 → その子の `PresetDialog(add, ...)`（transient = 追加）を開き、バックエンドの新メソッドを `True` に patch。
  最小化の間は 3 段目・4 段目とも transient が空、復元と待ちの後に元の親へ戻り、4 枚とも viewable、grab = 4 段目（Windows では 4 段目の `IsWindow(winfo_id())` が真）
- **予約の取り残し**: 3 段で最小化 → 復元（付け直しの予約がある状態）で `modal._deferred_return(self.app)` をもう一度呼んでも、予約が 1 つだけ（2 回目の前の id が取り消される）であることを確かめる。
  さらに `modal._app_minimized = True` の状態で `modal._reattach_transients(self.app)` を呼ぶと transient を付け直さず記録が残る
- **フォーカス（deep 4）**: 3 段で最小化 → 復元と待ちの後、`self.app.focus_get()` がプリセット追加の窓の中（`str(focus).startswith(str(add))`）。`_is_app_foreground` は setUp で偽に patch 済みなので、強制アクティブ化に頼らず `focus_set` で戻る経路を見る

### `tests/test_os_backend_contracts.py` / `tests/test_macos_window_backend.py`（deep 7）

- `releases_topmost_during_modal` の既存テストと同じ形で、`detaches_deep_transients_during_minimize` の契約（引数なし・bool）と Mac = False のテストを足す。
  Windows = True のテストは既存の Windows バックエンドのテストの形があれば同じ形で（無ければ足さない）

## 読むファイル

- `keyseq/presentation/modal.py:100-250`（編集対象）
- `tests_ui/test_minimize_grab_custody.py:1-150`（編集対象・task_02 の追加テストの形）
- `tests/test_os_backend_contracts.py:30-60`・`tests/test_macos_window_backend.py:1-40`（編集対象・手本）
- `instructions/phase/80_win_d_restore_blank_dialog/tasks/task_02_detach_deep_transients.md`（前タスクの対象範囲）

## 含まない

- 正本の修正（メインが済ませた: 理由の文「外さないと」）・記録（task_03）
- 保留の指摘（Codex 2 の付け直し後の再検証の仕組み・最小化の間に開いた深い窓・`_belongs_to_app` と `_transient_depth` の統合）
- Mac の挙動の変更

## 確認

- verifier: `compileall` clean / `unittest discover -s tests` 全 pass / `tests_ui.test_minimize_grab_custody` 全 pass（3 回）/ modal を使う tests_ui のモジュール pass / `-m tests.smoke_app` pass
- 追加テスト（4 段・予約・フォーカス・契約）が pass
- 実機目視: なし（task_02 で実施済み。挙動の変更は 4 段の検出と予約の取り消しのみで、アプリに 4 段の経路は無い）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実装エージェント = `codex-implementer`

## 結果（2026-11-25 完了）

- 実装 = `codex-implementer`（Luna high・単独）。メインの追加修正 2 点: 1 回目のループの `wm_transient()` を try で囲む / フォーカスのテストを 3 段に（4 段目もパス名が追加の窓で始まるため）
- verifier: compileall / tests 2282 pass（skip 9）/ `test_minimize_grab_custody` 38 件 × 3 回 / tests_ui 全体 1330 pass / smoke pass
- reviewer = 採用（低 2 件は参考: `_app_minimized` の直接書き換えは setUp の patch で戻る / 破棄後の after は App の破棄で消える）
