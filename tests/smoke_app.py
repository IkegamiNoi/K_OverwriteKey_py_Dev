"""アプリを 2 秒だけ起動して自動終了するスモークテスト。

注意: フック開始は行わない（グローバルフックを張らない）。
GUI が開ける環境（通常のデスクトップセッション）で実行すること。
"""
from keyseq.presentation.app import App


def main():
    app = App()
    app.after(2000, app.destroy)
    app.mainloop()
    print("SMOKE OK")


if __name__ == "__main__":
    main()
