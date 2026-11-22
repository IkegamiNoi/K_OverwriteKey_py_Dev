# 28_refactor_mac_support

phase 75（macOS 対応）の `/refactor_check` で「推奨」になった 2 か所の分割案。**挙動は変えない**（メッセージ・保存ファイル・公開面〔`get_backend()` と `install_minimize_grab_custody(app)`〕は今のまま）。ユーザー承認前に実施しない。

判定（PHASE_BASE = `47132f80`・変更 104 ファイル）: M1 = 1 件（下の R1）/ M2 = 1 件（R2）/ M3・M5 = 該当なし / M4 = `OsBackend(` と `Capabilities(` が 0 → 2（新しい型を各 OS の backend で 1 回ずつ作るだけなので非該当）/ M6 = 未測定。

## 項目 0: 安全網の確認

- 対象の領域は `tests/test_os_backend_contracts.py`・`tests/test_macos_*`（Mac の backend のモックのテスト）・`tests_ui/test_minimize_grab_custody.py`・`tests_ui/test_modal_grab.py` が覆っている見込み。実施前に verifier で次を確かめ、穴があれば特性テストを先に足す。
  - Windows: `compileall` / `tests` 全件 / `tests_ui` 全件 / smoke が pass
  - Mac: `tests` 全件と、上の tests_ui の 2 本（モジュール指定）が pass
- R1 は Mac のファイルなので **Mac でのテストと簡単な実機確認（フック開始・置換・メニュー・最小化）が要る**。

## R1: `macos/backend.py` を 1 クラス 1 ファイルへ分ける

- 対象: `keyseq/infrastructure/os_backend/macos/backend.py`（791 行・新規・M1）
- 問題: `MacKeyboardBackend`（83〜341）・`MacMouseBackend`（342〜421）・`MacWindowBackend`（422〜639）・`MacTkKeyTranslator`（640〜681）・`MacImeBackend`（682〜771）・`MacAppIdentity`（772〜782）と組み立て `create_backend()` が 1 ファイルにある。Windows 側は `windows/` で `keyboard_backend.py` / `mouse_backend.py` / `tk_key_translator.py` 等に分かれていて、両 OS で探し方が違う。
- どう変えるか: Windows 側と同じ分け方にする。

  ```text
  macos/
    backend.py            # create_backend() と組み立てだけ（〜40 行）
    keyboard_backend.py   # MacKeyboardBackend + _Hook・_normalize_key_name・_physical_flags・_unicode_chunks
    mouse_backend.py      # MacMouseBackend
    window_backend.py     # MacWindowBackend
    tk_key_translator.py  # MacTkKeyTranslator
    ime_backend.py        # MacImeBackend
    app_identity.py       # MacAppIdentity
  ```

  - 移した後に `backend.py` から各クラスを再輸出しない（旧パスの横流しの禁止・`file_organization_rules.md`）。テストの import と patch 先を新しいモジュールへ直す。
- 完了条件: 上の項目 0 のコマンドが両 OS で pass・AST の import 境界のテストが pass・`grep -rn "macos.backend import Mac" keyseq tests tests_ui` が 0 件。
- リスクと戻し方: patch 先の取りこぼしでテストが実物の pyobjc を呼ぶ（Mac のみ）。1 コミットで行い、失敗したら revert する。
- 依存: なし。

## R2: `install_minimize_grab_custody` の入れ子の関数を外へ出す

- 対象: `keyseq/presentation/modal.py:86`（98 行・phase 75 で 71 行変更・M2）
- 問題: 最小化での預かり（`deferred_check`）と戻し（`deferred_return`）・イベントの受け口（`take_custody` / `return_custody`）・台帳の判定（`belongs_to_app`）の 5 つが 1 つの関数の中の閉包で、どれか 1 つだけを直す・テストするのが難しい。
- どう変えるか: 閉包を `app` を引数に取るモジュールの関数へ出し、`install_minimize_grab_custody` は bind だけにする。

  ```python
  def install_minimize_grab_custody(app):
      get_backend().window.install_minimize_preparation(app)
      app.bind("<Unmap>", lambda e: _take_custody(app, e), add="+")
      app.bind("<Map>", lambda e: _return_custody(app, e), add="+")

  def _belongs_to_app(app, window) -> bool: ...
  def _deferred_check(app) -> None: ...     # 隠す・grab を預かる
  def _deferred_return(app) -> None: ...    # 戻す・grab を返す
  ```

  - モジュールの状態（`_app_minimized` 等の global）と処理の順は変えない。
- 完了条件: 項目 0 のコマンドが両 OS で pass・`modal.py` の 80 行を超える関数が無い。
- リスクと戻し方: Windows / Mac の最小化の目視（ダイアログを開いたまま最小化して戻す）が要る。1 コミットで行い revert で戻す。
- 依存: なし（R1 と独立）。

## 実施の時期（ユーザー判断）

(a) phase 75 の追加タスク（`task_15_refactor`）として起票 / (b) 次フェーズ前の独立ミニフェーズ / (c) 見送り（`current.md` の別タスク化候補へ）
