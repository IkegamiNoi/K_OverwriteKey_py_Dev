# 進捗と手動確認の申し送り

- 作成日: 2026-07-05 / 随時更新

## 重要: 手動GUI確認について
本作業は自動検証（compileall / unittest tests / unittest tests_ui / smoke）は全て実行・全緑を
確認しているが、計画書が「手動確認（必須）」とする対話的GUI操作（実際にキーを押す・
ダイアログのボタンを押す等）は、この実行環境では実施できない。
tests_ui による特性テストで観測可能な契約は固定済みだが、下記の手動項目は
**利用者による最終確認を推奨**する。

## 進捗
| 項目 | 状態 | コミット |
|---|---|---|
| 0 UI特性テスト | 完了 | test: app.py 分割前の UI 特性テストを追加した。 |
| S1 デッドコード削除 | 完了 | refactor: 未使用のデッドコード2件を削除した。 |
| S2 listbox_utils 抽出 | 完了 | refactor: Listbox選択ヘルパをlistbox_utilsへ抽出した。 |
| S3 ConfigPaths 抽出 | 完了 | refactor: パス解決をConfigPathsへ抽出した。 |
| S4 DirtyStateTracker 抽出 | 完了 | refactor: ダーティ状態管理をDirtyStateTrackerへ抽出した。 |
| S5 SingleKeyCaptureController 抽出 | 完了（自動検証のみ） | refactor: 停止/トグルキーのキャプチャをSingleKeyCaptureControllerへ統合した。 |

## S5 の手動確認項目（利用者にお願いしたい）
`py main.py` で起動し（※要 PYTHONPATH=. または通常起動）:
1. 「キー入力で取得」→ F9 押下 → 停止トリガー欄に `f9` が入り「未保存」になる
2. もう一度取得 → Esc → キャンセルされ値が変わらない
3. トグルキー側でも同様に取得できる
4. 停止キーに設定済みのキーをトグルキーへ取得しようとするとエラーダイアログが出る
5. 「クリア」で空に戻る

## S5 実装メモ
- 停止キー版・トグルキー版のほぼ同型2実装を `key_capture.py` の
  `SingleKeyCaptureController` 1実装へ統合した（計画書が唯一許容する統合）。
- 固有値（data_key / 各ウィジェット属性名 / label / 単キー例 / 競合チェック群）は
  コンストラクタ引数化。エラーメッセージ文言は元コードと完全一致を確認:
  - 単キーエラー: `{label}は単キーのみ対応です（例: {example}）。`
  - 競合エラー: `{label}が{相手名}と重複しています:\n{key}`
  - 不明キー: `不明なキー名です:\n{key}\n\n{e}`
- 相互排他（片方開始時にもう片方を止める）は App ファサード
  `_start_stop_key_capture` / `_start_toggle_key_capture` で実現。
  controller.stop() は `if not capturing: return` でガードするため元と等価。
- `_capturing_stop_key` / `_capturing_toggle_key` は App に読み取りプロパティを残置
  （app.py の `_is_menu_shortcut_enabled` 相当・`show_compact_view`・tests_ui が参照）。
- 統合で不要になった `App._normalize_tk_key_for_trigger` を削除。それに伴い
  app.py で未使用となった `from ...tk_keys import normalize_tk_keysym` も削除
  （挙動影響なしの直接的な死コード除去）。
