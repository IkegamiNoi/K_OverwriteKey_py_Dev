# task_06_edit_ui

## 目的

暫定仕様 26 §11.1・§11.2（編集 UI と追加・削除・移動）と §2-19（「末尾に追加」チェック欄）を実装する。
- 編集ダイアログで `system`（ループ / カウンター +1 / カウンターを 0 に / 待機 / 戻す / 先頭へ）と `file_line` を作成・編集できる。
- 追加ダイアログに「末尾に追加」チェック欄（既定 ON・開くたび ON）。OFF なら一覧の選択行の直後へ挿入（選択が無ければ末尾）。全種別。
  挿入しても「次に実行」は元のアクションを指したまま・追加した行を選択状態にしない。
- ループは始まり・終わりを対で追加（間は空）/ 対で削除（中は残す・確認文で示す）/ 深さ 9 超になる追加は拒否 /
  ループの行は他のループの行と入れ替わる移動をしない / 対応が崩れた行は単独で削除でき、編集は開かずその旨を示す。
- ループの行の編集: 始まり・終わりどちらを開いても対の始まりの設定（回数・無限・ラベル）を編集。種別・操作は変更不可。他の行をループへ変える選択肢は出さない。

**presentation + domain（編集規則の純関数）**。application・runner は変更しない（編集後の張り直しは既存の `reset_loop_frames` 呼び出しを使う）。

## 対象範囲（presentation + domain の純関数）

### `keyseq/domain/sequence_editing.py`（新規・純関数）

一覧の編集規則を UI から切り離して置く。`domain/sequence_control.py` の `analyze_loops` を使う。
- `insert_actions(actions, new_items, *, after_index: int | None) -> int`: `after_index` が None なら末尾、そうでなければその直後へ `new_items` を挿入し、
  挿入先の先頭添字を返す（リストはその場で更新）。
- `adjust_position_after_insert(position, insert_at, count) -> int`: 「次に実行」の位置を元のアクションに保つための補正（挿入位置 ≦ 位置なら `count` ずらす）。
- `loop_pair_items(start_fields) -> list[dict]`: 始まり（`type`/`op`/`count`/`infinite`/`label`）と終わり（`type`/`op`/`label=""`）の 2 要素。
- `can_insert_loop(actions, after_index) -> bool`: 挿入後の深さが `MAX_LOOP_DEPTH` を超えないか。
- `pair_index(actions, index) -> int | None`: ループの行の対の添字（対応崩れ・ループ以外は None）。
- `delete_indices(actions, index) -> list[int]`: 削除する添字（対応の取れたループの行なら対の 2 行・それ以外は自分だけ）。
- `can_move(actions, index, delta) -> bool`: ループの行（対応崩れを含む）が他のループの行と入れ替わる移動なら False。範囲外も False。

### `keyseq/presentation/dialogs/action_dialog.py`（と補助モジュール）

- コンストラクタにキーワード引数を追加: `mode: str`（`"add"` / `"edit"` / `"edit_loop"`）・`counter_names: list[str]`（カウンター名の候補）・`config_root: str`。
  既存の呼び出し（`initial` のみ）で従来どおり動くこと。
- 種類に `system` / `file_line` を追加（`edit` のループ以外の行と `add` で選べる。`edit_loop` は種類・操作を固定表示）。
  - system: 操作のコンボ（日本語表示 ↔ op 名の対応）。`edit` モードではループを選択肢に出さない（`add` のみ）。
    - ループ: 回数（既定 1）と「無限」チェック（ON で回数欄を無効）。
    - カウンター系: 編集可能なコンボ（候補 = `counter_names`）。
    - 待機: ミリ秒。
    - 戻す / 先頭へ: 入力欄なし。
  - file_line: ファイル（入力欄 + 参照ボタン〔`filedialog.askopenfilename(parent=self)`〕）/ カウンター名（候補つき編集可能コンボ）/
    文字コード（UTF-8 / Shift_JIS → `utf-8` / `shift_jis`）/ 範囲外（エラーで停止 / 空を送る / 折り返し → `error` / `empty` / `wrap`）。
    保存するパスは `config_service.to_config_relative_or_absolute(path, config_root)` の表記（`data_schema.md` §5.7）。存在は検査しない。
- 入力エラーは既存と同じく `messagebox.showerror` で示し**ダイアログを閉じない**: 回数が 1 以上の整数でない（無限 OFF 時）/ ミリ秒が 1 以上の整数でない /
  カウンター名が空 / ファイルが空。
