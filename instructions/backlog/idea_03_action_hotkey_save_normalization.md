# idea_03_action_hotkey_save_normalization.md

## 概要

**アクションの hotkey 保存経路がプリセットと非対称**で、生値のまま保存される点を統一したい。
プリセット編集は保存時に `validate_hotkey` を通して**正規化済みの値**を保存するが、
アクション編集（シーケンス）は**検証・正規化をせず入力そのまま**を保存する。
実行時には正規化されるため機能実害はないが、保存 JSON に生値（例: `"Ctrl+ A"`）が残る一貫性の欠落。

## 起票経緯（2026-07-18）

出所: phase [02_hotkey_validation](../phase/02_hotkey_validation/phase.md) task_04 の実機目視。
`config/user/sequences/a.json` の hotkey アクションが `"value": "Ctrl+ A"`（未正規化）で
保存されているのをユーザーが確認し、切り分けの結果 **task_04 とは無関係な既存の非対称**と判明。
ユーザー方針: 今フェーズでは触らず本 idea として記録（挙動変更を伴うため別案件）。
暫定仕様 01 §6-11 の文言補正（プリセット＝保存時正規化／アクション＝実行時正規化）は
**本 idea をそのうち実施する前提**で行う。

## 現状

- アクション保存: `keyseq/presentation/dialogs.py:123-134`（`ActionDialog.on_ok`）。
  `v = self.value_var.get()` を**検証・正規化せず** `_dialog_result["value"]` へ格納
  （空チェックのみ）。不正 hotkey も保存時には弾かれない。
- プリセット保存: `keyseq/presentation/dialogs.py:440,475`（`PresetDialog`）。
  `err_msg, normalized = self.parent.validate_hotkey(value)` を通し、**`normalized` を保存**。
- 実行時正規化: `keyseq/application/action_executor.py:76-84`（`_execute_hotkey`）。
  実行時に `validate_hotkey` → `send_hotkey(normalized)` で正規化・検証されるため
  **アクションは正しく発火し、不正 hotkey は実行時に `_on_action_error` で捕捉**される。
- 既存データ: 既に保存済みの `config/user/sequences/*.json` には生値が残っている。
- 関連正本: hotkey 検証の担当層は phase 02 で domain/application へ移設済
  （`keyseq/domain/hotkey.py` / `keyseq/application/hotkey_service.py`）。

## 提案（方向性・要設計）

いずれも**挙動変更を伴う**ため、着手時に設計を確定してから実装する（`spec_change_workflow.md`）。

- **案 1: 保存時に正規化**（`ActionDialog.on_ok` で `validate_hotkey` を通し `normalized` を保存）。
  プリセットと対称になる。ただし保存済みファイルは生値のまま残るため**新旧混在**が生じる。
- **案 2: 読込時に正規化**（ロード経路で正規化）。既存ファイルも吸収できるが、正規化の入口が増える。
- **案 3: 保存時に検証してエラー提示**（不正 hotkey をアクション保存時に拒否）。
  現状「保存は通り実行時にエラー」という UX を変えるため、要ユーザー合意。
- 併せて要検討: 正規化の入口を 1 箇所に集約するか（保存 or 読込のどちらか）、後方互換の扱い。

## 想定スコープ

- 含む: `keyseq/presentation/dialogs.py`（`ActionDialog`）中心。案 2 を採るなら読込経路（application）も。
- 含まない: 単キー検証の統一（暫定仕様 01 §7 の別ネタ）／hotkey 文法自体の変更。
- 影響レイヤ: presentation（＋案により application）。
- 仕様変更: **あり**（保存値・検証タイミングの変更）。優先度: **低**（機能実害なし・体裁と一貫性の改善）。
