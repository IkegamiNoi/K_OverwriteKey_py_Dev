# task_03_integration_and_close

## 目的

phase 22（task_01 / task_02）の成果を統合確認・二次レビュー・実機目視で確かめ、**正本へ昇格**して
暫定仕様 19 を凍結し、フェーズを完了する（`.claude/rules/task_execution.md`「フェーズ完了時」）。
**コードは原則変更しない**（レビュー指摘の採用分は枝番タスクで行う）。

## 対象範囲（検証・レビュー・正本反映・記録）

### 統合確認（`verifier`）

1. `-m compileall -q keyseq main.py tests tests_ui`
2. `-m unittest discover -s tests`（**478 から減っていないこと**）
3. `-m unittest discover -s tests_ui`（**445 から減っていないこと**）
4. `-m tests.smoke_app`

### 二次レビュー（差分 = `0518c93..HEAD`）

- `deep-reviewer`: 暫定仕様 19 と実装の整合 / 解放と `FAILSAFE` 復元の担保 / 後方互換（`drag` 無しの既存 JSON と UI）/
  層と依存（`ctypes` 不使用・所要時間の算出位置）/ テストの検出力。
- `codex-reviewer`: 標準レビュー。
- 指摘は提示のみ。採否はユーザー。

### 実機目視（ユーザー・暫定仕様 19 §8-11）

1. メモ帳等で**文字列の範囲選択**ができる（**短距離 50px 程度 / 長距離 500px 程度の両方**）。
2. エクスプローラ等で**ドラッグ&ドロップ**ができる。
3. **速度を変えると移動の速さが変わる**（100px 超の距離で比較する）。
4. 既存の**単発クリック**のアクションが従来どおり動く。
5. 最長（5 秒クランプ）のドラッグの後、**停止キー・トグルが正常に効く**。
6. **離す点を画面の隅**に指定したドラッグが完了し、ボタンが押しっぱなしにならない。
7. ドラッグ中に**物理マウスを画面の隅へ動かしても中断せず**、終了後にボタンが離れている。
8. ドラッグ**以外**のマウスクリックでは FailSafe が従来どおり効く（座標 (0,0) のクリックでエラーになる）。

### 正本への昇格（暫定仕様 19 §10・**メインセッションが実施**）

- `instructions/common/spec_detail/data_schema.md` に **§5.11「アクション要素」を新設**し、
  `hotkey` / `text` / `mouse_click`（+ ドラッグの `drag` / `to_x` / `to_y` / `drag_speed`）を規定する。
  §5.2（単一JSON の `triggers[].actions`）・§5.6（sequence）から参照させる。**§5.6 の下にぶら下げない**。
- **マウスのボタンも例外時に必ず離す**ことと、**ドラッグ中は pyautogui の FailSafe を無効化する**こと
  （理由と失うもの = 四隅の緊急停止）を明文化する。
- **マウス操作は send guard の対象外**であることを明文化する。
- `instructions/common/codebase_map.md`: 「キーの送信」節の隣に**マウス操作**の記述を追加
  （`click_mouse` / `drag_mouse`・所要時間の算出位置・`ActionDialog` のドラッグ UI）。
- **暫定仕様 19 を凍結**（ヘッダを「凍結（2026-MM-DD・正本反映済）」へ書き換え。以後編集しない）。

### 記録

- `instructions/phase/22_mouse_drag_action/integration_result.md`（統合確認の件数 / レビューの採否 / 実機目視の結果）。
- `.claude_data/state/decisions_archive/22_mouse_drag_action.md` + `decisions.md`「アーカイブ索引」へ 1 行。
- `instructions/phase/current.md`: 完了記載（アクティブなし・直近の領域の数行・次採番 phase 23 / 暫定 20 / decisions 23）。
- **「別タスク化候補」への追記**: `ActionDialog` の座標取得リスナーは、ダイアログ破棄後に `after(0, ...)` が走ると
  `TclError` になりうる（**task_02 以前からの既存挙動**・task_02 の reviewer 参考指摘）。
- `/refactor_check` の実行と判定の記載（メトリクス収集は `verifier`。**PHASE_BASE = `0518c93`**）。
- 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`（採否はユーザー）。
- 起票元は idea ではない（ユーザー要望）ため `INDEX_done` への移動は不要。**idea_23 は未着手のまま残す**。

## 読むファイル

1. `instructions/history/19_mouse_drag_action.md`（§8 受け入れ条件 / §10 正本反映）
2. `instructions/phase/22_mouse_drag_action/phase.md`
3. `instructions/common/spec_detail/data_schema.md`（§5.2 / §5.6 / 冒頭の後方互換方針。**昇格で編集**）
4. `instructions/common/codebase_map.md`（「キーの送信」節の前後。**昇格で編集**）

## 含まない

- レビュー指摘の修正（ユーザー採否の後、枝番タスク）。
- ホイール / 押す・離すアクション（idea_23）/ 別スレッド化 / macOS 対応 / 座標取得 UI の 1 ボタン化。

## 確認

- 統合確認 4 項目が pass。
- 二次レビュー・完了判定前レビューの指摘の採否がユーザーにより決定済み。
- 実機目視 1〜8 がユーザーにより確認済み。
- 正本 `data_schema.md` §5.11 が新設され、暫定仕様 19 が凍結済み。

## 完了条件

- 上記確認を満たし、記録済み・**reviewer 採用**（記録内容と正本反映の整合確認）。
- 実機目視は本タスクで実施。
