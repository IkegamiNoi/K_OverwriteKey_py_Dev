# idea_60_help_input_during_modal.md

## 概要

**ダイアログ（モーダル）からヘルプを開くと、ヘルプの絞り込みの入力欄にカーソルが入らない。**
ヘルプはモーダルでない普通の窓で、ダイアログが grab を持っている間は Tk がヘルプの窓への入力を止めるため。モーダルの間もヘルプを操作できるようにするかを決める。

## 起票経緯（2026-11-17）

phase 75 task_11d の Mac 目視の際に、ユーザーが報告。Windows でも起きるかは未確認（Tk の grab の通常の動きなので起きる見込み）。

## 現状

- `keyseq/presentation/help/help_window.py`・`help_window_controller.py`: ヘルプの窓は grab を取らず、開いたときに絞り込み欄へ `focus_set`（`help_window.py:124-128`・`help_window_controller.py:56`）。
- モーダルは `keyseq/presentation/modal.py` の `grab_modal`（ローカルの grab）。grab の間、grab の窓とその子孫以外の窓はクリック・キー入力を受けない。

## 提案（方向性・要設計）

- 案 A: ダイアログからヘルプを開いたときは、ヘルプの窓をダイアログの transient の子として開き、grab をヘルプへ移して、閉じたらダイアログへ戻す（ヘルプの間はダイアログを操作できない）。
- 案 B: ヘルプを開いている間だけ grab を外す（ダイアログの外も操作できてしまうので、モーダルの意味が崩れる）。
- 案 C: 仕様として受け入れ、ヘルプはダイアログを閉じてから使う旨をヘルプ・ツールチップに書く。

## 想定スコープ

- 含む: ヘルプの窓と modal の grab の関わり（presentation）。Windows での確認。
- 含まない: ヘルプの本文。
- 仕様変更: 案 A / B は `features.md` のヘルプ・モーダルの節に関わる見込み。