- 追加モードのみ「末尾に追加」チェック（既定 ON）を出す。結果は既存の `_dialog_result` に加え、ダイアログの属性（例: `append_to_end`）で呼び出し側へ渡す。
- 結果の dict は §3 のキーだけを持つ（ループの始まり: `type`/`op`/`count`/`infinite`/`label`。無限でも `count` を残す）。
- `action_dialog.py` は 418 行で目安超過のため、新しい入力欄の組み立て・値の読み取り・検証は**補助モジュールへ分ける**
  （例: `keyseq/presentation/dialogs/action_control_fields.py`。`dialogs/__init__.py` の再輸出は ActionDialog 以外に増やさない）。

### `keyseq/presentation/controllers/trigger_panel_controller.py`

- `add_action`: カウンター名の候補（`self._app.state.counters` の名前 + アクティブなトリガー一覧の全シーケンスに現れる `counter` の値・重複除去・ソート）と
  `config_root` を渡してダイアログを開く。結果がループの始まりなら `loop_pair_items` で対にする。`append_to_end` が OFF かつ選択行があれば直後、そうでなければ末尾へ
  `insert_actions`。ループで `can_insert_loop` が False なら `messagebox.showinfo` で理由（入れ子が 9 段を超える）を示して追加しない。
  挿入後、「次に実行」の位置を `adjust_position_after_insert` で補正し、`reset_loop_frames` → `refresh_actions`。追加した行を選択状態にしない。
- `edit_action`: 選択行がループの行なら、対応崩れ（`pair_index` が None）は `messagebox.showinfo` で「ループの対応が崩れているため編集できません。削除して追加し直してください」を示して開かない。
  対応が取れていれば対の始まりを `mode="edit_loop"` で開き、結果を始まりの行へ書く。それ以外は `mode="edit"`。
- `delete_action`: `delete_indices` の行を消す。対の削除では確認文を「ループの始まりと終わりを削除します（中の行は残ります）。よろしいですか？」にする。
- `move_action`: `can_move` が False なら何もしない（入れ替えない）。

### テスト

- `tests/test_sequence_editing.py`（新規）: 挿入（末尾 / 直後 / 先頭の直後 / 最後の行の直後）と位置補正 / ループの対の生成 / 深さ 9 の境界 /
  対の添字（正常・対応崩れ・ループ以外）/ 削除の添字 / 移動の可否（通常行はループ内外へ可・ループ行がループ以外と入れ替え可・ループ行どうし不可・対応崩れの行・範囲外）。
- `tests_ui/test_action_dialog_control.py`（新規）: 各種別・各操作の OK で期待どおりの dict / 入力エラーで閉じない（回数・ミリ秒・カウンター名・ファイル）/
  無限チェックで回数欄が無効 / 追加モードだけ「末尾に追加」が出て既定 ON / `edit` でループが選べない / `edit_loop` で種類・操作が固定 / パスの config 相対化。
- `tests_ui/` の既存 trigger panel 系テストの手本に倣い、コントローラの追加（末尾 / 直後 / 位置不変 / 選択しない / 深さ超過の拒否）・ループの編集（始まり・終わり・対応崩れ）・
  対の削除・移動の拒否を確認するテストを追加する（ファイル名は既存の命名に合わせる）。

### 設計メモ / 制約

- `sequence_editing.py` は tkinter・application を import しない。
- 既存の hotkey / text / mouse_click の入力 UI・記録・プリセット・ドラッグの動きは変えない（`tests_ui/test_action_dialog_drag.py` 等が通ること）。
- テストで `messagebox` / `filedialog` を差し替えるときは `patch.object` を優先（モジュール名前空間の patch は避ける）。

## 読むファイル

- `instructions/history/26_sequence_control_actions.md` §2-19・§3・§11.1・§11.2（仕様）
- `keyseq/domain/sequence_control.py`（使う関数・定数）
- `keyseq/presentation/dialogs/action_dialog.py`（編集対象・全体）
- `keyseq/presentation/controllers/trigger_panel_controller.py:490-600`（アクションの追加〜選択）
- `keyseq/application/config_service/__init__.py:738-750`（`to_config_relative_or_absolute`）
- `tests_ui/test_action_dialog_drag.py`（ダイアログの UI テストの手本・先頭 80 行程度）

## 含まない

- 一覧の表示（周回・カウンター値・色分け）・省略表示の要約 → task_07
- 実行側（runner・ステップ・executor）の変更
- 正本・codebase_map → task_08

## 確認

- 静的確認: `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests tests_ui` がエラー無し。
- 単体: `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_sequence_editing -v` が全 pass。
- UI: `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_action_dialog_control -v` と追加したコントローラのテストが全 pass。
- 退行: `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests`・`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` が全 pass、
  `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` が pass。
- `wc -l keyseq/presentation/dialogs/action_dialog.py` が 450 未満（補助モジュールへ分けたこと）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_07 でまとめて実施。
- **試行**（ユーザー判断 2026-09-27）: `codex-delegating-implementer` のサブエージェントを **Luna high**（`reasoning_effort: "high"`）にして実施し、所要時間・トークン・修正の往復を記録する。
