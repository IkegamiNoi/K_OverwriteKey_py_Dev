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

### 3.3 各層の責務

#### domain（`keyseq/domain`）

* トリガー
* アクション
* シーケンスのロジック

#### application（`keyseq/application`）

* ユースケース
* 実行制御（シーケンス実行・run_to_end）

#### infrastructure（`keyseq/infrastructure`）

* keyboard によるグローバルフック
* JSON 入出力（ConfigService）

#### presentation（`keyseq/presentation`）

* UI（tkinter）: FullView / CompactView / KeyboardWindow / ダイアログ
* イベント処理・各コントローラ

### 3.4 UI スレッド

* UI 更新は必ず UI スレッドで行う（`after()` を使用）
* フック処理は UI と分離する

### 3.5 実装状態の参照先

クラス構成・各コントローラの責務分担の現状は
`instructions/common/codebase_map.md` を正とする。

---
