# 单PyQt打包
# nuitka --mingw64 --standalone --show-progress --show-memory --enable-plugin=pyqt6 --nofollow-import-to=numpy,pandas,scipy,cv2,fitz --output-dir=nuitka_out app.py
import asyncio

from qasync import QApplication, QEventLoop

from Autoseek.window import BaseWindow


class Autoseek(QApplication):
    def __init__(self):
        super().__init__([])
        self.loop = QEventLoop(self)
        asyncio.set_event_loop(self.loop)
        self.win = BaseWindow()

    def run(self):
        self.win.show()
        with self.loop:
            self.loop.run_forever()


if __name__ == "__main__":
    app = Autoseek()
    app.run()
