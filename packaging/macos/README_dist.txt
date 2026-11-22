Key Replacer Sequencer
Copyright (C) 2026 池上ノイ (Ikegami Noi)
本ソフトウェアは GNU General Public License v3 以降で利用できます。
対応するソースコード: https://github.com/IkegamiNoi/K_OverwriteKey_py_Dev のタグ v{version}
PyInstaller のブートローダには GPL の例外が適用されます。第三者ライセンスはヘルプの「ライセンス」画面で確認できます。
sources/ には GPL / LGPL の依存ライブラリ mouseinfo と pynput のソースアーカイブを同梱しています。
pynput を変更版に差し替えるには keyseq.app/Contents/Resources/pynput/ のファイルを置き換え、`codesign --force --deep -s - keyseq.app` で署名し直してください。
初回起動時に「システム設定 > プライバシーとセキュリティ > アクセシビリティ」で keyseq を許可してください。新しい版に入れ替えたときや、差し替え・再署名の後は、一覧の keyseq がオンのままでも効かないことがあります。そのときは keyseq を終了し、一覧の keyseq を「−」で消して（またはターミナルで `tccutil reset Accessibility io.github.ikegaminoi.keyseq`）、起動し直してから許可し直してください。
署名・公証をしていないため、別の Mac では Gatekeeper が起動を止めることがあります。「システム設定」>「プライバシーとセキュリティ」>「このまま開く」を選ぶか、`xattr -dr com.apple.quarantine keyseq.app` を実行してください。

Key Replacer Sequencer
Copyright (C) 2026 Ikegami Noi
This software is licensed under the GNU General Public License v3 or later.
Corresponding source: https://github.com/IkegamiNoi/K_OverwriteKey_py_Dev, tag v{version}
The PyInstaller bootloader is covered by its bootloader exception. Third-party licenses are available in Help > Licenses.
The sources/ directory includes source archives for the GPL/LGPL dependencies mouseinfo and pynput.
To replace pynput with a modified version, replace the files in keyseq.app/Contents/Resources/pynput/ and re-sign with `codesign --force --deep -s - keyseq.app`.
On first launch, allow keyseq in System Settings > Privacy & Security > Accessibility. After installing a new version, replacing files or re-signing, keyseq may not work even though it is still switched on in the list. In that case, quit keyseq, remove it from the list with "-" (or run `tccutil reset Accessibility io.github.ikegaminoi.keyseq` in Terminal), launch it again and grant the permission again.
Because the app is not signed or notarized, Gatekeeper may block it on another Mac. Choose “Open Anyway” in System Settings > Privacy & Security, or run `xattr -dr com.apple.quarantine keyseq.app`.
