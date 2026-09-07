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
  公開面は `ConfigService` の委譲メソッド（`codebase_map.md`）とする
  * **例外（当面の許容）**: **判定名・理由コードなどの定数と、結果を運ぶデータクラス**の
    import は許す（表示文言の純関数がこれらで分岐・整形するため。`reference_cleanup_text.py` /
    `orphan_sweep_text.py` / `quarantine_manage_text.py` / 対応する `config_io/` の IO クラス）。
    **関数・ロジックの直参照は不可**
  * 公開面モジュールへ定数と結果型を集約する是正は
    [idea_14](../../backlog/idea_14_config_service_public_surface.md) で追跡する
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
