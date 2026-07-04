# R15 申し送り

- `JsonRepository.save_json` を一時ファイル書き込み後に `os.replace` する形へ変更した。
- JSON の `ensure_ascii=False` と `indent=2` は維持している。
- `.tmp` は同一パス隣に作成され、正常保存後は残らない。
