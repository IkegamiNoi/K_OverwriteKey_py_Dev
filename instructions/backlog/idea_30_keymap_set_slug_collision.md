# idea_30_keymap_set_slug_collision.md

## 概要

子ファイル名の算出に使う `slugify_file_stem` で、**別々の keymap_set 名が同一 stem へ丸まる衝突**が
起こり得る（例: 記号だけが違う名前）。衝突した側の既定保存先が重なる。

## 起票経緯（2026-09-22）

Phase β（phase 06 / 子ファイルの保存ダイアログ）の `/refactor_check` からの候補送り。
当時は**受入条件 8 の範囲外**として `instructions/phase/current.md`「別タスク化候補」へ送っていた。
2026-09-22 の current.md 整理でユーザー判断により idea へ昇格。

## 現状

- `keyseq/application/config_service/save_path_resolution.py:197` の `slugify_file_stem`。
  同ファイル内の**8 箇所**（keymap / trigger_set / sequence / プリセットの既定パス算出）が使う
- 同一保存**計画の中**での衝突は `used_paths` による連番回避がある
  （`save_path_resolution.py:113-123` 付近）が、**別の keymap_set から生まれた同一 stem**は
  互いを知らない
- 実害の見込み: 既定の保存先が提案された状態で気付かず上書き保存すると、
  別の構成セットの子を踏む。ただし**子の共有判定（§5.8.4）と確認ダイアログ（§5.8.5）**が
  どこまで受け止めるかは未確認

## 提案（方向性・要設計）

- まず**どこまで実害が出るか実測**する（既存の共有判定・参照元記録で防げているか）。
  防げているなら**クローズ**でよい
- 防げていない場合の案: ①stem 衝突時に keymap_set 側の識別子を付与 ②保存直前に実在確認して
  連番回避を通す ③既定パスの提案時に警告

## 想定スコープ

- 含む: `save_path_resolution.py` の stem 算出と、必要なら §5.8 の該当節
- 含まない: 既存ファイルの改名・移行
- 影響レイヤ: application（+ 仕様改訂の可能性）。**着手時は実測での切り分けが先**
