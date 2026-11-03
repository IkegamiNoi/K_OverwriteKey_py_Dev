## 3. アーキテクチャ方針

### 3.1 採用アーキテクチャ

本ツールはオニオンアーキテクチャを採用する（パッケージは `keyseq/` 配下）。

### 3.2 依存ルール

* 外側の層は内側の層に依存してよい
* 内側の層は外側の層に依存してはならない
* domain 層は tkinter / keyboard 等の UI・フック実装に依存してはならない
* infrastructure 層は domain / application のインターフェースに従って実装する
* presentation 層は application 層を通じて操作を実行する
* **presentation は `application/config_service/` の内部モジュールを直接参照しない**。
  公開面は **`ConfigService` の公開 API（委譲メソッドおよび公開クラス定数 `INTERNAL_*` 等。
  `codebase_map.md`）と `application/config_service/contracts.py`** とする
  * `contracts.py` は**判定名・理由コード・結果型（データクラス）の唯一の定義場所**。
    表示文言の純関数（`reference_cleanup_text.py` / `orphan_sweep_text.py` /
    `quarantine_manage_text.py`）と対応する `config_io/` の IO クラスは、ここから import する
  * **実装モジュール（`orphan_scan` / `quarantine` 等）の直参照は定数・型・関数のいずれも不可**
  * `contracts.py` は **`config_service` 内の他モジュールを import しない**
    （依存は実装モジュール → `contracts` の一方向。stdlib は可）
* **application は presentation（`app`）を参照しない**。走査対象・保護対象などの入力は
  **引数で明示的に受け取る**
* **`keyseq/shared/` は全層（presentation / application / domain / infrastructure）から依存してよい**（Global Shared・phase 72）。
  shared は他の層に依存せず、**標準ライブラリだけ**を使う。今あるのは画面の文言の多言語対応 `shared/i18n/`（`codebase_map.md`）
  * 内側の層で作られて画面に出る文言も、その層で `shared.i18n.tr` を使って作る（言語は実行中に変わらないので、表示の時点で訳すのと結果は同じ）

### 3.3 各層の責務

#### domain（`keyseq/domain`）

* トリガー
* アクション
* 出力シーケンスのロジック

#### application（`keyseq/application`）

* ユースケース
* 実行制御（出力シーケンス実行・run_to_end）

#### infrastructure（`keyseq/infrastructure`）

* keyboard によるグローバルフック
* JSON 入出力（ConfigService）

#### presentation（`keyseq/presentation`）

* UI（tkinter）: FullView / CompactView / KeyboardWindow / ダイアログ
* イベント処理・各コントローラ
* ヘルプ・ライセンスの表示は `keyseq/presentation/help/` に置く。`HelpWindowController` はヘルプ窓を、`LicenseWindowController` はライセンス窓をそれぞれ管理し、ヘルプ本文・絞り込み・同梱ライセンスの読込もこのパッケージ内で行う。バージョン情報の表示は、層の外の `keyseq/__init__.py` が公開する `__version__` を参照する。
* 同梱データ（LICENSE・ヘルプ本文・ライセンス全文・アイコンの土台の画像）の位置は `keyseq/presentation/bundled_paths.py` の `bundled_root()` に集約する（exe 化時の変更点を 1 か所に・phase 71 で `help/` から昇格）。
* タスクバーのアイコン（フックの状態の印）は `keyseq/presentation/status_icon/` に置く。印の形の計算は Tk に依存しない純関数（`badge_shapes`）、画像の合成と窓への設定は `StatusIcon`。AppUserModelID の設定（Win32）は infrastructure の `win32_window.set_app_user_model_id` で、エントリーポイント `main.py` から呼ぶ（最初の窓を作る前に 1 回だけ設定するため）。

### 3.4 UI スレッド

* UI 更新は必ず UI スレッドで行う（`after()` を使用）
* フック処理は UI と分離する
* file_line のファイル読込はワーカー（デーモンスレッド）で行う。ワーカーは Tk を呼ばず、共有状態は `FileLineLoader` の 1 つのロックの下だけ。結果は UI スレッドの確認タイマー（`after`）で受け取る（phase 38・`features.md` §4.2.7）

### 3.5 実装状態の参照先

クラス構成・各コントローラの責務分担の現状は
`instructions/common/codebase_map.md` を正とする。

---
