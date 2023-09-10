from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.uic.load_ui import loadUi
from PyQt6.QtCore import Qt

from base.draggable import DraggableWindow


class main_window(DraggableWindow):
    def __init__(self):
        super().__init__()
        loadUi("main.ui", self)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


if __name__ == "__main__":
    app = QApplication([])
    win = main_window()
    win.show()
    app.exec()
