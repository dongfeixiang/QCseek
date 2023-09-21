# 单PyQt打包
# nuitka --mingw64 --standalone --show-progress --show-memory --enable-plugin=pyqt6 --windows-disable-console --output-dir=nuitka_out app.py
import asyncio

from qasync import QApplication, QEventLoop

from QCseek.qcwidget import QcWidget


class Autoseek(QApplication):
    def __init__(self):
        super().__init__([])
        self.loop = QEventLoop(self)
        asyncio.set_event_loop(self.loop)
        # self.win = BaseWindow()
        self.win = QcWidget()

    def run(self):
        self.win.show()
        with self.loop:
            self.loop.run_forever()


if __name__ == "__main__":
    app = Autoseek()
    app.run()
