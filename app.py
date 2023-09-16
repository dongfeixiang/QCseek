# 单PyQt打包
# nuitka --mingw64 --standalone --show-progress --show-memory --enable-plugin=pyqt6 --windows-disable-console --output-dir=nuitka_out app.py
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.uic.load_ui import loadUi
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from base.draggable import DraggableWindow
from base.main_ui import Ui_Form


class main_window(DraggableWindow, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # loadUi("base/main.ui", self)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.maximizeButton.clicked.connect(self.onClickMaximizeButton)

    def onClickMaximizeButton(self):
        if self.isMaximized():
            self.showNormal()
            self.maximizeButton.setIcon(QIcon("resource/Maximize-1.png"))
        else:
            self.showMaximized()
            self.maximizeButton.setIcon(QIcon("resource/Maximize-3.png"))


if __name__ == "__main__":
    app = QApplication([])
    win = main_window()
    win.show()
    app.exec()
