# 单PyQt打包
# nuitka --mingw64 --standalone --show-progress --show-memory --enable-plugin=pyqt6 --windows-disable-console --output-dir=nuitka_out app.py
from PyQt6.QtWidgets import QApplication

from QCseek.qcwidget import QcWidget


class Autoseek(QApplication):
    def __init__(self):
        super().__init__([])
        # self.win = BaseWindow()
        self.win = QcWidget()

    def run(self):
        self.win.show()
        self.exec()


if __name__ == "__main__":
    app = Autoseek()
    app.run()
